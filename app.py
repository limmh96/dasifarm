"""다시 FARM 프로토타입 (Streamlit)
페이지 이름 = 피그마 프레임 이름 (README의 '피그마 연동' 표 참고)
실행:  streamlit run app.py
"""
import os
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from farm import ai, ui
from farm.data import load_buyers, load_farmers, save_retiree, save_buyer, list_retirees, save_trial, list_trials, public_lookup, CRITERIA
from farm.interview import Interview, run_structure, read_ledger
from farm import matching

st.set_page_config(page_title="다시 FARM", page_icon="🌱", layout="centered")
ui.inject_css()

# 키를 Secrets에서 환경변수로 (로컬은 .streamlit/secrets.toml, 배포는 Streamlit Cloud Secrets)
for k in ("GEMINI_API_KEY", "KAKAO_JS_KEY"):
    try:
        if k in st.secrets and not os.environ.get(k):
            os.environ[k] = st.secrets[k]
    except Exception:
        pass

PAGES = ["모바일 01 · 홈", "은퇴농 · AI 인터뷰", "모바일 06 · 판로 찾기", "모바일 07 · 구매처 상세",
         "모바일 08 · 시험 납품 신청", "구매처 · 후속 공급자 찾기", "데이터 · 매칭 기준"]
st.session_state.setdefault("page", PAGES[0])
st.session_state.setdefault("weights", dict(matching.WEIGHTS))


def go(page, **kw):
    st.session_state.page = page
    for k, v in kw.items():
        st.session_state[k] = v


with st.sidebar:
    st.markdown("### 🌱 다시 FARM")
    st.radio("화면", PAGES, key="page", label_visibility="collapsed")
    st.caption("AI 모드: " + ("Gemini 연결됨" if ai.has_ai() else "데모 모드 (키 없음)"))
    st.caption("모든 이름·수치는 시연용 가상 데이터")


def show_map(points):
    """points: [(이름, 위도, 경도, 색)] — 카카오 키가 있으면 카카오맵, 없으면 기본 지도"""
    key = os.environ.get("KAKAO_JS_KEY")
    if key:
        marks = ",".join(f"{{n:'{n}',la:{la},lo:{lo}}}" for n, la, lo, _ in points)
        components.html(f"""
        <div id="map" style="width:100%;height:320px;border-radius:16px"></div>
        <script src="//dapi.kakao.com/v2/maps/sdk.js?appkey={key}&autoload=false"></script>
        <script>kakao.maps.load(function(){{
          var ms=[{marks}]; var map=new kakao.maps.Map(document.getElementById('map'),
            {{center:new kakao.maps.LatLng(ms[0].la,ms[0].lo),level:10}});
          var bd=new kakao.maps.LatLngBounds();
          ms.forEach(function(m){{var p=new kakao.maps.LatLng(m.la,m.lo); bd.extend(p);
            new kakao.maps.CustomOverlay({{map:map,position:p,yAnchor:1.4,
              content:'<div style="background:#1F5E3B;color:#fff;padding:3px 8px;border-radius:8px;font-size:12px">'+m.n+'</div>'}});
            new kakao.maps.Marker({{map:map,position:p}});}});
          map.setBounds(bd);}});</script>""", height=330)
    else:
        st.map(pd.DataFrame([{"lat": la, "lon": lo} for _, la, lo, _ in points]), zoom=8, height=300)
        st.caption("카카오맵 키(KAKAO_JS_KEY)를 넣으면 카카오맵으로 표시됩니다.")


page = st.session_state.page

# ───────────────────────── 모바일 01 · 홈 ─────────────────────────
if page == PAGES[0]:
    ui.section("다시 FARM", "은퇴 농업인의 판로를 청년 농업인에게 잇는 AI 매칭")
    c1, c2, c3 = st.columns(3)
    c1.button("은퇴 예정 농업인", width="stretch", on_click=go, args=(PAGES[1],))
    c2.button("청년 농업인", width="stretch", type="primary", on_click=go, args=(PAGES[2],))
    c3.button("구매처", width="stretch", on_click=go, args=(PAGES[5],))
    b, f = load_buyers(), load_farmers()
    m1, m2, m3 = st.columns(3)
    m1.metric("등록 구매처", f"{len(b)}곳")
    m2.metric("청년농", f"{len(f)}명")
    m3.metric("은퇴농 인터뷰", f"{len(list_retirees())}건")
    ui.card("<b>어떻게 연결하나요?</b><br><span class='df-label'>① 은퇴농이 AI 인터뷰로 거래처를 알려주면 ② 구매처의 요구 조건과 청년농의 공급 능력을 "
            "같은 6가지 기준으로 비교해 ③ 매칭률과 부족한 조건을 양쪽에 보여줍니다.</span><br><br>"
            + "".join(ui.chip(c) for c in CRITERIA))

# ───────────────────────── 은퇴농 · AI 인터뷰 (모델 1) ─────────────────────────
elif page == PAGES[1]:
    ui.section("AI 인터뷰", "AI가 먼저 질문합니다. 담당자가 옆에서 대신 입력해도 됩니다.")
    tab1, tab2 = st.tabs(["대화형 인터뷰", "장부 사진 읽기"])
    with tab1:
        if "iv" not in st.session_state or st.button("인터뷰 새로 시작"):
            st.session_state.iv = Interview()
            st.session_state.pop("iv_result", None)
        iv = st.session_state.iv
        for who, msg in iv.log:
            st.chat_message(who).write(msg)
        if not iv.done:
            if ans := st.chat_input("답변을 입력하세요"):
                iv.reply(ans)
                st.rerun()
        else:
            if "iv_result" not in st.session_state:
                with st.spinner("대화를 표로 정리하는 중…"):
                    st.session_state.iv_result = run_structure(iv)
            res = st.session_state.iv_result
            st.success("정리된 내용입니다. 맞는지 확인 후 저장하세요.")
            st.markdown("**은퇴농 프로필**")
            st.dataframe(pd.DataFrame(res.get("retiree", {}).items(), columns=["항목", "답변"]), hide_index=True, width="stretch")
            st.markdown("**거래처 (구매처 표에 추가됨 → 매칭 대상)**")
            buyers = res.get("buyers", [])
            st.dataframe(pd.DataFrame(buyers), hide_index=True, width="stretch")
            if st.button("맞아요, 저장하기", type="primary"):
                save_retiree(res.get("retiree", {}), iv.log)
                for bb in buyers:
                    bb.setdefault("source", "은퇴농 구술")
                    bb.setdefault("from_farmer", (res.get("retiree", {}).get("기본정보", "") or "인터뷰 농가")[:12])
                    bb.setdefault("lat", 37.64); bb.setdefault("lng", 128.56)
                    if bb.get("name"):
                        save_buyer(bb)
                st.success("저장했습니다. '판로 찾기'에서 청년농과 매칭됩니다.")
    with tab2:
        st.caption("손글씨 장부 사진을 올리면 AI가 거래 기록 표로 바꿉니다.")
        up = st.file_uploader("장부 사진", type=["jpg", "jpeg", "png"])
        use_sample = st.checkbox("예시 장부 사진 사용", value=up is None)
        img = up.getvalue() if up else (open("data/sample_ledger.jpg", "rb").read() if use_sample else None)
        if img:
            st.image(img, width="stretch")
            if st.button("장부 읽기", type="primary"):
                rows = read_ledger(img, up.type if up else "image/jpeg")
                if rows is None:
                    st.info("데모 모드: Gemini 키가 없어서 예시 장부의 정답 데이터를 보여줍니다.")
                    st.dataframe(pd.read_csv("data/ledger_truth.csv").head(24), hide_index=True, width="stretch")
                else:
                    st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")

# ───────────────────────── 모바일 06 · 판로 찾기 (모델 2) ─────────────────────────
elif page == PAGES[2]:
    ui.section("판로 찾기", "내 정보와 구매처 요구 조건을 6가지 기준으로 비교합니다.")
    farmers = load_farmers()
    mode = st.radio("청년농", ["등록된 청년농", "새로 입력"], horizontal=True, label_visibility="collapsed")
    if mode == "등록된 청년농":
        name = st.selectbox("청년농 선택", farmers["name"], format_func=lambda n: f"{n} · {farmers.set_index('name').loc[n,'intro']}")
        y = farmers.set_index("name").loc[name].to_dict() | {"name": name}
    else:
        with st.form("young"):
            c1, c2 = st.columns(2)
            nm = c1.text_input("이름", "청년농N"); region = c2.text_input("지역", "평창군 진부면")
            items = st.multiselect("품목", ["감자", "토마토"], ["감자"])
            c3, c4 = st.columns(2)
            boxes = c3.number_input("주당 출하 (20kg 상자)", 1, 1000, 30)
            wish = c4.number_input("희망 단가 (원/20kg)", 5000, 100000, 24000, step=1000)
            grade = st.select_slider("주로 낼 수 있는 등급", ["무관", "중", "상", "특"], "상")
            months = st.multiselect("출하 가능 월", list(range(1, 13)), [8, 9, 10])
            days = st.multiselect("납품 가능 요일", list("월화수목금토"), ["화", "목"])
            truck = st.checkbox("트럭 있음", True)
            cert_no = st.text_input("인증번호 (있으면 공공데이터에서 자동 조회)")
            ok = st.form_submit_button("매칭하기", type="primary")
        cert = public_lookup("cert", cert_no) if cert_no else None
        if cert_no and cert:
            st.success(f"공공데이터에서 인증 정보를 찾았습니다: {cert}. 맞으면 그대로 진행합니다.")
        elif cert_no:
            st.warning("공공데이터에서 찾지 못했습니다. 인증 종류를 직접 선택해 주세요.")
        manual = st.multiselect("보유 인증 (직접 입력)", ["GAP", "무농약", "유기농"], [] if not cert else ["GAP"])
        coords = {"평창": (37.37, 128.39), "강릉": (37.75, 128.88), "정선": (37.38, 128.66), "원주": (37.34, 127.92)}
        la, lo = next((v for k, v in coords.items() if k in region), (37.64, 128.57))
        g = {"무관": 1, "중": 2, "상": 3, "특": 4}[grade]
        y = {"name": nm, "region": region, "lat": la, "lng": lo, "items": items, "grade": g, "weekly_kg": boxes * 20,
             "months": months, "days": days, "wish_price_kg": wish / 20, "certs": manual, "truck": "Y" if truck else "N",
             "intro": f"{region} {','.join(items)} 주 {boxes}상자"}
    res, excluded = matching.recommend_for_farmer(farmer=y, top=3, weights=st.session_state.weights)
    st.markdown(f"**{y['name']}에게 맞는 구매처 상위 {len(res)}곳**")
    for i, r in enumerate(res):
        ui.match_card(r)
        st.button(f"{r['거래처']} 상세 보기", key=f"d{i}", on_click=go, args=(PAGES[3],), kwargs={"sel": r, "sel_farmer": y})
    if excluded:
        with st.expander(f"필수조건에서 제외된 구매처 {len(excluded)}곳"):
            st.dataframe(pd.DataFrame(excluded), hide_index=True, width="stretch")

# ───────────────────────── 모바일 07 · 구매처 상세 ─────────────────────────
elif page == PAGES[3]:
    r = st.session_state.get("sel")
    if not r:
        st.info("'판로 찾기'에서 구매처를 먼저 선택해 주세요.")
        st.button("판로 찾기로", on_click=go, args=(PAGES[2],))
    else:
        ui.section(r["거래처"], f"{r['구매처유형']} · {r['농가']} 거래처 · 출처: {r['출처']}")
        st.markdown(f"<div class='df-score'>매칭률 {r['매칭률']}%</div>", unsafe_allow_html=True)
        bars = "".join(ui.score_bar(k, v, f"· {st.session_state.weights[k]}%") for k, v in r["항목점수"].items())
        ui.card(bars)
        st.dataframe(pd.DataFrame(r["근거"].items(), columns=["기준", "구매처 요구 / 청년농 공급"]), hide_index=True, width="stretch")
        with st.spinner("AI가 추천 이유를 쓰는 중…"):
            if st.session_state.get("exp_for") != (r["거래처"], r["청년농"]):
                st.session_state.exp = matching.explain(r)
                st.session_state.exp_for = (r["거래처"], r["청년농"])
        st.markdown("**AI 설명**")
        ui.card(st.session_state.exp.replace("\n", "<br>"))
        show_map([(r["청년농"], r["청년농위도"], r["청년농경도"], ""), (r["거래처"], r["위도"], r["경도"], "")])
        st.button("시험 납품 신청하기", type="primary", width="stretch", on_click=go, args=(PAGES[4],))

# ───────────────────────── 모바일 08 · 시험 납품 신청 ─────────────────────────
elif page == PAGES[4]:
    r = st.session_state.get("sel")
    if not r:
        st.info("구매처를 먼저 선택해 주세요.")
    else:
        ui.section("시험 납품 신청", f"{r['청년농']} → {r['거래처']}")
        with st.form("trial"):
            qty = st.text_input("시험 납품 물량", "5상자")
            memo = st.text_area("구매처에 남길 말", "샘플 먼저 보내드리고 싶습니다.")
            if st.form_submit_button("신청하기", type="primary"):
                save_trial(r["청년농"], r["거래처"], qty, memo)
                st.session_state.trial_done = True
        if st.session_state.get("trial_done"):
            st.success("시험 납품 신청 완료! 구매처와 은퇴 농가에 알림이 전달됩니다(시연에서는 아래 목록에 기록).")
            st.dataframe(list_trials(), hide_index=True, width="stretch")

# ───────────────────────── 구매처 · 후속 공급자 찾기 ─────────────────────────
elif page == PAGES[5]:
    ui.section("후속 공급자 찾기", "구매처 입장에서 같은 점수표를 반대로 조회합니다.")
    tab1, tab2 = st.tabs(["후보 청년농 보기", "구매처 등록 (공공데이터 자동 채움)"])
    with tab1:
        buyers = load_buyers()
        bname = st.selectbox("구매처", buyers["name"])
        cands = matching.recommend_for_buyer(bname, top=3, weights=st.session_state.weights)
        if not cands:
            st.info("조건을 통과한 청년농이 없습니다.")
        for r in cands:
            ui.match_card(r, who="farmer")
    with tab2:
        q = st.text_input("구매처 이름으로 공공데이터 조회", "학교급식")
        hit = public_lookup("buyer", q) if q else None
        if hit:
            st.success("공공데이터에서 찾았습니다. 미리 채운 값이 맞는지 확인해 주세요.")
            st.json({k: hit[k] for k in ("name", "type", "items", "weekly_kg", "price_kg", "months", "days", "cert")})
            st.button("맞아요", type="primary")
        else:
            st.warning("공공데이터에 없습니다. 직접 입력해 주세요.")
            with st.form("buyer"):
                nm = st.text_input("이름"); tp = st.selectbox("유형", ["식당", "반찬가게", "마트", "도매상", "식자재업체", "로컬푸드 직매장"])
                items = st.multiselect("품목", ["감자", "토마토"], ["감자"])
                c1, c2 = st.columns(2)
                boxes = c1.number_input("주당 필요 (20kg 상자)", 1, 1000, 10); price = c2.number_input("상자당 단가", 5000, 100000, 25000, step=1000)
                grade = st.select_slider("최소 등급", ["무관", "중", "상", "특"], "상")
                months = st.multiselect("필요한 월", list(range(1, 13)), [7, 8, 9, 10, 11])
                days = st.multiselect("납품 요일", list("월화수목금토"), ["화"])
                if st.form_submit_button("등록", type="primary") and nm:
                    save_buyer({"name": nm, "type": tp, "size": "소형", "source": "직접 입력", "from_farmer": "—", "location": "강원",
                                "lat": 37.64, "lng": 128.56, "items": items, "min_grade": {"무관": 1, "중": 2, "상": 3, "특": 4}[grade],
                                "weekly_kg": boxes * 20, "price_kg": price / 20, "months": months, "days": days,
                                "delivery": "", "settlement": "", "cert": "", "raw_text": f"{nm} {tp} 직접 입력"})
                    st.success("등록했습니다.")

# ───────────────────────── 데이터 · 매칭 기준 ─────────────────────────
elif page == PAGES[6]:
    ui.section("매칭 기준과 데이터", "가중치는 예시값입니다. 인터뷰 결과에 맞춰 조정하세요.")
    w = st.session_state.weights
    cols = st.columns(2)
    for i, k in enumerate(list(w)):
        w[k] = cols[i % 2].slider(k, 0, 40, w[k], key=f"w_{k}")
    st.caption(f"가중치 합계 {sum(w.values())} (합이 100이 아니어도 자동으로 비율 환산)")
    st.markdown("**구매처 (요구 조건)**")
    st.dataframe(load_buyers().drop(columns=["raw_text"]), hide_index=True, width="stretch")
    st.markdown("**청년농 (공급 능력)**")
    st.dataframe(load_farmers(), hide_index=True, width="stretch")
    st.markdown("**은퇴농 인터뷰 기록**")
    st.dataframe(pd.DataFrame([dict(p, 저장일시=c) for c, p in list_retirees()]), hide_index=True, width="stretch")
