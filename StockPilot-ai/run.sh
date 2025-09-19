#!/bin/bash

# StockPilot-AI 실행 스크립트

echo "╔══════════════════════════════════════════════════════════╗"
echo "║                 🚀 StockPilot-AI 시작                     ║"
echo "╚══════════════════════════════════════════════════════════╝"

# 1. API 서버 시작
echo "📈 API 서버 시작..."
python price_api.py &
API_PID=$!

sleep 2

# 2. 대시보드 시작
echo "📊 대시보드 시작..."
streamlit run dashboard.py --server.port 8501 --server.headless true &
DASH_PID=$!

echo ""
echo "✅ 시스템 시작 완료!"
echo "📑 API: http://localhost:8002"
echo "📑 대시보드: http://localhost:8501"
echo ""
echo "종료: Ctrl+C"

# 종료 시 프로세스 정리
trap "kill $API_PID $DASH_PID 2>/dev/null" EXIT

# 대기
wait