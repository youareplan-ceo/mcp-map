"""
StockPilot 실시간 성과 대시보드 API
종이 거래 성과를 실시간으로 모니터링
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import json
import sqlite3
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List
import os

app = FastAPI(
    title="StockPilot Performance Dashboard",
    description="실시간 종이 거래 성과 모니터링",
    version="1.0.0"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class RealtimeMonitor:
    """실시간 모니터링 클래스"""
    
    def __init__(self):
        self.active_positions = {}
        self.today_trades = []
        self.current_profit = 0
        
    def get_portfolio_status(self) -> Dict:
        """포트폴리오 현황"""
        conn = sqlite3.connect("trades.db")
        cursor = conn.cursor()
        
        # 현재 보유 종목 (매수 - 매도)
        cursor.execute("""
            SELECT 
                symbol,
                SUM(CASE WHEN action = 'BUY' THEN quantity ELSE -quantity END) as net_qty,
                AVG(CASE WHEN action = 'BUY' THEN price ELSE NULL END) as avg_price
            FROM trades
            GROUP BY symbol
            HAVING net_qty > 0
        """)
        
        positions = cursor.fetchall()
        
        # 오늘 거래
        cursor.execute("""
            SELECT * FROM trades
            WHERE DATE(timestamp) = DATE('now')
            ORDER BY timestamp DESC
            LIMIT 10
        """)
        
        today = cursor.fetchall()
        
        # 실시간 수익률
        cursor.execute("""
            SELECT 
                SUM(profit_loss) as total_profit,
                COUNT(CASE WHEN profit_loss > 0 THEN 1 END) as wins,
                COUNT(CASE WHEN profit_loss < 0 THEN 1 END) as losses
            FROM trades
            WHERE DATE(timestamp) = DATE('now')
        """)
        
        today_stats = cursor.fetchone()
        
        conn.close()
        
        return {
            "positions": positions,
            "today_trades": today,
            "today_profit": today_stats[0] or 0,
            "today_wins": today_stats[1] or 0,
            "today_losses": today_stats[2] or 0,
            "timestamp": datetime.now().isoformat()
        }
    
    def get_hourly_performance(self) -> List:
        """시간별 성과"""
        conn = sqlite3.connect("trades.db")
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                strftime('%H:00', timestamp) as hour,
                SUM(profit_loss) as profit,
                COUNT(*) as trades
            FROM trades
            WHERE DATE(timestamp) = DATE('now')
            GROUP BY strftime('%H', timestamp)
            ORDER BY hour
        """)
        
        hourly = cursor.fetchall()
        conn.close()
        
        return [
            {"hour": h, "profit": p or 0, "trades": t}
            for h, p, t in hourly
        ]

monitor = RealtimeMonitor()

@app.get("/")
async def root():
    """루트 페이지"""
    return {"message": "StockPilot Performance Dashboard API"}

@app.get("/api/portfolio")
async def get_portfolio():
    """포트폴리오 현황 API"""
    return JSONResponse(content=monitor.get_portfolio_status())

@app.get("/api/performance/hourly")
async def get_hourly():
    """시간별 성과 API"""
    return JSONResponse(content=monitor.get_hourly_performance())

@app.get("/api/analysis")
async def get_analysis():
    """성과 분석 API"""
    from paper_trading_analyzer import PaperTradingAnalyzer
    
    analyzer = PaperTradingAnalyzer()
    analysis = analyzer.analyze_performance()
    analysis["mdd"] = analyzer.calculate_mdd()
    analysis["best_strategy"] = analyzer.find_best_strategy()
    
    return JSONResponse(content=analysis)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """실시간 데이터 웹소켓"""
    await websocket.accept()
    try:
        while True:
            # 5초마다 업데이트
            data = monitor.get_portfolio_status()
            await websocket.send_json(data)
            await asyncio.sleep(5)
    except WebSocketDisconnect:
        pass

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    """웹 대시보드"""
    return """
<!DOCTYPE html>
<html>
<head>
    <title>StockPilot 성과 대시보드</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
        }
        .container {
            max-width: 1400px;
            margin: 0 auto;
        }
        h1 {
            text-align: center;
            margin-bottom: 30px;
            font-size: 2.5em;
        }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .stat-card {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            padding: 25px;
            text-align: center;
        }
        .stat-value {
            font-size: 2.5em;
            font-weight: bold;
            margin: 10px 0;
        }
        .stat-label {
            font-size: 0.9em;
            opacity: 0.8;
        }
        .positive { color: #4ade80; }
        .negative { color: #f87171; }
        .portfolio-table {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            padding: 20px;
            margin-bottom: 20px;
        }
        table {
            width: 100%;
            border-collapse: collapse;
        }
        th, td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }
        th {
            font-weight: bold;
            opacity: 0.9;
        }
        .trades-feed {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            padding: 20px;
            max-height: 400px;
            overflow-y: auto;
        }
        .trade-item {
            padding: 10px;
            margin: 5px 0;
            background: rgba(255, 255, 255, 0.05);
            border-radius: 8px;
            display: flex;
            justify-content: space-between;
        }
        .buy { border-left: 3px solid #4ade80; }
        .sell { border-left: 3px solid #f87171; }
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 StockPilot 실시간 성과 대시보드</h1>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-label">오늘 수익률</div>
                <div class="stat-value positive" id="today-profit">+0.00%</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">승률</div>
                <div class="stat-value" id="win-rate">0%</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">거래 횟수</div>
                <div class="stat-value" id="trade-count">0</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">보유 종목</div>
                <div class="stat-value" id="position-count">0</div>
            </div>
        </div>
        
        <div class="portfolio-table">
            <h2>💼 현재 포트폴리오</h2>
            <table>
                <thead>
                    <tr>
                        <th>종목</th>
                        <th>수량</th>
                        <th>평균가</th>
                        <th>현재가</th>
                        <th>수익률</th>
                    </tr>
                </thead>
                <tbody id="portfolio-tbody">
                    <!-- 동적 생성 -->
                </tbody>
            </table>
        </div>
        
        <div class="trades-feed">
            <h2>📈 실시간 거래 내역</h2>
            <div id="trades-list">
                <!-- 동적 생성 -->
            </div>
        </div>
    </div>
    
    <script>
        const ws = new WebSocket('ws://localhost:8000/ws');
        
        ws.onmessage = function(event) {
            const data = JSON.parse(event.data);
            updateDashboard(data);
        };
        
        function updateDashboard(data) {
            // 통계 업데이트
            const todayProfit = data.today_profit || 0;
            document.getElementById('today-profit').textContent = 
                todayProfit >= 0 ? `+${todayProfit.toFixed(2)}%` : `${todayProfit.toFixed(2)}%`;
            document.getElementById('today-profit').className = 
                todayProfit >= 0 ? 'stat-value positive' : 'stat-value negative';
            
            const winRate = data.today_wins / (data.today_wins + data.today_losses) * 100 || 0;
            document.getElementById('win-rate').textContent = `${winRate.toFixed(1)}%`;
            document.getElementById('trade-count').textContent = 
                data.today_trades ? data.today_trades.length : 0;
            document.getElementById('position-count').textContent = 
                data.positions ? data.positions.length : 0;
            
            // 포트폴리오 업데이트
            const tbody = document.getElementById('portfolio-tbody');
            tbody.innerHTML = '';
            if (data.positions) {
                data.positions.forEach(pos => {
                    const row = tbody.insertRow();
                    row.innerHTML = `
                        <td>${pos[0]}</td>
                        <td>${pos[1]}</td>
                        <td>$${pos[2]?.toFixed(2) || 'N/A'}</td>
                        <td>-</td>
                        <td>-</td>
                    `;
                });
            }
            
            // 거래 내역 업데이트
            const tradesList = document.getElementById('trades-list');
            tradesList.innerHTML = '';
            if (data.today_trades) {
                data.today_trades.forEach(trade => {
                    const div = document.createElement('div');
                    div.className = `trade-item ${trade[3].toLowerCase()}`;
                    div.innerHTML = `
                        <span>${new Date(trade[1]).toLocaleTimeString()} - ${trade[2]} ${trade[3]}</span>
                        <span>${trade[4]}주 @ $${trade[5]}</span>
                    `;
                    tradesList.appendChild(div);
                });
            }
        }
        
        // 초기 데이터 로드
        fetch('/api/portfolio')
            .then(res => res.json())
            .then(data => updateDashboard(data));
            
        // 분석 데이터 주기적 업데이트
        setInterval(() => {
            fetch('/api/analysis')
                .then(res => res.json())
                .then(analysis => {
                    console.log('Analysis:', analysis);
                });
        }, 30000); // 30초마다
    </script>
</body>
</html>
"""

if __name__ == "__main__":
    import uvicorn
    
    print("""
    ╔══════════════════════════════════════════════╗
    ║     StockPilot 성과 대시보드 서버 시작       ║
    ╚══════════════════════════════════════════════╝
    
    🌐 웹 대시보드: http://localhost:8001/dashboard
    📡 API: http://localhost:8001/api/portfolio
    🔌 WebSocket: ws://localhost:8001/ws
    """)
    
    uvicorn.run(app, host="0.0.0.0", port=8001)
