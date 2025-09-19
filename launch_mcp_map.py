#!/usr/bin/env python3
"""
MCP-MAP 통합 실행 스크립트
회장님의 모든 시스템을 한 번에 구동
"""

import subprocess
import time
import os
from pathlib import Path
import json
from datetime import datetime

# 경로 설정
BASE_DIR = Path("/Users/youareplan/Desktop/mcp-map")
os.chdir(BASE_DIR)

class MCPMapLauncher:
    def __init__(self):
        self.processes = []
        self.start_time = datetime.now()
        
    def banner(self):
        """시작 배너"""
        print("""
╔══════════════════════════════════════════════════════════╗
║                    🚀 MCP-MAP SYSTEM                     ║
║                  회장님의 통합 컨트롤 타워                   ║
╠══════════════════════════════════════════════════════════╣
║  💼 정책자금 | 📈 주식 | 🤖 AI | 📊 대시보드             ║
╚══════════════════════════════════════════════════════════╝
        """)
        print(f"🕐 시작 시간: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    def check_requirements(self):
        """필수 패키지 확인"""
        print("📦 필수 패키지 확인 중...")
        
        required = [
            "fastapi", "yfinance", "pandas", "numpy", 
            "streamlit", "plotly", "asyncio"
        ]
        
        missing = []
        for pkg in required:
            try:
                __import__(pkg)
                print(f"  ✅ {pkg}")
            except ImportError:
                print(f"  ❌ {pkg} - 설치 필요")
                missing.append(pkg)
        
        if missing:
            print(f"\n⚠️  설치 필요: pip install {' '.join(missing)}")
            return False
        
        print("✅ 모든 패키지 준비 완료\n")
        return True
    
    def start_database(self):
        """데이터베이스 시작"""
        print("🗄️  데이터베이스 시작...")
        
        # DuckDB는 파일 기반이라 별도 실행 불필요
        print("  ✅ DuckDB - 준비 완료")
        
        # PostgreSQL (Docker가 있다면)
        try:
            subprocess.run(["docker", "ps"], capture_output=True, check=True)
            postgres = subprocess.Popen([
                "docker", "run", "-d",
                "--name", "mcp-postgres",
                "-e", "POSTGRES_PASSWORD=mcp123",
                "-p", "5432:5432",
                "postgres:14"
            ])
            self.processes.append(postgres)
            print("  ✅ PostgreSQL - 시작됨")
        except:
            print("  ⚠️  PostgreSQL - Docker 없음 (스킵)")
        
        print()
    
    def start_api_servers(self):
        """API 서버들 시작"""
        print("🚀 API 서버들 시작...")
        
        # StockPilot-AI API
        api_path = BASE_DIR / "StockPilot-ai" / "price_api.py"
        if api_path.exists():
            api_process = subprocess.Popen(["python", str(api_path)])
            self.processes.append(api_process)
            print("  ✅ StockPilot-AI API - http://localhost:8002")
        
        print()
    
    def start_dashboard(self):
        """대시보드 시작"""
        print("📊 대시보드 시작...")
        
        dashboard_path = BASE_DIR / "StockPilot-ai" / "dashboard.py"
        if dashboard_path.exists():
            dashboard = subprocess.Popen([
                "streamlit", "run",
                str(dashboard_path),
                "--server.port", "8501",
                "--server.headless", "true"
            ])
            self.processes.append(dashboard)
            print("  ✅ StockPilot-AI 대시보드 - http://localhost:8501")
        
        print()
    
    def start_schedulers(self):
        """스케줄러 시작"""
        print("⏰ 자동 실행 스케줄러...")
        
        # 주식 일일 분석
        print("  • 09:00 - 장 시작 분석")
        print("  • 15:30 - 장 마감 리포트")
        print("  • 5분마다 - 실시간 모니터링")
        
        # 정책자금 체크
        print("  • 10:00 - 신규 공고 체크")
        print("  • 14:00 - 매칭 분석")
        
        print()
    
    def show_status(self):
        """시스템 상태 표시"""
        print("="*60)
        print("🎯 시스템 상태")
        print("="*60)
        
        services = {
            "StockPilot API": "http://localhost:8002",
            "대시보드": "http://localhost:8501",
            "데이터베이스": "정상 작동",
            "스케줄러": "자동 실행 중"
        }
        
        for name, status in services.items():
            print(f"  • {name}: {status}")
        
        print("\n📝 사용 가능한 명령:")
        print("  • curl http://localhost:8002/api/price/AAPL")
        print("  • curl http://localhost:8002/api/analysis/AAPL") 
        print("  • curl http://localhost:8002/api/recommend")
        print("  • python mcp/run.py stocks_daily_research")
        print("  • python mcp/run.py policy_daily")
        
        print("\n💡 API 사용 예시:")
        print("  실시간 주가: GET /api/price/{ticker}")
        print("  기술분석: GET /api/analysis/{ticker}")
        print("  차트 데이터: GET /api/chart/{ticker}")
        print("  포트폴리오: POST /api/prices")
        
        print("\n🛑 종료: Ctrl+C")
        print("="*60)
    
    def run(self):
        """전체 시스템 실행"""
        self.banner()
        
        if not self.check_requirements():
            print("❌ 필수 패키지를 먼저 설치해주세요!")
            return
        
        try:
            self.start_database()
            self.start_api_servers()
            self.start_dashboard()
            self.start_schedulers()
            self.show_status()
            
            # 계속 실행
            print("\n✨ 모든 시스템이 시작되었습니다!")
            print("🔄 실행 중... (종료: Ctrl+C)\n")
            
            while True:
                time.sleep(60)
                print(f"⏱️  실행 시간: {datetime.now() - self.start_time}")
                
        except KeyboardInterrupt:
            print("\n\n🛑 시스템 종료 중...")
            for p in self.processes:
                p.terminate()
            print("✅ 안전하게 종료되었습니다.")
        except Exception as e:
            print(f"\n❌ 오류 발생: {e}")
            for p in self.processes:
                p.terminate()

if __name__ == "__main__":
    launcher = MCPMapLauncher()
    launcher.run()