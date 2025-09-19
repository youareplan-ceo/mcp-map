# 🚀 자동 배포 파이프라인 설정 가이드

## 📋 회장님이 직접 하실 작업 (10분)

### 1️⃣ Vercel 토큰 발급 (2분)

1. **Vercel 토큰 페이지 접속**
   - URL: https://vercel.com/account/tokens
   - 로그인 필요

2. **토큰 생성**
   - "Create Token" 버튼 클릭
   - 토큰 이름: `GitHub Actions`
   - Scope: Full Access 선택
   - "Create" 클릭

3. **토큰 복사**
   - ⚠️ 생성된 토큰을 안전한 곳에 복사 (한 번만 표시됨!)

---

### 2️⃣ Vercel 프로젝트 ID 확인 (2분)

1. **프로젝트 대시보드 접속**
   - URL: https://vercel.com/youareplans-projects
   - mcp-map 프로젝트 클릭

2. **Settings 탭 클릭**

3. **Project ID 확인**
   ```
   Project ID: prj_xxxxxxxxxxxxx (복사)
   ```

4. **Organization ID 확인**
   ```
   Team ID: team_xxxxxxxxxxxxx (복사)
   ```

---

### 3️⃣ GitHub Secrets 설정 (3분)

1. **GitHub 저장소 Settings 접속**
   - URL: https://github.com/youareplan-ceo/mcp-map/settings/secrets/actions

2. **New repository secret 클릭하여 추가**

   | Secret Name | Value |
   |------------|-------|
   | VERCEL_TOKEN | (1번에서 복사한 토큰) |
   | VERCEL_ORG_ID | (2번에서 복사한 Team ID) |
   | VERCEL_PROJECT_ID | (2번에서 복사한 Project ID) |

3. **각 Secret 저장**
   - Secret name 입력
   - Value 입력
   - "Add secret" 클릭

---

### 4️⃣ Vercel 환경변수 설정 (3분)

1. **Vercel 프로젝트 Settings → Environment Variables**
   - URL: https://vercel.com/youareplans-projects/mcp-map/settings/environment-variables

2. **환경변수 추가** (Add 버튼 클릭)

   | Key | Value | Environment |
   |-----|-------|------------|
   | OPENAI_API_KEY | sk-proj-실제키 | Production |
   | ANTHROPIC_API_KEY | sk-ant-실제키 | Production |
   | GEMINI_API_KEY | AIzaSy실제키 | Production |
   | LINEAR_API_KEY | lin_api_실제키 | Production |
   | GITHUB_TOKEN | ghp_실제키 | Production |
   | SLACK_WEBHOOK_URL | https://hooks.slack.com/... | Production |

3. **Save 클릭**

---

## ✅ 설정 완료 확인

### 테스트 배포 실행

1. **터미널에서 실행**
   ```bash
   cd /Users/youareplanconsulting/mcp-map-check
   git add .
   git commit -m "feat: add automatic deployment pipeline"
   git push origin main
   ```

2. **GitHub Actions 확인**
   - URL: https://github.com/youareplan-ceo/mcp-map/actions
   - 자동으로 워크플로우 시작됨

3. **배포 상태 확인**
   - ✅ Test 통과
   - ✅ Deploy-Production 진행
   - ✅ 배포 URL 생성

---

## 🎯 문제 해결 가이드

### ❌ "Error: Missing VERCEL_TOKEN"
→ GitHub Secrets에 VERCEL_TOKEN 추가 필요

### ❌ "Error: Project not found"
→ VERCEL_PROJECT_ID가 잘못됨. Vercel 대시보드에서 다시 확인

### ❌ "Error: Invalid token"
→ VERCEL_TOKEN이 만료됨. 새 토큰 발급 필요

### ❌ "Build failed"
→ vercel.json 설정 확인 또는 requirements.lock 파일 확인

---

## 📞 지원

문제가 발생하면:
1. GitHub Actions 로그 확인
2. Vercel 대시보드 로그 확인
3. 김실장(Claude)에게 에러 메시지 전달

---

## 🎉 완료!

설정이 완료되면:
- `git push origin main` → 자동 Production 배포
- Pull Request 생성 → 자동 Preview 배포
- 배포 완료 → GitHub 코멘트로 URL 알림
