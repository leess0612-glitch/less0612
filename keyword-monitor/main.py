"""
당현함 키워드 노출 모니터링 시스템
실행: python main.py
      python main.py --keywords-only   # 키워드 확장만 실행
      python main.py --check-only      # 노출 체크만 실행
"""
import asyncio
import json
import sys
from datetime import datetime

import config
from crawler import run_check
from reporter import save_results, print_summary
from sheets_manager import write_exposure, write_keywords


def load_json(path: str) -> dict:
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def run_keyword_expansion():
    """네이버 광고 API → 연관키워드 수집 → 시트 기록"""
    from naver_ads_api import get_related_keywords, group_keywords

    if not config.NAVER_ADS_CUSTOMER_ID:
        print("[키워드 확장] API 키 미설정 → 건너뜀\n")
        return

    keywords_data = load_json('data/keywords.json')

    for category, kws in keywords_data.items():
        seeds = [k['keyword'] for k in kws if k.get('active', True)]
        print(f"\n[{category}] 씨앗 키워드 {len(seeds)}개로 연관키워드 조회 중...")

        raw = get_related_keywords(seeds)
        groups = group_keywords(raw)

        total = sum(len(v) for v in groups.values())
        print(f"  수집: {total}개 (A={len(groups['A_고볼륨'])}, "
              f"B={len(groups['B_중볼륨'])}, C={len(groups['C_저볼륨'])})")

        write_keywords(category, groups)


def run_exposure_check():
    """통합검색 크롤링 → 노출 여부 체크 → 저장"""
    keywords_data = load_json('data/keywords.json')
    channels = load_json('data/channels.json')

    total = sum(len(v) for v in keywords_data.items())
    print(f"키워드: ", end="")
    parts = [f"{cat} {len(kws)}개" for cat, kws in keywords_data.items()]
    print(" / ".join(parts))
    print(f"채널: 블로그 {len(channels['blog'])}개 / 카페 {len(channels['cafe'])}개\n")

    results = asyncio.run(run_check(keywords_data, channels))

    save_results(results)
    print_summary(results)
    write_exposure(results)


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else '--all'

    print("=" * 55)
    print("  당현함 키워드 노출 모니터링")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 55 + "\n")

    if mode in ('--all', '--keywords-only'):
        print("[ 1단계 ] 연관키워드 수집")
        run_keyword_expansion()

    if mode in ('--all', '--check-only'):
        print("[ 2단계 ] 통합검색 노출 체크")
        run_exposure_check()


if __name__ == '__main__':
    main()
