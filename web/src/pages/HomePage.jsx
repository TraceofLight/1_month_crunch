import { Link } from 'react-router-dom';
import { Card } from '../components/Card.jsx';
import { Button } from '../components/Button.jsx';
import { useAuth } from '../contexts/AuthContext.jsx';

export function HomePage() {
  const { user } = useAuth();
  return (
    <section className="stack">
      <h1 className="page-title">읽은 책을 가볍게 기록한다.</h1>
      <p className="page-subtitle">
        제목 · 저자 · 별점 · 한 줄 메모만 남겨도, 나중에 다시 들춰볼 때 한 권의 가치가 분명해진다.
      </p>
      <div className="row" style={{ marginTop: 8 }}>
        {user ? (
          <>
            <Link to="/books">
              <Button>내 책장 열기</Button>
            </Link>
            <Link to="/books/new">
              <Button variant="secondary">새 책 기록</Button>
            </Link>
          </>
        ) : (
          <>
            <Link to="/login">
              <Button>로그인해서 시작</Button>
            </Link>
            <Link to="/books">
              <Button variant="ghost">먼저 둘러보기</Button>
            </Link>
          </>
        )}
      </div>

      <div className="book-grid" style={{ marginTop: 24 }}>
        <Card>
          <h3 style={{ margin: '0 0 6px' }}>📚 단일 데이터 CRUD</h3>
          <p style={{ margin: 0, color: 'var(--text-muted)', fontSize: 14 }}>
            책 한 권을 등록 · 수정 · 삭제하며 React의 상태 흐름을 그대로 손에 익힌다.
          </p>
        </Card>
        <Card>
          <h3 style={{ margin: '0 0 6px' }}>🧩 컴포넌트 분리</h3>
          <p style={{ margin: 0, color: 'var(--text-muted)', fontSize: 14 }}>
            로딩/에러/빈 상태와 폼 UX를 재사용 컴포넌트로 통일해 페이지마다 다시 만들지 않는다.
          </p>
        </Card>
        <Card>
          <h3 style={{ margin: '0 0 6px' }}>🔐 본인 데이터만</h3>
          <p style={{ margin: 0, color: 'var(--text-muted)', fontSize: 14 }}>
            Supabase RLS 로 본인 행만 다룰 수 있게 분리되어 있다.
          </p>
        </Card>
      </div>
    </section>
  );
}
