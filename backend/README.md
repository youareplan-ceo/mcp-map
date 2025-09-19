# 🚀 StockPilot 실행 가이드

## 📱 StockPilot 백엔드 완성!

**"24시간 조용히 감시, 중요한 순간만 알림"**

---

## ✅ 구현된 기능

1. **포트폴리오 관리**
   - 종목 추가 (미국/한국)
   - 실시간 가치 계산
   - 수익률 표시

2. **24시간 자동 감시**
   - 5분마다 자동 체크
   - yfinance로 실시간 데이터

3. **AI 신호 생성**
   - RSI > 70: 매도 신호
   - RSI < 30: 매수 신호
   - MACD 골든크로스/데드크로스
   - 손절 신호 (-15%)

4. **중요한 순간만 알림**
   - 99% 시간: 조용
   - 1% 중요할 때만: 알림 생성

---

## 🏃‍♂️ 빠른 시작 (3단계)

### 1️⃣ 필요한 패키지 설치
```bash
cd /Users/youareplan/Desktop/mcp-map/backend
pip install fastapi uvicorn yfinance pandas numpy apscheduler
```

### 2️⃣ 서버 실행
```bash
python run_server.py
```

### 3️⃣ 웹 브라우저 열기
```
http://localhost:8000        # API 서버
http://localhost:8000/docs   # API 문서
web/stockpilot.html          # 웹 인터페이스
```

---

## 🧪 테스트 방법

### 방법 1: 테스트 스크립트
```bash
cd backend
python test_stockpilot.py
```

### 방법 2: 웹 인터페이스
1. `web/stockpilot.html` 파일 열기
2. "종목 추가" 탭에서 종목 등록
3. "포트폴리오" 탭에서 확인
4. "알림" 탭에서 신호 확인

### 방법 3: API 직접 호출
```bash
# 서버 상태
curl http://localhost:8000/

# 특정 종목 분석
curl http://localhost:8000/check/AAPL

# 강제 체크 실행
curl -X POST http://localhost:8000/force-check
```

---

## 📊 API 엔드포인트

| 메서드 | 경로 | 설명 |
|--------|------|------|
| GET | `/` | 서버 상태 |
| POST | `/users/create` | 사용자 생성 |
| POST | `/portfolio/add` | 종목 추가 |
| GET | `/portfolio/{user_id}` | 포트폴리오 조회 |
| GET | `/alerts/{user_id}` | 알림 조회 |
| GET | `/check/{ticker}` | 종목 즉시 분석 |
| POST | `/force-check` | 강제 체크 |

---

## 🎯 작동 방식

```
사용자 종목 등록
    ↓
5분마다 자동 체크
    ↓
기술적 지표 계산 (RSI, MACD)
    ↓
중요한 신호 감지 시
    ↓
알림 생성 (DB 저장)
    ↓
사용자 확인
```

---

## 📝 테스트 시나리오

### 시나리오 1: 매도 신호
1. RSI > 70인 종목 추가
2. 5분 대기 or 강제 체크
3. 알림 확인

### 시나리오 2: 매수 신호
1. RSI < 30인 종목 추가
2. 5분 대기 or 강제 체크
3. 알림 확인

---

## 🔧 문제 해결

### 서버가 시작 안 될 때
```bash
# 포트 확인
lsof -i :8000
# 프로세스 종료
kill -9 [PID]
```

### yfinance 오류
```bash
# 재설치
pip install --upgrade yfinance
```

### CORS 오류
- 이미 해결됨 (CORS 미들웨어 적용)

---

## 📈 다음 단계

1. **클라우드 배포**
   - Railway/Render 배포
   - PostgreSQL 연동

2. **알림 시스템**
   - 이메일 알림
   - 카카오톡 알림

3. **AI 고도화**
   - 뉴스 감성 분석
   - 패턴 학습

---

## 💡 핵심 철학

**"평소엔 조용, 중요할 때만 알림"**

- 99% 시간: 아무것도 안 함
- 1% 순간: 정확한 신호

---

회장님, 이제 실행만 하시면 됩니다! 🚀