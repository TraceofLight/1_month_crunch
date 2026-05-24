import { Link } from 'react-router-dom';
import { Button } from '../components/Button.jsx';

export function NotFoundPage() {
  return (
    <section className="stack" style={{ alignItems: 'center', textAlign: 'center', padding: '40px 0' }}>
      <h1 className="page-title" style={{ fontSize: 40 }}>404</h1>
      <p className="page-subtitle">요청한 페이지를 찾을 수 없다.</p>
      <Link to="/">
        <Button>홈으로</Button>
      </Link>
    </section>
  );
}
