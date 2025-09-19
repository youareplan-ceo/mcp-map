#!/usr/bin/env python3
"""
StockPilot 실시간 주가 API 서버
yfinance를 사용한 무료 실시간 데이터
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import List, Dict, Any
import yfinance as yf
import uvicorn
from datetime import datetime, timedelta
import asyncio

app = FastAPI(title="StockPilot Price API")

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 인기 종목 리스트
POPULAR_STOCKS = {
    "한국": {
        "삼성전자": "005930.KS",
        "SK하이닉스": "000660.KS",
        "LG에너지솔루션": "373220.KS",
        "네이버": "035420.KS",
        "카카오": "035720.KS",
        "현대차": "005380.KS",
        "기아": "000270.KS",
        "삼성바이오로직스": "207940.KS",
        "셀트리온": "068270.KS",
        "KB금융": "105560.KS"
    },
    "미국": {
        "애플": "AAPL",
        "마이크로소프트": "MSFT",
        "엔비디아": "NVDA",
        "구글": "GOOGL",
        "아마존": "AMZN",
        "메타": "META",
        "테슬라": "TSLA",
        "버크셔": "BRK-B",
        "비자": "V",
        "JP모건": "JPM"
    }
}

@app.get("/")
async def health():
    """헬스체크"""
    return {"status": "StockPilot Price API Running", "time": datetime.now().isoformat()}

@app.get("/api/price/{ticker}")
async def get_stock_price(ticker: str):
    """
    실시간 주가 조회
    ticker: 종목 코드 (예: AAPL, 005930.KS)
    """
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        # 기본 정보
        data = {
            "ticker": ticker,
            "name": info.get("longName", ticker),
            "currentPrice": info.get("currentPrice") or info.get("regularMarketPrice"),
            "previousClose": info.get("previousClose"),
            "dayChange": 0,
            "dayChangePercent": 0,
            "volume": info.get("volume"),
            "marketCap": info.get("marketCap"),
            "currency": info.get("currency", "KRW" if ticker.endswith(".KS") else "USD"),
            "timestamp": datetime.now().isoformat()
        }
        
        # 변동률 계산
        if data["currentPrice"] and data["previousClose"]:
            data["dayChange"] = data["currentPrice"] - data["previousClose"]
            data["dayChangePercent"] = (data["dayChange"] / data["previousClose"]) * 100
        
        return JSONResponse(content=data)
    
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"종목을 찾을 수 없습니다: {str(e)}")

@app.post("/api/prices")
async def get_multiple_prices(tickers: List[str]):
    """
    여러 종목 동시 조회
    """
    results = {}
    
    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            
            current_price = info.get("currentPrice") or info.get("regularMarketPrice")
            previous_close = info.get("previousClose")
            
            results[ticker] = {
                "name": info.get("longName", ticker),
                "price": current_price,
                "previousClose": previous_close,
                "change": current_price - previous_close if current_price and previous_close else 0,
                "changePercent": ((current_price - previous_close) / previous_close * 100) if current_price and previous_close else 0,
                "volume": info.get("volume")
            }
        except:
            results[ticker] = {"error": "데이터 없음"}
    
    return JSONResponse(content=results)

@app.get("/api/chart/{ticker}")
async def get_chart_data(ticker: str, period: str = "1d", interval: str = "5m"):
    """
    차트 데이터 조회
    period: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max
    interval: 1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo
    """
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period=period, interval=interval)
        
        chart_data = []
        for index, row in hist.iterrows():
            chart_data.append({
                "time": index.isoformat(),
                "open": row["Open"],
                "high": row["High"],
                "low": row["Low"],
                "close": row["Close"],
                "volume": int(row["Volume"])
            })
        
        return JSONResponse(content={"ticker": ticker, "data": chart_data})
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/analysis/{ticker}")
async def get_technical_analysis(ticker: str):
    """
    기술적 분석 지표
    """
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="3mo")
        
        if len(hist) < 20:
            return JSONResponse(content={"error": "데이터 부족"})
        
        closes = hist["Close"].values
        volumes = hist["Volume"].values
        
        # 이동평균선
        ma5 = closes[-5:].mean()
        ma20 = closes[-20:].mean()
        ma60 = closes[-60:].mean() if len(closes) >= 60 else None
        
        # RSI 계산 (14일)
        deltas = [closes[i] - closes[i-1] for i in range(1, min(15, len(closes)))]
        gains = [d if d > 0 else 0 for d in deltas]
        losses = [-d if d < 0 else 0 for d in deltas]
        
        avg_gain = sum(gains) / 14 if gains else 0
        avg_loss = sum(losses) / 14 if losses else 0
        
        if avg_loss == 0:
            rsi = 100
        else:
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
        
        # 볼린저 밴드
        std20 = closes[-20:].std()
        upper_band = ma20 + (std20 * 2)
        lower_band = ma20 - (std20 * 2)
        
        # 신호 생성
        current_price = closes[-1]
        signal = "중립"
        
        if ma5 > ma20 and rsi < 70:
            signal = "매수"
        elif ma5 < ma20 and rsi > 30:
            signal = "매도"
        elif rsi > 70:
            signal = "과매수"
        elif rsi < 30:
            signal = "과매도"
        
        return JSONResponse(content={
            "ticker": ticker,
            "currentPrice": float(current_price),
            "ma5": float(ma5),
            "ma20": float(ma20),
            "ma60": float(ma60) if ma60 else None,
            "rsi": float(rsi),
            "bollingerUpper": float(upper_band),
            "bollingerLower": float(lower_band),
            "volume": int(volumes[-1]),
            "avgVolume20": int(volumes[-20:].mean()),
            "signal": signal,
            "timestamp": datetime.now().isoformat()
        })
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/recommend")
async def get_recommendations():
    """
    AI 추천 종목 (간단한 로직)
    """
    recommendations = []
    
    # 한국 주식 체크
    for name, ticker in list(POPULAR_STOCKS["한국"].items())[:3]:
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period="1mo")
            
            if len(hist) >= 20:
                closes = hist["Close"].values
                ma5 = closes[-5:].mean()
                ma20 = closes[-20:].mean()
                
                if ma5 > ma20:  # 골든크로스
                    recommendations.append({
                        "type": "opportunity",
                        "ticker": ticker,
                        "name": name,
                        "reason": "골든크로스 발생",
                        "currentPrice": float(closes[-1]),
                        "targetPrice": float(closes[-1] * 1.05),
                        "confidence": 75
                    })
        except:
            pass
    
    # 미국 주식 체크
    for name, ticker in list(POPULAR_STOCKS["미국"].items())[:3]:
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            pe_ratio = info.get("trailingPE", 0)
            
            if 10 < pe_ratio < 25:  # 적정 PER
                recommendations.append({
                    "type": "value",
                    "ticker": ticker,
                    "name": name,
                    "reason": f"적정 PER ({pe_ratio:.1f})",
                    "currentPrice": info.get("currentPrice"),
                    "targetPrice": info.get("targetHighPrice"),
                    "confidence": 60
                })
        except:
            pass
    
    return JSONResponse(content={
        "recommendations": recommendations[:5],  # 최대 5개
        "timestamp": datetime.now().isoformat()
    })

@app.get("/api/popular")
async def get_popular_stocks():
    """
    인기 종목 리스트
    """
    return JSONResponse(content=POPULAR_STOCKS)

if __name__ == "__main__":
    print("🚀 StockPilot 실시간 주가 API")
    print("📍 http://localhost:8002")
    uvicorn.run(app, host="0.0.0.0", port=8002)
