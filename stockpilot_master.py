#!/usr/bin/env python3
"""
StockPilot 마스터 컨트롤
모든 시스템 통합 관리
"""

import os
import sys
import subprocess
import time
import signal
from datetime import datetime
from pathlib import Path
import psutil

class StockPilotMaster:
    """전체 시스템 관리자"""
    
    def __init__(self):
        self.processes = {}
        self.running = False
        
    def check_process(self, name: str) -> bool:
        """프로세스 실행 확인"""
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmdline = ' '.join(proc.info['cmdline'] or [])
                if name in cmdline:
                    return True
            except:
                pass
        return False
    
    def start_component(self, name: str, command: str):
        """컴포넌트 시작"""
        if name in self.processes and self.processes[name].poll() is None:
            print(f"✅ {name} 이미 실행 중")
            return
        
        print(f"🚀 {name} 시작 중...")
        process = subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        self.processes[name] = process
        time.sleep(2)  # 시작 대기
        
        if process.poll() is None:
            print(f"✅ {name} 시작 완료 (PID: {process.pid})")
        else:
            print(f"❌ {name} 시작 실패")
    
    def stop_component(self, name: str):
        """컴포넌트 중지"""
        if name in self.processes:
            process = self.processes[name]
            if process.poll() is None:
                process.terminate()
                process.wait(timeout=5)
                print(f"🛑 {name} 중지됨")
    
    def start_all(self):
        """전체 시스템 시작"""
        print("\n" + "="*60)
        print("     StockPilot 전체 시스템 시작")
        print("="*60 + "\n")
        
        # 1. 실시간 데이터 수집기
        self.start_component(
            "실시간 수집기",
            "python realtime_data_collector.py"
        )
        
        # 2. 백테스팅 스케줄러
        self.start_component(
            "백테스팅 스케줄러",
            "python daily_strategy_scheduler.py"
        )
        
        # 3. 종이 거래 시뮬레이터
        if os.path.exists("auto_paper_trader.py"):
            self.start_component(
                "종이 거래",
                "python auto_paper_trader.py --initial 10000000"
            )
        
        # 4. 모니터링 대시보드
        self.start_component(
            "모니터링 대시보드",
            "python monitor_dashboard.py"
        )
        
        # 5. 성과 대시보드 API
        self.start_component(
            "성과 대시보드",
            "python performance_dashboard.py"
        )
        
        # 6. StockPilot 메인 앱
        if os.path.exists("stockpilot_complete_app.py"):
            self.start_component(
                "StockPilot 앱",
                "python stockpilot_complete_app.py"
            )
        
        self.running = True
        print("\n✅ 모든 시스템 시작 완료!")
        self.show_status()
    
    def stop_all(self):
        """전체 시스템 중지"""
        print("\n🛑 시스템 종료 중...")
        for name in list(self.processes.keys()):
            self.stop_component(name)
        self.running = False
        print("✅ 모든 시스템 종료 완료")
    
    def show_status(self):
        """시스템 상태 표시"""
        print("\n" + "="*60)
        print("     시스템 상태")
        print("="*60)
        
        components = [
            ("실시간 수집기", "realtime_data_collector.py"),
            ("백테스팅", "daily_strategy_scheduler.py"),
            ("종이 거래", "auto_paper_trader.py"),
            ("모니터링", "monitor_dashboard.py"),
            ("성과 대시보드", "performance_dashboard.py"),
            ("메인 앱", "stockpilot_complete_app.py")
        ]
        
        for name, script in components:
            if self.check_process(script):
                print(f"✅ {name}: 실행 중")
            else:
                print(f"⭕ {name}: 중지됨")
        
        print("\n📊 접속 URL:")
        print("• 모니터링: http://localhost:8000/app")
        print("• 성과 대시보드: http://localhost:8001/dashboard")
        print("• API 문서: http://localhost:8000/docs")
        print("="*60)
    
    def show_logs(self):
        """최근 로그 표시"""
        log_files = [
            f"logs/collector_{datetime.now().strftime('%Y%m%d')}.log",
            f"logs/realtime_monitor.log",
            "logs/trades.log"
        ]
        
        print("\n" + "="*60)
        print("     최근 로그")
        print("="*60)
        
        for log_file in log_files:
            if os.path.exists(log_file):
                print(f"\n📄 {log_file}:")
                with open(log_file, 'r') as f:
                    lines = f.readlines()
                    for line in lines[-5:]:  # 최근 5줄
                        print(f"  {line.strip()}")
    
    def check_data(self):
        """데이터 상태 확인"""
        print("\n" + "="*60)
        print("     데이터 상태")
        print("="*60)
        
        # 실시간 데이터
        today = datetime.now().strftime("%Y%m%d")
        realtime_path = Path(f"data/realtime/{today}")
        if realtime_path.exists():
            files = list(realtime_path.glob("*.json"))
            print(f"📁 실시간 데이터: {len(files)}개 종목")
        else:
            print("⚠️ 오늘 실시간 데이터 없음")
        
        # 백테스팅 결과
        if os.path.exists("data/backtest_results.json"):
            import json
            with open("data/backtest_results.json", 'r') as f:
                results = json.load(f)
                print(f"📊 백테스팅: 승률 {results.get('win_rate', 0)*100:.1f}%")
        
        # 거래 DB
        if os.path.exists("trades.db"):
            import sqlite3
            conn = sqlite3.connect("trades.db")
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM trades")
            count = cursor.fetchone()[0]
            conn.close()
            print(f"💼 종이 거래: {count}건")
        
        print("="*60)

def signal_handler(signum, frame):
    """시그널 핸들러"""
    print("\n\n⚠️ 종료 신호 감지...")
    master.stop_all()
    sys.exit(0)

def main():
    """메인 실행"""
    global master
    master = StockPilotMaster()
    
    # 시그널 핸들러 등록
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    print("""
    ╔══════════════════════════════════════════════════════╗
    ║         StockPilot 마스터 컨트롤 v2.0               ║
    ║         AI 기반 주식 수익 극대화 시스템             ║
    ╚══════════════════════════════════════════════════════╝
    """)
    
    while True:
        print("\n명령어:")
        print("1. 전체 시작")
        print("2. 전체 중지")
        print("3. 시스템 상태")
        print("4. 데이터 확인")
        print("5. 로그 보기")
        print("6. 성과 분석")
        print("0. 종료")
        
        try:
            choice = input("\n선택 (0-6): ").strip()
            
            if choice == "1":
                master.start_all()
            elif choice == "2":
                master.stop_all()
            elif choice == "3":
                master.show_status()
            elif choice == "4":
                master.check_data()
            elif choice == "5":
                master.show_logs()
            elif choice == "6":
                os.system("python paper_trading_analyzer.py")
            elif choice == "0":
                master.stop_all()
                break
            else:
                print("❌ 잘못된 선택")
                
        except KeyboardInterrupt:
            print("\n")
            continue
        except Exception as e:
            print(f"❌ 오류: {e}")
    
    print("\n👋 StockPilot 마스터 컨트롤 종료")

if __name__ == "__main__":
    # 필요 패키지 확인
    required_packages = ["psutil", "fastapi", "uvicorn", "yfinance", "pandas"]
    missing = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing.append(package)
    
    if missing:
        print(f"⚠️ 필요 패키지 설치: pip install {' '.join(missing)}")
        sys.exit(1)
    
    # 디렉토리 생성
    os.makedirs("data/realtime", exist_ok=True)
    os.makedirs("logs", exist_ok=True)
    os.makedirs("reports", exist_ok=True)
    
    main()
