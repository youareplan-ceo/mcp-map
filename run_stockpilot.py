#!/usr/bin/env python3
"""
StockPilot 통합 실행 스크립트
백테스팅 + MCP + 수익 극대화 엔진 통합
"""

import os
import sys
import json
import asyncio
import subprocess
from datetime import datetime
from pathlib import Path

# 프로젝트 루트 설정
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from mcp.profit_maximizer import ProfitMaximizer

class StockPilotOrchestrator:
    """전체 시스템 오케스트레이터"""
    
    def __init__(self):
        self.profit_engine = ProfitMaximizer()
        self.backtest_results = {}
        self.active_signals = {}
    
    def run_backtesting(self):
        """백테스팅 실행"""
        print("🔄 백테스팅 시작...")
        
        # profit_strategy_finder.py 실행
        result = subprocess.run(
            ["python", "profit_strategy_finder.py"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            # 결과 파싱
            try:
                output = json.loads(result.stdout)
                self.backtest_results = output
                print(f"✅ 백테스팅 완료: 승률 {output['win_rate']:.1%}")
                
                # 결과 저장
                with open("data/backtest_results.json", "w") as f:
                    json.dump(output, f, indent=2)
                    
            except json.JSONDecodeError:
                print("⚠️ 백테스팅 결과 파싱 실패")
        else:
            print(f"❌ 백테스팅 실패: {result.stderr}")
    
    def run_mcp_flow(self, flow_name: str = "realtime_profit_signal"):
        """MCP Flow 실행"""
        print(f"🔄 MCP Flow 실행: {flow_name}")
        
        # flow 실행
        result = subprocess.run(
            ["bin/flow", flow_name],
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT
        )
        
        if result.returncode == 0:
            print(f"✅ Flow 완료")
            return result.stdout
        else:
            print(f"❌ Flow 실패: {result.stderr}")
            return None
    
    async def generate_signals(self, symbols: list):
        """실시간 시그널 생성"""
        print(f"🎯 시그널 생성 시작: {len(symbols)}개 종목")
        
        signals = []
        for symbol in symbols:
            # 수익 극대화 엔진으로 처리
            response = self.profit_engine.process_user_request(
                user_id="system",
                symbol=symbol
            )
            
            # 고득점만 저장
            if response["ai_score"] >= 75:
                signals.append(response)
                self.active_signals[symbol] = response
                
                print(f"  📊 {symbol}: {response['ai_score']}점 - {response['signal']}")
        
        return signals
    
    async def validate_yesterday_signals(self):
        """어제 시그널 검증"""
        print("🔍 어제 시그널 검증...")
        
        # 실제 수익률 체크
        self.profit_engine.validator.validate_signals(24)
        
        # 성과 리포트
        validated_count = 0
        success_count = 0
        
        # TODO: DB에서 검증 결과 조회
        
        print(f"✅ 검증 완료: {success_count}/{validated_count} 성공")
    
    async def run_daily_cycle(self):
        """일일 사이클 실행"""
        print("\n" + "="*50)
        print(f"📅 일일 사이클 시작: {datetime.now()}")
        print("="*50)
        
        # 1. 백테스팅 (주 1회)
        if datetime.now().weekday() == 0:  # 월요일
            self.run_backtesting()
        
        # 2. 어제 시그널 검증
        await self.validate_yesterday_signals()
        
        # 3. 종목 리스트 (실제로는 DB나 API에서)
        test_symbols = [
            "AAPL", "MSFT", "GOOGL", "TSLA", "NVDA",
            "005930.KS", "000660.KS", "035420.KS"
        ]
        
        # 4. 시그널 생성
        signals = await self.generate_signals(test_symbols)
        
        # 5. 고득점 시그널 알림
        high_score_signals = [s for s in signals if s["ai_score"] >= 85]
        if high_score_signals:
            print(f"\n🚨 강력 시그널 {len(high_score_signals)}개:")
            for signal in high_score_signals:
                print(f"  - {signal['symbol']}: {signal['message']}")
        
        # 6. 일일 작업
        self.profit_engine.run_daily_tasks()
        
        # 7. 결과 저장
        with open(f"logs/daily_signals_{datetime.now().strftime('%Y%m%d')}.json", "w") as f:
            json.dump({
                "date": datetime.now().isoformat(),
                "signals": signals,
                "high_score_count": len(high_score_signals),
                "backtest_results": self.backtest_results
            }, f, indent=2)
        
        print("\n✅ 일일 사이클 완료")
    
    async def monitor_realtime(self):
        """실시간 모니터링"""
        print("🔴 실시간 모니터링 시작...")
        
        while True:
            try:
                # 10분마다 체크
                await asyncio.sleep(600)
                
                # 긴급 종목 체크 (변동성 큰 종목)
                urgent_symbols = ["NVDA", "TSLA"]  # 실제로는 동적 선택
                
                signals = await self.generate_signals(urgent_symbols)
                
                # 95점 이상 즉시 알림
                for signal in signals:
                    if signal["ai_score"] >= 95:
                        print(f"⚡ 긴급 시그널: {signal['symbol']} - {signal['message']}")
                        # TODO: 실제 알림 전송
                
            except KeyboardInterrupt:
                print("\n🛑 모니터링 중단")
                break
            except Exception as e:
                print(f"❌ 모니터링 오류: {e}")

async def main():
    """메인 실행"""
    orchestrator = StockPilotOrchestrator()
    
    print("""
    ╔══════════════════════════════════════════╗
    ║     StockPilot 수익 극대화 시스템       ║
    ║          실전 통합 버전 v2.0             ║
    ╚══════════════════════════════════════════╝
    """)
    
    # 옵션 선택
    print("실행 모드 선택:")
    print("1. 일일 사이클 실행")
    print("2. 실시간 모니터링")
    print("3. 백테스팅만 실행")
    print("4. MCP Flow 테스트")
    
    choice = input("선택 (1-4): ")
    
    if choice == "1":
        await orchestrator.run_daily_cycle()
    elif choice == "2":
        await orchestrator.monitor_realtime()
    elif choice == "3":
        orchestrator.run_backtesting()
    elif choice == "4":
        orchestrator.run_mcp_flow()
    else:
        print("잘못된 선택")

if __name__ == "__main__":
    # 로그 디렉토리 생성
    os.makedirs("logs", exist_ok=True)
    os.makedirs("data", exist_ok=True)
    
    # 실행
    asyncio.run(main())
