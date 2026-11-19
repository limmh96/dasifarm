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

피그마와 코드는 자동 동기화되지 않습니다. 아래처럼 **이름을 맞춰 두고, 피그마에서 바뀐 값을 해당 파일에 옮겨 적는 방식**입니다.

| 피그마 | 코드 위치 |
|---|---|
| 프레임 `모바일 01 · 홈` | `app.py` → `PAGES[0]` |
| (인터뷰 화면) | `PAGES[1]` `은퇴농 · AI 인터뷰` |
| 프레임 `모바일 06 · 판로 찾기` | `PAGES[2]` |
| 프레임 `모바일 07 · 구매처 상세` | `PAGES[3]` |
| 프레임 `모바일 08 · 시험 납품 신청` / `시험 납품 신청 완료` | `PAGES[4]` (신청 후 완료 메시지) |
| (구매처 화면) | `PAGES[5]` `구매처 · 후속 공급자 찾기` |
| `00. 다시 FARM 공통 디자인`의 색 변수 | `design/tokens.json`의 `color/*` + `.streamlit/config.toml` |
| 컴포넌트 Card / Chip / ScoreBar / MatchCard | `farm/ui.py`의 `card()` `chip()` `score_bar()` `match_card()` |

피그마 쪽 프레임·컴포넌트 이름이 다르면 피그마 이름에 맞춰 `PAGES` 목록과 함수 이름을 고치면 됩니다.

## 5. 매칭률 계산

```
매칭률 = Σ(항목 점수 0~1 × 가중치) ÷ 가중치 합 × 100
```
- 필수조건(품목 불일치, 요구 인증 없음)은 점수 전에 제외
- 가중치 기본값(예시): 물량 25 · 품질 15 · 가격 15 · 주기 15 · 거리 15 · 인증 5 · 유사도 10
- `데이터 · 매칭 기준` 화면에서 슬라이더로 바로 바꿔볼 수 있음
- AI(Gemini)는 점수를 만들지 않고 **설명 문장만** 씀

## 6. 공공데이터 (자동 채움 → 확인 → 없으면 직접 입력)
- 지금은 `buyers.csv`에서 `source = 공공데이터`인 행(가상 학교급식센터)으로 시연
- GAP 인증 조회: `data/public_gap.csv`를 넣으면 `public_lookup("cert", 번호)`가 찾음. 없으면 직접 입력 화면으로 넘어감
- 실제 API로 바꿀 곳: `farm/data.py`의 `public_lookup()` 한 함수
