import asyncio
import json
import sys
from pathlib import Path
from playwright.async_api import async_playwright

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE_DIR = Path(__file__).parent
CONFIG_PATH = BASE_DIR / 'config.json'
COOKIE_PATH = BASE_DIR / 'naver_cookies.json'

_USER_AGENT = (
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
    'AppleWebKit/537.36 (KHTML, like Gecko) '
    'Chrome/125.0.0.0 Safari/537.36'
)


async def main():
    with open(CONFIG_PATH, encoding='utf-8') as f:
        config = json.load(f)
    club_id = config['cafe_clubid']
    menu_id = config['cafe_menuid']
    write_url = f'https://cafe.naver.com/ca-fe/cafes/{club_id}/articles/write?boardType=L&menuId={menu_id}'
    cafe_main_url = f'https://cafe.naver.com/realsportscafe'

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, args=['--disable-blink-features=AutomationControlled'])
        context = await browser.new_context(user_agent=_USER_AGENT)
        await context.add_init_script("Object.defineProperty(navigator,'webdriver',{get:()=>undefined})")

        with open(COOKIE_PATH, encoding='utf-8') as f:
            cookies = json.load(f)
        await context.add_cookies(cookies)
        page = await context.new_page()

        # 1) 네이버 메인 - 로그인 여부 확인
        await page.goto('https://www.naver.com', wait_until='load', timeout=30000)
        await page.wait_for_timeout(2000)
        print("=== 네이버 메인 ===")
        print("URL:", page.url)
        login_link = await page.query_selector('a.MyView-module__link_login___HpHMW, a[href*="nidlogin"]')
        print("로그인 링크 존재(=로그아웃 상태):", login_link is not None)
        await page.screenshot(path=str(BASE_DIR / '_check_1_naver.png'))

        # 2) 카페 메인
        await page.goto(cafe_main_url, wait_until='load', timeout=30000)
        await page.wait_for_timeout(2000)
        print("=== 카페 메인 ===")
        print("URL:", page.url)
        await page.screenshot(path=str(BASE_DIR / '_check_2_cafe.png'))

        # 3) 글쓰기 페이지
        await page.goto(write_url, wait_until='load', timeout=30000)
        await page.wait_for_timeout(3000)
        print("=== 글쓰기 페이지 ===")
        print("URL:", page.url)
        await page.screenshot(path=str(BASE_DIR / '_check_3_write.png'))

        await browser.close()


asyncio.run(main())
