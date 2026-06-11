import asyncio
import json
import random
import sys
from pathlib import Path
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
from playwright_stealth import Stealth

BASE_DIR = Path(__file__).parent
CONFIG_PATH = BASE_DIR / 'config.json'
PROFILE_DIR = BASE_DIR / 'chrome_profile'

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

_stealth = Stealth()


def load_config():
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


def notify_login_required():
    """Windows 알림: 재로그인 안내"""
    try:
        from plyer import notification
        notification.notify(
            title='입금명단 자동화 - 조치 필요',
            message='네이버 로그인 세션이 만료됐습니다.\npython main.py --refresh-login 을 실행해주세요.',
            timeout=20,
        )
        print("  Windows 알림 발송 완료")
    except Exception as e:
        print(f"  알림 실패: {e}")


# ── 브라우저 컨텍스트 (영구 프로필 + 실제 Chrome) ───────────────────────────
_LAUNCH_ARGS = [
    '--disable-blink-features=AutomationControlled',
    '--no-first-run',
    '--no-default-browser-check',
    '--disable-session-crashed-bubble',
    '--window-size=1920,1080',
]


def _fix_exit_type():
    """비정상 종료(재부팅 등) 후 '페이지 복원' 알림이 뜨지 않도록 보정"""
    prefs_path = PROFILE_DIR / 'Default' / 'Preferences'
    if not prefs_path.exists():
        return
    try:
        with open(prefs_path, 'r', encoding='utf-8') as f:
            prefs = json.load(f)
        profile = prefs.setdefault('profile', {})
        profile['exit_type'] = 'Normal'
        profile['exited_cleanly'] = True
        with open(prefs_path, 'w', encoding='utf-8') as f:
            json.dump(prefs, f)
    except Exception:
        pass


def _format_launch_error(e: Exception) -> str:
    """launch_persistent_context 실패 시, 거대한 명령줄/로그 덤프 대신 핵심 한 줄만 추출"""
    text = str(e).strip()
    return text.splitlines()[0] if text else type(e).__name__


async def _new_context(p, headless=False):
    _fix_exit_type()
    context = await p.chromium.launch_persistent_context(
        user_data_dir=str(PROFILE_DIR),
        channel='chrome',
        headless=headless,
        args=_LAUNCH_ARGS,
        no_viewport=True,
    )
    await context.add_init_script("Object.defineProperty(navigator,'webdriver',{get:()=>undefined})")
    await _stealth.apply_stealth_async(context)
    return context


# ── 사람처럼 동작하는 헬퍼 ──────────────────────────────────────────────────
async def _human_click(locator, timeout=5000, **kwargs):
    """클릭 전 마우스를 살짝 움직인 뒤 클릭"""
    page = locator.page
    try:
        await locator.wait_for(state='visible', timeout=timeout)
        box = await locator.bounding_box()
    except Exception:
        box = None
    if box:
        x = box['x'] + box['width'] * random.uniform(0.3, 0.7)
        y = box['y'] + box['height'] * random.uniform(0.3, 0.7)
        await page.mouse.move(x, y, steps=random.randint(15, 30))
        await page.wait_for_timeout(random.randint(80, 220))
    await locator.click(timeout=timeout, **kwargs)


async def _human_type(page, text):
    """글자마다 랜덤 딜레이를 주며 입력"""
    for ch in text:
        await page.keyboard.type(ch)
        await page.wait_for_timeout(random.randint(40, 160))


async def _browse_naturally(page, cafe_url):
    """글쓰기 페이지로 직행하지 않고 카페 메인을 먼저 거침"""
    try:
        await page.goto(cafe_url, wait_until='load', timeout=30000)
        await page.wait_for_timeout(random.randint(1500, 3500))
    except Exception:
        pass


async def _is_logged_in(page) -> bool:
    """카페 글쓰기 페이지 접근으로 로그인 상태 확인"""
    config = load_config()
    club_id = config['cafe_clubid']
    menu_id = config['cafe_menuid']
    write_url = f'https://cafe.naver.com/ca-fe/cafes/{club_id}/articles/write?boardType=L&menuId={menu_id}'
    try:
        await page.goto(write_url, wait_until='load', timeout=30000)
        await page.wait_for_timeout(random.randint(1500, 2500))
        if 'nidlogin' in page.url or 'login' in page.url:
            return False
        # 글쓰기 영역이 있으면 로그인 상태
        el = await page.query_selector('textarea.textarea_input, button.button')
        return el is not None
    except Exception:
        return False


# ── 수동 로그인 (영구 프로필에 세션 저장) ───────────────────────────────────
async def _do_refresh_login():
    print("브라우저가 열립니다. 네이버에 로그인해주세요. (최대 3분 대기)")

    async with async_playwright() as p:
        try:
            context = await _new_context(p, headless=False)
        except Exception as e:
            print(f"  브라우저 실행 실패: {_format_launch_error(e)}")
            print("  (다른 자동화가 실행 중이면 종료 후 다시 시도해주세요)")
            return

        page = context.pages[0] if context.pages else await context.new_page()

        await page.goto('https://nid.naver.com/nidlogin.login', wait_until='domcontentloaded')
        await page.bring_to_front()

        print("로그인 완료 후 자동으로 계속됩니다. (최대 3분 대기)")
        try:
            await page.wait_for_url(
                lambda url: 'nidlogin' not in url and 'naver.com' in url,
                timeout=180000
            )
            print("로그인 완료. 이후 자동 실행 가능합니다.")
        except PlaywrightTimeout:
            current_url = page.url
            print(f"  현재 URL: {current_url}")
            if 'naver.com' in current_url and 'nidlogin' not in current_url:
                print("로그인 완료. 이후 자동 실행 가능합니다.")
            else:
                print("로그인 시간 초과 (3분). 다시 시도해주세요.")
        finally:
            await context.close()


# ── 카페 게시 ────────────────────────────────────────────────────────────────
async def _do_post(image_path: str, title: str) -> tuple[bool, str]:
    config = load_config()
    board_name = config['cafe_board_name']
    cafe_url = config['cafe_url']

    async with async_playwright() as p:
        try:
            context = await _new_context(p, headless=False)
        except Exception as e:
            first_line = _format_launch_error(e)
            if 'closed' in first_line.lower():
                return False, '브라우저 실행 실패 - 다른 자동화가 이미 실행 중일 수 있음'
            return False, f'브라우저 실행 실패: {first_line}'

        page = context.pages[0] if context.pages else await context.new_page()

        # 글쓰기 페이지로 직행하지 않고 카페 메인을 먼저 거침
        await _browse_naturally(page, cafe_url)

        # 로그인 상태 확인 (글쓰기 페이지로 이동)
        print("  로그인 상태 확인 중...")
        logged_in = await _is_logged_in(page)
        if not logged_in:
            print("  로그인 세션 만료 감지")
            await context.close()
            notify_login_required()
            return False, '로그인 세션 만료 - 재로그인 필요 (--refresh-login)'

        print("  로그인 확인 완료")
        # _is_logged_in에서 이미 글쓰기 페이지로 이동됨
        await page.wait_for_timeout(random.randint(1500, 2500))

        # [1] 게시판 선택
        print(f"  게시판 선택: {board_name}")
        try:
            await _human_click(page.locator('button.button').first, timeout=10000)
            await page.wait_for_timeout(random.randint(400, 900))
            await _human_click(page.locator(f'button.option:has-text("{board_name}")'), timeout=5000)
            await page.wait_for_timeout(random.randint(800, 1500))
        except PlaywrightTimeout:
            print("  게시판 선택 실패")
            await context.close()
            return False, '게시판 선택 실패'

        # [2] 제목 입력
        print(f"  제목 입력: {title}")
        try:
            title_box = page.locator('textarea.textarea_input')
            await _human_click(title_box, timeout=5000)
            await _human_type(page, title)
        except PlaywrightTimeout:
            print("  제목 입력 실패")
            await context.close()
            return False, '제목 입력 실패'

        # [3] 이미지 업로드
        print("  이미지 업로드 중...")
        try:
            async with page.expect_file_chooser(timeout=10000) as fc_info:
                await _human_click(page.locator('button[data-name="image"]'), timeout=5000)
            file_chooser = await fc_info.value
            await file_chooser.set_files(image_path)
            print("  이미지 선택 완료 — 업로드 대기 중...")
            await page.wait_for_timeout(random.randint(4000, 6500))
        except PlaywrightTimeout:
            print("  이미지 업로드 실패")
            await context.close()
            return False, '이미지 업로드 실패'

        # [4] 등록 버튼
        print("  등록 버튼 클릭...")
        try:
            await page.evaluate('window.scrollTo(0, 0)')
            await page.wait_for_timeout(random.randint(400, 900))
            await _human_click(page.get_by_role('button', name='등록', exact=True).first, force=True, timeout=8000)
            await page.wait_for_timeout(random.randint(4000, 6000))
            print(f"  게시 완료 → {page.url}")
        except Exception as e:
            print(f"  등록 버튼 클릭 실패: {e}")
            await context.close()
            return False, f'등록 버튼 클릭 실패: {e}'

        await context.close()
        return True, ''


# ── 동기 래퍼 (main.py에서 호출) ────────────────────────────────────────────
def refresh_login():
    asyncio.run(_do_refresh_login())


def post_to_cafe(image_path: str, title: str) -> tuple[bool, str]:
    return asyncio.run(_do_post(image_path, title))
