"""Gemini 호출을 한 곳에 모은 모듈.
키가 없으면 has_ai()가 False → 각 기능이 '데모 모드'(규칙 기반)로 동작한다.
"""
import os
import json

DEFAULT_MODEL = "gemini-3.5-flash"     # Secrets의 GEMINI_MODEL로 바꿀 수 있음
EMBED_MODEL = "gemini-embedding-001"

_client = None


def _key():
    key = os.environ.get("GEMINI_API_KEY")
    if key:
        return key
    try:
        import streamlit as st
        return st.secrets.get("GEMINI_API_KEY")
    except Exception:
        return None


def demo_forced():
    """주소 끝에 ?demo=1 을 붙이면 키가 있어도 데모 모드 (발표 백업용)"""
    try:
        import streamlit as st
        return st.query_params.get("demo") in ("1", "true", "yes")
    except Exception:
        return False


def has_ai():
    return bool(_key()) and not demo_forced()


def _model():
    return os.environ.get("GEMINI_MODEL") or DEFAULT_MODEL


def client():
    global _client
    if _client is None:
        from google import genai
        from google.genai import types
        # 20초 안에 답이 없으면 포기 → 화면이 멈추지 않고 데모 모드로 이어감
        _client = genai.Client(api_key=_key(), http_options=types.HttpOptions(
            timeout=20000, retry_options=types.HttpRetryOptions(attempts=2)))
    return _client


def new_chat(system_instruction):
    from google.genai import types
    return client().chats.create(
        model=_model(),
        config=types.GenerateContentConfig(system_instruction=system_instruction, temperature=0.4),
    )


def text(prompt, temperature=0.4):
    from google.genai import types
    res = client().models.generate_content(
        model=_model(), contents=prompt,
        config=types.GenerateContentConfig(temperature=temperature))
    return res.text


def json_out(contents):
    """contents: 문자열 또는 [이미지 Part, 문자열] 목록. JSON으로만 답하게 한다."""
    from google.genai import types
    res = client().models.generate_content(
        model=_model(), contents=contents,
        config=types.GenerateContentConfig(response_mime_type="application/json", temperature=0))
    return json.loads(res.text)


def image_part(data: bytes, mime="image/jpeg"):
    from google.genai import types
    return types.Part.from_bytes(data=data, mime_type=mime)


def embed(texts):
    res = client().models.embed_content(model=EMBED_MODEL, contents=texts)
    return [e.values for e in res.embeddings]


def transcribe(audio: bytes, mime="audio/wav"):
    """녹음 → 한국어 받아쓰기 (은퇴농 음성 인터뷰)"""
    from google.genai import types
    res = client().models.generate_content(
        model=_model(),
        contents=[types.Part.from_bytes(data=audio, mime_type=mime),
                  "이 녹음은 강원도 농업인의 답변입니다. 사투리·숫자를 살려 한국어로 그대로 받아 적어 주세요. 받아 적은 문장만 출력하세요."],
        config=types.GenerateContentConfig(temperature=0))
    return res.text.strip()
