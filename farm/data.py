"""데이터 불러오기·저장.
- data/buyers.csv, data/farmers.csv : 시연용 가상 데이터(6가지 기준 단위로 정리됨)
- farm.db (SQLite) : 인터뷰로 새로 들어온 은퇴농·거래처, 시험 납품 신청 저장
흐름(팀 결정): 공공데이터 자동 불러오기 → 있으면 미리 채워 확인 → 없으면 직접 입력
"""
import os
import json
import sqlite3
import pandas as pd

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "data")
DB = os.path.join(BASE, "farm.db")

GRADE = {"특": 4, "상": 3, "중": 2, "못난이": 1, "무관": 1}
GRADE_NAME = {4: "특", 3: "상", 2: "중", 1: "무관"}
CRITERIA = ["물량 안정성", "품질·규격", "가격", "납품 주기", "물류·거리", "인증·신뢰"]


def _conn():
    c = sqlite3.connect(DB)
    c.executescript("""
    CREATE TABLE IF NOT EXISTS retirees (id INTEGER PRIMARY KEY AUTOINCREMENT, created TEXT, profile TEXT, transcript TEXT);
    CREATE TABLE IF NOT EXISTS buyers_extra (name TEXT PRIMARY KEY, row TEXT);
    CREATE TABLE IF NOT EXISTS trials (id INTEGER PRIMARY KEY AUTOINCREMENT, created TEXT, farmer TEXT, buyer TEXT, qty TEXT, memo TEXT);
    """)
    return c


def _split(v):
    if isinstance(v, list):
        return [str(x).strip() for x in v if str(x).strip()]
    if pd.isna(v) or v == "":
        return []
    return [x.strip() for x in str(v).split(",") if x.strip()]


def _norm(df):
    for col in ("items", "months", "days", "certs"):
        if col in df.columns:
            df[col] = df[col].apply(_split)
    if "months" in df.columns:
        df["months"] = df["months"].apply(lambda xs: [int(x) for x in xs])
    for col in ("cert",):
        if col in df.columns:
            df[col] = df[col].fillna("")
    return df


def load_buyers():
    df = pd.read_csv(os.path.join(DATA, "buyers.csv"))
    with _conn() as c:
        extra = [json.loads(r[0]) for r in c.execute("SELECT row FROM buyers_extra")]
    if extra:
        df = pd.concat([df, pd.DataFrame(extra)], ignore_index=True)
    return _norm(df)


def load_farmers():
    return _norm(pd.read_csv(os.path.join(DATA, "farmers.csv")))


def save_retiree(profile: dict, transcript: list):
    with _conn() as c:
        c.execute("INSERT INTO retirees(created, profile, transcript) VALUES (datetime('now','localtime'),?,?)",
                  (json.dumps(profile, ensure_ascii=False), json.dumps(transcript, ensure_ascii=False)))


def save_buyer(row: dict):
    """인터뷰로 정리된 거래처를 매칭 대상에 추가 (모델 1 → 모델 2 연결 지점)"""
    row = dict(row)
    for k in ("items", "months", "days"):
        if isinstance(row.get(k), list):
            row[k] = ",".join(str(x) for x in row[k])
    with _conn() as c:
        c.execute("INSERT OR REPLACE INTO buyers_extra(name,row) VALUES (?,?)",
                  (row["name"], json.dumps(row, ensure_ascii=False)))


def list_retirees():
    with _conn() as c:
        return [(r[0], json.loads(r[1])) for r in c.execute("SELECT created, profile FROM retirees ORDER BY id DESC")]


def save_trial(farmer, buyer, qty, memo):
    with _conn() as c:
        c.execute("INSERT INTO trials(created,farmer,buyer,qty,memo) VALUES (datetime('now','localtime'),?,?,?,?)",
                  (farmer, buyer, qty, memo))


def list_trials():
    with _conn() as c:
        return pd.read_sql("SELECT created AS 신청일시, farmer AS 청년농, buyer AS 구매처, qty AS 물량, memo AS 메모 FROM trials ORDER BY id DESC", c)


# ── 공공데이터: 있으면 미리 채우고, 없으면 None (→ 화면에서 직접 입력) ──
def public_lookup(kind: str, key: str):
    """kind='buyer' : 공공 판매처(급식 등) 이름으로 조회 / kind='cert' : 인증번호로 조회.
    해커톤에선 공공데이터포털에서 받아둔 CSV를 data/public_*.csv로 넣으면 여기서 읽힌다."""
    if kind == "buyer":
        b = load_buyers()
        hit = b[(b["source"] == "공공데이터") & (b["name"].str.contains(key, na=False))]
        return None if hit.empty else hit.iloc[0].to_dict()
    if kind == "cert":
        path = os.path.join(DATA, "public_gap.csv")
        if os.path.exists(path):
            g = pd.read_csv(path, dtype=str)
            hit = g[g.apply(lambda r: key in " ".join(r.values.astype(str)), axis=1)]
            return None if hit.empty else hit.iloc[0].to_dict()
        return None
    return None
