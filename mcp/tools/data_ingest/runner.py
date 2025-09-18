import os, sys, json, csv, io, time
from typing import List, Dict
import duckdb
import datetime
try:
    import requests
except Exception:
    requests = None

DB = os.getenv("SP_DB_PATH", "data/stock_signals.duckdb")

DDL = """
CREATE TABLE IF NOT EXISTS universe(
  ticker   VARCHAR PRIMARY KEY,
  name     VARCHAR,
  market   VARCHAR,
  note     VARCHAR,
  added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

def _ensure():
    con = duckdb.connect(DB)
    con.execute(DDL)
    con.close()

def _upsert_rows(rows: List[Dict]):
    _ensure()
    con = duckdb.connect(DB)
    for r in rows:
        con.execute("""
        MERGE INTO universe AS u
        USING (SELECT ? AS ticker, ? AS name, ? AS market, ? AS note) AS s
        ON u.ticker = s.ticker
        WHEN MATCHED THEN
          UPDATE SET name=s.name, market=s.market, note=s.note, added_at=CURRENT_TIMESTAMP
        WHEN NOT MATCHED THEN
          INSERT (ticker,name,market,note,added_at)
          VALUES (s.ticker,s.name,s.market,s.note,CURRENT_TIMESTAMP);
        """, [r.get("ticker","").strip().upper(),
              (r.get("name") or "").strip(),
              (r.get("market") or "").strip(),
              (r.get("note") or "").strip()])
    con.close()

def _load_csv_text(text: str):
    f = io.StringIO(text)
    reader = csv.DictReader(f)
    rows = []
    for row in reader:
        t = (row.get("ticker") or "").strip()
        if not t:
            continue
        rows.append({
            "ticker": t,
            "name": (row.get("name") or "").strip(),
            "market": (row.get("market") or "").strip(),
            "note": (row.get("note") or "").strip()
        })
    if not rows:
        return {"ok": False, "error": "no rows"}
    _upsert_rows(rows)
    return {"ok": True, "count": len(rows)}

def run(action: str, payload: dict):
    """
    actions:
      - load.csv         {path}                # 로컬 CSV
      - load.http_csv    {url}                 # 공개 CSV URL(예: 구글시트 '웹에 게시' CSV)
      - preview          {limit?=20}
      - reset            {}                    # 유니버스 비우기(주의)
      - list             {limit?=100}
    CSV 헤더 예시: ticker,name,market,note
    """
    if action == "load.csv":
        path = payload.get("path")
        if not path or not os.path.exists(path):
            return {"ok": False, "error": f"file not found: {path}"}
        text = open(path, "r", encoding="utf-8").read()
        return _load_csv_text(text)

    elif action == "load.http_csv":
        url = payload.get("url")
        if not url:
            return {"ok": False, "error": "url required"}
        if not requests:
            return {"ok": False, "error": "requests not installed"}
        r = requests.get(url, timeout=15)
        r.raise_for_status()
        return _load_csv_text(r.text)

    elif action == "preview":
        _ensure()
        limit = int(payload.get("limit") or 20)
        con = duckdb.connect(DB, read_only=True)
        rows = con.execute("SELECT * FROM universe ORDER BY ticker LIMIT ?", [limit]).fetchall()
        cols = [d[0] for d in con.description]
        con.close()
        return {"ok": True, "rows": [
        {k: (v.isoformat(sep=' ') if isinstance(v,(datetime.datetime,datetime.date)) else v) for k,v in zip(cols,row)} for row in rows]}

    elif action == "list":
        return run("preview", {"limit": int(payload.get("limit") or 100)})

    elif action == "reset":
        _ensure()
        con = duckdb.connect(DB)
        con.execute("DELETE FROM universe")
        con.close()
        return {"ok": True, "deleted": "all"}

    else:
        return {"ok": False, "error": f"unknown action: {action}"}

if __name__ == "__main__":
    action = sys.argv[1]
    payload = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}
    print(json.dumps(run(action, payload), ensure_ascii=False))
