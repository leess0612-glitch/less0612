import { prisma } from "@/lib/db";
import fs from "fs";
import path from "path";
import { NextResponse } from "next/server";

export const dynamic = "force-dynamic";

async function uploadToInstagram(videoPath: string, caption: string): Promise<string> {
  const accessToken = process.env.INSTAGRAM_ACCESS_TOKEN;
  const accountId = process.env.INSTAGRAM_BUSINESS_ACCOUNT_ID;
  const baseUrl = process.env.APP_BASE_URL ?? "http://localhost:3000";
  if (!accessToken || !accountId) throw new Error("Instagram API 키 없음");

  const videoUrl = `${baseUrl}${videoPath}`;

  // 릴스로 업로드
  const containerRes = await fetch(`https://graph.facebook.com/v21.0/${accountId}/media`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      media_type: "REELS",
      video_url: videoUrl,
      caption,
      access_token: accessToken,
    }),
  });
  const container = await containerRes.json();
  if (container.error) throw new Error(container.error.message);

  // 처리 대기 (최대 30초)
  for (let i = 0; i < 6; i++) {
    await new Promise((r) => setTimeout(r, 5000));
    const statusRes = await fetch(
      `https://graph.facebook.com/v21.0/${container.id}?fields=status_code&access_token=${accessToken}`
    );
    const status = await statusRes.json();
    if (status.status_code === "FINISHED") break;
  }

  const publishRes = await fetch(`https://graph.facebook.com/v21.0/${accountId}/media_publish`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ creation_id: container.id, access_token: accessToken }),
  });
  const published = await publishRes.json();
  if (published.error) throw new Error(published.error.message);

  return published.id;
}

async function uploadToYouTube(videoPath: string, title: string, description: string): Promise<string> {
  const refreshToken = process.env.YOUTUBE_REFRESH_TOKEN;
  const clientId = process.env.YOUTUBE_CLIENT_ID;
  const clientSecret = process.env.YOUTUBE_CLIENT_SECRET;
  if (!refreshToken || !clientId || !clientSecret) throw new Error("YouTube API 키 없음");

  // Access token 갱신
  const tokenRes = await fetch("https://oauth2.googleapis.com/token", {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: new URLSearchParams({
      client_id: clientId,
      client_secret: clientSecret,
      refresh_token: refreshToken,
      grant_type: "refresh_token",
    }),
  });
  const tokenData = await tokenRes.json();
  if (!tokenData.access_token) throw new Error("YouTube 토큰 갱신 실패");

  const absolutePath = path.join(process.cwd(), "public", videoPath);
  const videoBuffer = fs.readFileSync(absolutePath);

  // 업로드 초기화
  const initRes = await fetch(
    "https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status",
    {
      method: "POST",
      headers: {
        Authorization: `Bearer ${tokenData.access_token}`,
        "Content-Type": "application/json",
        "X-Upload-Content-Type": "video/mp4",
        "X-Upload-Content-Length": String(videoBuffer.length),
      },
      body: JSON.stringify({
        snippet: { title, description, categoryId: "22" },
        status: { privacyStatus: "public", selfDeclaredMadeForKids: false },
      }),
    }
  );
  const uploadUrl = initRes.headers.get("location");
  if (!uploadUrl) throw new Error("YouTube 업로드 URL 획득 실패");

  // 영상 업로드
  const uploadRes = await fetch(uploadUrl, {
    method: "PUT",
    headers: { "Content-Type": "video/mp4", "Content-Length": String(videoBuffer.length) },
    body: videoBuffer,
  });
  const uploaded = await uploadRes.json();
  if (!uploaded.id) throw new Error("YouTube 업로드 실패");

  return uploaded.id;
}

async function uploadToTikTok(videoPath: string, caption: string): Promise<string> {
  const accessToken = process.env.TIKTOK_ACCESS_TOKEN;
  if (!accessToken) throw new Error("TikTok API 키 없음");

  const absolutePath = path.join(process.cwd(), "public", videoPath);
  const videoBuffer = fs.readFileSync(absolutePath);

  // TikTok Content Posting API
  const initRes = await fetch("https://open.tiktokapis.com/v2/post/publish/video/init/", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${accessToken}`,
      "Content-Type": "application/json; charset=UTF-8",
    },
    body: JSON.stringify({
      post_info: { title: caption.slice(0, 150), privacy_level: "PUBLIC_TO_EVERYONE", disable_comment: false },
      source_info: { source: "FILE_UPLOAD", video_size: videoBuffer.length, chunk_size: videoBuffer.length, total_chunk_count: 1 },
    }),
  });
  const initData = await initRes.json();
  if (initData.error?.code !== "ok") throw new Error(initData.error?.message ?? "TikTok 초기화 실패");

  const { publish_id, upload_url } = initData.data;

  await fetch(upload_url, {
    method: "PUT",
    headers: {
      "Content-Type": "video/mp4",
      "Content-Range": `bytes 0-${videoBuffer.length - 1}/${videoBuffer.length}`,
    },
    body: videoBuffer,
  });

  return publish_id;
}

export async function POST(request: Request) {
  const { generatedAdId, platforms, title } = await request.json();

  const ad = await prisma.generatedAd.findUnique({
    where: { id: generatedAdId },
    include: { analysis: true },
  });
  if (!ad || !ad.videoPath) {
    return NextResponse.json({ error: "생성된 광고를 찾을 수 없습니다" }, { status: 404 });
  }

  const caption = `${ad.caption ?? ""}\n\n${JSON.parse(ad.hashtags ?? "[]").map((h: string) => `#${h}`).join(" ")}`;
  const videoTitle = title || `${ad.productName} 광고`;
  const results: Record<string, { success: boolean; id?: string; error?: string }> = {};

  for (const platform of platforms as string[]) {
    const upload = await prisma.adUpload.create({
      data: { generatedAdId, platform, status: "pending" },
    });

    try {
      let platformId = "";
      if (platform === "instagram") platformId = await uploadToInstagram(ad.videoPath, caption);
      else if (platform === "youtube") platformId = await uploadToYouTube(ad.videoPath, videoTitle, caption);
      else if (platform === "tiktok") platformId = await uploadToTikTok(ad.videoPath, caption);

      await prisma.adUpload.update({
        where: { id: upload.id },
        data: { status: "success", platformId, uploadedAt: new Date() },
      });
      results[platform] = { success: true, id: platformId };
    } catch (err) {
      const errMsg = err instanceof Error ? err.message : "업로드 실패";
      await prisma.adUpload.update({
        where: { id: upload.id },
        data: { status: "failed", error: errMsg },
      });
      results[platform] = { success: false, error: errMsg };
    }
  }

  await prisma.generatedAd.update({
    where: { id: generatedAdId },
    data: { status: "uploaded" },
  });

  return NextResponse.json(results);
}
