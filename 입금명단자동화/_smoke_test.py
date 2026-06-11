import asyncio
from playwright.async_api import async_playwright
from naver_post import _new_context, PROFILE_DIR


async def main():
    async with async_playwright() as p:
        context = await _new_context(p, headless=True)
        page = context.pages[0] if context.pages else await context.new_page()
        await page.goto('https://example.com')
        print('title:', await page.title())
        print('webdriver:', await page.evaluate('navigator.webdriver'))
        await context.close()
    print('profile dir exists:', PROFILE_DIR.exists())


asyncio.run(main())
