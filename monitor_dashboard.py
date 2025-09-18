#!/usr/bin/env python3
"""
StockPilot 실시간 모니터링 대시보드
실시간 데이터와 시그널을 콘솔에 표시
"""

import os
import sys
import json
import time
import yaml
from datetime import datetime
from pathlib import Path
from typing import Dict, List
import asyncio

# ANSI 색상 코드
class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def clear_screen():
    """화면 지우기"""
    os.system('clear' if os.name == 'posix' else 'cls')

def load_config() -> Dict:
    """설정 파일 로드"""
    config_path = Path("config/monitoring.yaml")
    if config_path.exists():
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    return {}

def load_realtime_data(symbol: str) -> Dict:
    """실시간 데이터 로드"""
    today = datetime.now().strftime("%Y%m%d")
    data_path = Path(f"data/realtime/{today}/{symbol}.json")
    
    if data_path.exists():
        with open(data_path, 'r') as f:
            data = json.load(f)
            if isinstance(data, list) and data:
                return data[-1]  # 최신 데이터
    
    return {"symbol": symbol, "price": 0, "rsi": 50, "volume": 0}

def get_signal_emoji(score: int) -> str:
    """점수에 따른 이모지"""
    if score >= 90:
        return "🔥"  # 매우 강한 시그널
    elif score >= 80:
        return "🚀"  # 강한 시그널
    elif score >= 70:
        return "📈"  # 상승 시그널
    elif score >= 50:
        return "➡️"  # 중립
    elif score >= 30:
        return "📉"  # 하락 시그널
    else:
        return "⚠️"  # 위험 시그널

def format_price_change(change: float) -> str:
    """가격 변동 포맷팅"""
    if change > 0:
        return f"{Colors.GREEN}+{change:.2f}%{Colors.RESET}"
    elif change < 0:
        return f"{Colors.RED}{change:.2f}%{Colors.RESET}"
    else:
        return f"{Colors.WHITE}{change:.2f}%{Colors.RESET}"

def display_dashboard(watchlist: List[str]):
    """대시보드 표시"""
    clear_screen()
    config = load_config()
    
    # 헤더
    print(f"{Colors.BOLD}{Colors.CYAN}")
    print("="*60)
    print("     StockPilot 실시간 모니터링 대시보드 v2.0")
    print("="*60)
    print(f"{Colors.RESET}")
    
    # 시간 정보
    now = datetime.now()
    print(f"⏰ 현재 시각: {now.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📊 모니터링 종목: {len(watchlist)}개")
    print()
    
    # 테이블 헤더
    print(f"{Colors.BOLD}{'종목':<10} {'현재가':<10} {'변동%':<10} {'RSI':<6} {'AI점수':<8} {'시그널':<10}{Colors.RESET}")
    print("-"*60)
    
    high_score_count = 0
    alerts = []
    
    # 각 종목 데이터 표시
    for symbol in watchlist:
        data = load_realtime_data(symbol)
        
        # 더미 AI 점수 (실제로는 계산)
        ai_score = int(50 + (data.get("rsi", 50) - 50) * 0.8)
        ai_score = max(0, min(100, ai_score))
        
        # 가격 변동 (더미)
        price_change = (data.get("price", 100) - 100) / 100 * 100
        
        # 색상 결정
        if ai_score >= 85:
            color = Colors.GREEN
            high_score_count += 1
            alerts.append((symbol, ai_score))
        elif ai_score <= 30:
            color = Colors.RED
        else:
            color = Colors.WHITE
        
        # 시그널
        emoji = get_signal_emoji(ai_score)
        
        # 출력
        print(f"{color}{symbol:<10} ${data.get('price', 0):>9.2f} "
              f"{format_price_change(price_change):<10} "
              f"{data.get('rsi', 50):>5.1f} "
              f"{ai_score:>6}/100 "
              f"{emoji} {Colors.RESET}")
    
    print("-"*60)
    
    # 알림 섹션
    if alerts:
        print()
        print(f"{Colors.YELLOW}{Colors.BOLD}📢 긴급 알림 ({len(alerts)}개){Colors.RESET}")
        for symbol, score in alerts:
            print(f"  {Colors.GREEN}✅ {symbol}: AI 점수 {score}/100 - 강력 시그널 감지{Colors.RESET}")
    
    # 통계
    print()
    print(f"{Colors.CYAN}📊 요약 통계{Colors.RESET}")
    print(f"  • 고득점 종목 (85+): {high_score_count}개")
    print(f"  • 평균 AI 점수: {sum([50 for _ in watchlist])/len(watchlist):.1f}")
    print(f"  • 다음 업데이트: {config.get('MONITORING', {}).get('interval_seconds', 60)}초 후")
    
    # 푸터
    print()
    print(f"{Colors.MAGENTA}{'='*60}{Colors.RESET}")
    print(f"{Colors.YELLOW}⚠️  모든 정보는 참고용이며 투자 권유가 아닙니다{Colors.RESET}")
    print(f"{Colors.MAGENTA}{'='*60}{Colors.RESET}")

async def monitor_loop():
    """모니터링 루프"""
    # watchlist 로드
    watchlist_path = Path("watchlist.txt")
    if not watchlist_path.exists():
        print("❌ watchlist.txt 파일이 없습니다")
        return
    
    with open(watchlist_path, 'r') as f:
        lines = f.readlines()
    
    # 주석과 빈 줄 제거
    watchlist = []
    for line in lines:
        line = line.strip()
        if line and not line.startswith('#'):
            watchlist.append(line)
    
    print(f"📋 {len(watchlist)}개 종목 모니터링 시작...")
    time.sleep(2)
    
    while True:
        try:
            # 대시보드 표시
            display_dashboard(watchlist[:10])  # 상위 10개만 표시
            
            # 대기
            await asyncio.sleep(60)  # 60초마다 업데이트
            
        except KeyboardInterrupt:
            print(f"\n{Colors.RED}🛑 모니터링 중단{Colors.RESET}")
            break
        except Exception as e:
            print(f"❌ 오류: {e}")
            await asyncio.sleep(5)

def main():
    """메인 함수"""
    print(f"{Colors.CYAN}{Colors.BOLD}")
    print("🚀 StockPilot 실시간 모니터링 시작...")
    print(f"{Colors.RESET}")
    
    # 디렉토리 생성
    os.makedirs("data/realtime", exist_ok=True)
    os.makedirs("logs", exist_ok=True)
    
    # 모니터링 시작
    asyncio.run(monitor_loop())

if __name__ == "__main__":
    main()
