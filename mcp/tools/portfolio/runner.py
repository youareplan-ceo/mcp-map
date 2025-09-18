from typing import Dict, Any, List, Optional
import yfinance as yf
import pandas as pd
import math
from pathlib import Path

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
        fv = _to_float(v)
        buf.append(fv)
        win = [x for x in buf[-n:] if x is not None]
        out.append(sum(win)/n if len(win)==n else None)
    return out

def _read_tickers_csv(path: str) -> List[str]:
    p = Path(path)
    if not p.exists():
        return []
    df = pd.read_csv(p)
    # 첫 컬럼 이름이 ticker / symbol 뭐든 간에 첫 번째 컬럼 사용
    col = df.columns[0]
    vals = [str(x).strip() for x in df[col].tolist() if str(x).strip()]
    # 주석/공란 제거 및 중복 제거
    vals = [v for v in vals if not v.startswith("#")]
    return list(dict.fromkeys(vals))

def _fetch_ohlcv(ticker: str, period="3mo", interval="1d"):
    t = yf.Ticker(ticker)
    df = t.history(period=period, interval=interval, auto_adjust=False)
    if df.empty:
        return None
    df = df.reset_index()
    df.rename(columns=str.lower, inplace=True)
    closes = [_to_float(x) for x in df["close"].tolist()]
    vols   = [None if pd.isna(x) else int(x) for x in df["volume"].fillna(0).tolist()]
    last_close = closes[-1]
    # 20일 평균 거래량
    window = [x for x in vols[-20:] if x is not None]
    avg_vol20 = int(sum(window)/len(window)) if window else 0
    return {
        "rows": len(df),
        "closes": closes,
        "vols": vols,
        "last_close": last_close,
        "avg_vol20": avg_vol20,
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

    # 입력: tickers 리스트 또는 csv_path 중 하나(둘 다 있으면 합침)
    tickers: List[str] = (payload.get("tickers") or [])[:]
    csv_path = payload.get("csv_path")
    if csv_path:
        tickers += _read_tickers_csv(csv_path)
    tickers = [t for t in tickers if t]  # 정리
    if not tickers:
        return {"error":"no tickers"}

    period   = payload.get("period", "3mo")
    interval = payload.get("interval", "1d")
    fast     = int(payload.get("fast", 5))
    slow     = int(payload.get("slow", 20))

    # 간단 필터(옵션): 최소 종가, 최소 20일 평균 거래량
    min_last_close  = _to_float(payload.get("min_last_close"))
    min_avg_vol20   = payload.get("min_avg_vol20")
    min_avg_vol20   = int(min_avg_vol20) if min_avg_vol20 not in (None, "",) else None

    results: List[Dict[str, Any]] = []
    for tk in tickers:
        data = _fetch_ohlcv(tk, period=period, interval=interval)
        if not data:
            results.append({"ticker": tk, "error": "no_data"})
            continue

        # 조건 필터링
        if min_last_close is not None and (data["last_close"] is None or data["last_close"] < min_last_close):
            results.append({"ticker": tk, "filtered": "price", "last_close": data["last_close"]})
            continue
        if (min_avg_vol20 is not None) and (data["avg_vol20"] < min_avg_vol20):
            results.append({"ticker": tk, "filtered": "volume", "avg_vol20": data["avg_vol20"], "last_close": data["last_close"]})
            continue

        sig = _sma_cross(data["closes"], fast=fast, slow=slow)
        results.append({
            "ticker": tk,
            "period": period,
            "interval": interval,
            "last_close": data["last_close"],
            "avg_vol20": data["avg_vol20"],
            "fast": fast,
            "slow": slow,
            **sig,
        })
    # 정렬: 골든크로스 우선, 다음 종가 내림차순
    order = {"golden_cross":0, "neutral":1, "death_cross":2}
    results.sort(key=lambda x: (order.get(x.get("signal","neutral"), 1), -(x.get("last_close") or 0)))
    return {"results": results, "count": len(results)}
