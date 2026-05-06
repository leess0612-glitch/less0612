import { chatCompletion } from "@/lib/ai";
import { prisma } from "@/lib/db";
import {
  AD_ANALYSIS_SYSTEM,
  buildAnalysisMessage,
} from "@/lib/prompts/ad-analyzer";
import { YoutubeTranscript } from "youtube-transcript";
import { NextResponse } from "next/server";

export const dynamic = "force-dynamic";

function extractYouTubeId(url: string): string | null {
  const patterns = [
    /(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/shorts\/)([a-zA-Z0-9_-]{11})/,
    /youtube\.com\/embed\/([a-zA-Z0-9_-]{11})/,
  ];
  for (const p of patterns) {
    const m = url.match(p);
    if (m) return m[1];
  }
  return null;
}

function detectPlatform(url: string): "youtube" | "instagram" | "unknown" {
  if (url.includes("youtube.com") || url.includes("youtu.be")) return "youtube";
  if (url.includes("instagram.com")) return "instagram";
  return "unknown";
}

async function getYouTubeMeta(videoId: string): Promise<{ title: string }> {
  try {
    const res = await fetch(
      `https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v=${videoId}&format=json`,
      { headers: { "User-Agent": "Mozilla/5.0" } }
    );
    const data = await res.json();
    return { title: data.title ?? "" };
  } catch {
    return { title: "" };
  }
}

async function getTranscript(videoId: string): Promise<string> {
  try {
    const items = await YoutubeTranscript.fetchTranscript(videoId, { lang: "ko" });
    return items.map((i) => i.text).join(" ");
  } catch {
    try {
      const items = await YoutubeTranscript.fetchTranscript(videoId);
      return items.map((i) => i.text).join(" ");
    } catch {
      return "";
    }
  }
}

// Instagram 페이지에서 OG 메타태그 추출
async function scrapeInstagramMeta(url: string): Promise<{ title: string; description: string }> {
  try {
    const res = await fetch(url, {
      headers: {
        "User-Agent": "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
        "Accept-Language": "ko-KR,ko;q=0.9",
      },
      signal: AbortSignal.timeout(8000),
    });
    const html = await res.text();

    const titleMatch =
      html.match(/<meta property="og:title" content="([^"]*)"/) ||
      html.match(/<title>([^<]*)<\/title>/);
    const descMatch =
      html.match(/<meta property="og:description" content="([^"]*)"/) ||
      html.match(/<meta name="description" content="([^"]*)"/);

    return {
      title: titleMatch?.[1]?.replace(/&quot;/g, '"').replace(/&amp;/g, "&").replace(/&#039;/g, "'") ?? "",
      description: descMatch?.[1]?.replace(/&quot;/g, '"').replace(/&amp;/g, "&").replace(/&#039;/g, "'") ?? "",
    };
  } catch {
    return { title: "", description: "" };
  }
}

// GPT 응답에서 JSON 추출 (여러 방법 시도)
function extractJson(raw: string): Record<string, unknown> | null {
  // 1차: 코드블록 안 JSON
  const codeBlock = raw.match(/```(?:json)?\s*([\s\S]*?)```/);
  if (codeBlock) {
    try { return JSON.parse(codeBlock[1].trim()); } catch {}
  }
  // 2차: 중괄호 블록
  const braceMatch = raw.match(/\{[\s\S]*\}/);
  if (braceMatch) {
    try { return JSON.parse(braceMatch[0]); } catch {}
  }
  return null;
}

export async function POST(request: Request) {
  try {
    const { url } = await request.json();
    if (!url?.trim()) {
      return NextResponse.json({ error: "URL을 입력해주세요" }, { status: 400 });
    }

    const platform = detectPlatform(url);
    let title = "";
    let transcript = "";
    let extraContext = "";

    if (platform === "youtube") {
      const videoId = extractYouTubeId(url);
      if (!videoId) {
        return NextResponse.json({ error: "유효하지 않은 YouTube URL입니다" }, { status: 400 });
      }
      const [meta, trans] = await Promise.all([
        getYouTubeMeta(videoId),
        getTranscript(videoId),
      ]);
      title = meta.title;
      transcript = trans;

    } else if (platform === "instagram") {
      const meta = await scrapeInstagramMeta(url);
      title = meta.title || "Instagram 광고";
      extraContext = meta.description
        ? `게시물 설명: ${meta.description}`
        : "※ Instagram 페이지에 직접 접근할 수 없습니다. 한국 렌탈/인터넷 서비스 광고의 일반적인 패턴을 기반으로 분석해주세요.";

    } else {
      title = url;
      extraContext = "※ URL에 직접 접근할 수 없습니다. 한국 렌탈/인터넷 서비스 광고의 일반적인 패턴을 기반으로 분석해주세요.";
    }

    const userMessage = buildAnalysisMessage(title, transcript, url, extraContext);
    const rawResult = await chatCompletion(AD_ANALYSIS_SYSTEM, userMessage, { temperature: 0.3 });

    const analysis = extractJson(rawResult);
    if (!analysis) {
      console.error("GPT raw response:", rawResult);
      throw new Error("AI 분석 결과를 파싱할 수 없습니다. 다시 시도해주세요.");
    }

    // 필수 필드 기본값 보장
    const safeAnalysis = {
      adStructure: analysis.adStructure ?? { hook: "", body: "", cta: "" },
      scriptStyle: analysis.scriptStyle ?? { tone: "", pacing: "", keywords: [] },
      visualStyle: analysis.visualStyle ?? { style: "", mood: "", recommendation: "" },
      hooks: analysis.hooks ?? [],
      targetAudience: analysis.targetAudience ?? "",
      summary: analysis.summary ?? "",
    };

    const record = await prisma.adAnalysis.create({
      data: {
        sourceUrl: url,
        platform,
        title,
        transcript: transcript.slice(0, 5000),
        adStructure: JSON.stringify(safeAnalysis.adStructure),
        scriptStyle: JSON.stringify(safeAnalysis.scriptStyle),
        visualStyle: JSON.stringify(safeAnalysis.visualStyle),
        hooks: JSON.stringify(safeAnalysis.hooks),
        targetAudience: String(safeAnalysis.targetAudience),
        rawAnalysis: JSON.stringify(safeAnalysis),
      },
    });

    return NextResponse.json({ ...record, analysis: safeAnalysis });
  } catch (error) {
    console.error("Analysis error:", error);
    return NextResponse.json(
      { error: error instanceof Error ? error.message : "분석 중 오류가 발생했습니다" },
      { status: 500 }
    );
  }
}

export async function GET() {
  const analyses = await prisma.adAnalysis.findMany({
    orderBy: { createdAt: "desc" },
    include: { generatedAds: true },
  });
  return NextResponse.json(analyses);
}
