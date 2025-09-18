"""
StockPilot 온라인 배포 가이드
로컬 → 온라인 전환 스크립트
"""

import os
import json
from pathlib import Path

def create_streamlit_app():
    """Streamlit 앱 생성 (가장 쉬운 배포)"""
    
    streamlit_code = '''
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import sqlite3
import json
from datetime import datetime, timedelta

# 페이지 설정
st.set_page_config(
    page_title="StockPilot AI Trading System",
    page_icon="📈",
    layout="wide"
)

# 제목
st.title("📈 StockPilot AI 자동매매 시스템")
st.markdown("### 실시간 수익 극대화 대시보드")

# 사이드바
with st.sidebar:
    st.header("⚙️ 설정")
    
    # 새로고침 간격
    refresh_interval = st.selectbox(
        "새로고침 간격",
        ["5초", "10초", "30초", "1분", "5분"],
        index=2
    )
    
    # 자동 새로고침
    if st.button("🔄 수동 새로고침"):
        st.experimental_rerun()
    
    st.markdown("---")
    st.info("""
    💡 **사용법**
    1. 실시간 데이터 확인
    2. AI 시그널 모니터링
    3. 수익률 추적
    """)

# 메인 레이아웃
col1, col2, col3, col4 = st.columns(4)

# KPI 카드
with col1:
    st.metric(
        label="오늘 수익률",
        value="+3.45%",
        delta="0.23%"
    )

with col2:
    st.metric(
        label="승률",
        value="73.2%",
        delta="2.1%"
    )

with col3:
    st.metric(
        label="거래 횟수",
        value="45",
        delta="12"
    )

with col4:
    st.metric(
        label="AI 평균점수",
        value="86.3",
        delta="3.2"
    )

st.markdown("---")

# 탭
tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 실시간 현황", "📈 차트", "📰 뉴스", "🤖 AI 시그널", "⚙️ 설정"])

with tab1:
    # 실시간 포트폴리오
    st.subheader("💼 현재 포트폴리오")
    
    # 더미 데이터
    portfolio_data = {
        "종목": ["NVDA", "AAPL", "TSLA", "GOOGL", "MSFT"],
        "보유수량": [10, 20, 5, 15, 25],
        "평균단가": [520.0, 150.0, 245.0, 140.0, 380.0],
        "현재가": [535.0, 155.0, 240.0, 142.0, 385.0],
        "수익률(%)": [2.88, 3.33, -2.04, 1.43, 1.32],
        "AI점수": [92, 85, 73, 88, 86]
    }
    
    df = pd.DataFrame(portfolio_data)
    
    # 색상 적용
    def color_profit(val):
        color = 'green' if val > 0 else 'red'
        return f'color: {color}'
    
    styled_df = df.style.applymap(color_profit, subset=['수익률(%)'])
    st.dataframe(styled_df)
    
    # 최근 거래
    st.subheader("📝 최근 거래 내역")
    trades_data = {
        "시간": ["14:32", "14:15", "13:48", "13:20", "12:55"],
        "종목": ["NVDA", "TSLA", "AAPL", "GOOGL", "MSFT"],
        "매매": ["매수", "매도", "매수", "매수", "매도"],
        "수량": [5, 3, 10, 8, 5],
        "가격": [535, 245, 153, 141, 382],
        "사유": ["AI_SIGNAL", "TAKE_PROFIT", "AI_SIGNAL", "NEWS_POSITIVE", "STOP_LOSS"]
    }
    
    trades_df = pd.DataFrame(trades_data)
    st.dataframe(trades_df)

with tab2:
    # 수익률 차트
    st.subheader("📈 실시간 수익률 차트")
    
    # 시간별 수익률 데이터 (더미)
    hours = list(range(9, 16))
    profits = [0, 0.5, 1.2, 0.8, 2.1, 3.2, 3.45]
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=hours,
        y=profits,
        mode='lines+markers',
        name='수익률(%)',
        line=dict(color='green', width=2),
        fill='tozeroy'
    ))
    
    fig.update_layout(
        title="일중 수익률 추이",
        xaxis_title="시간",
        yaxis_title="수익률(%)",
        showlegend=True,
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # 종목별 수익 기여도
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🥇 수익 TOP 5")
        top_stocks = {
            "종목": ["NVDA", "AAPL", "AMD", "GOOGL", "META"],
            "수익": ["+$523", "+$312", "+$245", "+$189", "+$156"]
        }
        st.table(pd.DataFrame(top_stocks))
    
    with col2:
        st.subheader("📉 손실 TOP 5")
        loss_stocks = {
            "종목": ["TSLA", "COIN", "RIOT", "SQ", "PYPL"],
            "손실": ["-$234", "-$123", "-$98", "-$67", "-$45"]
        }
        st.table(pd.DataFrame(loss_stocks))

with tab3:
    # 뉴스 분석
    st.subheader("📰 실시간 뉴스 감성 분석")
    
    news_data = {
        "시간": ["14:35", "14:20", "13:45"],
        "종목": ["NVDA", "TSLA", "AAPL"],
        "헤드라인": [
            "엔비디아 신규 AI칩 공개, 성능 3배 향상",
            "테슬라 대규모 리콜 발표",
            "애플 아이폰 판매 호조"
        ],
        "감성점수": [85, -72, 62],
        "영향도": ["+3-5%", "-2-3%", "+1-2%"]
    }
    
    news_df = pd.DataFrame(news_data)
    
    # 감성점수 색상
    def sentiment_color(val):
        if val > 30:
            return 'background-color: lightgreen'
        elif val < -30:
            return 'background-color: lightcoral'
        else:
            return 'background-color: lightyellow'
    
    styled_news = news_df.style.applymap(sentiment_color, subset=['감성점수'])
    st.dataframe(styled_news)
    
    # 시장 전체 분위기
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("전체 감성", "+23.4", "긍정적")
    with col2:
        st.metric("강세 종목", "18", "+3")
    with col3:
        st.metric("약세 종목", "7", "-2")

with tab4:
    # AI 시그널
    st.subheader("🤖 AI 매매 시그널")
    
    signals = {
        "종목": ["NVDA", "AMD", "GOOGL", "MSFT", "AAPL"],
        "AI점수": [95, 91, 87, 85, 82],
        "기술점수": [88, 85, 82, 80, 78],
        "뉴스점수": [92, 88, 85, 83, 80],
        "시그널": ["강력매수", "강력매수", "매수", "매수", "보유"],
        "추천액션": ["20% 매수", "15% 매수", "10% 매수", "10% 매수", "홀드"]
    }
    
    signals_df = pd.DataFrame(signals)
    
    # AI점수 색상
    def ai_score_color(val):
        if val >= 90:
            return 'background-color: darkgreen; color: white'
        elif val >= 80:
            return 'background-color: lightgreen'
        elif val >= 70:
            return 'background-color: yellow'
        else:
            return 'background-color: lightcoral'
    
    styled_signals = signals_df.style.applymap(ai_score_color, subset=['AI점수'])
    st.dataframe(styled_signals)
    
    # 전략 성과
    st.subheader("📊 전략별 성과")
    strategy_cols = st.columns(3)
    
    with strategy_cols[0]:
        st.info("""
        **보수적 전략 (AI 90+)**
        - 승률: 85%
        - 수익: +2.3%
        - 거래: 12건
        """)
    
    with strategy_cols[1]:
        st.success("""
        **균형 전략 (AI 85+)**
        - 승률: 72%
        - 수익: +3.8%
        - 거래: 28건
        """)
    
    with strategy_cols[2]:
        st.warning("""
        **공격적 전략 (AI 80+)**
        - 승률: 61%
        - 수익: +2.1%
        - 거래: 45건
        """)

with tab5:
    st.subheader("⚙️ 시스템 설정")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.number_input("초기 자금 (원)", value=10000000, step=1000000)
        st.slider("AI 점수 임계값", 70, 95, 85)
        st.slider("손절 기준 (%)", -10, -3, -5)
        st.slider("익절 기준 (%)", 5, 20, 15)
    
    with col2:
        st.selectbox("거래 전략", ["보수적", "균형", "공격적"])
        st.number_input("최대 보유 종목", 1, 20, 10)
        st.number_input("종목당 최대 비중 (%)", 5, 50, 30)
        st.checkbox("뉴스 감성 분석 사용", value=True)
    
    if st.button("💾 설정 저장", type="primary"):
        st.success("설정이 저장되었습니다!")

# 푸터
st.markdown("---")
st.caption("🚀 StockPilot AI Trading System v2.0 | 실시간 업데이트 중...")

# 자동 새로고침 (JavaScript)
if refresh_interval == "5초":
    st.markdown(
        """
        <script>
        setTimeout(function(){
            window.location.reload();
        }, 5000);
        </script>
        """,
        unsafe_allow_html=True
    )
'''
    
    # 파일 저장
    with open("streamlit_app.py", "w", encoding="utf-8") as f:
        f.write(streamlit_code)
    
    print("✅ streamlit_app.py 생성 완료")
    print("\n📱 온라인 배포 방법:")
    print("1. GitHub에 코드 업로드")
    print("2. share.streamlit.io 접속")
    print("3. GitHub 리포지토리 연결")
    print("4. 자동 배포 → 온라인 URL 생성!")
    
    return "streamlit_app.py"

def create_heroku_files():
    """Heroku 배포 파일 생성"""
    
    # Procfile
    procfile = "web: python performance_dashboard.py"
    with open("Procfile", "w") as f:
        f.write(procfile)
    
    # runtime.txt
    runtime = "python-3.11.0"
    with open("runtime.txt", "w") as f:
        f.write(runtime)
    
    # app.json
    app_config = {
        "name": "StockPilot AI Trading",
        "description": "AI-powered stock trading system",
        "repository": "https://github.com/youareplan-ceo/mcp-map",
        "keywords": ["python", "trading", "ai", "stocks"],
        "buildpacks": [
            {
                "url": "heroku/python"
            }
        ]
    }
    
    with open("app.json", "w", encoding="utf-8") as f:
        json.dump(app_config, f, indent=2)
    
    print("✅ Heroku 배포 파일 생성 완료")
    print("\n☁️ Heroku 배포 방법:")
    print("1. heroku create stockpilot-app")
    print("2. git push heroku main")
    print("3. heroku open")

def create_docker_compose():
    """Docker Compose 파일 생성 (자체 서버용)"""
    
    docker_compose = '''version: '3.8'

services:
  web:
    build: .
    ports:
      - "80:8000"
      - "8001:8001"
      - "9999:9999"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/stockpilot
    depends_on:
      - db
      - redis
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    restart: unless-stopped

  db:
    image: postgres:14
    environment:
      - POSTGRES_USER=stockpilot
      - POSTGRES_PASSWORD=secure_password
      - POSTGRES_DB=stockpilot
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7
    ports:
      - "6379:6379"
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data

  nginx:
    image: nginx:alpine
    ports:
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - web

volumes:
  postgres_data:
  redis_data:
'''
    
    with open("docker-compose.yml", "w") as f:
        f.write(docker_compose)
    
    # Dockerfile
    dockerfile = '''FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8000 8001 9999

CMD ["python", "stockpilot_master.py"]
'''
    
    with open("Dockerfile", "w") as f:
        f.write(dockerfile)
    
    print("✅ Docker 파일 생성 완료")
    print("\n🐳 Docker 배포 방법:")
    print("1. docker-compose build")
    print("2. docker-compose up -d")
    print("3. 브라우저: https://your-domain.com")

def main():
    """메인 실행"""
    print("""
    ╔══════════════════════════════════════════╗
    ║     StockPilot 온라인 배포 준비         ║
    ╚══════════════════════════════════════════╝
    """)
    
    print("\n배포 옵션 선택:")
    print("1. Streamlit Cloud (가장 쉬움, 무료)")
    print("2. Heroku (중급, 무료 티어)")
    print("3. Docker (자체 서버용)")
    print("4. 모든 파일 생성")
    
    choice = input("\n선택 (1-4): ")
    
    if choice == "1" or choice == "4":
        create_streamlit_app()
    
    if choice == "2" or choice == "4":
        create_heroku_files()
    
    if choice == "3" or choice == "4":
        create_docker_compose()
    
    print("\n" + "="*50)
    print("✅ 온라인 배포 준비 완료!")
    print("="*50)
    
    print("\n🌐 추천 배포 순서:")
    print("1. Streamlit Cloud로 먼저 테스트")
    print("2. 안정화 후 Heroku 배포")
    print("3. 수익 발생하면 전용 서버 구축")

if __name__ == "__main__":
    main()
