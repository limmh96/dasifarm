"""은퇴 농업인 음성 인터뷰 AI
AI가 질문(화면 + 소리로 읽기) → 은퇴농이 말로 답함 → Gemini 받아쓰기 → AI가 다음 질문 → … → 대화를 거래처 조건 표로 정리
키가 없으면: 정해진 질문 순서 + '예시 답변'으로 같은 흐름 시연
"""
from . import ai

END = "말씀 감사합니다. 들려주신 이야기를 정리해 볼게요."

SYSTEM = f"""너는 '다시팜' 상담원이다. 은퇴를 앞둔 강원도 농업인에게 그동안의 거래처를 묻는다.
규칙:
- 존댓말, 한 번에 질문 하나, 짧고 쉽게. 대답에 짧게 맞장구친 뒤 다음 질문을 한다.
- 먼저 어디서 어떤 농사를 몇 년 지었는지 묻는다.
- 그다음 거래처를 한 곳씩 묻는다: 이름·종류·위치, 품목, 납품 시기(월)와 요일, 한 번에 몇 상자(1상자=20kg), 상자당 가격, 품질 기준, 배송 방식, 정산 방식.
- 숫자(상자 수, 가격)는 "이백 상자 맞으시죠?"처럼 한 번 되물어 확인한다. 빠진 항목이 있으면 그것만 다시 묻는다.
- 한 곳이 끝나면 "다른 거래처도 있으세요?"라고 묻는다. 없다고 하면 정확히 "{END}"라고만 말한다.
- 건강·소득·재산은 캐묻지 않는다."""

DEMO = [
    ("안녕하세요, 선배님. 다시팜이에요. 어디서 어떤 농사를 몇 년 지으셨어요?",
     "평창 방림에서 감자 농사를 사십 년 지었어요."),
    ("사십 년이요, 정말 오래 지으셨네요. 감자는 주로 어디에 파셨어요? 가장 오래 거래한 곳부터 알려 주세요.",
     "강릉에 가나청과라고 도매상이 있는데 거기에 제일 많이 냈지."),
    ("가나청과에는 언제, 얼마나 자주, 몇 상자씩 내셨어요? 품질 기준도 있었나요?",
     "구월부터 십이월까지 매주 화요일 아침에 감자 이백 상자씩 납품했어요. 거기는 크기 기준이 엄격해서 고르게 골라 담아야 돼요."),
    ("이백 상자 맞으시죠? 한 상자에 얼마 받으셨고, 배송과 정산은 어떻게 하셨어요?",
     "맞아요. 한 상자에 이만 팔천 원. 내 트럭으로 직접 갖다주고 돈은 월말에 정산했지."),
    ("다른 거래처도 있으세요?",
     "진부에 솔밭식당이라고 있는데 못난이 감자도 받아 줘요. 월요일하고 목요일에 여섯 상자씩, 한 상자에 만 사천 원."),
    ("솔밭식당은 배송하고 정산은 어떻게 하셨어요?",
     "내가 직접 배달하고, 외상으로 달아 놨다가 한 달에 한 번 받았어요."),
    ("다른 거래처도 있으세요?", "아니요, 그 정도예요."),
]

DEMO_RESULT = {
    "farmer": {"name": "김순자", "region": "평창군 방림면", "career": "감자 40년"},
    "buyers": [
        {"name": "가나청과", "type": "도매상", "location": "강릉시", "items": ["감자"],
         "spec": "20kg 상자 · 크기 기준 엄격(크기 고르게 선별)", "min_grade": 3,
         "weekly_kg": 4000, "cycle": "매주 화요일 아침 · 9~12월", "months": [9, 10, 11, 12], "days": ["화"],
         "price_kg": 1400, "delivery": "직접 트럭 납품", "settlement": "월말 정산", "note": "가장 오래 거래"},
        {"name": "솔밭식당", "type": "식당", "location": "평창군 진부면", "items": ["감자"],
         "spec": "20kg 상자 · 못난이 감자도 받음", "min_grade": 1,
         "weekly_kg": 240, "cycle": "매주 월·목요일", "months": [7, 8, 9, 10, 11, 12], "days": ["월", "목"],
         "price_kg": 700, "delivery": "직접 배달", "settlement": "외상 후 월 1회 정산", "note": ""},
    ],
}

SCHEMA = """{"farmer":{"name":"","region":"시군구 읍면","career":""},
"buyers":[{"name":"","type":"식당|반찬가게|로컬푸드 직매장|도매상|식자재업체|마트|학교급식|기타","location":"시군구(배송거리 계산용)",
"items":["감자"],"spec":"규격: 포장 단위·크기·등급 기준을 말한 그대로 짧게","min_grade":1-4(특4 상3 중2 무관·못난이1),
"weekly_kg":숫자(납품량: 주당 kg, 1상자=20kg, 주2회면 2배),"cycle":"주기: 요일·시간대·시기를 말한 그대로","months":[9,10],"days":["화"],
"price_kg":숫자(원/kg = 상자당 가격÷20),"delivery":"배송 방식","settlement":"정산주기","note":"그 밖에 한 말"}]}
예: "매주 화요일 아침 감자 200상자 납품, 크기 기준 엄격, 월말 정산" → items ["감자"], spec "크기 기준 엄격", weekly_kg 4000, cycle "매주 화요일 아침", days ["화"], settlement "월말 정산".
"""


class Interview:
    def __init__(self):
        self.ai = ai.has_ai()
        self.log = []                 # [("ai"|"me", 문장)]
        self.turn = 0
        self.done = False
        self.fallback = ""             # AI 호출이 실패해 데모로 바뀐 이유
        if self.ai:
            try:
                self.chat = ai.new_chat(SYSTEM)
                self.log.append(("ai", self.chat.send_message("인터뷰를 시작해 주세요.").text.strip()))
                return
            except Exception as e:     # 키·모델·인터넷 문제 → 자동으로 데모 모드로 이어감
                self.ai, self.fallback = False, str(e)[:120]
        self.log.append(("ai", DEMO[0][0]))

    @property
    def question(self):
        return self.log[-1][1] if self.log and self.log[-1][0] == "ai" else ""

    def demo_answer(self):
        return DEMO[min(self.turn, len(DEMO) - 1)][1]

    def answer(self, text):
        self.log.append(("me", text))
        self.turn += 1
        nxt = None
        if self.ai:
            try:
                nxt = self.chat.send_message(text).text.strip()
            except Exception as e:
                self.ai, self.fallback = False, str(e)[:120]
        if nxt is None:
            nxt = DEMO[self.turn][0] if self.turn < len(DEMO) else END
        if END[:10] in nxt:
            nxt, self.done = END, True
        self.log.append(("ai", nxt))

    def transcript(self):
        return "\n".join(f"{'AI' if w == 'ai' else '선배님'}: {t}" for w, t in self.log)

    def structure(self):
        if not self.ai:
            return DEMO_RESULT
        try:
            return ai.json_out(f"아래 인터뷰를 이 JSON 형식으로만 정리해. 모르는 값은 빈 문자열/0/빈 배열.\n{SCHEMA}\n\n{self.transcript()}")
        except Exception as e:
            self.fallback = str(e)[:120]
            return DEMO_RESULT


def transcribe(audio, mime):
    return ai.transcribe(audio, mime or "audio/wav")
