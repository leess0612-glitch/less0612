import { chatCompletion } from "@/lib/ai";
import { prisma } from "@/lib/db";
import {
  BLOG_TO_SCRIPT_SYSTEM,
  PATTERN_ANALYSIS_SYSTEM,
} from "@/lib/prompts/script-analysis";
import { NextResponse } from "next/server";

export const dynamic = "force-dynamic";

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const { type, content } = body as {
      type: "blog-to-script" | "pattern-analysis";
      content: string;
    };

    if (!content?.trim()) {
      return NextResponse.json(
        { error: "내용을 입력해주세요" },
        { status: 400 }
      );
    }

    let systemPrompt: string;
    let userMessage: string;

    if (type === "blog-to-script") {
      systemPrompt = BLOG_TO_SCRIPT_SYSTEM;
      userMessage = `다음 블로그 글을 숏폼 광고 대본으로 변환해주세요:\n\n${content}`;
    } else {
      systemPrompt = PATTERN_ANALYSIS_SYSTEM;
      userMessage = `다음 광고 대본들을 분석하여 성공 패턴을 추출해주세요:\n\n${content}`;
    }

    const result = await chatCompletion(systemPrompt, userMessage);

    const record = await prisma.scriptAnalysis.create({
      data: {
        sourceType: type === "blog-to-script" ? "blog" : "script",
        sourceContent: content,
        result,
        generatedScript: type === "blog-to-script" ? result : null,
      },
    });

    return NextResponse.json({ result, id: record.id });
  } catch (error) {
    console.error("Script analysis error:", error);
    return NextResponse.json(
      { error: "AI 분석 중 오류가 발생했습니다. API 키를 확인해주세요." },
      { status: 500 }
    );
  }
}

export async function GET() {
  const records = await prisma.scriptAnalysis.findMany({
    orderBy: { createdAt: "desc" },
    take: 20,
  });
  return NextResponse.json(records);
}
