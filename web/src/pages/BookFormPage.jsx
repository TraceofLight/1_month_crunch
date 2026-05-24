import { useNavigate, useParams } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext.jsx';
import { useBook } from '../hooks/useBook.js';
import { supabase } from '../lib/supabase.js';
import { BookForm } from '../components/BookForm.jsx';
import { Card } from '../components/Card.jsx';
import { Loading } from '../components/Loading.jsx';
import { ErrorState } from '../components/ErrorState.jsx';

export function BookFormPage({ mode = 'new' }) {
  const { id } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();
  const isEdit = mode === 'edit';

  const { data, loading, error, refresh } = useBook(isEdit ? id : null);

  if (isEdit && loading) return <Loading />;
  if (isEdit && error) return <ErrorState description={error.message} onRetry={refresh} />;

  const initial = isEdit && data
    ? {
        title: data.title,
        author: data.author,
        category: data.category,
        rating: data.rating,
        memo: data.memo,
        finished_on: data.finished_on ?? '',
      }
    : undefined;

  const handleSubmit = async (values) => {
    if (isEdit) {
      const { error: err } = await supabase
        .from('books')
        .update(values)
        .eq('id', id);
      if (err) throw err;
      navigate(`/books/${id}`, { replace: true });
    } else {
      const { data: inserted, error: err } = await supabase
        .from('books')
        .insert({ ...values, user_id: user.id })
        .select('id')
        .single();
      if (err) throw err;
      navigate(`/books/${inserted.id}`, { replace: true });
    }
  };

  return (
    <section style={{ maxWidth: 640, margin: '0 auto' }}>
      <h1 className="page-title">{isEdit ? '기록 수정' : '새 책 기록'}</h1>
      <p className="page-subtitle">
        제목과 저자는 필수다. 별점은 클릭으로 조절할 수 있다.
      </p>
      <Card padding="lg">
        <BookForm
          initialValue={initial}
          onSubmit={handleSubmit}
          onCancel={() => navigate(-1)}
          submitLabel={isEdit ? '수정 저장' : '등록'}
        />
      </Card>
    </section>
  );
}
