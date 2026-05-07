"""
당현함 키워드 모니터링 - 웹 관리 화면
실행: streamlit run app.py
"""
import json
import os
import re
import glob
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

import streamlit as st
import pandas as pd

# ── 파일 경로 ──────────────────────────────────────────────
SETTINGS_FILE   = "settings.json"
KEYWORDS_FILE   = "data/keywords.json"
CHANNELS_FILE   = "data/channels.json"
RESULTS_DIR     = "results"
KW_COLLECT_DIR  = "results/collected"   # 수집된 후보 키워드 저장 위치

os.makedirs(KW_COLLECT_DIR, exist_ok=True)

# ── 공통 로드/저장 ─────────────────────────────────────────
def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def parse_qc(value):
    """네이버 검색량 값(정수 or '< 10' 등 문자열)을 정수로 변환"""
    if isinstance(value, int):
        return value
    try:
        return int(value)
    except (ValueError, TypeError):
        s = str(value).replace(",", "").strip()
        if s.startswith("<"):
            try:
                return int(s[1:].strip()) - 1
            except ValueError:
                return 0
        return 0

# ── 페이지 설정 ────────────────────────────────────────────
st.set_page_config(
    page_title="당현함 키워드 모니터",
    page_icon="📊",
    layout="wide",
)

st.title("📊 당현함 키워드 모니터링")

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📋 모니터링 키워드",
    "🔍 키워드 수집",
    "⚙️ 필터 설정",
    "🔗 채널 관리",
    "🚀 실행 & 결과",
    "⏰ 스케줄",
])


# ══════════════════════════════════════════════════════════
# TAB 1 : 모니터링 키워드 관리
# ══════════════════════════════════════════════════════════
with tab1:
    st.subheader("모니터링 키워드")
    st.caption("실제로 의뢰한 키워드만 등록합니다. 노출 체크 대상입니다.")

    keywords_data = load_json(KEYWORDS_FILE)
    changed = False

    for category in list(keywords_data.keys()):
        st.markdown(f"#### {category}")
        kws = keywords_data[category]

        col_kw, col_active, col_del = st.columns([4, 1, 1])
        col_kw.markdown("**키워드**")
        col_active.markdown("**활성**")
        col_del.markdown("**삭제**")

        to_delete = []
        for i, kw in enumerate(kws):
            c1, c2, c3 = st.columns([4, 1, 1])
            c1.text(kw["keyword"])
            new_active = c2.checkbox(
                "", value=kw.get("active", True),
                key=f"active_{category}_{i}"
            )
            if new_active != kw.get("active", True):
                keywords_data[category][i]["active"] = new_active
                changed = True
            if c3.button("삭제", key=f"del_{category}_{i}"):
                to_delete.append(i)

        for idx in reversed(to_delete):
            keywords_data[category].pop(idx)
            changed = True

        # 단일 키워드 추가
        with st.form(key=f"add_{category}"):
            new_kw = st.text_input(f"{category} 키워드 추가", placeholder="예) LG인터넷가입")
            if st.form_submit_button("추가"):
                if new_kw.strip():
                    existing = {k["keyword"] for k in keywords_data[category]}
                    if new_kw.strip() not in existing:
                        keywords_data[category].append({"keyword": new_kw.strip(), "active": True})
                    save_json(KEYWORDS_FILE, keywords_data)
                    st.rerun()

        # 엑셀 대량 붙여넣기
        with st.expander(f"📋 {category} — 대량 추가 (엑셀에서 복사·붙여넣기)"):
            st.caption("엑셀에서 키워드 셀 여러 개를 드래그 선택 후 Ctrl+C → 아래 입력창에 Ctrl+V")
            bulk_text = st.text_area(
                "키워드 목록 (한 줄에 하나씩, 탭·쉼표 구분도 지원)",
                height=150,
                placeholder="LG인터넷가입\nSK인터넷설치\nKT인터넷요금",
                key=f"bulk_{category}",
            )
            if st.button(f"대량 추가", key=f"bulk_add_{category}"):
                raw_kws = re.split(r"[\n\t,]+", bulk_text)
                new_items = [k.strip() for k in raw_kws if k.strip()]
                existing = {k["keyword"] for k in keywords_data[category]}
                added = 0
                for kw in new_items:
                    if kw not in existing:
                        keywords_data[category].append({"keyword": kw, "active": True})
                        existing.add(kw)
                        added += 1
                if added:
                    save_json(KEYWORDS_FILE, keywords_data)
                    st.success(f"{added}개 추가 완료!")
                    st.rerun()
                else:
                    st.info("추가할 새 키워드가 없습니다 (이미 등록된 키워드 제외).")

        if st.button(f"'{category}' 카테고리 전체 삭제", key=f"delcat_{category}"):
            del keywords_data[category]
            save_json(KEYWORDS_FILE, keywords_data)
            st.rerun()

        st.divider()

    with st.form("add_category"):
        new_cat = st.text_input("새 카테고리 추가", placeholder="예) 보험")
        if st.form_submit_button("카테고리 추가"):
            if new_cat.strip() and new_cat.strip() not in keywords_data:
                keywords_data[new_cat.strip()] = []
                save_json(KEYWORDS_FILE, keywords_data)
                st.rerun()

    if changed:
        save_json(KEYWORDS_FILE, keywords_data)
        st.success("저장 완료!")

    total  = sum(len(v) for v in keywords_data.values())
    active = sum(sum(1 for k in v if k.get("active", True)) for v in keywords_data.values())
    st.info(f"전체 {total}개 / 활성 {active}개")


SEED_FILE = "data/seed_keywords.json"

# ══════════════════════════════════════════════════════════
# TAB 2 : 키워드 수집 (네이버 광고 API)
# ══════════════════════════════════════════════════════════
with tab2:
    st.subheader("키워드 수집")
    st.caption("씨앗 키워드를 네이버 광고 API에 넣어 연관 키워드를 수집합니다. 모니터링 키워드와 별개입니다.")

    import config as _cfg
    api_ready = bool(_cfg.NAVER_ADS_CUSTOMER_ID)

    if not api_ready:
        st.warning("⚠️ 네이버 검색광고 API 키가 설정되지 않았습니다. config.py에 입력 후 사용 가능합니다.")

    seed_data    = load_json(SEED_FILE) if os.path.exists(SEED_FILE) else {}
    keywords_data = load_json(KEYWORDS_FILE)

    # ── 카테고리 선택 ──
    all_cats     = sorted(set(list(seed_data.keys()) + list(keywords_data.keys())))
    selected_cat = st.selectbox("카테고리 선택", all_cats, key="collect_cat")

    # ── 씨앗 키워드 편집 ──
    st.markdown("#### 씨앗 키워드")
    st.caption("많을수록 더 다양한 연관키워드가 나옵니다. 1개도 됩니다.")

    current_seeds = seed_data.get(selected_cat, [])
    seed_text = st.text_area(
        "씨앗 키워드 (한 줄에 하나씩)",
        value="\n".join(current_seeds),
        height=120,
        placeholder="예)\nlg인터넷가입\nsk인터넷설치\n인터넷가입현금지원",
    )

    if st.button("씨앗 키워드 저장"):
        seed_data[selected_cat] = [s.strip() for s in seed_text.splitlines() if s.strip()]
        save_json(SEED_FILE, seed_data)
        st.success("씨앗 키워드 저장 완료!")
        st.rerun()

    seed_kws = [s.strip() for s in seed_text.splitlines() if s.strip()]
    st.caption(f"현재 씨앗 키워드: {len(seed_kws)}개")

    # ── 수집 실행 ──
    if st.button("🔍 키워드 수집 시작", disabled=not api_ready, type="primary"):
        with st.spinner("네이버 API 조회 중..."):
            from naver_ads_api import get_related_keywords, filter_keywords, group_keywords
            raw  = get_related_keywords(seed_kws)
            filt = filter_keywords(raw)
            groups = group_keywords(filt)

        today = datetime.now().strftime("%Y-%m-%d")
        save_path = os.path.join(KW_COLLECT_DIR, f"{selected_cat}_{today}.json")
        save_json(save_path, {"category": selected_cat, "date": today, "keywords": filt})

        # 구글시트 저장
        try:
            from sheets_manager import write_keywords
            write_keywords(selected_cat, groups)
            st.success(f"수집 완료! {len(filt)}개 → 구글시트 업데이트 완료")
        except Exception as e:
            st.success(f"수집 완료! {len(filt)}개 저장")
            st.warning(f"구글시트 저장 실패: {e}")

        st.session_state[f"collect_{selected_cat}"] = filt
        st.rerun()

    # ── 수집 결과 표시 ──
    collect_key = f"collect_{selected_cat}"
    if collect_key in st.session_state and st.session_state[collect_key]:
        filt = st.session_state[collect_key]
        from naver_ads_api import group_keywords
        groups = group_keywords(filt)

        st.divider()

        # 요약 지표
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("전체", len(filt))
        m2.metric("A (1,000+)", len(groups["A_고볼륨"]))
        m3.metric("B (300~999)", len(groups["B_중볼륨"]))
        m4.metric("C (300 미만)", len(groups["C_저볼륨"]))

        # 필터 UI
        st.markdown("**결과 필터**")
        fc1, fc2, fc3 = st.columns(3)
        show_groups = fc1.multiselect(
            "그룹", ["A_고볼륨", "B_중볼륨", "C_저볼륨"],
            default=["A_고볼륨", "B_중볼륨", "C_저볼륨"]
        )
        min_mobile = fc2.number_input("모바일 검색 최소", value=0, step=100)
        comp_filter = fc3.multiselect(
            "경쟁도", ["높음", "보통", "낮음"],
            default=["높음", "보통", "낮음"]
        )

        # 필터 적용 후 테이블
        rows = []
        for g in show_groups:
            for k in groups.get(g, []):
                if parse_qc(k.get("monthlyMobileQcCnt", 0)) < min_mobile:
                    continue
                if k.get("compIdx", "") not in comp_filter:
                    continue
                rows.append({
                    "그룹":       g,
                    "키워드":     k.get("relKeyword", ""),
                    "PC검색":     parse_qc(k.get("monthlyPcQcCnt", 0)),
                    "모바일검색": parse_qc(k.get("monthlyMobileQcCnt", 0)),
                    "경쟁도":     k.get("compIdx", ""),
                })

        if rows:
            df = pd.DataFrame(rows)
            st.dataframe(df, use_container_width=True, hide_index=True, height=400)

            # 모니터링에 추가
            st.markdown("**모니터링 키워드로 추가**")
            add_kws = st.multiselect(
                "추가할 키워드 선택 (위 표에서 골라주세요)",
                options=[r["키워드"] for r in rows]
            )
            if st.button("선택 키워드를 모니터링에 추가") and add_kws:
                kw_data = load_json(KEYWORDS_FILE)
                existing_kws = {k["keyword"] for k in kw_data.get(selected_cat, [])}
                added = 0
                for kw in add_kws:
                    if kw not in existing_kws:
                        kw_data.setdefault(selected_cat, []).append({"keyword": kw, "active": True})
                        added += 1
                save_json(KEYWORDS_FILE, kw_data)
                st.success(f"{added}개 추가 완료! '모니터링 키워드' 탭에서 확인하세요.")

        else:
            st.info("필터 조건에 맞는 키워드가 없습니다.")

    else:
        st.info("수집된 결과가 없습니다. '키워드 수집 시작' 버튼을 눌러주세요.")


# ══════════════════════════════════════════════════════════
# TAB 3 : 필터 설정
# ══════════════════════════════════════════════════════════
with tab3:
    st.subheader("필터 설정")
    settings = load_json(SETTINGS_FILE)

    st.markdown("#### 글자 수 필터")
    max_chars = st.number_input(
        "이 글자 수 이하 키워드 제외",
        min_value=1, max_value=10,
        value=settings.get("filter_max_exclude_chars", 3),
        help="3 → 3글자 이하 제외 (LG, KT, 코웨이 등)"
    )

    st.markdown("#### 단독 브랜드명 제외 목록")
    st.caption("브랜드명만 있는 키워드 제외 / 브랜드+내용은 유지 (예: '코웨이' 제외, '코웨이정수기렌탈' 유지)")
    brand_text = st.text_area(
        "브랜드명 목록 (한 줄에 하나씩)",
        value="\n".join(settings.get("brand_names", [])),
        height=200,
    )

    st.markdown("#### 노출 확인 키워드")
    st.caption("본문·댓글에 하나라도 있으면 노출로 카운트")
    exposure_text = st.text_area(
        "확인 키워드 (한 줄에 하나씩)",
        value="\n".join(settings.get("exposure_keywords", ["당현함"])),
        height=100,
    )

    if st.button("💾 설정 저장", type="primary"):
        settings["filter_max_exclude_chars"] = int(max_chars)
        settings["brand_names"]       = [b.strip() for b in brand_text.splitlines() if b.strip()]
        settings["exposure_keywords"] = [e.strip() for e in exposure_text.splitlines() if e.strip()]
        save_json(SETTINGS_FILE, settings)
        st.success("설정 저장 완료!")

    with st.expander("현재 설정 확인"):
        st.json(settings)


# ══════════════════════════════════════════════════════════
# TAB 4 : 채널 관리
# ══════════════════════════════════════════════════════════
with tab4:
    st.subheader("채널 관리")
    st.caption("참고용 채널 목록입니다. 노출 판단은 본문·댓글의 키워드로만 합니다.")
    channels   = load_json(CHANNELS_FILE)
    ch_changed = False

    for ch_type, label in [("blog", "블로그"), ("cafe", "카페")]:
        st.markdown(f"#### {label}")
        ch_list = channels.get(ch_type, [])
        to_del  = []

        for i, ch in enumerate(ch_list):
            c1, c2, c3 = st.columns([2, 3, 1])
            c1.text(ch.get("name", ""))
            c2.text(ch.get("url", ""))
            if c3.button("삭제", key=f"delch_{ch_type}_{i}"):
                to_del.append(i)

        for idx in reversed(to_del):
            channels[ch_type].pop(idx)
            ch_changed = True

        with st.form(f"add_ch_{ch_type}"):
            cc1, cc2 = st.columns([2, 3])
            new_name = cc1.text_input("이름", placeholder="예) 파리지앵룩")
            new_url  = cc2.text_input("URL", placeholder="예) https://cafe.naver.com/parisienlook")
            if st.form_submit_button(f"{label} 추가"):
                if new_url.strip():
                    ch_id = new_url.strip().rstrip("/").split("/")[-1]
                    channels[ch_type].append({
                        "id":   ch_id,
                        "url":  new_url.strip(),
                        "name": new_name.strip() or ch_id,
                    })
                    ch_changed = True
                    st.rerun()

        st.divider()

    if ch_changed:
        save_json(CHANNELS_FILE, channels)
        st.success("채널 저장 완료!")


# ══════════════════════════════════════════════════════════
# TAB 5 : 실행 & 결과
# ══════════════════════════════════════════════════════════
with tab5:
    st.subheader("실행 & 결과")

    keywords_data = load_json(KEYWORDS_FILE)
    active_kws = [
        (cat, kw["keyword"])
        for cat, kws in keywords_data.items()
        for kw in kws if kw.get("active", True)
    ]
    st.info(f"활성 키워드 {len(active_kws)}개 대상으로 체크합니다.")

    if st.button("🔍 노출 체크 실행", type="primary"):
        prog_bar   = st.progress(0.0, text="준비 중...")
        c1, c2, c3 = st.columns(3)
        kw_slot    = c1.empty()
        prog_slot  = c2.empty()
        time_slot  = c3.empty()
        state_slot = st.empty()
        log_slot   = st.empty()

        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        process = subprocess.Popen(
            [sys.executable, "-u", "main.py", "--check-only"],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, encoding="utf-8", errors="replace",
            env=env,
        )

        log_lines = []
        done      = 0
        total_n   = max(len(active_kws), 1)
        start_ts  = time.time()

        for raw in process.stdout:
            line = raw.rstrip()
            if not line:
                continue
            log_lines.append(line)

            # "[1/74] [카테고리] 키워드 검색 중..."
            m = re.match(r'\[(\d+)/(\d+)\]\s+\[.*?\]\s+(.+?)\s+검색 중', line)
            if m:
                done    = int(m.group(1))
                total_n = int(m.group(2))
                cur_kw  = m.group(3)
                pct     = done / total_n
                prog_bar.progress(pct, text=f"{done}/{total_n} 완료 ({pct*100:.0f}%)")
                kw_slot.metric("현재 키워드", cur_kw)
                prog_slot.metric("진행", f"{done} / {total_n}")
                elapsed = time.time() - start_ts
                if done > 0:
                    rem = elapsed / done * (total_n - done)
                    mm, ss = divmod(int(rem), 60)
                    time_slot.metric("예상 남은 시간", f"{mm}분 {ss}초")
                state_slot.info("🔍 검색 중...")

            elif '[본문확인]' in line:
                state_slot.info("📄 본문 확인 중...")

            # "    → 8초 대기..."
            elif re.search(r'→\s*(\d+)초 대기', line):
                w = re.search(r'→\s*(\d+)초 대기', line).group(1)
                elapsed = time.time() - start_ts
                if done > 0:
                    rem = elapsed / done * (total_n - done)
                    mm, ss = divmod(int(rem), 60)
                    time_slot.metric("예상 남은 시간", f"{mm}분 {ss}초")
                state_slot.warning(f"⏳ {w}초 대기 중...")

            log_slot.code('\n'.join(log_lines[-10:]))

        process.wait()
        prog_bar.progress(1.0, text="완료!")
        state_slot.empty()

        if process.returncode == 0:
            st.success("✅ 노출 체크 완료!")
            with st.expander("실행 로그"):
                st.text('\n'.join(log_lines))
            st.rerun()
        else:
            st.error("오류 발생 — 아래 로그 확인")
            with st.expander("실행 로그", expanded=True):
                st.text('\n'.join(log_lines))

    st.divider()
    st.markdown("#### 결과 조회")
    st.caption(f"저장 위치: `{os.path.abspath(RESULTS_DIR)}`")

    result_files = sorted(glob.glob(os.path.join(RESULTS_DIR, "*.json")), reverse=True)

    if not result_files:
        st.info("아직 실행 결과가 없습니다.")
    else:
        selected = st.selectbox(
            "날짜 선택",
            options=result_files,
            format_func=lambda p: Path(p).stem
        )
        results = load_json(selected)

        total   = len(results)
        exposed = sum(1 for r in results if r.get("exposed"))
        c1, c2, c3 = st.columns(3)
        c1.metric("전체 키워드", total)
        c2.metric("노출", exposed)
        c3.metric("미노출", total - exposed)

        rows = []
        for r in results:
            if r.get("our_exposure"):
                for e in r["our_exposure"]:
                    rows.append({
                        "카테고리":   r["category"],
                        "키워드":     r["keyword"],
                        "노출":       "✅",
                        "블록명":     e.get("block_name", ""),
                        "블록순위":   e.get("block_position", ""),
                        "블록내순위": e.get("rank_in_block", ""),
                        "채널":       e.get("channel_id", ""),
                        "타입":       e.get("type", ""),
                        "발견방식":   "본문" if e.get("source") == "content" else "채널",
                        "매칭키워드": e.get("matched_keyword", "") or "",
                    })
            else:
                rows.append({
                    "카테고리":   r["category"],
                    "키워드":     r["keyword"],
                    "노출":       "❌",
                    "블록명":     "",
                    "블록순위":   "",
                    "블록내순위": "",
                    "채널":       "",
                    "타입":       "",
                    "발견방식":   "",
                    "매칭키워드": "",
                })

        df = pd.DataFrame(rows)
        st.dataframe(df, use_container_width=True, hide_index=True)

        csv = df.to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            "📥 CSV 다운로드",
            data=csv,
            file_name=f"결과_{Path(selected).stem}.csv",
            mime="text/csv"
        )

        st.caption(f"수집된 후보 키워드 위치: `{os.path.abspath(KW_COLLECT_DIR)}`")


# ══════════════════════════════════════════════════════════
# TAB 6 : 스케줄 설정
# ══════════════════════════════════════════════════════════
import signal
import psutil

SCHEDULER_PID_FILE = "scheduler.pid"
SCHEDULER_LOG_FILE = "scheduler.log"
DAY_LIST = ["월", "화", "수", "목", "금", "토", "일"]


def _scheduler_pid() -> int | None:
    if not os.path.exists(SCHEDULER_PID_FILE):
        return None
    try:
        pid = int(open(SCHEDULER_PID_FILE).read().strip())
        # 실제로 프로세스가 살아있는지 확인
        if psutil.pid_exists(pid):
            return pid
    except Exception:
        pass
    return None


def _next_run_str(days: list, time_str: str) -> str:
    from datetime import timedelta
    day_map = {"월": 0, "화": 1, "수": 2, "목": 3, "금": 4, "토": 5, "일": 6}
    day_nums = {day_map[d] for d in days if d in day_map}
    if not day_nums:
        return "요일 미설정"
    try:
        h, m = map(int, time_str.split(":"))
    except ValueError:
        return "시간 오류"
    now = datetime.now()
    for delta in range(1, 9):
        candidate = (now + timedelta(days=delta)).replace(
            hour=h, minute=m, second=0, microsecond=0
        )
        if candidate.weekday() in day_nums:
            kr = DAY_LIST[candidate.weekday()]
            return candidate.strftime(f"%Y-%m-%d ({kr}) %H:%M")
    return "계산 불가"


with tab6:
    st.subheader("자동 실행 스케줄")

    settings = load_json(SETTINGS_FILE)
    sched_changed = False

    # ── 활성화 토글 ──────────────────────────────────────
    enabled = st.toggle(
        "스케줄 활성화",
        value=settings.get("schedule_enabled", False),
        key="sched_enabled"
    )
    if enabled != settings.get("schedule_enabled", False):
        settings["schedule_enabled"] = enabled
        sched_changed = True

    st.divider()

    # ── 요일 선택 ────────────────────────────────────────
    st.markdown("#### 실행 요일")
    saved_days = settings.get("schedule_days", [])
    cols = st.columns(7)
    selected_days = []
    for i, day in enumerate(DAY_LIST):
        if cols[i].checkbox(day, value=day in saved_days, key=f"sched_day_{day}"):
            selected_days.append(day)

    if selected_days != saved_days:
        settings["schedule_days"] = selected_days
        sched_changed = True

    # ── 시간 설정 ────────────────────────────────────────
    st.markdown("#### 실행 시간")
    saved_time = settings.get("schedule_time", "09:00")
    try:
        saved_h, saved_m = map(int, saved_time.split(":"))
    except ValueError:
        saved_h, saved_m = 9, 0

    tc1, tc2 = st.columns(2)
    sel_h = tc1.number_input("시 (0~23)", min_value=0, max_value=23, value=saved_h, key="sched_h")
    sel_m = tc2.number_input("분 (0~59)", min_value=0, max_value=59, value=saved_m, step=5, key="sched_m")
    new_time = f"{int(sel_h):02d}:{int(sel_m):02d}"
    if new_time != saved_time:
        settings["schedule_time"] = new_time
        sched_changed = True

    if sched_changed:
        save_json(SETTINGS_FILE, settings)
        st.success("스케줄 저장 완료!")

    # ── 다음 실행 예정 ───────────────────────────────────
    st.divider()
    if settings.get("schedule_enabled") and settings.get("schedule_days"):
        next_run = _next_run_str(
            settings.get("schedule_days", []),
            settings.get("schedule_time", "09:00")
        )
        st.info(f"다음 실행 예정: **{next_run}**")
    else:
        st.warning("스케줄이 비활성화 상태이거나 요일이 설정되지 않았습니다.")

    # ── 스케줄러 프로세스 시작/중지 ─────────────────────
    st.divider()
    st.markdown("#### 스케줄러 프로세스")
    st.caption("스케줄러를 실행해두어야 자동 실행됩니다. 이 프로그램(app.py)과 별개로 동작합니다.")

    pid = _scheduler_pid()

    if pid:
        st.success(f"실행 중 (PID {pid})")
        if st.button("⏹ 스케줄러 중지"):
            try:
                psutil.Process(pid).terminate()
                if os.path.exists(SCHEDULER_PID_FILE):
                    os.remove(SCHEDULER_PID_FILE)
                st.success("중지 완료!")
                st.rerun()
            except Exception as e:
                st.error(f"중지 실패: {e}")
    else:
        st.error("중지 상태")
        if st.button("▶ 스케줄러 시작"):
            env = os.environ.copy()
            env["PYTHONIOENCODING"] = "utf-8"
            subprocess.Popen(
                [sys.executable, "-u", "scheduler.py"],
                env=env,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
            )
            import time as _t; _t.sleep(1)
            st.success("스케줄러 시작됨!")
            st.rerun()

    # ── 실행 로그 ────────────────────────────────────────
    st.divider()
    st.markdown("#### 스케줄러 로그")
    if os.path.exists(SCHEDULER_LOG_FILE):
        with open(SCHEDULER_LOG_FILE, encoding="utf-8") as f:
            lines = f.readlines()
        st.code("".join(lines[-30:]), language=None)
        if st.button("로그 초기화"):
            open(SCHEDULER_LOG_FILE, "w").close()
            st.rerun()
    else:
        st.info("로그 없음")
