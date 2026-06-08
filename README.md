# FastAPI 메모 관리 CRUD 웹 서비스

## 개요

이 애플리케이션은 브라우저에서 메모를 등록하고 목록, 상세, 수정, 삭제 흐름을 확인하는 FastAPI 기반 SSR CRUD 웹 서비스다. 데이터는 서버 메모리가 아니라 프로젝트 루트의 `database.db` SQLite 파일에 저장되며, SQLAlchemy ORM 모델과 세션을 통해 조회하고 변경한다.

관리 대상은 메모다. 메모는 제목, 내용, 분류, 작성일시, 수정일시를 가진 단일 모델이며, 화면 흐름은 홈, 목록, 상세, 등록 폼, 수정 폼, 없음 안내 화면으로 구성된다. 필드를 이 범위로 제한하면 모델 간 관계나 인증 없이도 등록, 조회, 수정, 삭제의 핵심 흐름을 모두 확인할 수 있다.

## 실행

Python 3.10 이상에서 실행할 수 있다. 의존성은 `requirements.txt`에 고정되어 있으며, 필요한 패키지는 `fastapi`, `uvicorn`, `sqlalchemy`, `jinja2`, `python-multipart`다.

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

## 프로젝트 구조와 역할

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

라우터와 서비스의 분리 기준은 FastAPI와 HTTP를 알아야 하는 코드인지 여부다. `Request`, `Form()`, `TemplateResponse`, `RedirectResponse`, `status.HTTP_303_SEE_OTHER`, `request.url_for()`처럼 웹 프레임워크와 화면 전환에 직접 묶인 처리는 라우터에 둔다. 이 로직은 같은 메모 저장 규칙을 쓰더라도 SSR 화면인지 REST API인지에 따라 달라질 수 있기 때문이다. 반대로 제목과 내용의 앞뒤 공백 제거, 빈 제목과 빈 내용 거부, 분류가 비어 있을 때 `일반`으로 저장, 수정/삭제 대상 존재 여부 판단은 HTTP 응답 형식과 무관한 메모 업무 규칙이므로 서비스에 둔다.

모든 로직을 라우터에 넣으면 화면 렌더링 코드, 입력 검증, DB 접근, 예외 판단이 한 함수에 섞인다. 그러면 같은 검증을 등록과 수정에서 중복 작성하기 쉽고, 검색 또는 API 응답을 추가할 때 기존 HTML 라우터를 건드려야 한다. 테스트도 어려워진다. 서비스는 FastAPI 객체 없이 호출할 수 있어 입력 규칙을 독립적으로 확인할 수 있고, 저장소는 SQLAlchemy 세션만 주입하면 DB 동작을 좁게 검증할 수 있다. 이 구조는 기능이 작을 때는 파일 수가 늘어나는 비용이 있지만, CRUD 흐름이 수정되거나 출력 방식이 바뀔 때 변경 범위를 줄인다.

## 메모 모델

`Memo` 모델의 필드는 단일 도메인 CRUD를 설명하기에 필요한 값만 남겼다. `id`는 상세, 수정, 삭제 URL에서 특정 메모를 식별하는 기본키다. `title`은 목록에서 빠르게 구분할 수 있는 짧은 제목이고, `content`는 상세 화면에 표시되는 본문이다. `category`는 관계형 테이블을 만들지 않고도 간단한 분류를 경험할 수 있는 문자열 필드다. `created_at`은 최신순 목록 정렬과 최초 등록 시각 표시를 위해 필요하고, `updated_at`은 수정 이후 값이 바뀌었는지 상세 화면에서 확인하기 위해 둔다.

`app/models/memo.py`의 `Memo` 클래스는 `memos` 테이블에 매핑된다. 저장소는 ORM 객체를 직접 다루며, 라우터는 `MemoView` DTO만 템플릿에 전달한다.

## 화면과 요청 흐름

홈 화면인 `GET /`는 앱 목적을 설명하고 메모 목록과 새 메모 작성 화면으로 이동하는 링크를 제공한다. 모든 주요 화면은 Jinja2 템플릿 렌더링 결과인 `TemplateResponse`로 출력된다.

메모 목록은 `GET /memos`에서 렌더링된다. `q` 쿼리 파라미터가 있으면 제목 또는 내용에 검색어가 포함된 메모만 보여준다. 등록 화면은 `GET /memos/new`에서 HTML 폼으로 렌더링되고, 등록 요청은 `POST /memos`에서 `Form()`으로 전달된 제목, 내용, 분류를 검증한 뒤 저장한다. 저장에 성공하면 `303 See Other`로 목록 화면에 리다이렉트한다.

상세 화면은 `GET /memos/{memo_id}`에서 렌더링된다. 제목, 내용, 분류, 작성일시, 수정일시를 포함한 전체 필드를 보여주며 수정, 삭제, 목록 이동 동선을 제공한다. 수정 화면은 `GET /memos/{memo_id}/edit`에서 기존 값을 채운 폼으로 렌더링되고, 수정 요청은 `POST /memos/{memo_id}/edit`에서 `Form()` 입력을 검증하고 수정한 뒤 `303 See Other`로 상세 화면에 리다이렉트한다. 삭제 요청은 `POST /memos/{memo_id}/delete`에서 처리되며, 삭제한 뒤 `303 See Other`로 목록 화면에 리다이렉트한다. 존재하지 않는 메모를 조회하면 `404 Not Found`와 "해당 메모를 찾을 수 없습니다" 안내 화면을 보여준다.

브라우저가 `GET /memos`를 요청하면 `app/routers/memos.py`의 `list_memos()`가 호출된다. 라우터는 `Depends(get_memo_service)`를 통해 서비스 객체를 받고, 서비스는 저장소를 통해 DB에서 메모 목록을 가져온다. 저장소는 `MemoRepository.list()`에서 SQLAlchemy `select(Memo)` 문을 실행한다. 서비스는 ORM 모델을 `MemoView` DTO로 바꾸고, 라우터는 DTO 목록을 `templates/memos/list.html`에 전달해 `TemplateResponse`를 반환한다.

등록 흐름은 `GET /memos/new`와 `POST /memos`로 나뉜다. `GET /memos/new`는 입력 폼만 렌더링한다. 사용자가 저장 버튼을 누르면 브라우저가 폼 필드를 `POST /memos`로 전송하고, 라우터는 `title`, `content`, `category`를 FastAPI의 `Form()` 파라미터로 받는다. 서비스는 제목과 내용의 앞뒤 공백을 제거하고 필수값을 확인한다. 유효하면 저장소가 `Memo` ORM 객체를 만들고 `Session.add()`, `Session.commit()`, `Session.refresh()` 순서로 SQLite에 저장한다.

상세, 수정, 삭제도 같은 계층 흐름을 따른다. 라우터는 URL과 화면 전환을 다루고, 서비스는 존재 여부와 입력 규칙을 판단하고, 저장소는 DB 작업만 수행한다.

## GET과 POST

`GET`은 화면 조회와 검색처럼 서버 상태를 바꾸지 않는 요청에 사용한다. 홈, 목록, 상세, 등록 폼, 수정 폼은 모두 `GET`으로 처리된다. 브라우저 새로고침, 뒤로 가기, 링크 공유가 자연스럽게 동작해야 하기 때문이다.

`POST`는 등록, 수정, 삭제처럼 서버 상태를 바꾸는 요청에 사용한다. HTML 폼은 `method="post"`로 제출되고, 서버는 `Form()` 파라미터로 입력값을 받는다. 이 분리는 사용자가 링크를 클릭하거나 페이지를 새로고침했을 때 의도하지 않은 DB 변경이 발생하지 않도록 만든다.

## PRG 패턴

등록, 수정, 삭제가 성공하면 라우터는 화면을 바로 렌더링하지 않고 `RedirectResponse`를 반환한다. 상태 코드는 모두 `status.HTTP_303_SEE_OTHER`를 사용한다.

```python
return RedirectResponse(request.url_for("list_memos"), status_code=status.HTTP_303_SEE_OTHER)
```

이 흐름은 POST 이후 브라우저 주소를 GET 화면으로 바꾼다. 사용자가 결과 화면에서 F5를 눌러도 마지막 요청은 POST가 아니라 GET이므로 같은 등록, 수정, 삭제가 다시 실행되지 않는다. `scripts/verify.py`는 자동 리다이렉트를 끈 요청으로 `303`과 `Location` 헤더를 먼저 확인한 뒤, 해당 위치로 GET 요청을 보내 최종 화면을 검증한다.

## 데이터 저장

`app/database.py`는 `sqlite:///.../database.db` URL로 엔진을 만들고 `SessionLocal`을 정의한다. `get_db()`는 FastAPI 의존성으로 사용되며 요청마다 SQLAlchemy `Session`을 열고 응답 후 닫는다.

저장소 메서드는 ORM 호출이 어떤 SQL 작업으로 이어지는지 확인하기 좋은 위치다. `MemoRepository.create()`에서 `Session.add(memo)`는 새 `Memo` 객체를 세션에 등록해 다음 flush 시 `INSERT` 대상이 되게 한다. `Session.commit()`은 트랜잭션을 커밋하면서 대기 중인 변경을 DB에 반영하므로 실제 `INSERT`가 실행된다. `Session.refresh(memo)`는 DB가 채운 기본키와 기본값을 다시 읽어 ORM 객체에 반영한다. 목록 조회의 `select(Memo)`와 `self.db.execute(statement).scalars()`는 `SELECT`에 대응하고, `self.db.get(Memo, memo_id)`는 기본키 조건으로 단건을 조회하는 `SELECT`에 대응한다. 수정은 이미 조회한 ORM 객체의 속성을 바꾼 뒤 `commit()`할 때 `UPDATE`로 반영된다. 삭제는 `Session.delete(memo)`로 삭제 대상을 표시하고 `commit()`할 때 `DELETE`로 반영된다.

현재 코드는 SQLAlchemy 2.x 스타일의 `select()`를 사용한다. 이전 SQLAlchemy 예제에서 자주 보이는 `Session.query(Memo)`와 목적은 같지만, 이 프로젝트에서는 `select(Memo)`를 기준으로 목록과 검색 조건을 만든다. 검색어가 있을 때 저장소는 `Memo.title.like(pattern)` 또는 `Memo.content.like(pattern)` 조건을 붙이고, SQLAlchemy가 값을 바인딩하므로 사용자가 입력한 검색어를 SQL 문자열에 직접 이어 붙이지 않는다.

SQLite 저장 여부는 두 방식으로 확인할 수 있다.

```bash
python -c "import sqlite3; con=sqlite3.connect('database.db'); print(con.execute('select id, title, category from memos').fetchall())"
```

또는 DB Browser for SQLite에서 `database.db`를 열어 `memos` 테이블을 확인한다.

## 입력 검증과 검색

제목과 내용은 필수값이다. 서비스 계층의 `_normalize_and_validate()`가 공백을 제거한 뒤 비어 있는 값을 검사한다. 검증 실패 시 저장소를 호출하지 않으므로 DB에 빈 메모가 저장되지 않는다. 라우터는 `400 Bad Request`로 같은 폼을 다시 렌더링하고, 사용자가 입력했던 값과 오류 문구를 함께 보여준다.

목록 검색은 `GET /memos?q=검색어`로 동작한다. 저장소는 제목 또는 내용에 검색어가 포함되는지 `like` 조건으로 필터링한다. 검색은 상태 변경이 아니므로 POST가 아니라 GET을 사용한다.

## 검증

전체 검증은 `scripts/verify.py` 한 파일로 수행한다. 이 스크립트는 서버를 시작하고, 실제 HTTP 요청으로 홈, 목록, 등록, 상세, 수정, 검색, 검증 실패, 없음 안내, 삭제 흐름을 실행한 뒤 SQLite 파일을 직접 조회한다. 검증 시작 시 기존 `database.db`를 삭제하므로 항상 같은 상태에서 재현된다.

```bash
docker build -t fastapi-memo-crud .
docker run --rm -v "${PWD}:/app" -w /app fastapi-memo-crud python scripts/verify.py
```

검증 결과는 다음 파일에 보존되어 있다.

- `evidence/docker-build.log`: Docker 이미지 빌드 성공과 빌드 컨텍스트 축소 확인
- `evidence/compile.log`: `python -m compileall app scripts` 성공 확인
- `evidence/verification.log`: Uvicorn 서버 기동, `200 OK`, `303 See Other`, `400 Bad Request`, `404 Not Found`, SQLite 직접 조회 검증 성공 확인

`evidence/docker-build.log`에는 Docker 이미지 빌드가 성공했고 빌드 컨텍스트가 `18.71kB`로 전송된 기록이 있다.

`evidence/compile.log`에는 다음 명령의 성공 결과가 기록되어 있다.

```bash
python -m compileall app scripts
```

`evidence/verification.log`에는 다음 흐름이 기록되어 있다.

```text
검증 성공: 홈, SSR CRUD, PRG, 검색, 검증, 404 안내, SQLite 저장을 모두 확인했습니다.
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     "POST /memos HTTP/1.1" 303 See Other
INFO:     "POST /memos/1/edit HTTP/1.1" 303 See Other
INFO:     "POST /memos/1/delete HTTP/1.1" 303 See Other
```

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

## 확장

SQLite에서 PostgreSQL 같은 다른 DB로 바꾸면 핵심 변경 지점은 `app/database.py`다. `DATABASE_URL`을 PostgreSQL 접속 문자열로 바꾸고, `create_engine()`의 SQLite 전용 옵션인 `connect_args={"check_same_thread": False}`를 제거해야 한다. 실제 운영 DB를 사용한다면 접속 정보는 코드에 고정하지 않고 환경 변수로 주입하는 방식이 적절하다. PostgreSQL 드라이버 패키지도 필요하지만, 현재 과제의 의존성 제한 때문에 이 구현에는 추가하지 않았다. SQLAlchemy `Session`, 모델, 저장소 메서드의 기본 구조는 유지되므로 라우터, 템플릿, 서비스의 대부분은 바뀌지 않는다. 다만 DB별 문자열 검색의 대소문자 처리, 날짜 함수, 마이그레이션 방식은 달라질 수 있어 저장소 쿼리와 DB 초기화 절차는 다시 확인해야 한다.

모델 간 연관관계를 추가한다면 `models/`에 새 ORM 모델을 만들고, 기존 `Memo`에는 외래키 컬럼과 `relationship()`을 추가한다. 예를 들어 카테고리를 별도 테이블로 분리한다면 `Category` 모델, `Memo.category_id`, `Memo.category` 관계가 필요하다. 그 다음 `repositories/`에는 조인 조회나 관련 행 저장 메서드를 추가하고, `services/`에는 관계 대상 존재 여부 확인과 삭제 정책 같은 규칙을 둔다. `schemas/`는 화면에 넘길 DTO를 확장하고, `templates/`와 라우터 폼은 선택 목록이나 관련 데이터 표시를 받도록 바뀐다. 관계가 생겨도 라우터가 직접 조인을 작성하지 않고, 서비스와 저장소를 거쳐 필요한 DTO만 받는 원칙은 유지한다.

SSR CRUD를 REST API와 별도 프론트엔드 구조로 전환하면 가장 많이 바뀌는 곳은 라우터와 템플릿이다. 라우터는 `TemplateResponse`와 `RedirectResponse` 대신 JSON 응답과 적절한 HTTP 상태 코드를 반환하고, 등록/수정 입력은 HTML `Form()` 대신 JSON 요청 본문으로 받을 수 있다. `templates/`와 서버 정적 화면은 React, Vue, 순수 JavaScript 같은 프론트엔드 앱으로 대체된다. 반면 메모 업무 규칙을 가진 서비스, DB 접근을 맡은 저장소, ORM 모델, 세션 의존성 구조는 대부분 유지할 수 있다. PRG 패턴은 서버 SSR에서 필요한 중복 제출 방지 방식이므로, API 구조에서는 프론트엔드가 POST 성공 후 목록 또는 상세 화면으로 이동하고 재요청을 제어하는 방식으로 바뀐다.

## 보안과 범위

이 과제는 인증, 인가, 사용자별 데이터 분리, 모델 간 관계를 구현하지 않는다. 따라서 개인 정보나 민감한 데이터를 저장하는 용도로 사용하면 안 된다. 삭제는 상세 화면의 POST 폼으로만 실행되지만, CSRF 방어 토큰은 구현 범위에 포함하지 않았다. 공개 배포를 한다면 CSRF 방어, 인증, 입력 길이 제한, 감사 로그, 운영 DB 백업 정책이 추가로 필요하다.

현재 입력값은 Jinja2 템플릿의 기본 escaping으로 출력되므로 사용자가 입력한 HTML은 그대로 실행되지 않는다. SQL 조건은 SQLAlchemy 표현식과 바인딩을 사용하므로 검색어를 문자열로 이어 붙여 SQL을 만들지 않는다.
