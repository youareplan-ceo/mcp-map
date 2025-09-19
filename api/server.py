from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List
import duckdb
import os

DB = os.getenv("SP_DB_PATH", "data/stock_signals.duckdb")

app = FastAPI(title="StockPilot API", version="0.1.0")

# 필요한 경우 CORS 허용 (임시-개발용: 로컬/모든 오리진)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"]
)

def latest_run_id(con) -> Optional[str]:
    row = con.execute("SELECT run_id FROM runs ORDER BY ts_epoch DESC LIMIT 1").fetchone()
    return row[0] if row else None

@app.get("/health")
def health():
    return {"ok": True}

@app.get("/signals/latest")
def signals_latest(
    limit: int = Query(50, ge=1, le=500),
    include: Optional[List[str]] = Query(None, description="포함할 티커 목록 (여러개 가능)"),
    exclude: Optional[List[str]] = Query(None, description="제외할 티커 목록 (여러개 가능)"),
    min_rsi: Optional[float] = Query(None, ge=0, le=100),
    max_rsi: Optional[float] = Query(None, ge=0, le=100),
    max_atr: Optional[float] = Query(None, ge=0),
    only_crossed: Optional[bool] = Query(False),
    signal_in: Optional[List[str]] = Query(None, description="예: BUY,SELL,WATCH,TAKE_PROFIT")
):
    con = duckdb.connect(DB, read_only=True)
    try:
        rid = latest_run_id(con)
        if not rid:
            return {"ok": True, "run_id": None, "rows": []}

        q = """
        SELECT ticker, last_close, rsi14, atr_pct, signal, crossed, fast, slow, avg_vol20
        FROM signals
        WHERE run_id = ?
        """
        params = [rid]

        if include:
            q += " AND ticker IN (" + ",".join(["?"]*len(include)) + ")"
            params += include
        if exclude:
            q += " AND ticker NOT IN (" + ",".join(["?"]*len(exclude)) + ")"
            params += exclude
        if min_rsi is not None:
            q += " AND rsi14 >= ?"; params.append(min_rsi)
        if max_rsi is not None:
            q += " AND rsi14 <= ?"; params.append(max_rsi)
        if max_atr is not None:
            q += " AND atr_pct <= ?"; params.append(max_atr)
        if only_crossed:
            q += " AND crossed = TRUE"
        if signal_in:
            q += " AND signal IN (" + ",".join(["?"]*len(signal_in)) + ")"
            params += signal_in

        q += " ORDER BY ticker LIMIT ?"
        params.append(limit)

        rows = [dict(zip([c[0] for c in con.description], r))
                for r in con.execute(q, params).fetchall()]
        return {"ok": True, "run_id": rid, "rows": rows}
    finally:
        con.close()
