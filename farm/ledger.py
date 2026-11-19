"""은퇴 농업인 판로 받기 — 장부 사진 촬영 버전
① 사진 → AI(Gemini)가 거래 기록 표로 읽기
② 사람이 표 확인·수정
③ 거래처별로 묶어서 매칭 조건 계산 (코드): 품목·주당 물량·kg당 단가·출하 월·납품 요일·등급·정산
④ 장부에 없는 정보만 직접 입력: 위치·배송 방식·필요 인증
"""
import re
import datetime as dt
from collections import Counter
import pandas as pd
from . import ai

COLS = ["date", "buyer", "buyer_type", "item", "grade", "qty", "unit", "unit_price", "amount", "payment", "memo"]
LABEL = {"date": "날짜", "buyer": "거래처", "buyer_type": "거래처 유형", "item": "품목", "grade": "규격·등급",
         "qty": "수량", "unit": "단위", "unit_price": "단가(원)", "amount": "금액(원)", "payment": "입금", "memo": "비고"}

PROMPT = """이 사진은 농가의 손글씨 거래 장부다. 한 줄씩 JSON 배열로 옮겨라.
형식: [{"date":"YYYY-MM-DD","buyer":"거래처 이름","buyer_type":"식당|반찬가게|로컬푸드 직매장|도매상|식자재업체|마트|학교급식|모름",
"item":"품목","grade":"규격·등급(특/상/중/못난이 또는 1kg팩 등 적힌 그대로)","qty":숫자,"unit":"상자(20kg)|팩|kg 등",
"unit_price":숫자,"amount":숫자,"payment":"입금 방식·상태","memo":"비고"}]
규칙: 같은 날짜 표시(〃)는 윗줄 날짜, "560만"은 5600000, 연도는 장부 위쪽 표기를 따른다. 읽을 수 없는 칸은 빈 문자열 또는 0."""


def read(image_bytes, mime="image/jpeg"):
    """AI로 장부 읽기. 키가 없으면 None (화면에서 예시 정답 데이터로 대신)"""
    if not ai.has_ai():
        return None
    rows = ai.json_out([ai.image_part(image_bytes, mime), PROMPT])
    return pd.DataFrame(rows).reindex(columns=COLS)


def sample():
    """예시 장부 사진(data/sample_ledger.jpg)의 정답 표"""
    d = pd.read_csv("data/ledger_truth.csv")
    d.columns = ["date", "buyer", "buyer_type", "item", "grade", "qty", "unit", "unit_price", "amount", "payment", "memo"]
    return d.reindex(columns=COLS).fillna("")


# ───────── ③ 거래처별 매칭 조건 계산 (AI 아님) ─────────
DAYS = "월화수목금토일"
GRADE_NUM = [("특", 4), ("상", 3), ("중", 2), ("하", 1), ("못난이", 1)]


def _kg(unit, grade):
    m = re.search(r"(\d+(?:\.\d+)?)\s*kg", f"{unit} {grade}")
    if m:
        return float(m.group(1))
    return 1.0 if "kg" in str(unit) else 20.0          # 단위 표기가 없으면 20kg 상자로 봄


def _grade(g):
    for k, v in GRADE_NUM:
        if k in str(g):
            return v
    return 1


def summarize(rows: pd.DataFrame):
    """장부 줄 → 거래처 1곳당 1줄 (매칭 AI가 쓰는 칸 이름으로)"""
    d = rows.copy()
    d["date"] = pd.to_datetime(d["date"], errors="coerce")
    d = d.dropna(subset=["date"])
    d["qty"] = pd.to_numeric(d["qty"], errors="coerce").fillna(0)
    d["unit_price"] = pd.to_numeric(d["unit_price"], errors="coerce").fillna(0)
    d["kg"] = [q * _kg(u, g) for q, u, g in zip(d["qty"], d["unit"], d["grade"])]
    d["price_kg"] = [p / _kg(u, g) if p else 0 for p, u, g in zip(d["unit_price"], d["unit"], d["grade"])]
    out = []
    for name, g in d.groupby("buyer"):
        weeks = max(1, ((g["date"].max() - g["date"].min()).days // 7) + 1)
        day_cnt = Counter(DAYS[x.weekday()] for x in g["date"])
        days = [k for k, c in day_cnt.most_common() if c >= max(2, len(g) * 0.25)] or [day_cnt.most_common(1)[0][0]]
        pay = Counter(str(p) for p in g["payment"] if str(p).strip()).most_common(1)
        types = Counter(str(t) for t in g["buyer_type"] if str(t).strip() and str(t) != "모름").most_common(1)
        out.append({
            "name": name, "type": types[0][0] if types else "",
            "items": sorted(set(g["item"].astype(str))),
            "거래 횟수": len(g), "기간": f"{g['date'].min():%Y.%m.%d}~{g['date'].max():%m.%d}",
            "weekly_kg": round(g["kg"].sum() / weeks),
            "price_kg": round((g["price_kg"] * g["kg"]).sum() / max(g["kg"].sum(), 1)),
            "months": sorted(set(int(x.month) for x in g["date"])),
            "days": [x for x in DAYS if x in days],
            "min_grade": min(_grade(x) for x in g["grade"]),
            "settlement": pay[0][0] if pay else "",
        })
    return out


GRADE_NAME = {4: "특", 3: "상", 2: "중", 1: "무관"}
