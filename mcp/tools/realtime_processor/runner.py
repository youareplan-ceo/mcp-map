"""
Realtime Data Processor - 실시간 데이터 처리 및 시그널 생성
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List

def load_realtime_data(symbol: str) -> Dict:
    """실시간 데이터 로드 (Claude Code가 수집한 데이터)"""
    today = datetime.now().strftime("%Y%m%d")
    data_path = f"data/realtime/{today}/{symbol}.json"
    
    if os.path.exists(data_path):
        with open(data_path, 'r') as f:
            data = json.load(f)
            # 최신 데이터만 반환
            if data and isinstance(data, list):
                return data[-1]  # 가장 최근 데이터
    
    # 더미 데이터 (파일 없을 때)
    return {
        "symbol": symbol,
        "price": 100,
        "volume": 1000000,
        "rsi": 50,
        "macd": {"value": 0, "signal": 0, "histogram": 0}
    }

def calculate_ai_score(data: Dict) -> int:
    """AI 점수 계산 (실시간 데이터 기반)"""
    score = 50  # 기본값
    
    # RSI 기반
    rsi = data.get("rsi", 50)
    if rsi < 30:
        score += 25  # 과매도 → 매수 신호
    elif rsi > 70:
        score -= 20  # 과매수 → 매도 신호
    else:
        score += (50 - abs(rsi - 50)) / 2
    
    # MACD 기반
    macd_data = data.get("macd", {})
    histogram = macd_data.get("histogram", 0)
    if histogram > 0:
        score += 15  # 상승 모멘텀
    else:
        score -= 10  # 하락 모멘텀
    
    # 거래량 기반
    volume = data.get("volume", 1000000)
    avg_volume = 1000000  # 실제로는 20일 평균
    volume_ratio = volume / avg_volume
    
    if volume_ratio > 1.5:
        score += 10  # 거래량 급증
    elif volume_ratio < 0.5:
        score -= 5   # 거래량 감소
    
    return max(0, min(100, int(score)))

def detect_pattern_anomaly(symbol: str, data: Dict) -> Dict:
    """이상 패턴 감지"""
    anomalies = []
    severity = "low"
    
    # RSI 극단값
    rsi = data.get("rsi", 50)
    if rsi < 20:
        anomalies.append("극심한 과매도 (RSI < 20)")
        severity = "critical"
    elif rsi > 80:
        anomalies.append("극심한 과매수 (RSI > 80)")
        severity = "high"
    
    # 거래량 이상
    volume = data.get("volume", 1000000)
    avg_volume = 1000000
    volume_ratio = volume / avg_volume
    
    if volume_ratio > 3:
        anomalies.append(f"거래량 폭증 ({volume_ratio:.1f}배)")
        severity = "high" if severity == "low" else severity
    elif volume_ratio > 5:
        anomalies.append(f"거래량 이상 급증 ({volume_ratio:.1f}배)")
        severity = "critical"
    
    # 가격 급변
    price_change = data.get("price_change_percent", 0)
    if abs(price_change) > 5:
        anomalies.append(f"가격 급변동 ({price_change:+.1f}%)")
        severity = "high" if severity == "low" else severity
    
    has_anomaly = len(anomalies) > 0
    
    return {
        "has_anomaly": has_anomaly,
        "anomaly_type": ", ".join(anomalies) if anomalies else "정상",
        "severity": severity if has_anomaly else "none",
        "message": f"{symbol}: {', '.join(anomalies)}" if anomalies else f"{symbol}: 정상 패턴"
    }

def run(action: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """MCP 액션 실행"""
    
    if action == "process_realtime":
        symbol = payload.get("symbol", "AAPL")
        timeframe = payload.get("timeframe", "5m")
        
        # 실시간 데이터 로드
        data = load_realtime_data(symbol)
        
        # AI 점수 계산
        ai_score = calculate_ai_score(data)
        
        # 시그널 강도 결정
        if ai_score >= 85:
            signal_strength = "STRONG_BUY"
        elif ai_score >= 70:
            signal_strength = "BUY"
        elif ai_score >= 40:
            signal_strength = "HOLD"
        elif ai_score >= 20:
            signal_strength = "SELL"
        else:
            signal_strength = "STRONG_SELL"
        
        # MACD 시그널
        macd_data = data.get("macd", {})
        macd_signal = "BULLISH" if macd_data.get("histogram", 0) > 0 else "BEARISH"
        
        return {
            "symbol": symbol,
            "current_price": data.get("price", 0),
            "volume_ratio": data.get("volume", 1000000) / 1000000,
            "rsi": data.get("rsi", 50),
            "macd_signal": macd_signal,
            "ai_score": ai_score,
            "signal_strength": signal_strength,
            "timestamp": datetime.now().isoformat()
        }
    
    elif action == "detect_anomaly":
        symbol = payload.get("symbol", "AAPL")
        data = load_realtime_data(symbol)
        return detect_pattern_anomaly(symbol, data)
    
    elif action == "batch_process":
        symbols = payload.get("symbols", ["AAPL", "MSFT", "GOOGL"])
        
        high_score_symbols = []
        alerts = []
        
        for symbol in symbols:
            # 각 종목 처리
            data = load_realtime_data(symbol)
            ai_score = calculate_ai_score(data)
            
            # 고득점 종목
            if ai_score >= 85:
                high_score_symbols.append({
                    "symbol": symbol,
                    "score": ai_score
                })
            
            # 이상 감지
            anomaly = detect_pattern_anomaly(symbol, data)
            if anomaly["has_anomaly"] and anomaly["severity"] in ["high", "critical"]:
                alerts.append({
                    "symbol": symbol,
                    "alert": anomaly["message"],
                    "severity": anomaly["severity"]
                })
        
        return {
            "processed": len(symbols),
            "high_score_symbols": high_score_symbols,
            "alerts": alerts,
            "timestamp": datetime.now().isoformat()
        }
    
    return {"error": f"Unknown action: {action}"}
