"""피그마 컴포넌트와 1:1로 대응하는 화면 부품.
피그마 컴포넌트 이름 → 함수 이름:  Card → card(), Chip → chip(), ScoreBar → score_bar(),
MatchCard → match_card(), SectionTitle → section().  색·모서리·글꼴은 design/tokens.json에서 읽는다.
"""
import os
import json
import streamlit as st

_T = json.load(open(os.path.join(os.path.dirname(os.path.dirname(__file__)), "design", "tokens.json"), encoding="utf-8"))


def tok(name):
    return _T[name]


def inject_css():
    st.markdown(f"""
    <style>
      html, body, [class*="css"] {{ font-family: {tok('font/family')}; }}
      .df-card {{ background:{tok('color/surface')}; border:1px solid {tok('color/border')};
                 border-radius:{tok('radius/card')}; padding:{tok('space/card-padding')}; margin-bottom:12px; }}
      .df-title {{ font-size:{tok('font/size-title')}; font-weight:700; color:{tok('color/text')}; margin:0 0 4px 0; }}
      .df-sub {{ color:{tok('color/text-sub')}; font-size:14px; margin:0 0 14px 0; }}
      .df-chip {{ display:inline-block; padding:3px 12px; margin:0 6px 6px 0; border-radius:{tok('radius/chip')};
                 font-size:13px; border:1px solid currentColor; }}
      .df-bar {{ height:8px; border-radius:8px; background:{tok('color/border')}; overflow:hidden; }}
      .df-bar > div {{ height:8px; background:{tok('color/primary')}; }}
      .df-score {{ font-size:28px; font-weight:800; color:{tok('color/accent')}; }}
      .df-label {{ font-size:13px; color:{tok('color/text-sub')}; }}
    </style>""", unsafe_allow_html=True)


def section(title, sub=""):
    st.markdown(f"<p class='df-title'>{title}</p>" + (f"<p class='df-sub'>{sub}</p>" if sub else ""), unsafe_allow_html=True)


def chip(text, color_token="color/primary"):
    return f"<span class='df-chip' style='color:{tok(color_token)}'>{text}</span>"


def card(html):
    st.markdown(f"<div class='df-card'>{html}</div>", unsafe_allow_html=True)


def score_bar(label, value, note=""):
    pct = max(0, min(100, round(value * 100)))
    return (f"<div style='margin:6px 0'><div style='display:flex;justify-content:space-between'>"
            f"<span class='df-label'>{label}</span><span class='df-label'>{pct}점 {note}</span></div>"
            f"<div class='df-bar'><div style='width:{pct}%'></div></div></div>")


def match_card(r, who="buyer"):
    """MatchCard: 판로 찾기 목록의 한 칸"""
    name = r["거래처"] if who == "buyer" else r["청년농"]
    sub = f"{r['구매처유형']} · {r['거리km']}km · 월 거래 규모 약 {r['월거래액']//10000:,}만 원" if who == "buyer" \
        else f"{r['거리km']}km"
    gaps = "".join(chip("부족: " + g.split(" (")[0], "color/accent") for g in r["부족한조건"]) or chip("부족한 조건 없음")
    src = chip(r["출처"], "color/buyer") if r.get("출처") else ""
    card(f"<div style='display:flex;justify-content:space-between;align-items:center'>"
         f"<div><b style='font-size:18px'>{name}</b><br><span class='df-label'>{sub}</span></div>"
         f"<div class='df-score'>{r['매칭률']}%</div></div><div style='margin-top:10px'>{src}{gaps}</div>")
