import { Link } from 'react-router-dom';

export default function NotFoundPage({
  title = 'Page not found',
  message = "There's nothing here.",
}) {
  return (
    <div className="empty-state">
      <h1>{title}</h1>
      <p className="muted">{message}</p>
      <Link to="/" className="button">
        Create a poll
      </Link>
    </div>
  );
}
