# Reading Log — React + Supabase 기반 독서 기록 SPA

읽은 책을 한 권씩 가볍게 기록하기 위한 단일 페이지 애플리케이션. 제목·저자·카테고리·별점·메모만으로 책 한 권을 등록하고, 나중에 카테고리·키워드로 다시 찾아본다. 로그인한 사용자는 자신이 등록한 책만 보이고 다룰 수 있다.

코드는 모두 `web/` 디렉터리 아래 있고, Supabase 스키마(SQL)는 `web/supabase/schema.sql` 한 파일에 정리되어 있다.

---

## 1. 기술 스택

| 영역 | 선택 | 비고 |
|---|---|---|
| 런타임 | React 18.3 | 함수형 컴포넌트 + Hooks 만 사용 |
| 번들러 | Vite 5 | dev 서버 + 프로덕션 번들 |
| 라우팅 | react-router-dom v6 | `Routes`/`Route`, `Outlet`, `useNavigate`, `useParams`, `NavLink` |
| 백엔드 | Supabase (Postgres + Auth) | `@supabase/supabase-js` v2 |
| 상태 관리 | React `useState` / `useReducer`(미사용) / Context 2개 | Auth, Theme |
| 비동기 데이터 | 직접 만든 커스텀 훅 (`useBooks`, `useBook`) | 라이브러리 미사용 |
| 스타일링 | 순수 CSS + CSS Variables (라이트/다크 토큰) | 컴포넌트별 `*.css` 파일 분리 |
| 타입 | JavaScript (TS 미사용) |  |
| 배포 | Vercel (권장) 또는 Netlify | 빌드 명령 `npm run build`, 출력 `dist/` |

`@supabase/supabase-js`, `react-router-dom`, React/Vite 외 런타임 의존성은 일부러 추가하지 않았다. CSS-in-JS 라이브러리·폼 라이브러리·상태 관리 라이브러리·UI 키트를 모두 배제하고, React 자체의 동작 원리(컴포넌트·props·state·effect·이벤트·렌더링)를 그대로 드러내는 것이 목표다.

---

## 2. 로컬에서 실행

전제: Node.js 18 이상(현 작성 환경은 24.x), npm 10 이상.

```bash
# 1) 저장소 클론 후
cd web

# 2) 의존성 설치
npm install

# 3) 환경변수 파일 작성 (.env.example 을 복사)
cp .env.example .env
#   VITE_SUPABASE_URL=https://<project-ref>.supabase.co
#   VITE_SUPABASE_ANON_KEY=<anon public key>

# 4) 개발 서버
npm run dev          # http://localhost:5173

# 5) 프로덕션 빌드 확인
npm run build        # dist/ 생성
npm run preview      # 빌드 결과를 로컬에서 미리 보기
```

`.env` 파일은 `.gitignore` 에 등록되어 있어 커밋되지 않는다. `.env.example` 만 추적된다.

---

## 3. Supabase 프로젝트 준비

1. <https://supabase.com> 에서 프로젝트를 새로 만든다 (Free tier 로 충분).
2. **Project Settings → API** 에서 `Project URL` 과 `anon public` 키를 복사해 `web/.env` 에 채운다. 두 값은 클라이언트에 노출되는 공개 키다.
3. **SQL Editor → New query** 에 `web/supabase/schema.sql` 의 전체 내용을 붙여넣고 Run. `books` 테이블, `updated_at` 트리거, RLS 정책 4개가 한 번에 생성된다.
4. **Authentication → Providers → Email** 을 활성화한다. 데모용으로는 *Confirm email* 옵션을 꺼 두면 가입 즉시 로그인할 수 있어 편하다.
5. (선택) **Authentication → Users → Invite user** 로 테스트 계정을 미리 만들어 두어도 된다.

스키마의 RLS 정책은 `auth.uid() = user_id` 만 허용한다. 다른 사용자의 행은 anon key 가 있어도 조회·수정·삭제가 모두 거부되므로, 클라이언트 전용 키 공개의 위험이 통제된다.

---

## 4. 배포 (Vercel)

1. GitHub 저장소를 Vercel 에 import.
2. **Root Directory** 를 `web` 으로 지정. Framework Preset 은 `Vite`.
3. **Environment Variables** 에 `VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY` 두 개를 등록 (Production / Preview 모두).
4. Deploy. 빌드 명령은 `npm run build`, 출력 디렉터리는 `dist`.
5. Vercel 이 자동으로 SPA fallback (모든 경로를 `index.html` 로) 처리해 주므로 `vercel.json` 없이도 `react-router-dom` 의 BrowserRouter 가 정상 동작한다.

Netlify 를 쓸 경우에는 동일하게 두 환경변수를 등록하고, `web/public/_redirects` 에 `/* /index.html 200` 한 줄을 두면 된다 (현재 리포에는 포함하지 않았다).

---

## 5. 프로젝트 구조

```
web/
├─ index.html
├─ vite.config.js
├─ .env.example
├─ supabase/
│  └─ schema.sql                 # 책 테이블 + RLS + 트리거
└─ src/
   ├─ main.jsx                   # ReactDOM root + Router/Context 주입
   ├─ App.jsx                    # <Routes> 정의
   ├─ index.css                  # 전역 토큰(라이트/다크) + 레이아웃 유틸
   ├─ lib/
   │  └─ supabase.js             # createClient + CATEGORIES 상수
   ├─ contexts/
   │  ├─ AuthContext.jsx         # Supabase 세션 → React Context
   │  └─ ThemeContext.jsx        # 라이트/다크 토글 + localStorage 유지
   ├─ hooks/
   │  ├─ useBooks.js             # 목록 조회/삭제 + 필터·검색
   │  ├─ useBook.js              # 상세 단건 조회
   │  └─ useDebounce.js          # 검색 입력 디바운스
   ├─ components/                # 재사용 UI 컴포넌트
   │  ├─ Layout.jsx / Layout.css     # Header + Nav + <Outlet/>
   │  ├─ Header.jsx                  # 브랜드 + 테마/로그인 컨트롤
   │  ├─ Button.jsx / Button.css
   │  ├─ Input.jsx / Field.css
   │  ├─ Textarea.jsx
   │  ├─ Select.jsx
   │  ├─ Card.jsx / Card.css
   │  ├─ Badge.jsx / Badge.css
   │  ├─ Rating.jsx / Rating.css
   │  ├─ Loading.jsx / States.css
   │  ├─ EmptyState.jsx
   │  ├─ ErrorState.jsx
   │  ├─ FilterBar.jsx / FilterBar.css
   │  ├─ BookCard.jsx / BookCard.css     # React.memo 적용
   │  ├─ BookForm.jsx
   │  ├─ ProtectedRoute.jsx
   │  └─ ThemeToggle.jsx
   └─ pages/                     # 라우트 단위 화면 (UI 컴포넌트와 분리)
      ├─ HomePage.jsx
      ├─ LoginPage.jsx
      ├─ BooksPage.jsx
      ├─ BookDetailPage.jsx
      ├─ BookFormPage.jsx        # mode="new" | "edit"
      ├─ ProfilePage.jsx
      └─ NotFoundPage.jsx
```

`pages/` 와 `components/` 는 의도적으로 분리한다.

- **pages/** 는 라우트와 1:1 로 대응되고, URL 파라미터를 읽어 데이터 훅을 호출하고, 작업 성공 후 어디로 보낼지 같은 **흐름 결정**을 담당한다. 다른 화면이 import 하지 않는다.
- **components/** 는 props 만 받으면 어디서든 동작하는 **표시 단위**다. Supabase 클라이언트를 직접 호출하지 않고, 라우터 훅(`useNavigate` 등)도 가능하면 끌어들이지 않는다 (예외: `Header`/`Layout`/`ThemeToggle` 처럼 그 자체가 라우터·전역 상태에 결합되는 UI).

---

## 6. 라우트 (총 8개, Not Found 포함)

| 경로 | 페이지 | 보호 여부 | 설명 |
|---|---|---|---|
| `/` | `HomePage` | 공개 | 서비스 소개 + 로그인 여부에 따라 CTA 가 달라진다 |
| `/login` | `LoginPage` | 공개 | 로그인/회원가입 토글, 성공 시 직전 경로로 복귀 |
| `/books` | `BooksPage` | 공개 (로그인 시 본인 데이터만 노출) | 목록 + 카테고리 필터 + 검색 |
| `/books/new` | `BookFormPage(mode="new")` | 보호됨 | 비로그인 시 `/login` 으로 |
| `/books/:id` | `BookDetailPage` | 공개 (RLS 가 본인 외 데이터를 거른다) | 상세 보기 + 수정/삭제 진입점 |
| `/books/:id/edit` | `BookFormPage(mode="edit")` | 보호됨 | 기존 값을 미리 채워 둔 폼 |
| `/profile` | `ProfilePage` | 보호됨 | 본인 통계 (총 권수, 평균 별점, 카테고리 Top 5) |
| `*` | `NotFoundPage` | 공개 | 존재하지 않는 경로 |

5개 이상의 요구를 충분히 넘는다. 보호 라우트는 `<ProtectedRoute>` 컴포넌트가 `useAuth()` 의 세션 로딩 상태까지 고려해 처리한다 (`loading` 동안에는 `Loading` 을 보여주고, 비로그인 시 `<Navigate to="/login" state={{ from }}/>`).

---

## 7. 데이터 모델

```sql
books (
  id          uuid primary key default gen_random_uuid(),
  user_id     uuid not null references auth.users(id) on delete cascade,
  title       text not null,
  author      text not null,
  category    text not null default '기타',
  rating      int  not null default 0 check (rating between 0 and 5),
  memo        text not null default '',
  finished_on date,
  created_at  timestamptz not null default now(),
  updated_at  timestamptz not null default now()
)
```

- `user_id` 는 `auth.users` 에 외래키로 묶여 사용자가 삭제되면 함께 정리된다.
- `updated_at` 은 트리거가 자동으로 갱신한다.
- `books_user_created_idx (user_id, created_at desc)` 인덱스가 목록 조회 패턴을 그대로 받쳐 준다.
- RLS 4종(`select`/`insert`/`update`/`delete`)을 `auth.uid() = user_id` 로 통일했다.

---

## 8. 컴포넌트 설계 — 어떤 기준으로 쪼갰나

쪼갠 기준은 “**다시 쓰일 가능성**” 과 “**책임이 한 가지인가**” 두 가지다.

1. **표시 원자(Atom)** — `Button`, `Input`, `Textarea`, `Select`, `Card`, `Badge`, `Rating`. props 한두 개로 외관/동작이 바뀐다. 색·여백·패딩 같은 시각 토큰만 책임지고, 비즈니스를 모른다. `Button` 은 `variant`(`primary`/`secondary`/`ghost`/`danger`)·`size`·`loading`·`disabled` 4개의 prop 으로 모든 호출처를 커버한다.
2. **상태 표시 컴포넌트** — `Loading`, `EmptyState`, `ErrorState`. 요구사항이 “페이지마다 따로 만들지 말고 통일하라”고 명시한 부분이다. 페이지마다 다시 만들지 않고 이 셋만 호출한다. `EmptyState`/`ErrorState` 는 모두 `description`·`action` 같은 prop 으로 메시지와 후속 버튼을 주입받는다.
3. **도메인 컴포넌트** — `BookCard`, `BookForm`, `FilterBar`. 책 도메인을 알지만 데이터 fetching 은 모른다. `BookCard` 는 `book` prop 만 받아 그린다 (`React.memo` 로 동일 책에 대해서는 리렌더 회피).
4. **라우팅/세션 결합 컴포넌트** — `Layout`, `Header`, `ProtectedRoute`, `ThemeToggle`. 라우터·Context 와 묶일 수밖에 없는 단위. 페이지가 아닌 것을 분리해서 모든 라우트에 `<Outlet/>` 으로 끼워 넣는다.
5. **페이지 컴포넌트** — `pages/*`. 라우트가 바뀌면 마운트되는 단위. 데이터 훅을 호출하고, 상태 분기(`loading`/`error`/`empty`/`data`)에 맞춰 위 컴포넌트를 조합한다.

재사용 컴포넌트는 모두 prop 으로 표시/동작이 달라진다 (`Button.variant`, `Card.padding`, `Badge.tone`, `Rating.readOnly`, `BookCard.book`, `FilterBar.category/search`, …). 단순 wrapper 가 아니다.

---

## 9. 상태를 어디에 두었나 (state lifting)

상태는 “**그 상태를 동시에 보거나 바꿔야 하는 컴포넌트들의 가장 가까운 공통 조상**” 에 둔다.

- **폼 입력 값** — `BookForm` 내부의 `useState` 에 둔다. 페이지(`BookFormPage`)는 입력 도중의 값을 알 필요가 없다. 페이지는 “저장 성공 후 어디로 보낼지” 만 결정한다 (`onSubmit` 콜백). 폼 컴포넌트가 곧 입력 상태의 소유자다.
- **목록 필터/검색어** — `BooksPage` 의 `useState` 에 둔다. `FilterBar` 가 값을 표시하고 변경 이벤트를 올려 보낸다 (controlled). 필터·검색 값은 `useBooks({ category, search })` 의 인자로 내려가 fetch 의존성이 된다.
- **목록/상세 데이터, 로딩/에러** — 커스텀 훅 (`useBooks`, `useBook`) 안의 `useState`. 호출한 페이지가 `{ data, loading, error, refresh, remove }` 만 받으면 된다. 페이지 컴포넌트의 본문이 짧고 단순해진다.
- **세션(로그인 유저)** — `AuthContext` 의 전역 상태. 헤더·보호 라우트·폼 제출 시 `user_id` 주입 등 여러 위치에서 동시에 필요하므로 상향 이동시켜 Context 로 노출한다.
- **테마(라이트/다크)** — `ThemeContext` 의 전역 상태. `useEffect` 가 `document.documentElement.dataset.theme` 과 `localStorage` 양쪽을 동기화한다.

데이터 흐름은 **상태 → props 로 하향**, **이벤트 → 콜백으로 상향** 의 단방향이다. 예) `BooksPage` 가 `search` 를 들고 있고 `FilterBar` 에 props 로 내려준다. 사용자가 입력하면 `onSearchChange` 콜백이 위로 올라와 `BooksPage` 의 `setSearch` 를 호출하고, 그 결과 `useBooks` 가 다시 호출되어 목록이 갱신된다.

### props 와 state 의 구분

- **props**: 부모에서 받은, 자기 자신이 바꿀 수 없는 값. 예: `BookCard` 의 `book`, `Button` 의 `variant`/`onClick`, `EmptyState` 의 `description`.
- **state**: 컴포넌트 자기 안에서 시간에 따라 변하는 값. 예: `BookForm` 의 `values`/`errors`/`submitting`, `BooksPage` 의 `search`/`category`, `LoginPage` 의 `mode`/`email`/`password`.

같은 값이라도 “여러 형제가 동시에 보아야 한다” 라는 신호가 잡히면 부모로 끌어올려 state 로 두고, 자식에는 props 로 흘려보낸다.

---

## 10. `useEffect` 가 어디에서 어떻게 쓰였나

각 effect 의 **언제 실행되는지(의존성)** 와 **클린업** 이 명확하도록 작성했다.

| 위치 | 의존성 | 하는 일 | 클린업 |
|---|---|---|---|
| `AuthContext` | `[]` (마운트 1회) | `supabase.auth.getSession()` 한 번 + `onAuthStateChange` 구독 | 언마운트 시 `subscription.unsubscribe()` + `mounted` 가드 |
| `ThemeContext` | `[theme]` | `data-theme` 속성과 `localStorage` 를 테마 값으로 동기화 | 없음 (멱등) |
| `useBooks` 내부 | `useCallback(fetchBooks, [user, category, search])` → `useEffect(fetchBooks)` | 사용자/필터/검색이 바뀔 때마다 Supabase 재조회 | 별도 abort 안 함 (응답이 빠르고 이전 응답이 늦게 와도 같은 인자로 다시 set 되면 화면에 모순이 없음) |
| `useBook` 내부 | `useCallback(fetchBook, [id])` → `useEffect(fetchBook)` | 경로 파라미터 `id` 가 바뀔 때마다 재조회 | 없음 |
| `useDebounce` | `[value, delay]` | 입력값을 `delay` ms 후에 새 값으로 설정 | `clearTimeout` |

세 가지 원칙을 지켰다.

1. **fetch 함수는 `useCallback` 으로 묶고 그 자체를 effect 의 의존성으로 둔다.** lint 가 잡히지 않게 하면서, 의존성이 명시적으로 보인다 (`useBooks` 의 `[user, category, search]`).
2. **마운트 후 1회 구독은 클린업을 반드시 둔다.** `AuthContext` 의 `onAuthStateChange` 구독을 언마운트 시 해제하지 않으면 hot-reload 마다 리스너가 누적된다.
3. **side-effect 와 렌더링을 섞지 않는다.** Supabase 호출은 effect 또는 이벤트 핸들러에서만 일어난다.

---

## 11. 로딩 / 성공 / 실패 / 빈 상태를 UI 로 어떻게 표현했나

데이터를 받아 그리는 모든 페이지가 동일한 4분기 패턴을 따른다.

```jsx
const { data, loading, error, refresh } = useBooks(...);

if (loading) return <Loading />;
if (error)   return <ErrorState description={error.message} onRetry={refresh} />;
if (data.length === 0) {
  return <EmptyState title="표시할 데이터가 없습니다." action={<...>} />;
}
return <BookList data={data} />;
```

- **로딩**: `Loading` 컴포넌트가 회전 스피너와 “불러오는 중…” 라벨을 그린다. `aria-live="polite"` 로 보조 기술에도 알린다.
- **성공**: 데이터가 있을 때만 도메인 컴포넌트(`BookCard` 그리드, 상세 카드)를 그린다.
- **실패**: `ErrorState` 가 `onRetry` 콜백을 받으면 “다시 시도” 버튼을 노출한다. `useBooks` / `useBook` 의 `refresh` 를 그대로 넘겨 준다.
- **빈 상태**: `EmptyState` 의 `action` prop 으로 “새 책 기록” 같은 다음 행동을 제시한다. 빈 상태가 막다른 골목이 되지 않게 한다.

폼 쪽 비동기 흐름(`BookForm`)은 별도로 다음을 처리한다.

- 제출 중에는 Submit 버튼이 `loading` prop 으로 스피너 + `disabled` 가 된다 → 더블 클릭으로 중복 등록되지 않는다.
- 실패 시 상단에 `.banner` 스타일의 빨간 박스로 메시지를 띄운다.
- 필드 검증 실패는 해당 필드 바로 아래 `.error` 텍스트로 노출된다.

---

## 12. 사용자 이벤트 → 상태 → 렌더링 흐름 (3가지 구체 예)

요구사항이 “상태 변경이 렌더링 변화로 이어지는 지점이 최소 3군데” 라 했다. 실제 코드의 흐름을 그대로 짚어 둔다.

### A. 카테고리 필터 변경 → 목록 변경

1. `FilterBar` 의 `<Select>` 가 `change` 이벤트를 발생시킨다.
2. `onCategoryChange(e.target.value)` 콜백이 부모(`BooksPage`)로 올라간다.
3. `BooksPage` 의 `setCategory(...)` 가 호출되어 state 가 바뀐다.
4. `BooksPage` 가 리렌더되며 `useBooks({ category, search })` 가 새 인자로 호출된다.
5. 훅 안에서 `useCallback` 의 의존성(`category`)이 바뀌므로 `fetchBooks` 가 새로 만들어지고, `useEffect` 가 다시 실행된다.
6. Supabase 호출이 끝나면 `setData(rows)` → `BookCard` 그리드가 새 데이터로 다시 그려진다.

### B. 검색어 입력 → (디바운스) → 목록 변경

1. 사용자가 검색창에 타자 → `Input` 의 `onChange` → `BooksPage.setSearch(value)`.
2. `BooksPage` 는 매 keystroke 마다 리렌더되지만 표시되는 입력값(즉시 반영)과 fetch 트리거(디바운스된 값)를 분리해 두었다 — `useDebounce(search, 300)` 가 300ms 정지 후에만 새 값을 내보낸다.
3. 디바운스된 값이 바뀌면 다시 A의 4~6 흐름.

이렇게 “**즉시 반영해야 하는 상태**” 와 “**서버 호출을 트리거하는 상태**” 를 분리하는 것이 사용자 입력 UI 의 흔한 패턴이다.

### C. 폼 제출 성공 → 상세 페이지로 이동 + 알림

1. `BookForm.handleSubmit` 이 검증(`validate`)을 통과하면 `setSubmitting(true)` → 버튼이 즉시 스피너로 바뀐다.
2. `onSubmit(values)` 콜백이 `BookFormPage` 로 올라가 Supabase `insert` (또는 `update`) 를 호출한다.
3. 성공하면 `navigate('/books/' + newId, { replace: true })` 로 라우트가 바뀐다 → React Router 가 트리를 교체하며 `BookDetailPage` 가 마운트된다.
4. `BookDetailPage` 의 `useBook(id)` 가 의존성에 새 `id` 가 들어와 데이터를 다시 가져온다 → 상세가 그려진다.
5. 실패 시에는 `setSubmitError(message)` 만 호출하고 라우팅은 그대로 — 상단 빨간 배너가 즉시 나타난다.

### 그 외

- **삭제** → `BookDetailPage.handleDelete` → Supabase `delete` → `navigate('/books', { replace: true })` → `BooksPage` 가 다시 마운트되며 목록을 새로 가져온다.
- **로그아웃** → `Header.handleSignOut` → `signOut()` → `AuthContext` 의 `onAuthStateChange` 가 `session = null` 로 갱신 → 헤더가 “로그인” 링크로 바뀌고, 보호 라우트는 다음 진입 시 `/login` 으로 리다이렉트된다.
- **테마 토글** → `ThemeToggle` 클릭 → `toggle()` → `setTheme(...)` → `ThemeContext` 의 `useEffect` 가 `document.documentElement.dataset.theme` 을 갈아끼움 → 모든 CSS 변수가 한 번에 다크 토큰으로 전환된다.

---

## 13. 보너스 — 무엇을 했나

요구사항의 5절(보너스 과제) 세 가지를 모두 적용했다.

1. **전역 상태**
   - `AuthContext`: Supabase 세션을 `getSession()` + `onAuthStateChange` 로 받아 `{ user, session, loading, signIn, signUp, signOut }` 으로 노출. `useMemo` 로 value 객체를 안정화해 불필요한 소비자 리렌더를 막는다.
   - `ThemeContext`: 라이트/다크 토글을 localStorage 와 동기화. `prefers-color-scheme` 을 초기값으로 채택.
2. **성능 최적화**
   - `BookCard` 에 `React.memo` + 사용자 정의 비교 함수. 목록 한 칸의 props(`book`)가 그대로면 다시 그리지 않는다.
   - `useBooks` 내부의 `fetchBooks` 는 `useCallback([user, category, search])` 로 안정화 → effect 가 불필요하게 재실행되지 않음.
   - `AuthContext` 의 `signIn`/`signUp`/`signOut` 도 `useCallback`, value 는 `useMemo`.
   - 검색 입력은 `useDebounce` 로 fetch 빈도를 줄인다.
   - `BooksPage` / `ProfilePage` 의 집계(`stats`)는 `useMemo([data])` 로 데이터가 같으면 다시 계산하지 않는다.
3. **인증과 보호 라우트**
   - Supabase Auth (이메일/비밀번호)로 가입·로그인·로그아웃을 구현.
   - `<ProtectedRoute>` 가 `/books/new`, `/books/:id/edit`, `/profile` 을 감싼다. 비로그인 사용자는 `/login` 으로 보내고, `state.from` 으로 직전 경로를 기억해 로그인 직후 다시 데려간다.
   - RLS 가 서버 단에서 본인 행만 허용하므로 클라이언트 가드가 우회되어도 데이터는 새지 않는다.

---

## 14. 요구사항 충족 자기점검

| 요구 (요약) | 만족 여부 | 위치/근거 |
|---|---|---|
| React 프로젝트, 폴더 역할 분리 (pages / components / hooks·lib) | ✅ | `web/src/{pages,components,hooks,lib,contexts}` |
| 공통 레이아웃(헤더·네비) 적용 | ✅ | `Layout.jsx` 가 `<Outlet/>` 으로 모든 라우트를 감싼다 |
| 단일 핵심 데이터 CRUD | ✅ | `books` 단일 테이블, 목록·상세·등록·수정·삭제 모두 동작 |
| 최소 5개 라우트 | ✅ | 8개 (`/`, `/login`, `/books`, `/books/new`, `/books/:id`, `/books/:id/edit`, `/profile`, `*`) |
| 목록/상세 라우트 | ✅ | `/books`, `/books/:id` |
| Not Found | ✅ | `NotFoundPage` + `<Route path="*">` |
| 네비게이션 링크 | ✅ | `Layout` 의 `<NavLink>` 4개 + 페이지 내 `<Link>` 다수 |
| 8개 이상 재사용 컴포넌트 | ✅ | Button/Input/Textarea/Select/Card/Badge/Rating/Loading/EmptyState/ErrorState/FilterBar/BookCard/BookForm/ProtectedRoute/ThemeToggle/Header/Layout = 17개 |
| 페이지/UI 컴포넌트 분리 | ✅ | `pages/` 는 라우터/데이터/흐름, `components/` 는 표시 |
| 로딩/에러/빈 상태 통일 컴포넌트 | ✅ | `Loading`/`ErrorState`/`EmptyState` 세 컴포넌트만 사용 |
| controlled input | ✅ | `BookForm`, `LoginPage`, `FilterBar` 모두 `value`+`onChange` |
| 목록/상세 데이터 상태 | ✅ | `useBooks`, `useBook` |
| 로딩/에러 상태 | ✅ | 두 훅 모두 `{loading, error}` 반환 |
| 커스텀 훅으로 데이터 흐름 분리 | ✅ | `useBooks`, `useBook`, `useDebounce` |
| Supabase 기반 CRUD | ✅ | `BooksPage`(조회), `BookDetailPage`(조회/삭제), `BookFormPage`(등록/수정) |
| 폼 필수값 검증 | ✅ | `BookForm.validate` — 제목·저자 비면 제출 불가 |
| 필드 옆/상단 에러 | ✅ | `Input.error` 슬롯 + 상단 `.banner` |
| 제출 중 진행 상태 | ✅ | `Button.loading` (스피너 + `disabled`) |
| 실패 시 사용자에게 표시 | ✅ | `submitError` 배너 / `ErrorState` |
| 이벤트 → 상태 → 렌더 흐름 3+ | ✅ | §12 A/B/C + 삭제/로그아웃/테마 |
| 환경변수 분리, `.env` gitignore | ✅ | `web/.env.example`, root `.gitignore` 에 `web/.env*` |
| 배포 가이드 | ✅ | §4 Vercel 절차 |

---

## 15. 알려진 제약 / 의도적으로 안 한 것

- **TypeScript 미사용** — 요구사항이 선택이라 명시했고, 학습 초점인 React 원리(컴포넌트·상태·이벤트)를 흐리지 않기 위해 일부러 뺐다. 도입은 `vite scaffold` + 파일 확장자 변경 + 최소 타입 정의로 가능.
- **테스트 코드 없음** — 요구사항에 단위 테스트는 포함되어 있지 않고, 평가가 React 구조·데이터 흐름에 집중되어 있어 비용 대비 효과를 고려해 생략. 추후 도입한다면 Vitest + React Testing Library 가 자연스러운 선택이다.
- **이미지 업로드 / 파일 스토리지 미사용** — 책 표지·첨부를 다루지 않는다. Supabase Storage 연동은 범위를 벗어난다.
- **반응형은 최소 수준** — 헤더·네비·그리드·필터바에 한해서만 좁은 화면을 깨지지 않게 처리했다. 모바일 UX 를 본격적으로 다듬지는 않았다.
- **이메일 인증 흐름** — `signUp` 후 확인 메일 링크 흐름은 다루지 않는다. Supabase Authentication 설정에서 *Confirm email* 을 끄면 즉시 로그인 가능하다.

---

## 16. 한 줄 정리

라우팅·상태·이벤트·비동기 렌더링의 연결 고리를 한 권의 책 CRUD 라는 가장 작은 도메인 위에 올려, **React 의 동작 원리를 코드로 그대로 드러내는** 데 초점을 둔 SPA. 백엔드는 Supabase 한 줄로 끝내고, 학습 가치가 있는 모든 결정(상태 위치, 컴포넌트 분리, effect 의존성, 메모이제이션 적용 지점)을 위 절들에서 설명했다.
