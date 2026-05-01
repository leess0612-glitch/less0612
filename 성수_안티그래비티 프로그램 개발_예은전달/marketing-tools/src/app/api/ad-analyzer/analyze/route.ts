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

async function getYouTubeMeta(videoId: string): Promise<{ title: string; description: string }> {
  try {
    const res = await fetch(`https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v=${videoId}&format=json`);
    const data = await res.json();
    return { title: data.title ?? "", description: "" };
  } catch {
    return { title: "", description: "" };
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

export async function POST(request: Request) {
  try {
    const { url } = await request.json();
    if (!url?.trim()) {
      return NextResponse.json({ error: "URL을 입력해주세요" }, { status: 400 });
    }

    const platform = detectPlatform(url);
    let title = "";
    let transcript = "";

    if (platform === "youtube") {
      const videoId = extractYouTubeId(url);
      if (!videoId) return NextResponse.json({ error: "유효하지 않은 YouTube URL입니다" }, { status: 400 });

      const [meta, trans] = await Promise.all([
        getYouTubeMeta(videoId),
        getTranscript(videoId),
      ]);
      title = meta.title;
      transcript = trans;
    } else {
      title = url;
    }

    const userMessage = buildAnalysisMessage(title, transcript, url);
    const rawResult = await chatCompletion(AD_ANALYSIS_SYSTEM, userMessage, { temperature: 0.3 });

    const jsonMatch = rawResult.match(/\{[\s\S]*\}/);
    if (!jsonMatch) throw new Error("분석 결과 파싱 실패");
    const analysis = JSON.parse(jsonMatch[0]);

    const record = await prisma.adAnalysis.create({
      data: {
        sourceUrl: url,
        platform,
        title,
        transcript: transcript.slice(0, 5000),
        adStructure: JSON.stringify(analysis.adStructure),
        scriptStyle: JSON.stringify(analysis.scriptStyle),
        visualStyle: JSON.stringify(analysis.visualStyle),
        hooks: JSON.stringify(analysis.hooks),
        targetAudience: analysis.targetAudience,
        rawAnalysis: JSON.stringify(analysis),
      },
    });

    return NextResponse.json({ ...record, analysis });
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
