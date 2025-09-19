import pandas as pd
import numpy as np
import yfinance as yf
import json
from datetime import datetime, timedelta
import concurrent.futures
import warnings
warnings.filterwarnings('ignore')

class ProfitStrategyFinder:
    def __init__(self):
        self.min_win_rate = 0.70
        self.strategies = {}
        self.results = {}

    def fetch_stock_data(self, symbol, period="1y"):
        """주식 데이터 가져오기 (한국/미국)"""
        try:
            if symbol.endswith('.KS') or symbol.endswith('.KQ'):
                ticker = yf.Ticker(symbol)
            else:
                ticker = yf.Ticker(symbol)

            data = ticker.history(period=period)
            if len(data) < 50:
                return None

            return data
        except:
            return None

    def calculate_rsi(self, prices, period=14):
        """RSI 계산"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))

    def calculate_macd(self, prices, fast=12, slow=26, signal=9):
        """MACD 계산"""
        exp1 = prices.ewm(span=fast).mean()
        exp2 = prices.ewm(span=slow).mean()
        macd = exp1 - exp2
        signal_line = macd.ewm(span=signal).mean()
        return macd, signal_line

    def calculate_bollinger_bands(self, prices, period=20):
        """볼린저 밴드 계산"""
        sma = prices.rolling(window=period).mean()
        std = prices.rolling(window=period).std()
        upper = sma + (std * 2)
        lower = sma - (std * 2)
        return upper, lower, sma

    def calculate_moving_averages(self, prices, short=20, long=50):
        """이동평균 계산"""
        ma_short = prices.rolling(window=short).mean()
        ma_long = prices.rolling(window=long).mean()
        return ma_short, ma_long

    def strategy_rsi_oversold(self, data):
        """RSI 과매도 전략 (30 이하 매수, 70 이상 매도)"""
        rsi = self.calculate_rsi(data['Close'])
        signals = []

        for i in range(1, len(data)):
            if rsi.iloc[i] < 30 and rsi.iloc[i-1] >= 30:
                signals.append({'date': data.index[i], 'action': 'buy', 'price': data['Close'].iloc[i]})
            elif rsi.iloc[i] > 70 and rsi.iloc[i-1] <= 70:
                signals.append({'date': data.index[i], 'action': 'sell', 'price': data['Close'].iloc[i]})

        return signals

    def strategy_golden_cross(self, data):
        """골든크로스 전략 (20일선이 50일선 돌파)"""
        ma20, ma50 = self.calculate_moving_averages(data['Close'], 20, 50)
        signals = []

        for i in range(1, len(data)):
            if ma20.iloc[i] > ma50.iloc[i] and ma20.iloc[i-1] <= ma50.iloc[i-1]:
                signals.append({'date': data.index[i], 'action': 'buy', 'price': data['Close'].iloc[i]})
            elif ma20.iloc[i] < ma50.iloc[i] and ma20.iloc[i-1] >= ma50.iloc[i-1]:
                signals.append({'date': data.index[i], 'action': 'sell', 'price': data['Close'].iloc[i]})

        return signals

    def strategy_bollinger_breakout(self, data):
        """볼린저 밴드 돌파 전략"""
        upper, lower, sma = self.calculate_bollinger_bands(data['Close'])
        signals = []

        for i in range(1, len(data)):
            if data['Close'].iloc[i] > upper.iloc[i] and data['Close'].iloc[i-1] <= upper.iloc[i-1]:
                signals.append({'date': data.index[i], 'action': 'buy', 'price': data['Close'].iloc[i]})
            elif data['Close'].iloc[i] < lower.iloc[i] and data['Close'].iloc[i-1] >= lower.iloc[i-1]:
                signals.append({'date': data.index[i], 'action': 'sell', 'price': data['Close'].iloc[i]})

        return signals

    def strategy_macd_signal(self, data):
        """MACD 시그널 전략"""
        macd, signal = self.calculate_macd(data['Close'])
        signals = []

        for i in range(1, len(data)):
            if macd.iloc[i] > signal.iloc[i] and macd.iloc[i-1] <= signal.iloc[i-1]:
                signals.append({'date': data.index[i], 'action': 'buy', 'price': data['Close'].iloc[i]})
            elif macd.iloc[i] < signal.iloc[i] and macd.iloc[i-1] >= signal.iloc[i-1]:
                signals.append({'date': data.index[i], 'action': 'sell', 'price': data['Close'].iloc[i]})

        return signals

    def strategy_volume_spike(self, data):
        """거래량 급증 전략"""
        volume_ma = data['Volume'].rolling(window=20).mean()
        signals = []

        for i in range(20, len(data)):
            if data['Volume'].iloc[i] > volume_ma.iloc[i] * 2:
                signals.append({'date': data.index[i], 'action': 'buy', 'price': data['Close'].iloc[i]})

        return signals

    def strategy_momentum_reversal(self, data):
        """모멘텀 반전 전략"""
        momentum = data['Close'].pct_change(periods=5)
        signals = []

        for i in range(5, len(data)):
            if momentum.iloc[i] > 0.05 and momentum.iloc[i-1] <= 0:
                signals.append({'date': data.index[i], 'action': 'buy', 'price': data['Close'].iloc[i]})
            elif momentum.iloc[i] < -0.05 and momentum.iloc[i-1] >= 0:
                signals.append({'date': data.index[i], 'action': 'sell', 'price': data['Close'].iloc[i]})

        return signals

    def strategy_mean_reversion(self, data):
        """평균회귀 전략"""
        sma20 = data['Close'].rolling(window=20).mean()
        std20 = data['Close'].rolling(window=20).std()
        signals = []

        for i in range(20, len(data)):
            if data['Close'].iloc[i] < sma20.iloc[i] - 2 * std20.iloc[i]:
                signals.append({'date': data.index[i], 'action': 'buy', 'price': data['Close'].iloc[i]})
            elif data['Close'].iloc[i] > sma20.iloc[i] + 2 * std20.iloc[i]:
                signals.append({'date': data.index[i], 'action': 'sell', 'price': data['Close'].iloc[i]})

        return signals

    def strategy_stochastic_oscillator(self, data):
        """스토캐스틱 오실레이터 전략"""
        high14 = data['High'].rolling(window=14).max()
        low14 = data['Low'].rolling(window=14).min()
        k_percent = ((data['Close'] - low14) / (high14 - low14)) * 100
        d_percent = k_percent.rolling(window=3).mean()
        signals = []

        for i in range(1, len(data)):
            if k_percent.iloc[i] < 20 and k_percent.iloc[i-1] >= 20:
                signals.append({'date': data.index[i], 'action': 'buy', 'price': data['Close'].iloc[i]})
            elif k_percent.iloc[i] > 80 and k_percent.iloc[i-1] <= 80:
                signals.append({'date': data.index[i], 'action': 'sell', 'price': data['Close'].iloc[i]})

        return signals

    def strategy_williams_r(self, data):
        """윌리엄스 %R 전략"""
        high14 = data['High'].rolling(window=14).max()
        low14 = data['Low'].rolling(window=14).min()
        williams_r = ((high14 - data['Close']) / (high14 - low14)) * -100
        signals = []

        for i in range(1, len(data)):
            if williams_r.iloc[i] > -20 and williams_r.iloc[i-1] <= -20:
                signals.append({'date': data.index[i], 'action': 'sell', 'price': data['Close'].iloc[i]})
            elif williams_r.iloc[i] < -80 and williams_r.iloc[i-1] >= -80:
                signals.append({'date': data.index[i], 'action': 'buy', 'price': data['Close'].iloc[i]})

        return signals

    def strategy_cci(self, data):
        """CCI(Commodity Channel Index) 전략"""
        tp = (data['High'] + data['Low'] + data['Close']) / 3
        sma = tp.rolling(window=20).mean()
        md = tp.rolling(window=20).apply(lambda x: np.mean(np.abs(x - x.mean())))
        cci = (tp - sma) / (0.015 * md)
        signals = []

        for i in range(1, len(data)):
            if cci.iloc[i] > 100 and cci.iloc[i-1] <= 100:
                signals.append({'date': data.index[i], 'action': 'buy', 'price': data['Close'].iloc[i]})
            elif cci.iloc[i] < -100 and cci.iloc[i-1] >= -100:
                signals.append({'date': data.index[i], 'action': 'sell', 'price': data['Close'].iloc[i]})

        return signals

    def strategy_atr_breakout(self, data):
        """ATR 브레이크아웃 전략"""
        high_low = data['High'] - data['Low']
        high_close = np.abs(data['High'] - data['Close'].shift())
        low_close = np.abs(data['Low'] - data['Close'].shift())
        tr = np.maximum(high_low, np.maximum(high_close, low_close))
        atr = tr.rolling(window=14).mean()
        signals = []

        for i in range(14, len(data)):
            if data['Close'].iloc[i] > data['Close'].iloc[i-1] + atr.iloc[i]:
                signals.append({'date': data.index[i], 'action': 'buy', 'price': data['Close'].iloc[i]})

        return signals

    def strategy_donchian_channel(self, data):
        """돈치안 채널 전략"""
        high20 = data['High'].rolling(window=20).max()
        low20 = data['Low'].rolling(window=20).min()
        signals = []

        for i in range(20, len(data)):
            if data['Close'].iloc[i] > high20.iloc[i-1]:
                signals.append({'date': data.index[i], 'action': 'buy', 'price': data['Close'].iloc[i]})
            elif data['Close'].iloc[i] < low20.iloc[i-1]:
                signals.append({'date': data.index[i], 'action': 'sell', 'price': data['Close'].iloc[i]})

        return signals

    def strategy_price_channel(self, data):
        """가격 채널 전략"""
        high_channel = data['High'].rolling(window=20).max()
        low_channel = data['Low'].rolling(window=20).min()
        mid_channel = (high_channel + low_channel) / 2
        signals = []

        for i in range(20, len(data)):
            if data['Close'].iloc[i] > high_channel.iloc[i-1]:
                signals.append({'date': data.index[i], 'action': 'buy', 'price': data['Close'].iloc[i]})
            elif data['Close'].iloc[i] < low_channel.iloc[i-1]:
                signals.append({'date': data.index[i], 'action': 'sell', 'price': data['Close'].iloc[i]})

        return signals

    def strategy_elder_ray(self, data):
        """엘더 레이 전략"""
        ema13 = data['Close'].ewm(span=13).mean()
        bull_power = data['High'] - ema13
        bear_power = data['Low'] - ema13
        signals = []

        for i in range(1, len(data)):
            if bull_power.iloc[i] > 0 and bear_power.iloc[i] > bear_power.iloc[i-1]:
                signals.append({'date': data.index[i], 'action': 'buy', 'price': data['Close'].iloc[i]})
            elif bear_power.iloc[i] < 0 and bull_power.iloc[i] < bull_power.iloc[i-1]:
                signals.append({'date': data.index[i], 'action': 'sell', 'price': data['Close'].iloc[i]})

        return signals

    def strategy_trix(self, data):
        """TRIX 전략"""
        ema1 = data['Close'].ewm(span=14).mean()
        ema2 = ema1.ewm(span=14).mean()
        ema3 = ema2.ewm(span=14).mean()
        trix = ema3.pct_change() * 10000
        trix_signal = trix.rolling(window=9).mean()
        signals = []

        for i in range(1, len(data)):
            if trix.iloc[i] > trix_signal.iloc[i] and trix.iloc[i-1] <= trix_signal.iloc[i-1]:
                signals.append({'date': data.index[i], 'action': 'buy', 'price': data['Close'].iloc[i]})
            elif trix.iloc[i] < trix_signal.iloc[i] and trix.iloc[i-1] >= trix_signal.iloc[i-1]:
                signals.append({'date': data.index[i], 'action': 'sell', 'price': data['Close'].iloc[i]})

        return signals

    def strategy_aroon(self, data):
        """Aroon 전략"""
        period = 25
        aroon_up = []
        aroon_down = []

        for i in range(period, len(data)):
            high_period = data['High'].iloc[i-period+1:i+1]
            low_period = data['Low'].iloc[i-period+1:i+1]

            high_idx = high_period.argmax()
            low_idx = low_period.argmin()

            aroon_up.append(((period - 1 - high_idx) / period) * 100)
            aroon_down.append(((period - 1 - low_idx) / period) * 100)

        signals = []
        for i in range(1, len(aroon_up)):
            if aroon_up[i] > 70 and aroon_down[i] < 30:
                signals.append({'date': data.index[period + i], 'action': 'buy', 'price': data['Close'].iloc[period + i]})
            elif aroon_down[i] > 70 and aroon_up[i] < 30:
                signals.append({'date': data.index[period + i], 'action': 'sell', 'price': data['Close'].iloc[period + i]})

        return signals

    def strategy_ultimate_oscillator(self, data):
        """Ultimate Oscillator 전략"""
        bp = data['Close'] - np.minimum(data['Low'], data['Close'].shift())
        tr = np.maximum(data['High'], data['Close'].shift()) - np.minimum(data['Low'], data['Close'].shift())

        avg7 = bp.rolling(window=7).sum() / tr.rolling(window=7).sum()
        avg14 = bp.rolling(window=14).sum() / tr.rolling(window=14).sum()
        avg28 = bp.rolling(window=28).sum() / tr.rolling(window=28).sum()

        uo = 100 * (4 * avg7 + 2 * avg14 + avg28) / 7
        signals = []

        for i in range(1, len(data)):
            if uo.iloc[i] < 30 and uo.iloc[i-1] >= 30:
                signals.append({'date': data.index[i], 'action': 'buy', 'price': data['Close'].iloc[i]})
            elif uo.iloc[i] > 70 and uo.iloc[i-1] <= 70:
                signals.append({'date': data.index[i], 'action': 'sell', 'price': data['Close'].iloc[i]})

        return signals

    def strategy_parabolic_sar(self, data):
        """Parabolic SAR 전략"""
        high = data['High'].values
        low = data['Low'].values
        close = data['Close'].values

        af = 0.02
        af_step = 0.02
        af_max = 0.2

        sar = np.zeros(len(data))
        trend = np.zeros(len(data))
        ep = np.zeros(len(data))
        af_current = np.zeros(len(data))

        sar[0] = low[0]
        trend[0] = 1
        ep[0] = high[0]
        af_current[0] = af

        for i in range(1, len(data)):
            if trend[i-1] == 1:
                sar[i] = sar[i-1] + af_current[i-1] * (ep[i-1] - sar[i-1])

                if low[i] <= sar[i]:
                    trend[i] = -1
                    sar[i] = ep[i-1]
                    ep[i] = low[i]
                    af_current[i] = af
                else:
                    trend[i] = 1
                    if high[i] > ep[i-1]:
                        ep[i] = high[i]
                        af_current[i] = min(af_current[i-1] + af_step, af_max)
                    else:
                        ep[i] = ep[i-1]
                        af_current[i] = af_current[i-1]
            else:
                sar[i] = sar[i-1] + af_current[i-1] * (ep[i-1] - sar[i-1])

                if high[i] >= sar[i]:
                    trend[i] = 1
                    sar[i] = ep[i-1]
                    ep[i] = high[i]
                    af_current[i] = af
                else:
                    trend[i] = -1
                    if low[i] < ep[i-1]:
                        ep[i] = low[i]
                        af_current[i] = min(af_current[i-1] + af_step, af_max)
                    else:
                        ep[i] = ep[i-1]
                        af_current[i] = af_current[i-1]

        signals = []
        for i in range(1, len(data)):
            if trend[i] == 1 and trend[i-1] == -1:
                signals.append({'date': data.index[i], 'action': 'buy', 'price': close[i]})
            elif trend[i] == -1 and trend[i-1] == 1:
                signals.append({'date': data.index[i], 'action': 'sell', 'price': close[i]})

        return signals

    def strategy_ichimoku(self, data):
        """일목균형표 전략"""
        high9 = data['High'].rolling(window=9).max()
        low9 = data['Low'].rolling(window=9).min()
        tenkan_sen = (high9 + low9) / 2

        high26 = data['High'].rolling(window=26).max()
        low26 = data['Low'].rolling(window=26).min()
        kijun_sen = (high26 + low26) / 2

        senkou_span_a = ((tenkan_sen + kijun_sen) / 2).shift(26)
        high52 = data['High'].rolling(window=52).max()
        low52 = data['Low'].rolling(window=52).min()
        senkou_span_b = ((high52 + low52) / 2).shift(26)

        signals = []
        for i in range(26, len(data)):
            if (tenkan_sen.iloc[i] > kijun_sen.iloc[i] and
                data['Close'].iloc[i] > senkou_span_a.iloc[i] and
                data['Close'].iloc[i] > senkou_span_b.iloc[i]):
                signals.append({'date': data.index[i], 'action': 'buy', 'price': data['Close'].iloc[i]})
            elif (tenkan_sen.iloc[i] < kijun_sen.iloc[i] and
                  data['Close'].iloc[i] < senkou_span_a.iloc[i] and
                  data['Close'].iloc[i] < senkou_span_b.iloc[i]):
                signals.append({'date': data.index[i], 'action': 'sell', 'price': data['Close'].iloc[i]})

        return signals

    def initialize_strategies(self):
        """전략 초기화"""
        self.strategies = {
            'RSI_30_70': self.strategy_rsi_oversold,
            'Golden_Cross': self.strategy_golden_cross,
            'Bollinger_Breakout': self.strategy_bollinger_breakout,
            'MACD_Signal': self.strategy_macd_signal,
            'Volume_Spike': self.strategy_volume_spike,
            'Momentum_Reversal': self.strategy_momentum_reversal,
            'Mean_Reversion': self.strategy_mean_reversion,
            'Stochastic': self.strategy_stochastic_oscillator,
            'Williams_R': self.strategy_williams_r,
            'CCI': self.strategy_cci,
            'ATR_Breakout': self.strategy_atr_breakout,
            'Donchian_Channel': self.strategy_donchian_channel,
            'Price_Channel': self.strategy_price_channel,
            'Elder_Ray': self.strategy_elder_ray,
            'TRIX': self.strategy_trix,
            'Aroon': self.strategy_aroon,
            'Ultimate_Oscillator': self.strategy_ultimate_oscillator,
            'Parabolic_SAR': self.strategy_parabolic_sar,
            'Ichimoku': self.strategy_ichimoku
        }

    def calculate_strategy_performance(self, signals):
        """전략 성과 계산"""
        if len(signals) < 2:
            return 0, 0, 0

        trades = []
        buy_price = None

        for signal in signals:
            if signal['action'] == 'buy' and buy_price is None:
                buy_price = signal['price']
            elif signal['action'] == 'sell' and buy_price is not None:
                profit = (signal['price'] - buy_price) / buy_price
                trades.append(profit)
                buy_price = None

        if len(trades) == 0:
            return 0, 0, 0

        wins = sum(1 for trade in trades if trade > 0)
        win_rate = wins / len(trades)
        avg_profit = np.mean(trades)

        return win_rate, avg_profit, len(trades)

    def test_strategy_on_stock(self, strategy_name, strategy_func, symbol):
        """개별 주식에서 전략 테스트"""
        data = self.fetch_stock_data(symbol)
        if data is None or len(data) < 100:
            return None

        try:
            signals = strategy_func(data)
            win_rate, avg_profit, total_trades = self.calculate_strategy_performance(signals)

            if total_trades > 0 and win_rate >= self.min_win_rate:
                return {
                    'symbol': symbol,
                    'win_rate': win_rate,
                    'avg_profit': avg_profit,
                    'total_trades': total_trades,
                    'profitable_signals': int(win_rate * total_trades)
                }
        except:
            pass

        return None

    def get_stock_symbols(self):
        """한국 + 미국 주식 심볼 가져오기"""
        korean_stocks = [
            '005930.KS', '000660.KS', '035420.KS', '005490.KS', '051910.KS',
            '068270.KS', '035720.KS', '028260.KS', '207940.KS', '006400.KS',
            '003670.KS', '066570.KS', '323410.KS', '000270.KS', '096770.KS',
            '017670.KS', '018260.KS', '003550.KS', '033780.KS', '009150.KS',
            '316140.KS', '051900.KS', '012330.KS', '086790.KS', '030200.KS',
            '003490.KS', '090430.KS', '034730.KS', '024110.KS', '009540.KS',
            '011070.KS', '010130.KS', '009830.KS', '036570.KS', '000720.KS',
            '021240.KS', '047050.KS', '105560.KS', '004020.KS', '139480.KS',
            '001570.KS', '011790.KS', '006800.KS', '267250.KS', '032640.KS',
            '078930.KS', '088350.KS', '010950.KS', '161390.KS', '015760.KS'
        ]

        us_stocks = [
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'BRK-B',
            'JNJ', 'V', 'PG', 'JPM', 'UNH', 'MA', 'HD', 'DIS', 'BAC', 'ADBE',
            'CRM', 'NFLX', 'PYPL', 'INTC', 'CMCSA', 'PEP', 'T', 'ABT', 'TMO',
            'COST', 'AVGO', 'ACN', 'ABBV', 'MRK', 'TXN', 'HON', 'LIN', 'NKE',
            'MDT', 'DHR', 'WMT', 'KO', 'ORCL', 'CVX', 'VZ', 'NEE', 'PM', 'IBM',
            'QCOM', 'LOW', 'BMY', 'UNP'
        ]

        return korean_stocks + us_stocks

    def test_all_strategies(self):
        """모든 전략을 모든 주식에서 테스트"""
        self.initialize_strategies()
        symbols = self.get_stock_symbols()

        best_strategies = {}

        for strategy_name, strategy_func in self.strategies.items():
            print(f"Testing {strategy_name}...")

            strategy_results = []

            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                futures = {executor.submit(self.test_strategy_on_stock, strategy_name, strategy_func, symbol): symbol
                          for symbol in symbols}

                for future in concurrent.futures.as_completed(futures):
                    result = future.result()
                    if result:
                        strategy_results.append(result)

            if strategy_results:
                total_trades = sum(r['total_trades'] for r in strategy_results)
                total_profitable = sum(r['profitable_signals'] for r in strategy_results)
                overall_win_rate = total_profitable / total_trades if total_trades > 0 else 0
                avg_profit = np.mean([r['avg_profit'] for r in strategy_results])

                if overall_win_rate >= self.min_win_rate and total_trades >= 10:
                    best_strategies[strategy_name] = {
                        'win_rate': round(overall_win_rate, 3),
                        'avg_profit': round(avg_profit, 4),
                        'tested_stocks': len(strategy_results),
                        'profitable_signals': total_profitable,
                        'total_trades': total_trades
                    }

        if best_strategies:
            best_strategy = max(best_strategies.items(),
                              key=lambda x: x[1]['win_rate'] * x[1]['avg_profit'])

            result = {
                'best_strategy': best_strategy[0],
                'win_rate': best_strategy[1]['win_rate'],
                'avg_profit': best_strategy[1]['avg_profit'],
                'tested_stocks': best_strategy[1]['tested_stocks'],
                'profitable_signals': best_strategy[1]['profitable_signals'],
                'all_profitable_strategies': best_strategies,
                'test_date': datetime.now().isoformat(),
                'total_symbols_tested': len(symbols)
            }
        else:
            result = {
                'best_strategy': None,
                'win_rate': 0,
                'avg_profit': 0,
                'tested_stocks': 0,
                'profitable_signals': 0,
                'message': 'No strategies met the 70% win rate threshold',
                'test_date': datetime.now().isoformat(),
                'total_symbols_tested': len(symbols)
            }

        return result

    def save_results(self, results, filename='profitable_strategies.json'):
        """결과를 JSON 파일로 저장"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

    def run_daily_update(self):
        """일일 업데이트 실행"""
        print("Starting daily strategy analysis...")
        results = self.test_all_strategies()
        self.save_results(results)

        return json.dumps(results, indent=2, ensure_ascii=False)

def main():
    finder = ProfitStrategyFinder()

    print("=" * 60)
    print("PROFIT STRATEGY FINDER - REAL MONEY MAKER")
    print("=" * 60)
    print("Testing 19 strategies on 100 stocks (Korean + US)")
    print("Minimum win rate: 70%")
    print("=" * 60)

    result_json = finder.run_daily_update()
    print(result_json)

    return result_json

if __name__ == "__main__":
    main()