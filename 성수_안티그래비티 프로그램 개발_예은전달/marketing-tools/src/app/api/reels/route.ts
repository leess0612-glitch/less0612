import { chatCompletion } from "@/lib/ai";
import { prisma } from "@/lib/db";
import { REELS_SCRIPT_SYSTEM } from "@/lib/prompts/reels";
import { NextResponse } from "next/server";

export const dynamic = "force-dynamic";

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const { action } = body as { action: string };

    if (action === "generate-script") {
      const { platform, topic, tone } = body as {
        platform: string;
        topic: string;
        tone?: string;
      };

      if (!topic?.trim()) {
        return NextResponse.json(
          { error: "주제를 입력해주세요" },
          { status: 400 }
        );
      }

      const userMessage = `플랫폼: ${platform}\n주제/키워드: ${topic}${tone ? `\n톤: ${tone}` : ""}\n\n위 조건에 맞는 숏폼 광고 대본을 작성해주세요.`;

      const result = await chatCompletion(REELS_SCRIPT_SYSTEM, userMessage);

      const record = await prisma.reelsProject.create({
        data: {
          title: topic,
          script: result,
          platform,
          status: "script_ready",
        },
      });

      return NextResponse.json({ result, id: record.id });
    }

    if (action === "save-upload") {
      const { id, uploadId, platform } = body;
      await prisma.reelsProject.update({
        where: { id },
        data: { uploadId, platform, status: "uploaded" },
      });
      return NextResponse.json({ success: true });
    }

    if (action === "update-metrics") {
      const { id, metrics } = body;
      await prisma.reelsProject.update({
        where: { id },
        data: { metrics: JSON.stringify(metrics), status: "tracking" },
      });
      return NextResponse.json({ success: true });
    }

    return NextResponse.json({ error: "Unknown action" }, { status: 400 });
  } catch (error) {
    console.error("Reels API error:", error);
    return NextResponse.json(
      { error: "오류가 발생했습니다. API 키를 확인해주세요." },
      { status: 500 }
    );
  }
}

export async function GET() {
  const projects = await prisma.reelsProject.findMany({
    orderBy: { createdAt: "desc" },
  });
  return NextResponse.json(
    projects.map((p) => ({
      ...p,
      metrics: p.metrics ? JSON.parse(p.metrics) : null,
    }))
  );
}
