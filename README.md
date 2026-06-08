# 인증과 연관관계로 완성하는 FastAPI 웹 서비스

프로젝트 작업 관리 서비스는 로그인한 사용자가 프로젝트를 만들고, 프로젝트에 속한 작업을 등록한 뒤, 작업 상태를 진행 전에서 완료로 변경하는 SSR 웹 애플리케이션이다. 공개 화면과 보호 화면을 분리하고, FastAPI의 `Depends`로 현재 로그인 사용자를 확인한다. 핵심 데이터는 SQLAlchemy ORM과 SQLite에 저장된다.

## 실행 환경

| 항목 | 버전 |
| --- | --- |
| Python | 3.12.3, Dockerfile의 `ubuntu:24.04` 기준 |
| FastAPI | 0.115.6 |
| Uvicorn | 0.34.0 |
| SQLAlchemy | 2.0.36 |
| Jinja2 | 3.1.4 |
| python-multipart | 0.0.20 |
| itsdangerous | 2.2.0 |

직접 의존성은 `requirements.txt`에 고정되어 있다. `starlette`, `pydantic`, `anyio` 같은 하위 의존성은 FastAPI가 설치하는 런타임 의존성이다.

## Docker 실행 방법

```bash
docker build -t ai-assignment-fastapi .
docker run --rm -p 8000:8000 -e SESSION_SECRET=local-secret ai-assignment-fastapi
```

브라우저에서 `http://127.0.0.1:8000`으로 접속한다. 컨테이너 내부에서 SQLite 파일 `app.db`가 생성되고, 애플리케이션 시작 시 테이블과 테스트 계정이 자동으로 준비된다.

## 가상환경 실행 방법

Python 3.10 이상 환경에서 실행할 수 있다.

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python scripts/run.py
```

macOS나 Linux에서는 활성화 명령만 다르다.

```bash
source .venv/bin/activate
python scripts/run.py
```

기본 접속 주소는 `http://127.0.0.1:8000`이다. 다른 SQLite 경로를 쓰려면 `DATABASE_URL`을 지정한다.

```bash
DATABASE_URL=sqlite:///./local.db SESSION_SECRET=local-secret python scripts/run.py
```

## 테스트 계정

| 항목 | 값 |
| --- | --- |
| 아이디 | `demo` |
| 비밀번호 | `demo1234` |
| 저장 방식 | 애플리케이션 시작 시 DB에 자동 생성 |
| 비밀번호 저장 | Python 표준 라이브러리의 PBKDF2-SHA256 해시로 저장 |

회원가입 기능은 포함하지 않았다. 요구사항의 로그인/비로그인 구분과 테스트 계정 명시를 만족하기 위해 하나의 DB 저장 계정을 사용한다.

## 주요 기능 경로

| 경로 | 메서드 | 기능 |
| --- | --- | --- |
| `/` | GET | 공개 홈 화면, 로그인 상태에 따라 버튼과 안내 문구 변경 |
| `/login` | GET | 로그인 화면 |
| `/login` | POST | 로그인 처리, 성공 시 세션에 사용자 ID 저장 |
| `/logout` | POST | 로그아웃 처리, 세션 초기화 |
| `/app` | GET | 보호된 작업 화면, 프로젝트와 작업 관계 데이터 출력 |
| `/app/projects` | POST | 프로젝트 생성 |
| `/app/tasks` | POST | 선택한 프로젝트에 작업 생성 |
| `/app/tasks/{task_id}/complete` | POST | 작업 상태를 진행 전에서 완료로 변경 |

## 공개 경로와 보호 경로 정책

| 구분 | 경로 | 접근 정책 | 비로그인 요청 처리 |
| --- | --- | --- | --- |
| 공개 | `/` | 누구나 접근 가능 | 홈 화면에 로그인 버튼 표시 |
| 공개 | `/login` | 누구나 접근 가능 | 로그인 폼 표시 |
| 공개 | `/login` | 누구나 로그인 시도 가능 | 실패 시 실패 문구 표시 |
| 공개 | `/logout` | 세션 초기화 요청 | 세션이 없어도 홈으로 이동 |
| 보호 | `/app` | 로그인 필수 | 401 상태와 로그인 화면 표시 |
| 보호 | `/app/projects` | 로그인 필수 | 401 상태와 로그인 화면 표시 |
| 보호 | `/app/tasks` | 로그인 필수 | 401 상태와 로그인 화면 표시 |
| 보호 | `/app/tasks/{task_id}/complete` | 로그인 필수 | 401 상태와 로그인 화면 표시 |

보호 경로는 `auth/dependencies.py`의 `require_user`가 담당한다. 이 함수는 세션 쿠키에서 `user_id`를 읽고 DB에서 사용자를 조회한다. 사용자가 없으면 `AuthRequiredError`를 발생시키고, `main.py`의 전역 예외 처리기가 로그인 화면을 렌더링한다.

## 인증 방식 선택

세션 기반 인증을 선택했다. 이 서비스는 Jinja2 SSR 화면이 중심이고, 브라우저에서 폼을 제출하며, 별도의 API 클라이언트나 토큰 저장소가 필요하지 않다. JWT는 모바일 앱이나 외부 API 소비자가 있을 때 장점이 크지만, 이 과제의 핵심 흐름은 로그인 후 같은 웹 화면에서 프로젝트와 작업을 조작하는 것이다. 따라서 서명된 세션 쿠키에 사용자 ID를 저장하는 방식이 가장 단순하고 요구사항에 맞다.

로그인 성공 시 `request.session["user_id"]`에 DB 사용자 ID를 저장한다. 이후 보호 경로의 `Depends(require_user)`가 같은 세션 값을 읽어 현재 사용자를 확정한다. 로그인 실패 시에는 세션을 만들지 않고 `아이디 또는 비밀번호가 올바르지 않습니다` 문구를 보여 준다. 로그아웃은 `request.session.clear()`로 세션을 제거한다.

## 인증 상태에 따른 UI 변화

로그인 전에는 상단에 로그인 버튼만 표시되고, 홈 화면에는 핵심 기능에 접근할 수 없다는 안내가 표시된다. 로그인 후에는 상단에 `demo님 환영합니다`, 작업 화면 링크, 로그아웃 버튼이 표시된다. 보호 화면인 `/app`에서는 프로젝트 생성 폼, 작업 생성 폼, 프로젝트별 작업 목록이 한 화면에 나온다.

## 도메인 모델과 연관관계

| 모델 | 역할 | 주요 관계 |
| --- | --- | --- |
| `User` | 로그인 사용자이자 프로젝트 소유자 | `User.projects`로 `Project`와 1:N |
| `Project` | 작업을 묶는 업무 단위 | `Project.owner`로 `User`와 N:1, `Project.tasks`로 `Task`와 1:N |
| `Task` | 상태가 바뀌는 작업 | `Task.project`로 `Project`와 N:1 |

양방향 관계는 `relationship`과 `back_populates`로 매핑했다. `User.projects`와 `Project.owner`, `Project.tasks`와 `Task.project`가 서로를 가리킨다. 화면에서는 프로젝트 목록을 조회할 때 소유자와 작업 목록을 함께 로딩하고, `/app`에서 프로젝트 이름, 소유자, 해당 프로젝트의 작업과 상태를 함께 출력한다.

부모 삭제 정책은 `cascade="all, delete-orphan"`을 사용했다. 사용자가 삭제되면 그 사용자의 프로젝트와 작업은 소유자를 잃고, 프로젝트가 삭제되면 하위 작업은 업무 맥락을 잃는다. 그래서 고아 레코드를 남기지 않는 정책이 이 도메인에 맞다. 해당 이유는 `models/user.py`와 `models/project.py`의 관계 선언 옆 주석에도 남겨 두었다.

## 상태 변경 중심 비즈니스 로직

핵심 상태 변경은 작업 완료 처리다. 작업은 생성될 때 `todo` 상태이며 화면에는 `진행 전`으로 표시된다. 사용자가 `완료 처리` 버튼을 누르면 `services/project_service.py`의 `complete_task`가 현재 사용자의 프로젝트에 속한 작업인지 확인한 뒤 상태를 `done`으로 바꾼다. 화면에는 `진행 전 → 완료` 메시지가 표시되고, 작업 배지는 `완료`로 바뀐다.

상태 변경 로직을 라우터가 아니라 서비스 계층에 둔 이유는 요청 처리와 비즈니스 규칙을 분리하기 위해서다. 라우터는 폼 값을 받고 응답 위치를 결정한다. 서비스는 소유권 확인, 빈 값 검증, 이미 완료된 작업 차단, 상태 변경 전후 라벨 반환을 담당한다. 데이터 접근은 repositories 계층이 맡는다.

## 전체 구조

```text
auth/
  dependencies.py
  exceptions.py
  passwords.py
models/
  user.py
  project.py
  task.py
repositories/
  user_repository.py
  project_repository.py
  task_repository.py
services/
  auth_service.py
  project_service.py
routers/
  auth.py
  pages.py
templates/
  base.html
  home.html
  login.html
  app.html
  error.html
scripts/
  run.py
  verify.py
```

사용자 관점의 흐름은 홈 접속, 로그인, 작업 화면 진입, 프로젝트 생성, 작업 생성, 완료 처리, 결과 확인이다. 개발자 관점의 흐름은 라우터가 요청을 받고, 인증 의존성이 현재 사용자를 결정하며, 서비스가 비즈니스 규칙을 실행하고, repository가 DB를 조회 또는 저장한 뒤, Jinja2 템플릿이 결과를 렌더링하는 구조다.

## 위협 모델과 보안 판단

이 서비스는 학습용 SSR 웹 애플리케이션이며 복잡한 역할 기반 권한 체계는 구현하지 않았다. 보호 대상은 프로젝트와 작업 화면 전체이고, 인가 기준은 로그인 여부와 데이터 소유자 일치 여부다. 작업 생성과 상태 변경 시 DB 조회 조건에 현재 사용자 ID를 포함해 다른 사용자의 프로젝트나 작업을 조작하지 못하게 했다.

세션 쿠키는 `SessionMiddleware`가 서명하므로 클라이언트가 `user_id`를 임의로 바꾸면 서명이 맞지 않는다. 운영 환경에서는 `SESSION_SECRET`을 반드시 예측하기 어려운 값으로 지정해야 한다. HTTPS 환경에서는 `https_only=True`로 바꾸고, 쿠키 보안 속성을 더 엄격하게 설정하는 것이 맞다.

비밀번호는 평문으로 저장하지 않고 PBKDF2-SHA256 해시로 저장한다. 외부 라이브러리 범위를 줄이기 위해 표준 라이브러리를 사용했다. 운영 서비스라면 비밀번호 정책, 계정 잠금, CSRF 방어, 감사 로그, 비밀값 관리, DB 마이그레이션 도구를 추가해야 한다.

## 문제 해결

| 증상 | 원인 | 해결 |
| --- | --- | --- |
| 로그인 후에도 `/app`에서 로그인 화면이 보임 | 브라우저 쿠키가 오래된 세션을 들고 있음 | 브라우저 쿠키를 삭제하거나 로그아웃 후 다시 로그인 |
| 서버 시작 시 `ModuleNotFoundError` 발생 | 프로젝트 루트가 아닌 위치에서 실행 | 저장소 루트에서 `python scripts/run.py` 실행 |
| 폼 제출이 422를 반환 | 필수 폼 값 누락 | 프로젝트 이름, 작업 제목, 프로젝트 선택 값을 입력 |
| DB를 새로 시작하고 싶음 | 기존 `app.db`가 남아 있음 | 서버를 중지하고 `app.db` 삭제 후 재실행 |
| Docker 컨테이너 재시작 후 데이터가 사라짐 | 컨테이너 내부 SQLite 파일을 사용함 | 데이터 보존이 필요하면 볼륨을 마운트하고 `DATABASE_URL` 경로를 볼륨 내부로 지정 |

## 검증 증거

검증은 Ubuntu 24.04 기반 Docker 컨테이너에서 수행했다. 의존성 설치, 서버 실행, HTTP 시나리오 확인, 컴파일 확인, Docker 이미지 빌드를 모두 컨테이너 또는 Docker 빌드 환경에서 실행했다.

| 증거 파일 | 확인 내용 |
| --- | --- |
| `evidence/verification.log` | 비로그인 `/app` 접근 차단, 로그인 실패 안내, 정상 로그인, 프로젝트 생성, 작업 생성, 완료 상태 변경 |
| `evidence/runtime.log` | 빌드된 Docker 이미지가 `/`와 `/login` 화면을 실제로 응답 |
| `evidence/compile.log` | `python -m compileall -q .` 통과 |
| `evidence/docker-build.log` | Dockerfile 기반 이미지 빌드 성공 |

`evidence/verification.log`의 핵심 결과는 다음과 같다.

```text
비로그인 /app 접근 상태: 401
잘못된 로그인 상태: 401
정상 로그인 후 상태: 200
프로젝트 생성 상태: 200
작업 생성 상태: 200
작업 완료 상태 변경 상태: 200
```

자동 검증을 다시 실행하려면 다음 명령을 사용한다.

```bash
python scripts/verify.py
```

이 명령은 검증용 SQLite DB를 만들고, Uvicorn 서버를 실행한 뒤, 로그인부터 상태 변경까지의 HTTP 흐름을 수행하고 `evidence/verification.log`를 갱신한다.
