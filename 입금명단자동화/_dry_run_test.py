# 시뮬레이션 전용 임시 스크립트 (실제 엑셀 저장/이미지 캡처/카페 게시 없음)
from datetime import date, datetime
import main as m
from holiday import is_holiday

print("=== 경로 점검 ===")
print(f"EXCEL_PATH = {m.EXCEL_PATH}")
print(f"  존재? {m.EXCEL_PATH.exists()}")
print(f"IMAGE_DIR  = {m.IMAGE_DIR}")
print(f"  존재? {m.IMAGE_DIR.exists()}")

date_filter = "6/9"
print(f"\n=== 구글시트 데이터 가져오기 (날짜 필터: {date_filter}) ===")
wired_data, rental_data = m.fetch_sheets()
wired_rows = m.process_wired(wired_data, date_filter)
rental_rows = m.process_rental(rental_data, date_filter)
print(f"유선개통: {len(wired_rows)}건")
for r in wired_rows:
    print("  ", r)
print(f"렌탈개통: {len(rental_rows)}건")
for r in rental_rows:
    print("  ", r)
print(f"합계: {len(wired_rows) + len(rental_rows)}행")

print("\n=== 휴일 체크 (참고용 - TEST_DATE 설정 시 실제 실행에선 건너뜀) ===")
print(f"오늘(실행일) 휴일여부: {is_holiday()}")
print(f"6/9 휴일여부: {is_holiday(date(2026, 6, 9))}")

print("\n=== 네이버 쿠키 상태 ===")
cookie_path = m.BASE_DIR / 'naver_cookies.json'
if cookie_path.exists():
    mtime = datetime.fromtimestamp(cookie_path.stat().st_mtime)
    age = (datetime.now() - mtime).days
    print(f"naver_cookies.json 수정: {mtime}, {age}일 전, 유효(<=25일)? {age <= 25}")
else:
    print("쿠키 없음")

print("\n=== 시뮬레이션 완료 (실제 저장/캡처/게시 없음) ===")
