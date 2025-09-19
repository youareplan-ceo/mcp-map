#!/usr/bin/env python3
import sqlite3
import json
import os
import time
import argparse
from datetime import datetime, timedelta
from pathlib import Path
import numpy as np
import logging
from typing import Dict, List, Optional, Tuple
import glob
import random

class PortfolioManager:
    def __init__(self, initial_krw=10000000, initial_usd=10000):
        self.initial_krw = initial_krw
        self.initial_usd = initial_usd
        self.cash_krw = initial_krw
        self.cash_usd = initial_usd

        # 포트폴리오 설정
        self.holdings = {}  # {symbol: {'quantity': int, 'avg_price': float, 'currency': str}}
        self.max_positions = 10
        self.max_position_weight = 0.30
        self.min_cash_ratio = 0.20

        # 매매 규칙
        self.stop_loss_pct = -0.05  # -5%
        self.take_profit_pct = 0.15  # +15%

        # 통계
        self.total_trades = 0
        self.winning_trades = 0
        self.max_drawdown = 0.0
        self.peak_value = max(initial_krw, initial_usd * 1300)  # 환율 1300원 가정

    def get_currency(self, symbol):
        """종목의 통화 확인"""
        if symbol.endswith('.KS') or symbol.endswith('.KQ'):
            return 'KRW'
        return 'USD'

    def get_available_cash(self, currency):
        """사용 가능한 현금"""
        return self.cash_krw if currency == 'KRW' else self.cash_usd

    def get_portfolio_value(self, market_data):
        """포트폴리오 총 가치 계산 (원화 기준)"""
        total_value = self.cash_krw + (self.cash_usd * 1300)  # 환율 1300원 가정

        for symbol, holding in self.holdings.items():
            if symbol in market_data:
                current_price = market_data[symbol]['current_price']
                quantity = holding['quantity']

                if holding['currency'] == 'USD':
                    value = current_price * quantity * 1300
                else:
                    value = current_price * quantity

                total_value += value

        return total_value

    def get_position_value(self, symbol, current_price):
        """특정 포지션의 현재 가치"""
        if symbol not in self.holdings:
            return 0

        holding = self.holdings[symbol]
        quantity = holding['quantity']

        if holding['currency'] == 'USD':
            return current_price * quantity * 1300
        else:
            return current_price * quantity

    def can_buy(self, symbol, price, quantity):
        """매수 가능 여부 확인"""
        # 최대 포지션 수 확인
        if len(self.holdings) >= self.max_positions and symbol not in self.holdings:
            return False, "Maximum positions reached"

        currency = self.get_currency(symbol)
        cost = price * quantity

        # 현금 보유량 확인
        available_cash = self.get_available_cash(currency)
        if cost > available_cash:
            return False, "Insufficient cash"

        # 최대 비중 확인
        total_value = self.get_portfolio_value({symbol: {'current_price': price}})
        if currency == 'USD':
            position_value = cost * 1300
        else:
            position_value = cost

        if symbol in self.holdings:
            current_position_value = self.get_position_value(symbol, price)
            total_position_value = current_position_value + position_value
        else:
            total_position_value = position_value

        position_weight = total_position_value / total_value
        if position_weight > self.max_position_weight:
            return False, f"Position weight {position_weight:.2%} exceeds maximum {self.max_position_weight:.2%}"

        # 최소 현금 비율 확인
        remaining_cash = available_cash - cost
        if currency == 'USD':
            remaining_total_cash = self.cash_krw + (remaining_cash * 1300)
        else:
            remaining_total_cash = remaining_cash + (self.cash_usd * 1300)

        cash_ratio = remaining_total_cash / total_value
        if cash_ratio < self.min_cash_ratio:
            return False, f"Cash ratio {cash_ratio:.2%} below minimum {self.min_cash_ratio:.2%}"

        return True, "OK"

    def buy(self, symbol, price, quantity, reason=""):
        """매수 실행"""
        can_buy, message = self.can_buy(symbol, price, quantity)
        if not can_buy:
            return False, message

        currency = self.get_currency(symbol)
        cost = price * quantity

        # 현금 차감
        if currency == 'USD':
            self.cash_usd -= cost
        else:
            self.cash_krw -= cost

        # 포지션 추가/업데이트
        if symbol in self.holdings:
            holding = self.holdings[symbol]
            total_quantity = holding['quantity'] + quantity
            total_cost = (holding['avg_price'] * holding['quantity']) + (price * quantity)
            avg_price = total_cost / total_quantity

            self.holdings[symbol] = {
                'quantity': total_quantity,
                'avg_price': avg_price,
                'currency': currency
            }
        else:
            self.holdings[symbol] = {
                'quantity': quantity,
                'avg_price': price,
                'currency': currency
            }

        self.total_trades += 1
        return True, f"Bought {quantity} shares of {symbol} at {price:.2f}"

    def sell(self, symbol, price, quantity=None, reason=""):
        """매도 실행"""
        if symbol not in self.holdings:
            return False, "No position to sell"

        holding = self.holdings[symbol]
        available_quantity = holding['quantity']

        if quantity is None:
            quantity = available_quantity
        elif quantity > available_quantity:
            return False, f"Insufficient shares. Have {available_quantity}, trying to sell {quantity}"

        currency = holding['currency']
        proceeds = price * quantity

        # 현금 추가
        if currency == 'USD':
            self.cash_usd += proceeds
        else:
            self.cash_krw += proceeds

        # 수익률 계산
        cost_basis = holding['avg_price'] * quantity
        profit_loss = proceeds - cost_basis
        profit_pct = (profit_loss / cost_basis) * 100

        # 포지션 업데이트
        remaining_quantity = available_quantity - quantity
        if remaining_quantity == 0:
            del self.holdings[symbol]
        else:
            self.holdings[symbol]['quantity'] = remaining_quantity

        # 통계 업데이트
        self.total_trades += 1
        if profit_loss > 0:
            self.winning_trades += 1

        return True, f"Sold {quantity} shares of {symbol} at {price:.2f} ({profit_pct:+.2f}%)"

    def get_win_rate(self):
        """승률 계산"""
        if self.total_trades == 0:
            return 0
        return (self.winning_trades / self.total_trades) * 100

class AIScoreCalculator:
    """AI 점수 계산기 (profit_maximizer.py 간소화 버전)"""

    def calculate_score(self, data):
        """종목의 AI 점수 계산 (0-100)"""
        try:
            score = 50  # 기본 점수

            # RSI 기반 점수
            rsi = data.get('technical_indicators', {}).get('rsi')
            if rsi is not None:
                if rsi < 30:  # 과매도
                    score += 25
                elif rsi < 40:
                    score += 15
                elif rsi > 70:  # 과매수
                    score -= 20
                elif rsi > 60:
                    score -= 10

            # MACD 기반 점수
            macd_data = data.get('technical_indicators', {}).get('macd', {})
            macd = macd_data.get('macd')
            signal = macd_data.get('signal')

            if macd is not None and signal is not None:
                if macd > signal:  # 상승 신호
                    score += 15
                else:  # 하락 신호
                    score -= 15

            # 거래량 기반 점수
            volume = data.get('volume', 0)
            if volume > 1000000:  # 거래량 많음
                score += 10
            elif volume < 100000:  # 거래량 적음
                score -= 5

            # 가격 변동률 기반 점수
            change_pct = data.get('change_percent', 0)
            if 0 < change_pct < 3:  # 적당한 상승
                score += 10
            elif change_pct > 5:  # 급등
                score -= 5
            elif change_pct < -3:  # 하락
                score -= 15

            # 랜덤 요소 추가 (시장 노이즈 시뮬레이션)
            score += random.randint(-5, 5)

            return max(0, min(100, score))

        except Exception as e:
            return 50  # 에러 시 중립 점수

class AutoPaperTrader:
    def __init__(self, initial_krw=10000000, initial_usd=10000):
        self.portfolio = PortfolioManager(initial_krw, initial_usd)
        self.ai_calculator = AIScoreCalculator()

        self.setup_database()
        self.setup_directories()
        self.setup_logging()

        self.running = False
        self.last_update = None

    def setup_database(self):
        """SQLite 데이터베이스 설정"""
        self.db_path = "trades.db"
        conn = sqlite3.connect(self.db_path)

        conn.execute('''
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                symbol TEXT NOT NULL,
                action TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                price REAL NOT NULL,
                reason TEXT,
                ai_score INTEGER,
                profit_loss REAL DEFAULT 0,
                total_value REAL
            )
        ''')

        conn.execute('''
            CREATE TABLE IF NOT EXISTS portfolio_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                total_value REAL,
                cash_krw REAL,
                cash_usd REAL,
                holdings TEXT,
                daily_return REAL,
                total_return REAL
            )
        ''')

        conn.commit()
        conn.close()

    def setup_directories(self):
        """필요한 디렉토리 생성"""
        today = datetime.now().strftime('%Y-%m-%d')

        self.portfolio_dir = Path(f'portfolio/{today}')
        self.reports_dir = Path('reports')

        self.portfolio_dir.mkdir(parents=True, exist_ok=True)
        self.reports_dir.mkdir(parents=True, exist_ok=True)

    def setup_logging(self):
        """로깅 설정"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('auto_trader.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def load_realtime_data(self):
        """실시간 데이터 로드"""
        try:
            today = datetime.now().strftime('%Y-%m-%d')
            data_dir = Path(f'data/realtime/{today}')

            if not data_dir.exists():
                return {}

            market_data = {}

            for json_file in data_dir.glob('*.json'):
                try:
                    with open(json_file, 'r') as f:
                        data_list = json.load(f)

                    if data_list:
                        # 최신 데이터 사용
                        latest_data = data_list[-1]
                        symbol = latest_data['symbol']
                        market_data[symbol] = latest_data

                except Exception as e:
                    self.logger.error(f"Error loading {json_file}: {e}")
                    continue

            return market_data

        except Exception as e:
            self.logger.error(f"Error loading realtime data: {e}")
            return {}

    def execute_trade(self, symbol, action, quantity, price, reason, ai_score):
        """거래 실행 및 DB 저장"""
        try:
            conn = sqlite3.connect(self.db_path)

            if action == 'BUY':
                success, message = self.portfolio.buy(symbol, price, quantity, reason)
            else:  # SELL
                success, message = self.portfolio.sell(symbol, price, quantity, reason)

            if success:
                # 거래 기록 저장
                total_value = self.portfolio.get_portfolio_value(
                    {symbol: {'current_price': price}}
                )

                conn.execute('''
                    INSERT INTO trades
                    (symbol, action, quantity, price, reason, ai_score, total_value)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (symbol, action, quantity, price, reason, ai_score, total_value))

                conn.commit()
                self.logger.info(f"✅ {action}: {message}")

            else:
                self.logger.warning(f"❌ {action} failed: {message}")

            conn.close()
            return success, message

        except Exception as e:
            self.logger.error(f"Error executing trade: {e}")
            return False, str(e)

    def check_stop_loss_take_profit(self, market_data):
        """손절/익절 확인"""
        trades_to_execute = []

        for symbol, holding in self.portfolio.holdings.items():
            if symbol not in market_data:
                continue

            current_price = market_data[symbol]['current_price']
            avg_price = holding['avg_price']
            quantity = holding['quantity']

            # 수익률 계산
            return_pct = (current_price - avg_price) / avg_price

            # 손절 확인
            if return_pct <= self.portfolio.stop_loss_pct:
                trades_to_execute.append({
                    'symbol': symbol,
                    'action': 'SELL',
                    'quantity': quantity,
                    'price': current_price,
                    'reason': 'STOP_LOSS',
                    'ai_score': 0
                })

            # 익절 확인
            elif return_pct >= self.portfolio.take_profit_pct:
                trades_to_execute.append({
                    'symbol': symbol,
                    'action': 'SELL',
                    'quantity': quantity,
                    'price': current_price,
                    'reason': 'TAKE_PROFIT',
                    'ai_score': 0
                })

        return trades_to_execute

    def generate_trading_signals(self, market_data):
        """매매 신호 생성"""
        trades_to_execute = []

        for symbol, data in market_data.items():
            try:
                ai_score = self.ai_calculator.calculate_score(data)
                current_price = data['current_price']
                rsi = data.get('technical_indicators', {}).get('rsi')

                if rsi is None:
                    continue

                # 매수 신호
                if ai_score >= 90 and rsi < 30:
                    # 자금의 20% 매수
                    currency = self.portfolio.get_currency(symbol)
                    available_cash = self.portfolio.get_available_cash(currency)
                    investment_amount = available_cash * 0.20
                    quantity = int(investment_amount / current_price)

                    if quantity > 0:
                        trades_to_execute.append({
                            'symbol': symbol,
                            'action': 'BUY',
                            'quantity': quantity,
                            'price': current_price,
                            'reason': 'AI_SIGNAL_STRONG',
                            'ai_score': ai_score
                        })

                elif ai_score >= 85 and ai_score < 90 and rsi < 40:
                    # 자금의 10% 매수
                    currency = self.portfolio.get_currency(symbol)
                    available_cash = self.portfolio.get_available_cash(currency)
                    investment_amount = available_cash * 0.10
                    quantity = int(investment_amount / current_price)

                    if quantity > 0:
                        trades_to_execute.append({
                            'symbol': symbol,
                            'action': 'BUY',
                            'quantity': quantity,
                            'price': current_price,
                            'reason': 'AI_SIGNAL_MEDIUM',
                            'ai_score': ai_score
                        })

                # 매도 신호
                elif ai_score <= 30 and symbol in self.portfolio.holdings:
                    # 전량 매도
                    quantity = self.portfolio.holdings[symbol]['quantity']
                    trades_to_execute.append({
                        'symbol': symbol,
                        'action': 'SELL',
                        'quantity': quantity,
                        'price': current_price,
                        'reason': 'AI_SIGNAL_WEAK',
                        'ai_score': ai_score
                    })

            except Exception as e:
                self.logger.error(f"Error generating signal for {symbol}: {e}")
                continue

        return trades_to_execute

    def save_portfolio_snapshot(self, market_data):
        """포트폴리오 스냅샷 저장"""
        try:
            timestamp = datetime.now()
            total_value = self.portfolio.get_portfolio_value(market_data)

            # 수익률 계산
            initial_value = self.portfolio.initial_krw + (self.portfolio.initial_usd * 1300)
            total_return = ((total_value - initial_value) / initial_value) * 100

            # JSON 스냅샷 저장
            snapshot = {
                'timestamp': timestamp.isoformat(),
                'total_value': total_value,
                'cash_krw': self.portfolio.cash_krw,
                'cash_usd': self.portfolio.cash_usd,
                'holdings': dict(self.portfolio.holdings),
                'total_return': total_return,
                'win_rate': self.portfolio.get_win_rate(),
                'total_trades': self.portfolio.total_trades
            }

            snapshot_file = self.portfolio_dir / f"snapshot_{timestamp.strftime('%H%M%S')}.json"
            with open(snapshot_file, 'w') as f:
                json.dump(snapshot, f, indent=2)

            # DB에도 저장
            conn = sqlite3.connect(self.db_path)
            conn.execute('''
                INSERT INTO portfolio_snapshots
                (total_value, cash_krw, cash_usd, holdings, total_return)
                VALUES (?, ?, ?, ?, ?)
            ''', (total_value, self.portfolio.cash_krw, self.portfolio.cash_usd,
                  json.dumps(self.portfolio.holdings), total_return))

            conn.commit()
            conn.close()

        except Exception as e:
            self.logger.error(f"Error saving portfolio snapshot: {e}")

    def display_status(self, market_data):
        """실시간 상태 출력"""
        os.system('clear' if os.name == 'posix' else 'cls')

        total_value = self.portfolio.get_portfolio_value(market_data)
        initial_value = self.portfolio.initial_krw + (self.portfolio.initial_usd * 1300)
        total_return = ((total_value - initial_value) / initial_value) * 100

        print("=" * 50)
        print("💰 종이 거래 실시간 현황")
        print("=" * 50)
        print(f"시작 자금: ₩{initial_value:,.0f}")
        print(f"현재 평가: ₩{total_value:,.0f} ({total_return:+.2f}%)")
        print("=" * 50)

        if self.portfolio.holdings:
            print("보유 종목:")
            for symbol, holding in self.portfolio.holdings.items():
                if symbol in market_data:
                    current_price = market_data[symbol]['current_price']
                    avg_price = holding['avg_price']
                    quantity = holding['quantity']
                    return_pct = ((current_price - avg_price) / avg_price) * 100

                    currency_symbol = '$' if holding['currency'] == 'USD' else '₩'
                    print(f"  {symbol}: {quantity}주 @ {currency_symbol}{avg_price:.2f} → "
                          f"{currency_symbol}{current_price:.2f} ({return_pct:+.2f}%)")
        else:
            print("보유 종목 없음")

        print("=" * 50)

        # 최근 거래 내역
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.execute('''
                SELECT timestamp, symbol, action, quantity, price, reason
                FROM trades
                ORDER BY timestamp DESC
                LIMIT 5
            ''')

            recent_trades = cursor.fetchall()
            conn.close()

            if recent_trades:
                print("최근 거래:")
                for trade in recent_trades:
                    timestamp, symbol, action, quantity, price, reason = trade
                    time_str = datetime.fromisoformat(timestamp).strftime('%H:%M')
                    action_kr = '매수' if action == 'BUY' else '매도'
                    print(f"  {time_str} {symbol} {action_kr} {quantity}주 @ {price:.2f} ({reason})")
            else:
                print("거래 내역 없음")

        except Exception as e:
            print(f"거래 내역 조회 오류: {e}")

        print("=" * 50)
        print(f"전체 수익률: {total_return:+.2f}%")
        print(f"승률: {self.portfolio.get_win_rate():.0f}% ({self.portfolio.winning_trades}승 {self.portfolio.total_trades - self.portfolio.winning_trades}패)")
        print(f"현금 보유: ₩{self.portfolio.cash_krw:,.0f} + ${self.portfolio.cash_usd:,.0f}")
        print("=" * 50)
        print(f"마지막 업데이트: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    def run_trading_cycle(self):
        """매매 사이클 실행"""
        try:
            # 실시간 데이터 로드
            market_data = self.load_realtime_data()

            if not market_data:
                self.logger.warning("No market data available")
                return

            # 손절/익절 확인
            stop_profit_trades = self.check_stop_loss_take_profit(market_data)

            # 매매 신호 생성
            signal_trades = self.generate_trading_signals(market_data)

            # 모든 거래 실행
            all_trades = stop_profit_trades + signal_trades

            for trade in all_trades:
                self.execute_trade(
                    trade['symbol'],
                    trade['action'],
                    trade['quantity'],
                    trade['price'],
                    trade['reason'],
                    trade['ai_score']
                )
                time.sleep(0.1)  # API 제한 방지

            # 포트폴리오 스냅샷 저장
            self.save_portfolio_snapshot(market_data)

            # 상태 출력
            self.display_status(market_data)

            self.last_update = datetime.now()

        except Exception as e:
            self.logger.error(f"Error in trading cycle: {e}")

    def start_trading(self):
        """자동 매매 시작"""
        self.running = True
        self.logger.info("🚀 Auto Paper Trading Started")

        try:
            while self.running:
                start_time = time.time()

                self.run_trading_cycle()

                # 1분 간격 유지
                elapsed = time.time() - start_time
                sleep_time = max(0, 60 - elapsed)

                if sleep_time > 0:
                    time.sleep(sleep_time)

        except KeyboardInterrupt:
            self.logger.info("Trading stopped by user")
        except Exception as e:
            self.logger.error(f"Fatal error in trading loop: {e}")
        finally:
            self.running = False

    def stop_trading(self):
        """자동 매매 중지"""
        self.running = False
        self.logger.info("Stopping auto trading...")

def main():
    parser = argparse.ArgumentParser(description='Auto Paper Trading Simulator')
    parser.add_argument('--initial', type=int, default=10000000,
                       help='Initial KRW amount (default: 10000000)')
    parser.add_argument('--initial-usd', type=int, default=10000,
                       help='Initial USD amount (default: 10000)')

    args = parser.parse_args()

    print("🚀 Auto Paper Trading Simulator")
    print("=" * 50)
    print(f"💰 Initial KRW: ₩{args.initial:,}")
    print(f"💰 Initial USD: ${args.initial_usd:,}")
    print("=" * 50)

    trader = AutoPaperTrader(args.initial, args.initial_usd)

    try:
        trader.start_trading()
    except KeyboardInterrupt:
        print("\n프로그램을 종료합니다...")
        trader.stop_trading()

if __name__ == "__main__":
    main()