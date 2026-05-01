import { chatCompletion } from "@/lib/ai";
import { prisma } from "@/lib/db";
import { LANDING_GENERATE_SYSTEM } from "@/lib/prompts/landing";
import { NextResponse } from "next/server";

export const dynamic = "force-dynamic";

export async function POST(request: Request) {
  try {
    const { analysisResult, projectId, customInstructions } =
      (await request.json()) as {
        analysisResult: string;
        projectId?: string;
        customInstructions?: string;
      };

    if (!analysisResult?.trim()) {
      return NextResponse.json(
        { error: "분석 결과가 필요합니다" },
        { status: 400 }
      );
    }

    let userMessage = `다음 분석 결과를 기반으로 랜딩페이지 HTML을 생성해주세요:\n\n${analysisResult}`;
    if (customInstructions) {
      userMessage += `\n\n추가 요구사항:\n${customInstructions}`;
    }

    const html = await chatCompletion(LANDING_GENERATE_SYSTEM, userMessage, {
      maxTokens: 8192,
    });

    // Clean up potential markdown code blocks
    const cleanHtml = html
      .replace(/^```html?\n?/i, "")
      .replace(/\n?```$/i, "")
      .trim();

    if (projectId) {
      await prisma.landingPageProject.update({
        where: { id: projectId },
        data: { generatedHtml: cleanHtml },
      });
    }

    return NextResponse.json({ html: cleanHtml, projectId });
  } catch (error) {
    console.error("Landing generate error:", error);
    return NextResponse.json(
      { error: "페이지 생성 중 오류가 발생했습니다" },
      { status: 500 }
    );
  }
}
