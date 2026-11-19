"""피그마 컴포넌트와 1:1로 대응하는 화면 부품 (모바일 390px 기준).
피그마 → 코드
  Header(다시, FARM + 메뉴)  → header()
  Breadcrumb(홈 / 오늘 할 일) → crumb()
  Hero(작은 제목 + 큰 제목 + 설명) → hero()
  Card/Green, Card/White, Card/Yellow → st.container(key="gcard_…" / "wcard_…" / "ycard_…")
  Chip → chip()   ScoreBar → score_bar()   MatchCard → match_card()
색·모서리·글꼴 값은 design/tokens.json 에서 읽는다.
"""
import os
import json
import streamlit as st

_T = json.load(open(os.path.join(os.path.dirname(os.path.dirname(__file__)), "design", "tokens.json"), encoding="utf-8"))


def tok(name):
    return _T[name]


ICON = {
    "home": "<svg width='15' height='15' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2'><path d='M3 11l9-7 9 7v9a1 1 0 0 1-1 1h-5v-6H9v6H4a1 1 0 0 1-1-1z'/></svg>",
    "search": "<svg width='15' height='15' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2'><circle cx='11' cy='11' r='7'/><path d='M20 20l-3.5-3.5'/></svg>",
    "swap": "<svg width='15' height='15' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2'><path d='M4 8h14l-3-3M20 16H6l3 3'/></svg>",
    "box": "<svg width='15' height='15' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2'><path d='M3 7l9-4 9 4-9 4zM3 7v10l9 4 9-4V7'/></svg>",
    "user": "<svg width='15' height='15' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2'><circle cx='12' cy='8' r='4'/><path d='M4 21c1-4 4-6 8-6s7 2 8 6'/></svg>",
}


def inject_css():
    W = tok("layout/mobile-width")
    st.markdown(f"""
    <style>
      @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
      html, body, .stApp, [class*="css"], button, input, textarea {{ font-family:{tok('font/family')} !important; }}
      [data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"], header[data-testid="stHeader"],
      [data-testid="stToolbar"], #MainMenu, footer {{ display:none !important; }}
      .stApp {{ background:{tok('color/canvas')}; }}
      [data-testid="stMainBlockContainer"], .block-container {{
          max-width:{W} !important; padding:0 0 48px 0 !important; background:{tok('color/background')};
          min-height:100vh; box-shadow:0 0 0 1px {tok('color/border')}; }}
      [data-testid="stMainBlockContainer"] > div {{ gap:12px; }}
      p, li, label {{ font-size:{tok('font/size-body')}; }}

      /* Header */
      .st-key-hdr {{ background:{tok('color/surface')}; padding:12px 14px; border-bottom:1px solid {tok('color/border')}; }}
      .st-key-hdr p {{ margin:0; }}
      .df-logo {{ font-weight:800; font-size:16px; color:{tok('color/primary')}; }}
      .st-key-hdr button {{ min-height:0; padding:5px 10px; font-size:12px; border:1px solid {tok('color/border')};
          border-radius:{tok('radius/button')}; background:#fff; color:{tok('color/text')}; }}

      /* 본문 여백 */
      .df-pad {{ padding:0 14px; }}
      div[class*="st-key-pad"] {{ padding:0 14px; }}
      .stTabs, [data-testid="stChatMessage"], [data-testid="stExpander"], [data-testid="stCaptionContainer"],
      [data-testid="stAlert"], [data-testid="stImage"], [data-testid="stFileUploader"], [data-testid="stCheckbox"],
      [data-testid="stSlider"], [data-testid="stChatInput"] {{ padding-left:14px; padding-right:14px; box-sizing:border-box; }}
      div[class*="st-key-wcard"] [data-testid="stExpander"], div[class*="st-key-gcard"] [data-testid="stExpander"],
      div[class*="st-key-wcard"] [data-testid="stCaptionContainer"], div[class*="st-key-wcard"] [data-testid="stSlider"],
      .stTabs [data-testid="stChatMessage"], .stTabs [data-testid="stImage"], .stTabs [data-testid="stFileUploader"],
      .stTabs [data-testid="stCheckbox"], .stTabs [data-testid="stCaptionContainer"], .stTabs [data-testid="stAlert"],
      .stTabs [data-testid="stExpander"] {{ padding-left:0; padding-right:0; }}

      /* Breadcrumb */
      .df-crumb {{ display:flex; align-items:center; gap:6px; background:{tok('color/crumb')}; color:{tok('color/text')};
          border-radius:{tok('radius/button')}; padding:8px 12px; font-size:12px; font-weight:600; margin:12px 0 8px; }}
      .df-crumb .sep {{ color:{tok('color/text-sub')}; }}

      /* Hero */
      .df-eyebrow {{ font-size:12px !important; font-weight:700; color:{tok('color/text')}; margin:6px 0 10px; }}
      .df-title {{ font-size:{tok('font/size-title')} !important; font-weight:800; line-height:1.4 !important; color:{tok('color/text')}; margin:0 0 10px !important; }}
      .df-sub {{ font-size:12.5px !important; color:{tok('color/text-sub')}; line-height:1.6; margin:0; }}
      .df-label {{ font-size:12px; color:{tok('color/text-sub')}; }}
      .df-big {{ font-size:22px; font-weight:800; color:{tok('color/primary')}; }}

      /* Cards */
      div[class*="st-key-gcard"], div[class*="st-key-wcard"], div[class*="st-key-ycard"] {{
          border-radius:{tok('radius/card')}; padding:{tok('space/card-padding')} !important; margin:0 14px; width:auto !important; }}
      div[class*="st-key-gcard"] {{ background:{tok('color/primary-soft')}; }}
      div[class*="st-key-wcard"] {{ background:{tok('color/surface')}; border:1px solid {tok('color/border')}; }}
      div[class*="st-key-ycard"] {{ background:{tok('color/warning-soft')}; }}
      div[class*="st-key-gcard"] [data-testid="stElementContainer"], div[class*="st-key-wcard"] [data-testid="stElementContainer"],
      div[class*="st-key-ycard"] [data-testid="stElementContainer"],
      div[class*="st-key-gcard"] [data-testid="stLayoutWrapper"], div[class*="st-key-wcard"] [data-testid="stLayoutWrapper"] {{ padding-left:0 !important; padding-right:0 !important; }}
      .df-card-title {{ font-size:15px !important; font-weight:800; margin:0 0 6px; color:{tok('color/text')}; }}
      .df-name {{ font-size:20px !important; font-weight:800; margin:4px 0 8px; color:{tok('color/text')}; }}
      .df-kv {{ margin:0 0 8px; }} .df-kv span {{ display:block; font-size:11.5px; color:{tok('color/text-sub')}; }}
      .df-kv b {{ font-size:13px; }}
      .df-check {{ width:34px; height:34px; border-radius:50%; background:{tok('color/primary')}; color:#fff;
          display:flex; align-items:center; justify-content:center; font-size:18px; margin-bottom:12px; }}

      /* Buttons */
      .stButton button, .stFormSubmitButton button {{ border-radius:{tok('radius/button')}; min-height:40px; font-size:13px; font-weight:700; }}
      .stButton button[kind="primary"], .stFormSubmitButton button[kind="primaryFormSubmit"] {{
          background:{tok('color/primary')}; border-color:{tok('color/primary')}; color:#fff; }}
      .stButton button[kind="secondary"] {{ background:#fff; border:1px solid {tok('color/border')}; color:{tok('color/text')}; }}

      /* Chip / ScoreBar */
      .df-chip {{ display:inline-block; padding:3px 10px; margin:0 4px 4px 0; border-radius:{tok('radius/chip')};
          font-size:11.5px; font-weight:600; background:#fff; }}
      .df-bar {{ height:6px; border-radius:6px; background:{tok('color/border')}; overflow:hidden; }}
      .df-bar > div {{ height:6px; background:{tok('color/primary')}; }}

      /* 고객 선택 버튼 (모바일 00) */
      .st-key-pad_roles {{ gap:14px; }}
      .st-key-pad_roles .stButton button {{ min-height:64px; font-size:17px !important; font-weight:700;
          border:1.5px solid {tok('color/text')}; border-radius:12px; background:#fff; }}
      .st-key-pad_roles .stButton button p {{ font-size:17px !important; }}
      .st-key-pad_roles .stButton button:hover {{ border-color:{tok('color/primary')}; color:{tok('color/primary')}; background:{tok('color/primary-soft')}; }}

      /* Menu popover */
      [data-testid="stPopoverBody"] {{ width:240px; }}
      [data-testid="stPopoverBody"] .stButton button, [data-testid="stPopoverBody"] .stButton button > div {{ justify-content:flex-start; text-align:left; border:none; background:transparent; min-height:34px; font-weight:600; }}
      [data-testid="stPopoverBody"] .stButton button:hover {{ background:{tok('color/primary-soft')}; }}
      [data-testid="stForm"] {{ border:none; padding:0; }}
    </style>""", unsafe_allow_html=True)


def header(menu_items, go):
    """Header: 왼쪽 '다시, FARM' 로고, 오른쪽 '메뉴' 버튼(팝오버)"""
    with st.container(key="hdr", horizontal=True, vertical_alignment="center", horizontal_alignment="distribute"):
        st.markdown("<span class='df-logo'>다시, FARM</span>", unsafe_allow_html=True, width="content")
        with st.popover("메뉴", width="content", key=f"menu_{st.session_state.get('page', '')}"):  # 페이지가 바뀌면 메뉴가 닫히도록
            for group, items in menu_items:
                st.caption(group)
                for label, page in items:
                    st.button(label, key=f"m_{group}_{label}", on_click=go, args=(page,), width="stretch")


def crumb(*parts, icon="search"):
    sep = "<span class='sep'>/</span>"
    st.markdown(f"<div class='df-pad'><div class='df-crumb'>{ICON[icon]}{sep.join(f'<span>{p}</span>' for p in parts)}</div></div>",
                unsafe_allow_html=True)


def hero(eyebrow, title, sub=""):
    st.markdown("<div class='df-pad'>" + (f"<p class='df-eyebrow'>{eyebrow}</p>" if eyebrow else "")
                + f"<p class='df-title'>{title}</p>" + (f"<p class='df-sub'>{sub}</p>" if sub else "") + "</div>",
                unsafe_allow_html=True)


def html(s):
    st.markdown(s, unsafe_allow_html=True)


def chip(text, color="color/primary"):
    return f"<span class='df-chip' style='color:{tok(color)}'>{text}</span>"


def kv(label, value):
    return f"<div class='df-kv'><span>{label}</span><b>{value}</b></div>"


def score_bar(label, value, note=""):
    pct = max(0, min(100, round(value * 100)))
    return (f"<div style='margin:8px 0'><div style='display:flex;justify-content:space-between'>"
            f"<span class='df-label'>{label}</span><span class='df-label'>{pct}점 {note}</span></div>"
            f"<div class='df-bar'><div style='width:{pct}%'></div></div></div>")


def match_card(r, key, who="buyer", on_click=None, args=(), kwargs=None):
    """MatchCard: 판로 목록의 한 칸 (흰 카드 + 매칭률 + 부족 조건 + 버튼)"""
    name = r["거래처"] if who == "buyer" else r["청년농"]
    sub = f"{r['구매처유형']} · {r['거리km']}km" if who == "buyer" else f"거리 {r['거리km']}km"
    gaps = "".join(chip("부족 · " + g.split(" (")[0], "color/text-sub") for g in r["부족한조건"]) or chip("조건 모두 충족")
    src = chip(r["출처"], "color/buyer") if r.get("출처") else ""
    with st.container(key=f"wcard_{key}"):
        html(f"<div style='display:flex;justify-content:space-between;align-items:flex-start'>"
             f"<div><p class='df-card-title'>{name}</p><span class='df-label'>{sub}</span></div>"
             f"<div style='text-align:right'><span class='df-label'>매칭률</span><div class='df-big'>{r['매칭률']}%</div></div></div>"
             f"<div style='margin-top:10px'>{src}{gaps}</div>")
        if on_click:
            st.button("납품 조건 보기", key=f"b_{key}", on_click=on_click, args=args, kwargs=kwargs or {}, width="stretch")
