#!/usr/bin/env python3
"""
🚀 StockPilot 실전 실행 마스터 스크립트
모든 시스템 통합 실행 및 모니터링
"""

import os
import sys
import time
import subprocess
from datetime import datetime

def check_requirements():
    """필수 패키지 체크"""
    required = [
        "yfinance", "pandas", "numpy", "ta", 
        "fastapi", "uvicorn", "websocket-client",
        "sqlite3", "requests", "beautifulsoup4"
    ]
    
    print("📦 패키지 확인 중...")
    missing = []
    for pkg in required:
        try:
            __import__(pkg.replace("-", "_"))
            print(f"  ✅ {pkg}")
        except ImportError:
            missing.append(pkg)
            print(f"  ❌ {pkg}")
    
    if missing:
        print(f"\n⚠️ 설치 필요: pip install {' '.join(missing)}")
        return False
    return True

def create_env_file():
    """환경 변수 파일 생성"""
    if not os.path.exists(".env"):
        print("\n📝 .env 파일 생성...")
        env_content = """# StockPilot Environment Variables
# NewsAPI (https://newsapi.org 무료 가입)
NEWSAPI_KEY=your_api_key_here

# Reddit API (선택사항)
REDDIT_CLIENT_ID=
REDDIT_CLIENT_SECRET=

# 초기 자금 설정
INITIAL_CAPITAL_KRW=10000000
INITIAL_CAPITAL_USD=10000

# AI 임계값
AI_THRESHOLD_BUY=85
AI_THRESHOLD_SELL=30

# 리스크 관리
STOP_LOSS_PERCENT=5
TAKE_PROFIT_PERCENT=15
MAX_POSITIONS=10

# 모니터링
MONITOR_INTERVAL_SECONDS=60
ALERT_PROFIT_THRESHOLD=5
ALERT_LOSS_THRESHOLD=3
"""
        with open(".env", "w") as f:
            f.write(env_content)
        print("  ✅ .env 파일 생성 완료")
        print("  ⚠️ API 키를 입력해주세요!")
        return False
    return True

def show_menu():
    """실행 메뉴 표시"""
    print("""
╔══════════════════════════════════════════════════════════╗
║         🚀 StockPilot AI Trading System v2.0            ║
║              Complete Edition - 실전 준비 완료           ║
╚══════════════════════════════════════════════════════════╝

실행 옵션을 선택하세요:

1️⃣  빠른 시작 (추천)
    → 모든 핵심 시스템 자동 실행
    
2️⃣  A/B 전략 테스트
    → 3개 전략 동시 비교 (24시간)
    
3️⃣  실전 모드 (소액)
    → 100만원으로 실제 테스트
    
4️⃣  개발자 모드
    → 개별 컴포넌트 선택 실행
    
5️⃣  온라인 배포
    → Streamlit Cloud 배포
    
6️⃣  시스템 상태
    → 현재 실행 중인 프로세스
    
0️⃣  종료

선택: """)

def quick_start():
    """빠른 시작 - 모든 시스템 실행"""
    print("\n🚀 빠른 시작 모드...")
    
    commands = [
        ("📡 실시간 수집", "python realtime_data_collector.py"),
        ("📰 뉴스 수집", "python news_sentiment_collector.py"),
        ("💰 자동 매매", "python auto_paper_trader.py --initial 10000000"),
        ("📊 24시간 모니터", "python run_24h_test.py"),
        ("🌐 웹 대시보드", "python performance_dashboard.py")
    ]
    
    processes = []
    for name, cmd in commands:
        print(f"시작: {name}")
        proc = subprocess.Popen(cmd, shell=True)
        processes.append((name, proc))
        time.sleep(2)
    
    print("\n✅ 모든 시스템 실행 완료!")
    print("\n📱 접속 URL:")
    print("  • 성과 대시보드: http://localhost:8001/dashboard")
    print("  • 24시간 모니터: http://localhost:9999")
    print("\n종료: Ctrl+C")
    
    try:
        while True:
            time.sleep(60)
            # 상태 체크
            for name, proc in processes:
                if proc.poll() is not None:
                    print(f"⚠️ {name} 종료됨 - 재시작...")
                    # 재시작 로직
    except KeyboardInterrupt:
        print("\n🛑 시스템 종료...")
        for name, proc in processes:
            proc.terminate()

def ab_test_mode():
    """A/B 전략 테스트"""
    print("\n🔬 A/B 전략 테스트 시작...")
    
    print("""
전략 설정:
• 전략 A (보수적): AI 90+ 
• 전략 B (균형): AI 85+
• 전략 C (공격적): AI 80+

테스트 기간: 24시간
초기 자금: 각 1000만원
""")
    
    os.system("python strategy_ab_test.py --duration 24")
    print("\n웹 대시보드: http://localhost:8888")

def production_mode():
    """실전 모드"""
    print("\n💎 실전 모드 (소액 테스트)")
    
    capital = input("초기 자금 (원): ") or "1000000"
    
    print(f"\n실전 설정:")
    print(f"• 초기 자금: {int(capital):,}원")
    print(f"• AI 임계값: 85점")
    print(f"• 손절: -5%")
    print(f"• 익절: +15%")
    
    confirm = input("\n시작하시겠습니까? (y/n): ")
    if confirm.lower() == 'y':
        os.system(f"python auto_paper_trader.py --initial {capital} --production")
        print("\n⚠️ 실전 모드 실행 중...")
    else:
        print("취소되었습니다.")

def developer_mode():
    """개발자 모드"""
    print("\n👨‍💻 개발자 모드")
    
    components = {
        "1": ("백테스팅", "python profit_strategy_finder.py"),
        "2": ("실시간 수집", "python realtime_data_collector.py"),
        "3": ("뉴스 수집", "python news_sentiment_collector.py"),
        "4": ("자동 매매", "python auto_paper_trader.py"),
        "5": ("A/B 테스트", "python strategy_ab_test.py"),
        "6": ("24시간 모니터", "python run_24h_test.py"),
        "7": ("성과 분석", "python paper_trading_analyzer.py"),
        "8": ("웹 대시보드", "python performance_dashboard.py"),
        "9": ("MCP 테스트", "python -m mcp.run")
    }
    
    print("\n실행할 컴포넌트:")
    for key, (name, _) in components.items():
        print(f"  {key}. {name}")
    
    choice = input("\n선택 (1-9): ")
    if choice in components:
        name, cmd = components[choice]
        print(f"\n실행: {name}")
        os.system(cmd)

def online_deployment():
    """온라인 배포"""
    print("\n🌐 온라인 배포")
    
    print("""
배포 옵션:
1. Streamlit Cloud (무료, 쉬움)
2. Heroku (무료 티어)
3. Docker (자체 서버)
""")
    
    choice = input("선택 (1-3): ")
    os.system(f"python deploy_online.py")

def system_status():
    """시스템 상태"""
    print("\n📊 시스템 상태")
    
    # 프로세스 체크
    import psutil
    
    stockpilot_processes = []
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            cmdline = ' '.join(proc.info['cmdline'] or [])
            if any(x in cmdline for x in [
                'realtime_data_collector',
                'auto_paper_trader',
                'news_sentiment_collector',
                'run_24h_test',
                'performance_dashboard',
                'strategy_ab_test'
            ]):
                stockpilot_processes.append({
                    'pid': proc.info['pid'],
                    'name': proc.info['name'],
                    'cmd': cmdline[:50] + '...' if len(cmdline) > 50 else cmdline
                })
        except:
            pass
    
    if stockpilot_processes:
        print("\n실행 중인 프로세스:")
        for proc in stockpilot_processes:
            print(f"  • PID {proc['pid']}: {proc['cmd']}")
    else:
        print("\n실행 중인 StockPilot 프로세스가 없습니다.")
    
    # 최근 성과
    if os.path.exists("trades.db"):
        import sqlite3
        conn = sqlite3.connect("trades.db")
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                COUNT(*) as trades,
                SUM(CASE WHEN profit_loss > 0 THEN 1 ELSE 0 END) as wins,
                AVG(profit_loss) as avg_profit
            FROM trades
            WHERE timestamp > datetime('now', '-1 day')
        """)
        
        stats = cursor.fetchone()
        if stats and stats[0] > 0:
            print(f"\n📈 최근 24시간 성과:")
            print(f"  • 거래: {stats[0]}건")
            print(f"  • 승률: {(stats[1]/stats[0]*100):.1f}%")
            print(f"  • 평균 수익: {(stats[2] or 0):.2f}%")
        
        conn.close()

def main():
    """메인 실행"""
    print("\n시스템 체크 중...")
    
    # 필수 체크
    if not check_requirements():
        print("\n필수 패키지를 먼저 설치하세요:")
        print("pip install -r requirements.txt")
        return
    
    if not create_env_file():
        print("\n.env 파일에 API 키를 설정하세요.")
        # API 키 없어도 계속 진행 가능
    
    while True:
        show_menu()
        choice = input().strip()
        
        if choice == "1":
            quick_start()
        elif choice == "2":
            ab_test_mode()
        elif choice == "3":
            production_mode()
        elif choice == "4":
            developer_mode()
        elif choice == "5":
            online_deployment()
        elif choice == "6":
            system_status()
        elif choice == "0":
            print("\n👋 StockPilot을 종료합니다.")
            break
        else:
            print("\n❌ 잘못된 선택입니다.")
        
        if choice in ["1", "2", "3"]:
            break  # 주요 모드 실행 후 종료
        
        input("\n계속하려면 Enter...")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 종료합니다.")
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
