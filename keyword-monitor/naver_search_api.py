"""
네이버 오픈 API - 블로그/카페 검색
네이버 개발자센터 앱 등록 후 무료 사용 (일 25,000회)
https://developers.naver.com
"""
import requests
import config


def _headers() -> dict:
    return {
        'X-Naver-Client-Id':     config.NAVER_OPEN_CLIENT_ID,
        'X-Naver-Client-Secret': config.NAVER_OPEN_CLIENT_SECRET,
    }


def _available() -> bool:
    if not config.NAVER_OPEN_CLIENT_ID:
        print("[naver_search_api] API 키 미설정 → 건너뜀")
        return False
    return True


def search_blog(query: str, display: int = 20) -> list[dict]:
    """블로그 탭 검색 결과 반환 (link, title, description, bloggername)"""
    if not _available():
        return []
    resp = requests.get(
        'https://openapi.naver.com/v1/search/blog.json',
        headers=_headers(),
        params={'query': query, 'display': display, 'sort': 'sim'},
        timeout=10
    )
    resp.raise_for_status()
    return resp.json().get('items', [])


def search_cafe(query: str, display: int = 20) -> list[dict]:
    """카페 탭 검색 결과 반환 (link, title, description, cafename)"""
    if not _available():
        return []
    resp = requests.get(
        'https://openapi.naver.com/v1/search/cafearticle.json',
        headers=_headers(),
        params={'query': query, 'display': display, 'sort': 'sim'},
        timeout=10
    )
    resp.raise_for_status()
    return resp.json().get('items', [])


def check_channel_exposure(query: str, channels: dict) -> list[dict]:
    """
    오픈 API 기준 블로그+카페 탭에서 우리 채널 노출 순위 확인
    (통합검색 순위와 다를 수 있음 - 보조 데이터로 활용)
    """
    if not _available():
        return []

    our_blogs = {c['id'].lower() for c in channels.get('blog', [])}
    our_cafes = {c['id'].lower() for c in channels.get('cafe', [])}
    found = []

    for rank, item in enumerate(search_blog(query), 1):
        link = item.get('link', '')
        for ch_id in our_blogs:
            if ch_id in link.lower():
                found.append({
                    'source': 'open_api_blog', 'channel_id': ch_id,
                    'rank': rank, 'title': item.get('title', ''), 'link': link
                })

    for rank, item in enumerate(search_cafe(query), 1):
        link = item.get('link', '')
        for ch_id in our_cafes:
            if ch_id in link.lower():
                found.append({
                    'source': 'open_api_cafe', 'channel_id': ch_id,
                    'rank': rank, 'title': item.get('title', ''), 'link': link
                })

    return found
