import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  serverExternalPackages: ["ffmpeg-static", "fluent-ffmpeg", "@ffprobe-installer/ffprobe"],
};

export default nextConfig;
