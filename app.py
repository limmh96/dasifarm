"""다시 FARM 프로토타입 (Streamlit, 모바일 390px 레이아웃)
페이지 이름 = 피그마 프레임 이름 (README의 '피그마 연동' 표 참고)
실행:  streamlit run app.py
"""
import os
import datetime as dt
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from farm import ai, ui
from farm.data import load_buyers, load_farmers, save_retiree, save_buyer, list_retirees, save_trial, list_trials, public_lookup, CRITERIA
from farm.interview import Interview, run_structure, read_ledger
from farm import matching, onboard
import json

st.set_page_config(page_title="다시, FARM", page_icon="🌱", layout="centered", initial_sidebar_state="collapsed")
ui.inject_css()

# 키: Secrets → 환경변수 (로컬 .streamlit/secrets.toml, 배포 Streamlit Cloud Secrets)
for k in ("GEMINI_API_KEY", "KAKAO_JS_KEY"):
    try:
        if k in st.secrets and not os.environ.get(k):
            os.environ[k] = st.secrets[k]
    except Exception:
        pass

# 피그마 프레임 이름
P_START, P_ONB_F, P_ONB_B = "모바일 00 · 고객 선택", "모바일 · 판매처 등록", "모바일 · 구매처 등록"
P_HOME, P_HANDOVER, P_FIND = "모바일 01 · 홈", "모바일 · 판로 물려주기", "모바일 06 · 판로 찾기"
P_DETAIL, P_TRIAL, P_DONE = "모바일 07 · 구매처 상세", "모바일 08 · 시험 납품 신청", "모바일 · 시험 납품 신청 완료"
P_BUYER, P_MY = "모바일 · 납품 조건 보기", "모바일 · 나의 다시팜"
MENU = [("전체 메뉴", [("처음 화면 (고객 선택)", P_START), ("홈", P_HOME), ("판로 물려주기", P_HANDOVER), ("납품 조건 보기", P_BUYER),
                     ("판로 찾기", P_FIND), ("나의 다시팜", P_MY)])]

st.session_state.setdefault("page", P_START)
st.session_state.setdefault("weights", dict(matching.WEIGHTS))
st.session_state.setdefault("me", "청년농D")


def go(page, **kw):
    st.session_state.page = page
    for k, v in kw.items():
        st.session_state[k] = v


ui.header(MENU, go)
page = st.session_state.page
FARMERS = load_farmers()


def me():
    if st.session_state.get("me_custom"):
        return st.session_state.me_custom
    n = st.session_state.me
    return FARMERS.set_index("name").loc[n].to_dict() | {"name": n}


def show_map(points):
    key = os.environ.get("KAKAO_JS_KEY")
    if key:
        marks = ",".join(f"{{n:'{n}',la:{la},lo:{lo}}}" for n, la, lo in points)
        components.html(f"""
        <div id="map" style="width:100%;height:220px;border-radius:12px"></div>
        <script src="//dapi.kakao.com/v2/maps/sdk.js?appkey={key}&autoload=false"></script>
        <script>kakao.maps.load(function(){{
          var ms=[{marks}]; var map=new kakao.maps.Map(document.getElementById('map'),
            {{center:new kakao.maps.LatLng(ms[0].la,ms[0].lo),level:10}});
          var bd=new kakao.maps.LatLngBounds();
          ms.forEach(function(m){{var p=new kakao.maps.LatLng(m.la,m.lo); bd.extend(p);
            new kakao.maps.CustomOverlay({{map:map,position:p,yAnchor:1.6,
              content:'<div style="background:#245C3F;color:#fff;padding:2px 8px;border-radius:8px;font-size:11px">'+m.n+'</div>'}});
            new kakao.maps.Marker({{map:map,position:p}});}});
          map.setBounds(bd);}});</script>""", height=228)
    else:
        st.map(pd.DataFrame([{"lat": la, "lon": lo} for _, la, lo in points]), zoom=8, height=220)


# ───────────────────────── 모바일 00 · 고객 선택 ─────────────────────────
if page == P_START:
    ui.html("<div class='df-pad' style='text-align:center;padding-top:90px'><p class='df-title'>어떤 고객이세요?</p>"
            "<p class='df-sub' style='margin-bottom:26px'>고객에 맞는 화면으로 안내해 드릴게요.</p></div>")
    with st.container(key="pad_roles"):
        st.button("농산물 판매처 (청년)", width="stretch", key="role_f", on_click=go, args=(P_ONB_F,))
        st.button("농산물 구매처", width="stretch", key="role_b", on_click=go, args=(P_ONB_B,))
        st.button("은퇴 농업인", width="stretch", key="role_r", on_click=go, args=(P_HANDOVER,))
    ui.html("<div class='df-pad' style='text-align:center;margin-top:18px'><span class='df-label'>"
            "판매처·구매처는 공공데이터로 정보를 먼저 불러오고,<br>은퇴 농업인은 AI와 말로 대화하며 정리해요.</span></div>")


def _farmer_done(row):
    st.session_state.pop("me_custom", None)
    go(P_FIND, me=row["name"])


def _buyer_done(row):
    go(P_BUYER, buyer_sel=row["name"])


if page == P_ONB_F:
    onboard.run("farmer", _farmer_done)

elif page == P_ONB_B:
    onboard.run("buyer", _buyer_done)

# ───────────────────────── 모바일 01 · 홈 ─────────────────────────
elif page == P_HOME:
    ui.crumb("홈", "오늘 할 일", icon="home")
    trials, retirees = list_trials(), list_retirees()
    with st.container(key="gcard_home"):
        ui.html(f"<p class='df-eyebrow' style='margin-top:0'>{me()['name']}님, 반갑습니다.</p>"
                "<p class='df-title' style='margin-bottom:6px'>농사의 다음을 잇다</p>"
                "<p class='df-sub'>오래 쌓아 온 거래의 신뢰,<br>이제 다음 농부와 함께 이어가요.</p>")
        st.button("나에게 맞는 판로 찾기", type="primary", width="stretch", on_click=go, args=(P_FIND,))
        st.button("판로 물려주기", width="stretch", on_click=go, args=(P_HANDOVER,))
    with st.container(key="wcard_todo"):
        ui.html(f"<span class='df-label'>시험 납품 신청</span><div class='df-big'>{len(trials):02d}</div>"
                "<span class='df-label'>구매처 검토를 기다리는 신청이에요</span>")
    with st.container(key="wcard_hand"):
        ui.html(f"<span class='df-label'>진행 중인 인수인계</span><div class='df-big'>{len(retirees):02d}</div>"
                "<span class='df-label'>AI 인터뷰로 정리된 은퇴 농가 판로예요</span>")
    with st.container(key="wcard_how"):
        ui.html("<p class='df-card-title'>매칭은 이렇게 해요</p><p class='df-sub'>구매처가 원하는 조건과 내 출하 조건을 "
                "같은 기준으로 비교해 매칭률과 부족한 조건을 보여드려요.</p><div style='margin-top:8px'>"
                + "".join(ui.chip(c) for c in CRITERIA) + "</div>")

# ───────────────────────── 판로 물려주기 (모델 1: AI 인터뷰) ─────────────────────────
elif page == P_HANDOVER:
    ui.crumb("판로 물려주기", "AI 인터뷰", icon="swap")
    ui.hero("판로 물려주기 · 은퇴 예정 농가", "AI가 여쭤보면<br>편하게 답해 주세요",
            "AI가 질문을 읽어 드려요. 녹음 버튼을 누르고 말로 답하시면 받아 적어요.")
    tab1, tab2 = st.tabs(["말로 대화하기", "장부 사진 읽기"])
    with tab1:
        if "iv" not in st.session_state:
            st.session_state.iv = Interview()
        iv = st.session_state.iv
        if not iv.done:
            q = next((m for w, m in reversed(iv.log) if w == "assistant"), "")
            with st.container(key="gcard_q"):
                ui.html(ui.chip("AI 질문") + f"<p class='df-name' style='font-size:19px !important;line-height:1.5'>{q}</p>")
                st.html(f"""<button onclick='speechSynthesis.cancel();var u=new SpeechSynthesisUtterance({json.dumps(q)});u.lang="ko-KR";u.rate=0.9;speechSynthesis.speak(u)'
                    style='width:100%;padding:10px;border:1px solid #E2E5E0;border-radius:8px;background:#fff;font-size:14px;font-weight:700;cursor:pointer'>
                    🔊 질문 듣기</button>""", unsafe_allow_javascript=True)
                audio = st.audio_input("🎙 눌러서 말로 답하기", key=f"rec_{len(iv.log)}")
            if audio is not None:
                if ai.has_ai():
                    with st.spinner("말씀을 받아 적는 중…"):
                        try:
                            said = ai.transcribe(audio.getvalue(), audio.type or "audio/wav")
                        except Exception as e:
                            said = None; st.error(f"받아쓰기 실패: {e}")
                    if said:
                        iv.reply(said); st.rerun()
                else:
                    st.info("데모 모드: 녹음을 글로 바꾸려면 Gemini 키가 필요해요. 아래 칸에 글로 입력해 주세요.")
            if ans := st.chat_input("말 대신 글로 입력해도 돼요"):
                iv.reply(ans); st.rerun()
        with st.expander(f"지금까지 나눈 대화 ({len(iv.log)})", expanded=iv.done):
            for who, msg in iv.log:
                st.chat_message(who).write(msg)
        if st.button("처음부터 다시", width="content"):
            st.session_state.iv = Interview(); st.session_state.pop("iv_result", None); st.rerun()
        if iv.done:
            if "iv_result" not in st.session_state:
                with st.spinner("대화를 표로 정리하는 중…"):
                    st.session_state.iv_result = run_structure(iv)
            res = st.session_state.iv_result
            with st.container(key="gcard_ivres"):
                ui.html("<p class='df-card-title'>정리된 내용이 맞는지 확인해 주세요</p>")
                st.dataframe(pd.DataFrame(res.get("retiree", {}).items(), columns=["항목", "답변"]), hide_index=True, width="stretch")
                ui.html("<p class='df-card-title' style='margin-top:8px'>물려줄 거래처</p>")
                buyers = res.get("buyers", [])
                st.dataframe(pd.DataFrame(buyers), hide_index=True, width="stretch")
                if st.button("맞아요, 저장하기", type="primary", width="stretch"):
                    save_retiree(res.get("retiree", {}), iv.log)
                    for bb in buyers:
                        bb.setdefault("source", "은퇴농 구술")
                        bb.setdefault("from_farmer", (res.get("retiree", {}).get("기본정보", "") or "인터뷰 농가")[:12])
                        bb.setdefault("lat", 37.64); bb.setdefault("lng", 128.56)
                        if bb.get("name"):
                            save_buyer(bb)
                    st.success("저장했어요. 이제 '판로 찾기'에서 청년농과 매칭됩니다.")
    with tab2:
        up = st.file_uploader("손글씨 장부 사진", type=["jpg", "jpeg", "png"])
        use_sample = st.checkbox("예시 장부 사진 사용", value=up is None)
        img = up.getvalue() if up else (open("data/sample_ledger.jpg", "rb").read() if use_sample else None)
        if img:
            st.image(img, width="stretch")
            if st.button("장부 읽기", type="primary", width="stretch"):
                rows = read_ledger(img, up.type if up else "image/jpeg")
                if rows is None:
                    st.info("데모 모드: Gemini 키가 없어 예시 장부의 정답 데이터를 보여줍니다.")
                    st.dataframe(pd.read_csv("data/ledger_truth.csv").head(24), hide_index=True, width="stretch")
                else:
                    st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")

# ───────────────────────── 모바일 06 · 판로 찾기 (모델 2) ─────────────────────────
elif page == P_FIND:
    ui.crumb("판로 찾기", "조건에 맞는 판로 찾기")
    y = me()
    ui.hero(f"판로 찾기 · {y['name']}", "내가 준비할 수 있는<br>판로부터",
            "지역과 수량, 납품 조건을 살펴보고 시험 납품으로 시작해 보세요.")
    with st.container(key="gcard_cond"):
        ui.html(f"<p class='df-card-title'>내 출하 조건 · {'/'.join(y['items'])} / {str(y['region']).split()[0]} / 주당 {int(y['weekly_kg']):,}kg</p>"
                "<p class='df-sub'>조건을 바꾸면 다른 판로도 찾아볼 수 있어요.</p>")
    with st.container(key="wcard_form"):
        mode = st.radio("청년농", ["등록된 농가", "직접 입력"], horizontal=True, label_visibility="collapsed",
                        index=1 if st.session_state.get("me_custom") else 0)
        if mode == "등록된 농가":
            st.session_state.pop("me_custom", None)
            st.selectbox("농가", FARMERS["name"], key="me",
                         format_func=lambda n: f"{n} · {FARMERS.set_index('name').loc[n, 'region']}")
        else:
            with st.form("young"):
                nm = st.text_input("농가 이름", "다시농장")
                region = st.text_input("지역", "평창군 진부면")
                items = st.multiselect("품목", ["감자", "토마토"], ["감자"])
                c1, c2 = st.columns(2)
                boxes = c1.number_input("주당 출하(20kg 상자)", 1, 1000, 30)
                wish = c2.number_input("희망 단가(원/20kg)", 5000, 100000, 24000, step=1000)
                grade = st.select_slider("주로 낼 수 있는 등급", ["무관", "중", "상", "특"], "상")
                months = st.multiselect("출하 가능 월", list(range(1, 13)), [8, 9, 10])
                days = st.multiselect("납품 가능 요일", list("월화수목금토"), ["화", "목"])
                truck = st.checkbox("트럭 있음", True)
                cert_no = st.text_input("인증번호 (있으면 공공데이터에서 자동 조회)")
                certs = st.multiselect("보유 인증 (조회가 안 되면 직접 선택)", ["GAP", "무농약", "유기농"])
                if st.form_submit_button("이 조건으로 찾기", type="primary", width="stretch"):
                    hit = public_lookup("cert", cert_no) if cert_no else None
                    coords = {"평창": (37.37, 128.39), "강릉": (37.75, 128.88), "정선": (37.38, 128.66), "원주": (37.34, 127.92)}
                    la, lo = next((v for k, v in coords.items() if k in region), (37.64, 128.57))
                    st.session_state.me_custom = {
                        "name": nm, "region": region, "lat": la, "lng": lo, "items": items,
                        "grade": {"무관": 1, "중": 2, "상": 3, "특": 4}[grade], "weekly_kg": boxes * 20, "months": months,
                        "days": days, "wish_price_kg": wish / 20, "certs": certs + (["GAP"] if hit else []),
                        "truck": "Y" if truck else "N", "intro": f"{region} {','.join(items)} 주 {boxes}상자"}
                    st.session_state.cert_msg = ("공공데이터에서 인증을 찾아 자동으로 넣었어요." if hit else
                                                 "공공데이터에서 찾지 못해 직접 선택한 인증으로 계산했어요.") if cert_no else ""
                    st.rerun()
            if st.session_state.get("cert_msg"):
                st.caption(st.session_state.cert_msg)
    y = me()
    res, excluded = matching.recommend_for_farmer(farmer=y, top=3, weights=st.session_state.weights)
    ui.html(f"<div class='df-pad'><p class='df-card-title' style='margin:6px 0 0'>추천 구매처 {len(res)}곳</p></div>")
    for i, r in enumerate(res):
        ui.match_card(r, key=f"m{i}", on_click=go, args=(P_DETAIL,), kwargs={"sel": r})
    if excluded:
        with st.expander(f"필수 조건이 맞지 않는 구매처 {len(excluded)}곳"):
            st.dataframe(pd.DataFrame(excluded), hide_index=True, width="stretch")

# ───────────────────────── 모바일 07 · 구매처 상세 ─────────────────────────
elif page == P_DETAIL:
    ui.crumb("판로 찾기", "구매처 납품 조건 보기")
    r = st.session_state.get("sel")
    with st.container(key="pad_back"):
        st.button("← 판로 목록으로", width="stretch", on_click=go, args=(P_FIND,))
    if not r:
        st.info("판로 찾기에서 구매처를 먼저 골라 주세요.")
    else:
        b = load_buyers().set_index("name").loc[r["거래처"]]
        with st.container(key="gcard_buyer"):
            ui.html(ui.chip(f"매칭률 {r['매칭률']}%") + ui.chip(r["출처"], "color/buyer")
                    + f"<p class='df-name'>{r['거래처']}</p>"
                    f"<p class='df-sub' style='color:#1E2621'>{b['location']} · {r['구매처유형']}</p><br>"
                    f"<p class='df-sub'>{r['농가']}의 거래 경험을 이어받는 판로예요.</p>")
            st.button("시험 납품 신청", type="primary", width="stretch", on_click=go, args=(P_TRIAL,))
        with st.container(key="wcard_regular"):
            ui.html("<p class='df-card-title'>앞으로 이어갈 정기 납품</p>"
                    + ui.kv("품목", "/".join(b["items"]))
                    + ui.kv("수량", f"주 {int(b['weekly_kg']):,}kg")
                    + ui.kv("단가", f"{int(b['price_kg']):,}원/kg")
                    + ui.kv("시기·요일", f"{min(b['months'])}~{max(b['months'])}월 · {'/'.join(b['days']) or '무관'}")
                    + ui.kv("배송·정산", f"{b['delivery'] or '-'} · {b['settlement'] or '-'}"))
        with st.container(key="wcard_score"):
            ui.html("<p class='df-card-title'>기준별 점수</p>"
                    + "".join(ui.score_bar(k, v, f"· 비중 {st.session_state.weights[k]}") for k, v in r["항목점수"].items()))
            with st.expander("요구 조건 / 내 조건 비교"):
                st.dataframe(pd.DataFrame(r["근거"].items(), columns=["기준", "구매처 요구 / 내 공급"]), hide_index=True, width="stretch")
        if st.session_state.get("exp_for") != (r["거래처"], r["청년농"]):
            with st.spinner("AI가 추천 이유를 정리하는 중…"):
                st.session_state.exp = matching.explain(r)
                st.session_state.exp_for = (r["거래처"], r["청년농"])
        with st.container(key="wcard_ai"):
            ui.html("<p class='df-card-title'>AI 설명</p><p class='df-sub' style='color:#1E2621'>"
                    + st.session_state.exp.replace("\n", "<br>") + "</p>")
        with st.container(key="wcard_map"):
            ui.html(f"<p class='df-card-title'>거리 {r['거리km']}km</p>")
            show_map([(r["청년농"], r["청년농위도"], r["청년농경도"]), (r["거래처"], r["위도"], r["경도"])])

# ───────────────────────── 모바일 08 · 시험 납품 신청 ─────────────────────────
elif page == P_TRIAL:
    ui.crumb("판로 찾기", "시험 납품 신청")
    r = st.session_state.get("sel")
    if not r:
        st.info("구매처를 먼저 골라 주세요.")
        st.button("판로 찾기로", width="stretch", on_click=go, args=(P_FIND,))
    else:
        b = load_buyers().set_index("name").loc[r["거래처"]]
        ui.hero("판로 찾기 · 시험 납품 신청", f"{r['거래처']}에<br>시험 납품을 신청해요",
                "작은 납품으로 서로의 조건을 확인하는 첫걸음입니다.")
        with st.container(key="gcard_trial"):
            ui.html(ui.chip("시험 납품") + f"<p class='df-name'>{r['거래처']}</p>" + ui.kv("지역", b["location"]))
            with st.form("trial"):
                item = st.selectbox("품목", b["items"])
                qty = st.text_input("수량", "20kg")
                pack = st.text_input("포장", "10kg 상자 2개, 크기별 선별")
                c1, c2 = st.columns(2)
                day = c1.date_input("희망 날짜", dt.date.today() + dt.timedelta(days=4))
                hour = c2.selectbox("시간", ["오전 9시", "오전 11시", "오후 2시"])
                memo = st.text_area("구매처에 남길 말", "샘플 먼저 보내드리고 조건을 맞춰 보고 싶습니다.", height=80)
                if st.form_submit_button("시험 납품 신청하기", type="primary", width="stretch"):
                    save_trial(r["청년농"], r["거래처"], f"{item} {qty}", f"{day} {hour} · {pack} · {memo}")
                    st.session_state.trial_info = {"농가": r["청년농"], "구매처": r["거래처"], "품목·수량": f"{item} {qty}",
                                              "희망 날짜": f"{day.year}년 {day.month}월 {day.day}일 {hour}", "포장": pack}
                    go(P_DONE); st.rerun()

# ───────────────────────── 모바일 · 시험 납품 신청 완료 ─────────────────────────
elif page == P_DONE:
    ui.html("<div class='df-pad'><p class='df-eyebrow' style='margin-top:14px'>시험 납품 신청 · 접수 완료</p></div>")
    t = st.session_state.get("trial_info")
    with st.container(key="gcard_done"):
        ui.html("<div class='df-check'>✓</div><p class='df-title'>시험 납품 신청을<br>보냈어요</p>"
                "<p class='df-sub'>아직 납품이 확정된 것은 아니에요.<br>구매처가 신청을 검토하면 알림으로 알려드릴게요.</p>")
    if t:
        with st.container(key="wcard_req"):
            ui.html("<p class='df-card-title'>신청 내용</p><p class='df-sub' style='color:#1E2621;line-height:1.9'>"
                    f"신청 농가 &nbsp;{t['농가']}<br>구매처 &nbsp;{t['구매처']}<br>품목·수량 &nbsp;{t['품목·수량']}<br>"
                    f"희망 날짜 &nbsp;{t['희망 날짜']}<br>포장 &nbsp;{t['포장']}</p>")
    with st.container(key="ycard_next"):
        ui.html("<p class='df-card-title'>다음은 구매처 검토예요.</p>"
                "<p class='df-sub'>구매처가 수락하면 은퇴 농가와 함께 첫 납품 일정을 맞춥니다.</p>")
    with st.container(key="pad_home"):
        st.button("홈으로", type="primary", width="stretch", on_click=go, args=(P_HOME,))

# ───────────────────────── 납품 조건 보기 (구매처 쪽) ─────────────────────────
elif page == P_BUYER:
    ui.crumb("납품 조건 보기", "후속 공급자 찾기", icon="box")
    ui.hero("구매처 · 납품 조건", "우리 조건에 맞는<br>다음 농가를 찾아요",
            "같은 점수표를 구매처 입장에서 거꾸로 조회합니다.")
    buyers = load_buyers()
    names = list(buyers["name"])
    if st.session_state.get("buyer_sel") not in names:
        st.session_state.buyer_sel = names[0]
    with st.container(key="wcard_bsel"):
        bname = st.selectbox("구매처", names, key="buyer_sel")
    cands = matching.recommend_for_buyer(bname, top=3, weights=st.session_state.weights)
    ui.html(f"<div class='df-pad'><p class='df-card-title' style='margin:6px 0 0'>추천 농가 {len(cands)}곳</p></div>")
    if not cands:
        st.info("조건을 통과한 농가가 없습니다.")
    for i, r in enumerate(cands):
        ui.match_card(r, key=f"c{i}", who="farmer")
    with st.container(key="pad_newb"):
        st.button("새 구매처 등록하기", width="stretch", on_click=go, args=(P_ONB_B,))

# ───────────────────────── 나의 다시팜 (데이터 · 매칭 기준) ─────────────────────────
elif page == P_MY:
    ui.crumb("나의 다시팜", "매칭 기준과 기록", icon="user")
    ui.hero("나의 다시팜", "매칭 기준과<br>기록을 확인해요", "가중치는 예시값이에요. 바꾸면 판로 찾기 결과에 바로 반영됩니다.")
    st.caption("AI: " + ("Gemini 연결됨" if ai.has_ai() else "데모 모드 (키 없음)") + " · 모든 이름·수치는 시연용 가상 데이터")
    with st.container(key="wcard_w"):
        ui.html("<p class='df-card-title'>기준별 비중</p>")
        w = st.session_state.weights
        for k in list(w):
            w[k] = st.slider(k, 0, 40, w[k], key=f"w_{k}")
        st.caption(f"합계 {sum(w.values())} (100이 아니어도 비율로 환산)")
    with st.expander("시험 납품 신청 기록"):
        st.dataframe(list_trials(), hide_index=True, width="stretch")
    with st.expander("구매처 표 (요구 조건)"):
        st.dataframe(load_buyers().drop(columns=["raw_text"]), hide_index=True, width="stretch")
    with st.expander("청년농 표 (공급 능력)"):
        st.dataframe(FARMERS, hide_index=True, width="stretch")
    with st.expander("은퇴농 인터뷰 기록"):
        st.dataframe(pd.DataFrame([dict(p, 저장일시=c) for c, p in list_retirees()]), hide_index=True, width="stretch")
