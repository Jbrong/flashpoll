import { useCallback, useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import CopyField from '../components/CopyField';
import ErrorMessage from '../components/ErrorMessage';
import Results from '../components/Results';
import { api } from '../lib/api';
import { timeUntil } from '../lib/time';
import { usePolling } from '../lib/usePolling';
import NotFoundPage from './NotFoundPage';

export const REFRESH_MS = 5000;

const HIDDEN_RESULTS_MESSAGE = {
  after_voting: 'Results appear once you vote.',
  private: 'Results are private. Only the poll creator can see them.',
};

export default function PollPage() {
  const { pollId } = useParams();
  const [poll, setPoll] = useState(null);
  const [results, setResults] = useState(null);
  const [loadError, setLoadError] = useState(null);
  const [voteError, setVoteError] = useState(null);
  const [selected, setSelected] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  const refreshResults = useCallback(async () => {
    try {
      setResults(await api.getResults(pollId));
    } catch {
      // Keep showing the last results; the next refresh may succeed.
    }
  }, [pollId]);

  const load = useCallback(
    async (isCancelled = () => false) => {
      try {
        const data = await api.getPoll(pollId);
        if (isCancelled()) return;
        setPoll(data);
        if (data.results_available) refreshResults();
      } catch (err) {
        if (!isCancelled()) setLoadError(err);
      }
    },
    [pollId, refreshResults],
  );

  useEffect(() => {
    let cancelled = false;
    setPoll(null);
    setResults(null);
    setLoadError(null);
    load(() => cancelled);
    return () => {
      cancelled = true;
    };
  }, [load]);

  const isOpen = poll?.status === 'open';
  usePolling(refreshResults, REFRESH_MS, Boolean(isOpen && poll?.results_available));

  async function vote(e) {
    e.preventDefault();
    if (selected === null) return;
    setSubmitting(true);
    setVoteError(null);
    try {
      const response = await api.vote(pollId, selected);
      setPoll((p) => ({ ...p, has_voted: true, results_available: response.results !== null }));
      if (response.results) setResults({ status: 'open', ...response.results });
    } catch (err) {
      setVoteError(err);
      // The poll changed under us (already voted from this browser/network, or it closed).
      if (err.code === 'already_voted' || err.code === 'poll_closed') await load();
    } finally {
      setSubmitting(false);
    }
  }

  if (loadError?.status === 404) {
    return (
      <NotFoundPage
        title="Poll not found"
        message="This poll doesn't exist, or it expired and was deleted."
      />
    );
  }
  if (loadError) return <ErrorMessage error={loadError} />;
  if (!poll) return <p className="muted">Loading…</p>;

  const canVote = isOpen && !poll.has_voted;

  return (
    <div className="poll">
      <h1>{poll.question}</h1>
      <p className={`status ${poll.status}`}>
        {isOpen ? `Open · closes in ${timeUntil(poll.expires_at)}` : 'Voting has closed'}
      </p>

      {canVote && (
        <form onSubmit={vote} className="vote-form">
          <fieldset>
            <legend className="sr-only">Choose an option</legend>
            {poll.options.map((option, i) => (
              <label key={option} className={`choice ${selected === i ? 'selected' : ''}`}>
                <input
                  type="radio"
                  name="option"
                  value={i}
                  checked={selected === i}
                  onChange={() => setSelected(i)}
                />
                <span>{option}</span>
              </label>
            ))}
          </fieldset>
          <ErrorMessage error={voteError} />
          <button type="submit" className="button primary wide" disabled={selected === null || submitting}>
            {submitting ? 'Voting…' : 'Vote'}
          </button>
        </form>
      )}

      {!canVote && (
        <>
          {voteError ? (
            <ErrorMessage error={voteError} />
          ) : (
            poll.has_voted && <p className="notice">Thanks for voting!</p>
          )}
        </>
      )}

      {poll.results_available && results ? (
        <Results options={poll.options} results={results} />
      ) : (
        !poll.results_available && (
          <p className="muted">{HIDDEN_RESULTS_MESSAGE[poll.results_visibility]}</p>
        )
      )}

      {isOpen && (
        <CopyField label="Share this poll" value={`${window.location.origin}/p/${poll.poll_id}`} />
      )}
    </div>
  );
}
