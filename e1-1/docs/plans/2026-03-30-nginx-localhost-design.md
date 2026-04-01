# Nginx Localhost 4000 Design

**Goal:** `C:\Users\heejun_kim\Desktop\test1`에서 `nginx:latest` 기반 이미지를 빌드하고, 이미지 내부에 포함된 정적 파일을 `http://localhost:4000`으로 제공한다.

## Architecture

- 베이스 이미지는 `nginx:latest`를 사용한다.
- 정적 웹 자산은 프로젝트의 `app/` 디렉터리에 둔다.
- `Dockerfile`은 빌드 컨텍스트 기준 상대 경로인 `app/`을 사용해 컨테이너 내부 웹 루트인 `/usr/share/nginx/html/`로 복사한다.
- 컨테이너 내부 Nginx는 기본 포트 `80`을 사용하고, 실행 시 호스트 포트 `4000`을 `80`에 매핑한다.
- 별도 `nginx.conf`는 추가하지 않고 Nginx 기본 설정을 그대로 사용한다.

## Path Rules

- 호스트 절대 경로는 `Dockerfile`에 하드코딩하지 않는다.
- `Dockerfile` 소스 경로는 빌드 컨텍스트 기준 상대 경로로 유지한다.
- 컨테이너 내부 대상 경로는 절대 경로로 유지한다. 예: `/usr/share/nginx/html/`
- 이후 바인드 마운트가 필요하면 런타임 명령에서만 호스트 경로를 지정한다.

## Components

- `Dockerfile`
  - `nginx:latest` 기반 이미지 정의
  - 기본 웹 루트 정리
  - `app/` 복사
  - 포트 `80` 노출
- `app/index.html`
  - 이미지에 포함될 기본 정적 페이지

## Data Flow

1. 사용자가 `test1` 디렉터리에서 이미지를 빌드한다.
2. Docker는 `app/` 디렉터리의 정적 파일을 이미지에 포함한다.
3. 컨테이너 실행 시 Nginx가 `/usr/share/nginx/html/`의 파일을 서빙한다.
4. 사용자는 `http://localhost:4000`으로 접속한다.

## Error Handling

- `app/` 또는 `index.html`이 없으면 빌드 또는 실행 후 기대한 페이지가 보이지 않는다.
- 포트 `4000`이 이미 사용 중이면 컨테이너 실행이 실패한다.
- 마운트를 사용할 경우 대상 디렉터리에 파일이 없으면 기본 포함 파일이 가려질 수 있다.

## Verification

- 이번 작업은 설정 파일 생성이 중심이므로 단위 테스트 대신 빌드/실행 검증으로 확인한다.
- `docker build`가 성공해야 한다.
- `docker run -p 4000:80`으로 컨테이너가 떠야 한다.
- `http://localhost:4000` 요청이 `200 OK`와 생성한 HTML을 반환해야 한다.

