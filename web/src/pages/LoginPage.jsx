import { useState } from 'react';
import { Navigate, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext.jsx';
import { Card } from '../components/Card.jsx';
import { Input } from '../components/Input.jsx';
import { Button } from '../components/Button.jsx';

export function LoginPage() {
  const { signIn, signUp, user } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const redirectTo = location.state?.from || '/books';

  const [mode, setMode] = useState('signIn');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);
  const [info, setInfo] = useState(null);

  // 이미 로그인한 사용자가 다시 들어오면 목록으로 보낸다.
  // 렌더 도중 navigate 를 호출하면 경고가 나므로 Navigate 컴포넌트로 처리.
  if (user) {
    return <Navigate to={redirectTo} replace />;
  }

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setInfo(null);
    if (!email.trim() || !password) {
      setError('이메일과 비밀번호를 모두 입력해 주세요.');
      return;
    }
    setSubmitting(true);
    try {
      if (mode === 'signIn') {
        await signIn(email.trim(), password);
        navigate(redirectTo, { replace: true });
      } else {
        await signUp(email.trim(), password);
        setInfo('가입을 완료했습니다. 곧바로 로그인해 보세요.');
        setMode('signIn');
      }
    } catch (err) {
      setError(err.message || '요청에 실패했습니다.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <section style={{ maxWidth: 420, margin: '0 auto' }}>
      <h1 className="page-title">{mode === 'signIn' ? '로그인' : '회원가입'}</h1>
      <p className="page-subtitle">
        본인 데이터만 보이도록 Supabase Auth 로 보호되어 있다.
      </p>
      <Card padding="lg">
        <form onSubmit={handleSubmit} className="form-grid" noValidate>
          {error ? <div className="banner">{error}</div> : null}
          {info ? <div className="banner" style={{ background: 'var(--surface-2)', color: 'var(--text)' }}>{info}</div> : null}
          <Input
            label="이메일"
            name="email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
          <Input
            label="비밀번호"
            name="password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            help="6자 이상"
          />
          <Button type="submit" loading={submitting} disabled={submitting}>
            {mode === 'signIn' ? '로그인' : '회원가입'}
          </Button>
        </form>
        <div className="row" style={{ marginTop: 14, justifyContent: 'center' }}>
          <button
            type="button"
            className="link-btn"
            onClick={() => {
              setError(null);
              setInfo(null);
              setMode((m) => (m === 'signIn' ? 'signUp' : 'signIn'));
            }}
            style={{
              background: 'none',
              border: 0,
              color: 'var(--accent)',
              cursor: 'pointer',
              fontWeight: 600,
            }}
          >
            {mode === 'signIn' ? '계정이 없으신가요? 가입하기' : '이미 계정이 있으신가요? 로그인'}
          </button>
        </div>
      </Card>
    </section>
  );
}
