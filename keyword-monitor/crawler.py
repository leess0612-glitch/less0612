"""
네이버 통합검색 크롤러
- 1단계: 채널 ID 매칭 (등록된 채널)
- 2단계: 본문 텍스트 매칭 (exposure_keywords 포함 여부)
"""
import asyncio
import json
import re
import random
from datetime import datetime
from urllib.parse import quote
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

import config


_BLOG_RE = re.compile(r'https?://(?:m\.)?blog\.naver\.com/([A-Za-z0-9_.-]+)', re.I)
_CAFE_RE = re.compile(r'https?://(?:m\.)?cafe\.naver\.com/([A-Za-z0-9_.-]+)', re.I)
_CAFE_BLACKLIST = {'articleread', 'commentview', 'search', 'cafemain', 'articlelist'}

_KNOWN_BLOCK_NAMES = [
    '인기글', '최신글', '블로그', '카페', '뷰', '인플루언서',
    '지식iN', '쇼핑', '뉴스', '이미지', '동영상', '웹사이트',
]
_SECTION_CLASS_HINTS = [
    'sc_new', 'sc_section', 'api_nbox_cont',
    'lst_total', 'type_section', 'col_type', 'section_blog', 'section_cafe',
]


def _find_block_title(el) -> str:
    for sel in ['.sct_title', '.sc_tit', '.title_area', '.tit_area',
                '.area_title', 'strong.tit', 'span.tit', '.lst_tit', 'h2', 'h3']:
        t = el.select_one(sel)
        if t:
            text = t.get_text(strip=True)
            if text and len(text) <= 15:
                return text
    full_text = el.get_text(' ', strip=True)
    for name in _KNOWN_BLOCK_NAMES:
        if full_text.lstrip().startswith(name):
            return name
    return '기타'


def parse_results(html: str) -> list[dict]:
    """
    통합검색 HTML → 블록 목록
    각 item에 url 포함 (본문 체크에 사용)
    """
    soup = BeautifulSoup(html, 'html.parser')
    all_bx = soup.find_all('div', class_='api_subject_bx')
    if not all_bx:
        return []

    seen_sections: dict[int, int] = {}
    sections: list[dict] = []

    for bx in all_bx:
        ancestor = bx.parent
        section_el = None
        for _ in range(10):
            if ancestor is None or ancestor.name in ('body', '[document]'):
                break
            classes = ' '.join(ancestor.get('class', []))
            if any(hint in classes for hint in _SECTION_CLASS_HINTS):
                section_el = ancestor
                break
            ancestor = ancestor.parent
        if section_el is None:
            section_el = bx.parent

        sid = id(section_el)
        if sid not in seen_sections:
            seen_sections[sid] = len(sections)
            sections.append({'el': section_el, 'bx_list': []})
        sections[seen_sections[sid]]['bx_list'].append(bx)

    blocks: list[dict] = []
    for pos, sec in enumerate(sections, 1):
        block_name = _find_block_title(sec['el'])
        items: list[dict] = []

        for rank, bx in enumerate(sec['bx_list'], 1):
            blog_links = bx.find_all('a', href=_BLOG_RE)
            cafe_links = bx.find_all('a', href=_CAFE_RE)

            if blog_links:
                href = blog_links[0]['href']
                m = _BLOG_RE.search(href)
                if m:
                    items.append({
                        'rank':  rank,
                        'type':  'blog',
                        'id':    m.group(1).lower(),
                        'url':   href,
                        'title': bx.get_text(' ', strip=True)[:60],
                    })
            elif cafe_links:
                href = cafe_links[0]['href']
                m = _CAFE_RE.search(href)
                if m:
                    ch_id = m.group(1).lower()
                    if ch_id not in _CAFE_BLACKLIST:
                        items.append({
                            'rank':  rank,
                            'type':  'cafe',
                            'id':    ch_id,
                            'url':   href,
                            'title': bx.get_text(' ', strip=True)[:60],
                        })

        if items:
            blocks.append({
                'block_name':     block_name,
                'block_position': pos,
                'items':          items,
            })

    return blocks


def check_exposure_by_channel(blocks: list[dict], channels: dict) -> list[dict]:
    """1단계: 등록된 채널 ID로 노출 확인"""
    our = {
        'blog': {c['id'].lower() for c in channels.get('blog', [])},
        'cafe': {c['id'].lower() for c in channels.get('cafe', [])},
    }
    found = []
    for block in blocks:
        for item in block['items']:
            if item['id'] in our.get(item['type'], set()):
                found.append({
                    'type':            item['type'],
                    'channel_id':      item['id'],
                    'block_name':      block['block_name'],
                    'block_position':  block['block_position'],
                    'rank_in_block':   item['rank'],
                    'title':           item['title'],
                    'source':          'channel',
                    'matched_keyword': None,
                })
    return found


async def fetch_page_text(page, url: str) -> str:
    """URL 방문 후 본문 + 동일도메인 iframe 텍스트 반환"""
    try:
        await page.goto(url, wait_until='domcontentloaded', timeout=15000)
        await asyncio.sleep(1.5)

        text = await page.inner_text('body')

        # 네이버 블로그 iframe 본문 추가 수집
        for frame in page.frames[1:]:
            try:
                if 'naver.com' in frame.url:
                    text += ' ' + await frame.inner_text('body')
            except Exception:
                pass

        return text
    except Exception:
        return ''


async def check_exposure_by_content(
    page,
    blocks: list[dict],
    already_found: set[tuple],
    exposure_keywords: list[str],
) -> list[dict]:
    """
    2단계: 채널 매칭 안 된 항목의 본문에서 exposure_keywords 검색
    already_found: {(channel_id, block_position, rank_in_block)} — 중복 방지
    """
    if not exposure_keywords:
        return []

    found = []
    for block in blocks:
        for item in block['items']:
            key = (item['id'], block['block_position'], item['rank'])
            if key in already_found:
                continue
            if not item.get('url'):
                continue

            text = await fetch_page_text(page, item['url'])
            for kw in exposure_keywords:
                if kw in text:
                    found.append({
                        'type':            item['type'],
                        'channel_id':      item['id'],
                        'block_name':      block['block_name'],
                        'block_position':  block['block_position'],
                        'rank_in_block':   item['rank'],
                        'title':           item['title'],
                        'source':          'content',
                        'matched_keyword': kw,
                    })
                    break

            await asyncio.sleep(random.uniform(1.0, 2.0))

    return found


async def run_check(keywords_data: dict, channels: dict) -> list[dict]:
    """전체 키워드 순회 → 채널 매칭 + 본문 매칭 → 결과 반환"""
    today = datetime.now().strftime('%Y-%m-%d')

    try:
        with open('settings.json', encoding='utf-8') as f:
            settings = json.load(f)
        exposure_keywords = settings.get('exposure_keywords', [])
    except Exception:
        exposure_keywords = []

    print(f"노출 확인 키워드: {exposure_keywords}")

    active_list = [
        (cat, kw['keyword'])
        for cat, kws in keywords_data.items()
        for kw in kws
        if kw.get('active', True)
    ]
    total = len(active_list)
    all_results = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=config.HEADLESS,
            args=['--lang=ko-KR']
        )
        context = await browser.new_context(
            locale='ko-KR',
            user_agent=(
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/124.0.0.0 Safari/537.36'
            )
        )
        page = await context.new_page()

        for idx, (category, keyword) in enumerate(active_list, 1):
            print(f"[{idx}/{total}] [{category}] {keyword} 검색 중...", flush=True)
            result = None
            error_msg = None
            try:
                # ── 1단계: 통합검색 ──────────────────────────
                url = f"https://search.naver.com/search.naver?query={quote(keyword)}"
                await page.goto(url, wait_until='networkidle', timeout=20000)
                await asyncio.sleep(random.uniform(2, 3))

                html = await page.content()
                blocks = parse_results(html)

                # ── 2단계: 채널 ID 매칭 ──────────────────────
                exposure = check_exposure_by_channel(blocks, channels)

                # ── 3단계: 본문 키워드 매칭 ──────────────────
                if exposure_keywords:
                    already_found = {
                        (e['channel_id'], e['block_position'], e['rank_in_block'])
                        for e in exposure
                    }
                    items_to_check = sum(
                        1 for b in blocks for item in b['items']
                        if (item['id'], b['block_position'], item['rank']) not in already_found
                        and item.get('url')
                    )
                    if items_to_check:
                        print(f"  [본문확인] {items_to_check}개 항목 본문 확인 중...", flush=True)
                    content_exposure = await check_exposure_by_content(
                        page, blocks, already_found, exposure_keywords
                    )
                    if content_exposure:
                        print(f"  [본문매칭] {len(content_exposure)}개 추가 발견", flush=True)
                    exposure.extend(content_exposure)

                result = {
                    'date':         today,
                    'category':     category,
                    'keyword':      keyword,
                    'blocks':       blocks,
                    'our_exposure': exposure,
                    'exposed':      len(exposure) > 0,
                    'best_rank':    min(e['rank_in_block'] for e in exposure) if exposure else None,
                    'best_block':   min(e['block_position'] for e in exposure) if exposure else None,
                }

                if exposure:
                    summary = ', '.join(
                        f"{e['block_name']}(블록{e['block_position']}위/{e['rank_in_block']}번째"
                        f"{'·' + e['matched_keyword'] if e.get('matched_keyword') else ''})"
                        for e in exposure
                    )
                    print(f"  [노출] {summary}")
                else:
                    print("  [미노출]")

            except Exception as exc:
                error_msg = str(exc)
                print(f"  [오류] {exc}")

            if result is not None:
                all_results.append(result)
            else:
                all_results.append({
                    'date': today, 'category': category, 'keyword': keyword,
                    'error': error_msg or '알 수 없는 오류',
                    'exposed': False, 'best_rank': None, 'best_block': None,
                    'our_exposure': [], 'blocks': [],
                })

            if idx < total:
                delay = random.uniform(config.CRAWL_DELAY_MIN, config.CRAWL_DELAY_MAX)
                print(f"  → {delay:.0f}초 대기...", flush=True)
                await asyncio.sleep(delay)

        await browser.close()

    return all_results
