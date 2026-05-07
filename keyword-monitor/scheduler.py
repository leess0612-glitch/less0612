"""
당현함 키워드 모니터링 - 주간 스케줄러
실행: python scheduler.py  (app.py에서 자동 관리)
"""
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timedelta

SETTINGS_FILE = 'settings.json'
PID_FILE      = 'scheduler.pid'
LOG_FILE      = 'scheduler.log'
CHECK_INTERVAL = 30  # 초마다 시각 확인

DAY_MAP = {'월': 0, '화': 1, '수': 2, '목': 3, '금': 4, '토': 5, '일': 6}
DAY_KR  = {0: '월', 1: '화', 2: '수', 3: '목', 4: '금', 5: '토', 6: '일'}


def load_settings() -> dict:
    with open(SETTINGS_FILE, encoding='utf-8') as f:
        return json.load(f)


def log(msg: str):
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(line + '\n')


def get_next_run(schedule_days: list, schedule_time: str):
    """다음 실행 예정 datetime 반환"""
    if not schedule_days:
        return None
    day_nums = {DAY_MAP[d] for d in schedule_days if d in DAY_MAP}
    h, m = map(int, schedule_time.split(':'))
    now = datetime.now()
    for delta in range(1, 9):
        candidate = (now + timedelta(days=delta)).replace(
            hour=h, minute=m, second=0, microsecond=0
        )
        if candidate.weekday() in day_nums:
            return candidate
    return None


def main():
    # PID 파일 기록
    with open(PID_FILE, 'w') as f:
        f.write(str(os.getpid()))

    log("스케줄러 시작")
    last_run_date = None

    try:
        while True:
            try:
                settings = load_settings()

                if not settings.get('schedule_enabled', False):
                    time.sleep(CHECK_INTERVAL)
                    continue

                days      = settings.get('schedule_days', [])
                time_str  = settings.get('schedule_time', '09:00')
                h, m      = map(int, time_str.split(':'))
                day_nums  = {DAY_MAP[d] for d in days if d in DAY_MAP}
                now       = datetime.now()
                today     = now.date()

                if (now.weekday() in day_nums
                        and now.hour == h
                        and now.minute == m
                        and last_run_date != today):

                    log("자동 실행 시작")
                    env = {**os.environ, 'PYTHONIOENCODING': 'utf-8'}
                    result = subprocess.run(
                        [sys.executable, '-u', 'main.py', '--check-only'],
                        encoding='utf-8', errors='replace', env=env,
                    )
                    last_run_date = today
                    log(f"자동 실행 완료 (returncode={result.returncode})")

            except Exception as e:
                log(f"오류: {e}")

            time.sleep(CHECK_INTERVAL)

    finally:
        if os.path.exists(PID_FILE):
            os.remove(PID_FILE)
        log("스케줄러 종료")


if __name__ == '__main__':
    main()
