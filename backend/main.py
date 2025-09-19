"""
StockPilot Backend Server
24시간 조용히 감시, 중요한 순간만 알림
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import asyncio
import sqlite3
import json
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="StockPilot API", version="1.0.0")

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 스케줄러 설정
scheduler = AsyncIOScheduler()

# 데이터베이스 초기화
def init_db():
    conn = sqlite3.connect('stockpilot.db')
    c = conn.cursor()
    
    # 사용자 테이블
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  email TEXT UNIQUE,
                  name TEXT,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    # 포트폴리오 테이블
    c.execute('''CREATE TABLE IF NOT EXISTS portfolios
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER,
                  ticker TEXT,
                  quantity REAL,
                  avg_price REAL,
                  market TEXT,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY (user_id) REFERENCES users(id))''')
    
    # 알림 테이블
    c.execute('''CREATE TABLE IF NOT EXISTS alerts
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER,
                  ticker TEXT,
                  alert_type TEXT,
                  message TEXT,
                  price REAL,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  is_read BOOLEAN DEFAULT 0,
                  FOREIGN KEY (user_id) REFERENCES users(id))''')
    
    conn.commit()
    conn.close()

# Pydantic 모델
class UserCreate(BaseModel):
    email: str
    name: str

class PortfolioAdd(BaseModel):
    user_id: int
    ticker: str
    quantity: float
    avg_price: float
    market: str = "US"  # US, KR

class Alert(BaseModel):
    id: int
    ticker: str
    alert_type: str
    message: str
    price: float
    created_at: str

# RSI 계산
def calculate_rsi(ticker: str, period: int = 14) -> float:
    """RSI (Relative Strength Index) 계산"""
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="1mo", interval="1d")
        
        if hist.empty:
            return 50.0
        
        close_prices = hist['Close']
        delta = close_prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        return float(rsi.iloc[-1]) if not pd.isna(rsi.iloc[-1]) else 50.0
    except Exception as e:
        logger.error(f"RSI 계산 실패 {ticker}: {e}")
        return 50.0

# MACD 계산
def calculate_macd(ticker: str) -> dict:
    """MACD 계산"""
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="3mo", interval="1d")
        
        if hist.empty:
            return {"macd": 0, "signal": 0, "histogram": 0}
        
        close_prices = hist['Close']
        
        # MACD 계산
        exp1 = close_prices.ewm(span=12, adjust=False).mean()
        exp2 = close_prices.ewm(span=26, adjust=False).mean()
        macd = exp1 - exp2
        signal = macd.ewm(span=9, adjust=False).mean()
        histogram = macd - signal
        
        return {
            "macd": float(macd.iloc[-1]),
            "signal": float(signal.iloc[-1]),
            "histogram": float(histogram.iloc[-1])
        }
    except Exception as e:
        logger.error(f"MACD 계산 실패 {ticker}: {e}")
        return {"macd": 0, "signal": 0, "histogram": 0}

# 현재가 조회
def get_current_price(ticker: str) -> float:
    """실시간 주가 조회"""
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        # 현재가 가져오기 (여러 필드 체크)
        price = info.get('currentPrice') or info.get('regularMarketPrice') or info.get('previousClose', 0)
        return float(price)
    except Exception as e:
        logger.error(f"주가 조회 실패 {ticker}: {e}")
        return 0.0

# 포트폴리오 체크 (5분마다 실행)
async def check_portfolios():
    """모든 포트폴리오 체크하고 중요한 신호만 생성"""
    logger.info("포트폴리오 체크 시작")
    
    conn = sqlite3.connect('stockpilot.db')
    c = conn.cursor()
    
    # 모든 포트폴리오 조회
    c.execute('''SELECT DISTINCT p.*, u.email 
                 FROM portfolios p 
                 JOIN users u ON p.user_id = u.id''')
    portfolios = c.fetchall()
    
    for portfolio in portfolios:
        user_id, ticker = portfolio[1], portfolio[2]
        quantity, avg_price = portfolio[3], portfolio[4]
        
        try:
            # 현재가 조회
            current_price = get_current_price(ticker)
            
            # 기술적 지표 계산
            rsi = calculate_rsi(ticker)
            macd_data = calculate_macd(ticker)
            
            # 수익률 계산
            profit_rate = ((current_price - avg_price) / avg_price) * 100 if avg_price > 0 else 0
            
            # ===== 핵심: 중요한 순간만 알림 =====
            alert_created = False
            
            # 1. 매도 신호 (RSI > 70 + 수익률 > 10%)
            if rsi > 70 and profit_rate > 10:
                message = f"🔴 매도 신호! RSI {rsi:.1f}, 수익률 +{profit_rate:.1f}%"
                c.execute('''INSERT INTO alerts (user_id, ticker, alert_type, message, price)
                           VALUES (?, ?, ?, ?, ?)''',
                         (user_id, ticker, 'SELL', message, current_price))
                alert_created = True
                logger.info(f"매도 신호 생성: {ticker}")
            
            # 2. 매수 신호 (RSI < 30)
            elif rsi < 30:
                message = f"🟢 매수 기회! RSI {rsi:.1f}, 현재가 ${current_price:.2f}"
                c.execute('''INSERT INTO alerts (user_id, ticker, alert_type, message, price)
                           VALUES (?, ?, ?, ?, ?)''',
                         (user_id, ticker, 'BUY', message, current_price))
                alert_created = True
                logger.info(f"매수 신호 생성: {ticker}")
            
            # 3. 손절 신호 (손실 -15% 이상)
            elif profit_rate < -15:
                message = f"⚠️ 손절 검토! 손실률 {profit_rate:.1f}%"
                c.execute('''INSERT INTO alerts (user_id, ticker, alert_type, message, price)
                           VALUES (?, ?, ?, ?, ?)''',
                         (user_id, ticker, 'STOP_LOSS', message, current_price))
                alert_created = True
                logger.info(f"손절 신호 생성: {ticker}")
            
            # 4. 골든크로스/데드크로스
            elif macd_data['histogram'] > 0 and abs(macd_data['histogram']) > abs(macd_data['signal']) * 0.1:
                message = f"📈 골든크로스 신호! MACD 상향돌파"
                c.execute('''INSERT INTO alerts (user_id, ticker, alert_type, message, price)
                           VALUES (?, ?, ?, ?, ?)''',
                         (user_id, ticker, 'GOLDEN_CROSS', message, current_price))
                alert_created = True
            
            # 99% 경우: 아무 알림도 생성하지 않음
            if not alert_created:
                logger.debug(f"{ticker}: 포트폴리오 안정 ✅")
                
        except Exception as e:
            logger.error(f"종목 체크 실패 {ticker}: {e}")
    
    conn.commit()
    conn.close()
    logger.info("포트폴리오 체크 완료")

# API 엔드포인트들

@app.on_event("startup")
async def startup_event():
    """서버 시작 시 초기화"""
    init_db()
    
    # 스케줄러 시작 (5분마다 체크)
    scheduler.add_job(check_portfolios, 'interval', minutes=5)
    scheduler.start()
    logger.info("StockPilot 서버 시작 - 24시간 감시 모드")
    
    # 초기 체크
    await check_portfolios()

@app.get("/")
async def root():
    """서버 상태 확인"""
    return {
        "service": "StockPilot",
        "status": "running",
        "message": "포트폴리오 안정 ✅",
        "philosophy": "평소엔 조용, 중요할 때만 알림"
    }

@app.post("/users/create")
async def create_user(user: UserCreate):
    """사용자 생성"""
    conn = sqlite3.connect('stockpilot.db')
    c = conn.cursor()
    
    try:
        c.execute("INSERT INTO users (email, name) VALUES (?, ?)",
                 (user.email, user.name))
        user_id = c.lastrowid
        conn.commit()
        return {"user_id": user_id, "message": "사용자 생성 완료"}
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="이미 존재하는 이메일")
    finally:
        conn.close()

@app.post("/portfolio/add")
async def add_portfolio(portfolio: PortfolioAdd):
    """포트폴리오에 종목 추가"""
    conn = sqlite3.connect('stockpilot.db')
    c = conn.cursor()
    
    # 한국 주식 티커 변환 (예: 삼성전자 -> 005930.KS)
    if portfolio.market == "KR" and not portfolio.ticker.endswith(".KS"):
        portfolio.ticker = f"{portfolio.ticker}.KS"
    
    c.execute('''INSERT INTO portfolios (user_id, ticker, quantity, avg_price, market)
                 VALUES (?, ?, ?, ?, ?)''',
             (portfolio.user_id, portfolio.ticker, portfolio.quantity, 
              portfolio.avg_price, portfolio.market))
    
    conn.commit()
    conn.close()
    
    # 즉시 체크
    await check_portfolios()
    
    return {"message": f"{portfolio.ticker} 추가 완료", "status": "monitoring"}

@app.get("/portfolio/{user_id}")
async def get_portfolio(user_id: int):
    """사용자 포트폴리오 조회"""
    conn = sqlite3.connect('stockpilot.db')
    c = conn.cursor()
    
    c.execute('''SELECT ticker, quantity, avg_price, market 
                 FROM portfolios WHERE user_id = ?''', (user_id,))
    
    portfolios = []
    total_value = 0
    total_cost = 0
    
    for row in c.fetchall():
        ticker, quantity, avg_price, market = row
        current_price = get_current_price(ticker)
        current_value = current_price * quantity
        cost = avg_price * quantity
        profit = current_value - cost
        profit_rate = (profit / cost * 100) if cost > 0 else 0
        
        portfolios.append({
            "ticker": ticker,
            "quantity": quantity,
            "avg_price": avg_price,
            "current_price": current_price,
            "current_value": current_value,
            "profit": profit,
            "profit_rate": profit_rate,
            "market": market
        })
        
        total_value += current_value
        total_cost += cost
    
    conn.close()
    
    total_profit = total_value - total_cost
    total_profit_rate = (total_profit / total_cost * 100) if total_cost > 0 else 0
    
    return {
        "portfolios": portfolios,
        "summary": {
            "total_value": total_value,
            "total_cost": total_cost,
            "total_profit": total_profit,
            "total_profit_rate": total_profit_rate,
            "status": "포트폴리오 안정 ✅" if abs(total_profit_rate) < 5 else "주의 필요 ⚠️"
        }
    }

@app.get("/alerts/{user_id}")
async def get_alerts(user_id: int, unread_only: bool = True):
    """사용자 알림 조회"""
    conn = sqlite3.connect('stockpilot.db')
    c = conn.cursor()
    
    if unread_only:
        c.execute('''SELECT id, ticker, alert_type, message, price, created_at 
                     FROM alerts 
                     WHERE user_id = ? AND is_read = 0
                     ORDER BY created_at DESC
                     LIMIT 10''', (user_id,))
    else:
        c.execute('''SELECT id, ticker, alert_type, message, price, created_at 
                     FROM alerts 
                     WHERE user_id = ?
                     ORDER BY created_at DESC
                     LIMIT 20''', (user_id,))
    
    alerts = []
    for row in c.fetchall():
        alerts.append({
            "id": row[0],
            "ticker": row[1],
            "alert_type": row[2],
            "message": row[3],
            "price": row[4],
            "created_at": row[5]
        })
    
    # 읽음 처리
    if unread_only and alerts:
        alert_ids = [a["id"] for a in alerts]
        c.execute(f"UPDATE alerts SET is_read = 1 WHERE id IN ({','.join('?' * len(alert_ids))})", 
                  alert_ids)
        conn.commit()
    
    conn.close()
    
    # 알림이 없으면 평온한 상태
    if not alerts:
        return {
            "alerts": [],
            "message": "포트폴리오 안정 ✅",
            "description": "특별한 신호가 없습니다"
        }
    
    return {"alerts": alerts}

@app.get("/check/{ticker}")
async def check_ticker(ticker: str):
    """특정 종목 즉시 분석"""
    try:
        current_price = get_current_price(ticker)
        rsi = calculate_rsi(ticker)
        macd = calculate_macd(ticker)
        
        # 신호 판단
        signal = "HOLD"
        if rsi > 70:
            signal = "SELL"
        elif rsi < 30:
            signal = "BUY"
        elif macd['histogram'] > 0:
            signal = "BULLISH"
        elif macd['histogram'] < 0:
            signal = "BEARISH"
        
        return {
            "ticker": ticker,
            "current_price": current_price,
            "rsi": rsi,
            "macd": macd,
            "signal": signal,
            "message": f"RSI {rsi:.1f} | MACD {macd['histogram']:.2f}"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/force-check")
async def force_check():
    """수동으로 포트폴리오 체크 실행"""
    await check_portfolios()
    return {"message": "체크 완료", "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)