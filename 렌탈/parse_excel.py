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
    s = clean(v)
    s = re.sub(r'\n+', '\n', s)
    return s.strip()

def months_to_label(m):
    m = int(m)
    if m % 12 == 0:
        return f"{m//12}년"
    return f"{m}개월"

def normalize_management_type(raw):
    if not raw:
        return None
    s = clean(raw).replace("\n", "").replace(" ", "")
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
    year_mgmt = re.match(r'^(\d+)년\(?(방문형|셀프형|무방문형)\)?$', s)
    if year_mgmt:
        return s
    for keyword, label in patterns:
        if keyword in s:
            return label
    return None

def detect_category(model_code, product_name, row_index):
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
    if not raw:
        return "", ""
    parts = [p.strip() for p in str(raw).replace("\xa0"," ").split("\n") if p.strip()]
    if not parts:
        return "", ""
    first = parts[0]
    model_code = ""
    name_parts = []
    if re.match(r'^[A-Z0-9\-]+$', first.replace(" ","").upper()) and len(first) < 30:
        model_code = first.strip()
        name_parts = parts[1:]
    else:
        name_parts = parts
    name = " ".join(name_parts).strip()
    return model_code, name

def clean_option_name(col4_raw, model_code):
    s = clean(col4_raw)
    lite = False
    if s.startswith("라이트시리즈"):
        lite = True
        s = s[len("라이트시리즈"):].strip()

    discounts = re.findall(r'\([\d,]+원\s*할인\)', s)

    if model_code and s.upper().replace(" ","").startswith(model_code.upper().replace(" ","")):
        s = s[len(model_code):].strip()

    s = re.sub(r'^[A-Z0-9,–\-\s]+(?=\(|$)', '', s).strip()
    s = re.sub(r'\(방문\)', '', s)
    s = re.sub(r'\(셀프\)', '', s)
    s = re.sub(r'\(\d+년의무\)', '', s)
    s = re.sub(r'\(\d+년\)', '', s)
    s = re.sub(r'[A-Z0-9]+(SK|ASK|CSK)[A-Z0-9]+(,[A-Z0-9]+(SK|ASK|CSK)[A-Z0-9]+)*', '', s)
    s = s.strip(" ,()-+")

    if discounts and not any(re.search(r'[\d,]+원\s*할인', s) for _ in [1]):
        d_clean = discounts[0].strip("()").replace("  "," ")
        s = (s + " " + d_clean).strip()

    if lite:
        s = ("라이트" + (" " + s if s else "")).strip()

    return s if s else ""

# ─────────────────────────────────────────────
# 단종 모델 목록
# ─────────────────────────────────────────────
DISCONTINUED_MODELS = {'KM720R', 'QM720R', 'MAT-KM720R', 'MAT-QM720R'}

# D열 기본 관리유형 (할인 없음) → 제외 대상
BASIC_MGMT_EXCLUDE = {'방문', '셀프', '무방문형'}

# ─────────────────────────────────────────────
# 메인 파서
# ─────────────────────────────────────────────

def parse_excel(filepath):
    wb = openpyxl.load_workbook(filepath, data_only=True)
    ws = wb.worksheets[0]
    sheet_title = ws.title.strip()
    rows = list(ws.iter_rows(values_only=True))

    DATA_START = 7

    # ── 1차 스캔: 모든 모델별 할인 옵션 존재 여부 확인 ──
    # 할인 옵션이 있는 모델 → 할인 옵션만 유효
    # 할인 옵션이 없는 모델 → 기본 옵션("방문"/"셀프")도 유효 데이터
    model_has_discount = {}  # model_code(upper) → bool
    scan_model = None
    scan_is_mat = False

    for row in rows[DATA_START:]:
        col2 = row[2]
        col3 = row[3]   # D열: 관리유형 (비MAT 할인 감지)
        col4 = row[4]   # E열: 옵션명   (MAT 할인 감지)

        if col2 is not None and str(col2).strip():
            model_code, _ = parse_product_name_from_col2(col2)
            scan_model = model_code.upper() if model_code else None
            scan_is_mat = bool(scan_model and scan_model.startswith('MAT'))
            if scan_model and scan_model not in model_has_discount:
                model_has_discount[scan_model] = False

        if scan_model:
            if scan_is_mat and col4 and '할인' in str(col4):
                model_has_discount[scan_model] = True
            elif not scan_is_mat and col3 and '할인' in str(col3):
                model_has_discount[scan_model] = True

    mat_has_discount = {k: v for k, v in model_has_discount.items() if k.startswith('MAT')}
    print(f"MAT 할인 스캔 결과: {sum(1 for v in mat_has_discount.values() if v)}개 모델에 할인 옵션 존재")

    # ── 2차 처리: 메인 파싱 ──
    products = []
    current_product = None
    current_model_code = ""
    current_product_name = ""
    current_category = ""
    current_mgmt_type = ""

    for i, row in enumerate(rows):
        if i < DATA_START:
            continue

        col1 = clean(row[1])
        col2 = row[2]
        col3 = clean(row[3])
        col4 = clean(row[4])
        fee_main   = row[5]   # F열: 실제 월요금 (기준)
        fee_guide  = row[6]   # G열: 가이드 월요금 (참고, 오류감지용)
        obligation = row[8]
        ownership  = clean(row[9])
        reg_fee    = row[10]
        base_comm  = row[11]
        add_cnt    = row[12]
        add_comm   = row[13]
        bonus_comm = row[14]
        total_comm = row[15]

        # 새 제품 그룹 시작
        if col2 is not None and str(col2).strip():
            model_code, product_name = parse_product_name_from_col2(col2)
            category = detect_category(model_code, product_name, i)

            # 구독/선결제/일시불/멤버쉽 섹션 스킵
            if any(k in (model_code + product_name) for k in ["구독", "선결제", "일시불", "멤버쉽"]):
                current_product = None
                current_model_code = ""
                current_product_name = ""
                current_category = category
                continue

            # ★ 단종 제품 제외
            model_upper = model_code.upper()
            if model_upper in DISCONTINUED_MODELS or any(d in model_upper for d in ['KM720R', 'QM720R']):
                current_product = None
                current_model_code = ""
                current_product_name = ""
                current_category = category
                print(f"  단종 제외: {model_code}")
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
            current_mgmt_type = ""
            products.append(current_product)

        if current_product is None:
            continue

        if col1:
            current_product["promotionNote"] = col1

        # 관리유형 처리
        mgmt_type = normalize_management_type(col3)
        if col3 and mgmt_type is None:
            special_note = clean(col3).replace("\n", " ").strip()
            if special_note and special_note not in current_product.get("note",""):
                current_product["note"] = (current_product.get("note","") + " " + special_note).strip()
        elif col3 and mgmt_type:
            current_mgmt_type = mgmt_type
        elif not col3:
            mgmt_type = current_mgmt_type
        if mgmt_type is None:
            mgmt_type = current_mgmt_type

        # ★ D열 "방문"/"셀프" 기본 행 제외
        # 단, 해당 모델에 할인 옵션이 없으면 기본 행도 유효 데이터로 포함
        if mgmt_type in BASIC_MGMT_EXCLUDE:
            if model_has_discount.get(current_model_code.upper(), True):
                continue

        # 수치 데이터
        try:
            monthly_fee  = int(fee_main)   if fee_main   else 0   # F열 기준
            monthly_ref  = int(fee_guide)  if fee_guide  else 0   # G열 참고
            months       = int(obligation) if obligation else 0
            base_c       = int(base_comm)  if base_comm  else 0
            add_c        = int(add_comm)   if add_comm   else 0
            bonus_c      = int(bonus_comm) if bonus_comm else 0
            total_c      = int(total_comm) if total_comm else 0
            reg          = int(reg_fee)    if reg_fee    else 0
        except (ValueError, TypeError):
            continue

        if monthly_fee == 0 and total_c == 0:
            continue

        # ★ 요금 오류 감지: F열 ≠ G열이면 경고 플래그
        data_warning = (monthly_fee != 0 and monthly_ref != 0 and monthly_fee != monthly_ref)

        # ★ MAT 모델: 할인 옵션 있는 모델은 할인 옵션만 유효
        if current_category == '매트리스':
            mat_key = current_model_code.upper()
            if mat_key in mat_has_discount and mat_has_discount[mat_key]:
                if '할인' not in col4:
                    continue

        option_label = clean_option_name(col4, current_model_code)

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
            "dataWarning": data_warning,
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

    # 중복 id 처리: 같은 모델코드면 options 합치기
    merged = {}
    for p in products:
        pid = p["id"]
        if pid in merged:
            merged[pid]["options"].extend(p["options"])
        else:
            merged[pid] = p
    products = list(merged.values())

    return {
        "metadata": {
            "brand": "SK매직",
            "sheetTitle": sheet_title,
            "sourceFile": os.path.basename(filepath),
            "parsedAt": datetime.now().strftime("%Y-%m-%d %H:%M")
        },
        "products": products
    }


# ─────────────────────────────────────────────
# 접수처 비교 헬퍼
# ─────────────────────────────────────────────

def _norm_model(code):
    return re.sub(r'[\-\s]', '', str(code)).upper()

def _tl_lookup_key(model_code, tl_mgmt, years, has_tasa, is_package):
    return f"{_norm_model(model_code)}|{tl_mgmt}|{years}|{int(has_tasa)}|{int(is_package)}"

def _tl_model_variants(code):
    """에이컴즈 모델코드 → 티엘 매칭용 변형 목록 (MAT TSM→SM 등)"""
    norm = _norm_model(code)
    variants = [norm]
    # MAT-TSM… → MAT-SM… (에이컴즈 Twin-spring SS 코드 처리)
    mat_t = re.match(r'^(MAT)T(.+)$', norm)
    if mat_t:
        variants.append(f"MAT{mat_t.group(2)}")
    return variants

def extract_e_model_codes(e_val):
    """E열 값에서 모델코드 추출.
    - (N년의무/의문) 등 괄호 제거
    - 공백/하이픈 정규화
    - * → C형, F형 두 개 반환
    """
    if not e_val:
        return []
    base = re.split(r'\(', e_val)[0].strip()
    norm = re.sub(r'[\-\s]', '', base).upper()
    if not norm:
        return []
    if '*' in norm:
        return [norm.replace('*', 'C'), norm.replace('*', 'F')]
    return [norm]

def tl_match_model(norm_code, tl_known_models):
    """정규화된 에이컴즈 E열 모델코드를 TL 모델코드로 매핑.
    - 정확히 일치: 그대로 사용
    - TL 코드가 더 긴 경우 (에이컴즈 truncated): TL 코드 사용
    - 에이컴즈 코드가 더 긴 경우 (후행 색상코드): TL 코드로 트리밍
    """
    if norm_code in tl_known_models:
        return norm_code
    # TL이 더 긴 경우 (짧은 TL 코드부터 확인)
    for tl in sorted(tl_known_models, key=len):
        if tl.startswith(norm_code) and len(tl) > len(norm_code):
            return tl
    # 에이컴즈가 더 긴 경우 (긴 TL 코드부터 확인하여 가장 긴 prefix 매칭)
    matched = [tl for tl in tl_known_models if norm_code.startswith(tl)]
    if matched:
        return max(matched, key=len)
    return norm_code

def compute_recommended_office(tl_lookup, model_code, mgmt_type, contract_months, ak_commission, is_package=False):
    if "방문" in mgmt_type:
        tl_mgmt = "방문관리"
    elif "셀프" in mgmt_type:
        tl_mgmt = "셀프관리"
    else:
        return None

    years = contract_months // 12
    has_tasa = "타사보상" in mgmt_type

    tl_commission = None
    for model_key in _tl_model_variants(model_code):
        key = f"{model_key}|{tl_mgmt}|{years}|{int(has_tasa)}|{int(is_package)}"
        if key in tl_lookup:
            tl_commission = tl_lookup[key]
            break

    if tl_commission is None:
        return None  # 티엘에 대응 없음

    if ak_commission > tl_commission:
        return "에이컴즈"
    elif tl_commission > ak_commission:
        return "티엘"
    else:
        return "동일"


if __name__ == "__main__":
    if len(sys.argv) < 2:
        filepath_sk = r"C:\Users\a\Documents\렌탈정책\26.04\SK 수수료표_2604v1 (1).xlsx"
        filepath_tl = r"C:\Users\a\Documents\렌탈정책\26.04\2026.04.06 수수료.xlsx"
    else:
        filepath_sk = sys.argv[1]
        filepath_tl = sys.argv[2] if len(sys.argv) > 2 else r"C:\Users\a\Documents\렌탈정책\26.04\2026.04.06 수수료.xlsx"

    base_dir = os.path.dirname(os.path.abspath(__file__))

    # ── 티엘 파싱 (에이컴즈보다 먼저 — 모델코드 정규화에 TL 사용) ──
    tl_warning_models = []
    tl_lookup = {}
    tl_visit_cycle = {}
    tl_model_display = {}
    tl_known_models = set()
    try:
        from parse_tl_excel import parse_tl
        print(f"[티엘] 파싱 중: {filepath_tl}")
        tl_data = parse_tl(filepath_tl)
        tl_warning_models = tl_data.get("warningModels", [])
        tl_lookup = tl_data.get("optionLookup", {})
        tl_visit_cycle = tl_data.get("visitCycleLookup", {})
        tl_model_display = tl_data.get("modelDisplayMap", {})
        tl_known_models = set(k.split('|')[0] for k in tl_lookup.keys())
    except Exception as e:
        print(f"[티엘] 파싱 실패: {e}")

    # ── 에이컴즈 파싱 ──
    print(f"[에이컴즈] 파싱 중: {filepath_sk}")
    data = parse_excel(filepath_sk)

    # ── E열 모델코드 정규화 (C열 모델코드 없는 제품) ──
    # WPUTD*114 → C형(하프), F형(스탠드) 두 제품으로 분리
    normalized_products = []
    for product in data["products"]:
        if product.get("modelCode"):
            normalized_products.append(product)
            continue

        # C열 모델코드 없는 제품: E열 option label에서 모델코드 추출
        # 첫 번째 옵션의 label이 E열 원본에서 파생됨
        # parse_excel에서 이미 clean_option_name 처리됨 → 원본 E열 필요
        # → 제품명을 기반으로 별도 Excel 재스캔
        # (간소화: products에 _raw_e 저장 방식 대신, 제품명→모델코드 매핑 사전 구축)
        normalized_products.append(product)

    # E열 원본값 재스캔으로 모델코드 추출
    import openpyxl as _openpyxl
    _wb = _openpyxl.load_workbook(filepath_sk, data_only=True)
    _ws = _wb.worksheets[0]
    _rows = list(_ws.iter_rows(values_only=True))
    DATA_START_IDX = 7

    # C열 없는 제품: 제품명 → {'codes': [...], 'd_empty': bool} 매핑
    # d_empty=True: 제품 헤더 행에 D열도 비어있음 → 관리방식 상속 오염 → "방문관리" 강제
    _no_model_e_map = {}
    _cur_no_name = None
    for _row in _rows[DATA_START_IDX:]:
        _c2 = _row[2]
        _c3 = _row[3]   # D열
        _c4 = _row[4]
        if _c2 is not None and str(_c2).strip():
            _mc, _pname = parse_product_name_from_col2(_c2)
            if not _mc and _pname:
                _cur_no_name = _pname
                _e_val = clean(_c4) if _c4 else ""
                _d_val = clean(_c3) if _c3 else ""
                _raw_codes = extract_e_model_codes(_e_val)
                _matched = [tl_match_model(c, tl_known_models) for c in _raw_codes]
                _no_model_e_map[_cur_no_name] = {
                    "codes": _matched,
                    "d_empty": not _d_val,  # 헤더행 D열이 비어있으면 관리방식 상속 오염
                }
            else:
                _cur_no_name = None

    # 모델코드 없는 제품에 모델코드 적용 + * 분리
    final_products = []
    for product in data["products"]:
        if product.get("modelCode"):
            final_products.append(product)
            continue

        pname = product.get("name", "")
        info = _no_model_e_map.get(pname)

        if not info or not info["codes"]:
            final_products.append(product)
            continue

        codes = info["codes"]
        for i, norm_code in enumerate(codes):
            display_code = tl_model_display.get(norm_code, norm_code)
            p_copy = dict(product)
            p_copy["options"] = [dict(o) for o in product["options"]]
            p_copy["modelCode"] = display_code
            p_copy["id"] = norm_code

            # 제품명에서 (하프/스탠드) 제거 후 형태 suffix 추가
            if len(codes) == 2:
                base_name = re.sub(r'\s*\(하프/스탠드\)\s*', '', pname).strip()
                p_copy["name"] = base_name + (" 하프형" if i == 0 else " 스탠드형")

            # D열이 비어있던 제품만 관리방식 "방문관리" 고정
            # (D열 있는 공기청정기/비데 등은 기존 managementType 유지)
            if info["d_empty"]:
                for opt in p_copy["options"]:
                    opt["managementType"] = "방문관리"

            final_products.append(p_copy)
        try:
            print(f"  [E열 정규화] {pname} -> {[tl_model_display.get(c,c) for c in codes]}")
        except UnicodeEncodeError:
            print(f"  [E열 정규화] -> {[tl_model_display.get(c,c) for c in codes]}")

    data["products"] = final_products

    # ── 접수처 비교 + 패키지 옵션 생성 ──
    for product in data["products"]:
        model_code = product.get("modelCode", "")
        regular_opts = list(product["options"])
        package_opts = []
        seen_pkg = set()

        for opt in regular_opts:
            mgmt = opt.get("managementType", "")
            months = opt.get("contractMonths", 0)
            total_c = opt.get("totalCommission", 0)

            # 접수처 비교
            opt["recommendedOffice"] = compute_recommended_office(
                tl_lookup, model_code, mgmt, months, total_c, is_package=False
            )

            # 패키지 옵션 생성 (타사보상 제외, 중복 방지)
            if "타사보상" in mgmt:
                continue
            pkg_key = f"{mgmt}_{months}"
            if pkg_key in seen_pkg:
                continue
            seen_pkg.add(pkg_key)

            base_c  = opt.get("baseCommission", 0)
            add_c   = opt.get("additionalCommission", 0)
            bonus_c = opt.get("bonusCommission", 0)
            pkg_commission = round(base_c * 0.75) + add_c + bonus_c
            if pkg_commission <= 0:
                continue

            pkg_opt = dict(opt)
            pkg_opt["managementType"] = mgmt + "_패키지"
            pkg_opt["monthlyFee"] = max(0, opt["monthlyFee"] - 2000)
            pkg_opt["totalCommission"] = pkg_commission
            pkg_opt["isPackage"] = True
            pkg_opt["recommendedOffice"] = compute_recommended_office(
                tl_lookup, model_code, mgmt, months, pkg_commission, is_package=True
            )
            package_opts.append(pkg_opt)

        product["options"] = regular_opts + package_opts

        # 관리주기 정보 (TL G열 기준)
        for mv in _tl_model_variants(model_code):
            if mv in tl_visit_cycle:
                product["visitCycleInfo"] = tl_visit_cycle[mv]
                break

    # ── JSON 저장 ──
    json_out = os.path.join(base_dir, "sk_data.json")
    with open(json_out, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"JSON 저장: {json_out}")

    # ── HTML 생성 ──
    tpl_path = os.path.join(base_dir, "렌탈수수료_템플릿.html")
    if os.path.exists(tpl_path):
        with open(tpl_path, "r", encoding="utf-8") as f:
            html = f.read()

        sk_js  = json.dumps(data, ensure_ascii=False)
        tl_js  = json.dumps(tl_warning_models, ensure_ascii=False)
        html_out_str = html.replace("__SK_DATA__", sk_js) \
                           .replace("__TL_WARNINGS__", tl_js)

        month_tag = data["metadata"].get("parsedAt", "")[:7].replace("-","")[2:]
        out_html = os.path.join(base_dir, f"렌탈수수료_{month_tag}.html")
        with open(out_html, "w", encoding="utf-8") as f:
            f.write(html_out_str)
        print(f"HTML 저장: {out_html}")

    print(f"\n완료! 제품 수: {len(data['products'])}개")
    cats = {}
    for p in data['products']:
        cats[p['category']] = cats.get(p['category'], 0) + 1
    for cat, cnt in sorted(cats.items()):
        print(f"  {cat}: {cnt}개")
