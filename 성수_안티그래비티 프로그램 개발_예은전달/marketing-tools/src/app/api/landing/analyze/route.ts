import { chatCompletion } from "@/lib/ai";
import { prisma } from "@/lib/db";
import { scrapeUrl } from "@/lib/scraper";
import { LANDING_ANALYSIS_SYSTEM } from "@/lib/prompts/landing";
import { NextResponse } from "next/server";

export const dynamic = "force-dynamic";

export async function POST(request: Request) {
  try {
    const { url } = (await request.json()) as { url: string };

    if (!url?.trim()) {
      return NextResponse.json(
        { error: "URL을 입력해주세요" },
        { status: 400 }
      );
    }

    const html = await scrapeUrl(url);
    const result = await chatCompletion(
      LANDING_ANALYSIS_SYSTEM,
      `다음 웹페이지를 분석해주세요.\n\nURL: ${url}\n\nHTML 콘텐츠:\n${html}`
    );

    const record = await prisma.landingPageProject.create({
      data: {
        sourceUrl: url,
        analysisResult: result,
      },
    });

    return NextResponse.json({ result, id: record.id });
  } catch (error) {
    console.error("Landing analysis error:", error);
    const message =
      error instanceof Error ? error.message : "분석 중 오류가 발생했습니다";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
