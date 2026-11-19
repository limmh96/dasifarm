"""Gemini 호출을 한 곳에 모은 모듈.
키가 없으면 has_ai()가 False → 각 기능이 '데모 모드'(규칙 기반)로 동작한다.
"""
import os
import json

MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")   # AI Studio에서 쓰는 모델 이름으로 바꿔도 됨
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


def has_ai():
    return bool(_key())


def client():
    global _client
    if _client is None:
        from google import genai
        _client = genai.Client(api_key=_key())
    return _client


def new_chat(system_instruction):
    from google.genai import types
    return client().chats.create(
        model=MODEL,
        config=types.GenerateContentConfig(system_instruction=system_instruction, temperature=0.4),
    )


def text(prompt, temperature=0.4):
    from google.genai import types
    res = client().models.generate_content(
        model=MODEL, contents=prompt,
        config=types.GenerateContentConfig(temperature=temperature))
    return res.text


def json_out(contents):
    """contents: 문자열 또는 [이미지 Part, 문자열] 목록. JSON으로만 답하게 한다."""
    from google.genai import types
    res = client().models.generate_content(
        model=MODEL, contents=contents,
        config=types.GenerateContentConfig(response_mime_type="application/json", temperature=0))
    return json.loads(res.text)


def image_part(data: bytes, mime="image/jpeg"):
    from google.genai import types
    return types.Part.from_bytes(data=data, mime_type=mime)


def embed(texts):
    res = client().models.embed_content(model=EMBED_MODEL, contents=texts)
    return [e.values for e in res.embeddings]
