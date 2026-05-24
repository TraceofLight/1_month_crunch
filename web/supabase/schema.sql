-- Reading Log — Supabase 스키마
--
-- 실행 방법:
--   Supabase 프로젝트 대시보드 → SQL Editor → 새 쿼리에 이 파일을 그대로 붙여넣고 Run.
--   인증은 Authentication → Providers → Email 을 활성화 (Confirm email 옵션을 꺼 두면 데모가 간편).

create extension if not exists "pgcrypto";

create table if not exists public.books (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  title text not null,
  author text not null,
  category text not null default '기타',
  rating int not null default 0 check (rating between 0 and 5),
  memo text not null default '',
  finished_on date,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists books_user_created_idx
  on public.books (user_id, created_at desc);

-- updated_at 자동 갱신 트리거
create or replace function public.set_updated_at()
returns trigger
language plpgsql
as $$
begin
  new.updated_at := now();
  return new;
end;
$$;

drop trigger if exists books_set_updated_at on public.books;
create trigger books_set_updated_at
  before update on public.books
  for each row execute procedure public.set_updated_at();

-- Row Level Security: 로그인한 사용자는 본인 행만 다룰 수 있다.
alter table public.books enable row level security;

drop policy if exists "own rows select" on public.books;
create policy "own rows select" on public.books
  for select using (auth.uid() = user_id);

drop policy if exists "own rows insert" on public.books;
create policy "own rows insert" on public.books
  for insert with check (auth.uid() = user_id);

drop policy if exists "own rows update" on public.books;
create policy "own rows update" on public.books
  for update using (auth.uid() = user_id) with check (auth.uid() = user_id);

drop policy if exists "own rows delete" on public.books;
create policy "own rows delete" on public.books
  for delete using (auth.uid() = user_id);
