import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext.jsx';
import { Button } from './Button.jsx';
import { ThemeToggle } from './ThemeToggle.jsx';

export function Header() {
  const { user, signOut } = useAuth();
  const navigate = useNavigate();

  const handleSignOut = async () => {
    await signOut();
    navigate('/');
  };

  return (
    <header className="header">
      <div className="container header__inner">
        <Link to="/" className="header__brand">
          📖 Reading Log
        </Link>
        <div className="row">
          <ThemeToggle />
          {user ? (
            <>
              <span className="header__email" title={user.email}>{user.email}</span>
              <Button variant="secondary" size="sm" onClick={handleSignOut}>
                로그아웃
              </Button>
            </>
          ) : (
            <Link to="/login">
              <Button variant="secondary" size="sm">로그인</Button>
            </Link>
          )}
        </div>
      </div>
    </header>
  );
}
