# 🚀 MCP-MAP Project

AI 기반 통합 비즈니스 자동화 시스템

## 📁 프로젝트 구조

```
mcp-map/
├── 📱 web/              # 웹 대시보드 (Vercel 배포)
│   ├── index.html       # 메인 대시보드
│   └── api.js           # API 연결 모듈
│
├── 🚀 apps/             # 애플리케이션
│   ├── stockpilot/      # 주식 분석 시스템
│   ├── stockpilot_price_api.py  # 실시간 주가 API
│   └── stockpilot_dashboard.py  # 대시보드
│
├── 🤖 mcp/              # 자동화 엔진
│   ├── flows/           # 워크플로우 정의
│   ├── agents/          # 실행 에이전트
│   └── run.py           # 플로우 실행기
│
├── 📊 data/             # 데이터 저장소
└── 📑 docs/             # 문서
```

## 🌐 시스템 아키텍처

```
[Web Dashboard] ← API → [Backend Services]
      ↓                        ↓
  Visualization          Data Processing
  User Interface         Business Logic
```

## ✨ 핵심 기능

### 📈 StockPilot - 실시간 주식 분석
- **실시간 주가 모니터링**: 한국/미국 주요 종목
- **기술적 분석**: RSI, MACD, 볼린저밴드
- **AI 추천**: 매수/매도 신호 생성
- **포트폴리오 관리**: 자산 배분 최적화

### 💼 정책자금 자동화
- **공고 수집**: 정부/지자체 지원사업 자동 수집
- **자격 분석**: AI 기반 자격요건 매칭
- **신청서 작성**: 자동 서류 생성

### 🔄 워크플로우 자동화
- **스케줄링**: 정기 작업 자동 실행
- **데이터 파이프라인**: ETL 프로세스
- **알림 시스템**: 실시간 알림 발송

## 🚀 빠른 시작

### 1. 설치
```bash
# 저장소 클론
git clone https://github.com/youareplan-ceo/mcp-map.git
cd mcp-map

# 의존성 설치
./install.sh
```

### 2. 환경 설정
```bash
# .env 파일 편집
cp .env.example .env
nano .env
```

### 3. 실행
```bash
# 전체 시스템 시작
python launch_mcp_map.py

# 개별 서비스 실행
python apps/stockpilot_price_api.py  # API 서버
streamlit run apps/stockpilot_dashboard.py  # 대시보드
```

## 📡 API 엔드포인트

### StockPilot API
```
GET  /api/price/{ticker}      # 실시간 주가
GET  /api/analysis/{ticker}   # 기술적 분석
GET  /api/chart/{ticker}      # 차트 데이터
POST /api/prices              # 다중 종목 조회
GET  /api/recommend           # AI 추천
GET  /api/popular             # 인기 종목
```

### 사용 예시
```bash
# 애플 주가 조회
curl http://localhost:8002/api/price/AAPL

# 삼성전자 기술 분석
curl http://localhost:8002/api/analysis/005930.KS

# AI 추천 종목
curl http://localhost:8002/api/recommend
```

## 🛠 기술 스택

- **Backend**: Python 3.9+, FastAPI, yfinance
- **Frontend**: React, Streamlit, Plotly
- **Database**: DuckDB, PostgreSQL
- **AI/ML**: OpenAI API, Anthropic API
- **Deploy**: Docker, Vercel

## 📦 주요 의존성

```txt
fastapi==0.104.1
yfinance==0.2.28
pandas==2.1.3
streamlit==1.29.0
plotly==5.18.0
```

## 🔧 설정

### 필수 API 키
- OpenAI API Key
- Anthropic API Key (선택)
- 증권사 API (선택)

### 포트 설정
- API Server: 8002
- Dashboard: 8501
- Database: 5432

## 📊 모니터링

대시보드 접속:
```
http://localhost:8501
```

## 🤝 기여

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## 📄 라이센스

MIT License

## 📞 문의

- GitHub: [@youareplan-ceo](https://github.com/youareplan-ceo)
- Email: contact@youareplan.com

---

**Built with ❤️ by YouArePlan CEO**