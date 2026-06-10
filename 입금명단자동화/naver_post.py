import asyncio
import json
import sys
from pathlib import Path
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout

BASE_DIR = Path(__file__).parent
CONFIG_PATH = BASE_DIR / 'config.json'
COOKIE_PATH = BASE_DIR / 'naver_cookies.json'

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')


def load_config():
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


async def _save_cookies(context):
    cookies = await context.cookies()
    with open(COOKIE_PATH, 'w', encoding='utf-8') as f:
        json.dump(cookies, f, ensure_ascii=False)
    print("  쿠키 저장 완료")


async def _load_cookies(context) -> bool:
    if not COOKIE_PATH.exists():
        return False
    with open(COOKIE_PATH, 'r', encoding='utf-8') as f:
        cookies = json.load(f)
    await context.add_cookies(cookies)
    return True


async def _is_logged_in(page) -> bool:
    """카페 글쓰기 페이지 접근으로 로그인 상태 확인"""
    config = load_config()
    club_id = config['cafe_clubid']
    menu_id = config['cafe_menuid']
    write_url = f'https://cafe.naver.com/ca-fe/cafes/{club_id}/articles/write?boardType=L&menuId={menu_id}'
    try:
        await page.goto(write_url, wait_until='load', timeout=30000)
        await page.wait_for_timeout(2000)
        if 'nidlogin' in page.url or 'login' in page.url:
            return False
        # 글쓰기 영역이 있으면 로그인 상태
        el = await page.query_selector('textarea.textarea_input, button.button')
        return el is not None
    except Exception:
        return False


def notify_cookie_expired():
    """Windows 알림: 쿠키 만료 안내"""
    try:
        from plyer import notification
        notification.notify(
            title='입금명단 자동화 - 조치 필요',
            message='네이버 쿠키가 만료됐습니다.\npython main.py --refresh-login 을 실행해주세요.',
            timeout=20,
        )
        print("  Windows 알림 발송 완료")
    except Exception as e:
        print(f"  알림 실패: {e}")


# ── 수동 로그인 + 쿠키 저장 ──────────────────────────────────────────────────
_LAUNCH_ARGS = [
    '--disable-blink-features=AutomationControlled',
]
_USER_AGENT = (
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
    'AppleWebKit/537.36 (KHTML, like Gecko) '
    'Chrome/125.0.0.0 Safari/537.36'
)


async def _do_refresh_login():
    print("브라우저가 열립니다. 네이버에 로그인해주세요. (최대 3분 대기)")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, args=_LAUNCH_ARGS)
        context = await browser.new_context(user_agent=_USER_AGENT)
        await context.add_init_script("Object.defineProperty(navigator,'webdriver',{get:()=>undefined})")
        page = await context.new_page()

        await page.goto('https://nid.naver.com/nidlogin.login', wait_until='domcontentloaded')
        await page.bring_to_front()

        print("로그인 완료 후 자동으로 계속됩니다. (최대 3분 대기)")
        try:
            await page.wait_for_url(
                lambda url: 'nidlogin' not in url and 'naver.com' in url,
                timeout=180000
            )
            await _save_cookies(context)
            print("로그인 완료. 이후 자동 실행 가능합니다.")
        except PlaywrightTimeout:
            current_url = page.url
            print(f"  현재 URL: {current_url}")
            if 'naver.com' in current_url and 'nidlogin' not in current_url:
                await _save_cookies(context)
                print("로그인 완료. 이후 자동 실행 가능합니다.")
            else:
                print("로그인 시간 초과 (3분). 다시 시도해주세요.")
        finally:
            await browser.close()


# ── 카페 게시 ────────────────────────────────────────────────────────────────
async def _do_post(image_path: str, title: str) -> tuple[bool, str]:
    config = load_config()
    club_id = config['cafe_clubid']
    menu_id = config['cafe_menuid']
    board_name = config['cafe_board_name']
    write_url = f'https://cafe.naver.com/ca-fe/cafes/{club_id}/articles/write?boardType=L&menuId={menu_id}'

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, args=_LAUNCH_ARGS)
        context = await browser.new_context(user_agent=_USER_AGENT)
        await context.add_init_script("Object.defineProperty(navigator,'webdriver',{get:()=>undefined})")
        page = await context.new_page()

        # 쿠키 로드
        has_cookie = await _load_cookies(context)
        if not has_cookie:
            print("  저장된 쿠키 없음. python main.py --refresh-login 실행 필요")
            await browser.close()
            return False, '쿠키 없음 - 재로그인 필요'

        # 로그인 상태 확인 (글쓰기 페이지로 바로 이동)
        print("  로그인 상태 확인 중...")
        logged_in = await _is_logged_in(page)
        if not logged_in:
            print("  쿠키 만료 감지")
            await browser.close()
            notify_cookie_expired()
            return False, '쿠키 만료 - 재로그인 필요'

        print("  로그인 확인 완료")
        # _is_logged_in에서 이미 글쓰기 페이지로 이동됨
        await page.wait_for_timeout(2000)

        # [1] 게시판 선택
        print(f"  게시판 선택: {board_name}")
        try:
            await page.click('button.button', timeout=10000)
            await page.wait_for_timeout(500)
            await page.click(f'button.option:has-text("{board_name}")', timeout=5000)
            await page.wait_for_timeout(1000)
        except PlaywrightTimeout:
            print("  게시판 선택 실패")
            await browser.close()
            return False, '게시판 선택 실패'

        # [2] 제목 입력
        print(f"  제목 입력: {title}")
        try:
            await page.fill('textarea.textarea_input', title, timeout=5000)
        except PlaywrightTimeout:
            print("  제목 입력 실패")
            await browser.close()
            return False, '제목 입력 실패'

        # [3] 이미지 업로드
        print("  이미지 업로드 중...")
        try:
            async with page.expect_file_chooser(timeout=10000) as fc_info:
                await page.click('button[data-name="image"]', timeout=5000)
            file_chooser = await fc_info.value
            await file_chooser.set_files(image_path)
            print("  이미지 선택 완료 — 업로드 대기 중...")
            await page.wait_for_timeout(5000)
        except PlaywrightTimeout:
            print("  이미지 업로드 실패")
            await browser.close()
            return False, '이미지 업로드 실패'

        # [4] 등록 버튼
        print("  등록 버튼 클릭...")
        try:
            await page.evaluate('window.scrollTo(0, 0)')
            await page.wait_for_timeout(500)
            await page.get_by_role('button', name='등록', exact=True).first.click(force=True, timeout=8000)
            await page.wait_for_timeout(5000)
            print(f"  게시 완료 → {page.url}")
        except Exception as e:
            print(f"  등록 버튼 클릭 실패: {e}")
            await browser.close()
            return False, f'등록 버튼 클릭 실패: {e}'

        await browser.close()
        return True, ''


# ── 동기 래퍼 (main.py에서 호출) ────────────────────────────────────────────
def refresh_login():
    asyncio.run(_do_refresh_login())


def post_to_cafe(image_path: str, title: str) -> tuple[bool, str]:
    return asyncio.run(_do_post(image_path, title))
