import { chatCompletion } from "@/lib/ai";
import { prisma } from "@/lib/db";
import {
  SLIDESHOW_GENERATION_SYSTEM,
  VOICEOVER_GENERATION_SYSTEM,
  buildSlideshowMessage,
  buildVoiceoverMessage,
} from "@/lib/prompts/ad-analyzer";
import { generateSlideshowVideo, generateVoiceoverVideo } from "@/lib/video-generator";
import { NextResponse } from "next/server";

export const dynamic = "force-dynamic";

function parseJson(raw: string) {
  const match = raw.match(/```(?:json)?\s*([\s\S]*?)```/) || raw.match(/\{[\s\S]*\}/);
  if (!match) throw new Error("JSON 파싱 실패");
  const str = match[1] ?? match[0];
  return JSON.parse(str.trim());
}

async function generateSlideshow(analysisId: string, rawAnalysis: string, serviceType: string, productName: string, price: string, ts: number) {
  const msg = buildSlideshowMessage(rawAnalysis, serviceType, productName, price);
  const raw = await chatCompletion(SLIDESHOW_GENERATION_SYSTEM, msg, { temperature: 0.7 });
  const data = parseJson(raw);
  const videoPath = await generateSlideshowVideo(data.slides, `slideshow_${ts}.mp4`);
  return prisma.generatedAd.create({
    data: {
      analysisId,
      adType: "B_slideshow",
      productName,
      serviceType,
      videoPath,
      script: JSON.stringify(data.slides),
      caption: data.caption,
      hashtags: JSON.stringify(data.hashtags || []),
    },
  });
}

async function generateVoiceover(analysisId: string, rawAnalysis: string, serviceType: string, productName: string, price: string, ts: number) {
  const msg = buildVoiceoverMessage(rawAnalysis, serviceType, productName, price);
  const raw = await chatCompletion(VOICEOVER_GENERATION_SYSTEM, msg, { temperature: 0.7 });
  const data = parseJson(raw);
  const videoPath = await generateVoiceoverVideo(
    data.script,
    data.subtitles,
    data.imagePrompt,
    `voiceover_${ts}.mp4`
  );
  return prisma.generatedAd.create({
    data: {
      analysisId,
      adType: "C_voiceover",
      productName,
      serviceType,
      videoPath,
      script: data.script,
      caption: data.caption,
      hashtags: JSON.stringify(data.hashtags || []),
    },
  });
}

export async function POST(request: Request) {
  try {
    const { analysisId, serviceType, productName, price, type = "both" } = await request.json();
    // type: "B" | "C" | "both"

    const analysis = await prisma.adAnalysis.findUnique({ where: { id: analysisId } });
    if (!analysis) return NextResponse.json({ error: "분석 결과를 찾을 수 없습니다" }, { status: 404 });

    const rawAnalysis = analysis.rawAnalysis ?? "";
    const ts = Date.now();

    if (type === "B") {
      const result = await generateSlideshow(analysisId, rawAnalysis, serviceType, productName, price, ts);
      return NextResponse.json({ slideshow: result, voiceover: null, slideshowError: null, voiceoverError: null });
    }

    if (type === "C") {
      const result = await generateVoiceover(analysisId, rawAnalysis, serviceType, productName, price, ts);
      return NextResponse.json({ slideshow: null, voiceover: result, slideshowError: null, voiceoverError: null });
    }

    // both: 병렬 생성
    const [slideshowResult, voiceoverResult] = await Promise.allSettled([
      generateSlideshow(analysisId, rawAnalysis, serviceType, productName, price, ts),
      generateVoiceover(analysisId, rawAnalysis, serviceType, productName, price, ts + 1),
    ]);

    return NextResponse.json({
      slideshow: slideshowResult.status === "fulfilled" ? slideshowResult.value : null,
      voiceover: voiceoverResult.status === "fulfilled" ? voiceoverResult.value : null,
      slideshowError: slideshowResult.status === "rejected" ? String(slideshowResult.reason) : null,
      voiceoverError: voiceoverResult.status === "rejected" ? String(voiceoverResult.reason) : null,
    });
  } catch (error) {
    console.error("Generate error:", error);
    return NextResponse.json(
      { error: error instanceof Error ? error.message : "생성 중 오류가 발생했습니다" },
      { status: 500 }
    );
  }
}
