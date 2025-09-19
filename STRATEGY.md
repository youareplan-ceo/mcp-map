# 📈 자산 증식 코치 - 사업 전략 문서

## 🎯 핵심 철학
**"매매 실행 없음, 최고의 정보만 제공"**
- 우리는 코치, 실행은 사용자가 증권사 앱에서

---

## 🚀 3단계 사업 로드맵

### **Phase 1: 포트폴리오 최적화 (MVP)**
> 목표: 보유 종목 수익 극대화

#### 핵심 기능
1. **포트폴리오 관리**
   - 사용자 보유 종목 등록
   - 실시간 수익률 추적
   - 매도 타이밍 알림

2. **데이터 수집 전략**
   ```python
   # 주가: 포트폴리오 종목만 실시간
   user_stocks = ["삼성전자", "SK하이닉스", "네이버"]  # 10-20개
   
   # 뉴스: 전체 수집 → AI 필터링
   all_news = collect_everything()  # 일 10,000개
   relevant = ai_filter(all_news, user_stocks)  # 10-50개
   ```

3. **알림 시스템**
   - 🚨 긴급: 목표가 도달, 급락 신호
   - ⚠️ 중요: 관련 악재/호재
   - 📰 일반: 일일 리포트

#### 기술 스택
```yaml
Frontend: Vercel (무료)
Backend: FastAPI + Railway ($5)
Database: Supabase (무료)
주가 API: yfinance (무료)
뉴스: RSS + 웹스크래핑 (무료)
AI: Claude API ($20)
월 비용: 약 3만원
```

#### 수익 모델
```python
pricing = {
    "무료": {
        "종목": 3개,
        "알림": "일 3회",
        "리포트": "주간"
    },
    "프리미엄": {  # 월 9,900원
        "종목": "무제한",
        "알림": "실시간",
        "리포트": "일일",
        "AI 분석": True
    }
}
```

---

### **Phase 2: 전체 시장 데이터 구축**
> 목표: AI 추천 기반 마련

#### 데이터 확보
1. **한국 시장**
   ```python
   # FinanceDataReader 활용
   kospi_all = fdr.StockListing('KOSPI')   # 900개
   kosdaq_all = fdr.StockListing('KOSDAQ')  # 1,600개
   total_kr = 2,500개
   ```

2. **미국 시장**
   ```python
   # 주요 지수만
   sp500 = get_sp500_list()      # 500개
   nasdaq100 = get_nasdaq100()   # 100개
   total_us = 600개
   ```

3. **3-Tier 데이터 관리**
   ```python
   class DataTiers:
       realtime = []     # 100개 (사용자 포트폴리오 + HOT)
       cached = []       # 500개 (1시간 갱신)
       on_demand = []    # 나머지 (요청시)
   ```

#### 뉴스 수집 고도화
```python
sources = {
    "국내": ["네이버", "다음", "한경", "매경"],
    "해외": ["Bloomberg", "Reuters", "WSJ"],
    "공시": ["DART", "KIND", "SEC"],
    "소셜": ["Reddit r/stocks", "StockTwits"]
}

# 영향도 분석
def analyze_impact(news, portfolio):
    # 1차: 직접 언급
    # 2차: 경쟁사/섹터
    # 3차: 공급망/매크로
    return impact_score
```

---

### **Phase 3: AI 추천 시스템**
> 목표: 개인 맞춤 매수/매도 추천

#### AI 추천 로직
```python
class AIRecommender:
    def analyze_user(self, user_id):
        # 1. 포트폴리오 분석
        portfolio = get_portfolio(user_id)
        overweight = find_overweight(portfolio)
        missing_sectors = find_gaps(portfolio)
        
        # 2. 시장 기회 스캔
        opportunities = scan_market()  # 전체 3,000개
        filtered = filter_by_user(opportunities, user_profile)
        
        # 3. Claude API 분석
        recommendations = claude_api.analyze({
            "portfolio": portfolio,
            "opportunities": filtered,
            "risk_profile": user.risk_level,
            "market_condition": get_market_status()
        })
        
        return {
            "매도": recommendations.sell,  # 포트폴리오 내
            "매수": recommendations.buy,    # 신규 종목
            "리밸런싱": recommendations.rebalance
        }
```

#### 차별화 전략
```python
features = {
    "무료": {
        "추천": "주 3개",
        "분석": "기본 지표만"
    },
    "프리미엄": {  # 월 9,900원
        "추천": "일일 무제한",
        "분석": "Claude AI 심층"
    },
    "프로": {  # 월 29,900원
        "추천": "실시간",
        "백테스팅": True,
        "자동 리밸런싱": True
    }
}
```

---

## 💰 예상 수익 시뮬레이션

### 6개월 후
- 사용자: 1,000명
- 유료전환: 10% (100명)
- 월 수익: 99만원

### 1년 후
- 사용자: 5,000명
- 유료전환: 15% (750명)
- 월 수익: 742만원

### 2년 후
- 사용자: 20,000명
- 유료전환: 20% (4,000명)
- B2B 계약: 5개
- 월 수익: 5,000만원

---

## 🔧 현재 필요한 MCP 도구

### 있는 것 (활용)
1. portfolio - 포트폴리오 관리
2. market - 실시간 주가
3. signals - 매매 신호
4. news_analyzer - 뉴스 분석

### 추가 필요
1. **user_data** - 사용자 데이터 관리
2. **profit_analyzer** - 수익 분석
3. **ai_advisor** - Claude API 연동

---

## 📝 Action Items

### 즉시 (1-2주)
- [ ] user_data MCP 도구 개발
- [ ] 포트폴리오 CRUD API 구축
- [ ] 실시간 가격 추적 시스템
- [ ] 기본 알림 기능

### 단기 (1개월)
- [ ] 전체 종목 리스트 DB 구축
- [ ] 뉴스 수집 파이프라인
- [ ] AI 필터링 로직
- [ ] 프리미엄 결제 시스템

### 중기 (3개월)
- [ ] AI 추천 엔진
- [ ] 백테스팅 시스템
- [ ] B2B API
- [ ] 모바일 앱

---

## 📌 핵심 원칙
1. **작게 시작** - 포트폴리오 최적화부터
2. **빠른 검증** - MVP로 시장 반응 테스트
3. **단계적 확장** - 데이터 → AI 순서로
4. **비용 최적화** - 무료 리소스 최대 활용
5. **명확한 가치** - "매도 타이밍"이 핵심

---

*Last Updated: 2025-09-19*
*By: YouArePlan CEO & 김실장*
