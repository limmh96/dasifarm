"""피그마(Figma Make) '다시팜' 디자인을 Streamlit에서 그대로 쓰기 위한 부품.
- design/figma.css : 피그마 앱의 CSS 원본(빌드본)을 그대로 사용
- 아래 OVERRIDE    : Streamlit 위젯(버튼·입력칸)을 피그마의 .primary/.secondary/.field 모양으로 맞춤
- 클래스 이름은 피그마 코드(App.tsx)와 동일: page-title, eyebrow, role-card, market-card, key-values ...
"""
import os
import html as _h
import streamlit as st

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_read = lambda p: open(os.path.join(BASE, p), encoding="utf-8").read()
FARM_SVG, FARM_GROWN_SVG = _read("design/farm.svg"), _read("design/farm_grown.svg")

PATHS = {
    "sprout": '<path d="M12 21V11M12 14C5 15 2 10 3 5c6-1 10 3 9 9ZM12 11c0-6 4-9 9-8 1 6-3 10-9 8Z"/>',
    "shop": '<path d="M4 10v11h16V10M3 7l2-4h14l2 4v3c-2 2-4 2-6 0-2 2-4 2-6 0-2 2-4 2-6 0V7ZM9 21v-7h6v7M3 7h18"/>',
    "heart": '<path d="M20 5c-3-3-6-1-8 1-2-2-5-4-8-1s-1 7 1 9l7 7 7-7c2-2 4-6 1-9Z"/><path d="m7 12 3-2 3 3 3-2"/>',
    "check": '<path d="m5 12 4 4L19 6"/>',
    "arrow": '<path d="m9 5 7 7-7 7M4 12h12"/>',
    "back": '<path d="m15 5-7 7 7 7"/>',
    "home": '<path d="m3 10 9-7 9 7v11H3Z"/><path d="M9 21v-8h6v8"/>',
    "mission": '<rect x="5" y="4" width="14" height="18" rx="3"/><path d="M9 3h6v4H9ZM9 13l2 2 4-4"/>',
    "user": '<circle cx="12" cy="7" r="4"/><path d="M4 22v-3a8 8 0 0 1 16 0v3"/>',
    "bell": '<path d="M5 10a7 7 0 0 1 14 0c0 6 2 6 2 8H3c0-2 2-2 2-8ZM10 22h4"/>',
    "mic": '<rect x="8" y="2" width="8" height="14" rx="4"/><path d="M4 11a8 8 0 0 0 16 0M12 19v3M8 22h8"/>',
    "box": '<path d="m3 7 9-5 9 5v12l-9 4-9-4ZM3 7l9 5 9-5M12 12v11M8 5l9 5"/>',
    "leaf": '<path d="M20 3C7 0-1 12 6 18S24 14 20 3ZM4 21 16 9"/>',
    "edit": '<path d="m4 16 12-12 4 4L8 20H4ZM13 7l4 4"/>',
    "camera": '<path d="M4 8h3l2-3h6l2 3h3v11H4Z"/><circle cx="12" cy="13" r="3.5"/>',
    "spark": '<path d="M12 3v4M12 17v4M3 12h4M17 12h4M6 6l2.5 2.5M15.5 15.5 18 18M6 18l2.5-2.5M15.5 8.5 18 6"/>',
}


def icon(name, size=24):
    return (f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" '
            f'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{PATHS[name]}</svg>')


def esc(s):
    return _h.escape(str(s))


def br(s):
    return esc(s).replace("\n", "<br>")


def html(s):
    # st.html은 SVG·style을 걸러내므로 markdown(HTML 허용)으로 출력. 빈 줄이 있으면 markdown이 끼어들어서 한 줄로 만듦
    st.markdown(" ".join(str(s).split("\n")), unsafe_allow_html=True)


OVERRIDE = """
:root{--brand-hover:#05b268}
html,body,.stApp,[data-testid="stAppViewContainer"]{background:var(--farm-pale-green)!important;font-family:"Pretendard",sans-serif!important}
.stApp *{font-family:"Pretendard",sans-serif}
.stApp [data-testid="stIconMaterial"], .stApp span[class*="material"]{font-family:"Material Symbols Rounded"!important}
header[data-testid="stHeader"],[data-testid="stToolbar"],[data-testid="stSidebar"],[data-testid="stSidebarCollapsedControl"],footer,#MainMenu,[data-testid="stDecoration"],[data-testid="stStatusWidget"]{display:none!important}
[data-testid="stMain"]{padding:0!important}
[data-testid="stMainBlockContainer"]{max-width:430px!important;width:100%;min-height:100dvh;margin:0 auto;padding:0 20px 40px!important;
  background:var(--farm-background);box-shadow:0 0 70px var(--farm-shadow);color:var(--farm-main-text)}
[data-testid="stMainBlockContainer"] > div > [data-testid="stVerticalBlock"]{gap:19px}
.stApp h1,.stApp h2,.stApp h3{padding:0;font-family:"Pretendard",sans-serif}
.stApp h1{font-size:29px;font-weight:700;line-height:1.45;letter-spacing:-1.3px;white-space:pre-line;color:var(--farm-main-text)}
.stApp h2{font-size:19px;font-weight:700;letter-spacing:-.6px;color:var(--farm-main-text)}
.stApp h3{font-size:17px;font-weight:600;color:var(--farm-main-text)}
[data-testid="stMarkdownContainer"] p{margin:0}[data-testid="stMarkdownContainer"]{font-size:inherit}
.page-title p{color:var(--farm-secondary-text);font-size:16px;line-height:1.75;margin-top:10px;word-break:keep-all}

/* ── 버튼 = 피그마 .primary / .secondary */
.stButton,.stButton>div,.stFormSubmitButton,.stFormSubmitButton>div{width:100%!important}
.stButton button,.stFormSubmitButton button{width:100%!important;min-height:54px;padding:15px 18px;border-radius:13px;font-size:16px;font-weight:600;letter-spacing:-.4px;position:relative}
.stButton button p,.stFormSubmitButton button p{font-size:16px;font-weight:600}
.stButton button[kind="primary"],.stFormSubmitButton button[kind="primaryFormSubmit"]{color:var(--farm-main-text);background:var(--farm-action-green);border:1px solid var(--farm-action-green);box-shadow:0 4px 10px var(--farm-shadow)}
.stButton button[kind="primary"]:hover,.stFormSubmitButton button[kind="primaryFormSubmit"]:hover{background:var(--brand-hover);border-color:var(--brand-hover);color:var(--farm-main-text)}
.stButton button[kind="primary"]::after{content:"";position:absolute;right:19px;width:20px;height:20px;background:currentColor;
  -webkit-mask:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='1.7' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='m9 5 7 7-7 7M4 12h12'/%3E%3C/svg%3E") center/contain no-repeat}
.stButton button[kind="secondary"]{color:var(--farm-main-text);background:var(--farm-background);border:1px solid var(--farm-border)}
.stButton button[kind="secondary"]:hover{background:var(--farm-pale-green);border-color:var(--farm-border);color:var(--farm-main-text)}
.stButton button:disabled{opacity:.45}

/* ── 입력칸 = 피그마 .field */
.stTextInput label p,.stTextArea label p,.stSelectbox label p,.stMultiSelect label p,.stNumberInput label p,.stDateInput label p,.stSelectSlider label p{font-size:16px!important;font-weight:500;color:var(--farm-main-text)}
.stTextInput [data-baseweb="input"],.stNumberInput [data-baseweb="input"],.stDateInput [data-baseweb="input"],.stTextArea [data-baseweb="textarea"],
.stSelectbox [data-baseweb="select"]>div,.stMultiSelect [data-baseweb="select"]>div{border:1px solid var(--farm-border)!important;border-radius:11px!important;min-height:54px;background:var(--farm-background)!important}
.stTextInput input,.stNumberInput input,.stDateInput input,.stTextArea textarea{font-size:16px!important;padding:14px!important;background:var(--farm-background)!important;color:var(--farm-main-text)}
.stTextInput [data-baseweb="input"]:focus-within,.stTextArea [data-baseweb="textarea"]:focus-within{border-color:var(--farm-primary-green)!important}
.stMultiSelect [data-baseweb="tag"]{background:var(--farm-pale-green)!important;color:var(--farm-main-text)!important}
.stCheckbox label p{font-size:15px;color:var(--farm-main-text)}
[data-testid="stForm"]{border:0;padding:0}
[data-testid="stForm"] [data-testid="stVerticalBlock"]{gap:19px}

/* ── 카드 전체를 누를 수 있게: 보이지 않는 버튼을 카드 위에 겹침 */
div[class*="st-key-ov_"]{position:relative;gap:0!important}
div[class*="st-key-ov_"] [data-testid="stElementContainer"]:has(.stButton){position:absolute;inset:0;z-index:5;margin:0;width:100%!important;height:100%!important}
div[class*="st-key-ov_"] [data-testid="stElementContainer"]:not(:has(.stButton)){pointer-events:none}
div[class*="st-key-ov_"] .stButton,div[class*="st-key-ov_"] .stButton>div{height:100%}
div[class*="st-key-ov_"] .stButton button{opacity:0;height:100%;min-height:0}

/* ── 헤더 · 하단 바 */
.st-key-hdr{min-height:78px;padding:23px 0 16px;justify-content:space-between;align-items:center;margin-bottom:-19px}
.st-key-hdr .stButton button{width:44px;min-height:44px;height:44px;padding:0;border:0;background:transparent;box-shadow:none}
.st-key-hdr .stButton button::after{display:none}
.st-key-wbottom{position:sticky;bottom:0;z-index:6;background:var(--farm-background);border-top:1px solid var(--farm-border);margin:0 -20px -40px;padding:27px 20px 20px}
.st-key-wbottom [data-testid="stMarkdownContainer"] p{text-align:center;font-size:14px;color:var(--farm-secondary-text);margin-top:12px}
.st-key-wbottom .stButton p{color:inherit!important;font-size:16px!important;margin:0!important}
.st-key-bnav{position:fixed;bottom:0;left:50%;transform:translateX(-50%);width:min(430px,100%);z-index:10;display:flex;flex-direction:row;gap:0;
  background:color-mix(in srgb,var(--farm-background) 93%,transparent);border-top:1px solid var(--farm-pale-green);padding:9px 8px 13px}
.st-key-bnav>div{flex:1}
.nav-item{color:var(--farm-secondary-text);display:flex;flex-direction:column;gap:5px;align-items:center;padding:5px;min-height:50px;font-size:14px}
.nav-item.active{color:var(--farm-primary-green);font-weight:600}
.with-nav-space{height:84px}

/* ── 필터 칩 */
.st-key-filters{flex-direction:row;gap:8px;flex-wrap:wrap}
.st-key-filters .stButton button{border-radius:30px;min-height:44px;padding:9px 17px;font-size:14px;width:auto;border:0;box-shadow:none}
.st-key-filters .stButton button p{font-size:14px}
.st-key-filters .stButton button[kind="secondary"]{background:var(--farm-pale-green);color:var(--farm-secondary-text)}
.st-key-filters .stButton button[kind="primary"]{background:var(--farm-primary-green)}
.st-key-filters .stButton button::after{display:none}

/* ── AI 분석 표시 */
.ai-badge{display:inline-flex;align-items:center;gap:5px;border-radius:30px;padding:4px 10px;font-size:13px;font-weight:600;background:var(--farm-primary-green);color:var(--farm-main-text)}
.fit-pct{font-size:30px;font-weight:800;color:var(--farm-primary-green);letter-spacing:-1px}
.score{margin:12px 0}.score .row{display:flex;justify-content:space-between;font-size:14px;color:var(--farm-secondary-text);margin-bottom:6px}
.score .track{height:7px;background:var(--farm-pale-green);border-radius:20px;overflow:hidden}.score .track i{display:block;height:100%;background:var(--farm-primary-green);border-radius:inherit}
.ai-steps{display:flex;flex-direction:column;gap:12px;text-align:left;width:100%;max-width:320px;margin-top:6px}
.ai-steps div{display:flex;gap:10px;align-items:center;font-size:15px;color:var(--farm-secondary-text)}
.ai-steps b{width:22px;height:22px;border-radius:50%;background:var(--farm-pale-green);color:var(--farm-primary-green);display:grid;place-items:center;font-size:12px}
.ai-steps .on{color:var(--farm-main-text);font-weight:600}.ai-steps .on b{background:var(--farm-primary-green);color:var(--farm-main-text)}
.ledger-thumb{width:100%;max-height:200px;object-fit:cover;border-radius:14px;border:1px solid var(--farm-border)}
[data-testid="stCameraInput"]{border-radius:14px;overflow:hidden}
[data-testid="stDataFrame"],[data-testid="stDataEditor"]{border:1px solid var(--farm-border);border-radius:11px}
.gap-0{margin-top:-19px}
.chat-log{display:flex;flex-direction:column;gap:10px}
.bubble{max-width:86%;padding:12px 14px;border-radius:14px;font-size:15px;line-height:1.65;word-break:keep-all}
.bubble b{display:block;font-size:12px;color:var(--farm-primary-green);margin-bottom:3px}
.bubble.ai{align-self:flex-start;background:var(--farm-background);border:1px solid var(--farm-border)}
.bubble.me{align-self:flex-end;background:var(--farm-pale-green)}
.bubble.me b{color:var(--farm-secondary-text)}
.wave{display:flex;align-items:center;justify-content:center;gap:4px;height:50px}
.wave i{display:block;width:4px;border-radius:4px;background:var(--farm-primary-green);opacity:.75}
[data-testid="stAudioInput"]{border:1px solid var(--farm-border);border-radius:14px}
.st-key-typed{gap:8px}
.st-key-typed .stButton,.st-key-typed .stButton>div{width:auto!important}
.st-key-typed .stButton button{min-height:44px;height:44px;padding:0 16px}
.st-key-typed .stButton button::after{display:none}
.st-key-typed .stTextInput [data-baseweb="input"]{min-height:44px}
.st-key-typed .stTextInput input{padding:10px 14px!important}
.stApp [data-stale="true"]{opacity:1!important;transition:none!important;filter:none!important}

/* ── 스크롤: 화면 높이를 넘는 내용은 위아래로 스크롤 */
[data-testid="stAppViewContainer"]{height:100dvh!important;overflow:hidden!important}
[data-testid="stMain"]{height:100%!important;overflow-y:auto!important;overflow-x:hidden!important;-webkit-overflow-scrolling:touch;overscroll-behavior:contain}
[data-testid="stMainBlockContainer"]{height:auto!important;min-height:100%!important;flex:none!important;padding-bottom:28px!important}

/* ── 데스크톱: 아이폰 18 Pro(402×874) 프레임 안에 보여주기 */
@media (min-width:600px){
  .stApp{display:flex!important;align-items:center;justify-content:center;min-height:100dvh}
  [data-testid="stAppViewContainer"]{position:relative!important;inset:auto!important;width:402px!important;height:min(874px,calc(100dvh - 40px))!important;
    flex:none;border-radius:52px;box-shadow:0 0 0 11px #1d2726,0 0 0 13px #3c4746,0 30px 70px rgba(21,63,61,.35);transform:translateZ(0);background:var(--farm-background)}
  [data-testid="stMainBlockContainer"]{max-width:402px!important;box-shadow:none!important}
  .st-key-bnav{width:100%!important;border-radius:0 0 52px 52px;padding-bottom:20px!important}
}

/* ── 시작 화면(팝업) */
.splash-pop{position:fixed;inset:0;z-index:1000;display:grid;place-items:center;background:var(--farm-splash-background-image) center/cover;
  animation:splash-gone 2.4s ease-in-out forwards}
.splash-pop img{width:72%;max-width:300px;opacity:0;filter:drop-shadow(0 8px 18px var(--farm-shadow));animation:splash-logo-reveal 1s cubic-bezier(.22,1,.36,1) .2s forwards;transform:translateY(12px) scale(.96)}
@keyframes splash-gone{0%,80%{opacity:1;visibility:visible}100%{opacity:0;visibility:hidden}}
.stApp [data-testid="stElementContainer"]:has(.splash-pop){position:absolute;height:0;margin:0}

/* ── 고객 선택 화면: 한 화면(874)에 맞추기 */
.welcome-hero{height:auto!important;padding:0!important;margin:-14px -20px -10px;overflow:visible!important}
.welcome-hero .farm-art{width:62%;margin:0 auto;display:block}
.welcome-title h1{font-size:27px;margin-bottom:4px}
.welcome-title>p{font-size:14px}
.st-key-roles{gap:10px!important}
.st-key-roles .role-card{min-height:82px;padding:14px 13px}
.role-help{margin-top:2px!important;font-size:12px!important}
.st-key-wbottom{padding:16px 0 18px!important;margin:0!important;width:100%!important;border-top:0!important;box-shadow:-20px 0 0 0 var(--farm-background),20px 0 0 0 var(--farm-background)}
.st-key-wbottom::before{content:"";position:absolute;top:0;left:-20px;right:-20px;border-top:1px solid var(--farm-border)}
div[class*="st-key-ov_"] [data-testid="stMarkdown"],div[class*="st-key-ov_"] [data-testid="stMarkdownContainer"],div[class*="st-key-ov_"] [data-testid="stMarkdown"] > div{margin-bottom:0!important}
.stApp h2 a,.stApp h1 a,.stApp h3 a{display:none!important}
.market-copy h2,.goal-card h2{display:flex!important;justify-content:space-between;align-items:center}
.market-picture .ai-badge{position:absolute;top:12px;right:12px}
.st-key-hdr .stButton,.st-key-hdr .stButton>div{width:44px!important}
.st-key-filters .stButton,.st-key-filters .stButton>div{width:auto!important}
.st-key-bnav .stButton,.st-key-bnav .stButton>div{width:100%!important}
"""


def inject():
    html("<style>" + _read("design/figma.css") + OVERRIDE + "</style>")


def hide_stale():
    """로딩 화면 동안 이전 화면이 아래에 남아 보이지 않게"""
    html('<style>.stApp [data-stale="true"]{display:none!important}</style>')


# ── 피그마 컴포넌트 (App.tsx 의 같은 이름) ──
def title(eyebrow, heading, desc=""):
    html(f'<div class="page-title"><span class="eyebrow">{esc(eyebrow)}</span><h1>{br(heading)}</h1>'
         + (f"<p>{esc(desc)}</p>" if desc else "") + "</div>")


def steps(active):  # 1 고객 선택 · 2 정보 등록 · 3 시작하기
    def one(n, label, cls):
        mark = icon("check", 13) if cls == "done" else str(n)
        return f'<span class="{cls}"><b>{mark}</b>{label}</span>'
    cls = lambda n: "active" if n == active else ("done" if n < active else "")
    html(f'<div class="steps {"steps-welcome" if active == 1 else ""}" style="padding-left:0;padding-right:0">'
         f'{one(1, "고객 선택", cls(1))}<i></i>{one(2, "정보 등록", cls(2))}<i></i>{one(3, "시작하기", cls(3))}</div>')


def hint():
    html('<div class="demo-note"><span class="demo-dot"></span>시연용 데이터 · 실제 조회·인증이 아니에요</div>')


def section(t, right=""):
    html(f'<div class="section-heading"><h2>{esc(t)}</h2>' + (f"<span>{esc(right)}</span>" if right else "") + "</div>")


def kv(rows):
    return '<dl class="key-values">' + "".join(f"<div><dt>{esc(k)}</dt><dd>{esc(v)}</dd></div>" for k, v in rows) + "</dl>"


def score_bar(label, value, note=""):
    p = max(0, min(100, round(value * 100)))
    return (f'<div class="score"><div class="row"><span>{esc(label)}</span><span>{p}점 {esc(note)}</span></div>'
            f'<div class="track"><i style="width:{p}%"></i></div></div>')


def success(heading, desc, eyebrow="차근차근, 다음 걸음", grown=True):
    html(f'<div class="success-page" style="padding-left:0;padding-right:0"><div class="success-mark">{icon("check", 35)}</div>'
         f'<span class="eyebrow">{esc(eyebrow)}</span><h1>{br(heading)}</h1><p>{esc(desc)}</p>'
         f'<div class="farm-art" style="width:100%">{FARM_GROWN_SVG if grown else FARM_SVG}</div></div>')


def overlay(key, inner_html, on_click, args=(), kwargs=None):
    """카드 HTML + 보이지 않는 버튼(카드 전체 클릭)"""
    with st.container(key=f"ov_{key}"):
        html(inner_html)
        st.button("열기", key=f"btn_{key}", on_click=on_click, args=args, kwargs=kwargs or {})
