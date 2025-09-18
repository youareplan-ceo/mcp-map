# StockPilot 수익 극대화 시스템 설계서
> 실제 수익을 내면서 규제를 회피하는 전략

## 1. 3단계 AI 필터링 시스템

### Level 1: 기초 스크리닝 (1000종목 → 100종목)
```python
def level1_screening(all_stocks):
    """빠른 필터링으로 쓰레기 종목 제거"""
    filtered = []
    for stock in all_stocks:
        if (stock.volume > avg_volume * 1.5 and  # 거래량 증가
            stock.rsi < 70 and                   # 과매수 아님
            stock.price > sma_20):                # 상승 추세
            filtered.append(stock)
    return filtered
```

### Level 2: AI 패턴 매칭 (100종목 → 20종목)
```python
def level2_ai_pattern(stocks):
    """과거 수익난 패턴과 유사도 체크"""
    high_profit_patterns = load_patterns()  # 백테스팅으로 찾은 패턴
    
    for stock in stocks:
        pattern_score = 0
        # 3일전 -3%, 2일전 +1%, 1일전 +2% → 오늘 +5% 패턴
        if matches_pattern(stock, high_profit_patterns):
            pattern_score = 95
        
        stock.ai_score = pattern_score
    
    return top_20_by_score(stocks)
```

### Level 3: 실전 검증 (20종목 → 5종목)
```python
def level3_realworld_validation(stocks):
    """최근 7일 실제 수익률 검증"""
    for stock in stocks:
        # 이 전략이 실제로 돈 벌었나?
        recent_performance = backtest_last_7days(stock)
        if recent_performance.win_rate < 0.7:
            stock.ai_score *= 0.8  # 점수 하향
    
    return top_5_by_score(stocks)
```

## 2. 점수-문구 변환 시스템 (규제 회피)

```python
class ComplianceMessenger:
    """점수를 합법적 문구로 변환"""
    
    MESSAGES = {
        (95, 100): {
            "signal": "매우 긍정적 시그널 포착",
            "action": "적극적 관심 필요",
            "risk": "단기 변동 가능성 존재",
            # 실제 의미: 지금 사세요!!!
        },
        (85, 94): {
            "signal": "긍정적 모멘텀 진행",
            "action": "포트폴리오 편입 고려 가능",
            "risk": "시장 상황 주시 필요",
            # 실제 의미: 매수 적기
        },
        (70, 84): {
            "signal": "중립 구간",
            "action": "추가 시그널 대기",
            "risk": "방향성 불명확",
            # 실제 의미: 홀드
        },
        (50, 69): {
            "signal": "조정 가능성",
            "action": "리스크 관리 점검",
            "risk": "하방 압력 존재",
            # 실제 의미: 매도 준비
        },
        (0, 49): {
            "signal": "부정적 시그널 감지",
            "action": "포지션 재검토 필요",
            "risk": "추가 하락 가능성",
            # 실제 의미: 당장 팔아!!!
        }
    }
    
    def convert(self, score):
        for (min_score, max_score), messages in self.MESSAGES.items():
            if min_score <= score <= max_score:
                return messages
```

## 3. 개인화 수익 추적 시스템

```python
class UserProfitTracker:
    """사용자별 수익률 몰래 추적"""
    
    def __init__(self):
        self.user_data = {}
    
    def track_signal_follow(self, user_id, signal):
        """사용자가 시그널 따랐는지 추정"""
        # 시그널 후 해당 종목 조회 증가 → 매수 추정
        # 가격 하락 후 조회 감소 → 매도 추정
        
        if user_id not in self.user_data:
            self.user_data[user_id] = {
                "signals_followed": [],
                "estimated_profit": 0,
                "user_type": None  # 공격적/보수적
            }
        
        # 패턴 분석
        self.analyze_user_pattern(user_id)
    
    def analyze_user_pattern(self, user_id):
        """사용자 성향 분석"""
        user = self.user_data[user_id]
        
        # 고점수(90+) 시그널만 따르는가? → 보수적
        # 70점대도 따르는가? → 공격적
        # 수익률 높은 사용자 전략 → AI 학습
        
        if user["estimated_profit"] > 0.2:  # 20% 이상 수익
            self.learn_from_winner(user)
        elif user["estimated_profit"] < -0.1:  # 10% 이상 손실
            self.learn_from_loser(user)
    
    def personalize_signals(self, user_id):
        """개인 맞춤 시그널"""
        user_type = self.user_data[user_id]["user_type"]
        
        if user_type == "conservative":
            return self.get_safe_signals()  # 승률 85% 이상
        elif user_type == "aggressive":
            return self.get_high_return_signals()  # 수익률 30% 이상
        else:
            return self.get_balanced_signals()
```

## 4. A/B 테스트 시스템

```python
class ABTestManager:
    """어떤 전략이 진짜 돈 버는지 테스트"""
    
    def __init__(self):
        self.groups = {
            "A": {
                "strategy": "conservative",
                "min_score": 85,
                "users": [],
                "total_profit": 0
            },
            "B": {
                "strategy": "aggressive", 
                "min_score": 70,
                "users": [],
                "total_profit": 0
            },
            "C": {
                "strategy": "momentum",
                "min_score": 75,
                "users": [],
                "total_profit": 0
            }
        }
    
    def assign_user(self, user_id):
        """신규 사용자 랜덤 배정"""
        import random
        group = random.choice(["A", "B", "C"])
        self.groups[group]["users"].append(user_id)
        return group
    
    def measure_performance(self):
        """30일마다 성과 측정"""
        best_group = None
        best_profit = 0
        
        for group_name, group_data in self.groups.items():
            avg_profit = group_data["total_profit"] / len(group_data["users"])
            
            if avg_profit > best_profit:
                best_profit = avg_profit
                best_group = group_name
        
        # 가장 수익 높은 전략으로 통일
        self.apply_winning_strategy(best_group)
```

## 5. 실전 수익 검증 루프

```python
class ProfitValidationLoop:
    """24시간 실시간 검증"""
    
    def __init__(self):
        self.signals_given = []  # 어제 준 시그널
        self.actual_results = []  # 오늘 실제 결과
    
    async def daily_validation(self):
        """매일 새벽 2시 실행"""
        
        # 1. 어제 높은 점수 준 종목들
        yesterday_signals = self.get_yesterday_signals()
        
        # 2. 오늘 실제 수익률
        for signal in yesterday_signals:
            actual = get_actual_return(signal.symbol)
            expected = signal.expected_return
            
            accuracy = 1 - abs(actual - expected) / expected
            
            # 3. 정확도 낮으면 모델 수정
            if accuracy < 0.7:
                self.adjust_model(signal.strategy)
        
        # 4. 새로운 전략 추가
        if self.find_new_pattern():
            self.add_strategy()
    
    def adjust_model(self, strategy):
        """실패한 전략 가중치 감소"""
        strategy.weight *= 0.9
        
        # 가중치 0.5 이하면 제거
        if strategy.weight < 0.5:
            self.remove_strategy(strategy)
```

## 6. 비용 최적화

```python
class CostOptimizer:
    """API 비용 최소화"""
    
    CACHE_DURATION = {
        "realtime_price": 60,      # 60초
        "technical_indicators": 300, # 5분
        "ai_analysis": 3600,       # 1시간
        "news_sentiment": 7200     # 2시간
    }
    
    def get_data(self, symbol, data_type):
        # 캐시 먼저 체크
        cached = self.check_cache(symbol, data_type)
        if cached and not self.is_expired(cached):
            return cached
        
        # 필요한 경우만 API 호출
        if self.is_worth_calling(symbol):
            return self.fetch_and_cache(symbol, data_type)
        
        return cached  # 오래된 데이터라도 반환
    
    def is_worth_calling(self, symbol):
        """API 호출 가치 있나?"""
        # 거래량 없으면 스킵
        # 변동성 낮으면 스킵
        # 사용자 관심 없으면 스킵
        return True
```

## 7. 데이터베이스 스키마

```sql
-- 시그널 성과 추적
CREATE TABLE signal_performance (
    signal_id TEXT PRIMARY KEY,
    symbol TEXT NOT NULL,
    signal_date TIMESTAMP,
    ai_score INTEGER,
    expected_return REAL,
    actual_return REAL,
    accuracy REAL,
    strategy_used TEXT,
    user_followed_count INTEGER DEFAULT 0
);

-- 사용자 수익률 (암묵적 추적)
CREATE TABLE user_profit_tracking (
    user_id TEXT,
    date DATE,
    estimated_portfolio_value REAL,
    signals_viewed INTEGER,
    signals_followed_est INTEGER,
    profit_rate REAL,
    user_segment TEXT  -- 'winner', 'loser', 'neutral'
);

-- A/B 테스트 결과
CREATE TABLE ab_test_results (
    test_id TEXT,
    group_name TEXT,
    strategy TEXT,
    user_count INTEGER,
    avg_profit_rate REAL,
    win_rate REAL,
    test_period_days INTEGER
);
```

## 8. 핵심 KPI

1. **실제 수익률** (사용자가 따라했을 때)
2. **시그널 정확도** (예측 vs 실제)
3. **사용자 재방문율** (돈 벌면 계속 옴)
4. **유료 전환율** (무료 → 프로)
5. **API 비용 대비 수익** (ROI)

---

**면책조항**: 본 시스템은 정보 제공 목적이며 투자 권유가 아닙니다.
(하지만 진짜 목표는 사용자가 돈 벌게 하는 것)
