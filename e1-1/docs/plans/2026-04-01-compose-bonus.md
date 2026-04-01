# Compose Bonus Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** `docker-compose.yml`과 환경 변수 구성을 추가해 보너스 Compose 과제를 실행하고 README에 결과를 반영한다.

**Architecture:** 하나의 Compose 파일에서 `single`과 `multi` 프로필을 나눠 관리한다. `single`은 기존 Nginx 이미지를 빌드해 단일 서비스로 실행하고, `multi`는 `web + echo + probe` 조합으로 서비스 디스커버리와 운영 명령을 검증한다.

**Tech Stack:** Docker Compose v2, Nginx, hashicorp/http-echo, curlimages/curl, Markdown

---

### Task 1: Add Compose configuration

**Files:**
- Create: `docker-compose.yml`
- Create: `.env`

**Step 1: Add compose profiles**

Create services for `web`, `echo`, `probe`.

**Step 2: Validate configuration**

Run: `docker compose config`
Expected: merged compose config prints without errors.

### Task 2: Execute bonus scenarios

**Files:**
- Use: `docker-compose.yml`

**Step 1: Verify single-service compose**

Run: `docker compose --profile single up -d`
Expected: web service starts and serves HTTP on `${WEB_PORT}`.

**Step 2: Verify multi-container compose**

Run: `docker compose --profile multi up -d`
Expected: `web`, `echo`, `probe` are all up.

**Step 3: Verify service discovery**

Run: `docker compose --profile multi exec probe curl -s http://echo:5678`
Expected: `${API_MESSAGE}` is returned.

**Step 4: Capture operations**

Run: `docker compose ps`, `docker compose logs`, `docker compose down`
Expected: outputs are available for README.

### Task 3: Update README bonus sections

**Files:**
- Modify: `README.md`

**Step 1: Update checklist statuses**

Mark executed bonus items as complete and SSH as excluded.

**Step 2: Fill sections 13-16**

Add compose structure, commands, outputs, and environment variable usage logs.
