# 🚀 MCP-MAP 통합 시스템 사용법

## 시스템 실행 가이드

### 1️⃣ **시스템 전체 실행**
```bash
cd ~/Desktop/mcp-map
python launch_mcp_map.py
```
→ 모든 시스템이 자동으로 시작됩니다!

### 2️⃣ **API 엔드포인트 사용**

**실시간 주가 조회**
```bash
curl http://localhost:8002/api/price/AAPL
```

**기술적 분석**
```bash
curl http://localhost:8002/api/analysis/AAPL
```

**AI 추천 종목**
```bash
curl http://localhost:8002/api/recommend
```

### 3️⃣ **웹 대시보드 접속**
- 주식 대시보드: http://localhost:8501
- API 서버: http://localhost:8002

---

## 📊 현재 구축된 시스템

### 💼 **정책자금 시스템**
- 자동 공고 수집
- AI 매칭 분석
- 자동 신청서 작성
- 실시간 알림

### 📈 **주식 시스템 (StockPilot)**
- 실시간 주가 모니터링
- 기술적 분석 (RSI, MACD, 볼린저)
- AI 매매 신호
- 포트폴리오 최적화
- 자동매매 (시뮬레이션)

### 🤖 **AI 통합**
- OpenAI API 연동
- Anthropic API 연동
- 자율 에이전트 시스템

---

## 🔥 즉시 사용 가능한 명령어

### 주식 일일 분석
```bash
python mcp/run.py stocks_daily_research
```

### 정책자금 체크
```bash
python mcp/run.py policy_daily
```

### 포트폴리오 백테스팅
```bash
python scripts/performance_dashboard.py
```

### 특정 종목 분석
```bash
curl http://localhost:8002/api/analysis/AAPL
```

---

## 🎯 다음 단계 추천

1. **증권사 API 연동**
   - 한국투자증권 API
   - 실전 매매 연결

2. **알림 시스템 강화**
   - 텔레그램 봇
   - 카카오톡 알림

3. **AI 고도화**
   - 뉴스 센티먼트 분석
   - 재무제표 자동 분석

4. **리스크 관리**
   - 손절 자동화
   - 포지션 사이징

---

## 📱 모바일 접속

Vercel 배포 후:
```
https://mcp-map.vercel.app
```

언제 어디서나 시스템 모니터링 가능!

---

## 🆘 문제 해결

### 포트 충돌 시
```bash
# 사용 중인 포트 확인
lsof -i :8002
lsof -i :8501

# 프로세스 종료
kill -9 [PID]
```

### 패키지 설치 오류
```bash
# 가상환경 활성화
source venv/bin/activate

# 패키지 재설치
pip install -r requirements.txt
```

---

## 📞 지원

시스템 관련 모든 문의:
- GitHub Issues: https://github.com/youareplan-ceo/mcp-map/issues
- Email: contact@youareplan.com

---

**성공적인 비즈니스 자동화를 위해! 🚀**
