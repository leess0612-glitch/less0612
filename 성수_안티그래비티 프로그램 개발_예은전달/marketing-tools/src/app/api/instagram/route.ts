import { chatCompletion } from "@/lib/ai";
import { prisma } from "@/lib/db";
import { INSTAGRAM_AD_COPY_SYSTEM, buildAdUserMessage } from "@/lib/prompts/instagram";
import OpenAI from "openai";
import fs from "fs";
import path from "path";
import { NextResponse } from "next/server";

export const dynamic = "force-dynamic";

async function saveImageLocally(url: string): Promise<string> {
  const res = await fetch(url);
  const buffer = await res.arrayBuffer();
  const dir = path.join(process.cwd(), "public", "generated");
  fs.mkdirSync(dir, { recursive: true });
  const filename = `ig_${Date.now()}.png`;
  fs.writeFileSync(path.join(dir, filename), Buffer.from(buffer));
  return `/generated/${filename}`;
}

export async function GET() {
  const ads = await prisma.instagramAd.findMany({
    orderBy: { createdAt: "desc" },
  });
  return NextResponse.json(
    ads.map((ad) => ({
      ...ad,
      features: JSON.parse(ad.features || "[]"),
      adCopy: ad.adCopy ? JSON.parse(ad.adCopy) : null,
      hashtags: JSON.parse(ad.hashtags || "[]"),
    }))
  );
}

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const { serviceType, productName, price, features, tone } = body;

    if (!productName?.trim()) {
      return NextResponse.json({ error: "제품명을 입력해주세요" }, { status: 400 });
    }

    // 1. GPT-4o로 광고 카피 생성
    const userMessage = buildAdUserMessage({ serviceType, productName, price, features, tone });
    const rawResult = await chatCompletion(INSTAGRAM_AD_COPY_SYSTEM, userMessage, {
      temperature: 0.8,
    });

    const jsonMatch = rawResult.match(/\{[\s\S]*\}/);
    if (!jsonMatch) throw new Error("AI 응답 파싱 실패");
    const adData = JSON.parse(jsonMatch[0]);

    // 2. DALL-E 3으로 이미지 생성
    const openai = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });
    const imageResponse = await openai.images.generate({
      model: "dall-e-3",
      prompt: `${adData.imagePrompt} Clean modern Korean advertisement style, professional product photography, soft gradient background, Instagram square format, high quality, no text or watermarks.`,
      size: "1024x1024",
      quality: "standard",
      n: 1,
    });

    const dalleUrl = (imageResponse.data ?? [])[0]?.url ?? "";
    const localImageUrl = await saveImageLocally(dalleUrl);

    // 3. DB 저장
    const ad = await prisma.instagramAd.create({
      data: {
        serviceType,
        productName,
        price: price || null,
        features: JSON.stringify(features || []),
        adCopy: JSON.stringify({ headline: adData.headline, subheadline: adData.subheadline }),
        imageUrl: localImageUrl,
        imagePrompt: adData.imagePrompt,
        caption: adData.caption,
        hashtags: JSON.stringify(adData.hashtags || []),
        status: "generated",
      },
    });

    return NextResponse.json({
      ...ad,
      features: features || [],
      adCopy: { headline: adData.headline, subheadline: adData.subheadline },
      hashtags: adData.hashtags || [],
    });
  } catch (error) {
    console.error("Instagram generate error:", error);
    return NextResponse.json(
      { error: error instanceof Error ? error.message : "생성 중 오류가 발생했습니다. API 키를 확인해주세요." },
      { status: 500 }
    );
  }
}

export async function PATCH(request: Request) {
  try {
    const body = await request.json();
    const { id, caption, hashtags } = body;

    const ad = await prisma.instagramAd.update({
      where: { id },
      data: {
        caption,
        hashtags: JSON.stringify(hashtags || []),
      },
    });

    return NextResponse.json(ad);
  } catch (error) {
    return NextResponse.json({ error: "수정 실패" }, { status: 500 });
  }
}

export async function DELETE(request: Request) {
  const { searchParams } = new URL(request.url);
  const id = searchParams.get("id");
  if (!id) return NextResponse.json({ error: "ID 필요" }, { status: 400 });

  await prisma.instagramAd.delete({ where: { id } });
  return NextResponse.json({ success: true });
}
