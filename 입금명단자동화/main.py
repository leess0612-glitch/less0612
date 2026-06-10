import re
import sys
import json
import pickle
import random
import subprocess
import threading
import time
import argparse
from pathlib import Path
from datetime import date, datetime as _dt

# Windows 터미널 UTF-8 출력
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import win32api
import gspread
import xlwings as xw
from PIL import ImageGrab
from holiday import is_holiday
from naver_post import refresh_login, post_to_cafe

# ─────────────────────────── 설정 ───────────────────────────
SPREADSHEET_ID  = '1y5wfMhcM3_S7FnJWHAhTIkqyzFZZCcItGQpVL5nu5XY'
EXCEL_PATH      = Path(r'C:\Users\a\Documents\신청현황.xlsx')
SCOPES          = ['https://www.googleapis.com/auth/spreadsheets.readonly']
BASE_DIR        = Path(__file__).parent
SHARED_DIR      = BASE_DIR.parent  # 안티그라비티\ (공유 Google 인증 파일 위치)
TOKEN_PATH      = SHARED_DIR / 'token.pickle'
CREDENTIALS_PATH = SHARED_DIR / 'credentials.json'
BACKUP_MIN      = 15
BACKUP_MAX      = 30
DATA_START_ROW  = 3   # 데이터 시작 행 (2행은 고정행)
LOG_PATH        = BASE_DIR / 'run_log.json'
STATUS_HTML_PATH = BASE_DIR / 'status.html'
IMAGE_DIR       = BASE_DIR / '사은품지급명단'
IMAGE_DIR.mkdir(exist_ok=True)
EXCEL_OPEN_TIMEOUT = 30  # 초 - 다른 곳에서 파일이 열려있어 대화상자가 뜨는 경우 대비

# 날짜 필터 설정 (대시보드 '날짜지정')
# None 이면 오늘 날짜 자동 사용, 특정 날짜 처리 시 "6/8"처럼 직접 지정
# (지정된 값은 main() 실행 시 한 번 사용된 후 config.json에서 자동으로 초기화됨)
TARGET_DATE = None

def get_date_filter():
    if TARGET_DATE:
        return TARGET_DATE
    today = date.today()
    return f"{today.month}/{today.day}"

TELECOM_MAP = {
    'KT': 'KT', 'SKT': 'SK', 'SKB': 'SK', 'SK알뜰': 'SK',
    'LGU+': 'LG', 'LG소호': 'LG', '스카이': 'SKY LIFE', 'SKY LIFE': 'SKY LIFE', 'LG헬로': 'LG헬로',
}
PRODUCT_MAP = {'인단': '인터넷', '번들': '인터넷+TV'}


# ─────────────────────────── 실행 로그 + 상태 HTML ───────────────────────────
def log_run(entry: dict):
    logs = []
    if LOG_PATH.exists():
        try:
            with open(LOG_PATH, 'r', encoding='utf-8') as f:
                logs = json.load(f)
        except Exception:
            logs = []
    logs.append(entry)
    logs = logs[-60:]
    with open(LOG_PATH, 'w', encoding='utf-8') as f:
        json.dump(logs, f, ensure_ascii=False, indent=2)
    _generate_status_html(logs)
    print(f"  상태 페이지 업데이트 → {STATUS_HTML_PATH}")


def _generate_status_html(logs: list):
    logs_json = json.dumps(logs, ensure_ascii=False)
    html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta http-equiv="refresh" content="60">
<title>입금명단 자동화 - 실행 현황</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: 'Malgun Gothic', -apple-system, sans-serif; background: #f0f2f5; padding: 24px; color: #222; }}
  h1 {{ font-size: 20px; margin-bottom: 20px; color: #1a1a2e; }}
  .cards {{ display: flex; gap: 16px; margin-bottom: 20px; flex-wrap: wrap; }}
  .card {{ background: white; border-radius: 10px; padding: 18px 24px; min-width: 160px; box-shadow: 0 1px 4px rgba(0,0,0,.08); }}
  .card .val {{ font-size: 26px; font-weight: 700; margin-bottom: 4px; }}
  .card .lbl {{ font-size: 12px; color: #888; }}
  .green {{ color: #1e8e3e; }}
  .red {{ color: #d93025; }}
  .orange {{ color: #e37400; }}
  .blue {{ color: #1a73e8; }}
  table {{ width: 100%; border-collapse: collapse; background: white; border-radius: 10px; overflow: hidden; box-shadow: 0 1px 4px rgba(0,0,0,.08); }}
  th {{ background: #1a73e8; color: white; padding: 11px 14px; text-align: left; font-size: 13px; font-weight: 600; }}
  td {{ padding: 9px 14px; border-bottom: 1px solid #f0f0f0; font-size: 13px; }}
  tr:last-child td {{ border-bottom: none; }}
  tr:hover td {{ background: #f8f9ff; }}
  .badge {{ display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 12px; font-weight: 600; }}
  .badge-ok {{ background: #e6f4ea; color: #1e8e3e; }}
  .badge-fail {{ background: #fce8e6; color: #d93025; }}
  .badge-skip {{ background: #fff3e0; color: #e37400; }}
  .empty {{ text-align: center; padding: 40px; color: #aaa; font-size: 14px; }}
  .footer {{ margin-top: 12px; font-size: 11px; color: #aaa; text-align: right; }}
</style>
</head>
<body>
<h1>입금명단 자동화 — 실행 현황</h1>
<div id="root"></div>
<div class="footer">※ 이 페이지는 프로그램 실행 시 자동 갱신됩니다 (브라우저 1분 자동새로고침)</div>
<script>
const LOGS = {logs_json};

function render() {{
  const el = document.getElementById('root');
  if (!LOGS.length) {{
    el.innerHTML = '<div class="empty">아직 실행 기록이 없습니다.</div>';
    return;
  }}

  const last = [...LOGS].reverse().find(e => !e.skipped) || LOGS[LOGS.length - 1];
  const lastAny = LOGS[LOGS.length - 1];

  const cards = `<div class="cards">
    <div class="card">
      <div class="val blue">${{lastAny.run_at}}</div>
      <div class="lbl">마지막 실행 시각</div>
    </div>
    <div class="card">
      <div class="val ${{lastAny.skipped ? 'orange' : (lastAny.cafe_posted ? 'green' : 'red')}}">${{lastAny.skipped || (lastAny.cafe_posted ? '게시 완료' : '게시 실패')}}</div>
      <div class="lbl">마지막 결과</div>
    </div>
    <div class="card">
      <div class="val blue">${{last ? (last.total_rows || 0) : 0}}</div>
      <div class="lbl">최근 게시 건수</div>
    </div>
    <div class="card">
      <div class="val blue">${{LOGS.length}}</div>
      <div class="lbl">총 실행 횟수 (최근 60회)</div>
    </div>
  </div>`;

  let rows = '';
  for (const e of [...LOGS].reverse()) {{
    let badge;
    if (e.skipped) badge = `<span class="badge badge-skip">${{e.skipped}}</span>`;
    else if (e.cafe_posted) badge = '<span class="badge badge-ok">완료</span>';
    else badge = '<span class="badge badge-fail">실패</span>';

    const rowStyle = (!e.skipped && !e.cafe_posted) ? ' style="background:#fef4f3"' : '';
    rows += `<tr${{rowStyle}}>
      <td>${{e.run_at}}</td>
      <td>${{e.date_filter || '-'}}</td>
      <td>${{e.wired_count ?? '-'}}</td>
      <td>${{e.rental_count ?? '-'}}</td>
      <td>${{e.backup_count ?? '-'}}</td>
      <td><b>${{e.total_rows ?? '-'}}</b></td>
      <td>${{badge}}</td>
      <td style="color:#d93025;font-size:12px;font-weight:600">${{e.error || ''}}</td>
    </tr>`;
  }}

  const table = `<table>
    <tr><th>실행 시각</th><th>날짜</th><th>유선</th><th>렌탈</th><th>백업</th><th>합계</th><th>결과</th><th>오류</th></tr>
    ${{rows}}
  </table>`;

  el.innerHTML = cards + table;
}}
render();
</script>
</body>
</html>"""
    with open(STATUS_HTML_PATH, 'w', encoding='utf-8') as f:
        f.write(html)


# ─────────────────────────── 이름 정제 및 마스킹 ───────────────────────────
def clean_name(name: str) -> str:
    name = name.strip()
    if '/' in name:
        name = name[:name.index('/')]   # / 이후 삭제
    name = re.sub(r'\d', '', name)      # 숫자 삭제
    return name.strip()

def mask_name(name: str) -> str:
    name = clean_name(name)
    n = len(name)
    if n <= 1:
        return name
    if n == 2:
        return name[0] + '#'
    return name[0] + '#' * (n - 2) + name[-1]


# ─────────────────────────── Google 인증 ───────────────────────────
def get_credentials():
    creds = None

    if TOKEN_PATH.exists():
        with open(TOKEN_PATH, 'rb') as f:
            creds = pickle.load(f)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not CREDENTIALS_PATH.exists():
                raise FileNotFoundError(
                    f"credentials.json 파일이 없습니다.\n"
                    f"Google Cloud Console에서 OAuth 클라이언트 ID를 생성한 후\n"
                    f"{CREDENTIALS_PATH} 위치에 저장해주세요."
                )
            flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_PATH), SCOPES)
            creds = flow.run_local_server(port=0)

        with open(TOKEN_PATH, 'wb') as f:
            pickle.dump(creds, f)

    return creds


# ─────────────────────────── 구글시트 데이터 추출 ───────────────────────────
def fetch_sheets():
    client = gspread.authorize(get_credentials())
    ss = client.open_by_key(SPREADSHEET_ID)
    wired  = ss.worksheet('유선개통').get_all_values()
    rental = ss.worksheet('렌탈개통').get_all_values()
    return wired, rental


def process_wired(data, date_filter):
    """유선개통 탭 → (고객명, 통신사, 상품, 은행) 목록"""
    rows = []
    for row in data[1:]:   # 1행 헤더 제외
        if len(row) < 12:
            continue
        if row[1].strip() != date_filter:  # B열 날짜 필터
            continue
        telecom = row[2].strip()    # C열
        name    = row[6].strip()    # G열
        bank    = row[7].strip()    # H열
        product = row[11].strip()   # L열

        if not name:
            continue
        if '유심' in product:
            continue

        rows.append((
            mask_name(name),
            TELECOM_MAP.get(telecom, telecom),
            PRODUCT_MAP.get(product, product),
            bank,
        ))
    return rows


def process_rental(data, date_filter):
    """렌탈개통 탭 → (고객명, '', '가전렌탈', 은행) 목록"""
    rows = []
    for row in data[1:]:
        if len(row) < 8:
            continue
        if row[1].strip() != date_filter:  # B열 날짜 필터
            continue
        name = row[6].strip()   # G열
        bank = row[7].strip()   # H열

        if not name:
            continue

        rows.append((mask_name(name), '', '가전렌탈', bank))
    return rows


def _open_workbook(app, path):
    """파일이 다른 곳에서 열려있어 '사용 중' 대화상자가 뜨면 무한 대기에 빠지는 것을 방지.
    EXCEL_OPEN_TIMEOUT초 안에 안 열리면 invisible 엑셀을 강제 종료해 대기를 풀고 알림을 띄운다.
    (COM 객체는 생성한 스레드에서만 접근 가능하므로, app.books.open()은 항상 메인 스레드에서
    그대로 호출하고 워치독 스레드는 PID 강제종료/알림만 담당한다.)"""
    pid = app.pid
    done = threading.Event()
    timed_out = threading.Event()

    def _watchdog():
        if not done.wait(EXCEL_OPEN_TIMEOUT):
            timed_out.set()
            subprocess.run(['taskkill', '/F', '/T', '/PID', str(pid)], capture_output=True)
            try:
                from plyer import notification
                notification.notify(
                    title='입금명단 자동화 - 조치 필요',
                    message=f'{EXCEL_PATH.name} 파일이 다른 곳에서 열려있어 자동화가 실패했습니다.\n파일을 닫고 대시보드에서 다시 실행해주세요.',
                    timeout=20,
                )
            except Exception:
                pass

    watchdog = threading.Thread(target=_watchdog, daemon=True)
    watchdog.start()
    try:
        wb = app.books.open(path)
    except Exception:
        if timed_out.is_set():
            raise TimeoutError(f'엑셀 파일이 열려있어 자동화 실패 ({EXCEL_OPEN_TIMEOUT}초 타임아웃)')
        raise
    finally:
        done.set()
    return wb


# ─────────────────────────── 엑셀 업데이트 + 캡처 + 재정렬 ───────────────────────────
def update_excel(wired_rows, rental_rows, source='all', capture_only=False):
    """
    한 세션에서 모든 처리:
    1) 백업 선택 → 표시 영역 기입 → 저장
    2) (all 모드) 이미지 캡처 (visible=True 전환)
    3) (all 모드) 표시 데이터 무작위 재정렬 → 맨 아래 아카이브 → 표시 행 초기화 → 저장
    반환: (total_rows, image_path, backup_count)
    """
    app = xw.App(visible=False)
    try:
        short_path = win32api.GetShortPathName(str(EXCEL_PATH))
        wb = _open_workbook(app, short_path)
        ws = wb.sheets.active

        max_row = ws.used_range.last_cell.row

        # A~G열 한번에 읽기
        if max_row >= DATA_START_ROW:
            raw = ws.range(f'A{DATA_START_ROW}:G{max_row}').value
            if raw and not isinstance(raw[0], list):
                raw = [raw]
        else:
            raw = []

        # A열 번호 있는 마지막 행 = 표시 영역 끝 (rows 3~62)
        last_display_row = DATA_START_ROW - 1
        for i, row_data in enumerate(raw or []):
            a = row_data[0]
            if a is not None and str(a).strip() != '':
                last_display_row = DATA_START_ROW + i

        # 백업 후보 수집 (표시 영역 아래, A 비어있고 D에 값 있는 행)
        backup_candidates = []
        for i, row_data in enumerate(raw or []):
            r = DATA_START_ROW + i
            if r <= last_display_row:
                continue
            a = row_data[0]
            d = row_data[3]
            if (a is None or str(a).strip() == '') and d:
                backup_candidates.append((r, (row_data[3], row_data[4], row_data[5], row_data[6])))

        # 백업 선택 (가용 수에 따라 조정)
        if len(backup_candidates) == 0:
            backup_count = 0
            selected = []
        elif len(backup_candidates) < BACKUP_MIN:
            backup_count = len(backup_candidates)
            selected = backup_candidates[:]
        else:
            backup_count = random.randint(BACKUP_MIN, min(BACKUP_MAX, len(backup_candidates)))
            selected = backup_candidates[:backup_count]
        backup = [data for _, data in selected]

        print(f"  백업 후보: {len(backup_candidates)}개 → 선택: {backup_count}개")

        # 선택된 백업행 삭제 (역순 = 행 번호 밀림 방지)
        for row_num, _ in sorted(selected, key=lambda x: x[0], reverse=True):
            ws.range(f'{row_num}:{row_num}').delete()

        # 모드별 출력 데이터 결정
        if source == 'wired':
            all_rows = list(wired_rows)
        elif source == 'rental':
            all_rows = list(rental_rows)
        elif source == 'backup':
            all_rows = list(backup)
        else:
            all_rows = backup + list(wired_rows) + list(rental_rows)

        # 가나다 오름차순 정렬
        all_rows.sort(key=lambda x: str(x[0] or ''))

        # 표시 영역 D~G 초기화 후 기입
        if last_display_row >= DATA_START_ROW:
            ws.range(f'D{DATA_START_ROW}:G{last_display_row}').clear_contents()

        if all_rows:
            write_data = [[d, e or None, f, g] for d, e, f, g in all_rows]
            ws.range(f'D{DATA_START_ROW}').value = write_data

        if source == 'all':
            print(f"  유선개통: {len(wired_rows)}건 | 렌탈개통: {len(rental_rows)}건 | 합계: {len(all_rows)}행")
        else:
            print(f"  [{source}] {len(all_rows)}행 출력")

        # ── [all 모드] 이미지 캡처 (같은 세션, visible 전환) ──────────────────
        image_path = None
        if source == 'all' and all_rows:
            wb.save()

            last_row = DATA_START_ROW + len(all_rows) - 1
            today = date.today()
            if TARGET_DATE:
                m, d_val = TARGET_DATE.split('/')
                cap_date = date(today.year, int(m), int(d_val))
            else:
                cap_date = today
            image_path = IMAGE_DIR / f"{cap_date.strftime('%Y%m%d')}_사은품명단.png"

            print("[3] 이미지 캡처 중...")
            app.visible = True
            try:
                ws.range(f'D2:G{last_row}').api.CopyPicture(Appearance=1, Format=2)
                time.sleep(0.5)
                img = ImageGrab.grabclipboard()
                if img:
                    img.save(str(image_path))
                    print(f"  이미지 저장 → {image_path}")
                else:
                    print("  이미지 캡처 실패 (클립보드 비어있음) — 아카이브 중단")
                    image_path = None
                    wb.save()
                    wb.close()
                    return len(all_rows), None, backup_count
            finally:
                app.visible = False

            if not capture_only:
                # ── 스크린샷 후 처리: 무작위 재정렬 → 맨 아래 복사 → 표시 행 초기화 ──
                print("[4] 무작위 재정렬 및 백업 보관 중...")
                shuffled = list(all_rows)
                random.shuffle(shuffled)

                archive_start = ws.used_range.last_cell.row + 1
                archive_data = [[d, e or None, f, g] for d, e, f, g in shuffled]
                ws.range(f'D{archive_start}').value = archive_data

                display_end = DATA_START_ROW + len(all_rows) - 1
                ws.range(f'D{DATA_START_ROW}:G{display_end}').clear_contents()
                print(f"  {len(shuffled)}행 → {archive_start}행부터 아카이브 완료, 표시 영역 초기화")
            else:
                print("[4] 캡처 전용 모드 - 아카이브 생략")

        wb.save()
        wb.close()
        print(f"  저장 완료 → {EXCEL_PATH}")
        return len(all_rows), image_path, backup_count

    finally:
        try:
            app.quit()
        except Exception:
            pass


# ─────────────────────────── 아카이브 전용 ───────────────────────────
def archive_only(args):
    print("[4] 무작위 재정렬 및 백업 보관 중...")
    app = xw.App(visible=False)
    try:
        short_path = win32api.GetShortPathName(str(EXCEL_PATH))
        wb = _open_workbook(app, short_path)
        ws = wb.sheets.active

        max_row = ws.used_range.last_cell.row
        if max_row < DATA_START_ROW:
            print("  표시 영역이 비어있음 - 종료")
            wb.close()
            return

        raw = ws.range(f'A{DATA_START_ROW}:G{max_row}').value
        if raw and not isinstance(raw[0], list):
            raw = [raw]

        # A열에 번호 있는 행 = 표시 영역
        display_rows = []
        last_display_row = DATA_START_ROW - 1
        for i, row_data in enumerate(raw or []):
            a = row_data[0]
            if a is not None and str(a).strip() != '':
                last_display_row = DATA_START_ROW + i
                d, e, f, g = row_data[3], row_data[4], row_data[5], row_data[6]
                if d:
                    display_rows.append((d, e, f, g))

        if not display_rows:
            print("  표시 영역에 데이터 없음 - 종료")
            wb.close()
            return

        shuffled = list(display_rows)
        random.shuffle(shuffled)

        archive_start = ws.used_range.last_cell.row + 1
        archive_data = [[d, e or None, f, g] for d, e, f, g in shuffled]
        ws.range(f'D{archive_start}').value = archive_data

        ws.range(f'D{DATA_START_ROW}:G{last_display_row}').clear_contents()
        print(f"  {len(shuffled)}행 → {archive_start}행부터 아카이브 완료, 표시 영역 초기화")

        wb.save()
        wb.close()
        print(f"  저장 완료 → {EXCEL_PATH}")
    finally:
        try:
            app.quit()
        except Exception:
            pass
    print("\n완료!")


# ─────────────────────────── 실행 ───────────────────────────
def parse_args():
    parser = argparse.ArgumentParser(description='입금명단 자동화')
    parser.add_argument(
        '--source',
        choices=['wired', 'rental', 'backup', 'all'],
        default='all',
        help='wired=유선개통 / rental=렌탈개통 / backup=백업 / all=전체(기본값)'
    )
    parser.add_argument(
        '--capture-only',
        action='store_true',
        help='이미지 캡처까지만 실행하고 아카이브/초기화 생략'
    )
    parser.add_argument(
        '--archive-only',
        action='store_true',
        help='표시 영역 데이터를 무작위 재정렬 후 아카이브만 실행'
    )
    parser.add_argument(
        '--refresh-login',
        action='store_true',
        help='네이버 로그인 후 쿠키 저장 (쿠키 만료 시 실행)'
    )
    return parser.parse_args()


def main():
    global TARGET_DATE, BACKUP_MIN, BACKUP_MAX
    try:
        with open(BASE_DIR / 'config.json', 'r', encoding='utf-8') as f:
            _cfg = json.load(f)
        TARGET_DATE = _cfg.get('test_date') or None
        BACKUP_MIN = int(_cfg.get('backup_min', BACKUP_MIN))
        BACKUP_MAX = int(_cfg.get('backup_max', BACKUP_MAX))
    except Exception:
        pass

    args = parse_args()
    source = args.source
    run_at = _dt.now().strftime('%Y-%m-%d %H:%M:%S')

    print("=" * 50)
    print(f"입금명단 자동화  [모드: {source}]")
    print("=" * 50)

    if args.refresh_login:
        refresh_login()
        return

    if args.archive_only:
        archive_only(args)
        return

    # 주말/공휴일 체크 (all 모드일 때만)
    if source == 'all' and not TARGET_DATE:
        print("\n[0] 오늘 날짜 확인 중...")
        if is_holiday():
            print("  오늘은 주말 또는 공휴일 - 실행 종료")
            log_run({'run_at': run_at, 'date_filter': get_date_filter(),
                     'skipped': '휴일/주말', 'cafe_posted': False,
                     'wired_count': None, 'rental_count': None,
                     'backup_count': None, 'total_rows': None,
                     'image_file': None, 'error': None})
            return

    date_filter = get_date_filter()
    wired_rows, rental_rows = [], []

    try:
        if source in ('wired', 'rental', 'all'):
            print(f"\n[1] 구글시트 데이터 가져오는 중... (날짜 필터: {date_filter})")
            wired_data, rental_data = fetch_sheets()

            if source in ('wired', 'all'):
                wired_rows = process_wired(wired_data, date_filter)
                print(f"  유선개통: {len(wired_rows)}건")

            if source in ('rental', 'all'):
                rental_rows = process_rental(rental_data, date_filter)
                print(f"  렌탈개통: {len(rental_rows)}건")
        else:
            print("\n[1] 구글시트 접속 생략 (백업 모드)")

        print("[2] 엑셀 업데이트 중...")
        row_count, image_path, backup_count = update_excel(
            wired_rows, rental_rows, source, capture_only=args.capture_only
        )

        cafe_posted = False
        cafe_error = None
        if source == 'all' and image_path and not args.capture_only:
            print("\n[5] 네이버 카페 게시 중...")
            from datetime import date as _date
            if TARGET_DATE:
                m, d_val = TARGET_DATE.split('/')
                post_date = _date(date.today().year, int(m), int(d_val))
            else:
                post_date = _date.today()
            title = f"{post_date.strftime('%Y-%m-%d')} 사은품지급 명단"
            cafe_posted, cafe_error = post_to_cafe(str(image_path), title)
            if cafe_posted:
                print("  카페 게시 완료")
            else:
                print(f"  카페 게시 실패: {cafe_error} (수동 게시 필요)")

        if source == 'all' and not args.capture_only:
            if row_count == 0:
                error_msg = '오늘 등록할 데이터 없음'
            elif not image_path:
                error_msg = '이미지 캡처 실패'
            elif not cafe_posted:
                error_msg = cafe_error or '카페 게시 실패'
            else:
                error_msg = None
            log_run({
                'run_at': run_at,
                'date_filter': date_filter,
                'wired_count': len(wired_rows),
                'rental_count': len(rental_rows),
                'backup_count': backup_count,
                'total_rows': row_count,
                'image_file': Path(image_path).name if image_path else None,
                'cafe_posted': cafe_posted,
                'skipped': None,
                'error': error_msg,
            })

    except Exception as e:
        log_run({
            'run_at': run_at,
            'date_filter': date_filter if 'date_filter' in dir() else None,
            'wired_count': len(wired_rows) if wired_rows is not None else None,
            'rental_count': len(rental_rows) if rental_rows is not None else None,
            'backup_count': None,
            'total_rows': None,
            'image_file': None,
            'cafe_posted': False,
            'skipped': None,
            'error': str(e),
        })
        raise

    print("\n완료!")


if __name__ == '__main__':
    main()
