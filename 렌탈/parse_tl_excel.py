"""
티엘 SK매직 수수료 엑셀 → JSON 변환 파서
"""
import openpyxl
import json
import re
import os
from datetime import datetime


def clean(v):
    if v is None:
        return ""
    return str(v).strip().replace("\xa0", " ").replace("\u3000", " ")


def normalize_model_code(code):
    return re.sub(r'[\-\s]', '', str(code)).upper()


def parse_tl(filepath):
    wb = openpyxl.load_workbook(filepath, data_only=True)

    ws = None
    for name in wb.sheetnames:
        if name.strip().upper() == "SK":
            ws = wb[name]
            break
    if ws is None:
        for name in wb.sheetnames:
            if "SK" in name.upper():
                ws = wb[name]
                break
    if ws is None:
        raise ValueError(f"SK 시트를 찾을 수 없습니다. 시트 목록: {wb.sheetnames}")

    rows = list(ws.iter_rows(values_only=True))
    DATA_START = 2  # 행2=헤더, 행3(index 2)부터 데이터

    products = []
    warning_models = set()
    # 접수처 비교용 lookup: key → commission
    # key = "{normalized_model}|{mgmt}|{years}|{tasa}|{package}"
    option_lookup = {}
    # 관리주기 lookup: normalized_model → G열 원본값
    visit_cycle_lookup = {}

    current_model_code = ""
    current_product_name = ""

    for i, row in enumerate(rows):
        if i < DATA_START:
            continue

        col_b = clean(row[1])
        col_c = clean(row[2])
        col_e = clean(row[4])
        col_f = clean(row[5])
        col_g = clean(row[6])
        col_h = row[7]
        col_j = row[9]
        col_k = row[10]
        col_l = row[11]

        if col_b:
            current_model_code = col_b
            # G열 관리주기 저장 (B열이 있는 행에만 G열 존재, 해당없음 제외)
            if col_g and col_g != '해당없음' and '+' not in col_b:
                visit_cycle_lookup[normalize_model_code(col_b)] = col_g
        if col_c:
            current_product_name = col_c

        if not current_model_code:
            continue

        # "+" 포함 패키지 모델 제외
        if "+" in current_model_code:
            continue

        is_package = "_패키지" in col_f

        # 관리구분
        col_e_s = col_e.replace(" ", "")
        if "방문" in col_e_s:
            mgmt = "방문관리"
        elif "셀프" in col_e_s:
            mgmt = "셀프관리"
        else:
            continue

        # 약정년수
        year_match = re.search(r'(\d+)년', col_f)
        if not year_match:
            continue
        contract_years = int(year_match.group(1))
        has_tasa = "_타사보상" in col_f

        # 수치
        try:
            monthly_fee = int(col_j) if col_j else 0
            fee_ref     = int(col_k) if col_k else 0
            commission  = int(col_l) if col_l else 0
        except (ValueError, TypeError):
            continue

        if monthly_fee == 0 and commission == 0:
            continue

        # ★ K열은 반값할인가이므로 비교 무의미 → 티엘 dataWarning 없음
        data_warning = False

        # lookup 등록 (패키지/비패키지 모두)
        lookup_key = (f"{normalize_model_code(current_model_code)}"
                      f"|{mgmt}|{contract_years}|{int(has_tasa)}|{int(is_package)}")
        option_lookup[lookup_key] = commission

        # 제품 목록 (패키지 행은 products에 저장하지 않음 - lookup용으로만 사용)
        if not is_package:
            model_key = normalize_model_code(current_model_code)
            existing = next((p for p in products
                             if normalize_model_code(p["modelCode"]) == model_key), None)
            if existing is None:
                existing = {
                    "modelCode": current_model_code,
                    "name": current_product_name,
                    "options": []
                }
                products.append(existing)

            existing["options"].append({
                "managementType": mgmt,
                "contractYears": contract_years,
                "contractLabel": f"{contract_years}년",
                "hasTasa": has_tasa,
                "monthlyFee": monthly_fee,
                "commission": commission,
                "dataWarning": data_warning,
            })

    warn_count = len(warning_models)
    print(f"[티엘] 파싱 완료: {len(products)}개 제품, "
          f"J≠K 경고 {warn_count}개: {sorted(warning_models) if warn_count else '없음'}")

    return {
        "metadata": {
            "source": "티엘",
            "sheetName": ws.title,
            "sourceFile": os.path.basename(filepath),
            "parsedAt": datetime.now().strftime("%Y-%m-%d %H:%M")
        },
        "products": products,
        "warningModels": sorted(warning_models),
        "optionLookup": option_lookup,
        "visitCycleLookup": visit_cycle_lookup,
    }


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        filepath = r"C:\Users\a\Documents\렌탈정책\26.04\2026.04.06 수수료.xlsx"
    else:
        filepath = sys.argv[1]

    data = parse_tl(filepath)

    base_dir = os.path.dirname(os.path.abspath(__file__))
    out = os.path.join(base_dir, "tl_data.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"저장: {out}")
    print(f"lookup 항목수: {len(data['optionLookup'])}")
