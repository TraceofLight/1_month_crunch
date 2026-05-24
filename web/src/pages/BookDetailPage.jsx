import { useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { useBook } from '../hooks/useBook.js';
import { supabase } from '../lib/supabase.js';
import { Card } from '../components/Card.jsx';
import { Badge } from '../components/Badge.jsx';
import { Rating } from '../components/Rating.jsx';
import { Button } from '../components/Button.jsx';
import { Loading } from '../components/Loading.jsx';
import { ErrorState } from '../components/ErrorState.jsx';
import { EmptyState } from '../components/EmptyState.jsx';

export function BookDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { data, loading, error, refresh } = useBook(id);
  const [deleting, setDeleting] = useState(false);
  const [deleteError, setDeleteError] = useState(null);

  if (loading) return <Loading />;
  if (error) return <ErrorState description={error.message} onRetry={refresh} />;
  if (!data) {
    return (
      <EmptyState
        title="찾을 수 없는 책입니다."
        description="다른 사용자의 데이터이거나 이미 삭제되었을 수 있다."
        action={
          <Link to="/books">
            <Button size="sm" variant="secondary">목록으로</Button>
          </Link>
        }
      />
    );
  }

  const handleDelete = async () => {
    if (!window.confirm('이 기록을 삭제할까요? 되돌릴 수 없다.')) return;
    setDeleting(true);
    setDeleteError(null);
    const { error: err } = await supabase.from('books').delete().eq('id', id);
    setDeleting(false);
    if (err) {
      setDeleteError(err.message);
      return;
    }
    navigate('/books', { replace: true });
  };

  return (
    <article>
      <div className="row between" style={{ marginBottom: 12 }}>
        <Link to="/books" className="link-back" style={{ color: 'var(--text-muted)' }}>
          ← 목록으로
        </Link>
        <div className="row" style={{ gap: 8 }}>
          <Link to={`/books/${id}/edit`}>
            <Button variant="secondary" size="sm">수정</Button>
          </Link>
          <Button variant="danger" size="sm" onClick={handleDelete} loading={deleting}>
            삭제
          </Button>
        </div>
      </div>

      {deleteError ? <div className="banner" style={{ marginBottom: 12 }}>{deleteError}</div> : null}

      <Card padding="lg">
        <div className="row between" style={{ alignItems: 'flex-start' }}>
          <div>
            <h1 className="page-title" style={{ marginBottom: 4 }}>{data.title}</h1>
            <p className="page-subtitle" style={{ marginBottom: 8 }}>{data.author}</p>
            <Rating value={data.rating} readOnly />
          </div>
          <Badge tone="accent">{data.category}</Badge>
        </div>

        <hr style={{ border: 0, borderTop: '1px solid var(--border)', margin: '20px 0' }} />

        <dl style={{ display: 'grid', gridTemplateColumns: '120px 1fr', rowGap: 8, columnGap: 12, margin: 0 }}>
          <dt style={{ color: 'var(--text-muted)' }}>다 읽은 날</dt>
          <dd style={{ margin: 0 }}>{data.finished_on ?? '—'}</dd>
          <dt style={{ color: 'var(--text-muted)' }}>등록일</dt>
          <dd style={{ margin: 0 }}>{new Date(data.created_at).toLocaleDateString('ko-KR')}</dd>
          <dt style={{ color: 'var(--text-muted)' }}>메모</dt>
          <dd style={{ margin: 0, whiteSpace: 'pre-wrap' }}>{data.memo || '—'}</dd>
        </dl>
      </Card>
    </article>
  );
}
