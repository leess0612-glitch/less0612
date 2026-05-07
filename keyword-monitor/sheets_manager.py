"""
구글시트 연동 - Apps Script 웹앱 방식
랜딩페이지와 동일한 방식 (credentials.json 불필요)
"""
import requests
import config


def _post(payload: dict) -> bool:
    if not config.GOOGLE_SCRIPT_URL:
        print("[sheets] URL 미설정 → 건너뜀")
        return False
    try:
        resp = requests.post(config.GOOGLE_SCRIPT_URL, json=payload, timeout=15, allow_redirects=True)
        result = resp.json()
        if result.get("status") == "ok":
            return True
        print(f"[sheets] 오류: {result.get('message')}")
        return False
    except Exception as e:
        print(f"[sheets] 연결 실패: {e}")
        return False


def write_exposure(results: list[dict]):
    """노출 체크 결과 → '노출현황' 시트"""
    rows = []
    for r in results:
        if r.get("our_exposure"):
            for e in r["our_exposure"]:
                rows.append([
                    r["date"], r["category"], r["keyword"],
                    "O",
                    e.get("block_name", ""),
                    e.get("block_position", ""),
                    e.get("rank_in_block", ""),
                    e.get("channel_id", ""),
                    e.get("type", ""),
                ])
        else:
            rows.append([r["date"], r["category"], r["keyword"], "X", "", "", "", "", ""])

    ok = _post({"type": "exposure", "rows": rows})
    if ok:
        print(f"[sheets] 노출현황 {len(rows)}행 기록 완료")


def _to_int(val):
    try:
        return int(val)
    except (ValueError, TypeError):
        s = str(val).replace(",", "").strip()
        if s.startswith("<"):
            try:
                return int(s[1:].strip()) - 1
            except ValueError:
                return 0
        return 0


def write_keywords(category: str, groups: dict):
    """수집 키워드 → '키워드_카테고리' 시트"""
    rows = []
    for group, kws in groups.items():
        for k in kws:
            rows.append([
                group,
                k.get("relKeyword", ""),
                _to_int(k.get("monthlyPcQcCnt", 0)),
                _to_int(k.get("monthlyMobileQcCnt", 0)),
                k.get("compIdx", ""),
            ])

    ok = _post({"type": "keywords", "category": category, "rows": rows})
    if ok:
        print(f"[sheets] 키워드_{category} {len(rows)}행 기록 완료")
