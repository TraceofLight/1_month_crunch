# Compose Bonus Design

## 목표

보너스 과제의 Compose 관련 항목을 기존 Nginx 실습 저장소에 최소 변경으로 추가한다.

## 선택한 접근

`docker-compose.yml` 하나에 `profiles`를 사용한다.

- `single` 프로필: 기존 `Dockerfile`을 빌드하는 단일 웹 서비스
- `multi` 프로필: `web`, `echo`, `probe` 3개 서비스
- `.env` 파일: 호스트 포트와 echo 메시지를 환경 변수로 주입

## 이유

- 단일 서비스와 멀티 컨테이너 실습을 한 파일에서 관리할 수 있다.
- `docker compose up/down/ps/logs` 명령을 같은 파일 기준으로 문서화하기 쉽다.
- `probe` 컨테이너를 두면 서비스 디스커버리 검증을 `docker compose exec probe curl ...` 형태로 바로 남길 수 있다.

## 서비스 구성

- `web`
  - 기존 `Dockerfile` 빌드
  - `WEB_PORT` 환경 변수로 호스트 포트를 변경
- `echo`
  - `hashicorp/http-echo` 이미지
  - `API_MESSAGE` 환경 변수로 응답 문구 변경
- `probe`
  - `curlimages/curl` 이미지
  - 내부 네트워크에서 `web`, `echo`에 curl 수행

## 검증 계획

1. `docker compose config`로 구성 검증
2. `--profile single up -d` 후 브라우저/HTTP 응답 확인
3. `--profile multi up -d` 후 `ps`, `logs`, `exec probe curl ...`로 네트워크 확인
4. `down`으로 종료 확인

## 문서 반영

- README의 Bonus 체크리스트 갱신
- `### 13`~`### 16` 섹션에 Compose/환경 변수 로그 추가
- `### 12`의 GitHub 로그인 항목은 기존 `github_login.png`를 연결
