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
export const maxDuration = 300;

function parseJson(raw: string) {
  const m = raw.match(/\{[\s\S]*\}/);
  if (!m) throw new Error("JSON 파싱 실패");
  return JSON.parse(m[0]);
}

export async function POST(request: Request) {
  try {
    const { analysisId, serviceType, productName, price } = await request.json();

    const analysis = await prisma.adAnalysis.findUnique({ where: { id: analysisId } });
    if (!analysis) return NextResponse.json({ error: "분석 결과를 찾을 수 없습니다" }, { status: 404 });

    const rawAnalysis = analysis.rawAnalysis ?? "";
    const ts = Date.now();

    // B타입과 C타입 동시 생성
    const [slideshowResult, voiceoverResult] = await Promise.allSettled([
      // B: 슬라이드쇼
      (async () => {
        const msg = buildSlideshowMessage(rawAnalysis, serviceType, productName, price);
        const raw = await chatCompletion(SLIDESHOW_GENERATION_SYSTEM, msg, { temperature: 0.7 });
        const data = parseJson(raw);
        const videoPath = await generateSlideshowVideo(data.slides, `slideshow_${ts}.mp4`);
        return await prisma.generatedAd.create({
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
      })(),
      // C: 나레이션
      (async () => {
        const msg = buildVoiceoverMessage(rawAnalysis, serviceType, productName, price);
        const raw = await chatCompletion(VOICEOVER_GENERATION_SYSTEM, msg, { temperature: 0.7 });
        const data = parseJson(raw);
        const videoPath = await generateVoiceoverVideo(
          data.script,
          data.subtitles,
          data.imagePrompt,
          `voiceover_${ts}.mp4`
        );
        return await prisma.generatedAd.create({
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
      })(),
    ]);

    const results = {
      slideshow: slideshowResult.status === "fulfilled" ? slideshowResult.value : null,
      voiceover: voiceoverResult.status === "fulfilled" ? voiceoverResult.value : null,
      slideshowError: slideshowResult.status === "rejected" ? String(slideshowResult.reason) : null,
      voiceoverError: voiceoverResult.status === "rejected" ? String(voiceoverResult.reason) : null,
    };

    return NextResponse.json(results);
  } catch (error) {
    console.error("Generate error:", error);
    return NextResponse.json(
      { error: error instanceof Error ? error.message : "생성 중 오류가 발생했습니다" },
      { status: 500 }
    );
  }
}
