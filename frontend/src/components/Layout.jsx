import { Link, Outlet } from 'react-router-dom';

export default function Layout() {
  return (
    <div className="shell">
      <header className="site-header">
        <Link to="/" className="brand" aria-label="Flashpoll home">
          <img src="/logo.png" alt="Flashpoll" width="160" height="36" />
        </Link>
      </header>
      <main className="card">
        <Outlet />
      </main>
      <footer className="site-footer">
        No accounts. Polls delete themselves after they close.
      </footer>
    </div>
  );
}
