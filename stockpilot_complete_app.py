#!/usr/bin/env python3
"""
StockPilot Complete App - 전체 통합 버전
AI 기반 주식 시장 분석 도구 (투자자문업 규제 준수)
"""

# ============================================================================
# CONFIGURATION & IMPORTS
# ============================================================================

import os
import sys
import json
import logging
import asyncio
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum

# FastAPI & Web
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
import uvicorn

# Data & Finance
import yfinance as yf
import pandas as pd
import numpy as np

# Environment
from dotenv import load_dotenv
load_dotenv()

# API Keys from environment variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "your-api-key-here")
YAHOO_API_KEY = os.getenv("YAHOO_API_KEY", "")
SENTRY_DSN = os.getenv("SENTRY_DSN", "")

# ============================================================================
# PRICING MODEL (규제 준수)
# ============================================================================

class PricingTier(str, Enum):
    FREE = "FREE"
    BASIC = "BASIC"
    PRO = "PRO"
    PREMIUM = "PREMIUM"

class PricingModel:
    """월정액 구독 모델 - 투자자문업 규제 회피"""
    
    TIERS = {
        PricingTier.FREE: {
            "price": 0,
            "name": "무료",
            "features": {
                "realtime_quotes": True,
                "portfolio_tracking": True,
                "basic_charts": True,
                "ai_analysis_count": 0,
                "news_access": True
            }
        },
        PricingTier.BASIC: {
            "price": 19900,
            "name": "베이직",
            "features": {
                "realtime_quotes": True,
                "portfolio_tracking": True,
                "advanced_charts": True,
                "ai_analysis_count": 10,
                "technical_indicators": True,
                "risk_analysis": True
            }
        },
        PricingTier.PRO: {
            "price": 49900,
            "name": "프로",
            "features": {
                "realtime_quotes": True,
                "portfolio_tracking": True,
                "advanced_charts": True,
                "ai_analysis_count": -1,  # 무제한
                "technical_indicators": True,
                "risk_analysis": True,
                "pattern_recognition": True,
                "sector_analysis": True
            }
        },
        PricingTier.PREMIUM: {
            "price": 99900,
            "name": "프리미엄",
            "features": {
                "realtime_quotes": True,
                "portfolio_tracking": True,
                "advanced_charts": True,
                "ai_analysis_count": -1,
                "technical_indicators": True,
                "risk_analysis": True,
                "pattern_recognition": True,
                "sector_analysis": True,
                "realtime_alerts": True,
                "api_access": True,
                "priority_support": True
            }
        }
    }

# ============================================================================
# COMPLIANCE MANAGER (법적 준수)
# ============================================================================

class ComplianceManager:
    """규제 준수 관리자"""
    
    DISCLAIMER = "본 정보는 투자 참고 자료이며, 투자 결정은 이용자 책임입니다"
    
    PROHIBITED_TERMS = [
        "매수 추천", "매도 추천", "투자 권유", 
        "수익 보장", "손실 보전", "원금 보장"
    ]
    
    REPLACEMENT_TERMS = {
        "매수": "상승 신호",
        "매도": "하락 신호",
        "추천": "분석",
        "목표가": "저항선",
        "손절가": "지지선"
    }
    
    @staticmethod
    def add_disclaimer(response: dict) -> dict:
        """모든 응답에 면책조항 추가"""
        response["disclaimer"] = ComplianceManager.DISCLAIMER
        return response
    
    @staticmethod
    def filter_terms(text: str) -> str:
        """규제 위반 용어 필터링"""
        for old, new in ComplianceManager.REPLACEMENT_TERMS.items():
            text = text.replace(old, new)
        return text

# ============================================================================
# DATABASE MANAGER
# ============================================================================

class DatabaseManager:
    """SQLite 데이터베이스 관리"""
    
    def __init__(self, db_path: str = "stockpilot.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """데이터베이스 초기화"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 포트폴리오 테이블
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS portfolio (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                symbol TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                avg_price REAL NOT NULL,
                current_price REAL,
                pnl REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 사용자 구독 테이블
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS subscriptions (
                user_id TEXT PRIMARY KEY,
                tier TEXT NOT NULL,
                started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP,
                ai_usage_count INTEGER DEFAULT 0
            )
        ''')
        
        # 분석 로그 테이블
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS analysis_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                symbol TEXT NOT NULL,
                analysis_type TEXT NOT NULL,
                result TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()

# ============================================================================
# STOCK ANALYZER (AI 분석 엔진)
# ============================================================================

class StockAnalyzer:
    """주식 분석 엔진 - 규제 준수 버전"""
    
    def __init__(self):
        self.compliance = ComplianceManager()
    
    def analyze_stock(self, symbol: str) -> dict:
        """종목 분석 - 투자 권유가 아닌 정보 제공"""
        try:
            stock = yf.Ticker(symbol)
            info = stock.info
            hist = stock.history(period="1mo")
            
            # 기술적 지표 계산
            current_price = hist['Close'].iloc[-1]
            sma_20 = hist['Close'].rolling(window=20).mean().iloc[-1]
            rsi = self.calculate_rsi(hist['Close'])
            
            # 분석 결과 (권유가 아닌 지표)
            analysis = {
                "symbol": symbol,
                "current_price": current_price,
                "technical_indicators": {
                    "rsi": rsi,
                    "sma_20": sma_20,
                    "volume_trend": "증가" if hist['Volume'].iloc[-1] > hist['Volume'].mean() else "감소",
                    "price_position": "과매수" if rsi > 70 else "과매도" if rsi < 30 else "중립"
                },
                "ai_score": np.random.randint(40, 90),  # 실제로는 AI 모델 사용
                "resistance_level": current_price * 1.05,  # 목표가 아닌 저항선
                "support_level": current_price * 0.95,      # 손절가 아닌 지지선
                "analysis_type": "기술적 분석",
                "timestamp": datetime.now().isoformat()
            }
            
            # 규제 준수를 위한 면책조항 추가
            return self.compliance.add_disclaimer(analysis)
            
        except Exception as e:
            logging.error(f"Analysis error for {symbol}: {str(e)}")
            return {
                "error": "분석 실패",
                "message": str(e),
                "disclaimer": self.compliance.DISCLAIMER
            }
    
    def calculate_rsi(self, prices: pd.Series, period: int = 14) -> float:
        """RSI 계산"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi.iloc[-1]

# ============================================================================
# MCP SERVER INTEGRATION
# ============================================================================

class StockPilotMCP:
    """MCP 서버 통합 - Claude/GPT 연동"""
    
    def __init__(self):
        self.db = DatabaseManager()
        self.analyzer = StockAnalyzer()
        self.watchlist = ["AAPL", "MSFT", "GOOGL", "TSLA", "NVDA"]
    
    async def get_portfolio_analysis(self, user_id: str) -> dict:
        """포트폴리오 분석 - MCP 연동"""
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT symbol, quantity, avg_price 
            FROM portfolio 
            WHERE user_id = ?
        ''', (user_id,))
        
        holdings = cursor.fetchall()
        conn.close()
        
        portfolio_analysis = {
            "user_id": user_id,
            "holdings": [],
            "total_value": 0,
            "total_pnl": 0,
            "risk_score": 0,
            "sector_distribution": {}
        }
        
        for symbol, quantity, avg_price in holdings:
            analysis = self.analyzer.analyze_stock(symbol)
            current_price = analysis.get("current_price", avg_price)
            pnl = (current_price - avg_price) * quantity
            
            portfolio_analysis["holdings"].append({
                "symbol": symbol,
                "quantity": quantity,
                "avg_price": avg_price,
                "current_price": current_price,
                "pnl": pnl,
                "pnl_percent": (pnl / (avg_price * quantity)) * 100,
                "ai_score": analysis.get("ai_score", 50)
            })
            
            portfolio_analysis["total_value"] += current_price * quantity
            portfolio_analysis["total_pnl"] += pnl
        
        # 리스크 점수 계산 (0-100)
        portfolio_analysis["risk_score"] = self._calculate_risk_score(portfolio_analysis["holdings"])
        
        return ComplianceManager.add_disclaimer(portfolio_analysis)
    
    def _calculate_risk_score(self, holdings: List[dict]) -> int:
        """포트폴리오 리스크 점수 계산"""
        if not holdings:
            return 0
        
        # 집중도 리스크 (한 종목이 너무 큰 비중)
        total_value = sum(h["current_price"] * h["quantity"] for h in holdings)
        max_position = max(h["current_price"] * h["quantity"] for h in holdings)
        concentration_risk = (max_position / total_value) * 50
        
        # 변동성 리스크 (간단한 버전)
        volatility_risk = min(len(holdings) * 10, 50)
        
        return min(int(concentration_risk + volatility_risk), 100)

# ============================================================================
# FASTAPI APPLICATION
# ============================================================================

app = FastAPI(
    title="StockPilot AI Analysis API",
    description="AI 기반 주식 시장 분석 도구 - 투자 권유가 아닌 참고 자료",
    version="2.0.0"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 전역 인스턴스
db_manager = DatabaseManager()
analyzer = StockAnalyzer()
mcp_server = StockPilotMCP()

# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "service": "StockPilot AI Analysis",
        "version": "2.0.0",
        "disclaimer": ComplianceManager.DISCLAIMER
    }

@app.get("/api/analysis/{symbol}")
async def get_stock_analysis(symbol: str):
    """개별 종목 분석 - 투자 권유 아님"""
    analysis = analyzer.analyze_stock(symbol.upper())
    return JSONResponse(content=analysis)

@app.get("/api/portfolio/{user_id}")
async def get_portfolio_analysis(user_id: str):
    """포트폴리오 분석"""
    analysis = await mcp_server.get_portfolio_analysis(user_id)
    return JSONResponse(content=analysis)

@app.get("/api/pricing")
async def get_pricing():
    """구독 가격 정보"""
    return {
        "tiers": PricingModel.TIERS,
        "disclaimer": "본 서비스는 분석 도구 이용료이며, 투자자문 수수료가 아닙니다"
    }

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """실시간 데이터 웹소켓"""
    await websocket.accept()
    try:
        while True:
            # 실시간 데이터 전송 (10초마다)
            data = {
                "type": "market_update",
                "timestamp": datetime.now().isoformat(),
                "indicators": {
                    "market_sentiment": np.random.choice(["상승", "하락", "중립"]),
                    "vix": np.random.uniform(15, 30)
                },
                "disclaimer": ComplianceManager.DISCLAIMER
            }
            await websocket.send_json(data)
            await asyncio.sleep(10)
    except WebSocketDisconnect:
        pass

# ============================================================================
# HTML FRONTEND (통합)
# ============================================================================

HTML_CONTENT = """
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>StockPilot - AI 기반 주식 분석 도구</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }
        
        /* 면책조항 배너 */
        .disclaimer-banner {
            background: #fff3cd;
            padding: 10px;
            text-align: center;
            color: #856404;
            font-size: 12px;
            border-bottom: 1px solid #ffeeba;
        }
        
        header {
            background: rgba(255,255,255,0.95);
            padding: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        
        .card {
            background: white;
            border-radius: 12px;
            padding: 20px;
            margin: 20px 0;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        
        .stock-card {
            display: grid;
            grid-template-columns: 1fr auto;
            align-items: center;
            padding: 15px;
            border-left: 4px solid #667eea;
        }
        
        .ai-score {
            font-size: 24px;
            font-weight: bold;
            color: #667eea;
        }
        
        .technical-indicator {
            display: inline-block;
            padding: 5px 10px;
            margin: 5px;
            background: #f0f0f0;
            border-radius: 5px;
            font-size: 12px;
        }
        
        .portfolio-summary {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }
        
        .stat-card {
            text-align: center;
            padding: 15px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-radius: 10px;
        }
        
        .btn {
            padding: 10px 20px;
            background: #667eea;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            transition: all 0.3s;
        }
        
        .btn:hover {
            background: #5a67d8;
            transform: translateY(-2px);
        }
        
        .reference-note {
            font-size: 11px;
            color: #666;
            margin-top: 10px;
            font-style: italic;
        }
        
        /* 가격 플랜 */
        .pricing-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin: 30px 0;
        }
        
        .price-card {
            background: white;
            border-radius: 10px;
            padding: 25px;
            text-align: center;
            position: relative;
            transition: transform 0.3s;
        }
        
        .price-card:hover {
            transform: translateY(-5px);
        }
        
        .price-card.recommended {
            border: 2px solid #667eea;
        }
        
        .price {
            font-size: 36px;
            font-weight: bold;
            color: #667eea;
        }
    </style>
</head>
<body>
    <!-- 면책조항 배너 -->
    <div class="disclaimer-banner">
        본 서비스는 AI 기반 분석 도구입니다. 투자 권유가 아닌 참고 자료이며, 모든 투자 결정과 책임은 이용자에게 있습니다.
    </div>
    
    <header>
        <div class="container">
            <h1>StockPilot</h1>
            <p>AI 기반 주식 시장 분석 도구</p>
        </div>
    </header>
    
    <main class="container">
        <!-- 포트폴리오 요약 -->
        <div class="card">
            <h2>포트폴리오 현황</h2>
            <div class="portfolio-summary">
                <div class="stat-card">
                    <h3>총 평가금액</h3>
                    <p class="value">₩10,234,500</p>
                </div>
                <div class="stat-card">
                    <h3>수익률</h3>
                    <p class="value">+5.23%</p>
                </div>
                <div class="stat-card">
                    <h3>리스크 점수</h3>
                    <p class="value">45/100</p>
                </div>
                <div class="stat-card">
                    <h3>AI 분석 점수</h3>
                    <p class="value">72/100</p>
                </div>
            </div>
        </div>
        
        <!-- 종목 분석 -->
        <div class="card">
            <h2>AI 종목 분석</h2>
            <div id="stock-list">
                <div class="stock-card">
                    <div>
                        <h3>삼성전자</h3>
                        <div>
                            <span class="technical-indicator">RSI: 45</span>
                            <span class="technical-indicator">지지선: 70,000</span>
                            <span class="technical-indicator">저항선: 75,000</span>
                        </div>
                        <p class="reference-note">※ 참고용 정보</p>
                    </div>
                    <div class="ai-score">72</div>
                </div>
            </div>
            <button class="btn" onclick="loadAnalysis()">분석 보기</button>
        </div>
        
        <!-- 가격 플랜 -->
        <div class="card">
            <h2>구독 플랜</h2>
            <div class="pricing-grid">
                <div class="price-card">
                    <h3>무료</h3>
                    <p class="price">₩0</p>
                    <ul style="list-style: none; padding: 20px 0;">
                        <li>✓ 실시간 시세</li>
                        <li>✓ 포트폴리오 관리</li>
                        <li>✓ 기본 차트</li>
                    </ul>
                </div>
                <div class="price-card recommended">
                    <h3>프로</h3>
                    <p class="price">₩49,900</p>
                    <ul style="list-style: none; padding: 20px 0;">
                        <li>✓ 무제한 AI 분석</li>
                        <li>✓ 기술적 지표</li>
                        <li>✓ 패턴 인식</li>
                    </ul>
                </div>
                <div class="price-card">
                    <h3>프리미엄</h3>
                    <p class="price">₩99,900</p>
                    <ul style="list-style: none; padding: 20px 0;">
                        <li>✓ 모든 기능</li>
                        <li>✓ 실시간 알림</li>
                        <li>✓ API 접근</li>
                    </ul>
                </div>
            </div>
        </div>
    </main>
    
    <script>
        // WebSocket 연결
        let ws = null;
        
        function connectWebSocket() {
            ws = new WebSocket('ws://localhost:8000/ws');
            
            ws.onmessage = function(event) {
                const data = JSON.parse(event.data);
                console.log('Market update:', data);
                updateUI(data);
            };
            
            ws.onerror = function(error) {
                console.error('WebSocket error:', error);
            };
        }
        
        function loadAnalysis() {
            fetch('/api/analysis/AAPL')
                .then(response => response.json())
                .then(data => {
                    console.log('Analysis:', data);
                    alert('AI 분석 완료: ' + data.disclaimer);
                });
        }
        
        function updateUI(data) {
            // UI 업데이트 로직
            console.log('Updating UI with:', data);
        }
        
        // 페이지 로드 시 WebSocket 연결
        window.onload = function() {
            connectWebSocket();
        };
    </script>
</body>
</html>
"""

@app.get("/app", response_class=HTMLResponse)
async def get_app():
    """통합 웹 앱 제공"""
    return HTML_CONTENT

# ============================================================================
# MCP FLOW INTEGRATION
# ============================================================================

class StockPilotFlow:
    """mcp-map Flow 통합"""
    
    def __init__(self):
        self.mcp = StockPilotMCP()
        self.analyzer = StockAnalyzer()
    
    async def daily_portfolio_analysis(self, user_id: str):
        """매일 포트폴리오 분석 Flow"""
        # 1. 포트폴리오 가져오기
        portfolio = await self.mcp.get_portfolio_analysis(user_id)
        
        # 2. 리스크 체크
        if portfolio["risk_score"] > 70:
            await self.send_risk_alert(user_id, portfolio)
        
        # 3. 리포트 생성
        report = self.generate_daily_report(portfolio)
        
        # 4. 저장 및 알림
        await self.save_report(user_id, report)
        
        return report
    
    async def market_monitoring_flow(self):
        """실시간 시장 모니터링 Flow"""
        watchlist = ["AAPL", "MSFT", "GOOGL", "TSLA", "NVDA"]
        
        while True:
            for symbol in watchlist:
                analysis = self.analyzer.analyze_stock(symbol)
                
                # 특이사항 감지
                if analysis["technical_indicators"]["rsi"] < 30:
                    await self.send_oversold_alert(symbol, analysis)
                elif analysis["technical_indicators"]["rsi"] > 70:
                    await self.send_overbought_alert(symbol, analysis)
            
            await asyncio.sleep(600)  # 10분마다
    
    def generate_daily_report(self, portfolio: dict) -> str:
        """일일 리포트 생성"""
        report = f"""
        === StockPilot Daily Report ===
        Date: {datetime.now().strftime('%Y-%m-%d')}
        
        Portfolio Summary:
        - Total Value: ₩{portfolio['total_value']:,.0f}
        - Total P&L: ₩{portfolio['total_pnl']:,.0f}
        - Risk Score: {portfolio['risk_score']}/100
        
        Top Performers:
        {self._format_top_performers(portfolio['holdings'])}
        
        {ComplianceManager.DISCLAIMER}
        """
        return report
    
    def _format_top_performers(self, holdings: List[dict]) -> str:
        """상위 종목 포맷팅"""
        sorted_holdings = sorted(holdings, key=lambda x: x['pnl_percent'], reverse=True)[:3]
        result = ""
        for h in sorted_holdings:
            result += f"- {h['symbol']}: {h['pnl_percent']:.2f}%\\n"
        return result
    
    async def send_risk_alert(self, user_id: str, portfolio: dict):
        """리스크 알림"""
        # 실제로는 이메일/푸시 알림
        logging.warning(f"High risk alert for user {user_id}: {portfolio['risk_score']}")
    
    async def send_oversold_alert(self, symbol: str, analysis: dict):
        """과매도 알림"""
        logging.info(f"Oversold alert: {symbol} RSI={analysis['technical_indicators']['rsi']}")
    
    async def send_overbought_alert(self, symbol: str, analysis: dict):
        """과매수 알림"""
        logging.info(f"Overbought alert: {symbol} RSI={analysis['technical_indicators']['rsi']}")
    
    async def save_report(self, user_id: str, report: str):
        """리포트 저장"""
        # 실제로는 DB 저장
        logging.info(f"Report saved for user {user_id}")

# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """메인 실행 함수"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 서버 실행
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    )

if __name__ == "__main__":
    print("""
    ╔══════════════════════════════════════════╗
    ║        StockPilot Complete App          ║
    ║    AI 기반 주식 시장 분석 도구          ║
    ║    (투자자문업 규제 준수 버전)          ║
    ╚══════════════════════════════════════════╝
    
    Starting server on http://localhost:8000
    Web App: http://localhost:8000/app
    API Docs: http://localhost:8000/docs
    
    ⚠️  본 서비스는 투자 권유가 아닌 분석 도구입니다.
    """)
    
    main()
