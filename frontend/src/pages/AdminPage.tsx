import { useCallback, useEffect, useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import CopyField from '../components/CopyField';
import ErrorMessage from '../components/ErrorMessage';
import Results from '../components/Results';
import { ApiError, api, toError } from '../lib/api';
import { VISIBILITY_LABELS, VOTE_CONTROL_LABELS } from '../lib/labels';
import { formatDateTime, timeUntil } from '../lib/time';
import type { AdminPoll } from '../lib/types';
import { usePolling } from '../lib/usePolling';
import NotFoundPage from './NotFoundPage';
import { REFRESH_MS } from './PollPage';

export default function AdminPage() {
  // The token lives in the URL fragment so it is never sent to the server (docs/spec.md, 1.2).
  const token = useLocation().hash.slice(1);
  const [poll, setPoll] = useState<AdminPoll | null>(null);
  const [error, setError] = useState<Error | null>(null);
  const [actionError, setActionError] = useState<Error | null>(null);
  const [busy, setBusy] = useState(false);
  const [confirmingDelete, setConfirmingDelete] = useState(false);
  const [deleted, setDeleted] = useState(false);

  const load = useCallback(async () => {
    try {
      setPoll(await api.getAdminPoll(token));
      setError(null);
    } catch (err) {
      setError(toError(err));
    }
  }, [token]);

  useEffect(() => {
    if (token) load();
  }, [token, load]);

  usePolling(load, REFRESH_MS, poll?.status === 'open' && !deleted);

  async function run(action: () => Promise<void>) {
    setBusy(true);
    setActionError(null);
    try {
      await action();
    } catch (err) {
      setActionError(toError(err));
    } finally {
      setBusy(false);
    }
  }

  const closePoll = () => run(async () => setPoll(await api.closePoll(token)));
  const deletePoll = () =>
    run(async () => {
      await api.deletePoll(token);
      setDeleted(true);
    });

  if (!token || (error instanceof ApiError && (error.status === 401 || error.status === 404))) {
    return (
      <NotFoundPage
        title="Admin link not valid"
        message="This admin link is incomplete, or the poll has been deleted."
      />
    );
  }
  if (deleted) {
    return (
      <div className="empty-state">
        <h1>Poll deleted</h1>
        <p className="muted">The poll and all its votes are gone for good.</p>
        <Link to="/" className="button">
          Create a poll
        </Link>
      </div>
    );
  }
  if (error) return <ErrorMessage error={error} />;
  if (!poll) return <p className="muted">Loading…</p>;

  const isOpen = poll.status === 'open';
  const shareUrl = `${window.location.origin}/p/${poll.poll_id}`;

  return (
    <div className="admin">
      <p className="eyebrow">Admin</p>
      <h1>{poll.question}</h1>
      <p className={`status ${poll.status}`}>
        {isOpen ? `Open · closes in ${timeUntil(poll.expires_at)}` : 'Voting has closed'}
      </p>

      <Results options={poll.options} results={poll.results} />

      <dl className="details">
        <div>
          <dt>Who can vote</dt>
          <dd>{VOTE_CONTROL_LABELS[poll.vote_control]}</dd>
        </div>
        <div>
          <dt>Who sees results</dt>
          <dd>{VISIBILITY_LABELS[poll.results_visibility]}</dd>
        </div>
        <div>
          <dt>{isOpen ? 'Closes' : 'Closed'}</dt>
          <dd>{formatDateTime(poll.expires_at)}</dd>
        </div>
        <div>
          <dt>Auto-deletes</dt>
          <dd>{formatDateTime(poll.deletes_at)}</dd>
        </div>
      </dl>

      <CopyField label="Share link" value={shareUrl} />

      <ErrorMessage error={actionError} />
      <div className="actions">
        {isOpen && (
          <button type="button" className="button secondary" onClick={closePoll} disabled={busy}>
            Close voting now
          </button>
        )}
        {confirmingDelete ? (
          <>
            <button type="button" className="button danger" onClick={deletePoll} disabled={busy}>
              Yes, delete forever
            </button>
            <button
              type="button"
              className="button secondary"
              onClick={() => setConfirmingDelete(false)}
              disabled={busy}
            >
              Cancel
            </button>
          </>
        ) : (
          <button
            type="button"
            className="button danger-outline"
            onClick={() => setConfirmingDelete(true)}
            disabled={busy}
          >
            Delete poll
          </button>
        )}
      </div>
    </div>
  );
}
