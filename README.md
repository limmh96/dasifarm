# 다시 FARM 프로토타입 (Streamlit)

은퇴 농업인의 거래처(판로)를 청년 농업인에게 잇는 AI 매칭 시연용 앱.
**모든 이름·수치는 가상 데이터**입니다.

## 1. 실행 (내 노트북)

```bash
pip install -r requirements.txt
streamlit run app.py
```

키 없이도 **데모 모드**로 전 화면이 동작합니다 (정해진 질문 순서, 템플릿 설명, 임시 벡터).

### API 키 넣기 (선택)
`.streamlit/secrets.toml` 파일을 만들고 아래처럼 적습니다. **이 파일은 GitHub에 올리지 않습니다** (`.gitignore`에 포함됨).

```toml
GEMINI_API_KEY = "여기에_키"
KAKAO_JS_KEY = "여기에_카카오_자바스크립트_키"
# GEMINI_MODEL = "gemini-2.5-flash"   # AI Studio에서 현재 쓸 수 있는 Flash 모델명으로 바꿔도 됨
```

## 2. 배포 (Streamlit Cloud)
1. 이 폴더를 GitHub 저장소에 올림 (secrets.toml 제외 확인)
2. share.streamlit.io → New app → 저장소·`app.py` 선택
3. App settings → **Secrets**에 위 toml 내용 붙여넣기
4. 카카오 개발자 콘솔 → 앱 → 플랫폼 → Web 도메인에 `https://○○.streamlit.app` 추가

## 3. 구조

| 파일 | 역할 |
|---|---|
| `app.py` | 화면 (페이지 이름 = 피그마 프레임 이름) |
| `farm/interview.py` | **모델 1** 은퇴농 대화형 인터뷰 AI + 대화→표 정리 + 장부 사진 읽기 |
| `farm/matching.py` | **모델 2** 적합도 분석 AI (필수조건 → 6기준 점수 → 유사도 → 가중합 → AI 설명) |
| `farm/data.py` | CSV 불러오기, SQLite 저장(`farm.db` 자동 생성), 공공데이터 조회 자리 |
| `farm/ai.py` | Gemini 연결 (키 없으면 데모 모드) |
| `farm/ui.py` | 피그마 컴포넌트와 같은 이름의 화면 부품 |
| `design/tokens.json` | 피그마 Variables와 같은 이름의 색·글꼴·모서리 값 |
| `data/*.csv` | 가상 구매처 7곳, 청년농 5명, 장부 정답 데이터 |

데이터 흐름: 인터뷰 저장 → `buyers_extra` 표에 구매처 추가 → `판로 찾기`에서 바로 매칭 대상이 됨.

## 4. 피그마 연동 표

화면은 **모바일 390px** 기준이고 피그마 프레임 이름을 그대로 페이지 이름으로 씁니다. 자동 동기화가 아니라 **이름을 맞춰 두고 값을 옮겨 적는 방식**입니다.

| 피그마 | 코드 위치 |
|---|---|
| `모바일 00 · 고객 선택` (어떤 고객이세요?) | `P_START` — 앱 첫 화면 |
| 판매처 등록 (공공데이터 불러오는 중 → 확인 → 없는 정보 입력) | `P_ONB_F` + `farm/onboard.py` |
| 구매처 등록 (같은 3단계) | `P_ONB_B` + `farm/onboard.py` |
| `모바일 01 · 홈` | `app.py` `P_HOME` |
| (판로 물려주기 = AI 인터뷰) | `P_HANDOVER` `모바일 · 판로 물려주기` |
| `모바일 06 · 판로 찾기` | `P_FIND` |
| `모바일 07 · 구매처 상세` | `P_DETAIL` |
| `모바일 08 · 시험 납품 신청` | `P_TRIAL` |
| `모바일 · 시험 납품 신청 완료` | `P_DONE` |
| 메뉴 `납품 조건 보기` (구매처 쪽) | `P_BUYER` |
| 메뉴 `나의 다시팜` (가중치·기록) | `P_MY` |
| `00. 다시 FARM 공통 디자인` 색 변수 | `design/tokens.json` + `.streamlit/config.toml` |
| 헤더(다시, FARM + 메뉴) / 경로표시 / 큰 제목 | `farm/ui.py` `header()` `crumb()` `hero()` |
| 연두 카드 / 흰 카드 / 노랑 카드 | `st.container(key="gcard_…" / "wcard_…" / "ycard_…")` |
| Chip / ScoreBar / 판로 카드 | `chip()` `score_bar()` `match_card()` |

## 5. 매칭률 계산

```
매칭률 = Σ(항목 점수 0~1 × 가중치) ÷ 가중치 합 × 100
```
- 필수조건(품목 불일치, 요구 인증 없음)은 점수 전에 제외
- 가중치 기본값(예시): 물량 25 · 품질 15 · 가격 15 · 주기 15 · 거리 15 · 인증 5 · 유사도 10
- `데이터 · 매칭 기준` 화면에서 슬라이더로 바로 바꿔볼 수 있음
- AI(Gemini)는 점수를 만들지 않고 **설명 문장만** 씀

## 6. 공공데이터 (자동 채움 → 확인 → 없으면 직접 입력)
- 시연용 가상 공공데이터: `data/public_gap.csv`(GAP 인증 농가), `data/public_buyers.csv`(공공급식)
  - 판매처: `다시농장` 또는 `GAP-2025-0731` 입력 → 이름·지역·품목·인증 자동 채움 / `없는농장` → 전부 직접 입력
  - 구매처: `강릉학교급식` 입력 → 이름·지역·품목·인증·물량·요일 자동 채움
- 실제 API로 바꿀 곳: `farm/data.py`의 `public_farmer()` `public_buyer()`
- 은퇴 농업인: 질문 듣기(브라우저 음성) → 녹음 → Gemini 받아쓰기(`ai.transcribe`) → 대화형 인터뷰. 키가 없으면 글 입력으로 진행
- 지금은 `buyers.csv`에서 `source = 공공데이터`인 행(가상 학교급식센터)으로 시연
- GAP 인증 조회: `data/public_gap.csv`를 넣으면 `public_lookup("cert", 번호)`가 찾음. 없으면 직접 입력 화면으로 넘어감
- 실제 API로 바꿀 곳: `farm/data.py`의 `public_lookup()` 한 함수
