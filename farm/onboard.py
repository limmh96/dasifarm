"""판매처(청년농)·구매처 등록 흐름 (팀 결정):
① 공공데이터 불러오는 중 → ② 불러온 값 확인 → ③ 없는 정보만 직접 입력 → 저장 → 매칭 화면
"""
import time
import streamlit as st
from . import ui
from .data import public_farmer, public_buyer, save_farmer, save_buyer

GRADES = ["무관", "중", "상", "특"]
GRADE_NUM = {"무관": 1, "중": 2, "상": 3, "특": 4}
COORDS = {"평창": (37.37, 128.39), "강릉": (37.75, 128.88), "정선": (37.38, 128.66), "원주": (37.34, 127.92),
          "춘천": (37.88, 127.73), "삼척": (37.45, 129.17), "홍천": (37.69, 127.89)}

# (키, 화면 이름, 입력 종류, 기본값, 선택지)
FARMER_FIELDS = [
    ("name", "농가 이름", "text", "", None),
    ("region", "지역", "text", "평창군 진부면", None),
    ("items", "품목", "multi", ["감자"], ["감자", "토마토"]),
    ("certs", "보유 인증", "multi", [], ["GAP", "무농약", "유기농"]),
    ("boxes", "주당 출하량 (20kg 상자)", "int", 30, None),
    ("wish", "희망 단가 (원/20kg 상자)", "money", 24000, None),
    ("grade", "주로 낼 수 있는 등급", "slider", "상", GRADES),
    ("months", "출하 가능 월", "multi", [8, 9, 10], list(range(1, 13))),
    ("days", "납품 가능 요일", "multi", ["화", "목"], list("월화수목금토")),
    ("truck", "직접 배송할 트럭이 있어요", "check", True, None),
]
BUYER_FIELDS = [
    ("name", "구매처 이름", "text", "", None),
    ("type", "유형", "select", "식당", ["식당", "반찬가게", "마트", "도매상", "식자재업체", "로컬푸드 직매장", "학교급식", "공공급식"]),
    ("location", "지역", "text", "강릉시", None),
    ("items", "필요한 품목", "multi", ["감자"], ["감자", "토마토"]),
    ("cert", "꼭 필요한 인증", "select", "", ["", "GAP", "무농약", "유기농"]),
    ("weekly_kg", "주당 필요량 (kg)", "int", 200, None),
    ("days", "납품 받는 요일", "multi", ["화"], list("월화수목금토")),
    ("price", "단가 (원/20kg 상자)", "money", 25000, None),
    ("min_grade", "최소 등급", "slider", "상", GRADES),
    ("months", "필요한 월", "multi", [7, 8, 9, 10, 11], list(range(1, 13))),
    ("delivery", "받는 방식", "select", "직접 트럭 납품", ["직접 트럭 납품", "택배", "구매처가 수거"]),
    ("settlement", "정산", "select", "월말 일괄", ["월말 일괄", "주 단위", "납품 즉시"]),
]
CFG = {
    "farmer": dict(title="판매처(청년 농가)", fields=FARMER_FIELDS, lookup=public_farmer,
                   key_label="농가 이름 또는 GAP 인증번호", key_ph="예: 다시농장 / GAP-2025-0731",
                   steps=["농산물우수관리(GAP) 인증 정보 확인 중", "지역·품목 정리 중", "매칭 기준에 맞춰 정리 중"]),
    "buyer": dict(title="구매처", fields=BUYER_FIELDS, lookup=public_buyer,
                  key_label="구매처(기관) 이름", key_ph="예: 강릉학교급식지원센터",
                  steps=["공공급식 식재료 정보 확인 중", "품목·물량·요일 정리 중", "매칭 기준에 맞춰 정리 중"]),
}


def _widget(f, value, wkey):
    k, label, kind, default, opts = f
    v = default if value is None else value
    if kind == "text":
        return st.text_input(label, v, key=wkey)
    if kind == "multi":
        return st.multiselect(label, opts, [x for x in v if x in opts], key=wkey)
    if kind == "int":
        return st.number_input(label, 0, 100000, int(v), key=wkey)
    if kind == "money":
        return st.number_input(label, 0, 300000, int(v), step=1000, key=wkey)
    if kind == "slider":
        return st.select_slider(label, opts, v, key=wkey)
    if kind == "select":
        return st.selectbox(label, opts, opts.index(v) if v in opts else 0, key=wkey,
                            format_func=lambda x: x or "필요 없음")
    if kind == "check":
        return st.checkbox(label, bool(v), key=wkey)


def _show(v):
    if isinstance(v, list):
        return ", ".join(map(str, v)) or "없음"
    return str(v) if v not in ("", None) else "필요 없음"


def _coords(text):
    return next((v for k, v in COORDS.items() if k in str(text)), (37.64, 128.57))


def _to_farmer(d):
    la, lo = _coords(d["region"])
    return {"name": d["name"] or "새 농가", "region": d["region"], "lat": la, "lng": lo, "size": "등록",
            "items": d["items"], "variety": "", "grade": GRADE_NUM[d["grade"]], "weekly_kg": int(d["boxes"]) * 20,
            "months": d["months"], "days": d["days"], "wish_price_kg": d["wish"] / 20, "certs": d["certs"],
            "truck": "Y" if d["truck"] else "N", "intro": f"{d['region']} {','.join(d['items'])} 주 {d['boxes']}상자"}


def _to_buyer(d, src):
    la, lo = d.get("lat") or _coords(d["location"])[0], d.get("lng") or _coords(d["location"])[1]
    return {"name": d["name"] or "새 구매처", "type": d["type"], "size": "등록", "source": src, "from_farmer": "—",
            "location": d["location"], "lat": la, "lng": lo, "items": d["items"], "min_grade": GRADE_NUM[d["min_grade"]],
            "weekly_kg": int(d["weekly_kg"]), "price_kg": d["price"] / 20, "months": d["months"], "days": d["days"],
            "delivery": d["delivery"], "settlement": d["settlement"], "cert": d["cert"],
            "raw_text": f"{d['name']} {d['type']} {d['location']} {','.join(d['items'])} 주 {d['weekly_kg']}kg"}


def run(kind, on_done):
    """on_done(saved_row) : 저장 후 이동할 곳"""
    c = CFG[kind]
    s = st.session_state.setdefault(f"onb_{kind}", {"step": "input", "found": None, "data": {}})
    fields = c["fields"]
    step = s["step"]
    n = {"input": 1, "loading": 1, "confirm": 2, "missing": 3}[step]
    ui.crumb(f"{c['title']} 등록", f"{n}/3 단계", icon="user")

    # ① 키 입력 + 동의
    if step == "input":
        ui.hero(f"{c['title']} 등록", "공공데이터에서<br>정보를 먼저 불러올게요",
                "있는 정보는 미리 채워 드리고, 없는 정보만 여쭤볼게요.")
        with st.container(key="wcard_onb_in"):
            key = st.text_input(c["key_label"], placeholder=c["key_ph"], key=f"onb_key_{kind}")
            agree = st.checkbox("공공데이터 조회와 매칭을 위한 정보 활용에 동의합니다", key=f"onb_ok_{kind}")
            if st.button("공공데이터 불러오기", type="primary", width="stretch", disabled=not (key and agree)):
                s.update(step="loading", key=key); st.rerun()
            if st.button("공공데이터 없이 직접 입력", width="stretch", disabled=not agree):
                s.update(step="missing", found=None, data={}); st.rerun()

    # ①-2 불러오는 중
    elif step == "loading":
        ui.hero(f"{c['title']} 등록", "공공데이터를<br>불러오는 중이에요", f"'{s['key']}'(으)로 찾고 있어요.")
        with st.container(key="gcard_onb_load"):
            bar = st.progress(0, text=c["steps"][0])
            for i, t in enumerate(c["steps"]):
                bar.progress(int((i + 1) / len(c["steps"]) * 100), text=t)
                time.sleep(float(__import__("os").environ.get("ONB_DELAY", "0.6")))
        found = c["lookup"](s["key"])
        s.update(found=found, data=dict(found or {}), step="confirm" if found else "missing")
        st.rerun()

    # ② 불러온 값 확인 (고칠 수 있음)
    elif step == "confirm":
        f = s["found"]
        ui.hero(f"{c['title']} 등록", "불러온 정보가<br>맞는지 확인해 주세요", "다른 부분이 있으면 바로 고쳐 주세요.")
        with st.container(key="gcard_onb_conf"):
            ui.html(ui.chip("공공데이터") + ui.chip(f.get("_src", ""), "color/text-sub"))
            with st.form(f"conf_{kind}"):
                vals = {fd[0]: _widget(fd, f[fd[0]], f"cf_{kind}_{fd[0]}") for fd in fields if fd[0] in f}
                ok = st.form_submit_button("맞아요, 다음", type="primary", width="stretch")
            if ok:
                s["data"].update(vals); s["step"] = "missing"; st.rerun()
        with st.container(key="pad_onb_retry"):
            if st.button("다른 이름으로 다시 찾기", width="stretch"):
                s.update(step="input", found=None, data={}); st.rerun()

    # ③ 없는 정보만 입력
    elif step == "missing":
        filled = {k: v for k, v in s["data"].items() if not k.startswith("_") and k != "cert_no"}
        todo = [fd for fd in fields if fd[0] not in filled]
        if s["found"] is None:
            ui.hero(f"{c['title']} 등록", "공공데이터에서<br>찾지 못했어요" if s.get("key") else "정보를<br>입력해 주세요",
                    "아래 정보를 직접 입력해 주세요.")
        else:
            ui.hero(f"{c['title']} 등록", "없는 정보를<br>입력해 주세요", f"공공데이터로 {len(filled)}개 항목을 채웠어요. 나머지 {len(todo)}개만 입력하면 끝나요.")
            with st.container(key="wcard_onb_filled"):
                ui.html("<p class='df-card-title'>확인된 정보</p>" + "".join(
                    ui.kv(fd[1], _show(filled[fd[0]])) for fd in fields if fd[0] in filled))
        with st.container(key="gcard_onb_miss"):
            with st.form(f"miss_{kind}"):
                vals = {fd[0]: _widget(fd, None, f"ms_{kind}_{fd[0]}") for fd in todo}
                ok = st.form_submit_button("등록하고 매칭 보기", type="primary", width="stretch")
            if ok:
                d = {**{fd[0]: fd[3] for fd in fields}, **filled, **vals}
                if kind == "farmer":
                    row = _to_farmer(d); save_farmer(row)
                else:
                    row = _to_buyer(d, "공공데이터" if s["found"] else "직접 입력"); save_buyer(row)
                st.session_state.pop(f"onb_{kind}")
                on_done(row)
                st.rerun()
