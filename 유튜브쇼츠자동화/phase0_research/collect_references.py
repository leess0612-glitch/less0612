"""
Phase 0' - 레퍼런스 영상 자동 수집
휴대폰 IT/이슈/밈 카테고리의 쇼츠 중 조회수가 높은 영상을 yt-dlp 검색으로 모아서
메타데이터 + 자막을 references/raw/ 에 저장한다. (공식 API 키 불필요)
"""
import json
import re
from pathlib import Path

import yt_dlp
from youtube_transcript_api import YouTubeTranscriptApi

BASE_DIR = Path(__file__).parent
RAW_DIR = BASE_DIR / "references" / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)

# 검색 키워드 목록 (휴대폰 IT/이슈/밈 카테고리)
KEYWORDS = [
    "아이폰 밈 쇼츠",
    "휴대폰 IT 이슈 쇼츠",
    "스마트폰 꿀팁 쇼츠",
    "갤럭시 아이폰 비교 쇼츠",
]

SEARCH_COUNT_PER_KEYWORD = 15
MAX_SHORTS_DURATION_SEC = 90  # 쇼츠로 간주할 최대 길이
TOP_N_BY_VIEWS = 12  # 최종 분석 대상으로 추릴 개수


def search_videos(keyword: str, count: int):
    query = f"ytsearch{count}:{keyword}"
    ydl_opts = {
        "quiet": True,
        "skip_download": True,
        "extract_flat": False,
        "noplaylist": True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(query, download=False)
    return info.get("entries", []) or []


def safe_filename(text: str) -> str:
    return re.sub(r'[\\/:*?"<>|]', "_", text)[:60]


def fetch_transcript(video_id: str) -> str | None:
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=["ko", "en"])
        return "\n".join(seg["text"] for seg in transcript)
    except Exception:
        return None


def main():
    seen_ids = set()
    collected = []

    for kw in KEYWORDS:
        print(f"[검색] '{kw}' ...")
        try:
            entries = search_videos(kw, SEARCH_COUNT_PER_KEYWORD)
        except Exception as e:
            print(f"  검색 실패: {e}")
            continue

        for entry in entries:
            if not entry:
                continue
            vid = entry.get("id")
            duration = entry.get("duration") or 0
            if not vid or vid in seen_ids:
                continue
            if duration == 0 or duration > MAX_SHORTS_DURATION_SEC:
                continue
            seen_ids.add(vid)
            collected.append({
                "id": vid,
                "title": entry.get("title", ""),
                "channel": entry.get("channel") or entry.get("uploader", ""),
                "view_count": entry.get("view_count") or 0,
                "like_count": entry.get("like_count") or 0,
                "duration": duration,
                "url": f"https://www.youtube.com/watch?v={vid}",
                "keyword": kw,
            })

    collected.sort(key=lambda x: x["view_count"], reverse=True)
    top = collected[:TOP_N_BY_VIEWS]

    print(f"\n총 {len(collected)}개 후보 중 조회수 상위 {len(top)}개 선정\n")

    index = []
    for v in top:
        print(f"- ({v['view_count']:>10,}회) {v['title']}  [{v['url']}]")
        transcript = fetch_transcript(v["id"])

        md_lines = [
            f"# {v['title']}",
            "",
            f"- 채널: {v['channel']}",
            f"- 조회수: {v['view_count']:,}",
            f"- 좋아요: {v['like_count']:,}",
            f"- 길이: {v['duration']}초",
            f"- URL: {v['url']}",
            f"- 검색 키워드: {v['keyword']}",
            "",
            "## 자막/스크립트",
            "",
            transcript if transcript else "(자막 추출 실패 - 자동 자막 없음. 수동 확인 필요)",
        ]

        filename = f"{v['view_count']:010d}_{safe_filename(v['title'])}.md"
        out_path = RAW_DIR / filename
        out_path.write_text("\n".join(md_lines), encoding="utf-8")
        index.append({**v, "transcript_collected": transcript is not None, "file": filename})

    (BASE_DIR / "references" / "index.json").write_text(
        json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"\n완료: {RAW_DIR} 에 {len(top)}개 파일 저장, references/index.json 생성")


if __name__ == "__main__":
    main()
