#!/usr/bin/env python3
"""
StockPilot 고급 대시보드
- 설정 기능 (알림 임계치, 관심종목)
- 시뮬레이션 거래 로그
- 실시간 차트 및 분석
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import yfinance as yf
import requests
from datetime import datetime, timedelta
import time
import json
import os

# 페이지 설정
st.set_page_config(
    page_title="StockPilot Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 세션 상태 초기화
if 'watchlist' not in st.session_state:
    st.session_state.watchlist = ['AAPL', 'GOOGL', 'TSLA', '005930.KS', '035720.KS']
if 'simulation_logs' not in st.session_state:
    st.session_state.simulation_logs = []
if 'real_logs' not in st.session_state:
    st.session_state.real_logs = []
if 'alert_threshold' not in st.session_state:
    st.session_state.alert_threshold = {
        'price_change': 5.0,  # 5% 가격 변동
        'volume_spike': 200,   # 200% 거래량 증가
        'rsi_oversold': 30,
        'rsi_overbought': 70
    }
if 'show_settings' not in st.session_state:
    st.session_state.show_settings = False

# CSS 스타일
st.markdown("""
<style>
    .stButton > button {
        width: 100%;
        background-color: #4CAF50;
        color: white;
        font-weight: bold;
    }
    .sell-button > button {
        background-color: #f44336 !important;
    }
    .settings-button {
        position: fixed;
        top: 60px;
        right: 20px;
        z-index: 999;
    }
    .alert-box {
        padding: 10px;
        border-radius: 5px;
        margin: 10px 0;
    }
    .alert-danger {
        background-color: #ffebee;
        border-left: 4px solid #f44336;
    }
    .alert-success {
        background-color: #e8f5e9;
        border-left: 4px solid #4caf50;
    }
    .simulation-badge {
        background-color: #2196F3;
        color: white;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 12px;
    }
    .real-badge {
        background-color: #FF9800;
        color: white;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 12px;
    }
</style>
""", unsafe_allow_html=True)

# API 연결 함수
def get_stock_data(ticker):
    """API 서버에서 주식 데이터 가져오기"""
    try:
        response = requests.get(f"http://localhost:8002/api/price/{ticker}")
        return response.json()
    except:
        # 백업: yfinance 직접 사용
        stock = yf.Ticker(ticker)
        info = stock.info
        return {
            'ticker': ticker,
            'name': info.get('longName', ticker),
            'currentPrice': info.get('currentPrice', 0),
            'previousClose': info.get('previousClose', 0),
            'dayChange': 0,
            'dayChangePercent': 0
        }

def get_technical_analysis(ticker):
    """기술적 분석 데이터"""
    try:
        response = requests.get(f"http://localhost:8002/api/analysis/{ticker}")
        return response.json()
    except:
        return None

def add_simulation_log(action, ticker, quantity, price, reason="Manual"):
    """시뮬레이션 거래 로그 추가"""
    log = {
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'action': action,
        'ticker': ticker,
        'quantity': quantity,
        'price': price,
        'total': quantity * price,
        'reason': reason,
        'type': 'simulation'
    }
    st.session_state.simulation_logs.append(log)
    return log

# 헤더 및 설정 버튼
col1, col2, col3 = st.columns([2, 6, 1])
with col1:
    st.title("📈 StockPilot")
with col3:
    if st.button("⚙️ 설정", key="settings_btn"):
        st.session_state.show_settings = not st.session_state.show_settings

# 설정 모달
if st.session_state.show_settings:
    with st.container():
        st.markdown("### ⚙️ 대시보드 설정")
        
        tab1, tab2 = st.tabs(["알림 임계치", "관심종목"])
        
        with tab1:
            st.markdown("#### 알림 임계치 설정")
            col1, col2 = st.columns(2)
            with col1:
                price_change = st.number_input(
                    "가격 변동 알림 (%)", 
                    min_value=0.1, 
                    max_value=20.0,
                    value=st.session_state.alert_threshold['price_change'],
                    step=0.5
                )
                rsi_oversold = st.number_input(
                    "RSI 과매도", 
                    min_value=10, 
                    max_value=50,
                    value=st.session_state.alert_threshold['rsi_oversold']
                )
            with col2:
                volume_spike = st.number_input(
                    "거래량 급증 (%)", 
                    min_value=50, 
                    max_value=500,
                    value=st.session_state.alert_threshold['volume_spike'],
                    step=10
                )
                rsi_overbought = st.number_input(
                    "RSI 과매수", 
                    min_value=50, 
                    max_value=90,
                    value=st.session_state.alert_threshold['rsi_overbought']
                )
            
            if st.button("임계치 저장", type="primary"):
                st.session_state.alert_threshold = {
                    'price_change': price_change,
                    'volume_spike': volume_spike,
                    'rsi_oversold': rsi_oversold,
                    'rsi_overbought': rsi_overbought
                }
                st.success("✅ 알림 설정이 저장되었습니다!")
        
        with tab2:
            st.markdown("#### 관심종목 관리")
            
            # 현재 관심종목
            st.markdown("**현재 관심종목:**")
            for ticker in st.session_state.watchlist:
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.text(ticker)
                with col2:
                    if st.button("삭제", key=f"del_{ticker}"):
                        st.session_state.watchlist.remove(ticker)
                        st.rerun()
            
            # 새 종목 추가
            new_ticker = st.text_input("종목 코드 추가")
            if st.button("추가", type="primary"):
                if new_ticker and new_ticker not in st.session_state.watchlist:
                    st.session_state.watchlist.append(new_ticker.upper())
                    st.success(f"✅ {new_ticker.upper()} 추가됨!")
                    st.rerun()
        
        if st.button("설정 닫기"):
            st.session_state.show_settings = False
            st.rerun()

# 메인 탭
main_tabs = st.tabs(["📊 실시간", "📈 분석", "💰 포트폴리오", "📝 거래 기록", "🤖 AI 추천"])

# 1. 실시간 탭
with main_tabs[0]:
    st.markdown("### 실시간 시장 현황")
    
    # 관심종목 카드
    cols = st.columns(len(st.session_state.watchlist))
    for idx, ticker in enumerate(st.session_state.watchlist):
        with cols[idx]:
            data = get_stock_data(ticker)
            
            # 가격 정보
            st.metric(
                label=data.get('name', ticker)[:10],
                value=f"${data.get('currentPrice', 0):,.2f}",
                delta=f"{data.get('dayChangePercent', 0):.2f}%"
            )
            
            # 매수/매도 버튼
            col1, col2 = st.columns(2)
            with col1:
                if st.button("매수", key=f"buy_{ticker}"):
                    # 확인 모달 (시뮬레이션)
                    st.session_state[f'confirm_buy_{ticker}'] = True
            with col2:
                if st.button("매도", key=f"sell_{ticker}", help="매도"):
                    st.session_state[f'confirm_sell_{ticker}'] = True
            
            # 매수 확인 모달
            if st.session_state.get(f'confirm_buy_{ticker}', False):
                with st.container():
                    st.warning(f"**시뮬레이션 매수** - {ticker}")
                    qty = st.number_input(f"수량", min_value=1, value=10, key=f"qty_buy_{ticker}")
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("확인", key=f"confirm_yes_buy_{ticker}"):
                            log = add_simulation_log(
                                "BUY", ticker, qty, 
                                data.get('currentPrice', 0),
                                "Manual Order"
                            )
                            st.success(f"✅ 시뮬레이션 매수 기록: {qty}주 @ ${data.get('currentPrice', 0):.2f}")
                            st.session_state[f'confirm_buy_{ticker}'] = False
                            time.sleep(1)
                            st.rerun()
                    with col2:
                        if st.button("취소", key=f"confirm_no_buy_{ticker}"):
                            st.session_state[f'confirm_buy_{ticker}'] = False
                            st.rerun()
            
            # 매도 확인 모달
            if st.session_state.get(f'confirm_sell_{ticker}', False):
                with st.container():
                    st.error(f"**시뮬레이션 매도** - {ticker}")
                    qty = st.number_input(f"수량", min_value=1, value=10, key=f"qty_sell_{ticker}")
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("확인", key=f"confirm_yes_sell_{ticker}"):
                            log = add_simulation_log(
                                "SELL", ticker, qty,
                                data.get('currentPrice', 0),
                                "Manual Order"
                            )
                            st.error(f"✅ 시뮬레이션 매도 기록: {qty}주 @ ${data.get('currentPrice', 0):.2f}")
                            st.session_state[f'confirm_sell_{ticker}'] = False
                            time.sleep(1)
                            st.rerun()
                    with col2:
                        if st.button("취소", key=f"confirm_no_sell_{ticker}"):
                            st.session_state[f'confirm_sell_{ticker}'] = False
                            st.rerun()
    
    # 실시간 차트
    st.markdown("### 📊 실시간 차트")
    selected_ticker = st.selectbox("종목 선택", st.session_state.watchlist)
    
    if selected_ticker:
        stock = yf.Ticker(selected_ticker)
        hist = stock.history(period="1d", interval="5m")
        
        fig = go.Figure()
        fig.add_trace(go.Candlestick(
            x=hist.index,
            open=hist['Open'],
            high=hist['High'],
            low=hist['Low'],
            close=hist['Close'],
            name='가격'
        ))
        fig.update_layout(
            title=f"{selected_ticker} - 5분봉 차트",
            yaxis_title="가격",
            xaxis_title="시간",
            height=500
        )
        st.plotly_chart(fig, use_container_width=True)

# 2. 분석 탭
with main_tabs[1]:
    st.markdown("### 📈 기술적 분석")
    
    analysis_ticker = st.selectbox("분석 종목", st.session_state.watchlist, key="analysis")
    
    if analysis_ticker:
        analysis_data = get_technical_analysis(analysis_ticker)
        
        if analysis_data:
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("MA5", f"${analysis_data.get('ma5', 0):,.2f}")
                st.metric("MA20", f"${analysis_data.get('ma20', 0):,.2f}")
            
            with col2:
                rsi = analysis_data.get('rsi', 50)
                st.metric("RSI", f"{rsi:.1f}")
                if rsi > st.session_state.alert_threshold['rsi_overbought']:
                    st.markdown('<div class="alert-box alert-danger">⚠️ 과매수 신호</div>', unsafe_allow_html=True)
                elif rsi < st.session_state.alert_threshold['rsi_oversold']:
                    st.markdown('<div class="alert-box alert-success">✅ 과매도 신호</div>', unsafe_allow_html=True)
            
            with col3:
                st.metric("볼린저 상단", f"${analysis_data.get('bollingerUpper', 0):,.2f}")
                st.metric("볼린저 하단", f"${analysis_data.get('bollingerLower', 0):,.2f}")
            
            with col4:
                signal = analysis_data.get('signal', '중립')
                signal_color = "🟢" if signal == "매수" else "🔴" if signal == "매도" else "⚪"
                st.metric("신호", f"{signal_color} {signal}")
                
                # 자동 시뮬레이션 제안
                if signal == "매수":
                    if st.button("자동 매수 시뮬레이션", key="auto_buy"):
                        log = add_simulation_log(
                            "BUY", analysis_ticker, 10,
                            analysis_data.get('currentPrice', 0),
                            f"Auto Signal: {signal}"
                        )
                        st.success("✅ 자동 시뮬레이션 매수 실행!")
                elif signal == "매도":
                    if st.button("자동 매도 시뮬레이션", key="auto_sell"):
                        log = add_simulation_log(
                            "SELL", analysis_ticker, 10,
                            analysis_data.get('currentPrice', 0),
                            f"Auto Signal: {signal}"
                        )
                        st.success("✅ 자동 시뮬레이션 매도 실행!")

# 3. 포트폴리오 탭
with main_tabs[2]:
    st.markdown("### 💰 포트폴리오 현황")
    
    # 시뮬레이션 포트폴리오 계산
    portfolio = {}
    for log in st.session_state.simulation_logs:
        ticker = log['ticker']
        if ticker not in portfolio:
            portfolio[ticker] = {'quantity': 0, 'avg_price': 0}
        
        if log['action'] == 'BUY':
            # 평균 단가 계산
            total_value = portfolio[ticker]['quantity'] * portfolio[ticker]['avg_price']
            total_value += log['quantity'] * log['price']
            portfolio[ticker]['quantity'] += log['quantity']
            if portfolio[ticker]['quantity'] > 0:
                portfolio[ticker]['avg_price'] = total_value / portfolio[ticker]['quantity']
        else:  # SELL
            portfolio[ticker]['quantity'] -= log['quantity']
    
    # 포트폴리오 표시
    if portfolio:
        portfolio_data = []
        total_value = 0
        total_profit = 0
        
        for ticker, data in portfolio.items():
            if data['quantity'] > 0:
                current_price = get_stock_data(ticker).get('currentPrice', 0)
                current_value = data['quantity'] * current_price
                cost = data['quantity'] * data['avg_price']
                profit = current_value - cost
                profit_pct = (profit / cost * 100) if cost > 0 else 0
                
                portfolio_data.append({
                    '종목': ticker,
                    '보유수량': data['quantity'],
                    '평균단가': f"${data['avg_price']:.2f}",
                    '현재가': f"${current_price:.2f}",
                    '평가금액': f"${current_value:,.2f}",
                    '손익': f"${profit:+,.2f}",
                    '수익률': f"{profit_pct:+.2f}%"
                })
                
                total_value += current_value
                total_profit += profit
        
        if portfolio_data:
            st.dataframe(portfolio_data, use_container_width=True)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("총 평가액", f"${total_value:,.2f}")
            with col2:
                st.metric("총 손익", f"${total_profit:+,.2f}")
            with col3:
                profit_rate = (total_profit / (total_value - total_profit) * 100) if (total_value - total_profit) > 0 else 0
                st.metric("수익률", f"{profit_rate:+.2f}%")
    else:
        st.info("포트폴리오가 비어있습니다. 시뮬레이션 거래를 시작해보세요!")

# 4. 거래 기록 탭
with main_tabs[3]:
    st.markdown("### 📝 거래 기록")
    
    # 필터 옵션
    col1, col2 = st.columns([1, 3])
    with col1:
        filter_type = st.selectbox("거래 유형", ["전체", "시뮬레이션", "실거래"])
    
    # 거래 기록 표시
    if filter_type == "시뮬레이션" or filter_type == "전체":
        if st.session_state.simulation_logs:
            st.markdown("#### 🔵 시뮬레이션 거래")
            sim_df = pd.DataFrame(st.session_state.simulation_logs)
            sim_df = sim_df.sort_values('timestamp', ascending=False)
            
            # 컬럼 순서 조정
            columns_order = ['timestamp', 'action', 'ticker', 'quantity', 'price', 'total', 'reason']
            sim_df = sim_df[columns_order]
            
            # 스타일 적용
            def highlight_action(row):
                if row['action'] == 'BUY':
                    return ['background-color: #e8f5e9'] * len(row)
                else:
                    return ['background-color: #ffebee'] * len(row)
            
            styled_df = sim_df.style.apply(highlight_action, axis=1)
            st.dataframe(styled_df, use_container_width=True)
            
            # 통계
            col1, col2, col3 = st.columns(3)
            with col1:
                total_trades = len(sim_df)
                st.metric("총 거래 횟수", total_trades)
            with col2:
                buy_trades = len(sim_df[sim_df['action'] == 'BUY'])
                st.metric("매수 거래", buy_trades)
            with col3:
                sell_trades = len(sim_df[sim_df['action'] == 'SELL'])
                st.metric("매도 거래", sell_trades)
    
    if filter_type == "실거래" or filter_type == "전체":
        if st.session_state.real_logs:
            st.markdown("#### 🟠 실거래")
            real_df = pd.DataFrame(st.session_state.real_logs)
            st.dataframe(real_df, use_container_width=True)
        elif filter_type == "실거래":
            st.info("실거래 기록이 없습니다.")
    
    # CSV 다운로드
    if st.session_state.simulation_logs:
        if st.button("📥 거래 기록 다운로드"):
            df = pd.DataFrame(st.session_state.simulation_logs)
            csv = df.to_csv(index=False)
            st.download_button(
                label="CSV 다운로드",
                data=csv,
                file_name=f"trading_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )

# 5. AI 추천 탭
with main_tabs[4]:
    st.markdown("### 🤖 AI 추천")
    
    if st.button("AI 분석 실행", type="primary"):
        with st.spinner("AI가 분석 중입니다..."):
            try:
                response = requests.get("http://localhost:8002/api/recommend")
                recommendations = response.json().get('recommendations', [])
                
                if recommendations:
                    for rec in recommendations:
                        col1, col2, col3 = st.columns([2, 2, 1])
                        with col1:
                            st.markdown(f"**{rec['name']}** ({rec['ticker']})")
                            st.markdown(f"유형: {rec['type']}")
                            st.markdown(f"이유: {rec['reason']}")
                        with col2:
                            st.metric("현재가", f"${rec.get('currentPrice', 0):,.2f}")
                            st.metric("목표가", f"${rec.get('targetPrice', 0):,.2f}")
                        with col3:
                            confidence = rec.get('confidence', 50)
                            st.metric("신뢰도", f"{confidence}%")
                            
                            if st.button(f"시뮬레이션", key=f"ai_sim_{rec['ticker']}"):
                                log = add_simulation_log(
                                    "BUY", rec['ticker'], 10,
                                    rec.get('currentPrice', 0),
                                    f"AI Recommendation: {rec['reason']}"
                                )
                                st.success(f"✅ AI 추천 종목 시뮬레이션 매수!")
                        
                        st.divider()
                else:
                    st.info("현재 추천할 종목이 없습니다.")
            except Exception as e:
                st.error(f"AI 분석 중 오류 발생: {e}")

# 자동 새로고침
if st.checkbox("자동 새로고침 (10초)", value=False):
    time.sleep(10)
    st.rerun()

# 푸터
st.markdown("---")
st.markdown("📈 **StockPilot** - AI 기반 주식 분석 시스템 | 🔵 시뮬레이션 모드")
