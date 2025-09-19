# 🚀 StockPilot-AI

AI 기반 실시간 주식 분석 및 자동매매 시스템

## 📊 핵심 기능

### 실시간 분석
- 한국/미국 주식 실시간 모니터링
- RSI, MACD, 볼린저밴드 기술적 분석
- AI 기반 매수/매도 신호 생성

### 시뮬레이션 트레이딩
- 모의 투자 시스템
- 포트폴리오 손익 추적
- 거래 기록 관리

### AI 추천
- 골든크로스/데드크로스 감지
- PER 기반 가치주 발굴
- 신뢰도 기반 추천

## 🚀 빠른 시작

### 1. API 서버 실행
```bash
cd StockPilot-ai
python price_api.py
# http://localhost:8002
```

### 2. 대시보드 실행
```bash
streamlit run dashboard.py
# http://localhost:8501
```

## 📡 API 엔드포인트

- `GET /api/price/{ticker}` - 실시간 주가
- `GET /api/analysis/{ticker}` - 기술적 분석
- `GET /api/chart/{ticker}` - 차트 데이터
- `POST /api/prices` - 다중 종목 조회
- `GET /api/recommend` - AI 추천
- `GET /api/popular` - 인기 종목

## 🛠 기술 스택

- **Backend**: FastAPI, yfinance
- **Frontend**: Streamlit, Plotly
- **AI**: OpenAI API, Technical Indicators

## 📄 라이선스

© 2024 StockPilot-AI. All rights reserved.