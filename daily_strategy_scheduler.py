#!/usr/bin/env python3
import schedule
import time
import subprocess
import json
from datetime import datetime
import os

def run_strategy_finder():
    """매일 전략 파인더 실행"""
    try:
        print(f"\n{datetime.now()} - Starting daily strategy analysis...")

        result = subprocess.run(['python', 'profit_strategy_finder.py'],
                              capture_output=True, text=True, cwd=os.path.dirname(os.path.abspath(__file__)))

        if result.returncode == 0:
            print("✅ Strategy analysis completed successfully")

            output_data = json.loads(result.stdout.split('\n')[-2])

            print(f"📊 Results:")
            print(f"   Best Strategy: {output_data.get('best_strategy', 'None')}")
            print(f"   Win Rate: {output_data.get('win_rate', 0):.1%}")
            print(f"   Avg Profit: {output_data.get('avg_profit', 0):.2%}")
            print(f"   Tested Stocks: {output_data.get('tested_stocks', 0)}")

            with open('daily_strategy_log.txt', 'a') as f:
                f.write(f"{datetime.now()}: {output_data.get('best_strategy', 'None')} - "
                       f"Win Rate: {output_data.get('win_rate', 0):.3f}, "
                       f"Profit: {output_data.get('avg_profit', 0):.4f}\n")

        else:
            print("❌ Strategy analysis failed")
            print(f"Error: {result.stderr}")

    except Exception as e:
        print(f"❌ Error running strategy finder: {e}")

def main():
    print("🚀 Daily Strategy Scheduler Started")
    print("⏰ Scheduled to run every day at 09:00")

    schedule.every().day.at("09:00").do(run_strategy_finder)

    schedule.every().monday.at("18:00").do(run_strategy_finder)

    print("📅 Next run:", schedule.next_run())

    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    main()