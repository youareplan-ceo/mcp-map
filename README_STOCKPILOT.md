# 🚀 StockPilot AI Trading System v2.0

## 📊 현재 상태
- ✅ **로컬 환경**: 100% 완성
- 🔄 **온라인 배포**: 준비 완료 (배포 대기)
- 📰 **뉴스 분석**: MCP 도구 추가 완료

---

## 💻 로컬 실행 (현재 가능)

### 1. 전체 시스템 실행
```bash
python stockpilot_master.py
# 선택: 1 (전체 시작)
```

### 2. 24시간 테스트
```bash
python run_24h_test.py
# 웹 대시보드: http://localhost:9999
```

### 3. 개별 컴포넌트
```bash
python realtime_data_collector.py     # 실시간 수집
python auto_paper_trader.py           # 자동 매매
python paper_trading_analyzer.py      # 성과 분석
python performance_dashboard.py       # 웹 대시보드
```

---

## 🌐 온라인 배포 방법

### 옵션 1: Streamlit Cloud (가장 쉬움, 무료)
```bash
python deploy_online.py
# 선택: 1

# GitHub 업로드 후
# share.streamlit.io 에서 연결
# → 자동으로 온라인 URL 생성
```

### 옵션 2: Heroku (중급)
```bash
python deploy_online.py
# 선택: 2

heroku create stockpilot-app
git push heroku main
heroku open
```

### 옵션 3: 자체 서버 (Docker)
```bash
python deploy_online.py
# 선택: 3

docker-compose up -d
# → https://your-domain.com
```

---

## 📰 뉴스 기능 (NEW!)

### MCP 뉴스 분석 도구
- **위치**: `mcp/tools/news_analyzer/`
- **기능**:
  - 실시간 뉴스 수집
  - 감성 분석 (-100 ~ +100)
  - 주가 영향도 예측
  - 긴급 알림

### 뉴스 통합 Flow
```yaml
name: news_integrated_signal
# 뉴스 + 기술 분석 통합
# AI 점수 = (기술 60% + 뉴스 40%)
```

---

## 📱 접속 URL (로컬)

| 서비스 | URL | 설명 |
|--------|-----|------|
| 메인 앱 | http://localhost:8000 | StockPilot 메인 |
| 성과 대시보드 | http://localhost:8001/dashboard | 실시간 성과 |
| 24시간 모니터 | http://localhost:9999 | 종합 모니터링 |
| API 문서 | http://localhost:8001/docs | FastAPI Docs |

---

## 🎯 실전 체크리스트

### 필수 확인
- [ ] watchlist.txt 종목 설정
- [ ] 초기 자금 설정 (1000만원)
- [ ] 알림 임계값 설정
- [ ] 뉴스 소스 API 키 설정

### 성과 목표
- [ ] 일일 수익률: +2% 이상
- [ ] 승률: 70% 이상
- [ ] 최대 낙폭: -5% 이내
- [ ] 월 수익률: +10% 이상

---

## 📞 문제 해결

### 시스템 재시작
```bash
python stockpilot_master.py
> 2 (전체 중지)
> 1 (전체 시작)
```

### 데이터베이스 초기화
```bash
rm trades.db
python prepare_live_test.py
```

### 로그 확인
```bash
tail -f logs/*.log
```

---

## 🔄 다음 업데이트 예정

1. **실제 API 연동**
   - Alpaca Trading API
   - Yahoo Finance API
   - News API

2. **머신러닝 고도화**
   - LSTM 가격 예측
   - 강화학습 전략 최적화

3. **모바일 앱**
   - React Native
   - 실시간 푸시 알림

---

**Created by CEO & Claude & GPT Team**
**Version 2.0.0 | 2025.01.15**
