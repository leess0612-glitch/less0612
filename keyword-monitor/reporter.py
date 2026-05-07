"""결과 저장 및 콘솔 요약 출력"""
import json
import os
import csv
from datetime import datetime
import config


def save_results(results: list[dict]):
    os.makedirs(config.RESULTS_DIR, exist_ok=True)
    today = datetime.now().strftime('%Y-%m-%d')

    # JSON 저장
    json_path = os.path.join(config.RESULTS_DIR, f"{today}.json")
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    # CSV 저장 (엑셀로 열기 편함)
    csv_path = os.path.join(config.RESULTS_DIR, f"{today}.csv")
    with open(csv_path, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        writer.writerow(['날짜', '카테고리', '키워드', '노출여부', '블록명', '블록순위', '블록내순위', '채널ID', '채널타입', '발견방식', '매칭키워드'])
        for r in results:
            if r.get('our_exposure'):
                for e in r['our_exposure']:
                    writer.writerow([
                        r['date'], r['category'], r['keyword'], 'O',
                        e.get('block_name', ''), e.get('block_position', ''), e.get('rank_in_block', ''),
                        e.get('channel_id', ''), e.get('type', ''),
                        e.get('source', ''), e.get('matched_keyword', '') or '',
                    ])
            else:
                writer.writerow([
                    r['date'], r['category'], r['keyword'],
                    'X', '', '', '', '', '', '', ''
                ])

    print(f"\n결과 저장 완료")
    print(f"  JSON: {json_path}")
    print(f"  CSV : {csv_path}")


def print_summary(results: list[dict]):
    print("\n" + "=" * 55)
    print("  요약")
    print("=" * 55)

    by_cat = {}
    for r in results:
        cat = r.get('category', '?')
        by_cat.setdefault(cat, {'total': 0, 'exposed': 0, 'rows': []})
        by_cat[cat]['total'] += 1
        if r.get('exposed'):
            by_cat[cat]['exposed'] += 1
            by_cat[cat]['rows'].append(r)

    for cat, d in by_cat.items():
        print(f"\n[{cat}]  노출 {d['exposed']}/{d['total']}개")
        for r in d['rows']:
            for e in r['our_exposure']:
                src = '본문' if e.get('source') == 'content' else '채널'
                kw  = f" ({e['matched_keyword']})" if e.get('matched_keyword') else ''
                print(f"  [노출] {r['keyword']:<20} → {e.get('channel_id','')}({e.get('type','')}) [{e.get('block_name','')}] 블록{e.get('block_position','')}위/{e.get('rank_in_block','')}번째 [{src}{kw}]")

    total = len(results)
    exposed = sum(1 for r in results if r.get('exposed'))
    print(f"\n전체: {exposed}/{total}개 노출")
    print("=" * 55)
