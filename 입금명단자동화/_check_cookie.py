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

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, args=['--disable-blink-features=AutomationControlled'])
        context = await browser.new_context(user_agent=_USER_AGENT)
        await context.add_init_script("Object.defineProperty(navigator,'webdriver',{get:()=>undefined})")
        with open(COOKIE_PATH, encoding='utf-8') as f:
            cookies = json.load(f)
        print(f"쿠키 {len(cookies)}개 로드, 만료시각 샘플:", [(c['name'], c.get('expires')) for c in cookies if c['name'] in ('NID_AUT', 'NID_SES')])
        try:
            await context.add_cookies(cookies)
        except Exception as e:
            print("ADD_COOKIES ERROR:", e)
        page = await context.new_page()
        page.on("framenavigated", lambda f: print("NAV:", f.url))
        page.on("close", lambda: print("PAGE CLOSED"))
        page.on("crash", lambda: print("PAGE CRASHED"))
        context.on("page", lambda pg: print("NEW PAGE OPENED:", pg.url))

        try:
            resp = await page.goto(write_url, wait_until='load', timeout=30000)
            print("GOTO STATUS:", resp.status if resp else None)
            print("URL right after goto:", page.url)
        except Exception as e:
            print("GOTO ERROR:", e)

        for i in range(6):
            await page.wait_for_timeout(1000)
            print(f"  +{i+1}s URL:", page.url)

        print("PAGES IN CONTEXT:", [pg.url for pg in context.pages])
        if 'nidlogin' in page.url or 'login' in page.url:
            print("RESULT: 만료 (로그인 페이지로 리다이렉트됨)")
        else:
            el = await page.query_selector('textarea.textarea_input, button.button')
            print("RESULT:", "유효 (글쓰기 화면 정상 로드)" if el else "판단불가 (요소 없음)")
        await browser.close()


asyncio.run(main())
