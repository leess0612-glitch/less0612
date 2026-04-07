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
    """비교용 모델코드 정규화 (대문자, 공백 제거)"""
    return re.sub(r'\s+', '', str(code)).upper()


def parse_tl(filepath):
    wb = openpyxl.load_workbook(filepath, data_only=True)

    # SK 시트 찾기
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

    # 행2(index 1)가 헤더, 행3(index 2)부터 데이터
    DATA_START = 2

    products = []          # 파싱된 제품 목록
    warning_models = set() # J≠K 경고 모델코드 집합

    current_model_code = ""
    current_product_name = ""

    for i, row in enumerate(rows):
        if i < DATA_START:
            continue

        # 열 읽기
        col_b = clean(row[1])   # B열: 모델명 (carry-forward)
        col_c = clean(row[2])   # C열: 제품명
        col_e = clean(row[4])   # E열: 관리구분
        col_f = clean(row[5])   # F열: 약정명
        col_h = row[7]          # H열: 반값 프로모션 (비어있으면 None/"")
        col_j = row[9]          # J열: 일반가 (월요금 기준)
        col_k = row[10]         # K열: 비교가 (오류감지용)
        col_l = row[11]         # L열: 수수료

        # 모델명 carry-forward
        if col_b:
            current_model_code = col_b
        if col_c:
            current_product_name = col_c

        if not current_model_code:
            continue

        # "+" 포함 패키지 모델 제외
        if "+" in current_model_code:
            continue

        # _패키지 약정 제외
        if "_패키지" in col_f:
            continue

        # 관리구분 확인 (없으면 스킵)
        col_e_stripped = col_e.replace(" ", "")
        if "방문" in col_e_stripped:
            mgmt = "방문관리"
        elif "셀프" in col_e_stripped:
            mgmt = "셀프관리"
        else:
            continue

        # 약정년수 추출
        year_match = re.search(r'(\d+)년', col_f)
        if not year_match:
            continue
        contract_years = int(year_match.group(1))
        has_tasa = "_타사보상" in col_f

        # 수치 데이터
        try:
            monthly_fee = int(col_j) if col_j else 0
            fee_ref     = int(col_k) if col_k else 0
            commission  = int(col_l) if col_l else 0
        except (ValueError, TypeError):
            continue

        if monthly_fee == 0 and commission == 0:
            continue

        # ★ 요금 오류 감지: H열 비어있는데 J열 ≠ K열
        h_empty = (col_h is None or clean(col_h) == "" or col_h == 0)
        data_warning = h_empty and fee_ref != 0 and monthly_fee != fee_ref

        if data_warning:
            warning_models.add(normalize_model_code(current_model_code))

        # 제품 찾기 또는 생성
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
          f"J≠K 경고 모델 {warn_count}개: {sorted(warning_models) if warn_count else '없음'}")

    return {
        "metadata": {
            "source": "티엘",
            "sheetName": ws.title,
            "sourceFile": os.path.basename(filepath),
            "parsedAt": datetime.now().strftime("%Y-%m-%d %H:%M")
        },
        "products": products,
        "warningModels": sorted(warning_models)
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
    print(f"경고 모델: {data['warningModels']}")
