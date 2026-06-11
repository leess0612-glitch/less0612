import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

PROFILE = str(Path(__file__).parent / '_test_profile')


async def hold():
    async with async_playwright() as p:
        ctx = await p.chromium.launch_persistent_context(
            user_data_dir=PROFILE, channel='chrome', headless=True, args=['--no-first-run']
        )
        await asyncio.sleep(5)
        await ctx.close()


async def try_second():
    await asyncio.sleep(1.5)
    async with async_playwright() as p:
        try:
            ctx2 = await p.chromium.launch_persistent_context(
                user_data_dir=PROFILE, channel='chrome', headless=True, args=['--no-first-run']
            )
            print("SECOND LAUNCH SUCCEEDED (unexpected)")
            await ctx2.close()
        except Exception as e:
            print("EXCEPTION TYPE:", type(e))
            print("EXCEPTION MSG:", repr(str(e)))


async def main():
    await asyncio.gather(hold(), try_second())


asyncio.run(main())
