#!/bin/bash

# 🚀 빠른 Vercel 연결 스크립트
# 회장님을 위한 원클릭 Vercel 연결

echo "🎯 Vercel 프로젝트 연결 시작..."
echo "================================"

# Vercel CLI 설치 확인
if ! command -v vercel &> /dev/null; then
    echo "📦 Vercel CLI 설치 중..."
    npm install -g vercel
fi

# Vercel 로그인
echo "🔐 Vercel 로그인..."
vercel login

# 프로젝트 연결
echo "🔗 프로젝트 연결..."
vercel link

# 환경변수 가져오기
echo "📥 환경변수 동기화..."
vercel env pull

echo "✅ 완료!"
echo ""
echo "다음 단계:"
echo "1. GitHub에서 Secrets 설정 (SETUP_GUIDE.md 참조)"
echo "2. git push origin main 으로 자동 배포 테스트"
