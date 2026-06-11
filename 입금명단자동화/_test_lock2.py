import asyncio
from playwright.async_api import async_playwright
import naver_post as np


async def hold():
    async with async_playwright() as p:
        ctx = await p.chromium.launch_persistent_context(
            user_data_dir=str(np.PROFILE_DIR), channel='chrome', headless=True, args=['--no-first-run']
        )
        await asyncio.sleep(5)
        await ctx.close()


async def try_second():
    await asyncio.sleep(1.5)
    async with async_playwright() as p:
        try:
            context = await np._new_context(p, headless=True)
            print("SECOND LAUNCH SUCCEEDED (unexpected)")
            await context.close()
        except Exception as e:
            print("formatted:", np._format_launch_error(e))


async def main():
    await asyncio.gather(hold(), try_second())


asyncio.run(main())
