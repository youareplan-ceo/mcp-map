# 🚀 MCP-MAP Project

AI 기반 주식 자동매매 시스템 with MCP (Model Context Protocol)

## 📑 프로젝트 개요

MCP-MAP은 "최소 자금으로 최대 성능"을 목표로 하는 통합 AI 플랫폼입니다.
여러 AI 도구들(MCP)을 레고 블록처럼 조합하여 다양한 앱을 만들 수 있습니다.

## 🏗️ MCP-MAP 핵심 구조 이해하기 (중요!)

### 💡 MCP-MAP이란?
**MCP-MAP = 레고 블록 시스템**
- **MCP 도구들** = 레고 블록 (재사용 가능한 기능 모듈)
- **MCP-MAP** = 레고 판 (블록을 조립하는 플랫폼)
- **주식앱/정책자금앱** = 완성된 레고 작품

### 📐 실제 작동 구조
```
사용자 → index.html (UI)
           ↓
    MCP Bridge Server (8001포트)
    /        |        \
portfolio  signals  market  (MCP 도구들)
    ↓        ↓        ↓
yfinance  Claude AI  데이터분석
    ↓        ↓        ↓
    통합 분석 결과
           ↓
    화면에 표시
```

## 📁 프로젝트 구조

```
mcp-map/
├── 📱 index.html        # 메인 UI (StockPilot AI)
├── 🧠 mcp/              # MCP 도구들
│   ├── tools/           # 개별 기능 도구
│   │   ├── portfolio/   # 포트폴리오 분석
│   │   ├── signals/     # 매매 신호
│   │   ├── market/      # 시장 분석
│   │   └── ...
│   └── run.py           # MCP 실행기
│
├── 🤖 백엔드 서버
│   ├── stockpilot_complete_app.py  # 메인 서버 (8000포트)
│   ├── mcp_bridge.py               # MCP 연결 서버 (8001포트)
│   ├── auth.py                     # 인증
│   ├── database.py                 # DB 관리
│   └── market_data.py              # 시장 데이터
│
└── 📊 설정 파일
    ├── .env                        # API 키 (비공개)
    ├── requirements-saas.txt       # Python 패키지
    └── vercel.json                 # Vercel 배포 설정
```

## 🌐 배포 아키텍처

```
[Vercel Cloud] ← API 통신 → [로컬 서버]
     ↓                           ↓
  웹 대시보드               MCP 서버들
  (UI만)                  (실제 작업)
```

### Vercel (클라우드)
- **URL**: https://mcp-map.vercel.app
- **역할**: UI 표시만
- **비용**: 무료

### 로컬 서버
- **포트 8000**: FastAPI 메인 서버
- **포트 8001**: MCP Bridge 서버
- **역할**: 실제 데이터 처리, AI 분석

## 🔌 MCP 도구 연결 방법

### 1. **MCP Bridge 서버 실행** (핵심!)
```bash
cd /Users/youareplan/mcp-map
python mcp_bridge.py  # 8001포트
```

### 2. **기존 FastAPI 서버 실행**
```bash
python stockpilot_complete_app.py  # 8000포트
```

### 3. **UI에서 API 호출**
```javascript
// MCP 도구 호출 예시
fetch('http://localhost:8001/api/portfolio/analyze', {
    method: 'POST',
    body: JSON.stringify({
        tickers: ['AAPL', 'GOOGL'],
        period: '3mo'
    })
})
```

## 📦 MCP 도구 목록 및 용도

| MCP 도구 | 위치 | 기능 | 사용 예시 |
|---------|------|------|----------|
| **portfolio** | `mcp/tools/portfolio/` | 포트폴리오 분석, 골든크로스 탐지 | 종목 분석, 매수 타이밍 |
| **signals** | `mcp/tools/signals/` | 매매 신호 생성 | 매도 타이밍, 손절선 |
| **market** | `mcp/tools/market/` | 시장 전체 분석 | KOSPI 상황, 섹터 분석 |
| **webfetch** | `mcp/tools/webfetch/` | 웹 데이터 수집 | 뉴스, 공시 정보 |
| **embedder** | `mcp/tools/embedder/` | 텍스트 임베딩 | AI 학습 데이터 |
| **qdrant** | `mcp/tools/qdrant/` | 벡터 DB 관리 | 유사 종목 검색 |

## 💰 비용 절감 효과

**기존 방식 (월 780만원)**
```
주식 API 구독: 100만원/월
AI API 각각: 50만원 x 3
서버 운영: 30만원/월  
개발자: 500만원/월
```

**MCP-MAP 방식 (월 5만원)**
```
MCP 도구: 무료 (오픈소스)
AI API: 5만원/월 (사용량 기반)
Vercel: 무료 플랜
운영: 회장님 직접
```

## 🚀 빠른 시작 가이드

### 1단계: 로컬 환경 설정
```bash
cd /Users/youareplan/mcp-map
python -m venv venv
source venv/bin/activate
pip install -r requirements-saas.txt
```

### 2단계: 환경변수 설정
```bash
cp .env.example .env
# .env 파일 편집하여 API 키 입력
# ANTHROPIC_API_KEY=sk-ant-...
# OPENAI_API_KEY=sk-...
# GEMINI_API_KEY=...
```

### 3단계: 서버 실행
```bash
# 터미널 1 - 메인 서버
python stockpilot_complete_app.py

# 터미널 2 - MCP Bridge  
python mcp_bridge.py

# 브라우저에서 접속
http://localhost:8000
```

## 🔥 현재 작업 상태 (2025.01.19)

### ✅ 완성된 부분 (85%)
- [x] UI 인터페이스 (index.html) - StockPilot AI
- [x] FastAPI 백엔드 서버
- [x] MCP 도구 구조
- [x] 데이터베이스 연동
- [x] 인증 시스템
- [x] Vercel 배포

### ⚠️ 추가 필요한 부분 (15%)
- [ ] MCP Bridge 서버 실행 테스트
- [ ] 실시간 WebSocket 연결
- [ ] 한국투자증권 API 연동
- [ ] 실거래 주문 모듈
- [ ] 리스크 관리 시스템

## 🚀 다른 앱으로 확장하기

### 1. 정책자금 앱 추가
```python
# mcp/tools/policy/ 폴더 생성
# crawler, document_generator 도구 추가
# 같은 방식으로 API 노출
```

### 2. 브랜드 관리 앱 추가
```python
# mcp/tools/brand/ 폴더 생성  
# design_analyzer, social_monitor 도구 추가
# 같은 방식으로 API 노출
```

**핵심: 한번 만든 MCP 도구는 모든 앱에서 재사용!**

## 🎯 핵심 이해 포인트

1. **MCP = 기능 모듈** (한번 만들면 계속 재사용)
2. **MCP-MAP = 조립 플랫폼** (모듈을 연결하는 허브)
3. **최소 비용 = MCP 재사용** (개발 비용 1/10)
4. **확장성 = 새 MCP 추가만** (기존 코드 수정 불필요)

## 📊 주요 기능

### 대시보드 (Vercel)
- ✅ 실시간 주식 현황
- ✅ 포트폴리오 구성 차트
- ✅ 수익률 추이 그래프
- ✅ AI 추천 종목 표시
- ✅ 모바일 반응형 디자인

### MCP 서버 (로컬)
- ✅ 실시간 주식 데이터 수집
- ✅ AI 기반 매매 신호 생성
- ✅ 자동 매매 실행
- ✅ 리스크 관리
- ✅ 백테스팅

## 🔗 관련 파일 위치

- **메인 경로**: `/Users/youareplan/mcp-map/`
- **백업 경로**: `/Users/youareplan/Desktop/mcp-map/`
- **GitHub**: https://github.com/youareplan-ceo/mcp-map
- **Vercel**: https://mcp-map.vercel.app

## 📝 작업 예시 코드

### MCP 도구 호출 예시
```python
# portfolio 도구로 골든크로스 찾기
from mcp.tools.portfolio.runner import run as portfolio_run

result = portfolio_run("batch_sma", {
    "tickers": ["005930.KS", "000660.KS"],  # 삼성전자, SK하이닉스
    "period": "3mo",
    "fast": 5,
    "slow": 20,
    "min_rsi": 40,
    "max_rsi": 70
})

# 골든크로스 종목만 추출
golden_stocks = [r for r in result["results"] 
                 if r.get("signal") == "golden_cross"]
```

### API 엔드포인트 추가 예시
```python
# mcp_bridge.py에 새 엔드포인트 추가
@app.post("/api/custom/strategy")
async def custom_strategy(request: dict):
    # 여러 MCP 도구 조합
    portfolio_result = portfolio_run(...)
    signals_result = signals_run(...)
    market_result = market_run(...)
    
    # 종합 분석
    return {
        "recommendation": "BUY" if ... else "HOLD",
        "confidence": 0.85,
        "details": {...}
    }
```

## 🎨 UI 커스터마이징

index.html 수정 시 주의사항:
1. localStorage 사용 (서버 없이도 작동)
2. MCP API 호출은 fetch로 처리
3. 실시간 업데이트는 setInterval 사용
4. 모바일 반응형 디자인 유지

## 🔧 트러블슈팅

### 서버 연결 안될 때
```bash
# 포트 확인
lsof -i :8000
lsof -i :8001

# 프로세스 종료
kill -9 [PID]

# 재시작
python stockpilot_complete_app.py
python mcp_bridge.py
```

### Vercel 배포 문제
```bash
# GitHub 강제 재배포
git commit --allow-empty -m "Redeploy"
git push origin main
```

### API 키 에러
```bash
# .env 파일 확인
cat .env

# 환경변수 직접 설정
export ANTHROPIC_API_KEY=sk-ant-...
```

## 📞 문의

CEO: ceo@youareplan.co.kr

---

**Made with ❤️ by YouArePlan**
**작성: 김실장 (Claude) - 2025.01.19**
**목적: 다음 Claude 세션에서도 프로젝트를 바로 이해하고 작업할 수 있도록**