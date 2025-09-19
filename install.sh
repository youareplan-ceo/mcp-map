#!/bin/bash

# MCP-MAP 시스템 설치 스크립트
# 회장님을 위한 원클릭 설치

echo "╔══════════════════════════════════════════════════════════╗"
echo "║                 🚀 MCP-MAP 시스템 설치                    ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

# 1. Python 버전 확인
echo "📌 Python 버전 확인..."
python_version=$(python3 --version 2>&1 | grep -oE '[0-9]+\.[0-9]+')
echo "   현재 버전: Python $python_version"

if [ $(echo "$python_version < 3.9" | bc) -eq 1 ]; then
    echo "   ⚠️  Python 3.9 이상이 필요합니다!"
    echo "   brew install python@3.11 실행해주세요"
    exit 1
fi

# 2. 가상환경 생성
echo ""
echo "📦 가상환경 생성..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "   ✅ 가상환경 생성 완료"
else
    echo "   ✅ 기존 가상환경 사용"
fi

# 3. 가상환경 활성화
echo ""
echo "🔧 가상환경 활성화..."
source venv/bin/activate
echo "   ✅ 활성화 완료"

# 4. pip 업그레이드
echo ""
echo "📥 pip 업그레이드..."
pip install --upgrade pip -q
echo "   ✅ pip 최신 버전"

# 5. 필수 패키지 설치
echo ""
echo "📚 필수 패키지 설치 중... (2-3분 소요)"
pip install -r requirements.txt -q

# 6. 디렉토리 권한 설정
echo ""
echo "🔐 권한 설정..."
chmod +x launch_mcp_map.py
chmod +x mcp/run.py
echo "   ✅ 실행 권한 설정 완료"

# 7. 환경변수 파일 생성
echo ""
echo "🔑 환경변수 설정..."
if [ ! -f ".env" ]; then
    cat > .env << EOF
# MCP-MAP 환경변수

# API Keys
OPENAI_API_KEY=your-openai-key
ANTHROPIC_API_KEY=your-anthropic-key
BRAVE_API_KEY=your-brave-key

# Database
DB_HOST=localhost
DB_PORT=5432
DB_NAME=mcp_map
DB_USER=postgres
DB_PASSWORD=mcp123

# Stock API (선택)
KIS_APP_KEY=your-kis-app-key
KIS_APP_SECRET=your-kis-secret

# Notification (선택)
TELEGRAM_BOT_TOKEN=your-telegram-token
TELEGRAM_CHAT_ID=your-chat-id

# Server
API_HOST=0.0.0.0
API_PORT=8002
DASHBOARD_PORT=8501
EOF
    echo "   ✅ .env 파일 생성 완료"
    echo "   ⚠️  .env 파일에 API 키를 입력해주세요!"
else
    echo "   ✅ 기존 .env 파일 유지"
fi

# 8. 데이터 디렉토리 생성
echo ""
echo "📁 데이터 디렉토리 생성..."
mkdir -p data/stocks
mkdir -p data/policies
mkdir -p logs
mkdir -p tmp
echo "   ✅ 디렉토리 생성 완료"

# 9. 완료
echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║                   ✨ 설치 완료!                          ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""
echo "🚀 실행 방법:"
echo "   python launch_mcp_map.py"
echo ""
echo "📝 다음 단계:"
echo "   1. .env 파일에 API 키 입력"
echo "   2. python launch_mcp_map.py 실행"
echo ""
echo "💡 도움말:"
echo "   cat QUICKSTART.md"
echo ""
