import ffmpegStatic from "ffmpeg-static";
import ffprobeInstaller from "@ffprobe-installer/ffprobe";
import Ffmpeg from "fluent-ffmpeg";
import fs from "fs";
import path from "path";
import os from "os";
import OpenAI from "openai";

// Next.js 번들링 시 \ROOT\ 경로를 실제 경로로 치환
function resolveBinaryPath(p: string): string {
  if (!p) return p;
  if (p.startsWith("\\ROOT\\") || p.startsWith("/ROOT/")) {
    return path.join(process.cwd(), p.replace(/^[/\\]ROOT[/\\]/, ""));
  }
  return p;
}

const ffmpegPath = resolveBinaryPath(ffmpegStatic as unknown as string);
const ffprobePath = resolveBinaryPath(ffprobeInstaller.path);

if (ffmpegPath && fs.existsSync(ffmpegPath)) {
  Ffmpeg.setFfmpegPath(ffmpegPath);
} else {
  const fallback = path.join(process.cwd(), "node_modules", "ffmpeg-static", "ffmpeg.exe");
  if (fs.existsSync(fallback)) Ffmpeg.setFfmpegPath(fallback);
}

if (ffprobePath && fs.existsSync(ffprobePath)) {
  Ffmpeg.setFfprobePath(ffprobePath);
} else {
  const fallback = path.join(process.cwd(), "node_modules", "@ffprobe-installer", "win32-x64", "ffprobe.exe");
  if (fs.existsSync(fallback)) Ffmpeg.setFfprobePath(fallback);
}

const KOREAN_FONT = "C:/Windows/Fonts/malgun.ttf";
const FALLBACK_FONT = "C:/Windows/Fonts/arial.ttf";

function getFont(): string {
  return fs.existsSync(KOREAN_FONT) ? KOREAN_FONT : FALLBACK_FONT;
}

// Windows TEMP 디렉토리 사용 — 한국어/공백 경로 문제 우회
function makeTempDir(): string {
  const dir = path.join(os.tmpdir(), `mt_${Date.now()}_${Math.random().toString(36).slice(2)}`);
  fs.mkdirSync(dir, { recursive: true });
  return dir;
}

function ensurePublicDir(): string {
  const dir = path.join(process.cwd(), "public", "generated-videos");
  fs.mkdirSync(dir, { recursive: true });
  return dir;
}

async function downloadImage(url: string, dest: string): Promise<void> {
  const res = await fetch(url);
  const buf = await res.arrayBuffer();
  fs.writeFileSync(dest, Buffer.from(buf));
}

function escapeDrawtext(text: string): string {
  return text
    .replace(/\\/g, "\\\\")
    .replace(/'/g, "’")   // 작은따옴표 → 유니코드 대체
    .replace(/:/g, "\\:")
    .replace(/\[/g, "\\[")
    .replace(/\]/g, "\\]");
}

export interface Slide {
  imagePrompt: string;
  mainText: string;
  subText: string;
  duration: number;
}

export interface Subtitle {
  text: string;
  startSec: number;
  endSec: number;
}

// B타입: 슬라이드쇼 영상 생성
export async function generateSlideshowVideo(
  slides: Slide[],
  outputFilename: string
): Promise<string> {
  const openai = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });
  const tmpDir = makeTempDir();
  const font = getFont();

  try {
    const imagePaths: string[] = [];

    // DALL-E 3 이미지 생성 (순서대로)
    for (let i = 0; i < slides.length; i++) {
      const imgRes = await openai.images.generate({
        model: "dall-e-3",
        prompt: `${slides[i].imagePrompt}. Clean Korean advertisement background, professional, high quality, no text, no watermarks, square format.`,
        size: "1024x1024",
        quality: "standard",
        n: 1,
      });
      const imgUrl = (imgRes.data ?? [])[0]?.url ?? "";
      const imgPath = path.join(tmpDir, `slide_${i}.png`);
      await downloadImage(imgUrl, imgPath);
      imagePaths.push(imgPath);
    }

    // ffmpeg 출력도 TEMP에 먼저 생성
    const tmpOutput = path.join(tmpDir, outputFilename);

    await new Promise<void>((resolve, reject) => {
      const cmd = Ffmpeg();
      slides.forEach((_, i) =>
        cmd.input(imagePaths[i]).inputOptions(["-loop 1", `-t ${slides[i].duration}`])
      );

      const filterParts: string[] = [];
      const concatInputs: string[] = [];

      slides.forEach((slide, i) => {
        const mainText = escapeDrawtext(slide.mainText);
        const subText = escapeDrawtext(slide.subText);
        const drawMain = `drawtext=fontfile='${font}':text='${mainText}':fontcolor=white:fontsize=52:x=(w-text_w)/2:y=h*0.72:shadowcolor=black:shadowx=2:shadowy=2:box=1:boxcolor=black@0.45:boxborderw=12`;
        const drawSub = `drawtext=fontfile='${font}':text='${subText}':fontcolor=white:fontsize=30:x=(w-text_w)/2:y=h*0.82:shadowcolor=black:shadowx=1:shadowy=1`;
        filterParts.push(`[${i}:v]scale=1080:1080,${drawMain},${drawSub}[v${i}]`);
        concatInputs.push(`[v${i}]`);
      });

      filterParts.push(`${concatInputs.join("")}concat=n=${slides.length}:v=1:a=0[outv]`);

      cmd
        .complexFilter(filterParts.join(";"))
        .outputOptions(["-map [outv]", "-c:v libx264", "-pix_fmt yuv420p", "-r 30"])
        .output(tmpOutput)
        .on("end", () => resolve())
        .on("error", (err) => reject(new Error(`ffmpeg 오류: ${err.message}`)))
        .run();
    });

    // TEMP → public/generated-videos/ 로 복사
    const finalDir = ensurePublicDir();
    const finalPath = path.join(finalDir, outputFilename);
    fs.copyFileSync(tmpOutput, finalPath);

    return `/generated-videos/${outputFilename}`;
  } finally {
    fs.rmSync(tmpDir, { recursive: true, force: true });
  }
}

// C타입: 나레이션 영상 생성
export async function generateVoiceoverVideo(
  script: string,
  subtitles: Subtitle[],
  imagePrompt: string,
  outputFilename: string
): Promise<string> {
  const openai = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });
  const tmpDir = makeTempDir();
  const font = getFont();

  try {
    // 1. 배경 이미지 생성
    const imgRes = await openai.images.generate({
      model: "dall-e-3",
      prompt: `${imagePrompt}. Clean professional Korean advertisement background, no text, no people, soft gradient, high quality.`,
      size: "1024x1024",
      quality: "standard",
      n: 1,
    });
    const bgPath = path.join(tmpDir, "bg.png");
    await downloadImage((imgRes.data ?? [])[0]?.url ?? "", bgPath);

    // 2. TTS 나레이션 생성
    const ttsResponse = await openai.audio.speech.create({
      model: "tts-1",
      voice: "nova",
      input: script,
      response_format: "mp3",
    });
    const audioPath = path.join(tmpDir, "audio.mp3");
    fs.writeFileSync(audioPath, Buffer.from(await ttsResponse.arrayBuffer()));

    // 3. 오디오 길이 확인
    const audioDuration = await new Promise<number>((resolve, reject) => {
      Ffmpeg.ffprobe(audioPath, (err, meta) => {
        if (err) reject(new Error(`ffprobe 오류: ${err.message}`));
        else resolve(meta.format.duration ?? 20);
      });
    });

    const tmpOutput = path.join(tmpDir, outputFilename);

    // 4. 영상 + 자막 + 오디오 합성
    await new Promise<void>((resolve, reject) => {
      const subtitleFilters = subtitles.map((sub) => {
        const text = escapeDrawtext(sub.text);
        return `drawtext=fontfile='${font}':text='${text}':fontcolor=white:fontsize=40:x=(w-text_w)/2:y=h*0.8:shadowcolor=black:shadowx=2:shadowy=2:box=1:boxcolor=black@0.5:boxborderw=10:enable='between(t\\,${sub.startSec}\\,${sub.endSec})'`;
      });

      Ffmpeg()
        .input(bgPath).inputOptions(["-loop 1"])
        .input(audioPath)
        .videoFilter([`scale=1080:1080`, ...subtitleFilters])
        .outputOptions([`-t ${audioDuration}`, "-c:v libx264", "-c:a aac", "-pix_fmt yuv420p", "-r 30", "-shortest"])
        .output(tmpOutput)
        .on("end", () => resolve())
        .on("error", (err) => reject(new Error(`ffmpeg 오류: ${err.message}`)))
        .run();
    });

    const finalDir = ensurePublicDir();
    const finalPath = path.join(finalDir, outputFilename);
    fs.copyFileSync(tmpOutput, finalPath);

    return `/generated-videos/${outputFilename}`;
  } finally {
    fs.rmSync(tmpDir, { recursive: true, force: true });
  }
}
