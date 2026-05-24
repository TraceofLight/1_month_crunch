import { useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { useBooks } from '../hooks/useBooks.js';
import { useDebounce } from '../hooks/useDebounce.js';
import { FilterBar } from '../components/FilterBar.jsx';
import { BookCard } from '../components/BookCard.jsx';
import { Loading } from '../components/Loading.jsx';
import { EmptyState } from '../components/EmptyState.jsx';
import { ErrorState } from '../components/ErrorState.jsx';
import { Button } from '../components/Button.jsx';

export function BooksPage() {
  const [category, setCategory] = useState('all');
  const [search, setSearch] = useState('');
  const debouncedSearch = useDebounce(search, 300);
  const { data, loading, error, refresh } = useBooks({ category, search: debouncedSearch });

  const stats = useMemo(() => {
    if (!data.length) return null;
    const avg = data.reduce((sum, b) => sum + (b.rating || 0), 0) / data.length;
    return { count: data.length, avg: avg.toFixed(1) };
  }, [data]);

  return (
    <section>
      <div className="row between" style={{ marginBottom: 8 }}>
        <div>
          <h1 className="page-title">내 책장</h1>
          <p className="page-subtitle">
            {stats
              ? `총 ${stats.count}권 · 평균 별점 ${stats.avg}`
              : '아직 등록된 책이 없다.'}
          </p>
        </div>
        <Link to="/books/new">
          <Button>+ 새 책 기록</Button>
        </Link>
      </div>

      <FilterBar
        category={category}
        onCategoryChange={setCategory}
        search={search}
        onSearchChange={setSearch}
      />

      {loading ? (
        <Loading />
      ) : error ? (
        <ErrorState description={error.message} onRetry={refresh} />
      ) : data.length === 0 ? (
        <EmptyState
          title="표시할 데이터가 없습니다."
          description={search || category !== 'all' ? '검색 조건을 바꿔 보세요.' : '첫 번째 책을 기록해 보세요.'}
          action={
            <Link to="/books/new">
              <Button size="sm">새 책 기록</Button>
            </Link>
          }
        />
      ) : (
        <div className="book-grid">
          {data.map((book) => (
            <BookCard key={book.id} book={book} />
          ))}
        </div>
      )}
    </section>
  );
}
