# Workstation README Update Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 남아 있는 개발 워크스테이션 과제 필수 항목을 로컬에서 실행하고 결과를 README에 재현 가능하게 정리한다.

**Architecture:** 기존 `Dockerfile`과 정적 웹 자산은 유지하고, Docker 실습 로그와 권한 실험 결과를 추가 수집한다. README는 체크리스트 중심 초안을 과제 제출용 기술 문서 형식으로 재구성한다.

**Tech Stack:** PowerShell, Git Bash, Docker Desktop, Ubuntu/Nginx 컨테이너, Markdown

---

### Task 1: Collect missing local evidence

**Files:**
- Use: `Dockerfile`
- Use: `app/index.html`

**Step 1: Verify Docker daemon and versions**

Run: `docker version`
Expected: client/server 버전이 모두 출력된다.

**Step 2: Capture Docker operations**

Run: `docker info`, `docker images`, `docker ps -a`, `docker logs ...`, `docker stats --no-stream ...`
Expected: 설치/운영 상태를 설명할 수 있는 출력이 확보된다.

**Step 3: Capture Linux permission exercise**

Run: `docker run --rm ubuntu bash -lc "... chmod ... ls ..."`
Expected: 파일/디렉터리 권한이 `600/700`에서 `644/755`로 바뀐 출력이 확보된다.

### Task 2: Verify container scenarios

**Files:**
- Use: `Dockerfile`
- Create: `bind-mount-site/index.html`

**Step 1: Run hello-world and Ubuntu labs**

Run: `docker run --name ws-hello hello-world`, `docker run -d --name ws-ubuntu ubuntu sleep infinity`, `docker exec ...`
Expected: 일회성 컨테이너와 장기 실행 컨테이너의 차이를 설명할 수 있다.

**Step 2: Run custom Nginx image**

Run: `docker build -t workstation-nginx:1.0 .`, `docker run -d --name ws-web -p 4000:80 workstation-nginx:1.0`
Expected: `localhost:4000`에서 HTML 응답을 확인한다.

**Step 3: Verify bind mount and volume persistence**

Run: `docker run -d -v ...`, `docker volume create ...`, `docker exec ...`
Expected: 호스트 수정이 즉시 반영되고, 컨테이너 삭제 후에도 볼륨 데이터가 유지된다.

### Task 3: Rewrite README for submission

**Files:**
- Modify: `README.md`

**Step 1: Replace checklist draft with submission-ready structure**

Include: 프로젝트 개요, 환경, 체크리스트, 검증 방법, 수행 로그, 트러블슈팅, Git 제한사항.

**Step 2: Reference existing screenshot and mask sensitive values**

Expected: 이미지 링크가 살아 있고 이메일/계정 정보는 마스킹된 형태로 기록된다.
