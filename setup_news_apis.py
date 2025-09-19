#!/usr/bin/env python3
"""
뉴스 API 설정 도우미 스크립트
NewsAPI.org 및 Reddit API 키 설정을 안내합니다.
"""

import os
from pathlib import Path

def create_env_file():
    """환경변수 파일 생성"""
    env_content = """# 뉴스 API 설정
# NewsAPI.org에서 무료 계정 생성 후 API 키 입력
NEWSAPI_KEY=your_newsapi_key_here

# Reddit API (선택사항 - read-only 접근용)
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_client_secret
"""

    with open('.env', 'w') as f:
        f.write(env_content)

    print("✅ .env 파일이 생성되었습니다.")

def show_setup_instructions():
    """API 설정 가이드 출력"""
    print("📰 뉴스 API 설정 가이드")
    print("=" * 50)

    print("\n🔑 NewsAPI.org 설정 (권장):")
    print("1. https://newsapi.org 방문")
    print("2. 무료 계정 생성 (이메일 인증)")
    print("3. API 키 복사")
    print("4. .env 파일에서 NEWSAPI_KEY=your_key 수정")
    print("5. 무료 플랜: 1,000 요청/일, 최신 뉴스만")

    print("\n🐾 Reddit API 설정 (선택사항):")
    print("1. https://reddit.com/prefs/apps 방문")
    print("2. 'Create App' 클릭")
    print("3. Script 타입 선택")
    print("4. client_id와 client_secret 복사")
    print("5. .env 파일에 설정")

    print("\n🌐 무료 소스 (API 키 불필요):")
    print("- Yahoo Finance 뉴스 스크래핑")
    print("- 네이버 금융 RSS")
    print("- 한경/매경 RSS 피드")

    print("\n💡 팁:")
    print("- API 키 없어도 기본 동작 가능")
    print("- 더미 감성 분석기 내장")
    print("- MCP news_analyzer 연동 지원")

def check_api_setup():
    """API 설정 상태 확인"""
    print("\n🔍 현재 API 설정 상태:")

    newsapi_key = os.getenv('NEWSAPI_KEY', '')
    reddit_client_id = os.getenv('REDDIT_CLIENT_ID', '')

    if newsapi_key and newsapi_key != 'your_newsapi_key_here':
        print("✅ NewsAPI 키 설정됨")
    else:
        print("❌ NewsAPI 키 미설정")

    if reddit_client_id and reddit_client_id != 'your_reddit_client_id':
        print("✅ Reddit API 설정됨")
    else:
        print("❌ Reddit API 미설정")

    # MCP 연동 확인
    mcp_path = Path('mcp/tools/news_analyzer/runner.py')
    if mcp_path.exists():
        print("✅ MCP news_analyzer 발견")
    else:
        print("⚠️ MCP news_analyzer 없음 (더미 분석기 사용)")

def main():
    print("🚀 뉴스 감성 수집기 설정")
    print("=" * 50)

    # .env 파일 생성
    if not Path('.env').exists():
        create_env_file()
    else:
        print("📝 .env 파일이 이미 존재합니다.")

    # 설정 가이드 출력
    show_setup_instructions()

    # 현재 상태 확인
    check_api_setup()

    print("\n" + "=" * 50)
    print("🏃‍♂️ 실행: python news_sentiment_collector.py")
    print("=" * 50)

if __name__ == "__main__":
    main()