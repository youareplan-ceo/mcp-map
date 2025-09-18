"""
News Sentiment Analyzer - 뉴스 수집 및 감성 분석
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List
import re
import random  # 실제로는 API 사용

class NewsSentimentAnalyzer:
    """뉴스 감성 분석기"""
    
    def __init__(self):
        self.positive_words = [
            "surge", "rally", "gain", "profit", "breakthrough", "innovation",
            "상승", "호재", "실적", "성장", "돌파", "혁신", "수익"
        ]
        
        self.negative_words = [
            "crash", "fall", "loss", "decline", "recall", "lawsuit",
            "하락", "악재", "손실", "리콜", "소송", "부진", "적자"
        ]
        
        self.news_cache = {}
    
    def collect_news(self, symbol: str, source: str = "all", hours: int = 24) -> Dict:
        """뉴스 수집 (실제로는 API 사용)"""
        
        # 더미 뉴스 데이터 생성
        dummy_news = {
            "NVDA": [
                {
                    "title": "NVIDIA Announces Revolutionary AI Chip Breaking Performance Records",
                    "source": "TechCrunch",
                    "timestamp": datetime.now().isoformat(),
                    "url": "https://example.com/news1",
                    "summary": "NVIDIA's new H200 GPU shows 3x performance improvement..."
                },
                {
                    "title": "엔비디아, 차세대 AI 칩 공개... 주가 급등 예상",
                    "source": "한국경제",
                    "timestamp": datetime.now().isoformat(),
                    "url": "https://example.com/news2",
                    "summary": "엔비디아가 혁신적인 AI 칩을 공개하며..."
                }
            ],
            "TSLA": [
                {
                    "title": "Tesla Recalls 100,000 Vehicles Over Safety Concerns",
                    "source": "Reuters",
                    "timestamp": datetime.now().isoformat(),
                    "url": "https://example.com/news3",
                    "summary": "Tesla announced a recall of Model 3 and Model Y..."
                },
                {
                    "title": "Tesla FSD Beta Shows Impressive Progress",
                    "source": "Electrek",
                    "timestamp": datetime.now().isoformat(),
                    "url": "https://example.com/news4",
                    "summary": "Latest FSD beta demonstrates significant improvements..."
                }
            ],
            "005930.KS": [  # 삼성전자
                {
                    "title": "삼성전자, 역대 최대 실적 달성 전망",
                    "source": "매일경제",
                    "timestamp": datetime.now().isoformat(),
                    "url": "https://example.com/news5",
                    "summary": "삼성전자가 4분기 반도체 호황으로..."
                }
            ]
        }
        
        # 심볼에 해당하는 뉴스 반환
        articles = dummy_news.get(symbol, [
            {
                "title": f"Latest Update on {symbol}",
                "source": "Generic News",
                "timestamp": datetime.now().isoformat(),
                "url": "https://example.com/generic",
                "summary": f"Market analysis for {symbol}..."
            }
        ])
        
        return {
            "news_count": len(articles),
            "articles": articles,
            "last_updated": datetime.now().isoformat()
        }
    
    def analyze_sentiment(self, text: str, symbol: str = None) -> Dict:
        """텍스트 감성 분석"""
        
        text_lower = text.lower()
        
        # 긍정/부정 단어 카운트
        positive_count = sum(1 for word in self.positive_words if word in text_lower)
        negative_count = sum(1 for word in self.negative_words if word in text_lower)
        
        # 감성 점수 계산 (-100 ~ +100)
        if positive_count + negative_count == 0:
            sentiment_score = 0
        else:
            sentiment_score = ((positive_count - negative_count) / (positive_count + negative_count)) * 100
        
        # 감성 라벨
        if sentiment_score > 30:
            sentiment_label = "positive"
        elif sentiment_score < -30:
            sentiment_label = "negative"
        else:
            sentiment_label = "neutral"
        
        # 주가 영향도 예측 (단순화된 버전)
        impact_prediction = sentiment_score * 0.05  # -5% ~ +5%
        
        # 핵심 키워드 추출
        keywords = []
        for word in self.positive_words + self.negative_words:
            if word in text_lower:
                keywords.append(word)
        
        # 특별 이벤트 감지
        special_events = []
        if "recall" in text_lower or "리콜" in text_lower:
            special_events.append("RECALL_WARNING")
            impact_prediction -= 2
        if "breakthrough" in text_lower or "혁신" in text_lower:
            special_events.append("INNOVATION_SIGNAL")
            impact_prediction += 2
        if "lawsuit" in text_lower or "소송" in text_lower:
            special_events.append("LEGAL_RISK")
            impact_prediction -= 1.5
        if "earnings beat" in text_lower or "실적 호조" in text_lower:
            special_events.append("EARNINGS_BEAT")
            impact_prediction += 3
        
        return {
            "sentiment_score": round(sentiment_score, 2),
            "sentiment_label": sentiment_label,
            "impact_prediction": round(impact_prediction, 2),
            "keywords": keywords[:5],  # 상위 5개
            "special_events": special_events
        }
    
    def get_market_mood(self, symbols: List[str]) -> Dict:
        """전체 시장 분위기 분석"""
        
        overall_sentiments = []
        bullish_count = 0
        bearish_count = 0
        symbol_sentiments = []
        alerts = []
        
        for symbol in symbols:
            # 각 종목 뉴스 수집
            news_data = self.collect_news(symbol)
            
            # 각 기사 감성 분석
            symbol_sentiment = 0
            for article in news_data["articles"]:
                full_text = f"{article['title']} {article['summary']}"
                analysis = self.analyze_sentiment(full_text, symbol)
                symbol_sentiment += analysis["sentiment_score"]
                
                # 특별 알림
                if analysis["sentiment_score"] > 70:
                    alerts.append({
                        "type": "STRONG_POSITIVE",
                        "symbol": symbol,
                        "message": f"{symbol}: 매우 긍정적 뉴스 - {article['title'][:50]}..."
                    })
                elif analysis["sentiment_score"] < -70:
                    alerts.append({
                        "type": "STRONG_NEGATIVE",
                        "symbol": symbol,
                        "message": f"{symbol}: 부정적 뉴스 주의 - {article['title'][:50]}..."
                    })
                
                # 특별 이벤트 알림
                if analysis.get("special_events"):
                    for event in analysis["special_events"]:
                        alerts.append({
                            "type": event,
                            "symbol": symbol,
                            "message": f"{symbol}: {event} 감지"
                        })
            
            # 평균 감성 계산
            avg_sentiment = symbol_sentiment / len(news_data["articles"]) if news_data["articles"] else 0
            
            symbol_sentiments.append({
                "symbol": symbol,
                "sentiment": avg_sentiment,
                "news_count": news_data["news_count"]
            })
            
            overall_sentiments.append(avg_sentiment)
            
            if avg_sentiment > 30:
                bullish_count += 1
            elif avg_sentiment < -30:
                bearish_count += 1
        
        # 정렬
        symbol_sentiments.sort(key=lambda x: x["sentiment"], reverse=True)
        
        # 전체 시장 감성
        overall_sentiment = sum(overall_sentiments) / len(overall_sentiments) if overall_sentiments else 0
        
        return {
            "overall_sentiment": round(overall_sentiment, 2),
            "bullish_count": bullish_count,
            "bearish_count": bearish_count,
            "top_positive": symbol_sentiments[:3],
            "top_negative": symbol_sentiments[-3:] if len(symbol_sentiments) > 3 else [],
            "alerts": alerts[:10],  # 최대 10개 알림
            "market_status": self._get_market_status(overall_sentiment),
            "timestamp": datetime.now().isoformat()
        }
    
    def _get_market_status(self, sentiment: float) -> str:
        """시장 상태 판단"""
        if sentiment > 50:
            return "🔥 VERY_BULLISH"
        elif sentiment > 20:
            return "📈 BULLISH"
        elif sentiment < -50:
            return "🚨 VERY_BEARISH"
        elif sentiment < -20:
            return "📉 BEARISH"
        else:
            return "➡️ NEUTRAL"

# MCP 인터페이스
analyzer = NewsSentimentAnalyzer()

def run(action: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """MCP 액션 실행"""
    
    if action == "collect_news":
        symbol = payload.get("symbol", "AAPL")
        source = payload.get("source", "all")
        hours = payload.get("hours", 24)
        
        return analyzer.collect_news(symbol, source, hours)
    
    elif action == "analyze_sentiment":
        text = payload.get("text", "")
        symbol = payload.get("symbol", None)
        
        if not text:
            return {"error": "Text is required for sentiment analysis"}
        
        return analyzer.analyze_sentiment(text, symbol)
    
    elif action == "get_market_mood":
        symbols = payload.get("symbols", ["AAPL", "NVDA", "TSLA", "GOOGL", "MSFT"])
        
        return analyzer.get_market_mood(symbols)
    
    return {"error": f"Unknown action: {action}"}

# 테스트 실행
if __name__ == "__main__":
    # 뉴스 수집 테스트
    news = run("collect_news", {"symbol": "NVDA"})
    print(f"📰 NVDA 뉴스: {news['news_count']}개")
    
    # 감성 분석 테스트
    sentiment = run("analyze_sentiment", {
        "text": "NVIDIA announces breakthrough AI chip with record-breaking performance",
        "symbol": "NVDA"
    })
    print(f"📊 감성 분석: {sentiment['sentiment_label']} ({sentiment['sentiment_score']})")
    
    # 시장 분위기 테스트
    mood = run("get_market_mood", {
        "symbols": ["NVDA", "TSLA", "AAPL"]
    })
    print(f"🌍 시장 분위기: {mood['market_status']}")
    print(f"   전체 감성: {mood['overall_sentiment']}")
    print(f"   강세: {mood['bullish_count']}개 | 약세: {mood['bearish_count']}개")
    
    if mood['alerts']:
        print("\n⚠️ 알림:")
        for alert in mood['alerts'][:3]:
            print(f"   • {alert['message']}")
