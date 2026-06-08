# FastAPI 메모 관리 CRUD 웹 서비스

## 개요

이 애플리케이션은 브라우저에서 메모를 등록하고 목록, 상세, 수정, 삭제 흐름을 확인하는 FastAPI 기반 SSR CRUD 웹 서비스다. 데이터는 서버 메모리가 아니라 프로젝트 루트의 `database.db` SQLite 파일에 저장되며, SQLAlchemy ORM 모델과 세션을 통해 조회하고 변경한다.

관리 대상은 메모다. 메모는 제목, 내용, 분류, 작성일시, 수정일시를 가진 단일 모델이며, 화면 흐름은 홈, 목록, 상세, 등록 폼, 수정 폼, 없음 안내 화면으로 구성된다.

## 주요 기능

- `GET /`: 앱 목적을 설명하고 메모 목록과 새 메모 작성 화면으로 이동하는 링크를 제공한다.
- `GET /memos`: 메모 목록을 보여주고 `q` 쿼리 파라미터로 제목 또는 내용을 검색한다.
- `GET /memos/new`: HTML 폼으로 새 메모 입력 화면을 렌더링한다.
- `POST /memos`: `Form()`으로 전달된 제목, 내용, 분류를 검증한 뒤 저장하고 `303 See Other`로 목록 화면에 리다이렉트한다.
- `GET /memos/{memo_id}`: 메모의 전체 필드와 수정, 삭제, 목록 이동 동선을 보여준다.
- `GET /memos/{memo_id}/edit`: 기존 값을 채운 수정 폼을 렌더링한다.
- `POST /memos/{memo_id}/edit`: `Form()` 입력을 검증하고 수정한 뒤 `303 See Other`로 상세 화면에 리다이렉트한다.
- `POST /memos/{memo_id}/delete`: 삭제한 뒤 `303 See Other`로 목록 화면에 리다이렉트한다.
- 존재하지 않는 메모를 조회하면 `404 Not Found`와 "해당 메모를 찾을 수 없습니다" 안내 화면을 보여준다.
- 제목과 내용이 비어 있으면 저장하지 않고 같은 폼에 오류 문구를 표시한다.

## 프로젝트 구조

```text
.
├── app/
│   ├── database.py
│   ├── main.py
│   ├── models/
│   │   └── memo.py
│   ├── repositories/
│   │   └── memo_repository.py
│   ├── routers/
│   │   ├── dependencies.py
│   │   ├── home.py
│   │   └── memos.py
│   ├── schemas/
│   │   └── memo.py
│   └── services/
│       └── memo_service.py
├── templates/
│   ├── base.html
│   ├── home.html
│   └── memos/
├── static/
│   └── styles.css
├── scripts/
│   ├── run.py
│   └── verify.py
├── evidence/
├── Dockerfile
├── requirements.txt
└── README.md
```

`routers/`는 HTTP 요청, 폼 수신, 템플릿 렌더링, 리다이렉트를 담당한다. `services/`는 입력 정규화와 필수값 검증 같은 비즈니스 규칙을 담당한다. `repositories/`는 SQLAlchemy `Session`으로 DB 조회와 변경을 수행한다. `models/`는 SQLite 테이블과 연결되는 ORM 모델을 정의한다. `schemas/`는 라우터가 ORM 객체에 직접 의존하지 않도록 폼 입력 DTO와 템플릿 출력 DTO를 제공한다.

## 실행 방법

Python 3.10 이상에서 실행할 수 있다. 의존성은 `requirements.txt`에 고정되어 있다.

Windows PowerShell 기준:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python scripts/run.py --host 0.0.0.0 --port 8000
```

macOS 또는 Linux 기준:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python scripts/run.py --host 0.0.0.0 --port 8000
```

서버가 시작되면 브라우저에서 `http://localhost:8000`으로 접속한다. `scripts/run.py`는 실행 전에 SQLAlchemy 테이블 생성 함수를 호출하므로, 별도 DB 초기화 명령 없이 `database.db`가 프로젝트 루트에 생성된다.

Docker로도 동일하게 실행할 수 있다.

```bash
docker build -t fastapi-memo-crud .
docker run --rm -p 8000:8000 fastapi-memo-crud
```

## 재현 검증

전체 검증은 `scripts/verify.py` 한 파일로 수행한다. 이 스크립트는 서버를 시작하고, 실제 HTTP 요청으로 홈, 목록, 등록, 상세, 수정, 검색, 검증 실패, 없음 안내, 삭제 흐름을 실행한 뒤 SQLite 파일을 직접 조회한다. 검증 시작 시 기존 `database.db`를 삭제하므로 항상 같은 상태에서 재현된다.

```bash
docker build -t fastapi-memo-crud .
docker run --rm -v "${PWD}:/app" -w /app fastapi-memo-crud python scripts/verify.py
```

검증 결과는 다음 파일에 보존되어 있다.

- `evidence/docker-build.log`: Docker 이미지 빌드 성공과 빌드 컨텍스트 축소 확인
- `evidence/compile.log`: `python -m compileall app scripts` 성공 확인
- `evidence/verification.log`: Uvicorn 서버 기동, `200 OK`, `303 See Other`, `400 Bad Request`, `404 Not Found`, SQLite 직접 조회 검증 성공 확인

`evidence/verification.log`에는 다음 흐름이 기록되어 있다.

```text
검증 성공: 홈, SSR CRUD, PRG, 검색, 검증, 404 안내, SQLite 저장을 모두 확인했습니다.
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     "POST /memos HTTP/1.1" 303 See Other
INFO:     "POST /memos/1/edit HTTP/1.1" 303 See Other
INFO:     "POST /memos/1/delete HTTP/1.1" 303 See Other
```

## 요청 흐름

브라우저가 `GET /memos`를 요청하면 `app/routers/memos.py`의 `list_memos()`가 호출된다. 라우터는 `Depends(get_memo_service)`를 통해 서비스 객체를 받고, 서비스는 저장소를 통해 DB에서 메모 목록을 가져온다. 저장소는 `MemoRepository.list()`에서 SQLAlchemy `select(Memo)` 문을 실행한다. 서비스는 ORM 모델을 `MemoView` DTO로 바꾸고, 라우터는 DTO 목록을 `templates/memos/list.html`에 전달해 `TemplateResponse`를 반환한다.

등록 흐름은 `GET /memos/new`와 `POST /memos`로 나뉜다. `GET /memos/new`는 입력 폼만 렌더링한다. 사용자가 저장 버튼을 누르면 브라우저가 폼 필드를 `POST /memos`로 전송하고, 라우터는 `title`, `content`, `category`를 FastAPI의 `Form()` 파라미터로 받는다. 서비스는 제목과 내용을 trim하고 필수값을 확인한다. 유효하면 저장소가 `Memo` ORM 객체를 만들고 `Session.add()`, `Session.commit()`, `Session.refresh()` 순서로 SQLite에 저장한다.

상세, 수정, 삭제도 같은 계층 흐름을 따른다. 라우터는 URL과 화면 전환을 다루고, 서비스는 존재 여부와 입력 규칙을 판단하고, 저장소는 DB 작업만 수행한다.

## GET과 POST 분리

`GET`은 화면 조회와 검색처럼 서버 상태를 바꾸지 않는 요청에 사용한다. 홈, 목록, 상세, 등록 폼, 수정 폼은 모두 `GET`으로 처리된다. 브라우저 새로고침, 뒤로 가기, 링크 공유가 자연스럽게 동작해야 하기 때문이다.

`POST`는 등록, 수정, 삭제처럼 서버 상태를 바꾸는 요청에 사용한다. HTML 폼은 `method="post"`로 제출되고, 서버는 `Form()` 파라미터로 입력값을 받는다. 이 분리는 사용자가 링크를 클릭하거나 페이지를 새로고침했을 때 의도하지 않은 DB 변경이 발생하지 않도록 만든다.

## PRG 패턴

등록, 수정, 삭제가 성공하면 라우터는 화면을 바로 렌더링하지 않고 `RedirectResponse`를 반환한다. 상태 코드는 모두 `status.HTTP_303_SEE_OTHER`를 사용한다.

```python
return RedirectResponse(request.url_for("list_memos"), status_code=status.HTTP_303_SEE_OTHER)
```

이 흐름은 POST 이후 브라우저 주소를 GET 화면으로 바꾼다. 사용자가 결과 화면에서 F5를 눌러도 마지막 요청은 POST가 아니라 GET이므로 같은 등록, 수정, 삭제가 다시 실행되지 않는다. `scripts/verify.py`는 자동 리다이렉트를 끈 요청으로 `303`과 `Location` 헤더를 먼저 확인한 뒤, 해당 위치로 GET 요청을 보내 최종 화면을 검증한다.

## SQLAlchemy ORM과 SQLite 저장

`app/database.py`는 `sqlite:///.../database.db` URL로 엔진을 만들고 `SessionLocal`을 정의한다. `get_db()`는 FastAPI 의존성으로 사용되며 요청마다 SQLAlchemy `Session`을 열고 응답 후 닫는다.

`app/models/memo.py`의 `Memo` 클래스는 `memos` 테이블에 매핑된다. `id`는 기본키이고, `title`, `content`, `category`, `created_at`, `updated_at` 컬럼이 있다. 저장소는 ORM 객체를 직접 다루며, 라우터는 `MemoView` DTO만 템플릿에 전달한다.

SQLite 저장 여부는 두 방식으로 확인할 수 있다.

```bash
python -c "import sqlite3; con=sqlite3.connect('database.db'); print(con.execute('select id, title, category from memos').fetchall())"
```

또는 DB Browser for SQLite에서 `database.db`를 열어 `memos` 테이블을 확인한다.

## 입력 검증과 검색

제목과 내용은 필수값이다. 서비스 계층의 `_normalize_and_validate()`가 공백을 제거한 뒤 비어 있는 값을 검사한다. 검증 실패 시 저장소를 호출하지 않으므로 DB에 빈 메모가 저장되지 않는다. 라우터는 `400 Bad Request`로 같은 폼을 다시 렌더링하고, 사용자가 입력했던 값과 오류 문구를 함께 보여준다.

목록 검색은 `GET /memos?q=검색어`로 동작한다. 저장소는 제목 또는 내용에 검색어가 포함되는지 `like` 조건으로 필터링한다. 검색은 상태 변경이 아니므로 POST가 아니라 GET을 사용한다.

## 운영과 문제 해결

서버가 시작되지 않으면 먼저 의존성이 설치되었는지 확인한다.

```bash
python -m pip install -r requirements.txt
```

`python-multipart`가 없으면 FastAPI가 `Form()` 파라미터를 처리하지 못한다. 이 패키지는 `requirements.txt`에 포함되어 있다.

포트가 이미 사용 중이면 실행 포트를 바꾼다.

```bash
python scripts/run.py --host 0.0.0.0 --port 8001
```

DB를 초기 상태로 되돌리고 싶으면 서버를 종료한 뒤 `database.db`를 삭제하고 다시 실행한다. 앱 시작 시 테이블은 자동 생성된다.

템플릿 경로 오류가 나면 `templates/` 디렉터리가 프로젝트 루트에 있는지 확인한다. 정적 CSS가 보이지 않으면 `static/styles.css`와 `app/main.py`의 `/static` 마운트가 함께 있어야 한다.

## 보안과 범위

이 과제는 인증, 인가, 사용자별 데이터 분리, 모델 간 관계를 구현하지 않는다. 따라서 개인 정보나 민감한 데이터를 저장하는 용도로 사용하면 안 된다. 삭제는 상세 화면의 POST 폼으로만 실행되지만, CSRF 방어 토큰은 구현 범위에 포함하지 않았다. 공개 배포를 한다면 CSRF 방어, 인증, 입력 길이 제한, 감사 로그, 운영 DB 백업 정책이 추가로 필요하다.

현재 입력값은 Jinja2 템플릿의 기본 escaping으로 출력되므로 사용자가 입력한 HTML은 그대로 실행되지 않는다. SQL 조건은 SQLAlchemy 표현식과 바인딩을 사용하므로 검색어를 문자열로 이어 붙여 SQL을 만들지 않는다.
