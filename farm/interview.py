"""모델 1: 은퇴농 인터뷰 AI
AI가 먼저 질문 → 은퇴농 답변 → 끝나면 대화 전체를 JSON(은퇴농 프로필 + 거래처 목록)으로 정리.
키가 없으면 정해진 질문 목록을 순서대로 묻는 데모 모드로 동작한다.
"""
import re
from . import ai

# 은퇴농 사전 질문 (스케치 '사전 질문' 11개 + 동의)
RETIREE_Q = [
    ("동의", "안녕하세요, 다시 FARM입니다. 말씀해 주시는 내용을 정리해서 젊은 농부와 연결하는 데 써도 괜찮으실까요?"),
    ("기본정보", "어디에 사시고, 연세는 어떻게 되세요?"),
    ("영농경력", "농사는 몇 년째 하셨고, 주로 뭘 키우세요?"),
    ("농사규모", "땅은 대략 몇 평(또는 몇 헥타르)이고, 1년에 몇 상자쯤 내세요?"),
    ("은퇴계획", "언제쯤 그만두실 생각이세요? 아예 그만두시나요, 줄이시나요?"),
    ("은퇴이유", "그만두시려는 이유가 있으세요? 자녀분 중에 이어받을 분은 있으세요?"),
    ("장부여부", "거래 적어두시는 장부나 공책이 있으세요?"),
]
BUYER_Q = [
    ("name", "거래하시는 곳 한 군데씩 여쭤볼게요. 가게 이름이랑, 어떤 가게(식당·마트·도매상 등)인지, 어디 있는지 알려주세요."),
    ("items", "그 집에는 어떤 작물을 내세요?"),
    ("volume", "한 번에 몇 상자쯤, 일주일에 몇 번 가져가요?"),
    ("grade", "크기나 상태는 어떤 걸로 받아요? (특·상·중·못난이)"),
    ("price", "한 상자(20kg)에 얼마 받으세요?"),
    ("days", "무슨 요일에, 몇 월부터 몇 월까지 납품하세요?"),
    ("delivery", "직접 갖다주세요, 가지러 와요?"),
    ("settlement", "돈은 언제 어떻게 받으세요?"),
    ("cert", "인증(GAP·친환경 같은 것)을 달라고 한 적 있어요?"),
    ("more", "다른 거래처도 있으세요? (있다/없다)"),
]
AFTER_Q = [
    ("넘길수있는것", "거래처 말고도 땅이나 창고, 기계를 넘기실 생각이 있으세요?"),
    ("인수인계의향", "젊은 농부를 데리고 거래처에 한 번 같이 가주실 수 있으세요?"),
    ("원하는후계자", "어떤 사람한테 넘기고 싶으세요?"),
    ("보상기대", "소개해서 거래가 되면 판매액 일부를 보상으로 드려요. 어떻게 받으시면 좋겠어요?"),
    ("연락방식", "연락은 문자가 편하세요, 전화가 편하세요?"),
]
END = "말씀 감사합니다. 인터뷰를 마칩니다. 정리된 내용을 확인해 주세요."

SYSTEM = f"""너는 은퇴를 앞둔 강원도 농업인을 인터뷰하는 '다시 FARM' 상담원이다.
규칙:
- 한 번에 질문 하나만, 존댓말로 쉽고 짧게 묻는다. 어르신이 편하게 말하도록 맞장구를 짧게 친다.
- 숫자(상자 수, 가격, 요일, 월)는 "이백 상자 맞으세요?"처럼 되물어 확인한다.
- 질문 순서: {", ".join(k for k, _ in RETIREE_Q)} → 거래처 이야기 → {", ".join(k for k, _ in AFTER_Q)}
- 거래처는 한 곳씩: 이름·종류·위치, 품목, 물량과 횟수, 품질 기준, 상자당 가격, 요일과 시기(월), 배송 방식, 정산, 인증 요구.
  한 곳이 끝나면 "다른 거래처도 있으세요?"라고 묻는다.
- 건강·소득·재산은 더 캐묻지 않는다. 동의하지 않으면 정중히 인터뷰를 끝낸다.
- 모든 질문이 끝나면 정확히 "{END}" 라고 말한다."""


# ───────────────────────── 대화 진행 ─────────────────────────
class Interview:
    def __init__(self):
        self.log = []            # [("assistant"|"user", text)]
        self.ai = ai.has_ai()
        self.done = False
        if self.ai:
            self.chat = ai.new_chat(SYSTEM)
            first = self.chat.send_message("인터뷰를 시작해 주세요.").text
        else:
            self.queue = list(RETIREE_Q) + list(BUYER_Q) + list(AFTER_Q)
            self.answers = []    # [(key, answer)]
            first = self.queue[0][1]
            self.current = self.queue.pop(0)
        self.log.append(("assistant", first))

    def reply(self, msg: str):
        self.log.append(("user", msg))
        if self.ai:
            out = self.chat.send_message(msg).text
        else:
            out = self._demo_next(msg)
        if END in out:
            self.done = True
        self.log.append(("assistant", out))
        return out

    def _demo_next(self, msg):
        key = self.current[0]
        self.answers.append((key, msg))
        if key == "동의" and any(w in msg for w in ("싫", "안 돼", "아니")):
            self.queue = []
        if key == "more" and any(w in msg for w in ("있", "네", "예")) and "없" not in msg:
            self.queue = list(BUYER_Q) + self.queue
        if not self.queue:
            return END
        self.current = self.queue.pop(0)
        return self.current[1]


# ───────────────────────── 구조화 (대화 → JSON) ─────────────────────────
SCHEMA_HINT = """{
 "retiree": {"동의": "", "기본정보": "", "영농경력": "", "농사규모": "", "은퇴계획": "", "은퇴이유": "",
             "장부여부": "", "넘길수있는것": "", "인수인계의향": "", "원하는후계자": "", "보상기대": "", "연락방식": ""},
 "buyers": [{"name": "", "type": "식당|반찬가게|로컬푸드 직매장|도매상|식자재업체|마트|학교급식|기타",
             "size": "소형|소형(직판)|중형|대형|대형(공공)", "location": "", "items": ["감자"],
             "min_grade": 1-4 (특4 상3 중2 무관1), "weekly_kg": 숫자(주당 kg, 1상자=20kg),
             "price_kg": 숫자(원/kg), "months": [9,10], "days": ["화"], "delivery": "", "settlement": "",
             "cert": "", "raw_text": "그 거래처에 대해 은퇴농이 한 말 요약"}]
}"""


def structure(log):
    transcript = "\n".join(f"{'AI' if w == 'assistant' else '농부'}: {m}" for w, m in log)
    return ai.json_out(f"아래 인터뷰를 이 JSON 형식으로만 정리해. 모르는 값은 빈 문자열/0.\n{SCHEMA_HINT}\n\n{transcript}")


def _num(s, default=0):
    m = re.findall(r"\d[\d,]*", s or "")
    return int(m[0].replace(",", "")) if m else default


def _demo_structure_buyer(ans):
    name_part = ans.get("name", "")
    name = re.split(r"[,\s]", name_part.strip())[0] if name_part else "이름 미상"
    vol = ans.get("volume", "")
    boxes = _num(vol, 0)
    times = 2 if ("두 번" in vol or "2번" in vol or "주 2" in vol) else 1
    price_box = _num(ans.get("price", ""), 0)
    g = 1
    for k, v in (("특", 4), ("상", 3), ("중", 2)):
        if k in ans.get("grade", ""):
            g = v
            break
    _d = re.sub(r"\d{1,2}\s*월|요일", " ", ans.get("days", ""))   # '9월', '요일' 글자 제거 후 요일만 추출
    days = [d for d in "월화수목금토일" if d in _d]
    months = [int(x) for x in re.findall(r"(\d{1,2})\s*월", ans.get("days", ""))]
    if len(months) == 2 and months[0] < months[1]:
        months = list(range(months[0], months[1] + 1))
    t = "식당" if "식당" in name_part else "마트" if "마트" in name_part else "도매상" if "청과" in name_part or "도매" in name_part else "기타"
    size = {"식당": "소형", "마트": "중형", "도매상": "중형"}.get(t, "소형")
    return {"name": name, "type": t, "size": size, "location": name_part,
            "items": [x.strip() for x in re.split(r"[,·\s]", ans.get("items", "감자")) if x.strip()] or ["감자"],
            "min_grade": g, "weekly_kg": boxes * 20 * times, "price_kg": round(price_box / 20) if price_box > 1000 else price_box,
            "months": months or [7, 8, 9, 10], "days": days or ["화"], "delivery": ans.get("delivery", ""),
            "settlement": ans.get("settlement", ""), "cert": "" if "없" in ans.get("cert", "없") else ans.get("cert", ""),
            "raw_text": " / ".join(f"{k}: {v}" for k, v in ans.items() if k != "more")}


def structure_demo(iv: "Interview"):
    retiree, buyers, cur = {}, [], {}
    for key, ans in iv.answers:
        if key in dict(BUYER_Q):
            if key == "more":
                buyers.append(_demo_structure_buyer(cur))
                cur = {}
            else:
                cur[key] = ans
        else:
            retiree[key] = ans
    if cur:
        buyers.append(_demo_structure_buyer(cur))
    return {"retiree": retiree, "buyers": buyers}


def run_structure(iv: "Interview"):
    return structure(iv.log) if iv.ai else structure_demo(iv)


# ───────────────────────── 장부 사진 → 거래 기록 (OCR) ─────────────────────────
LEDGER_PROMPT = """이 사진은 농가의 손글씨 거래장이다. 각 줄을 JSON 배열로 옮겨라.
형식: [{"date":"YYYY-MM-DD","buyer":"","item":"","grade":"","qty":숫자,"unit_price":숫자,"amount":숫자,"payment":"","memo":""}]
규칙: 같은 날짜 표시(〃)는 위 줄 날짜, "560만"은 5600000, "보름뒤"는 그대로 payment에. 연도는 표 위쪽 표기를 따른다."""


def read_ledger(image_bytes: bytes, mime="image/jpeg"):
    if not ai.has_ai():
        return None
    return ai.json_out([ai.image_part(image_bytes, mime), LEDGER_PROMPT])
