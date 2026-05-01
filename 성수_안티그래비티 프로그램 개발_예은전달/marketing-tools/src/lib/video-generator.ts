import ffmpegStatic from "ffmpeg-static";
import Ffmpeg from "fluent-ffmpeg";
import fs from "fs";
import path from "path";
import OpenAI from "openai";

if (ffmpegStatic) Ffmpeg.setFfmpegPath(ffmpegStatic);

const KOREAN_FONT = "C:/Windows/Fonts/malgun.ttf";
const FALLBACK_FONT = "C:/Windows/Fonts/arial.ttf";

function getFont(): string {
  return fs.existsSync(KOREAN_FONT) ? KOREAN_FONT : FALLBACK_FONT;
}

export function ensureDir(dir: string) {
  fs.mkdirSync(dir, { recursive: true });
}

async function downloadImage(url: string, dest: string): Promise<void> {
  const res = await fetch(url);
  const buf = await res.arrayBuffer();
  fs.writeFileSync(dest, Buffer.from(buf));
}

function escapeDrawtext(text: string): string {
  return text.replace(/'/g, "’").replace(/:/g, "\\:").replace(/\[/g, "\\[").replace(/\]/g, "\\]");
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
  const dir = path.join(process.cwd(), "public", "generated-videos");
  const tmpDir = path.join(dir, "tmp_" + Date.now());
  ensureDir(tmpDir);
  ensureDir(dir);

  const font = getFont();
  const imagePaths: string[] = [];

  // 이미지 생성 + 다운로드
  for (let i = 0; i < slides.length; i++) {
    const slide = slides[i];
    const imgRes = await openai.images.generate({
      model: "dall-e-3",
      prompt: `${slide.imagePrompt}. Clean Korean advertisement background, professional, high quality, no text, no watermarks, Instagram square format.`,
      size: "1024x1024",
      quality: "standard",
      n: 1,
    });
    const imgUrl = (imgRes.data ?? [])[0]?.url ?? "";
    const imgPath = path.join(tmpDir, `slide_${i}.png`);
    await downloadImage(imgUrl, imgPath);
    imagePaths.push(imgPath);
  }

  const outputPath = path.join(dir, outputFilename);

  // ffmpeg로 슬라이드쇼 조합
  await new Promise<void>((resolve, reject) => {
    const cmd = Ffmpeg();

    // 각 이미지를 duration초짜리 클립으로
    slides.forEach((_, i) => cmd.input(imagePaths[i]).inputOptions(["-loop 1", `-t ${slides[i].duration}`]));

    // 필터 체인 구성
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
      .output(outputPath)
      .on("end", () => resolve())
      .on("error", (err) => reject(err))
      .run();
  });

  // tmp 정리
  fs.rmSync(tmpDir, { recursive: true, force: true });

  return `/generated-videos/${outputFilename}`;
}

// C타입: 나레이션 영상 생성
export async function generateVoiceoverVideo(
  script: string,
  subtitles: Subtitle[],
  imagePrompt: string,
  outputFilename: string
): Promise<string> {
  const openai = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });
  const dir = path.join(process.cwd(), "public", "generated-videos");
  const tmpDir = path.join(dir, "tmp_" + Date.now());
  ensureDir(tmpDir);
  ensureDir(dir);

  const font = getFont();

  // 1. 배경 이미지 생성
  const imgRes = await openai.images.generate({
    model: "dall-e-3",
    prompt: `${imagePrompt}. Clean professional Korean advertisement background, no text, no people, soft gradient, high quality.`,
    size: "1024x1024",
    quality: "standard",
    n: 1,
  });
  const imgUrl = (imgRes.data ?? [])[0]?.url ?? "";
  const bgPath = path.join(tmpDir, "background.png");
  await downloadImage(imgUrl, bgPath);

  // 2. TTS 나레이션 생성
  const ttsResponse = await openai.audio.speech.create({
    model: "tts-1",
    voice: "nova",
    input: script,
    response_format: "mp3",
  });
  const audioPath = path.join(tmpDir, "narration.mp3");
  const audioBuffer = Buffer.from(await ttsResponse.arrayBuffer());
  fs.writeFileSync(audioPath, audioBuffer);

  // 3. 오디오 길이 확인
  const audioDuration = await new Promise<number>((resolve, reject) => {
    Ffmpeg.ffprobe(audioPath, (err, meta) => {
      if (err) reject(err);
      else resolve(meta.format.duration ?? 20);
    });
  });

  const outputPath = path.join(dir, outputFilename);

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
      .outputOptions([
        `-t ${audioDuration}`,
        "-c:v libx264",
        "-c:a aac",
        "-pix_fmt yuv420p",
        "-r 30",
        "-shortest",
      ])
      .output(outputPath)
      .on("end", () => resolve())
      .on("error", (err) => reject(err))
      .run();
  });

  fs.rmSync(tmpDir, { recursive: true, force: true });

  return `/generated-videos/${outputFilename}`;
}
