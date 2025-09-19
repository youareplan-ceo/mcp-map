#!/usr/bin/env python3
import yfinance as yf
import pandas as pd
import numpy as np
import json
import os
import time
import logging
from datetime import datetime, timedelta
import threading
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

class RealtimeDataCollector:
    def __init__(self, watchlist_file='watchlist.txt', collection_interval=60):
        self.watchlist_file = watchlist_file
        self.collection_interval = collection_interval
        self.symbols = []
        self.running = False

        self.setup_directories()
        self.setup_logging()
        self.load_watchlist()

    def setup_directories(self):
        """필요한 디렉토리 생성"""
        today = datetime.now().strftime('%Y-%m-%d')

        self.data_dir = Path(f'data/realtime/{today}')
        self.logs_dir = Path('logs')

        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)

    def setup_logging(self):
        """로깅 설정"""
        today = datetime.now().strftime('%Y-%m-%d')
        log_file = self.logs_dir / f'collector_{today}.log'

        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )

        self.logger = logging.getLogger(__name__)

    def load_watchlist(self):
        """감시 종목 리스트 로드"""
        try:
            if os.path.exists(self.watchlist_file):
                with open(self.watchlist_file, 'r') as f:
                    self.symbols = [line.strip() for line in f if line.strip()]
                self.logger.info(f"Loaded {len(self.symbols)} symbols from watchlist")
            else:
                self.logger.warning(f"Watchlist file {self.watchlist_file} not found. Creating default...")
                self.create_default_watchlist()

        except Exception as e:
            self.logger.error(f"Error loading watchlist: {e}")
            self.symbols = []

    def create_default_watchlist(self):
        """기본 감시 리스트 생성"""
        default_symbols = [
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA',
            '005930.KS', '000660.KS', '035420.KS', '005490.KS', '051910.KS'
        ]

        try:
            with open(self.watchlist_file, 'w') as f:
                for symbol in default_symbols:
                    f.write(f"{symbol}\n")
            self.symbols = default_symbols
            self.logger.info(f"Created default watchlist with {len(default_symbols)} symbols")
        except Exception as e:
            self.logger.error(f"Error creating default watchlist: {e}")

    def calculate_rsi(self, prices, period=14):
        """RSI 계산"""
        try:
            if len(prices) < period + 1:
                return None

            delta = prices.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))

            return rsi.iloc[-1] if not pd.isna(rsi.iloc[-1]) else None

        except Exception as e:
            self.logger.error(f"Error calculating RSI: {e}")
            return None

    def calculate_macd(self, prices, fast=12, slow=26, signal=9):
        """MACD 계산"""
        try:
            if len(prices) < slow + signal:
                return None, None, None

            exp1 = prices.ewm(span=fast).mean()
            exp2 = prices.ewm(span=slow).mean()
            macd = exp1 - exp2
            signal_line = macd.ewm(span=signal).mean()
            histogram = macd - signal_line

            return (
                macd.iloc[-1] if not pd.isna(macd.iloc[-1]) else None,
                signal_line.iloc[-1] if not pd.isna(signal_line.iloc[-1]) else None,
                histogram.iloc[-1] if not pd.isna(histogram.iloc[-1]) else None
            )

        except Exception as e:
            self.logger.error(f"Error calculating MACD: {e}")
            return None, None, None

    def get_historical_data(self, symbol, period='1mo'):
        """기술지표 계산을 위한 과거 데이터 가져오기"""
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period=period)

            if len(hist) == 0:
                return None

            return hist['Close']

        except Exception as e:
            self.logger.error(f"Error getting historical data for {symbol}: {e}")
            return None

    def collect_symbol_data(self, symbol):
        """개별 종목 데이터 수집"""
        try:
            ticker = yf.Ticker(symbol)

            # 현재 정보 가져오기
            info = ticker.info
            hist = ticker.history(period='1d', interval='1m')

            if len(hist) == 0:
                self.logger.warning(f"No recent data for {symbol}")
                return None

            # 최신 데이터
            latest = hist.iloc[-1]
            current_price = latest['Close']
            volume = latest['Volume']

            # 기술지표 계산을 위한 과거 데이터
            historical_prices = self.get_historical_data(symbol)

            # RSI 계산
            rsi = None
            if historical_prices is not None:
                # 최신 1분 데이터와 과거 데이터 결합
                combined_prices = pd.concat([historical_prices, hist['Close']])
                rsi = self.calculate_rsi(combined_prices)

            # MACD 계산
            macd, macd_signal, macd_histogram = None, None, None
            if historical_prices is not None:
                combined_prices = pd.concat([historical_prices, hist['Close']])
                macd, macd_signal, macd_histogram = self.calculate_macd(combined_prices)

            # 데이터 구성
            data = {
                'symbol': symbol,
                'timestamp': datetime.now().isoformat(),
                'current_price': float(current_price),
                'volume': int(volume),
                'change': float(latest['Close'] - latest['Open']),
                'change_percent': float((latest['Close'] - latest['Open']) / latest['Open'] * 100),
                'technical_indicators': {
                    'rsi': float(rsi) if rsi is not None else None,
                    'macd': {
                        'macd': float(macd) if macd is not None else None,
                        'signal': float(macd_signal) if macd_signal is not None else None,
                        'histogram': float(macd_histogram) if macd_histogram is not None else None
                    }
                },
                'market_data': {
                    'open': float(latest['Open']),
                    'high': float(latest['High']),
                    'low': float(latest['Low']),
                    'close': float(latest['Close'])
                }
            }

            return data

        except Exception as e:
            self.logger.error(f"Error collecting data for {symbol}: {e}")
            return None

    def save_data(self, symbol, data):
        """데이터를 JSON 파일로 저장"""
        try:
            # 심볼명에서 특수문자 제거 (파일명용)
            safe_symbol = symbol.replace('.', '_')
            filename = self.data_dir / f'{safe_symbol}.json'

            # 기존 데이터 로드
            existing_data = []
            if filename.exists():
                try:
                    with open(filename, 'r') as f:
                        existing_data = json.load(f)
                except:
                    existing_data = []

            # 새 데이터 추가
            existing_data.append(data)

            # 데이터가 너무 많으면 오래된 것 삭제 (최근 1000개만 유지)
            if len(existing_data) > 1000:
                existing_data = existing_data[-1000:]

            # 파일 저장
            with open(filename, 'w') as f:
                json.dump(existing_data, f, indent=2)

            self.logger.debug(f"Saved data for {symbol}")

        except Exception as e:
            self.logger.error(f"Error saving data for {symbol}: {e}")

    def collect_all_symbols(self):
        """모든 종목 데이터 수집"""
        successful_collections = 0

        for symbol in self.symbols:
            try:
                data = self.collect_symbol_data(symbol)
                if data:
                    self.save_data(symbol, data)
                    successful_collections += 1

                # API 제한을 위한 짧은 대기
                time.sleep(0.1)

            except Exception as e:
                self.logger.error(f"Error processing {symbol}: {e}")
                continue

        self.logger.info(f"Successfully collected data for {successful_collections}/{len(self.symbols)} symbols")

    def check_market_hours(self):
        """장 시간 확인 (단순화된 버전)"""
        now = datetime.now()
        hour = now.hour

        # 24시간 수집하도록 항상 True 반환
        # 실제로는 한국/미국 장시간을 고려해서 구현할 수 있음
        return True

    def run_collection_cycle(self):
        """수집 사이클 실행"""
        try:
            # 오늘 날짜가 바뀌었는지 확인하고 디렉토리 업데이트
            today = datetime.now().strftime('%Y-%m-%d')
            expected_dir = Path(f'data/realtime/{today}')

            if self.data_dir != expected_dir:
                self.setup_directories()
                self.logger.info(f"Directory updated for new day: {today}")

            # 감시 리스트 재로드 (파일이 업데이트되었을 수 있음)
            self.load_watchlist()

            # 데이터 수집
            if self.check_market_hours():
                self.logger.info("Starting data collection cycle...")
                self.collect_all_symbols()
            else:
                self.logger.info("Outside market hours, skipping collection")

        except Exception as e:
            self.logger.error(f"Error in collection cycle: {e}")

    def start_collection(self):
        """실시간 데이터 수집 시작"""
        self.running = True
        self.logger.info("Starting realtime data collection...")
        self.logger.info(f"Collection interval: {self.collection_interval} seconds")
        self.logger.info(f"Monitoring {len(self.symbols)} symbols")

        try:
            while self.running:
                start_time = time.time()

                self.run_collection_cycle()

                # 정확한 인터벌 유지
                elapsed = time.time() - start_time
                sleep_time = max(0, self.collection_interval - elapsed)

                if sleep_time > 0:
                    self.logger.debug(f"Sleeping for {sleep_time:.1f} seconds")
                    time.sleep(sleep_time)
                else:
                    self.logger.warning(f"Collection took {elapsed:.1f}s, longer than interval {self.collection_interval}s")

        except KeyboardInterrupt:
            self.logger.info("Collection stopped by user")
        except Exception as e:
            self.logger.error(f"Fatal error in collection loop: {e}")
        finally:
            self.running = False

    def stop_collection(self):
        """데이터 수집 중지"""
        self.running = False
        self.logger.info("Stopping data collection...")

    def get_status(self):
        """수집기 상태 반환"""
        return {
            'running': self.running,
            'symbols_count': len(self.symbols),
            'symbols': self.symbols,
            'collection_interval': self.collection_interval,
            'data_directory': str(self.data_dir),
            'last_update': datetime.now().isoformat()
        }

def main():
    """메인 실행 함수"""
    print("🚀 Realtime Stock Data Collector")
    print("=" * 50)

    try:
        # 수집기 초기화
        collector = RealtimeDataCollector()

        # 상태 출력
        status = collector.get_status()
        print(f"📊 Monitoring: {status['symbols_count']} symbols")
        print(f"⏰ Interval: {status['collection_interval']} seconds")
        print(f"💾 Data dir: {status['data_directory']}")
        print("=" * 50)

        # 수집 시작
        collector.start_collection()

    except Exception as e:
        print(f"❌ Error starting collector: {e}")

if __name__ == "__main__":
    main()