import { NavLink, Outlet } from 'react-router-dom';
import { Header } from './Header.jsx';
import './Layout.css';

export function Layout() {
  return (
    <div className="app-shell">
      <Header />
      <nav className="nav">
        <div className="container nav__inner">
          <NavLink to="/" end className={({ isActive }) => 'nav__link' + (isActive ? ' is-active' : '')}>
            홈
          </NavLink>
          <NavLink to="/books" className={({ isActive }) => 'nav__link' + (isActive ? ' is-active' : '')}>
            내 책장
          </NavLink>
          <NavLink to="/books/new" className={({ isActive }) => 'nav__link' + (isActive ? ' is-active' : '')}>
            새 기록
          </NavLink>
          <NavLink to="/profile" className={({ isActive }) => 'nav__link' + (isActive ? ' is-active' : '')}>
            프로필
          </NavLink>
        </div>
      </nav>
      <main className="page">
        <div className="container">
          <Outlet />
        </div>
      </main>
      <footer className="footer">
        <div className="container">
          <small>Reading Log · React + Supabase 학습용 SPA</small>
        </div>
      </footer>
    </div>
  );
}
