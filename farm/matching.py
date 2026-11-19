"""모델 2: 적합도 분석 AI
① 필수조건 거르기 → ② 6가지 기준 점수(코드) → ③ 벡터 유사도(RAG) → ④ 가중합 → ⑤ Gemini 설명
같은 점수표를 두 방향으로 조회: 청년농 → 구매처 추천 / 구매처 → 청년농 추천
"""
import math
import hashlib
import numpy as np
from . import ai
from .data import load_buyers, load_farmers, GRADE_NAME

# 가중치 예시값 (합 100). 화면에서 바꿀 수 있음. 실제 값은 인터뷰로 확정.
WEIGHTS = {"물량 안정성": 25, "품질·규격": 15, "가격": 15, "납품 주기": 15,
           "물류·거리": 15, "인증·신뢰": 5, "유사도(RAG)": 10}
MAX_KM = 100


def dist_km(a, b):
    R = 6371
    la1, lo1, la2, lo2 = map(math.radians, [a["lat"], a["lng"], b["lat"], b["lng"]])
    h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 2 * R * math.asin(math.sqrt(h))


# ───────── ③ 벡터 유사도 (RAG 검색) ─────────
def _fake_vec(text, dim=256):
    """키 없을 때 임시 벡터: 두 글자씩 해시. 겹치는 표현이 많을수록 가까움"""
    v = np.zeros(dim)
    t = str(text).replace(" ", "")
    for i in range(len(t) - 1):
        v[int(hashlib.md5(t[i:i + 2].encode()).hexdigest(), 16) % dim] += 1
    n = np.linalg.norm(v)
    return v / n if n else v


_cache = {}


def vectors(texts):
    out = []
    need = [t for t in texts if t not in _cache]
    if need:
        if ai.has_ai():
            try:
                for t, v in zip(need, ai.embed(need)):
                    v = np.array(v); _cache[t] = v / (np.linalg.norm(v) or 1)
            except Exception:
                for t in need:
                    _cache[t] = _fake_vec(t)
        else:
            for t in need:
                _cache[t] = _fake_vec(t)
    for t in texts:
        out.append(_cache[t])
    return out


def buyer_text(b):
    return (f"{b['name']} {b['type']} {b['location']} 품목 {','.join(b['items'])} 최소등급 {GRADE_NAME.get(int(b['min_grade']), '')} "
            f"주 {int(b['weekly_kg'])}kg {','.join(map(str, b['months']))}월 {','.join(b['days'])}요일 {b['delivery']} {b['settlement']} {b['raw_text']}")


def farmer_text(y):
    return (f"{y['name']} {y['region']} 품목 {','.join(y['items'])} {y.get('variety', '')} 등급 {GRADE_NAME.get(int(y['grade']), '')} "
            f"주 {int(y['weekly_kg'])}kg {','.join(map(str, y['months']))}월 {','.join(y['days'])}요일 {'트럭 있음' if y['truck'] == 'Y' else '트럭 없음'} {y.get('intro', '')}")


def similarity(y, b):
    vy, vb = vectors([farmer_text(y), buyer_text(b)])
    return float(max(0.0, min(1.0, np.dot(vy, vb))))


# ───────── ① 필수조건 ─────────
def hard_filter(y, b):
    if not set(y["items"]) & set(b["items"]):
        return "품목 불일치"
    if b["cert"] and b["cert"] not in y["certs"]:
        return f"필수 인증({b['cert']}) 없음"
    return None


# ───────── ② 6가지 기준 점수 ─────────
def criteria_scores(y, b, sim):
    km = dist_km(y, b)
    months_b = b["months"] or list(range(1, 13))
    month_ratio = len(set(y["months"]) & set(months_b)) / len(months_b)
    day_ok = (not b["days"]) or bool(set(y["days"]) & set(b["days"]))
    dist = max(0.0, 1 - km / MAX_KM)
    if "직접" in str(b["delivery"]) and y["truck"] != "Y":
        dist *= 0.5                                    # 직접 납품 요구인데 트럭 없음
    s = {
        "물량 안정성": min(y["weekly_kg"] / b["weekly_kg"], 1.0) if b["weekly_kg"] else 1.0,
        "품질·규격": 1.0 if int(y["grade"]) >= int(b["min_grade"]) else 0.4,
        "가격": 1.0 if b["price_kg"] >= y["wish_price_kg"] else b["price_kg"] / y["wish_price_kg"],
        "납품 주기": month_ratio * (1.0 if day_ok else 0.6),
        "물류·거리": dist,
        "인증·신뢰": 1.0,
        "유사도(RAG)": sim,
    }
    detail = {
        "물량 안정성": f"요구 주 {int(b['weekly_kg']):,}kg / 공급 주 {int(y['weekly_kg']):,}kg",
        "품질·규격": f"요구 '{GRADE_NAME.get(int(b['min_grade']))}' 이상 / 공급 '{GRADE_NAME.get(int(y['grade']))}'",
        "가격": f"단가 {int(b['price_kg']):,}원/kg / 희망 {int(y['wish_price_kg']):,}원/kg",
        "납품 주기": f"요구 {_months(months_b)}·{'/'.join(b['days']) or '무관'} / 공급 {_months(y['months'])}·{'/'.join(y['days'])}",
        "물류·거리": f"{km:.0f}km · 트럭 {'있음' if y['truck'] == 'Y' else '없음'} · {b['delivery']}",
        "인증·신뢰": f"요구 {b['cert'] or '없음'} / 보유 {', '.join(y['certs']) or '없음'}",
        "유사도(RAG)": "구술 원문 ↔ 청년농 프로필 벡터 유사도",
    }
    return s, detail, km


def _months(ms):
    return f"{min(ms)}~{max(ms)}월" if ms else "연중"


GAP_TEXT = {"물량 안정성": "물량 부족", "품질·규격": "등급 기준 미달", "가격": "희망단가보다 낮은 단가",
            "납품 주기": "납품 시기·요일 불일치", "물류·거리": "거리·배송 부담"}


def evaluate(y, b, weights=None):
    w = weights or WEIGHTS
    reason = hard_filter(y, b)
    if reason:
        return {"excluded": reason}
    s, detail, km = criteria_scores(y, b, similarity(y, b))
    total = sum(s[k] * w[k] for k in w) / sum(w.values()) * 100
    weak = [k for k, v in sorted(s.items(), key=lambda x: x[1]) if v < 0.7 and k in GAP_TEXT][:2]
    return {
        "농가": b.get("from_farmer", "—"), "거래처": b["name"], "청년농": y["name"],
        "구매처유형": f"{b['size']} · {b['type']}", "출처": b.get("source", ""),
        "월거래액": int(b["weekly_kg"] * b["price_kg"] * 4.3),
        "매칭률": round(total), "항목점수": s, "근거": detail, "거리km": round(km),
        "부족한조건": [f"{GAP_TEXT[k]} ({detail[k]})" for k in weak],
        "위도": b["lat"], "경도": b["lng"], "청년농위도": y["lat"], "청년농경도": y["lng"],
    }


# ───────── ⑤ 설명 (AI는 설명만, 숫자는 위 코드) ─────────
def explain(r):
    if ai.has_ai():
        try:
            return ai.text(
                f"농산물 판로 매칭 결과를 청년농에게 설명해줘. 숫자는 바꾸지 말 것.\n"
                f"청년농 {r['청년농']} ↔ 구매처 {r['거래처']}({r['구매처유형']}), 매칭률 {r['매칭률']}%\n"
                f"항목별 근거: {r['근거']}\n부족한 조건: {r['부족한조건']}\n"
                f"형식: '추천 이유' 2줄, '보완 방법' 1줄, '구매처에 물어볼 질문' 2개. 짧게.")
        except Exception as e:
            return _template(r)
    return _template(r)


def _template(r):
    strong = [k for k, v in sorted(r["항목점수"].items(), key=lambda x: -x[1])[:2]]
    lines = [f"추천 이유: {', '.join(strong)} 기준을 잘 충족합니다 ({r['근거'][strong[0]]})."]
    if r["부족한조건"]:
        lines.append("부족한 조건: " + " / ".join(r["부족한조건"]))
    lines.append("구매처에 물어볼 질문: 시험 납품 물량은 얼마인가요? 정산 주기를 조정할 수 있나요?")
    return "\n".join(lines) + "\n\n(데모 모드: Gemini 키를 넣으면 AI가 문장으로 설명합니다)"


# ───────── 양방향 추천 ─────────
def recommend_for_farmer(farmer_name=None, farmer=None, top=3, weights=None):
    y = farmer or load_farmers().set_index("name").loc[farmer_name].to_dict() | {"name": farmer_name}
    res, out = [], []
    for _, b in load_buyers().iterrows():
        r = evaluate(y, b.to_dict(), weights)
        (out if "excluded" in r else res).append(r if "excluded" not in r else {"거래처": b["name"], "제외 이유": r["excluded"]})
    res.sort(key=lambda r: -r["매칭률"])
    return res[:top], out


def recommend_for_buyer(buyer_name, top=3, weights=None):
    b = load_buyers().set_index("name").loc[buyer_name].to_dict() | {"name": buyer_name}
    res = []
    for _, y in load_farmers().iterrows():
        r = evaluate(y.to_dict(), b, weights)
        if "excluded" not in r:
            res.append(r)
    res.sort(key=lambda r: -r["매칭률"])
    return res[:top]
