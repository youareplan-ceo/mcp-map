#!/usr/bin/env python
"""
🔍 배포 전 체크 스크립트
회장님의 프로젝트가 배포 준비가 되었는지 확인합니다.
"""

import os
import sys
import json
from pathlib import Path

def check_mark(status):
    return "✅" if status else "❌"

def main():
    print("=" * 50)
    print("🔍 MCP-Map 배포 전 체크리스트")
    print("=" * 50)
    
    checks = {
        "필수 파일": [],
        "환경 설정": [],
        "보안": [],
        "배포 준비": []
    }
    
    # 1. 필수 파일 체크
    required_files = [
        ".github/workflows/vercel-deploy.yml",
        "vercel.json",
        ".gitignore",
        "requirements.lock"
    ]
    
    for file in required_files:
        exists = Path(file).exists()
        checks["필수 파일"].append({
            "항목": file,
            "상태": exists,
            "메시지": "파일 존재" if exists else f"파일 없음 - 생성 필요"
        })
    
    # 2. 환경 파일 체크
    env_files = [
        ".env",
        "config/.env"
    ]
    
    for file in env_files:
        exists = Path(file).exists()
        if exists:
            checks["보안"].append({
                "항목": file,
                "상태": False,
                "메시지": "⚠️ 실제 환경 파일 발견 - .gitignore 확인 필요!"
            })
    
    # 3. .gitignore 체크
    if Path(".gitignore").exists():
        with open(".gitignore", "r") as f:
            gitignore_content = f.read()
            
        important_ignores = [".env", "*.env", "config/.env"]
        for pattern in important_ignores:
            is_ignored = pattern in gitignore_content
            checks["보안"].append({
                "항목": f".gitignore에 {pattern}",
                "상태": is_ignored,
                "메시지": "포함됨" if is_ignored else "추가 필요"
            })
    
    # 4. vercel.json 체크
    if Path("vercel.json").exists():
        with open("vercel.json", "r") as f:
            try:
                vercel_config = json.load(f)
                has_env = "env" in vercel_config
                checks["배포 준비"].append({
                    "항목": "vercel.json 환경변수 설정",
                    "상태": has_env,
                    "메시지": "설정됨" if has_env else "env 섹션 추가 필요"
                })
                
                # API 키가 하드코딩되어 있는지 체크
                if has_env:
                    for key, value in vercel_config["env"].items():
                        if "API" in key or "TOKEN" in key:
                            is_safe = value.startswith("@")
                            checks["보안"].append({
                                "항목": f"{key} 보안",
                                "상태": is_safe,
                                "메시지": "안전 (참조)" if is_safe else "⚠️ 위험! 하드코딩됨"
                            })
            except json.JSONDecodeError:
                checks["배포 준비"].append({
                    "항목": "vercel.json 유효성",
                    "상태": False,
                    "메시지": "JSON 파싱 오류"
                })
    
    # 5. GitHub Actions 워크플로우 체크
    workflow_path = Path(".github/workflows/vercel-deploy.yml")
    if workflow_path.exists():
        with open(workflow_path, "r") as f:
            workflow_content = f.read()
            
        required_secrets = ["VERCEL_TOKEN", "VERCEL_ORG_ID", "VERCEL_PROJECT_ID"]
        for secret in required_secrets:
            is_used = secret in workflow_content
            checks["배포 준비"].append({
                "항목": f"GitHub Actions에서 {secret} 사용",
                "상태": is_used,
                "메시지": "설정됨" if is_used else "추가 필요"
            })
    
    # 결과 출력
    print("\n📋 체크 결과:\n")
    
    all_passed = True
    for category, items in checks.items():
        if items:
            print(f"\n【 {category} 】")
            for item in items:
                status_icon = check_mark(item["상태"])
                print(f"  {status_icon} {item['항목']}: {item['메시지']}")
                if not item["상태"]:
                    all_passed = False
    
    print("\n" + "=" * 50)
    
    if all_passed:
        print("🎉 모든 체크 통과! 배포 준비 완료!")
        print("\n다음 명령어로 배포하세요:")
        print("  bash scripts/deploy.sh")
    else:
        print("⚠️  일부 항목 확인 필요!")
        print("\n위의 ❌ 항목들을 먼저 해결하세요.")
        print("도움이 필요하면 SETUP_GUIDE.md를 참조하세요.")
    
    print("=" * 50)
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
