"""다시, FARM — 피그마(Figma Make) 디자인을 Streamlit으로 옮긴 시연 앱
AI가 쓰이는 곳
  ① 은퇴 농업인: AI가 질문 → 말로 답함 → Gemini 받아쓰기 → 다음 질문 → 거래처 조건 표로 정리 (farm/voice.py)
  ② 판로 찾기·추천 농가: 매칭 AI 적합도 분석 (farm/matching.py — 기준 점수 + Gemini 임베딩 유사도 + Gemini 설명)
실행: streamlit run app.py
"""
import os
import time
import base64
import datetime as dt
import pandas as pd
import streamlit as st

from farm import ai, fui, voice, matching
from farm.fui import html, icon, esc, title
from farm.data import (load_buyers, load_farmers, save_buyer, save_farmer, save_trial, list_trials,
                       save_retiree, public_farmer, public_buyer)
from farm.onboard import COORDS

st.set_page_config(page_title="다시, FARM", page_icon="static/assets/dasi-farm-logo.png", layout="centered",
                   initial_sidebar_state="collapsed")
fui.inject()

# 피그마 버튼은 모두 가로 꽉 차게 (width="stretch"가 기본이 되도록)
_button, _submit = st.button, st.form_submit_button
st.button = lambda *a, **k: _button(*a, **{"width": "stretch", **k})
st.form_submit_button = lambda *a, **k: _submit(*a, **{"width": "stretch", **k})

for k in ("GEMINI_API_KEY", "KAKAO_JS_KEY"):        # 키는 Streamlit Secrets에만
    try:
        if k in st.secrets and not os.environ.get(k):
            os.environ[k] = st.secrets[k]
    except Exception:
        pass

S = st.session_state
S.setdefault("page", "welcome")
S.setdefault("role", "seller")
S.setdefault("hist", [])
S.setdefault("f", {})            # 가입 정보
S.setdefault("filter", "전체")
GRADES = {"무관": 1, "중": 2, "상": 3, "특": 4}
GNAME = {v: k for k, v in GRADES.items()}
ROLES = [("seller", "농산물 판매처", "판매 농가", "내 농산물의 첫 판로를 찾고 싶어요", "sprout"),
         ("buyer", "농산물 구매처", "구매 파트너", "우리에게 맞는 농가를 만나고 싶어요", "shop"),
         ("senior", "은퇴 농업인", "경험 파트너", "쌓아온 거래처를 다음 농부에게 잇고 싶어요", "heart")]


def go(p, **kw):
    S.hist.append(S.page)
    S.page = p
    S.update(kw)


def back():
    if S.hist:
        S.page = S.hist.pop()


def reset():
    for k in list(S.keys()):
        del S[k]


def coords(text):
    return next((v for k, v in COORDS.items() if k in str(text)), (37.64, 128.57))


# ───────────────────────── 공통: 헤더 · 하단 메뉴 ─────────────────────────
NAV = {"seller": [("내 농장", "home", "home"), ("미션", "mission", "missions"), ("판로", "shop", "market"), ("나의", "user", "profile")],
       "buyer": [("홈", "home", "home"), ("납품 조건", "mission", "conditions"), ("추천 농가", "sprout", "farms"), ("나의", "user", "profile")],
       "senior": [("홈", "home", "home"), ("거래 경험", "mic", "interview"), ("거래처", "box", "experiences")]}
NAV_PAGES = {p for v in NAV.values() for _, _, p in v} | {"detail", "apply", "farmdetail"}


def header(page):
    if page in ("welcome", "splash"):
        return
    main_tab = S.get("registered") and page in {p for _, _, p in NAV[S.role]}
    with st.container(key="hdr", horizontal=True, vertical_alignment="center"):
        if main_tab:
            html(f'<div class="brand"><span class="brand-symbol">{icon("sprout", 22)}</span>다시<span class="brand-comma">,</span> <b>FARM</b></div>')
            html(f'<span class="notification" style="color:var(--farm-main-text);display:grid;place-items:center;width:44px;height:44px">{icon("bell")}<i></i></span>')
        else:
            with st.container(key="ov_back", width=44):
                html(f'<span style="display:grid;place-items:center;width:44px;height:44px;color:var(--farm-main-text)">{icon("back")}</span>')
                st.button("뒤로", key="btn_back", on_click=back, disabled=page in ("loading", "transcribing"))
            if S.role == "senior":
                html('<span class="header-caption">경험 나누기</span>')


def bottom_nav(page):
    if not (S.get("registered") and page in NAV_PAGES):
        return
    html('<div class="with-nav-space"></div>')
    with st.container(key="bnav", horizontal=True):
        for i, (label, ic, p) in enumerate(NAV[S.role]):
            act = "active" if page == p else ""
            fui.overlay(f"nav{i}", f'<div class="nav-item {act}">{icon(ic, 23)}<span>{label}</span></div>', go, args=(p,))


def demo_banner():
    if not ai.has_ai():
        html('<div class="demo-note"><span class="demo-dot"></span>데모 모드: Gemini 키가 없어 예시 데이터로 보여줘요</div>')


# ───────────────────────── 화면 ─────────────────────────
def page_splash():
    html('<style>[data-testid="stMainBlockContainer"]{padding:0!important}</style>'
         '<section class="splash-screen" style="height:100dvh;animation:none">'
         '<img class="splash-logo" src="/app/static/assets/dasi-farm-logo.png" alt="다시, 팜 Dasi Farm"></section>')
    time.sleep(2.2)
    S.page = "welcome"
    st.rerun()


def page_welcome():
    if not S.get("splashed"):            # 다시팜 시작 화면(팝업): 서버 대기 없이 CSS로 2.4초 보여주고 사라짐
        S.splashed = True
        html('<div class="splash-pop"><img src="/app/static/assets/dasi-farm-logo.png" alt="다시, 팜 Dasi Farm"></div>')
    html('<style>[data-testid="stMainBlockContainer"]{background:linear-gradient(174deg,var(--farm-gradient-start) 0%,var(--farm-background) 68%)!important}</style>')
    fui.steps(1)
    html(f'<section class="welcome-hero">{fui.FARM_SVG}</section>')
    html('<div class="welcome-title"><span class="eyebrow">반가워요, 다시팜이에요</span>'
         '<h1>어떤 고객이세요?</h1><p>나에게 맞는 첫걸음을 준비해 드릴게요.</p></div>')
    with st.container(key="roles"):
        for rid, t, tag, desc, ic in ROLES:
            sel = "selected" if S.role == rid else ""
            card = (f'<div class="role-card {rid} {sel}"><span class="role-icon">{icon(ic, 28)}</span>'
                    f'<span class="role-copy"><span class="role-title">{t}<span class="role-tag">{tag}</span></span>'
                    f'<span class="role-desc">{desc}</span></span>'
                    f'<span class="radio-circle">{icon("check", 15) if sel else ""}</span></div>')
            fui.overlay(f"role_{rid}", card, lambda r=rid: S.update(role=r))
        html(f'<p class="role-help">{icon("leaf", 15)}‘판매처’는 농산물을 직접 판매하는 농가를 뜻해요.</p>')
    with st.container(key="wbottom"):
        st.button("다음", type="primary", key="next", on_click=go, args=("interview" if S.role == "senior" else "import",))
        html("<p>서로의 경험이 모여, 더 단단한 농업으로</p>")


def page_import():
    fui.steps(2)
    seller = S.role == "seller"
    title("정보 등록 · 1 / 3", "입력은 가볍게,\n시작은 간편하게", "기본 정보를 불러오면 필요한 내용만 채울 수 있어요.")
    html(f'<div class="mini-art">{icon("sprout" if seller else "shop", 46)}</div>')
    fui.hint()
    name = st.text_input("대표자 이름", S.f.get("name", ""), placeholder="이름을 입력해 주세요")
    idlabel = "농업경영체 등록번호 / GAP 인증번호" if seller else "사업자등록번호 / 기관 이름"
    rid = st.text_input(idlabel, S.f.get("id", ""), placeholder="시연: GAP-2025-0731 / 강릉학교급식" if seller else "시연: 강릉학교급식")
    html('<p class="helper">끝 4자리가 0000이거나 공공데이터에 없으면 ‘조회 결과 없음’을 체험해요.</p>')
    if st.button("정보 불러오기", type="primary"):
        if not name.strip() or not rid.strip():
            st.error("필수 정보를 입력해 주세요.")
        else:
            S.f.update(name=name, id=rid)
            go("loading"); st.rerun()
    st.button("직접 입력할게요", on_click=lambda: (S.f.update(name=name, id=rid, manual=True), go("missing")))


def page_loading():
    fui.hide_stale()
    fui.steps(2)
    html('<div class="loading-page" style="height:auto;padding:90px 0 30px"><div class="spinner"></div>'
         '<h1>기본 정보를 불러오고 있어요</h1><p>잠시만 기다려 주세요.<br>공공데이터에서 등록 정보를 찾고 있어요.</p></div>')
    fui.hint()
    time.sleep(0.9)
    key = S.f.get("id", "")
    hit = None if key.endswith("0000") else (public_farmer(key) if S.role == "seller" else public_buyer(key))
    if hit is None and S.role == "seller" and not key.endswith("0000"):
        hit = public_farmer("다시농장")            # 시연: 아무 번호나 넣으면 예시 농가로 채움
    S.f["public"] = hit
    S.page = "confirm" if hit else "notfound"
    st.rerun()


def page_notfound():
    fui.steps(2)
    title("조회 결과 없음", "조회된 정보가 없어요", "괜찮아요. 직접 입력해도 다시팜을 시작할 수 있어요.")
    html(f'<div class="mini-art">{icon("edit", 45)}</div>')
    fui.hint()
    st.button("직접 입력하기", type="primary", on_click=lambda: (S.f.update(manual=True), go("missing")))


def page_confirm():
    fui.steps(2)
    h = S.f["public"]
    seller = S.role == "seller"
    title("정보 등록 · 2 / 3", "불러온 정보를\n확인해 주세요", "다른 내용이 있다면 바로 수정할 수 있어요.")
    html(f'<div class="info-banner">{icon("check", 20)}<div>공공데이터에서 기본 정보를 불러왔어요'
         f'<p>출처: {"농산물우수관리(GAP) 인증정보" if seller else "공공급식 식재료 정보"} (시연용 가상 데이터)</p></div></div>')
    name = st.text_input("대표자 이름", S.f.get("name", ""))
    biz = st.text_input("농장 이름" if seller else "사업장 이름", h["name"])
    region = st.text_input("소재지", h.get("region") or h.get("location", ""))
    crop = st.text_input("주요 생산 품목" if seller else "구매 품목", ", ".join(h.get("items", [])))
    extra = (f"보유 인증 · {', '.join(h.get('certs', []))}" if seller else
             f"주당 사용량 {h.get('weekly_kg')}kg · 납품 {'/'.join(h.get('days', []))} · 요구 인증 {h.get('cert') or '없음'}")
    html(f'<div class="source-box">공공데이터에서 함께 불러온 정보<p>{esc(extra)}</p></div>')
    fui.hint()
    if st.button("이 정보가 맞아요", type="primary"):
        S.f.update(name=name, business=biz, region=region, crop=[c.strip() for c in crop.split(",") if c.strip()], manual=False)
        go("missing"); st.rerun()


def page_missing():
    fui.steps(2)
    seller = S.role == "seller"
    pub = S.f.get("public") or {}
    manual = S.f.get("manual") or not pub
    title("정보 등록 · 3 / 3", "조금만 더 알려주시면\n준비가 끝나요", "맞는 거래 상대를 찾기 위해 필요한 정보예요.")
    with st.form("missing"):
        if manual:
            name = st.text_input("대표자 이름 *", S.f.get("name", ""), placeholder="예: 김초록")
            biz = st.text_input(("농장 이름" if seller else "사업장 이름") + " *", placeholder="이름을 입력해 주세요")
            region = st.text_input("소재지 *", placeholder="예: 강원 평창군 진부면")
            crop = st.multiselect(("생산 품목" if seller else "구매 희망 품목") + " *", ["감자", "토마토"], ["감자"])
        if seller:
            boxes = st.number_input("주당 출하 가능 물량 (20kg 상자) *", 1, 2000, 30)
            wish = st.number_input("희망 단가 (원 / 20kg 상자) *", 1000, 200000, 26000, step=1000)
            grade = st.select_slider("주로 낼 수 있는 등급", list(GRADES), "상")
            months = st.multiselect("출하 가능 월", list(range(1, 13)), [8, 9, 10, 11], format_func=lambda m: f"{m}월")
            days = st.multiselect("납품 가능 요일", list("월화수목금토"), ["화", "목"])
            truck = st.checkbox("직접 배송할 트럭이 있어요", True)
        else:
            kg = st.number_input("주당 필요한 물량 (kg) *", 10, 50000, int(pub.get("weekly_kg") or 200))
            price = st.number_input("단가 (원 / 20kg 상자) *", 1000, 200000, 25000, step=1000)
            grade = st.select_slider("최소 등급", list(GRADES), "상")
            months = st.multiselect("필요한 월", list(range(1, 13)), [7, 8, 9, 10, 11], format_func=lambda m: f"{m}월")
            days = st.multiselect("납품 받는 요일", list("월화수목금토"), pub.get("days") or ["화"])
            deliv = st.selectbox("받는 방식", ["직접 트럭 납품", "택배", "구매처가 수거", "화물 용달"])
        note = st.text_input("추가로 알리고 싶은 조건 (선택)", placeholder="예: 크기별 선별 가능, 세척 출하")
        html('<p class="helper">* 필수 정보예요. 입력한 내용은 이번 시연에서만 유지돼요.</p>')
        ok = st.form_submit_button("등록 완료하기", type="primary")
    if ok:
        if manual:
            S.f.update(name=name, business=biz, region=region, crop=crop)
        if not (S.f.get("business") and S.f.get("crop")):
            st.error("필수 정보를 입력해 주세요."); return
        la, lo = coords(S.f["region"])
        if seller:
            row = {"name": S.f["business"], "region": S.f["region"], "lat": la, "lng": lo, "size": "등록",
                   "items": S.f["crop"], "variety": "", "grade": GRADES[grade], "weekly_kg": boxes * 20, "months": months,
                   "days": days, "wish_price_kg": wish / 20, "certs": pub.get("certs", []), "truck": "Y" if truck else "N",
                   "intro": f"{S.f['region']} {','.join(S.f['crop'])} 주 {boxes}상자 {note}"}
            save_farmer(row)
        else:
            row = {"name": S.f["business"], "type": pub.get("type", "구매처"), "size": "등록",
                   "source": "공공데이터" if pub else "직접 입력", "from_farmer": "—", "location": S.f["region"],
                   "lat": pub.get("lat", la), "lng": pub.get("lng", lo), "items": S.f["crop"], "min_grade": GRADES[grade],
                   "weekly_kg": kg, "price_kg": price / 20, "months": months, "days": days, "delivery": deliv,
                   "settlement": "", "cert": pub.get("cert", ""), "raw_text": f"{S.f['business']} {note}"}
            save_buyer(row)
        S.f["row"] = row
        S.registered = True
        go("registered"); st.rerun()


def page_registered():
    fui.steps(3)
    seller = S.role == "seller"
    fui.success("반가워요!\n이제 함께 시작해요",
                f"{S.f.get('business', '')}의 기본 정보가 등록됐어요. " +
                ("AI가 우리 농장에 맞는 판로를 찾아볼게요." if seller else "AI가 우리 조건에 맞는 농가를 찾아볼게요."))
    st.button("판로 찾으러 가기" if seller else "추천 농가 보기", type="primary", on_click=go, args=("market" if seller else "farms",))


# ── AI 적합도 분석 (판매처 → 구매처)
def fit_progress(n_targets, what):
    fui.hide_stale()
    box = st.empty()
    labels = [f"{what} {n_targets}곳의 필수 조건(품목·인증) 확인",
              "생산량 · 품질 · 출하 시기 · 납품 주기 · 거리 · 가격 · 인증 점수 계산",
              "거래 조건 ↔ 소개 문장 의미 비교 (" + ("Gemini 임베딩" if ai.has_ai() else "데모: 글자 비교") + ")",
              "매칭률 계산"]
    for i in range(len(labels) + 1):
        steps_html = "".join(f'<div class="{"on" if j < i else ""}"><b>{icon("check", 13) if j < i else j + 1}</b>{l}</div>'
                             for j, l in enumerate(labels))
        with box.container():
            html(f'<div class="loading-page" style="height:auto;padding:30px 0 10px;gap:18px"><div class="spinner"></div>'
                 f'<h1 style="font-size:24px">AI가 적합도를 분석하고 있어요</h1><div class="ai-steps">{steps_html}</div></div>')
        time.sleep(0.3)
    box.empty()


def me_farmer():
    r = S.f.get("row")
    if r and S.role == "seller":
        return r
    df = load_farmers()
    return df.set_index("name").loc["청년농D"].to_dict() | {"name": "청년농D"}


TAG = {"로컬푸드": ["로컬푸드 직매장"], "급식": ["학교급식", "공공급식"], "식당": ["식당", "반찬가게"], "도매·마트": ["도매상", "마트", "식자재업체"]}


def page_market():
    y = me_farmer()
    title("AI가 찾은 연결", "우리 농산물을\n기다리는 곳", "구매처의 조건과 우리 농장을 AI가 비교했어요. 첫 거래를 준비해 보세요.")
    q = st.text_input("검색", placeholder="지역 또는 품목 검색", label_visibility="collapsed")
    with st.container(key="filters", horizontal=True):
        for f in ["전체", *TAG]:
            st.button(f, key=f"flt_{f}", type="primary" if S.filter == f else "secondary", width="content", on_click=lambda f=f: S.update(filter=f))
    buyers = load_buyers()
    fk = (y["name"], len(buyers))
    if S.get("fit_key") != fk:
        fit_progress(len(buyers), "구매처")
        S.fit = matching.recommend_for_farmer(farmer=y, top=50)
        S.fit_key = fk
    res, excluded = S.fit
    shown = [r for r in res if (S.filter == "전체" or r["구매처유형"].split(" · ")[-1] in TAG[S.filter])
             and (not q or q.replace(" ", "") in (r["거래처"] + r["구매처유형"]).replace(" ", ""))]
    fui.section("AI 추천 구매처", f"{len(shown)}곳 · 적합도 순")
    for i, r in enumerate(shown):
        b = buyers.set_index("name").loc[r["거래처"]]
        gaps = " · ".join(g.split(" (")[0] for g in r["부족한조건"]) or "조건 모두 충족"
        card = (f'<div class="market-card" style="display:block"><div class="market-picture picture-{i % 3}">{icon("shop", 44)}'
                f'<span>{esc(b["type"])}</span><div class="ai-badge">{icon("spark", 14)} AI 적합도 {r["매칭률"]}%</div></div>'
                f'<div class="market-copy"><span class="eyebrow">{esc(b["location"])} · {r["거리km"]}km</span>'
                f'<div style="display:flex;justify-content:space-between;align-items:center"><h2>{esc(r["거래처"])}</h2>{icon("arrow", 18)}</div><p>{"/".join(b["items"])} · 주 {int(b["weekly_kg"]):,}kg · {"/".join(b["days"]) or "요일 협의"}</p>'
                f'<div class="condition-line">부족한 조건: {esc(gaps)}</div>'
                f'<span class="source">{esc(r["출처"])}{" · " + esc(r["농가"]) + " 거래처" if r["농가"] not in ("—", "", None) else ""}</span></div></div>')
        fui.overlay(f"mk{i}", card, go, args=("detail",), kwargs={"sel": r})
    if not shown:
        html('<p class="helper">조회된 구매처가 없어요. 다른 지역이나 품목으로 검색해 주세요.</p>')
    if excluded:
        html(f'<p class="helper">품목·필수 인증이 맞지 않아 제외된 구매처 {len(excluded)}곳: '
             + esc(", ".join(f"{e['거래처']}({e['제외 이유']})" for e in excluded)) + "</p>")


def page_detail():
    r = S.get("sel")
    if not r:
        return go("market")
    b = load_buyers().set_index("name").loc[r["거래처"]]
    html(f'<div class="detail-visual">{icon("shop", 64)}<span class="chip">시험 납품부터 시작</span></div>')
    title(f"구매처 상세 · {r['출처']}", r["거래처"], f"{b['location']} · {b['type']}")
    src = f"{r['농가']}의 음성 인터뷰 (은퇴 농업인)" if r["출처"] == "은퇴농 구술" else r["출처"]
    html(f'<div class="source-box">정보 출처: {esc(src)}<p>실제 거래 전 구매처와 조건을 다시 확인해 주세요.</p></div>')
    fui.section("AI 적합도 분석")
    bars = "".join(fui.score_bar(k, v, f"· 비중 {matching.WEIGHTS[k]}") for k, v in r["항목점수"].items())
    html(f'<div class="goal-card"><div style="display:flex;justify-content:space-between;align-items:center">'
         f'<span class="ai-badge">{icon("spark", 14)} 매칭 AI</span><span class="fit-pct">{r["매칭률"]}%</span></div>{bars}</div>')
    fui.section("이런 조건으로 납품해요")
    html(fui.kv([("희망 품목", "/".join(b["items"])), ("주당 물량", f"{int(b['weekly_kg']):,}kg"),
                 ("단가", f"{int(b['price_kg']):,}원/kg"),
                 ("납품 일정", f"{min(b['months'])}~{max(b['months'])}월 · {'/'.join(b['days']) or '협의'}"),
                 ("받는 방식", b["delivery"] or "협의"), ("정산", b["settlement"] or "협의")]))
    if S.get("exp_for") != (r["거래처"], r["청년농"]):
        with st.spinner("AI가 추천 이유를 정리하고 있어요"):
            S.exp, S.exp_for = matching.explain(r), (r["거래처"], r["청년농"])
    html(f'<div class="feedback-card"><span class="chip">AI 추천 이유 · {"Gemini" if ai.has_ai() else "데모"}</span>'
         f'<p>{esc(S.exp).replace(chr(10), "<br>")}</p></div>')
    st.button("시험 납품 신청하기", type="primary", on_click=go, args=("apply",))


def page_apply():
    r = S.get("sel")
    title("첫 거래를 향한 한 걸음", "시험 납품을\n제안해 볼까요?", f"{r['거래처']}에 보낼 내용을 확인해 주세요.")
    with st.form("apply"):
        item = st.text_input("납품 품목 *", ", ".join(S.f.get("crop", [])) or "감자")
        qty = st.text_input("제안 물량 *", "20kg 상자 5개")
        day = st.date_input("희망 납품일 *", dt.date.today() + dt.timedelta(days=5))
        memo = st.text_area("구매처에 전할 이야기 (선택)", placeholder="재배와 포장 준비 상황을 알려주세요")
        html('<div class="source-box">시연 신청은 실제 구매처에 전달되지 않아요.</div>')
        if st.form_submit_button("시험 납품 제안하기", type="primary"):
            save_trial(r["청년농"], r["거래처"], f"{item} {qty}", f"{day} · {memo}")
            go("applied"); st.rerun()


def page_applied():
    fui.success("시험 납품을\n제안했어요", f"{S.sel['거래처']}가 확인하면 알려드릴게요. 은퇴 농업인의 거래 경험도 함께 전달돼요.")
    st.button("홈으로 돌아가기", type="primary", on_click=go, args=("home",))


def page_home():
    nm = S.f.get("name") or "초록"
    if S.role == "seller":
        title("나의 첫 거래 준비", f"{nm}님,\n오늘도 한 걸음 자라요.")
        n = len(list_trials())
        html(f'<div class="farm-panel"><span class="chip">준비 단계 {1 + (n > 0)} · {"납품 준비" if n else "판로 찾기"}</span>'
             f'<div class="farm-art">{fui.FARM_GROWN_SVG if n else fui.FARM_SVG}</div><p>경험이 쌓일수록 내 농장도 자라나요</p></div>')
        html(f'<div class="goal-card"><span class="eyebrow">이번 목표</span><h2>나의 첫 시험 납품 준비하기</h2>'
             f'<div class="progress-track"><i style="width:{66 if n else 33}%"></i></div><p>3가지 준비 중 {2 if n else 1}가지 완료</p></div>')
        fui.section("오늘 할 일")
        fui.overlay("todo", f'<div class="list-card"><span class="small-icon">{icon("shop")}</span><div><h3>AI 추천 판로 확인하기</h3>'
                            f'<p>은퇴 농업인의 거래처 중 우리 농장에 맞는 곳</p></div>{icon("arrow", 20)}</div>', go, args=("market",))
    elif S.role == "buyer":
        title("함께 만드는 좋은 거래", f"{nm}님,\n오늘도 한 걸음 자라요.")
        html(f'<div class="farm-panel"><div class="farm-art">{fui.FARM_SVG}</div><h2>좋은 농가와 만나는 시작</h2><p>납품 조건을 정하고 함께 시험해 보세요.</p></div>')
        fui.section("우리 구매처 현황")
        fui.overlay("bfarms", f'<div class="list-card">{icon("sprout")}<div><h3>AI 추천 농가</h3><p>우리 조건에 맞는 청년 농가를 확인해 보세요</p></div>{icon("arrow")}</div>', go, args=("farms",))
    else:
        title("다음 세대로 이어지는 거래", f"{nm or '선배'}님,\n오늘도 한 걸음 자라요.")
        html(f'<div class="farm-panel"><div class="farm-art">{fui.FARM_SVG}</div><h2>선배님의 거래처가, 누군가의 시작</h2><p>편하게 말씀해 주세요. AI가 정리를 도와요.</p></div>')
        st.button("새 거래 경험 나누기", type="primary", on_click=lambda: (S.pop("iv", None), go("interview")))
        fui.section("나눈 거래처")
        n = len(S.get("saved_buyers", []))
        fui.overlay("exp", f'<div class="list-card">{icon("box")}<div><h3>나의 거래처 기록</h3><p>{f"저장한 거래처 {n}곳" if n else "첫 경험을 나눠 주세요"}</p></div>{icon("arrow")}</div>', go, args=("experiences",))


def page_missions():
    title("준비가 쌓이면 농장도 쑥쑥", "오늘의 작은 실천,\n내일의 첫 거래", "AI 추천 판로를 보고 시험 납품을 준비해요.")
    html(f'<div class="farm-panel"><div class="farm-art">{fui.FARM_SVG}</div><span class="chip">나의 준비 단계 · 판로 찾기</span></div>')
    html('<div class="goal-card"><span class="eyebrow">오늘의 미션</span><h2>AI 추천 구매처 한 곳에 시험 납품 제안하기</h2>'
         '<p>적합도가 높은 곳부터 작은 물량으로 시작해 보세요.</p></div>')
    st.button("판로 보러 가기", type="primary", on_click=go, args=("market",))


def page_profile():
    title("나의 다시팜", f"{S.f.get('name') or '초록'}님의 정보")
    html(f'<div style="width:64px;height:64px;border-radius:50%;background:var(--farm-pale-green);color:var(--farm-primary-green);display:grid;place-items:center">{icon("user", 30)}</div>')
    html(f'<span class="chip">{dict((r[0], r[1]) for r in ROLES)[S.role]}</span>')
    html(fui.kv([("이름", S.f.get("name", "-")), ("농장·구매처", S.f.get("business", "-")), ("지역", S.f.get("region", "-")),
                 ("납품 신청", f"{len(list_trials())}건")]))
    fui.hint()
    html('<p class="helper">AI: ' + ("Gemini 연결됨" if ai.has_ai() else "데모 모드 (키 없음)") + " · 입력 내용은 시연용이에요.</p>")
    st.button("처음으로 · 고객 유형 바꾸기", on_click=reset)


# ── 구매처: 납품 조건 · AI 추천 농가
def my_buyer():
    r = S.f.get("row")
    if r and S.role == "buyer":
        return r["name"]
    return "가나청과"


def page_conditions():
    nm = my_buyer()
    b = load_buyers().set_index("name").loc[nm]
    title("구매처의 납품 조건", "어떤 농산물을\n기다리고 계세요?", "조건을 구체적으로 적을수록 AI가 더 잘 맞는 농가를 찾아요.")
    html(fui.kv([("품목", "/".join(b["items"])), ("주당 물량", f"{int(b['weekly_kg']):,}kg"), ("단가", f"{int(b['price_kg']):,}원/kg"),
                 ("최소 등급", GNAME.get(int(b["min_grade"]), "-")), ("필요한 월", f"{min(b['months'])}~{max(b['months'])}월"),
                 ("납품 요일", "/".join(b["days"]) or "협의"), ("받는 방식", b["delivery"] or "협의")]))
    st.button("조건으로 추천 농가 보기", type="primary", on_click=go, args=("farms",))
    fui.hint()


def page_farms():
    nm = my_buyer()
    title("조건을 바탕으로 살펴보기", "AI가 찾은\n함께 시작할 농가", "실제 거래 적합성은 대화로 확인해 주세요.")
    farmers = load_farmers()
    fk = (nm, len(farmers))
    if S.get("ffit_key") != fk:
        fit_progress(len(farmers), "청년 농가")
        S.ffit, S.ffit_key = matching.recommend_for_buyer(nm, top=10), fk
    for i, r in enumerate(S.ffit):
        f = farmers.set_index("name").loc[r["청년농"]]
        gaps = " · ".join(g.split(" (")[0] for g in r["부족한조건"]) or "조건 모두 충족"
        card = (f'<div class="goal-card"><div style="display:flex;justify-content:space-between;align-items:center">'
                f'<span class="chip">{esc(f["region"])} · {r["거리km"]}km</span><span class="fit-pct" style="font-size:24px">{r["매칭률"]}%</span></div>'
                f'<div style="display:flex;justify-content:space-between;align-items:center"><h2>{esc(r["청년농"])}</h2>{icon("arrow", 18)}</div><p>{"/".join(f["items"])} · 주 {int(f["weekly_kg"]):,}kg · 등급 {GNAME.get(int(f["grade"]))}</p>'
                f'<p style="margin-top:-8px">부족한 조건: {esc(gaps)}</p></div>')
        fui.overlay(f"fm{i}", card, go, args=("farmdetail",), kwargs={"fsel": r})


def page_farmdetail():
    r = S.fsel
    title("추천 농가 · AI 적합도", r["청년농"], f"{r['거래처']}의 조건과 비교한 결과예요.")
    bars = "".join(fui.score_bar(k, v) for k, v in r["항목점수"].items())
    html(f'<div class="goal-card"><div style="display:flex;justify-content:space-between;align-items:center">'
         f'<span class="ai-badge">{icon("spark", 14)} 매칭 AI</span><span class="fit-pct">{r["매칭률"]}%</span></div>{bars}</div>')
    html(fui.kv([(k, v) for k, v in r["근거"].items() if k != "유사도(RAG)"]))
    st.button("이 농가에 시험 납품 요청하기", type="primary", on_click=lambda: (save_trial(r["청년농"], r["거래처"], "시험 납품 요청", "구매처 요청"), go("home")))


# ── 은퇴 농업인: AI가 묻고, 말로 답하고, AI가 받아써서 정리
def tts_button(text, key):
    """질문 듣기 — 브라우저 음성으로 읽기 (피그마 '질문 듣기' 버튼 모양)"""
    import json
    import streamlit.components.v1 as components
    components.html(f"""<button onclick='speechSynthesis.cancel();var u=new SpeechSynthesisUtterance({json.dumps(text)});u.lang="ko-KR";u.rate=0.9;speechSynthesis.speak(u)'
      style='width:100%;min-height:52px;border:1px solid #dfe8d5;border-radius:13px;background:#fff;color:#153f3d;font:600 16px Pretendard,sans-serif;
      display:flex;align-items:center;justify-content:center;gap:9px;cursor:pointer'>
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">
      <path d="m3 9 5 0 5-5v16l-5-5H3ZM17 8c3 2 3 6 0 8M20 4c6 5 6 11 0 16"/></svg>질문 듣기</button>""", height=58)


def page_interview():
    if "iv" not in S:
        S.iv = voice.Interview()
    iv = S.iv
    title("선배님의 경험을 들려주세요", "그때의 거래가,\n누군가의 길이 되도록", "글로 쓰지 않아도 괜찮아요. AI가 여쭤보면 편하게 말씀해 주세요.")
    def history():
        if len(iv.log) > 1:
            with st.expander(f"지금까지 나눈 대화 ({iv.turn})", expanded=iv.done):
                html('<div class="chat-log">' + "".join(
                    f'<div class="bubble {w}"><b>{"AI" if w == "ai" else "선배님"}</b>{esc(t)}</div>' for w, t in iv.log) + "</div>")
    if S.get("last_said") and iv.turn:
        html(f'<div class="bubble me" style="max-width:100%;align-self:stretch"><b>AI가 받아쓴 선배님 말씀</b>“{esc(S.last_said)}”</div>')
    if iv.done:
        html(f'<div class="interview-question"><span class="chip">인터뷰 완료</span><h2>{esc(voice.END)}</h2>'
             f'<p>질문 {iv.turn}개에 답해 주셨어요. AI가 거래처별 조건으로 정리할게요.</p></div>')
        st.button("AI로 정리하기", type="primary", on_click=go, args=("transcribing",))
        st.button("처음부터 다시", on_click=lambda: (S.pop("iv"), S.pop("last_said", None)))
        history()
        return
    html(f'<div class="interview-question"><span class="chip">{iv.turn + 1}번째 질문 · AI</span><h2>{esc(iv.question)}</h2></div>')
    tts_button(iv.question, f"tts{iv.turn}")
    html(f'<div class="record-area" style="padding:0"><div class="wave">' +
         "".join(f'<i style="height:{12 + (i * 17) % 35}px;animation-delay:{i * .07}s"></i>' for i in range(17)) +
         '</div><p>아래 마이크를 눌러 말씀해 주세요</p></div>')
    audio = st.audio_input("말로 답하기", key=f"rec{iv.turn}", label_visibility="collapsed")
    if audio is not None and S.get("heard") != (iv.turn, len(audio.getvalue())):
        S.heard = (iv.turn, len(audio.getvalue()))
        if ai.has_ai():
            with st.spinner("AI가 받아쓰고 있어요"):
                try:
                    said = voice.transcribe(audio.getvalue(), audio.type)
                except Exception as e:
                    said = None; st.error(f"받아쓰기 실패: {e}")
            if said:
                S.last_said = said
                iv.answer(said); st.rerun()
        else:
            S.demo_note = True
    if S.get("demo_note") and not ai.has_ai():
        html('<div class="demo-note"><span class="demo-dot"></span>데모 모드: 키가 없어 녹음을 받아쓸 수 없어요. 예시 답변으로 이어가 주세요</div>')
    if not ai.has_ai():
        if st.button("예시 답변으로 대답하기", icon=":material/record_voice_over:"):
            S.last_said = iv.demo_answer(); iv.answer(S.last_said); st.rerun()
    with st.container(key="typed", horizontal=True, vertical_alignment="bottom"):
        typed = st.text_input("말 대신 글로 답해도 돼요", key=f"typed{iv.turn}")
        if st.button("보내기", width="content") and typed.strip():
            S.last_said = typed; iv.answer(typed); st.rerun()
    history()


def page_transcribing():
    fui.hide_stale()
    box = st.empty()
    labels = ["대화 내용 확인", "거래처마다 품목·규격·납품량·주기 찾기", "단위 맞추기 (상자→kg, 상자당→kg당)", "배송거리·정산주기까지 표로 정리"]

    def show(i):
        steps_html = "".join(f'<div class="{"on" if j < i else ""}"><b>{icon("check", 13) if j < i else j + 1}</b>{l}</div>'
                             for j, l in enumerate(labels))
        with box.container():
            html(f'<div class="loading-page" style="height:auto;padding:50px 0 10px;gap:20px"><div class="spinner"></div>'
                 f'<h1 style="font-size:25px">이야기를 정리하고 있어요</h1><p style="color:var(--farm-secondary-text)">'
                 f'{"Gemini가 대화를 표로 정리하는 중" if ai.has_ai() else "데모: 예시 정리 결과를 준비하는 중"}</p>'
                 f'<div class="ai-steps">{steps_html}</div></div>')
    show(0); time.sleep(0.4); show(1)
    try:
        res = S.iv.structure()
    except Exception as e:
        st.error(f"정리 실패: {e}"); res = voice.DEMO_RESULT
    show(2); time.sleep(0.4); show(3); time.sleep(0.3)
    S.vres = res
    S.page = "vreview"
    st.rerun()


def page_vreview():
    res = S.vres
    fm, buyers = res.get("farmer", {}), res.get("buyers", [])
    title("AI 받아쓰기 · 정리", "이렇게 정리했어요", "말씀하신 내용을 거래처마다 같은 항목으로 정리했어요. 틀린 칸은 눌러서 고쳐 주세요.")
    html(f'<div class="info-banner">{icon("check", 20)}<div>대화에서 거래처 {len(buyers)}곳을 찾았어요'
         f'<p>{esc(fm.get("name", ""))} · {esc(fm.get("region", ""))} · {esc(fm.get("career", ""))}</p></div></div>')
    home = coords(fm.get("region", "평창"))
    for b in buyers:                                   # 배송거리 = 은퇴농 농장 ↔ 거래처 (코드 계산)
        la, lo = coords(b.get("location", ""))
        b["dist"] = round(matching.dist_km({"lat": home[0], "lng": home[1]}, {"lat": la, "lng": lo}))
    for b in buyers:
        said = next((t for w, t in S.iv.log if w == "me" and b["name"] in t), "")
        html(f'<div class="goal-card" style="gap:4px"><span class="eyebrow">{esc(b.get("type", ""))} · {esc(b.get("location", ""))}</span>'
             f'<h2>{esc(b["name"])}</h2>' + fui.kv([
                 ("품목", "/".join(b.get("items", []))), ("규격", b.get("spec", "") or "-"),
                 ("납품량", f"주 {int(b.get('weekly_kg') or 0):,}kg ({int((b.get('weekly_kg') or 0) / 20):,}상자)"),
                 ("주기", b.get("cycle", "") or "/".join(b.get("days", []))), ("배송거리", f"약 {b['dist']}km · {b.get('delivery', '')}"),
                 ("정산주기", b.get("settlement", "") or "-"), ("단가", f"{int(b.get('price_kg') or 0):,}원/kg")]) + "</div>")
    cols = {"name": "거래처", "items": "품목", "spec": "규격", "weekly_kg": "납품량(주 kg)", "cycle": "주기", "days": "요일",
            "months": "월", "dist": "배송거리(km)", "settlement": "정산주기", "price_kg": "단가(원/kg)", "min_grade": "최소 등급(1~4)",
            "type": "유형", "location": "위치", "delivery": "배송 방식", "note": "메모"}
    df = pd.DataFrame(buyers).reindex(columns=list(cols))
    for c in ("items", "months", "days"):
        df[c] = df[c].apply(lambda v: ", ".join(map(str, v)) if isinstance(v, list) else (v or ""))
    html('<p class="helper" style="margin-bottom:-10px">표에서 바로 고칠 수 있어요</p>')
    edited = st.data_editor(df.rename(columns=cols), hide_index=True, width="stretch", num_rows="dynamic",
                            disabled=["배송거리(km)"])
    with st.expander("대화 원문 보기"):
        st.text(S.iv.transcript())
    if st.button("확인하고 저장하기", type="primary"):
        farmer = fm.get("name") or "은퇴 농업인"
        sp = lambda v: [x.strip() for x in str(v).split(",") if x.strip() and x.strip() != "nan"]
        for _, r in edited.rename(columns={v: k for k, v in cols.items()}).iterrows():
            if not str(r["name"]).strip():
                continue
            la, lo = coords(r["location"])
            save_buyer({"name": r["name"], "type": r["type"] or "기타", "size": "은퇴농 거래처", "source": "은퇴농 구술",
                        "from_farmer": f"{farmer} 농가", "location": r["location"], "lat": la, "lng": lo, "items": sp(r["items"]),
                        "min_grade": int(float(r["min_grade"] or 1)), "weekly_kg": float(r["weekly_kg"] or 0),
                        "price_kg": float(r["price_kg"] or 0), "months": [int(float(m)) for m in sp(r["months"])],
                        "days": sp(r["days"]), "delivery": r["delivery"] or "", "settlement": r["settlement"] or "",
                        "cert": "", "raw_text": f"{farmer} 구술 · 규격 {r['spec'] or ''} · 주기 {r['cycle'] or ''} · {r['note'] or ''}"})
        save_retiree({"기본정보": f"{farmer} · {fm.get('region', '')}", "영농경력": fm.get("career", ""), "거래처 수": len(edited)},
                     S.iv.log)
        S.f["name"] = farmer
        S.saved_buyers = [n for n in edited["거래처"] if str(n).strip()]
        S.registered = True
        S.pop("fit_key", None)
        go("saved"); st.rerun()


def page_saved():
    fui.success("소중한 거래처,\n잘 담아두었어요", "선배님의 한마디가 청년 농업인의 첫 판로가 돼요. AI가 맞는 청년 농가와 이어 드릴게요.")
    st.button("홈으로 가기", type="primary", on_click=go, args=("home",))


def page_experiences():
    title("선배님이 나눈 거래처", "나의 거래처 기록", "청년 농업인과의 매칭에 쓰이고 있어요.")
    names = S.get("saved_buyers", [])
    b = load_buyers().set_index("name")
    if not names:
        html('<p class="helper">아직 저장한 거래처가 없어요. 거래 경험을 들려주세요.</p>')
    for i, n in enumerate(names):
        r = b.loc[n]
        cands = matching.recommend_for_buyer(n, top=1)
        best = f"AI 추천 청년 농가: {cands[0]['청년농']} ({cands[0]['매칭률']}%)" if cands else "조건에 맞는 청년 농가를 찾는 중"
        html(f'<div class="list-card"><span class="small-icon">{icon("shop")}</span><div><h3>{esc(n)}</h3>'
             f'<p>{"/".join(r["items"])} · 주 {int(r["weekly_kg"]):,}kg · {"/".join(r["days"])}</p><p>{esc(best)}</p></div></div>')


PAGES = {"splash": page_splash, "welcome": page_welcome, "import": page_import, "loading": page_loading,
         "notfound": page_notfound, "confirm": page_confirm, "missing": page_missing, "registered": page_registered,
         "market": page_market, "detail": page_detail, "apply": page_apply, "applied": page_applied, "home": page_home,
         "missions": page_missions, "profile": page_profile, "conditions": page_conditions, "farms": page_farms,
         "farmdetail": page_farmdetail, "interview": page_interview, "transcribing": page_transcribing,
         "vreview": page_vreview, "saved": page_saved, "experiences": page_experiences}

page = S.page
header(page)
PAGES.get(page, page_welcome)()
bottom_nav(page)
