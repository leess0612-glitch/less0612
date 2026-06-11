import asyncio
import shutil
from pathlib import Path
from playwright.async_api import async_playwright
from playwright_stealth import Stealth

PROFILE = Path(__file__).parent / '_test_profile_wd'
ARGS = [
    '--disable-blink-features=AutomationControlled',
    '--no-first-run',
    '--no-default-browser-check',
]


async def check(label, with_manual_override):
    if PROFILE.exists():
        shutil.rmtree(PROFILE)
    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir=str(PROFILE), channel='chrome', headless=True, args=ARGS, no_viewport=True
        )
        if with_manual_override:
            await context.add_init_script("Object.defineProperty(navigator,'webdriver',{get:()=>undefined})")
        await Stealth().apply_stealth_async(context)
        page = context.pages[0] if context.pages else await context.new_page()
        await page.goto('https://example.com')
        wd = await page.evaluate('navigator.webdriver')
        own = await page.evaluate("navigator.hasOwnProperty('webdriver')")
        proto_desc = await page.evaluate("""() => {
            const d = Object.getOwnPropertyDescriptor(Object.getPrototypeOf(navigator), 'webdriver');
            return d ? {configurable: d.configurable, hasGet: typeof d.get} : null;
        }""")
        print(f"[{label}] navigator.webdriver = {wd!r}, hasOwnProperty('webdriver') = {own}, proto descriptor = {proto_desc}")
        await context.close()
    shutil.rmtree(PROFILE, ignore_errors=True)


async def main():
    await check("WITHOUT manual override", with_manual_override=False)
    await check("WITH manual override (current code)", with_manual_override=True)


asyncio.run(main())
