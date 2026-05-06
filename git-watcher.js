const chokidar = require("C:/Users/a/Desktop/안티그라비티/성수_안티그래비티 프로그램 개발_예은전달/marketing-tools/node_modules/chokidar");
const { execSync } = require("child_process");
const path = require("path");

const WATCH_PATH = "C:/Users/a/Desktop/안티그라비티";
const DEBOUNCE_MS = 8000; // 마지막 변경 후 8초 대기

const IGNORE = [
  /[/\\]\.git[/\\]/,
  /[/\\]node_modules[/\\]/,
  /[/\\]\.next[/\\]/,
  /__pycache__/,
  /\.pyc$/,
  /git-watcher\.js$/,
  /auto-commit-watcher\.ps1$/,
  /Thumbs\.db$/,
];

let debounceTimer = null;
let lastPath = "";

function shouldIgnore(filePath) {
  return IGNORE.some((p) => p.test(filePath));
}

function tryCommit() {
  try {
    const status = execSync("git status --porcelain", { cwd: WATCH_PATH, encoding: "utf8" }).trim();
    if (!status) {
      console.log("[watcher] 변경사항 없음 - 스킵");
      return;
    }
    const dateStr = new Date().toLocaleString("ko-KR", { timeZone: "Asia/Seoul" });
    execSync("git add -A", { cwd: WATCH_PATH });
    execSync(`git commit -m "auto: ${dateStr}"`, { cwd: WATCH_PATH });
    execSync("git push origin main", { cwd: WATCH_PATH });
    console.log(`[watcher] 커밋+푸시 완료: ${dateStr}`);
  } catch (err) {
    console.error("[watcher] 오류:", err.message);
  }
}

function onFileChange(filePath) {
  if (shouldIgnore(filePath)) return;
  lastPath = filePath;
  console.log(`[watcher] 변경 감지: ${path.relative(WATCH_PATH, filePath)}`);

  if (debounceTimer) clearTimeout(debounceTimer);
  debounceTimer = setTimeout(() => {
    console.log("[watcher] 디바운스 완료 → 커밋 시작");
    tryCommit();
    debounceTimer = null;
  }, DEBOUNCE_MS);
}

const watcher = chokidar.watch(WATCH_PATH, {
  ignored: IGNORE,
  persistent: true,
  ignoreInitial: true,
  depth: 10,
  awaitWriteFinish: { stabilityThreshold: 1000, pollInterval: 200 },
});

watcher
  .on("add", onFileChange)
  .on("change", onFileChange)
  .on("unlink", onFileChange)
  .on("addDir", onFileChange)
  .on("unlinkDir", onFileChange)
  .on("ready", () => console.log(`[watcher] 감시 시작: ${WATCH_PATH}`))
  .on("error", (err) => console.error("[watcher] 감시 오류:", err));

process.on("SIGINT", () => { watcher.close(); process.exit(0); });
process.on("SIGTERM", () => { watcher.close(); process.exit(0); });
