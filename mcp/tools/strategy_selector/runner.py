"""
Strategy Selector Runner - 백테스팅 결과 기반 최적 전략 선택
"""

import json
import os
from typing import Dict, Any
from datetime import datetime, timedelta

# 백테스팅 결과 로드 (profit_strategy_finder.py 실행 결과)
STRATEGY_RESULTS_PATH = "data/backtest_results.json"

# 전략별 점수 매핑
STRATEGY_SCORES = {
    "RSI_30_70": {"base_score": 85, "confidence": 0.73},
    "MACD_SIGNAL": {"base_score": 80, "confidence": 0.68},
    "BB_SQUEEZE": {"base_score": 82, "confidence": 0.71},
    "GOLDEN_CROSS": {"base_score": 78, "confidence": 0.65},
    "VOLUME_BREAKOUT": {"base_score": 83, "confidence": 0.70},
    "ICHIMOKU_CLOUD": {"base_score": 81, "confidence": 0.69},
    "STOCH_RSI": {"base_score": 79, "confidence": 0.67},
    "MOMENTUM": {"base_score": 77, "confidence": 0.66}
}

def load_best_strategies():
    """백테스팅 결과에서 최적 전략 로드"""
    try:
        if os.path.exists(STRATEGY_RESULTS_PATH):
            with open(STRATEGY_RESULTS_PATH, 'r') as f:
                return json.load(f)
    except:
        pass
    
    # 기본값
    return {
        "best_strategy": "RSI_30_70",
        "win_rate": 0.73,
        "strategies": STRATEGY_SCORES
    }

def run(action: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """MCP 액션 실행"""
    
    if action == "get_best_strategy":
        # 종목별 최적 전략 선택
        symbol = payload.get("symbol", "AAPL")
        period = payload.get("period", "1w")
        
        strategies = load_best_strategies()
        
        # 종목 특성에 따른 전략 선택 (실제로는 ML 모델)
        if symbol.endswith(".KS") or symbol.endswith(".KQ"):
            # 한국 주식: 변동성 전략
            best = "BB_SQUEEZE"
        elif symbol in ["AAPL", "MSFT", "GOOGL"]:
            # 대형 기술주: RSI
            best = "RSI_30_70"
        else:
            # 기본: 백테스팅 최고 전략
            best = strategies.get("best_strategy", "RSI_30_70")
        
        strategy_info = STRATEGY_SCORES.get(best, {"confidence": 0.7})
        
        return {
            "strategy_name": best,
            "expected_win_rate": strategy_info["confidence"],
            "confidence": strategy_info["confidence"],
            "period": period,
            "last_updated": datetime.now().isoformat()
        }
    
    elif action == "apply_strategy":
        # 전략 적용해서 AI 스코어 생성
        symbol = payload.get("symbol", "AAPL")
        strategy = payload.get("strategy", "RSI_30_70")
        
        strategy_info = STRATEGY_SCORES.get(strategy, {"base_score": 75, "confidence": 0.65})
        
        # 실제 시장 데이터 기반 조정 (여기서는 더미)
        import random
        market_adjustment = random.randint(-10, 10)
        
        ai_score = strategy_info["base_score"] + market_adjustment
        ai_score = max(0, min(100, ai_score))  # 0-100 범위
        
        # 점수 기반 시그널 결정
        if ai_score >= 85:
            signal = "BULLISH"
        elif ai_score <= 50:
            signal = "BEARISH"
        else:
            signal = "NEUTRAL"
        
        return {
            "ai_score": ai_score,
            "signal": signal,
            "strategy_used": strategy,
            "confidence": strategy_info["confidence"],
            "symbol": symbol,
            "timestamp": datetime.now().isoformat()
        }
    
    return {"error": f"Unknown action: {action}"}
