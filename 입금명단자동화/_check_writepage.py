import asyncio
import sys
from pathlib import Path
from playwright.async_api import async_playwright

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

sys.path.insert(0, str(Path(__file__).parent))
from naver_post import _load_cookies, _is_logged_in, _LAUNCH_ARGS, _USER_AGENT

BASE_DIR = Path(__file__).parent


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, args=_LAUNCH_ARGS)
        context = await browser.new_context(user_agent=_USER_AGENT)
        await context.add_init_script("Object.defineProperty(navigator,'webdriver',{get:()=>undefined})")
        page = await context.new_page()

        has_cookie = await _load_cookies(context)
        print("쿠키 로드:", has_cookie)

        logged_in = await _is_logged_in(page)
        print("_is_logged_in() 결과:", logged_in)
        print("최종 URL:", page.url)
        await page.screenshot(path=str(BASE_DIR / '_check_writepage.png'))

        await browser.close()


asyncio.run(main())
