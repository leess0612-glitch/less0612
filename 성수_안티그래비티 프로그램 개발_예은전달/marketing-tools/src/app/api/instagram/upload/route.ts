import { prisma } from "@/lib/db";
import { NextResponse } from "next/server";

export const dynamic = "force-dynamic";

export async function POST(request: Request) {
  try {
    const { id, caption } = await request.json();

    const accessToken = process.env.INSTAGRAM_ACCESS_TOKEN;
    const accountId = process.env.INSTAGRAM_BUSINESS_ACCOUNT_ID;
    const appBaseUrl = process.env.APP_BASE_URL;

    if (!accessToken || !accountId) {
      return NextResponse.json(
        { error: "Instagram API 키가 설정되지 않았습니다. .env 파일을 확인해주세요." },
        { status: 500 }
      );
    }

    const ad = await prisma.instagramAd.findUnique({ where: { id } });
    if (!ad || !ad.imageUrl) {
      return NextResponse.json({ error: "광고를 찾을 수 없습니다." }, { status: 404 });
    }

    const publicImageUrl = `${appBaseUrl}${ad.imageUrl}`;
    const fullCaption = caption
      ? caption
      : `${ad.caption}\n\n${JSON.parse(ad.hashtags || "[]")
          .map((h: string) => `#${h}`)
          .join(" ")}`;

    // Step 1: 미디어 컨테이너 생성
    const containerRes = await fetch(
      `https://graph.facebook.com/v21.0/${accountId}/media`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          image_url: publicImageUrl,
          caption: fullCaption,
          access_token: accessToken,
        }),
      }
    );

    const container = await containerRes.json();
    if (container.error) {
      return NextResponse.json({ error: `Instagram 오류: ${container.error.message}` }, { status: 400 });
    }

    // Step 2: 게시
    const publishRes = await fetch(
      `https://graph.facebook.com/v21.0/${accountId}/media_publish`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          creation_id: container.id,
          access_token: accessToken,
        }),
      }
    );

    const published = await publishRes.json();
    if (published.error) {
      return NextResponse.json({ error: `게시 오류: ${published.error.message}` }, { status: 400 });
    }

    await prisma.instagramAd.update({
      where: { id },
      data: {
        status: "uploaded",
        instagramId: published.id,
        postedAt: new Date(),
      },
    });

    return NextResponse.json({ success: true, instagramId: published.id });
  } catch (error) {
    console.error("Instagram upload error:", error);
    return NextResponse.json(
      { error: error instanceof Error ? error.message : "업로드 중 오류가 발생했습니다." },
      { status: 500 }
    );
  }
}
