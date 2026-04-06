"""
SK매직 수수료 엑셀 → JSON 변환 파서
사용법: python parse_excel.py "파일경로.xlsx"
"""
import openpyxl
import json
import sys
import re
import os
from datetime import datetime

# ─────────────────────────────────────────────
# 유틸
# ─────────────────────────────────────────────

def clean(v):
    if v is None:
        return ""
    return str(v).strip().replace("\xa0", " ").replace("\u3000", " ")

def clean_name(v):
    """제품명/모델명 줄바꿈 정리"""
    s = clean(v)
    s = re.sub(r'\n+', '\n', s)
    return s.strip()

def months_to_label(m):
    m = int(m)
    if m % 12 == 0:
        return f"{m//12}년"
    return f"{m}개월"

def normalize_management_type(raw):
    """col3 값을 정규화"""
    if not raw:
        return None
    s = clean(raw).replace("\n", "").replace(" ", "")
    # 관리유형 패턴
    patterns = [
        ("방문할인+타사보상", "방문할인+타사보상"),
        ("셀프할인+타사보상", "셀프할인+타사보상"),
        ("방문할인", "방문할인"),
        ("셀프할인", "셀프할인"),
        ("무방문형할인", "무방문형할인"),
        ("방문", "방문"),
        ("셀프", "셀프"),
        ("무방문형", "무방문형"),
        ("타사보상", "타사보상"),
    ]
    # 연도형 패턴 (1년(방문형) 등)
    year_mgmt = re.match(r'^(\d+)년\(?(방문형|셀프형|무방문형)\)?$', s)
    if year_mgmt:
        return s
    for keyword, label in patterns:
        if keyword in s:
            return label
    # 관리유형이 아닌 것 (Basic, Lite, 법인 등)
    return None

def detect_category(model_code, product_name, row_index):
    """모델코드/제품명으로 카테고리 추론"""
    m = (model_code + product_name).upper()
    if any(x in m for x in ["WPU", "정수기", "언더싱크", "그랜드정수기", "뉴랜드정수기", "뉴슬림정수기"]):
        return "정수기"
    if any(x in m for x in ["ACL", "공기청정기", "청정기"]):
        return "공기청정기"
    if any(x in m for x in ["BID", "비데"]):
        return "비데"
    if any(x in m for x in ["MAT", "매트리스", "워커힐", "에코휴", "파운데이션", "헤드보드", "PVC", "레더"]):
        return "매트리스"
    if any(x in m for x in ["구독", "선결제", "일시불", "멤버쉽"]):
        return "기타"
    return "기타"

def parse_product_name_from_col2(raw):
    """
    col2에서 모델코드와 제품명 분리.
    보통 첫 줄이 모델코드, 이후가 제품명.
    """
    if not raw:
        return "", ""
    parts = [p.strip() for p in str(raw).replace("\xa0"," ").split("\n") if p.strip()]
    if not parts:
        return "", ""
    # 첫 줄이 알파벳+숫자로 시작하면 모델코드
    first = parts[0]
    model_code = ""
    name_parts = []
    # 모델코드 패턴: 대문자/숫자 포함, 공백 없는 짧은 문자열
    if re.match(r'^[A-Z0-9\-]+$', first.replace(" ","").upper()) and len(first) < 30:
        model_code = first.strip()
        name_parts = parts[1:]
    else:
        # 모델코드가 없을 수도 있음
        name_parts = parts
    name = " ".join(name_parts).strip()
    # 괄호 안 색상/옵션 정보 제거 (제품명 정리)
    return model_code, name

def clean_option_name(col4_raw, model_code):
    """
    col4 제품 옵션명 정리
    - 모델코드 앞부분 제거
    - (3년의무) → 3년 약정
    - 라이트시리즈 prefix 정리
    """
    s = clean(col4_raw)
    # 라이트시리즈 prefix
    lite = False
    if s.startswith("라이트시리즈"):
        lite = True
        s = s[len("라이트시리즈"):].strip()
    # 모델코드 제거 (앞에 붙어있는 경우)
    if model_code and s.upper().startswith(model_code.upper()):
        s = s[len(model_code):].strip()
    # (방문) (셀프) 관리유형 제거 (col3에 이미 있음)
    s = re.sub(r'\(방문\)', '', s)
    s = re.sub(r'\(셀프\)', '', s)
    # (3년의무) → 이미 months에서 처리
    s = re.sub(r'\(\d+년의무\)', '', s)
    s = re.sub(r'\(\d+년\)', '', s)
    # 쉼표로 연결된 복수 모델코드 정리
    s = re.sub(r'[A-Z0-9,]+ASKOB|[A-Z0-9,]+ASKZG|[A-Z0-9,]+CSKSL|[A-Z0-9,]+CSKCE|[A-Z0-9,]+ASKWH|[A-Z0-9,]+ASKCE|[A-Z0-9,]+CJDG|[A-Z0-9,]+SKPN', '', s)
    s = s.strip(" ,()-+")
    if lite:
        s = ("라이트 " + s).strip()
    return s if s else ""

# ─────────────────────────────────────────────
# 메인 파서
# ─────────────────────────────────────────────

def parse_excel(filepath):
    wb = openpyxl.load_workbook(filepath, data_only=True)
    ws = wb.worksheets[0]

    # 시트명에서 월 정보 추출
    sheet_title = ws.title.strip()

    rows = list(ws.iter_rows(values_only=True))

    products = []
    current_product = None
    current_model_code = ""
    current_product_name = ""
    current_category = ""
    current_promo = ""

    # 헤더는 row 6 (index 6), 데이터는 row 7부터
    DATA_START = 7

    for i, row in enumerate(rows):
        if i < DATA_START:
            continue

        col1 = clean(row[1])   # 프로모션 정보
        col2 = row[2]           # 모델코드+제품명 (raw)
        col3 = clean(row[3])   # 관리방법
        col4 = clean(row[4])   # 제품 옵션명
        fee_guide = row[6]     # 가이드 월 요금 (col F)
        obligation = row[8]    # 의무개월 수
        ownership = clean(row[9])  # 소유권
        reg_fee = row[10]      # 등록비
        base_comm = row[11]    # 기본 수수료
        add_cnt = row[12]      # 장려 횟수
        add_comm = row[13]     # 장려1 금액
        bonus_comm = row[14]   # 장려2 금액
        total_comm = row[15]   # 총 수수료

        # 새 제품 그룹 시작 여부
        if col2 is not None and str(col2).strip():
            model_code, product_name = parse_product_name_from_col2(col2)
            if not model_code and product_name:
                # 모델코드 없음, 전체가 제품명
                model_code = ""
            # 카테고리 추론
            category = detect_category(model_code, product_name, i)
            # 특수 카테고리 (구독/선결제/일시불은 스킵)
            if "구독" in (model_code+product_name) or \
               "선결제" in (model_code+product_name) or \
               "일시불" in (model_code+product_name) or \
               "멤버쉽" in (model_code+product_name):
                current_product = None
                current_model_code = ""
                current_product_name = ""
                current_category = category
                continue

            current_product = {
                "id": (model_code or product_name[:10]).replace(" ",""),
                "modelCode": model_code,
                "name": product_name,
                "category": category,
                "promotionNote": "",
                "note": "",
                "options": []
            }
            current_model_code = model_code
            current_product_name = product_name
            current_category = category
            products.append(current_product)

        # 현재 제품이 없으면 스킵
        if current_product is None:
            continue

        # 프로모션 정보 업데이트
        if col1:
            current_product["promotionNote"] = col1

        # 관리유형이 특수 노트인 경우 (Basic, Lite 등) → 제품 note에 추가
        mgmt_type = normalize_management_type(col3)
        special_note = ""
        if col3 and mgmt_type is None:
            # 특수 노트
            special_note = clean(col3).replace("\n", " ").strip()
            if special_note and special_note not in current_product.get("note",""):
                current_product["note"] = (current_product.get("note","") + " " + special_note).strip()

        # 수치 데이터 유효성 확인
        try:
            monthly_fee = int(fee_guide) if fee_guide else 0
            months = int(obligation) if obligation else 0
            base_c = int(base_comm) if base_comm else 0
            add_c = int(add_comm) if add_comm else 0
            bonus_c = int(bonus_comm) if bonus_comm else 0
            total_c = int(total_comm) if total_comm else 0
            reg = int(reg_fee) if reg_fee else 0
        except (ValueError, TypeError):
            continue

        if monthly_fee == 0 and total_c == 0:
            continue

        # 옵션 이름 정리
        option_label = clean_option_name(col4, current_model_code)

        # 소유권 개월수 추출
        own_months = 0
        own_match = re.search(r'(\d+)', ownership)
        if own_match:
            own_months = int(own_match.group(1))

        option = {
            "label": option_label,
            "managementType": mgmt_type or "",
            "contractMonths": months,
            "contractLabel": months_to_label(months) if months else "",
            "monthlyFee": monthly_fee,
            "visitCycle": clean(row[7]),
            "ownershipMonths": own_months,
            "registrationFee": reg,
            "baseCommission": base_c,
            "additionalCount": int(add_cnt) if add_cnt else 0,
            "additionalCommission": add_c,
            "bonusCommission": bonus_c,
            "totalCommission": total_c,
        }
        current_product["options"].append(option)

    # 빈 옵션 제품 제거
    products = [p for p in products if p["options"]]

    # 중복 id 처리
    seen_ids = {}
    for p in products:
        base_id = p["id"]
        if base_id in seen_ids:
            seen_ids[base_id] += 1
            p["id"] = f"{base_id}_{seen_ids[base_id]}"
        else:
            seen_ids[base_id] = 1

    return {
        "metadata": {
            "brand": "SK매직",
            "sheetTitle": sheet_title,
            "sourceFile": os.path.basename(filepath),
            "parsedAt": datetime.now().strftime("%Y-%m-%d %H:%M")
        },
        "products": products
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        # 기본 경로 사용
        filepath = r"C:\Users\a\Documents\렌탈정책\26.04\SK 수수료표_2604v1 (1).xlsx"
    else:
        filepath = sys.argv[1]

    print(f"파싱 중: {filepath}")
    data = parse_excel(filepath)
    outfile = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sk_data.json")
    with open(outfile, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"완료: {outfile}")
    print(f"제품 수: {len(data['products'])}")
    cats = {}
    for p in data['products']:
        cats[p['category']] = cats.get(p['category'], 0) + 1
    for cat, cnt in sorted(cats.items()):
        print(f"  {cat}: {cnt}개")
