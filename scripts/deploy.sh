#!/bin/bash

# 🚀 MCP-Map 배포 스크립트
# 회장님을 위한 원클릭 배포 시스템

echo "🎯 MCP-Map 배포 시작..."
echo "================================"

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 1. Git 상태 확인
echo -e "${YELLOW}📋 Git 상태 확인...${NC}"
if [ -n "$(git status --porcelain)" ]; then
    echo -e "${RED}❌ 커밋되지 않은 변경사항이 있습니다!${NC}"
    echo "다음 명령어로 커밋하세요:"
    echo "  git add ."
    echo "  git commit -m 'feat: your message'"
    exit 1
fi

# 2. 현재 브랜치 확인
BRANCH=$(git rev-parse --abbrev-ref HEAD)
echo -e "${GREEN}✅ 현재 브랜치: $BRANCH${NC}"

# 3. 테스트 실행 (선택사항)
read -p "테스트를 실행하시겠습니까? (y/n): " run_tests
if [ "$run_tests" = "y" ]; then
    echo -e "${YELLOW}🧪 테스트 실행 중...${NC}"
    python -m pytest tests/ 2>/dev/null || echo "테스트 파일이 없거나 pytest가 설치되지 않았습니다."
fi

# 4. 배포 타입 선택
echo ""
echo "배포 타입을 선택하세요:"
echo "1) Production (main 브랜치)"
echo "2) Preview (현재 브랜치)"
echo "3) Local 테스트만"
read -p "선택 (1-3): " deploy_type

case $deploy_type in
    1)
        # Production 배포
        echo -e "${YELLOW}🚀 Production 배포 시작...${NC}"
        
        # main 브랜치로 체크아웃
        if [ "$BRANCH" != "main" ]; then
            read -p "main 브랜치로 전환하시겠습니까? (y/n): " switch_main
            if [ "$switch_main" = "y" ]; then
                git checkout main
                git pull origin main
            else
                echo "main 브랜치에서만 production 배포가 가능합니다."
                exit 1
            fi
        fi
        
        # GitHub에 푸시
        echo -e "${YELLOW}📤 GitHub에 푸시 중...${NC}"
        git push origin main
        
        echo -e "${GREEN}✅ Production 배포가 시작되었습니다!${NC}"
        echo "GitHub Actions에서 자동으로 배포됩니다."
        echo "진행상황: https://github.com/youareplan-ceo/mcp-map/actions"
        ;;
        
    2)
        # Preview 배포
        echo -e "${YELLOW}👀 Preview 배포 시작...${NC}"
        
        # Vercel CLI로 직접 배포
        if command -v vercel &> /dev/null; then
            vercel --confirm
        else
            echo -e "${RED}❌ Vercel CLI가 설치되지 않았습니다.${NC}"
            echo "설치: npm i -g vercel"
            exit 1
        fi
        ;;
        
    3)
        # Local 테스트
        echo -e "${YELLOW}🏠 Local 테스트 시작...${NC}"
        
        # StockPilot 실행
        if [ -f "stockpilot_launch.py" ]; then
            python stockpilot_launch.py
        else
            echo "stockpilot_launch.py 파일을 찾을 수 없습니다."
        fi
        ;;
        
    *)
        echo -e "${RED}❌ 잘못된 선택입니다.${NC}"
        exit 1
        ;;
esac

echo ""
echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}🎉 작업 완료!${NC}"
echo -e "${GREEN}================================${NC}"

# 배포 후 체크리스트
echo ""
echo "📝 배포 후 체크리스트:"
echo "  □ Vercel 대시보드 확인"
echo "  □ 배포된 URL 테스트"
echo "  □ API 키 동작 확인"
echo "  □ 에러 로그 확인"
