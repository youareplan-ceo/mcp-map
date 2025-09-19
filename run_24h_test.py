#!/usr/bin/env python3
import subprocess
import psutil
import time
import json
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
from pathlib import Path
import threading
import logging
import os
import signal
import sys
from flask import Flask, render_template, jsonify
import warnings
warnings.filterwarnings('ignore')

class System24HMonitor:
    def __init__(self):
        self.start_time = datetime.now()
        self.processes = {}
        self.checkpoints = []
        self.running = False

        self.setup_directories()
        self.setup_logging()

        # 성과 추적
        self.initial_value = None
        self.peak_value = None
        self.lowest_value = None
        self.peak_time = None
        self.lowest_time = None

        # 알림 임계값
        self.profit_alert_threshold = 0.05  # +5%
        self.loss_alert_threshold = -0.03   # -3%
        self.last_alert_time = {}

        # Flask 앱 설정
        self.app = Flask(__name__)
        self.setup_flask_routes()

    def setup_directories(self):
        """필요한 디렉토리 생성"""
        directories = [
            'reports',
            'logs',
            'data/realtime',
            'portfolio',
            'checkpoints'
        ]

        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)

    def setup_logging(self):
        """로깅 설정"""
        today = datetime.now().strftime('%Y-%m-%d')
        log_file = f'logs/24h_monitor_{today}.log'

        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )

        self.logger = logging.getLogger(__name__)

    def setup_flask_routes(self):
        """Flask 웹 대시보드 라우트 설정"""
        @self.app.route('/')
        def dashboard():
            return render_template('dashboard.html')

        @self.app.route('/api/status')
        def api_status():
            return jsonify(self.get_current_status())

        @self.app.route('/api/performance')
        def api_performance():
            return jsonify(self.get_performance_data())

    def check_required_files(self):
        """필요한 파일들 확인 및 생성"""
        required_files = {
            'realtime_data_collector.py': True,
            'auto_paper_trader.py': True,
            'watchlist.txt': False,
            'requirements.txt': False
        }

        missing_files = []

        for filename, required in required_files.items():
            if not Path(filename).exists():
                if required:
                    missing_files.append(filename)
                else:
                    self.create_missing_file(filename)

        if missing_files:
            self.logger.error(f"Required files missing: {missing_files}")
            return False

        return True

    def create_missing_file(self, filename):
        """누락된 파일 생성"""
        if filename == 'watchlist.txt':
            with open(filename, 'w') as f:
                f.write("AAPL\nMSFT\nGOOGL\nTSLA\n005930.KS\n000660.KS\n")
            self.logger.info(f"Created default {filename}")

        elif filename == 'requirements.txt':
            with open(filename, 'w') as f:
                f.write("pandas\nnumpy\nyfinance\nflask\nmatplotlib\npsutil\n")
            self.logger.info(f"Created default {filename}")

    def start_process(self, script_name, process_name):
        """프로세스 시작"""
        try:
            cmd = [sys.executable, script_name]
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            self.processes[process_name] = {
                'process': process,
                'script': script_name,
                'start_time': datetime.now(),
                'restart_count': 0
            }

            self.logger.info(f"✅ Started {process_name} (PID: {process.pid})")
            return True

        except Exception as e:
            self.logger.error(f"❌ Failed to start {process_name}: {e}")
            return False

    def check_process_health(self, process_name):
        """프로세스 상태 확인"""
        if process_name not in self.processes:
            return False

        process_info = self.processes[process_name]
        process = process_info['process']

        # 프로세스가 종료되었는지 확인
        if process.poll() is not None:
            return False

        # CPU/메모리 사용량 확인
        try:
            p = psutil.Process(process.pid)
            cpu_percent = p.cpu_percent()
            memory_percent = p.memory_percent()

            # 비정상적인 리소스 사용량 확인
            if cpu_percent > 90 or memory_percent > 80:
                self.logger.warning(f"⚠️ {process_name} high resource usage: CPU {cpu_percent}%, Memory {memory_percent}%")

            return True

        except psutil.NoSuchProcess:
            return False

    def restart_process(self, process_name):
        """프로세스 재시작"""
        if process_name in self.processes:
            process_info = self.processes[process_name]

            # 기존 프로세스 종료
            try:
                process_info['process'].terminate()
                process_info['process'].wait(timeout=10)
            except:
                try:
                    process_info['process'].kill()
                except:
                    pass

            # 재시작 카운트 증가
            process_info['restart_count'] += 1

            self.logger.warning(f"🔄 Restarting {process_name} (restart #{process_info['restart_count']})")

            # 잠시 대기 후 재시작
            time.sleep(5)
            return self.start_process(process_info['script'], process_name)

        return False

    def get_portfolio_data(self):
        """포트폴리오 데이터 조회"""
        try:
            if not Path('trades.db').exists():
                return None

            conn = sqlite3.connect('trades.db')

            # 최신 포트폴리오 스냅샷
            cursor = conn.execute('''
                SELECT total_value, cash_krw, cash_usd, holdings, total_return
                FROM portfolio_snapshots
                ORDER BY timestamp DESC
                LIMIT 1
            ''')

            latest = cursor.fetchone()

            if latest:
                total_value, cash_krw, cash_usd, holdings_json, total_return = latest
                holdings = json.loads(holdings_json) if holdings_json else {}

                return {
                    'total_value': total_value,
                    'cash_krw': cash_krw,
                    'cash_usd': cash_usd,
                    'holdings': holdings,
                    'total_return': total_return
                }

            conn.close()
            return None

        except Exception as e:
            self.logger.error(f"Error getting portfolio data: {e}")
            return None

    def get_trade_statistics(self):
        """거래 통계 조회"""
        try:
            if not Path('trades.db').exists():
                return {}

            conn = sqlite3.connect('trades.db')

            # 총 거래 수
            cursor = conn.execute('SELECT COUNT(*) FROM trades')
            total_trades = cursor.fetchone()[0]

            # 매수/매도 분리
            cursor = conn.execute('SELECT action, COUNT(*) FROM trades GROUP BY action')
            action_counts = dict(cursor.fetchall())

            # 수익 거래 수
            cursor = conn.execute('SELECT COUNT(*) FROM trades WHERE profit_loss > 0')
            profitable_trades = cursor.fetchone()[0]

            # 시간별 거래 분포
            cursor = conn.execute('''
                SELECT strftime('%H', timestamp) as hour, COUNT(*) as count
                FROM trades
                GROUP BY hour
                ORDER BY hour
            ''')
            hourly_trades = dict(cursor.fetchall())

            conn.close()

            win_rate = (profitable_trades / total_trades * 100) if total_trades > 0 else 0

            return {
                'total_trades': total_trades,
                'buy_trades': action_counts.get('BUY', 0),
                'sell_trades': action_counts.get('SELL', 0),
                'win_rate': win_rate,
                'hourly_distribution': hourly_trades
            }

        except Exception as e:
            self.logger.error(f"Error getting trade statistics: {e}")
            return {}

    def create_hourly_checkpoint(self):
        """시간별 체크포인트 생성"""
        try:
            now = datetime.now()
            portfolio_data = self.get_portfolio_data()
            trade_stats = self.get_trade_statistics()

            if not portfolio_data:
                return

            # 초기값 설정
            if self.initial_value is None:
                self.initial_value = portfolio_data['total_value']
                self.peak_value = portfolio_data['total_value']
                self.lowest_value = portfolio_data['total_value']
                self.peak_time = now
                self.lowest_time = now

            current_value = portfolio_data['total_value']
            current_return = ((current_value - self.initial_value) / self.initial_value) * 100

            # 최고/최저 기록 업데이트
            if current_value > self.peak_value:
                self.peak_value = current_value
                self.peak_time = now

            if current_value < self.lowest_value:
                self.lowest_value = current_value
                self.lowest_time = now

            # 체크포인트 데이터
            checkpoint = {
                'timestamp': now.isoformat(),
                'runtime_hours': (now - self.start_time).total_seconds() / 3600,
                'total_value': current_value,
                'current_return': current_return,
                'peak_value': self.peak_value,
                'peak_time': self.peak_time.isoformat(),
                'lowest_value': self.lowest_value,
                'lowest_time': self.lowest_time.isoformat(),
                'trade_stats': trade_stats,
                'portfolio_data': portfolio_data
            }

            # 체크포인트 저장
            self.checkpoints.append(checkpoint)

            checkpoint_file = f"checkpoints/checkpoint_{now.strftime('%Y%m%d_%H%M')}.json"
            with open(checkpoint_file, 'w') as f:
                json.dump(checkpoint, f, indent=2)

            # 콘솔 출력
            self.display_checkpoint(checkpoint)

            # 알림 확인
            self.check_alerts(current_return)

            # 성과 그래프 업데이트
            self.update_performance_chart()

        except Exception as e:
            self.logger.error(f"Error creating checkpoint: {e}")

    def display_checkpoint(self, checkpoint):
        """체크포인트 콘솔 출력"""
        os.system('clear' if os.name == 'posix' else 'cls')

        now = datetime.fromisoformat(checkpoint['timestamp'])
        runtime = checkpoint['runtime_hours']

        print("=" * 50)
        print(f"⏰ {now.strftime('%Y-%m-%d %H:%M')} 체크포인트")
        print("=" * 50)
        print(f"운영 시간: {int(runtime)}시간 {int((runtime % 1) * 60)}분")

        stats = checkpoint['trade_stats']
        if stats:
            print(f"총 거래: {stats['total_trades']}건 (매수 {stats['buy_trades']}, 매도 {stats['sell_trades']})")

        print(f"현재 수익률: {checkpoint['current_return']:+.2f}%")

        peak_time = datetime.fromisoformat(checkpoint['peak_time'])
        lowest_time = datetime.fromisoformat(checkpoint['lowest_time'])

        peak_return = ((checkpoint['peak_value'] - checkpoint['total_value']) / checkpoint['total_value']) * 100
        lowest_return = ((checkpoint['lowest_value'] - checkpoint['total_value']) / checkpoint['total_value']) * 100

        print(f"최고 수익률: {peak_return:+.2f}% ({peak_time.strftime('%H:%M')})")
        print(f"최저 수익률: {lowest_return:+.2f}% ({lowest_time.strftime('%H:%M')})")

        # 상위 종목 표시
        holdings = checkpoint['portfolio_data']['holdings']
        if holdings:
            print("-" * 50)
            print("보유 종목:")
            sorted_holdings = sorted(holdings.items(), key=lambda x: x[1]['quantity'] * x[1]['avg_price'], reverse=True)

            for i, (symbol, holding) in enumerate(sorted_holdings[:5], 1):
                quantity = holding['quantity']
                avg_price = holding['avg_price']
                currency = '₩' if holding['currency'] == 'KRW' else '$'
                print(f"  {i}. {symbol}: {quantity}주 @ {currency}{avg_price:.2f}")

        print("=" * 50)

    def check_alerts(self, current_return):
        """알림 확인"""
        now = datetime.now()

        # 수익 알림
        if current_return >= self.profit_alert_threshold * 100:
            if 'profit' not in self.last_alert_time or (now - self.last_alert_time['profit']).seconds > 3600:
                self.send_alert(f"🎉 수익률 {current_return:.2f}% 달성!", "PROFIT")
                self.last_alert_time['profit'] = now

        # 손실 알림
        elif current_return <= self.loss_alert_threshold * 100:
            if 'loss' not in self.last_alert_time or (now - self.last_alert_time['loss']).seconds > 3600:
                self.send_alert(f"⚠️ 손실 {current_return:.2f}% 발생", "LOSS")
                self.last_alert_time['loss'] = now

    def send_alert(self, message, alert_type):
        """알림 전송"""
        self.logger.warning(f"🚨 ALERT [{alert_type}]: {message}")

        # 알림 파일 저장
        alert_data = {
            'timestamp': datetime.now().isoformat(),
            'type': alert_type,
            'message': message
        }

        alerts_file = 'reports/alerts.json'

        alerts = []
        if Path(alerts_file).exists():
            try:
                with open(alerts_file, 'r') as f:
                    alerts = json.load(f)
            except:
                alerts = []

        alerts.append(alert_data)

        with open(alerts_file, 'w') as f:
            json.dump(alerts, f, indent=2)

    def update_performance_chart(self):
        """성과 차트 업데이트"""
        try:
            if len(self.checkpoints) < 2:
                return

            # 데이터 준비
            timestamps = [datetime.fromisoformat(cp['timestamp']) for cp in self.checkpoints]
            returns = [cp['current_return'] for cp in self.checkpoints]
            values = [cp['total_value'] for cp in self.checkpoints]

            # 차트 생성
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))

            # 수익률 차트
            ax1.plot(timestamps, returns, 'b-', linewidth=2, label='수익률')
            ax1.axhline(y=0, color='gray', linestyle='--', alpha=0.5)
            ax1.axhline(y=5, color='green', linestyle='--', alpha=0.5, label='목표 +5%')
            ax1.axhline(y=-3, color='red', linestyle='--', alpha=0.5, label='경고 -3%')
            ax1.set_ylabel('수익률 (%)')
            ax1.set_title('24시간 실시간 수익률 추이')
            ax1.legend()
            ax1.grid(True, alpha=0.3)

            # 포트폴리오 가치 차트
            ax2.plot(timestamps, values, 'g-', linewidth=2, label='포트폴리오 가치')
            ax2.axhline(y=self.initial_value, color='gray', linestyle='--', alpha=0.5, label='초기 자금')
            ax2.set_ylabel('포트폴리오 가치 (원)')
            ax2.set_xlabel('시간')
            ax2.legend()
            ax2.grid(True, alpha=0.3)

            # 시간 축 포맷
            for ax in [ax1, ax2]:
                ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
                ax.xaxis.set_major_locator(mdates.HourLocator(interval=2))
                plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)

            plt.tight_layout()
            plt.savefig('reports/hourly_performance.png', dpi=300, bbox_inches='tight')
            plt.close()

        except Exception as e:
            self.logger.error(f"Error updating performance chart: {e}")

    def create_symbol_performance_report(self):
        """종목별 성과 리포트 생성"""
        try:
            if not Path('trades.db').exists():
                return

            conn = sqlite3.connect('trades.db')

            # 종목별 거래 통계
            query = '''
                SELECT
                    symbol,
                    COUNT(*) as total_trades,
                    SUM(CASE WHEN action = 'BUY' THEN 1 ELSE 0 END) as buy_count,
                    SUM(CASE WHEN action = 'SELL' THEN 1 ELSE 0 END) as sell_count,
                    SUM(CASE WHEN profit_loss > 0 THEN 1 ELSE 0 END) as profitable_trades,
                    ROUND(AVG(CASE WHEN profit_loss > 0 THEN profit_loss ELSE NULL END), 4) as avg_profit,
                    ROUND(AVG(CASE WHEN profit_loss < 0 THEN profit_loss ELSE NULL END), 4) as avg_loss,
                    ROUND(SUM(profit_loss), 4) as total_profit_loss
                FROM trades
                WHERE symbol != ''
                GROUP BY symbol
                ORDER BY total_profit_loss DESC
            '''

            df = pd.read_sql_query(query, conn)

            if not df.empty:
                # 승률 계산
                df['win_rate'] = (df['profitable_trades'] / df['total_trades'] * 100).round(2)

                # CSV 저장
                df.to_csv('reports/symbol_performance.csv', index=False, encoding='utf-8-sig')

                self.logger.info("✅ Symbol performance report created")

            conn.close()

        except Exception as e:
            self.logger.error(f"Error creating symbol performance report: {e}")

    def get_current_status(self):
        """현재 상태 조회 (API용)"""
        portfolio_data = self.get_portfolio_data()
        trade_stats = self.get_trade_statistics()

        runtime = (datetime.now() - self.start_time).total_seconds() / 3600

        process_status = {}
        for name, info in self.processes.items():
            process_status[name] = {
                'running': self.check_process_health(name),
                'start_time': info['start_time'].isoformat(),
                'restart_count': info['restart_count']
            }

        return {
            'runtime_hours': runtime,
            'process_status': process_status,
            'portfolio_data': portfolio_data,
            'trade_stats': trade_stats,
            'checkpoints_count': len(self.checkpoints)
        }

    def get_performance_data(self):
        """성과 데이터 조회 (API용)"""
        if not self.checkpoints:
            return {'timestamps': [], 'returns': [], 'values': []}

        timestamps = [cp['timestamp'] for cp in self.checkpoints]
        returns = [cp['current_return'] for cp in self.checkpoints]
        values = [cp['total_value'] for cp in self.checkpoints]

        return {
            'timestamps': timestamps,
            'returns': returns,
            'values': values
        }

    def start_web_dashboard(self):
        """웹 대시보드 시작"""
        def run_flask():
            self.app.run(host='0.0.0.0', port=9999, debug=False, use_reloader=False)

        flask_thread = threading.Thread(target=run_flask, daemon=True)
        flask_thread.start()

        self.logger.info("🌐 Web dashboard started at http://localhost:9999")

    def create_dashboard_template(self):
        """대시보드 HTML 템플릿 생성"""
        templates_dir = Path('templates')
        templates_dir.mkdir(exist_ok=True)

        dashboard_html = '''
<!DOCTYPE html>
<html>
<head>
    <title>24시간 거래 모니터링</title>
    <meta charset="utf-8">
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .container { max-width: 1200px; margin: 0 auto; }
        .status-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 20px; }
        .status-card { border: 1px solid #ddd; border-radius: 8px; padding: 15px; background: #f9f9f9; }
        .status-card h3 { margin-top: 0; color: #333; }
        .chart-container { border: 1px solid #ddd; border-radius: 8px; padding: 15px; margin-bottom: 20px; }
        .green { color: #28a745; }
        .red { color: #dc3545; }
        .blue { color: #007bff; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 24시간 자동 거래 모니터링</h1>

        <div class="status-grid">
            <div class="status-card">
                <h3>운영 상태</h3>
                <div id="runtime">운영 시간: --</div>
                <div id="processes">프로세스: --</div>
            </div>

            <div class="status-card">
                <h3>포트폴리오</h3>
                <div id="total-value">총 자산: --</div>
                <div id="total-return">수익률: --</div>
            </div>

            <div class="status-card">
                <h3>거래 통계</h3>
                <div id="total-trades">총 거래: --</div>
                <div id="win-rate">승률: --</div>
            </div>
        </div>

        <div class="chart-container">
            <h3>실시간 수익률</h3>
            <div id="performance-chart"></div>
        </div>
    </div>

    <script>
        function updateDashboard() {
            fetch('/api/status')
                .then(response => response.json())
                .then(data => {
                    document.getElementById('runtime').innerHTML =
                        `운영 시간: ${Math.floor(data.runtime_hours)}시간 ${Math.floor((data.runtime_hours % 1) * 60)}분`;

                    let processCount = Object.keys(data.process_status).length;
                    let runningCount = Object.values(data.process_status).filter(p => p.running).length;
                    document.getElementById('processes').innerHTML =
                        `프로세스: ${runningCount}/${processCount} 실행중`;

                    if (data.portfolio_data) {
                        document.getElementById('total-value').innerHTML =
                            `총 자산: ₩${data.portfolio_data.total_value.toLocaleString()}`;
                        document.getElementById('total-return').innerHTML =
                            `수익률: ${data.portfolio_data.total_return > 0 ? '+' : ''}${data.portfolio_data.total_return.toFixed(2)}%`;
                    }

                    if (data.trade_stats) {
                        document.getElementById('total-trades').innerHTML =
                            `총 거래: ${data.trade_stats.total_trades}건`;
                        document.getElementById('win-rate').innerHTML =
                            `승률: ${data.trade_stats.win_rate.toFixed(1)}%`;
                    }
                });

            fetch('/api/performance')
                .then(response => response.json())
                .then(data => {
                    if (data.timestamps.length > 0) {
                        let trace = {
                            x: data.timestamps,
                            y: data.returns,
                            type: 'scatter',
                            mode: 'lines+markers',
                            name: '수익률',
                            line: {color: '#007bff', width: 2}
                        };

                        let layout = {
                            title: '',
                            xaxis: {title: '시간'},
                            yaxis: {title: '수익률 (%)'},
                            showlegend: false
                        };

                        Plotly.newPlot('performance-chart', [trace], layout);
                    }
                });
        }

        // 초기 로드 및 5초마다 업데이트
        updateDashboard();
        setInterval(updateDashboard, 5000);
    </script>
</body>
</html>
        '''

        with open(templates_dir / 'dashboard.html', 'w', encoding='utf-8') as f:
            f.write(dashboard_html)

    def generate_final_report(self):
        """24시간 최종 리포트 생성"""
        try:
            runtime = (datetime.now() - self.start_time).total_seconds() / 3600

            portfolio_data = self.get_portfolio_data()
            trade_stats = self.get_trade_statistics()

            if not portfolio_data:
                self.logger.error("No portfolio data for final report")
                return

            # 최적 거래 시간대 분석
            best_hour = None
            if trade_stats and 'hourly_distribution' in trade_stats:
                hourly_dist = trade_stats['hourly_distribution']
                if hourly_dist:
                    best_hour = max(hourly_dist, key=hourly_dist.get)

            final_report = {
                'test_period': {
                    'start_time': self.start_time.isoformat(),
                    'end_time': datetime.now().isoformat(),
                    'duration_hours': runtime
                },
                'final_performance': {
                    'initial_value': self.initial_value,
                    'final_value': portfolio_data['total_value'],
                    'total_return': portfolio_data['total_return'],
                    'peak_value': self.peak_value,
                    'lowest_value': self.lowest_value,
                    'max_drawdown': ((self.peak_value - self.lowest_value) / self.peak_value) * 100
                },
                'trading_summary': trade_stats,
                'best_trading_hour': best_hour,
                'checkpoints_created': len(self.checkpoints),
                'recommendations': self.generate_recommendations(portfolio_data, trade_stats)
            }

            # 리포트 저장
            report_file = f"reports/final_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(final_report, f, indent=2, ensure_ascii=False)

            # 콘솔 출력
            self.display_final_report(final_report)

            self.logger.info(f"✅ Final report saved to {report_file}")

        except Exception as e:
            self.logger.error(f"Error generating final report: {e}")

    def generate_recommendations(self, portfolio_data, trade_stats):
        """개선 권고사항 생성"""
        recommendations = []

        if trade_stats:
            win_rate = trade_stats.get('win_rate', 0)

            if win_rate < 60:
                recommendations.append("승률이 낮습니다. 매매 전략을 재검토하세요.")

            if trade_stats.get('total_trades', 0) < 10:
                recommendations.append("거래 빈도가 낮습니다. 신호 감도를 조정하세요.")

            if trade_stats.get('total_trades', 0) > 100:
                recommendations.append("과도한 거래가 발생했습니다. 수수료를 고려하세요.")

        if portfolio_data:
            total_return = portfolio_data.get('total_return', 0)

            if total_return < 0:
                recommendations.append("손실이 발생했습니다. 리스크 관리를 강화하세요.")
            elif total_return > 10:
                recommendations.append("좋은 성과입니다. 현재 전략을 유지하세요.")

        if not recommendations:
            recommendations.append("전반적으로 안정적인 성과를 보였습니다.")

        return recommendations

    def display_final_report(self, report):
        """최종 리포트 콘솔 출력"""
        print("\n" + "=" * 60)
        print("📊 24시간 테스트 최종 리포트")
        print("=" * 60)

        duration = report['test_period']['duration_hours']
        print(f"테스트 기간: {duration:.1f}시간")

        perf = report['final_performance']
        print(f"초기 자금: ₩{perf['initial_value']:,.0f}")
        print(f"최종 자산: ₩{perf['final_value']:,.0f}")
        print(f"총 수익률: {perf['total_return']:+.2f}%")
        print(f"최대 낙폭: {perf['max_drawdown']:-.2f}%")

        if report['trading_summary']:
            stats = report['trading_summary']
            print(f"\n거래 통계:")
            print(f"  총 거래: {stats.get('total_trades', 0)}건")
            print(f"  승률: {stats.get('win_rate', 0):.1f}%")
            print(f"  매수/매도: {stats.get('buy_trades', 0)}/{stats.get('sell_trades', 0)}")

        if report['best_trading_hour']:
            print(f"최적 거래 시간: {report['best_trading_hour']}시")

        print(f"\n개선 권고사항:")
        for rec in report['recommendations']:
            print(f"  • {rec}")

        print("=" * 60)

    def run_monitoring(self, duration_hours=24):
        """24시간 모니터링 실행"""
        self.running = True

        print("🚀 24시간 시스템 모니터링 시작")
        print("=" * 50)

        # 필수 파일 확인
        if not self.check_required_files():
            return False

        # 웹 대시보드 템플릿 생성
        self.create_dashboard_template()

        # 웹 대시보드 시작
        self.start_web_dashboard()

        # 주요 프로세스 시작
        processes_to_start = [
            ('realtime_data_collector.py', 'data_collector'),
            ('auto_paper_trader.py', 'paper_trader')
        ]

        for script, name in processes_to_start:
            if not self.start_process(script, name):
                self.logger.error(f"Failed to start {name}")
                return False

        self.logger.info("✅ All systems started successfully")
        self.logger.info("🌐 Dashboard: http://localhost:9999")

        end_time = self.start_time + timedelta(hours=duration_hours)
        next_checkpoint = self.start_time + timedelta(hours=1)

        try:
            while self.running and datetime.now() < end_time:
                current_time = datetime.now()

                # 프로세스 상태 확인
                for process_name in list(self.processes.keys()):
                    if not self.check_process_health(process_name):
                        self.logger.warning(f"⚠️ {process_name} is not healthy")
                        if not self.restart_process(process_name):
                            self.logger.error(f"❌ Failed to restart {process_name}")

                # 시간별 체크포인트
                if current_time >= next_checkpoint:
                    self.create_hourly_checkpoint()
                    self.create_symbol_performance_report()
                    next_checkpoint += timedelta(hours=1)

                # 30초마다 상태 확인
                time.sleep(30)

            # 24시간 완료 - 최종 리포트
            if not self.running:
                self.logger.info("Monitoring stopped by user")
            else:
                self.logger.info("✅ 24-hour test completed")
                self.generate_final_report()

        except KeyboardInterrupt:
            self.logger.info("Monitoring stopped by user")

        finally:
            self.cleanup()

        return True

    def cleanup(self):
        """정리 작업"""
        self.running = False

        # 모든 프로세스 종료
        for process_name, process_info in self.processes.items():
            try:
                process_info['process'].terminate()
                process_info['process'].wait(timeout=10)
                self.logger.info(f"✅ Stopped {process_name}")
            except:
                try:
                    process_info['process'].kill()
                except:
                    pass

        self.logger.info("🏁 Cleanup completed")

    def signal_handler(self, signum, frame):
        """시그널 핸들러"""
        self.logger.info(f"Received signal {signum}")
        self.running = False

def main():
    monitor = System24HMonitor()

    # 시그널 핸들러 설정
    signal.signal(signal.SIGINT, monitor.signal_handler)
    signal.signal(signal.SIGTERM, monitor.signal_handler)

    try:
        success = monitor.run_monitoring(duration_hours=24)
        if success:
            print("✅ 24시간 테스트가 성공적으로 완료되었습니다.")
        else:
            print("❌ 24시간 테스트 중 오류가 발생했습니다.")

    except Exception as e:
        print(f"❌ 치명적 오류: {e}")
        monitor.cleanup()

if __name__ == "__main__":
    main()