#!/usr/bin/env python3
import argparse
import json
import sqlite3
import time
import threading
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from flask import Flask, render_template, jsonify
from scipy import stats
import logging
import os
import random
from typing import Dict, List, Tuple
import warnings
warnings.filterwarnings('ignore')

class AIScoreCalculator:
    """AI 점수 계산기"""

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

class VirtualAccount:
    """가상 계좌 클래스"""

    def __init__(self, strategy_name, initial_krw=10000000, initial_usd=0):
        self.strategy_name = strategy_name
        self.initial_krw = initial_krw
        self.initial_usd = initial_usd
        self.cash_krw = initial_krw
        self.cash_usd = initial_usd

        self.holdings = {}  # {symbol: {'quantity': int, 'avg_price': float, 'currency': str, 'entry_time': datetime}}
        self.trades = []
        self.portfolio_history = []

        # 성과 지표
        self.peak_value = initial_krw
        self.lowest_value = initial_krw
        self.max_drawdown = 0.0

    def get_currency(self, symbol):
        """종목의 통화 확인"""
        if symbol.endswith('.KS') or symbol.endswith('.KQ'):
            return 'KRW'
        return 'USD'

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

    def can_buy(self, symbol, price, quantity):
        """매수 가능 여부 확인"""
        currency = self.get_currency(symbol)
        cost = price * quantity

        available_cash = self.cash_krw if currency == 'KRW' else self.cash_usd

        return cost <= available_cash

    def buy(self, symbol, price, quantity, reason="", ai_score=0):
        """매수 실행"""
        if not self.can_buy(symbol, price, quantity):
            return False, "Insufficient cash"

        currency = self.get_currency(symbol)
        cost = price * quantity

        # 현금 차감
        if currency == 'USD':
            self.cash_usd -= cost
        else:
            self.cash_krw -= cost

        # 포지션 추가/업데이트
        current_time = datetime.now()

        if symbol in self.holdings:
            holding = self.holdings[symbol]
            total_quantity = holding['quantity'] + quantity
            total_cost = (holding['avg_price'] * holding['quantity']) + (price * quantity)
            avg_price = total_cost / total_quantity

            self.holdings[symbol] = {
                'quantity': total_quantity,
                'avg_price': avg_price,
                'currency': currency,
                'entry_time': holding['entry_time']  # 최초 진입 시간 유지
            }
        else:
            self.holdings[symbol] = {
                'quantity': quantity,
                'avg_price': price,
                'currency': currency,
                'entry_time': current_time
            }

        # 거래 기록
        trade = {
            'timestamp': current_time,
            'symbol': symbol,
            'action': 'BUY',
            'quantity': quantity,
            'price': price,
            'reason': reason,
            'ai_score': ai_score
        }

        self.trades.append(trade)
        return True, f"Bought {quantity} shares of {symbol} at {price:.2f}"

    def sell(self, symbol, price, quantity=None, reason="", ai_score=0):
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

        # 보유 기간 계산
        holding_period = (datetime.now() - holding['entry_time']).total_seconds() / 3600  # 시간 단위

        # 포지션 업데이트
        remaining_quantity = available_quantity - quantity
        if remaining_quantity == 0:
            del self.holdings[symbol]
        else:
            self.holdings[symbol]['quantity'] = remaining_quantity

        # 거래 기록
        trade = {
            'timestamp': datetime.now(),
            'symbol': symbol,
            'action': 'SELL',
            'quantity': quantity,
            'price': price,
            'reason': reason,
            'ai_score': ai_score,
            'profit_loss': profit_loss,
            'profit_pct': profit_pct,
            'holding_period': holding_period
        }

        self.trades.append(trade)
        return True, f"Sold {quantity} shares of {symbol} at {price:.2f} ({profit_pct:+.2f}%)"

    def update_portfolio_history(self, market_data):
        """포트폴리오 이력 업데이트"""
        current_value = self.get_portfolio_value(market_data)
        current_return = ((current_value - self.initial_krw) / self.initial_krw) * 100

        # 최대 낙폭 계산
        if current_value > self.peak_value:
            self.peak_value = current_value

        if current_value < self.lowest_value:
            self.lowest_value = current_value

        self.max_drawdown = max(self.max_drawdown, ((self.peak_value - current_value) / self.peak_value) * 100)

        history_entry = {
            'timestamp': datetime.now(),
            'total_value': current_value,
            'return_pct': current_return,
            'cash_krw': self.cash_krw,
            'cash_usd': self.cash_usd,
            'holdings_count': len(self.holdings)
        }

        self.portfolio_history.append(history_entry)

    def get_performance_metrics(self):
        """성과 지표 계산"""
        if len(self.portfolio_history) < 2:
            return {}

        # 수익률 데이터
        returns = [h['return_pct'] for h in self.portfolio_history]
        values = [h['total_value'] for h in self.portfolio_history]

        # 기본 지표
        current_return = returns[-1]

        # 변동성 (일간 수익률의 표준편차)
        if len(returns) > 1:
            daily_returns = np.diff(returns)
            volatility = np.std(daily_returns) if len(daily_returns) > 1 else 0
        else:
            volatility = 0

        # 샤프 비율 (무위험 수익률 3% 가정)
        risk_free_rate = 3.0
        sharpe_ratio = (current_return - risk_free_rate) / volatility if volatility > 0 else 0

        # 거래 통계
        profitable_trades = len([t for t in self.trades if t.get('profit_loss', 0) > 0])
        total_sell_trades = len([t for t in self.trades if t['action'] == 'SELL'])
        win_rate = (profitable_trades / total_sell_trades * 100) if total_sell_trades > 0 else 0

        # 평균 보유 기간
        holding_periods = [t.get('holding_period', 0) for t in self.trades if t['action'] == 'SELL']
        avg_holding_period = np.mean(holding_periods) if holding_periods else 0

        return {
            'current_return': current_return,
            'max_drawdown': self.max_drawdown,
            'volatility': volatility,
            'sharpe_ratio': sharpe_ratio,
            'win_rate': win_rate,
            'total_trades': len(self.trades),
            'avg_holding_period': avg_holding_period,
            'current_value': values[-1] if values else self.initial_krw
        }

class TradingStrategy:
    """거래 전략 기본 클래스"""

    def __init__(self, name, account, ai_calculator, buy_threshold=90, sell_threshold=30):
        self.name = name
        self.account = account
        self.ai_calculator = ai_calculator
        self.buy_threshold = buy_threshold
        self.sell_threshold = sell_threshold

        # 손절/익절 설정
        self.stop_loss_pct = -0.05  # -5%
        self.take_profit_pct = 0.15  # +15%

    def should_buy(self, symbol, data, ai_score):
        """매수 신호 확인"""
        rsi = data.get('technical_indicators', {}).get('rsi')

        if rsi is None:
            return False, 0

        if ai_score >= self.buy_threshold:
            if self.name == "Conservative" and rsi < 30:
                return True, 0.10  # 자금의 10%
            elif self.name == "Balanced" and rsi < 40:
                return True, 0.15  # 자금의 15%
            elif self.name == "Aggressive" and rsi < 50:
                return True, 0.20  # 자금의 20%

        return False, 0

    def should_sell(self, symbol, data, ai_score):
        """매도 신호 확인"""
        if symbol not in self.account.holdings:
            return False

        # AI 점수 기반 매도
        if ai_score <= self.sell_threshold:
            return True

        return False

    def check_stop_loss_take_profit(self, symbol, current_price):
        """손절/익절 확인"""
        if symbol not in self.account.holdings:
            return False, ""

        holding = self.account.holdings[symbol]
        avg_price = holding['avg_price']
        return_pct = (current_price - avg_price) / avg_price

        if return_pct <= self.stop_loss_pct:
            return True, "STOP_LOSS"
        elif return_pct >= self.take_profit_pct:
            return True, "TAKE_PROFIT"

        return False, ""

    def execute_strategy(self, market_data):
        """전략 실행"""
        signals = []

        for symbol, data in market_data.items():
            try:
                ai_score = self.ai_calculator.calculate_score(data)
                current_price = data['current_price']

                # 손절/익절 확인
                should_exit, exit_reason = self.check_stop_loss_take_profit(symbol, current_price)
                if should_exit:
                    if symbol in self.account.holdings:
                        quantity = self.account.holdings[symbol]['quantity']
                        signals.append({
                            'action': 'SELL',
                            'symbol': symbol,
                            'price': current_price,
                            'quantity': quantity,
                            'reason': exit_reason,
                            'ai_score': ai_score
                        })

                # 매도 신호 확인
                elif self.should_sell(symbol, data, ai_score):
                    if symbol in self.account.holdings:
                        quantity = self.account.holdings[symbol]['quantity']
                        signals.append({
                            'action': 'SELL',
                            'symbol': symbol,
                            'price': current_price,
                            'quantity': quantity,
                            'reason': 'AI_SIGNAL_WEAK',
                            'ai_score': ai_score
                        })

                # 매수 신호 확인
                else:
                    should_buy, investment_ratio = self.should_buy(symbol, data, ai_score)
                    if should_buy:
                        currency = self.account.get_currency(symbol)
                        available_cash = self.account.cash_krw if currency == 'KRW' else self.account.cash_usd
                        investment_amount = available_cash * investment_ratio
                        quantity = int(investment_amount / current_price)

                        if quantity > 0:
                            signals.append({
                                'action': 'BUY',
                                'symbol': symbol,
                                'price': current_price,
                                'quantity': quantity,
                                'reason': f'AI_SIGNAL_{self.name.upper()}',
                                'ai_score': ai_score
                            })

            except Exception as e:
                continue

        return signals

class StrategyABTest:
    """A/B 테스트 관리자"""

    def __init__(self, test_duration_hours=24):
        self.start_time = datetime.now()
        self.test_duration = test_duration_hours
        self.running = False

        # AI 점수 계산기
        self.ai_calculator = AIScoreCalculator()

        # 3가지 전략 생성
        self.strategies = {
            'Conservative': TradingStrategy(
                "Conservative",
                VirtualAccount("Conservative"),
                self.ai_calculator,
                buy_threshold=90,  # 매우 높은 확신
                sell_threshold=40
            ),
            'Balanced': TradingStrategy(
                "Balanced",
                VirtualAccount("Balanced"),
                self.ai_calculator,
                buy_threshold=85,  # 높은 확신
                sell_threshold=35
            ),
            'Aggressive': TradingStrategy(
                "Aggressive",
                VirtualAccount("Aggressive"),
                self.ai_calculator,
                buy_threshold=80,  # 적당한 확신
                sell_threshold=30
            )
        }

        self.setup_directories()
        self.setup_logging()
        self.setup_database()

        # Flask 앱 설정
        self.app = Flask(__name__)
        self.setup_flask_routes()

        # 성과 비교 데이터
        self.hourly_comparisons = []

    def setup_directories(self):
        """필요한 디렉토리 생성"""
        directories = [
            'ab_test_reports',
            'ab_test_checkpoints',
            'ab_test_charts'
        ]

        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)

    def setup_logging(self):
        """로깅 설정"""
        today = datetime.now().strftime('%Y-%m-%d')
        log_file = f'ab_test_{today}.log'

        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )

        self.logger = logging.getLogger(__name__)

    def setup_database(self):
        """SQLite 데이터베이스 설정"""
        self.db_path = "ab_test_results.db"
        conn = sqlite3.connect(self.db_path)

        conn.execute('''
            CREATE TABLE IF NOT EXISTS strategy_trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                strategy_name TEXT NOT NULL,
                symbol TEXT NOT NULL,
                action TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                price REAL NOT NULL,
                reason TEXT,
                ai_score INTEGER,
                profit_loss REAL DEFAULT 0
            )
        ''')

        conn.execute('''
            CREATE TABLE IF NOT EXISTS strategy_performance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                strategy_name TEXT NOT NULL,
                total_value REAL,
                return_pct REAL,
                max_drawdown REAL,
                win_rate REAL,
                total_trades INTEGER,
                sharpe_ratio REAL
            )
        ''')

        conn.commit()
        conn.close()

    def setup_flask_routes(self):
        """Flask 웹 대시보드 라우트 설정"""
        @self.app.route('/')
        def dashboard():
            return render_template('ab_test_dashboard.html')

        @self.app.route('/api/ab_status')
        def api_ab_status():
            return jsonify(self.get_ab_test_status())

        @self.app.route('/api/performance_comparison')
        def api_performance_comparison():
            return jsonify(self.get_performance_comparison())

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

    def execute_trade(self, strategy_name, signal):
        """거래 실행 및 DB 저장"""
        try:
            strategy = self.strategies[strategy_name]
            account = strategy.account

            if signal['action'] == 'BUY':
                success, message = account.buy(
                    signal['symbol'],
                    signal['price'],
                    signal['quantity'],
                    signal['reason'],
                    signal['ai_score']
                )
            else:  # SELL
                success, message = account.sell(
                    signal['symbol'],
                    signal['price'],
                    signal.get('quantity'),
                    signal['reason'],
                    signal['ai_score']
                )

            if success:
                # DB에 거래 기록
                conn = sqlite3.connect(self.db_path)

                profit_loss = 0
                if signal['action'] == 'SELL' and len(account.trades) > 0:
                    last_trade = account.trades[-1]
                    profit_loss = last_trade.get('profit_loss', 0)

                conn.execute('''
                    INSERT INTO strategy_trades
                    (strategy_name, symbol, action, quantity, price, reason, ai_score, profit_loss)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (strategy_name, signal['symbol'], signal['action'],
                      signal['quantity'], signal['price'], signal['reason'],
                      signal['ai_score'], profit_loss))

                conn.commit()
                conn.close()

                self.logger.info(f"✅ {strategy_name}: {message}")

            return success, message

        except Exception as e:
            self.logger.error(f"Error executing trade for {strategy_name}: {e}")
            return False, str(e)

    def run_ab_test_cycle(self):
        """A/B 테스트 사이클 실행"""
        try:
            # 실시간 데이터 로드
            market_data = self.load_realtime_data()

            if not market_data:
                self.logger.warning("No market data available")
                return

            # 각 전략별로 신호 생성 및 실행
            for strategy_name, strategy in self.strategies.items():
                try:
                    # 포트폴리오 이력 업데이트
                    strategy.account.update_portfolio_history(market_data)

                    # 매매 신호 생성
                    signals = strategy.execute_strategy(market_data)

                    # 신호 실행
                    for signal in signals:
                        self.execute_trade(strategy_name, signal)
                        time.sleep(0.1)  # API 제한 방지

                except Exception as e:
                    self.logger.error(f"Error in strategy {strategy_name}: {e}")
                    continue

            # 성과 업데이트
            self.update_performance_records()

        except Exception as e:
            self.logger.error(f"Error in AB test cycle: {e}")

    def update_performance_records(self):
        """성과 기록 업데이트"""
        try:
            conn = sqlite3.connect(self.db_path)

            for strategy_name, strategy in self.strategies.items():
                metrics = strategy.account.get_performance_metrics()

                if metrics:
                    conn.execute('''
                        INSERT INTO strategy_performance
                        (strategy_name, total_value, return_pct, max_drawdown,
                         win_rate, total_trades, sharpe_ratio)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        strategy_name,
                        metrics['current_value'],
                        metrics['current_return'],
                        metrics['max_drawdown'],
                        metrics['win_rate'],
                        metrics['total_trades'],
                        metrics['sharpe_ratio']
                    ))

            conn.commit()
            conn.close()

        except Exception as e:
            self.logger.error(f"Error updating performance records: {e}")

    def create_hourly_comparison(self):
        """시간별 성과 비교"""
        try:
            comparison = {
                'timestamp': datetime.now().isoformat(),
                'runtime_hours': (datetime.now() - self.start_time).total_seconds() / 3600
            }

            strategy_results = {}

            for strategy_name, strategy in self.strategies.items():
                metrics = strategy.account.get_performance_metrics()

                strategy_results[strategy_name] = {
                    'return_pct': metrics.get('current_return', 0),
                    'win_rate': metrics.get('win_rate', 0),
                    'total_trades': metrics.get('total_trades', 0),
                    'max_drawdown': metrics.get('max_drawdown', 0),
                    'sharpe_ratio': metrics.get('sharpe_ratio', 0),
                    'current_value': metrics.get('current_value', 10000000)
                }

            comparison['strategies'] = strategy_results

            # 순위 계산
            ranked_strategies = sorted(
                strategy_results.items(),
                key=lambda x: x[1]['return_pct'],
                reverse=True
            )

            comparison['ranking'] = [name for name, _ in ranked_strategies]

            # 통계적 유의성 검증
            comparison['statistical_significance'] = self.calculate_statistical_significance()

            self.hourly_comparisons.append(comparison)

            # 체크포인트 저장
            checkpoint_file = f"ab_test_checkpoints/comparison_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
            with open(checkpoint_file, 'w') as f:
                json.dump(comparison, f, indent=2)

            # 콘솔 출력
            self.display_comparison(comparison)

            # 차트 업데이트
            self.update_comparison_charts()

        except Exception as e:
            self.logger.error(f"Error creating hourly comparison: {e}")

    def calculate_statistical_significance(self):
        """통계적 유의성 계산"""
        try:
            # 각 전략의 시간별 수익률 데이터 수집
            strategy_returns = {}

            for strategy_name, strategy in self.strategies.items():
                returns = []
                history = strategy.account.portfolio_history

                if len(history) > 1:
                    for i in range(1, len(history)):
                        prev_value = history[i-1]['total_value']
                        curr_value = history[i]['total_value']
                        period_return = (curr_value - prev_value) / prev_value
                        returns.append(period_return)

                strategy_returns[strategy_name] = returns

            # 최소 10개 데이터 포인트 필요
            min_data_points = min(len(returns) for returns in strategy_returns.values())

            if min_data_points < 10:
                return {'p_value': 1.0, 'significant': False, 'note': 'Insufficient data'}

            # 일원분산분석 (ANOVA) 수행
            returns_arrays = [np.array(returns) for returns in strategy_returns.values()]
            f_stat, p_value = stats.f_oneway(*returns_arrays)

            return {
                'p_value': p_value,
                'f_statistic': f_stat,
                'significant': p_value < 0.05,
                'confidence_level': 0.95
            }

        except Exception as e:
            self.logger.error(f"Error calculating statistical significance: {e}")
            return {'p_value': 1.0, 'significant': False, 'note': 'Calculation error'}

    def display_comparison(self, comparison):
        """비교 결과 콘솔 출력"""
        os.system('clear' if os.name == 'posix' else 'cls')

        runtime = comparison['runtime_hours']
        ranking = comparison['ranking']
        strategies = comparison['strategies']

        print("=" * 50)
        print("     A/B 테스트 실시간 현황")
        print("=" * 50)
        print(f"운영 시간: {int(runtime)}:{int((runtime % 1) * 60):02d}:{int(((runtime % 1) * 60 % 1) * 60):02d}")
        print()

        # 순위별 출력
        medals = ['🥇', '🥈', '🥉']

        for i, strategy_name in enumerate(ranking):
            medal = medals[i] if i < 3 else f"{i+1}."
            strategy_data = strategies[strategy_name]

            return_pct = strategy_data['return_pct']
            win_rate = strategy_data['win_rate']

            print(f"{medal} 전략 {strategy_name}: {return_pct:+.2f}% | 승률 {win_rate:.0f}%")

        print()
        print("최근 1시간 성과:")

        for strategy_name in ranking:
            strategy_data = strategies[strategy_name]
            trades = strategy_data['total_trades']
            return_pct = strategy_data['return_pct']

            print(f"- 전략 {strategy_name}: 거래 {trades}건, {return_pct:+.1f}%")

        # 통계적 유의성
        sig_test = comparison.get('statistical_significance', {})
        p_value = sig_test.get('p_value', 1.0)
        significant = sig_test.get('significant', False)

        print()
        print(f"통계적 유의성: p={p_value:.3f} ({'유의함' if significant else '유의하지 않음'})")
        print("=" * 50)

    def update_comparison_charts(self):
        """비교 차트 업데이트"""
        try:
            if len(self.hourly_comparisons) < 2:
                return

            # 데이터 준비
            timestamps = [datetime.fromisoformat(comp['timestamp']) for comp in self.hourly_comparisons]

            strategy_data = {}
            for strategy_name in self.strategies.keys():
                strategy_data[strategy_name] = {
                    'returns': [comp['strategies'][strategy_name]['return_pct'] for comp in self.hourly_comparisons],
                    'win_rates': [comp['strategies'][strategy_name]['win_rate'] for comp in self.hourly_comparisons],
                    'trades': [comp['strategies'][strategy_name]['total_trades'] for comp in self.hourly_comparisons]
                }

            # 차트 생성
            fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))

            # 수익률 비교
            colors = ['blue', 'green', 'red']
            for i, (strategy_name, data) in enumerate(strategy_data.items()):
                ax1.plot(timestamps, data['returns'],
                        color=colors[i], linewidth=2, label=f'전략 {strategy_name}')

            ax1.set_title('전략별 수익률 비교')
            ax1.set_ylabel('수익률 (%)')
            ax1.legend()
            ax1.grid(True, alpha=0.3)

            # 승률 비교
            for i, (strategy_name, data) in enumerate(strategy_data.items()):
                ax2.plot(timestamps, data['win_rates'],
                        color=colors[i], linewidth=2, label=f'전략 {strategy_name}')

            ax2.set_title('전략별 승률 비교')
            ax2.set_ylabel('승률 (%)')
            ax2.legend()
            ax2.grid(True, alpha=0.3)

            # 거래 횟수 비교
            for i, (strategy_name, data) in enumerate(strategy_data.items()):
                ax3.plot(timestamps, data['trades'],
                        color=colors[i], linewidth=2, label=f'전략 {strategy_name}')

            ax3.set_title('전략별 거래 횟수')
            ax3.set_ylabel('총 거래 수')
            ax3.legend()
            ax3.grid(True, alpha=0.3)

            # 최종 성과 막대 그래프
            final_returns = [strategy_data[name]['returns'][-1] for name in self.strategies.keys()]
            strategy_names = list(self.strategies.keys())

            bars = ax4.bar(strategy_names, final_returns, color=colors)
            ax4.set_title('최종 수익률 비교')
            ax4.set_ylabel('수익률 (%)')

            # 막대 위에 값 표시
            for bar, value in zip(bars, final_returns):
                ax4.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1,
                        f'{value:.1f}%', ha='center', va='bottom')

            plt.tight_layout()
            plt.savefig('ab_test_charts/strategy_comparison.png', dpi=300, bbox_inches='tight')
            plt.close()

        except Exception as e:
            self.logger.error(f"Error updating comparison charts: {e}")

    def create_ab_test_dashboard_template(self):
        """A/B 테스트 대시보드 HTML 템플릿 생성"""
        templates_dir = Path('templates')
        templates_dir.mkdir(exist_ok=True)

        dashboard_html = '''
<!DOCTYPE html>
<html>
<head>
    <title>A/B 전략 테스트</title>
    <meta charset="utf-8">
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
        .container { max-width: 1400px; margin: 0 auto; }
        .header { text-align: center; margin-bottom: 30px; background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
        .strategy-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; margin-bottom: 30px; }
        .strategy-card { background: white; border-radius: 10px; padding: 20px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); text-align: center; }
        .strategy-card.rank-1 { border-top: 5px solid #FFD700; }
        .strategy-card.rank-2 { border-top: 5px solid #C0C0C0; }
        .strategy-card.rank-3 { border-top: 5px solid #CD7F32; }
        .strategy-name { font-size: 1.5em; font-weight: bold; margin-bottom: 10px; }
        .strategy-return { font-size: 2em; font-weight: bold; margin: 10px 0; }
        .positive { color: #28a745; }
        .negative { color: #dc3545; }
        .neutral { color: #6c757d; }
        .chart-container { background: white; border-radius: 10px; padding: 20px; margin-bottom: 20px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
        .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-top: 20px; }
        .stat-item { text-align: center; }
        .stat-value { font-size: 1.5em; font-weight: bold; }
        .stat-label { color: #666; margin-top: 5px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🏆 A/B 전략 테스트 대시보드</h1>
            <div id="runtime">운영 시간: --</div>
        </div>

        <div class="strategy-grid">
            <div class="strategy-card" id="conservative-card">
                <div class="strategy-name">보수적 전략</div>
                <div class="strategy-return" id="conservative-return">--</div>
                <div class="stats-grid">
                    <div class="stat-item">
                        <div class="stat-value" id="conservative-winrate">--</div>
                        <div class="stat-label">승률</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value" id="conservative-trades">--</div>
                        <div class="stat-label">거래수</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value" id="conservative-sharpe">--</div>
                        <div class="stat-label">샤프비율</div>
                    </div>
                </div>
            </div>

            <div class="strategy-card" id="balanced-card">
                <div class="strategy-name">균형 전략</div>
                <div class="strategy-return" id="balanced-return">--</div>
                <div class="stats-grid">
                    <div class="stat-item">
                        <div class="stat-value" id="balanced-winrate">--</div>
                        <div class="stat-label">승률</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value" id="balanced-trades">--</div>
                        <div class="stat-label">거래수</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value" id="balanced-sharpe">--</div>
                        <div class="stat-label">샤프비율</div>
                    </div>
                </div>
            </div>

            <div class="strategy-card" id="aggressive-card">
                <div class="strategy-name">공격적 전략</div>
                <div class="strategy-return" id="aggressive-return">--</div>
                <div class="stats-grid">
                    <div class="stat-item">
                        <div class="stat-value" id="aggressive-winrate">--</div>
                        <div class="stat-label">승률</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value" id="aggressive-trades">--</div>
                        <div class="stat-label">거래수</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value" id="aggressive-sharpe">--</div>
                        <div class="stat-label">샤프비율</div>
                    </div>
                </div>
            </div>
        </div>

        <div class="chart-container">
            <h3>실시간 수익률 비교</h3>
            <div id="performance-chart"></div>
        </div>

        <div class="chart-container">
            <h3>통계적 유의성</h3>
            <div id="significance-info">분석 중...</div>
        </div>
    </div>

    <script>
        function updateDashboard() {
            fetch('/api/ab_status')
                .then(response => response.json())
                .then(data => {
                    // 운영 시간 업데이트
                    const runtime = data.runtime_hours || 0;
                    const hours = Math.floor(runtime);
                    const minutes = Math.floor((runtime % 1) * 60);
                    const seconds = Math.floor(((runtime % 1) * 60 % 1) * 60);
                    document.getElementById('runtime').innerHTML =
                        `운영 시간: ${hours}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;

                    // 전략별 데이터 업데이트
                    if (data.strategies) {
                        updateStrategyCard('conservative', data.strategies.Conservative, data.ranking);
                        updateStrategyCard('balanced', data.strategies.Balanced, data.ranking);
                        updateStrategyCard('aggressive', data.strategies.Aggressive, data.ranking);
                    }

                    // 통계적 유의성
                    if (data.statistical_significance) {
                        const sig = data.statistical_significance;
                        const sigText = sig.significant ?
                            `통계적으로 유의함 (p=${sig.p_value.toFixed(3)})` :
                            `통계적으로 유의하지 않음 (p=${sig.p_value.toFixed(3)})`;
                        document.getElementById('significance-info').innerHTML = sigText;
                    }
                });

            fetch('/api/performance_comparison')
                .then(response => response.json())
                .then(data => {
                    if (data.timestamps && data.timestamps.length > 0) {
                        const traces = [];
                        const colors = ['blue', 'green', 'red'];
                        const strategies = ['Conservative', 'Balanced', 'Aggressive'];

                        strategies.forEach((strategy, index) => {
                            if (data[strategy]) {
                                traces.push({
                                    x: data.timestamps,
                                    y: data[strategy],
                                    type: 'scatter',
                                    mode: 'lines+markers',
                                    name: `전략 ${strategy}`,
                                    line: {color: colors[index], width: 3}
                                });
                            }
                        });

                        const layout = {
                            title: '',
                            xaxis: {title: '시간'},
                            yaxis: {title: '수익률 (%)'},
                            showlegend: true,
                            height: 400
                        };

                        Plotly.newPlot('performance-chart', traces, layout);
                    }
                });
        }

        function updateStrategyCard(strategy, data, ranking) {
            const returnValue = data.return_pct || 0;
            const returnClass = returnValue > 0 ? 'positive' : returnValue < 0 ? 'negative' : 'neutral';

            document.getElementById(`${strategy}-return`).innerHTML = `${returnValue > 0 ? '+' : ''}${returnValue.toFixed(2)}%`;
            document.getElementById(`${strategy}-return`).className = `strategy-return ${returnClass}`;

            document.getElementById(`${strategy}-winrate`).innerHTML = `${(data.win_rate || 0).toFixed(1)}%`;
            document.getElementById(`${strategy}-trades`).innerHTML = `${data.total_trades || 0}건`;
            document.getElementById(`${strategy}-sharpe`).innerHTML = `${(data.sharpe_ratio || 0).toFixed(2)}`;

            // 순위에 따른 카드 스타일
            const card = document.getElementById(`${strategy}-card`);
            card.className = 'strategy-card';

            const strategyNames = {'conservative': 'Conservative', 'balanced': 'Balanced', 'aggressive': 'Aggressive'};
            const rank = ranking.indexOf(strategyNames[strategy]) + 1;
            if (rank <= 3) {
                card.classList.add(`rank-${rank}`);
            }
        }

        // 초기 로드 및 5초마다 업데이트
        updateDashboard();
        setInterval(updateDashboard, 5000);
    </script>
</body>
</html>
        '''

        with open(templates_dir / 'ab_test_dashboard.html', 'w', encoding='utf-8') as f:
            f.write(dashboard_html)

    def get_ab_test_status(self):
        """A/B 테스트 상태 조회 (API용)"""
        runtime = (datetime.now() - self.start_time).total_seconds() / 3600

        strategy_data = {}
        for strategy_name, strategy in self.strategies.items():
            metrics = strategy.account.get_performance_metrics()
            strategy_data[strategy_name] = metrics

        # 순위 계산
        ranking = sorted(
            strategy_data.items(),
            key=lambda x: x[1].get('current_return', 0),
            reverse=True
        )

        return {
            'runtime_hours': runtime,
            'strategies': strategy_data,
            'ranking': [name for name, _ in ranking],
            'statistical_significance': self.calculate_statistical_significance() if len(self.hourly_comparisons) > 0 else None
        }

    def get_performance_comparison(self):
        """성과 비교 데이터 조회 (API용)"""
        if not self.hourly_comparisons:
            return {'timestamps': []}

        timestamps = [comp['timestamp'] for comp in self.hourly_comparisons]

        comparison_data = {'timestamps': timestamps}

        for strategy_name in self.strategies.keys():
            comparison_data[strategy_name] = [
                comp['strategies'][strategy_name]['return_pct']
                for comp in self.hourly_comparisons
            ]

        return comparison_data

    def start_web_dashboard(self):
        """웹 대시보드 시작"""
        def run_flask():
            self.app.run(host='0.0.0.0', port=8888, debug=False, use_reloader=False)

        flask_thread = threading.Thread(target=run_flask, daemon=True)
        flask_thread.start()

        self.logger.info("🌐 A/B Test dashboard started at http://localhost:8888")

    def generate_final_ab_report(self):
        """최종 A/B 테스트 리포트 생성"""
        try:
            runtime = (datetime.now() - self.start_time).total_seconds() / 3600

            # 최종 성과 수집
            final_results = {}
            for strategy_name, strategy in self.strategies.items():
                metrics = strategy.account.get_performance_metrics()

                final_results[strategy_name] = {
                    'final_return': metrics.get('current_return', 0),
                    'max_drawdown': metrics.get('max_drawdown', 0),
                    'win_rate': metrics.get('win_rate', 0),
                    'total_trades': metrics.get('total_trades', 0),
                    'sharpe_ratio': metrics.get('sharpe_ratio', 0),
                    'volatility': metrics.get('volatility', 0),
                    'avg_holding_period': metrics.get('avg_holding_period', 0),
                    'final_value': metrics.get('current_value', 10000000)
                }

            # 최고 전략 선정
            best_strategy = max(final_results.items(), key=lambda x: x[1]['final_return'])

            # 통계적 유의성
            statistical_test = self.calculate_statistical_significance()

            # 최적 매개변수 분석
            optimization_suggestions = self.generate_optimization_suggestions(final_results)

            final_report = {
                'test_summary': {
                    'start_time': self.start_time.isoformat(),
                    'end_time': datetime.now().isoformat(),
                    'duration_hours': runtime,
                    'total_checkpoints': len(self.hourly_comparisons)
                },
                'strategy_results': final_results,
                'winner': {
                    'strategy': best_strategy[0],
                    'final_return': best_strategy[1]['final_return'],
                    'reason': self.analyze_winning_factors(best_strategy[0], final_results)
                },
                'statistical_analysis': statistical_test,
                'optimization_suggestions': optimization_suggestions,
                'risk_analysis': self.analyze_risk_metrics(final_results)
            }

            # 리포트 저장
            report_file = f"ab_test_reports/final_ab_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(final_report, f, indent=2, ensure_ascii=False)

            # 콘솔 출력
            self.display_final_ab_report(final_report)

            self.logger.info(f"✅ Final A/B test report saved to {report_file}")

        except Exception as e:
            self.logger.error(f"Error generating final A/B report: {e}")

    def generate_optimization_suggestions(self, results):
        """최적화 제안 생성"""
        suggestions = []

        # 수익률 기반 분석
        best_return = max(results.values(), key=lambda x: x['final_return'])['final_return']

        for strategy_name, metrics in results.items():
            if metrics['final_return'] < best_return * 0.8:  # 최고 대비 80% 미만
                if metrics['win_rate'] < 60:
                    suggestions.append(f"{strategy_name}: 승률이 낮음. 매수 임계값을 높이거나 손절 규칙을 강화하세요.")

                if metrics['total_trades'] < 10:
                    suggestions.append(f"{strategy_name}: 거래 빈도가 낮음. 매수 임계값을 낮추거나 신호 감도를 조정하세요.")

                if metrics['max_drawdown'] > 10:
                    suggestions.append(f"{strategy_name}: 최대 낙폭이 높음. 리스크 관리를 강화하세요.")

        if not suggestions:
            suggestions.append("모든 전략이 균형잡힌 성과를 보였습니다. 현재 설정을 유지하세요.")

        return suggestions

    def analyze_winning_factors(self, winning_strategy, results):
        """승리 요인 분석"""
        winner_metrics = results[winning_strategy]
        factors = []

        if winner_metrics['win_rate'] > 70:
            factors.append("높은 승률")

        if winner_metrics['sharpe_ratio'] > 1.0:
            factors.append("우수한 리스크 대비 수익률")

        if winner_metrics['max_drawdown'] < 5:
            factors.append("낮은 최대 낙폭")

        if winner_metrics['total_trades'] > 20:
            factors.append("적절한 거래 빈도")

        return factors if factors else ["전반적으로 균형잡힌 성과"]

    def analyze_risk_metrics(self, results):
        """리스크 지표 분석"""
        risk_analysis = {}

        for strategy_name, metrics in results.items():
            risk_score = 0

            # 최대 낙폭 점수 (낮을수록 좋음)
            if metrics['max_drawdown'] < 3:
                risk_score += 30
            elif metrics['max_drawdown'] < 5:
                risk_score += 20
            elif metrics['max_drawdown'] < 10:
                risk_score += 10

            # 샤프 비율 점수 (높을수록 좋음)
            if metrics['sharpe_ratio'] > 1.5:
                risk_score += 30
            elif metrics['sharpe_ratio'] > 1.0:
                risk_score += 20
            elif metrics['sharpe_ratio'] > 0.5:
                risk_score += 10

            # 변동성 점수 (적절한 수준이 좋음)
            volatility = metrics.get('volatility', 0)
            if 2 < volatility < 8:
                risk_score += 20
            elif volatility <= 2:
                risk_score += 10

            risk_analysis[strategy_name] = {
                'risk_score': risk_score,
                'risk_level': 'Low' if risk_score > 50 else 'Medium' if risk_score > 30 else 'High'
            }

        return risk_analysis

    def display_final_ab_report(self, report):
        """최종 A/B 리포트 콘솔 출력"""
        print("\n" + "=" * 60)
        print("🏆 A/B 테스트 최종 리포트")
        print("=" * 60)

        duration = report['test_summary']['duration_hours']
        print(f"테스트 기간: {duration:.1f}시간")

        # 승리 전략
        winner = report['winner']
        print(f"\n🥇 최고 전략: {winner['strategy']}")
        print(f"최종 수익률: {winner['final_return']:+.2f}%")
        print(f"승리 요인: {', '.join(winner['reason'])}")

        # 전략별 상세 결과
        print(f"\n📊 전략별 상세 결과:")
        results = report['strategy_results']

        for strategy_name, metrics in results.items():
            print(f"\n{strategy_name}:")
            print(f"  수익률: {metrics['final_return']:+.2f}%")
            print(f"  승률: {metrics['win_rate']:.1f}%")
            print(f"  최대낙폭: {metrics['max_drawdown']:.2f}%")
            print(f"  샤프비율: {metrics['sharpe_ratio']:.2f}")
            print(f"  총 거래: {metrics['total_trades']}건")

        # 통계적 유의성
        stat_test = report['statistical_analysis']
        print(f"\n📈 통계적 분석:")
        if stat_test.get('significant', False):
            print(f"  결과가 통계적으로 유의함 (p={stat_test['p_value']:.3f})")
        else:
            print(f"  결과가 통계적으로 유의하지 않음 (p={stat_test.get('p_value', 1.0):.3f})")

        # 최적화 제안
        print(f"\n💡 최적화 제안:")
        for suggestion in report['optimization_suggestions']:
            print(f"  • {suggestion}")

        print("=" * 60)

    def run_ab_test(self, duration_hours=24):
        """A/B 테스트 실행"""
        self.running = True

        print("🚀 A/B 전략 테스트 시작")
        print("=" * 50)
        print("전략 A (보수적): AI 90+ 매수")
        print("전략 B (균형): AI 85+ 매수")
        print("전략 C (공격적): AI 80+ 매수")
        print("=" * 50)

        # 웹 대시보드 템플릿 생성
        self.create_ab_test_dashboard_template()

        # 웹 대시보드 시작
        self.start_web_dashboard()

        end_time = self.start_time + timedelta(hours=duration_hours)
        next_comparison = self.start_time + timedelta(hours=1)

        try:
            while self.running and datetime.now() < end_time:
                current_time = datetime.now()

                # A/B 테스트 사이클 실행
                self.run_ab_test_cycle()

                # 시간별 비교
                if current_time >= next_comparison:
                    self.create_hourly_comparison()
                    next_comparison += timedelta(hours=1)

                # 1분마다 체크
                time.sleep(60)

            # 테스트 완료 - 최종 리포트
            if not self.running:
                self.logger.info("A/B test stopped by user")
            else:
                self.logger.info("✅ A/B test completed")
                self.generate_final_ab_report()

        except KeyboardInterrupt:
            self.logger.info("A/B test stopped by user")

        finally:
            self.running = False

        return True

def main():
    parser = argparse.ArgumentParser(description='Strategy A/B Testing System')
    parser.add_argument('--duration', type=int, default=24,
                       help='Test duration in hours (default: 24)')

    args = parser.parse_args()

    print("🏆 전략 A/B 테스트 시스템")
    print("=" * 50)
    print(f"⏰ 테스트 기간: {args.duration}시간")
    print("🌐 대시보드: http://localhost:8888")
    print("=" * 50)

    ab_test = StrategyABTest(args.duration)

    try:
        ab_test.run_ab_test(args.duration)
    except KeyboardInterrupt:
        print("\n프로그램을 종료합니다...")
        ab_test.running = False

if __name__ == "__main__":
    main()