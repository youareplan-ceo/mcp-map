"""
StockPilot 종이 거래 성과 분석기
실시간으로 수익률 분석하고 전략 개선점 찾기
"""

import os
import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple
import statistics

class PaperTradingAnalyzer:
    """종이 거래 성과 실시간 분석"""
    
    def __init__(self, db_path: str = "trades.db"):
        self.db_path = db_path
        self.analysis_results = {}
        
    def connect_db(self):
        """거래 DB 연결"""
        return sqlite3.connect(self.db_path)
    
    def analyze_performance(self) -> Dict:
        """전체 성과 분석"""
        conn = self.connect_db()
        cursor = conn.cursor()
        
        # 1. 전체 수익률
        cursor.execute("""
            SELECT 
                COUNT(*) as total_trades,
                SUM(CASE WHEN profit_loss > 0 THEN 1 ELSE 0 END) as wins,
                SUM(CASE WHEN profit_loss < 0 THEN 1 ELSE 0 END) as losses,
                AVG(profit_loss) as avg_profit,
                MAX(profit_loss) as max_profit,
                MIN(profit_loss) as min_loss
            FROM trades
            WHERE timestamp > datetime('now', '-30 days')
        """)
        
        stats = cursor.fetchone()
        total, wins, losses, avg_profit, max_profit, min_loss = stats
        
        win_rate = (wins / total * 100) if total > 0 else 0
        
        # 2. AI 점수별 성과
        cursor.execute("""
            SELECT 
                CASE 
                    WHEN ai_score >= 90 THEN '90+'
                    WHEN ai_score >= 80 THEN '80-89'
                    WHEN ai_score >= 70 THEN '70-79'
                    ELSE '70 미만'
                END as score_range,
                COUNT(*) as trades,
                AVG(profit_loss) as avg_profit,
                SUM(CASE WHEN profit_loss > 0 THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as win_rate
            FROM trades
            WHERE action = 'BUY'
            GROUP BY score_range
            ORDER BY ai_score DESC
        """)
        
        score_performance = cursor.fetchall()
        
        # 3. 시간대별 성과
        cursor.execute("""
            SELECT 
                strftime('%H', timestamp) as hour,
                COUNT(*) as trades,
                AVG(profit_loss) as avg_profit
            FROM trades
            GROUP BY hour
            ORDER BY avg_profit DESC
        """)
        
        time_performance = cursor.fetchall()
        
        # 4. 종목별 성과
        cursor.execute("""
            SELECT 
                symbol,
                COUNT(*) as trades,
                SUM(profit_loss) as total_profit,
                AVG(profit_loss) as avg_profit,
                SUM(CASE WHEN profit_loss > 0 THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as win_rate
            FROM trades
            GROUP BY symbol
            ORDER BY total_profit DESC
            LIMIT 10
        """)
        
        symbol_performance = cursor.fetchall()
        
        # 5. 매매 사유별 성과
        cursor.execute("""
            SELECT 
                reason,
                COUNT(*) as count,
                AVG(profit_loss) as avg_profit
            FROM trades
            WHERE action = 'SELL'
            GROUP BY reason
        """)
        
        reason_performance = cursor.fetchall()
        
        conn.close()
        
        return {
            "overall": {
                "total_trades": total or 0,
                "win_rate": round(win_rate, 2),
                "avg_profit": round(avg_profit or 0, 2),
                "max_profit": round(max_profit or 0, 2),
                "min_loss": round(min_loss or 0, 2),
                "profit_factor": abs(max_profit / min_loss) if min_loss else 0
            },
            "by_ai_score": score_performance,
            "by_hour": time_performance[:5],  # 상위 5개 시간대
            "by_symbol": symbol_performance,
            "by_reason": reason_performance
        }
    
    def calculate_mdd(self) -> float:
        """최대 낙폭(MDD) 계산"""
        conn = self.connect_db()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT timestamp, SUM(profit_loss) OVER (ORDER BY timestamp) as cumulative_pl
            FROM trades
            ORDER BY timestamp
        """)
        
        results = cursor.fetchall()
        conn.close()
        
        if not results:
            return 0
        
        # MDD 계산
        peak = 0
        mdd = 0
        
        for _, cumulative_pl in results:
            if cumulative_pl > peak:
                peak = cumulative_pl
            drawdown = (peak - cumulative_pl) / peak if peak > 0 else 0
            mdd = max(mdd, drawdown)
        
        return round(mdd * 100, 2)
    
    def find_best_strategy(self) -> Dict:
        """최고 수익 전략 찾기"""
        conn = self.connect_db()
        cursor = conn.cursor()
        
        # AI 점수 + RSI 조합별 성과
        cursor.execute("""
            SELECT 
                ai_score,
                COUNT(*) as trades,
                AVG(profit_loss) as avg_profit,
                SUM(profit_loss) as total_profit
            FROM trades
            WHERE action = 'BUY' AND ai_score >= 70
            GROUP BY ai_score
            HAVING COUNT(*) >= 5
            ORDER BY avg_profit DESC
            LIMIT 1
        """)
        
        best_score = cursor.fetchone()
        conn.close()
        
        if best_score:
            return {
                "best_ai_score": best_score[0],
                "trades": best_score[1],
                "avg_profit": round(best_score[2], 2),
                "total_profit": round(best_score[3], 2)
            }
        return {}
    
    def generate_recommendations(self, analysis: Dict) -> List[str]:
        """개선 추천사항 생성"""
        recommendations = []
        
        # 승률 기반 추천
        win_rate = analysis["overall"]["win_rate"]
        if win_rate < 50:
            recommendations.append("⚠️ 승률 50% 미만: AI 점수 임계값을 85점으로 상향 조정 필요")
        elif win_rate > 70:
            recommendations.append("✅ 높은 승률: 포지션 크기를 10% 증가 가능")
        
        # AI 점수별 성과 기반
        for score_range, trades, avg_profit, score_win_rate in analysis["by_ai_score"]:
            if score_range == "90+" and avg_profit < 0:
                recommendations.append(f"🔴 90+ 점수 전략 재검토 필요 (평균 손실: {avg_profit}%)")
            elif score_range == "80-89" and score_win_rate > 75:
                recommendations.append(f"🟢 80-89점 구간 우수 (승률: {score_win_rate:.1f}%)")
        
        # 시간대 기반
        if analysis["by_hour"]:
            best_hour = analysis["by_hour"][0]
            recommendations.append(f"⏰ 최적 거래 시간: {best_hour[0]}시 (평균 수익: {best_hour[2]:.2f}%)")
        
        # MDD 기반
        mdd = self.calculate_mdd()
        if mdd > 20:
            recommendations.append(f"⚠️ 높은 MDD ({mdd}%): 손절 기준을 3%로 강화 필요")
        
        # 종목 집중도
        if analysis["by_symbol"]:
            top_symbol = analysis["by_symbol"][0]
            if top_symbol[2] > analysis["overall"]["avg_profit"] * 10:
                recommendations.append(f"💎 {top_symbol[0]} 집중 투자 고려 (누적 수익: {top_symbol[2]:.2f}%)")
        
        return recommendations
    
    def create_report(self) -> str:
        """성과 리포트 생성"""
        analysis = self.analyze_performance()
        mdd = self.calculate_mdd()
        best_strategy = self.find_best_strategy()
        recommendations = self.generate_recommendations(analysis)
        
        report = f"""
════════════════════════════════════════════════════════
       StockPilot 종이 거래 성과 분석 리포트
       {datetime.now().strftime('%Y-%m-%d %H:%M')}
════════════════════════════════════════════════════════

📊 전체 성과
────────────────────────────────────────────────────────
• 총 거래 횟수: {analysis['overall']['total_trades']}회
• 승률: {analysis['overall']['win_rate']}%
• 평균 수익률: {analysis['overall']['avg_profit']}%
• 최대 수익: +{analysis['overall']['max_profit']}%
• 최대 손실: {analysis['overall']['min_loss']}%
• Profit Factor: {analysis['overall']['profit_factor']:.2f}
• 최대 낙폭(MDD): {mdd}%

🎯 AI 점수별 성과
────────────────────────────────────────────────────────"""
        
        for score_range, trades, avg_profit, win_rate in analysis["by_ai_score"]:
            report += f"\n• {score_range}점: {trades}회, 평균 {avg_profit:.2f}%, 승률 {win_rate:.1f}%"
        
        report += f"""

🏆 최고 수익 전략
────────────────────────────────────────────────────────
• AI 점수: {best_strategy.get('best_ai_score', 'N/A')}점
• 평균 수익: {best_strategy.get('avg_profit', 0)}%
• 누적 수익: {best_strategy.get('total_profit', 0)}%

📈 TOP 5 수익 종목
────────────────────────────────────────────────────────"""
        
        for symbol, trades, total_profit, avg_profit, win_rate in analysis["by_symbol"][:5]:
            report += f"\n• {symbol}: {trades}회, 누적 {total_profit:.2f}%, 승률 {win_rate:.1f}%"
        
        report += f"""

💡 AI 추천사항
────────────────────────────────────────────────────────"""
        
        for i, rec in enumerate(recommendations, 1):
            report += f"\n{i}. {rec}"
        
        report += f"""

⚖️ 매도 사유 분석
────────────────────────────────────────────────────────"""
        
        for reason, count, avg_profit in analysis["by_reason"]:
            report += f"\n• {reason}: {count}회, 평균 {avg_profit:.2f}%"
        
        report += f"""

════════════════════════════════════════════════════════
💰 결론: """
        
        if analysis['overall']['win_rate'] > 60 and analysis['overall']['avg_profit'] > 0:
            report += "수익성 있는 전략 ✅ - 실전 투자 고려 가능"
        else:
            report += "전략 개선 필요 ⚠️ - 추가 백테스팅 권장"
        
        report += "\n════════════════════════════════════════════════════════\n"
        
        return report

def main():
    """메인 실행"""
    print("🔍 종이 거래 성과 분석 시작...\n")
    
    # trades.db 파일 체크
    if not os.path.exists("trades.db"):
        print("⚠️ trades.db 파일이 없습니다. 종이 거래를 먼저 실행하세요.")
        
        # 더미 DB 생성 (테스트용)
        conn = sqlite3.connect("trades.db")
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY,
                timestamp DATETIME,
                symbol TEXT,
                action TEXT,
                quantity INTEGER,
                price REAL,
                reason TEXT,
                ai_score INTEGER,
                profit_loss REAL
            )
        """)
        
        # 더미 데이터 삽입
        import random
        symbols = ["AAPL", "NVDA", "TSLA", "GOOGL", "MSFT"]
        reasons = ["AI_SIGNAL", "STOP_LOSS", "TAKE_PROFIT"]
        
        for i in range(100):
            cursor.execute("""
                INSERT INTO trades 
                (timestamp, symbol, action, quantity, price, reason, ai_score, profit_loss)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                datetime.now() - timedelta(days=random.randint(0, 30)),
                random.choice(symbols),
                random.choice(["BUY", "SELL"]),
                random.randint(1, 10),
                random.uniform(100, 1000),
                random.choice(reasons),
                random.randint(60, 95),
                random.uniform(-5, 15)
            ))
        
        conn.commit()
        conn.close()
        print("✅ 테스트용 더미 데이터 생성 완료\n")
    
    # 분석 실행
    analyzer = PaperTradingAnalyzer()
    
    # 리포트 생성
    report = analyzer.create_report()
    print(report)
    
    # 파일로 저장
    os.makedirs("reports", exist_ok=True)
    report_file = f"reports/analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\n📁 리포트 저장: {report_file}")
    
    # JSON 형식으로도 저장
    analysis_data = analyzer.analyze_performance()
    analysis_data["mdd"] = analyzer.calculate_mdd()
    analysis_data["best_strategy"] = analyzer.find_best_strategy()
    analysis_data["recommendations"] = analyzer.generate_recommendations(analysis_data)
    
    json_file = f"reports/analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(analysis_data, f, indent=2, ensure_ascii=False)
    
    print(f"📁 JSON 데이터: {json_file}")

if __name__ == "__main__":
    main()
