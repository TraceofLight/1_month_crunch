import { useMemo } from 'react';
import { useAuth } from '../contexts/AuthContext.jsx';
import { useBooks } from '../hooks/useBooks.js';
import { useTheme } from '../contexts/ThemeContext.jsx';
import { Card } from '../components/Card.jsx';
import { Badge } from '../components/Badge.jsx';
import { Loading } from '../components/Loading.jsx';
import { ErrorState } from '../components/ErrorState.jsx';

export function ProfilePage() {
  const { user } = useAuth();
  const { theme } = useTheme();
  const { data, loading, error, refresh } = useBooks();

  const stats = useMemo(() => {
    if (!data.length) return null;
    const byCategory = data.reduce((acc, b) => {
      acc[b.category] = (acc[b.category] ?? 0) + 1;
      return acc;
    }, {});
    const avg = data.reduce((sum, b) => sum + (b.rating || 0), 0) / data.length;
    const top = Object.entries(byCategory).sort((a, b) => b[1] - a[1]).slice(0, 5);
    return { count: data.length, avg: avg.toFixed(1), top };
  }, [data]);

  if (loading) return <Loading />;
  if (error) return <ErrorState description={error.message} onRetry={refresh} />;

  return (
    <section className="stack">
      <h1 className="page-title">프로필</h1>
      <p className="page-subtitle">로그인한 본인 계정의 요약 정보다.</p>

      <Card padding="lg">
        <div className="stack" style={{ gap: 8 }}>
          <div className="row" style={{ gap: 12 }}>
            <strong style={{ width: 120, color: 'var(--text-muted)' }}>이메일</strong>
            <span>{user?.email}</span>
          </div>
          <div className="row" style={{ gap: 12 }}>
            <strong style={{ width: 120, color: 'var(--text-muted)' }}>사용자 ID</strong>
            <code style={{ fontSize: 12 }}>{user?.id}</code>
          </div>
          <div className="row" style={{ gap: 12 }}>
            <strong style={{ width: 120, color: 'var(--text-muted)' }}>테마</strong>
            <Badge>{theme}</Badge>
          </div>
        </div>
      </Card>

      <Card padding="lg">
        <h2 style={{ marginTop: 0, fontSize: 18 }}>독서 통계</h2>
        {stats ? (
          <div className="stack">
            <div className="row" style={{ gap: 24 }}>
              <div>
                <div style={{ color: 'var(--text-muted)', fontSize: 13 }}>총 권수</div>
                <div style={{ fontSize: 28, fontWeight: 700 }}>{stats.count}</div>
              </div>
              <div>
                <div style={{ color: 'var(--text-muted)', fontSize: 13 }}>평균 별점</div>
                <div style={{ fontSize: 28, fontWeight: 700 }}>{stats.avg}</div>
              </div>
            </div>
            <div>
              <div style={{ color: 'var(--text-muted)', fontSize: 13, marginBottom: 8 }}>
                카테고리 Top 5
              </div>
              <div className="row" style={{ flexWrap: 'wrap', gap: 6 }}>
                {stats.top.map(([cat, n]) => (
                  <Badge key={cat} tone="accent">
                    {cat} · {n}
                  </Badge>
                ))}
              </div>
            </div>
          </div>
        ) : (
          <p style={{ margin: 0, color: 'var(--text-muted)' }}>아직 기록이 없다.</p>
        )}
      </Card>
    </section>
  );
}
