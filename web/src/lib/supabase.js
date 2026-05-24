import { createClient } from '@supabase/supabase-js';

const url = import.meta.env.VITE_SUPABASE_URL;
const anonKey = import.meta.env.VITE_SUPABASE_ANON_KEY;

if (!url || !anonKey) {
  // 환경변수가 누락된 상태로 빌드/실행되는 사고를 막기 위한 명시적 경고.
  // .env.example 을 참고해 .env 파일을 채우거나 Vercel 환경변수를 등록한다.
  console.warn(
    '[supabase] VITE_SUPABASE_URL / VITE_SUPABASE_ANON_KEY 가 설정되지 않았다. ' +
      '데이터 조회/저장이 모두 실패한다.',
  );
}

export const supabase = createClient(url ?? '', anonKey ?? '', {
  auth: {
    persistSession: true,
    autoRefreshToken: true,
  },
});

export const CATEGORIES = ['소설', '에세이', '경영/경제', '과학/기술', '인문/사회', '자기계발', '기타'];
