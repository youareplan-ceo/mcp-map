from typing import Dict, Any, List, Optional
import yfinance as yf
import pandas as pd
import math

def _to_float(v) -> Optional[float]:
    if v is None: return None
    try:
        if isinstance(v, str):
            t = v.strip()
            if t == "": return None
            v = float(t)
        else:
            v = float(v)
        if math.isnan(v): return None
        return v
    except Exception:
        return None

def _sma(vals: List[Optional[float]], n: int) -> List[Optional[float]]:
    out: List[Optional[float]] = []
    buf: List[Optional[float]] = []
    for v in vals:
        buf.append(_to_float(v))
        win = [x for x in buf[-n:] if x is not None]
        out.append(sum(win)/n if len(win)==n else None)
    return out

def _fetch_ohlcv(ticker: str, period="3mo", interval="1d"):
    t = yf.Ticker(ticker)
    df = t.history(period=period, interval=interval, auto_adjust=False)
    if df.empty:
        return None
    df = df.reset_index()
    df.rename(columns=str.lower, inplace=True)
    closes = [_to_float(x) for x in df["close"].tolist()]
    last_close = closes[-1]
    return {
        "rows": len(df),
        "closes": closes,
        "last_close": last_close,
    }

def _sma_cross(closes: List[Optional[float]], fast=5, slow=20):
    if not closes or len([x for x in closes if x is not None]) < slow+1:
        return {"signal":"neutral", "fast_ma":None, "slow_ma":None, "crossed":None}
    sma_f = _sma(closes, fast)
    sma_s = _sma(closes, slow)
    last = len(closes)-1
    fast_last, slow_last = sma_f[last], sma_s[last]
    fast_prev = sma_f[last-1] if last-1 >= 0 else None
    slow_prev = sma_s[last-1] if last-1 >= 0 else None

    signal, crossed = "neutral", None
    if (fast_prev is not None and slow_prev is not None and
        fast_last is not None and slow_last is not None):
        if fast_prev <= slow_prev and fast_last > slow_last:
            signal, crossed = "golden_cross", "up"
        elif fast_prev >= slow_prev and fast_last < slow_last:
            signal, crossed = "death_cross", "down"
    return {
        "signal": signal,
        "fast_ma": fast_last,
        "slow_ma": slow_last,
        "crossed": crossed,
    }

def run(action: str, payload: Dict[str, Any]):
    payload = payload or {}
    if action != "batch_sma":
        return {"error":"unknown action"}

    tickers: List[str] = payload.get("tickers") or []
    period   = payload.get("period", "3mo")
    interval = payload.get("interval", "1d")
    fast     = int(payload.get("fast", 5))
    slow     = int(payload.get("slow", 20))

    results: List[Dict[str, Any]] = []
    for tk in tickers:
        data = _fetch_ohlcv(tk, period=period, interval=interval)
        if not data:
            results.append({"ticker": tk, "error": "no_data"})
            continue
        sig = _sma_cross(data["closes"], fast=fast, slow=slow)
        results.append({
            "ticker": tk,
            "period": period,
            "interval": interval,
            "last_close": data["last_close"],
            "fast": fast,
            "slow": slow,
            **sig,
        })
    # 간단 정렬: 골든크로스 우선, 그다음 종가 내림차순
    order = {"golden_cross":0, "neutral":1, "death_cross":2}
    results.sort(key=lambda x: (order.get(x.get("signal","neutral"), 1), -(x.get("last_close") or 0)))
    return {"results": results, "count": len(results)}
