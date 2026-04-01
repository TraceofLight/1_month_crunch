# Nginx Localhost 4000 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** `test1` 디렉터리에 `nginx:latest` 기반 Docker 이미지를 위한 `Dockerfile`과 정적 웹 자산을 추가해 `http://localhost:4000`으로 접속 가능하게 만든다.

**Architecture:** `app/` 디렉터리의 정적 파일을 `Dockerfile`에서 `/usr/share/nginx/html/`로 복사한다. Nginx 기본 설정을 유지하고, 컨테이너 내부는 `80`, 호스트는 `4000`을 사용한다. 이후 바인드 마운트가 필요하면 동일한 컨테이너 경로를 덮어쓸 수 있게 설계한다.

**Tech Stack:** Docker, Nginx `latest`, 정적 HTML

---

### Task 1: Create bundled static content

**Files:**
- Create: `app/index.html`

**Step 1: Add the initial landing page**

작성 내용:

```html
<!DOCTYPE html>
<html lang="ko">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Nginx on localhost:4000</title>
  </head>
  <body>
    <main>
      <h1>Nginx is running</h1>
      <p>Served from the Docker image.</p>
    </main>
  </body>
</html>
```

**Step 2: Verify file exists**

Run: `Get-ChildItem .\app`
Expected: `index.html`이 보인다.

### Task 2: Create the Docker image definition

**Files:**
- Create: `Dockerfile`

**Step 1: Write the Dockerfile**

작성 내용:

```dockerfile
FROM nginx:latest

RUN rm -rf /usr/share/nginx/html/*

COPY app/ /usr/share/nginx/html/

EXPOSE 80
```

**Step 2: Verify file contents**

Run: `Get-Content .\Dockerfile`
Expected: `COPY app/ /usr/share/nginx/html/`가 포함된다.

### Task 3: Verify the image works locally

**Files:**
- Use: `Dockerfile`
- Use: `app/index.html`

**Step 1: Build the image**

Run: `docker build -t test1-nginx .`
Expected: 성공적으로 이미지가 생성된다.

**Step 2: Run the container**

Run: `docker run -d --rm --name test1-nginx -p 4000:80 test1-nginx`
Expected: 컨테이너 ID가 출력된다.

**Step 3: Verify HTTP response**

Run: `Invoke-WebRequest http://localhost:4000 | Select-Object -ExpandProperty Content`
Expected: `Nginx is running`과 `Served from the Docker image.`가 포함된다.

**Step 4: Stop the container**

Run: `docker stop test1-nginx`
Expected: `test1-nginx`가 출력된다.

### Task 4: Document optional bind mount usage

**Files:**
- Modify: `README.md`

**Step 1: Add build and run examples**

추가 내용:

```powershell
docker build -t test1-nginx .
docker run -d --rm --name test1-nginx -p 4000:80 test1-nginx
docker run -d --rm --name test1-nginx -p 4000:80 -v "${PWD}\\app:/usr/share/nginx/html:ro" test1-nginx
```

**Step 2: Verify README mentions optional mount**

Run: `Select-String -Path .\README.md -Pattern 'test1-nginx'`
Expected: 빌드/실행 예시가 검색된다.

**Step 3: Commit**

Skip: 현재 디렉터리는 Git 저장소가 아니므로 커밋 단계는 수행하지 않는다.

