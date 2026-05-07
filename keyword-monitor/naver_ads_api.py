"""
네이버 검색광고 API - 연관 키워드 확장
광고주센터 API 키 발급 후 사용 가능
docs: https://naver.github.io/searchad-apidoc/
"""
import hashlib
import hmac
import base64
import time
import requests

import config

BASE_URL = "https://api.naver.com"


def _make_signature(timestamp: str, method: str, path: str) -> str:
    message = f"{timestamp}.{method}.{path}"
    raw = hmac.new(
        config.NAVER_ADS_SECRET_KEY.encode('utf-8'),
        message.encode('utf-8'),
        digestmod=hashlib.sha256
    ).digest()
    return base64.b64encode(raw).decode('utf-8')


def _headers(method: str, path: str) -> dict:
    ts = str(int(time.time() * 1000))
    return {
        'Content-Type':  'application/json; charset=UTF-8',
        'X-Timestamp':   ts,
        'X-API-KEY':     config.NAVER_ADS_ACCESS_LICENSE,
        'X-Customer':    str(config.NAVER_ADS_CUSTOMER_ID),
        'X-Signature':   _make_signature(ts, method, path),
    }


def get_related_keywords(seed_keywords: list[str]) -> list[dict]:
    """
    씨앗 키워드로 연관키워드 + 검색량 + 경쟁도 조회
    5개씩 나눠서 요청 후 중복 제거하여 반환
    """
    if not config.NAVER_ADS_CUSTOMER_ID:
        print("[naver_ads_api] API 키 미설정 → 건너뜀")
        return []

    path = '/keywordstool'
    seen = {}

    for i in range(0, len(seed_keywords), 5):
        batch = seed_keywords[i:i+5]
        params = {
            'hintKeywords': ','.join(batch),
            'showDetail':   '1',
        }
        resp = requests.get(
            BASE_URL + path,
            headers=_headers('GET', path),
            params=params,
            timeout=15
        )
        resp.raise_for_status()
        for kw in resp.json().get('keywordList', []):
            key = kw.get('relKeyword', '')
            if key not in seen:
                seen[key] = kw

    return list(seen.values())


def filter_keywords(raw_list: list[dict],
                    min_mobile: int = 0,
                    max_mobile: int = 9_999_999) -> list[dict]:
    """
    3단계 필터 적용 후 모바일 검색량 내림차순 정렬

    1) 글자 수: config.FILTER_MAX_EXCLUDE_CHARS 이하 제외
       - 기본값 3 → 3글자 이하 제외 (config.py에서 숫자만 바꾸면 됨)

    2) 단독 브랜드명: config.BRAND_NAMES 에 있는 키워드 제외
       - "코웨이" → 제외 / "코웨이정수기렌탈" → 유지
       - config.py BRAND_NAMES 목록에 추가·삭제

    3) 모바일 검색량: min_mobile ~ max_mobile 범위 외 제외
    """
    import json, os
    _s = json.load(open('settings.json', encoding='utf-8')) if os.path.exists('settings.json') else {}
    brand_set = {b.lower() for b in _s.get('brand_names', [])}
    max_chars = _s.get('filter_max_exclude_chars', 3)

    def _to_int(val):
        try:
            return int(val)
        except (ValueError, TypeError):
            return 0  # '< 10' 등 문자열은 0으로 처리

    filtered = []
    for k in raw_list:
        kw = k.get('relKeyword', '')
        mobile_cnt = _to_int(k.get('monthlyMobileQcCnt', 0))

        # 1) 글자 수 필터
        if len(kw) <= max_chars:
            continue

        # 2) 단독 브랜드명 필터 (정확히 일치하는 것만 제외)
        if kw.lower() in brand_set:
            continue

        # 3) 검색량 필터
        if not (min_mobile <= mobile_cnt <= max_mobile):
            continue

        filtered.append(k)

    return sorted(filtered, key=lambda k: _to_int(k.get('monthlyMobileQcCnt', 0)), reverse=True)


def group_keywords(raw_list: list[dict]) -> dict:
    """
    전체 연관키워드를 3개 그룹으로 자동 분류

    A그룹 (고볼륨)  : 모바일 1,000 이상
    B그룹 (중볼륨)  : 모바일 300 ~ 999
    C그룹 (저볼륨)  : 모바일 300 미만
    """
    def _to_int(val):
        try:
            return int(val)
        except (ValueError, TypeError):
            return 0

    groups = {'A_고볼륨': [], 'B_중볼륨': [], 'C_저볼륨': []}
    for k in raw_list:
        cnt = _to_int(k.get('monthlyMobileQcCnt', 0))
        if cnt >= 1000:
            groups['A_고볼륨'].append(k)
        elif cnt >= 300:
            groups['B_중볼륨'].append(k)
        else:
            groups['C_저볼륨'].append(k)
    return groups
