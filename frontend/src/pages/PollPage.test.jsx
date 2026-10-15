import { act, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { apiError, mockApi } from '../test/mockApi';
import { renderAt } from '../test/renderAt';

const basePoll = {
  poll_id: 'abc12345',
  question: 'Lunch?',
  options: ['Pizza', 'Tacos', 'Salad'],
  vote_control: 'one_per_browser',
  results_visibility: 'live',
  created_at: '2026-10-15T18:00:00Z',
  expires_at: '2099-01-01T00:00:00Z',
  status: 'open',
  has_voted: false,
  results_available: true,
};
const results = { status: 'open', total_votes: 4, counts: [1, 3, 0] };

const meter = (name) => screen.getByRole('meter', { name });

describe('PollPage', () => {
  afterEach(() => vi.useRealTimers());

  it('shows live results and votes with the voter token', async () => {
    const api = mockApi({
      'GET /api/polls/abc12345': basePoll,
      'GET /api/polls/abc12345/results': results,
      'POST /api/polls/abc12345/votes': { results: { total_votes: 5, counts: [2, 3, 0] } },
    });
    const user = userEvent.setup();
    renderAt('/p/abc12345');

    expect(await screen.findByRole('heading', { name: 'Lunch?' })).toBeInTheDocument();
    expect(await screen.findByText('4 votes')).toBeInTheDocument();
    expect(meter('Tacos')).toHaveAttribute('aria-valuenow', '75');

    expect(screen.getByRole('button', { name: 'Vote' })).toBeDisabled();
    await user.click(screen.getByRole('radio', { name: 'Pizza' }));
    await user.click(screen.getByRole('button', { name: 'Vote' }));

    expect(await screen.findByText('Thanks for voting!')).toBeInTheDocument();
    expect(screen.getByText('5 votes')).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Vote' })).not.toBeInTheDocument();

    const voteRequest = api.requests.find((r) => r.method === 'POST');
    expect(voteRequest.body).toEqual({ option_index: 0 });
    expect(voteRequest.headers['X-Voter-Token']).toMatch(/^[\w-]{16,64}$/);
    // The same token is reused across requests.
    expect(api.requests[0].headers['X-Voter-Token']).toBe(voteRequest.headers['X-Voter-Token']);
  });

  it('hides results until voting when visibility is after_voting', async () => {
    mockApi({
      'GET /api/polls/abc12345': {
        ...basePoll,
        results_visibility: 'after_voting',
        results_available: false,
      },
      'POST /api/polls/abc12345/votes': { results: { total_votes: 1, counts: [0, 1, 0] } },
    });
    const user = userEvent.setup();
    renderAt('/p/abc12345');

    expect(await screen.findByText('Results appear once you vote.')).toBeInTheDocument();
    expect(screen.queryByRole('meter')).not.toBeInTheDocument();

    await user.click(await screen.findByRole('radio', { name: 'Tacos' }));
    await user.click(screen.getByRole('button', { name: 'Vote' }));
    expect(await screen.findByText('1 vote')).toBeInTheDocument();
  });

  it('remembers a previous vote', async () => {
    mockApi({
      'GET /api/polls/abc12345': { ...basePoll, has_voted: true },
      'GET /api/polls/abc12345/results': results,
    });
    renderAt('/p/abc12345');
    expect(await screen.findByText('Thanks for voting!')).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Vote' })).not.toBeInTheDocument();
  });

  it('explains an already_voted rejection', async () => {
    mockApi({
      'GET /api/polls/abc12345': basePoll,
      'GET /api/polls/abc12345/results': results,
      'POST /api/polls/abc12345/votes': apiError(
        409,
        'already_voted',
        'You have already voted on this poll',
      ),
    });
    const user = userEvent.setup();
    renderAt('/p/abc12345');
    await user.click(await screen.findByRole('radio', { name: 'Salad' }));
    await user.click(screen.getByRole('button', { name: 'Vote' }));
    expect(await screen.findByRole('alert')).toHaveTextContent('You have already voted');
  });

  it('shows a closed poll without the vote form', async () => {
    mockApi({
      'GET /api/polls/abc12345': { ...basePoll, status: 'closed' },
      'GET /api/polls/abc12345/results': { ...results, status: 'closed' },
    });
    renderAt('/p/abc12345');
    expect(await screen.findByText('Voting has closed')).toBeInTheDocument();
    expect(await screen.findByText('4 votes')).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Vote' })).not.toBeInTheDocument();
  });

  it('says when results are private', async () => {
    mockApi({
      'GET /api/polls/abc12345': {
        ...basePoll,
        results_visibility: 'private',
        results_available: false,
      },
    });
    renderAt('/p/abc12345');
    expect(await screen.findByText(/Results are private/)).toBeInTheDocument();
  });

  it('shows not found for a missing or expired poll', async () => {
    mockApi({ 'GET /api/polls/gone1234': apiError(404, 'poll_not_found') });
    renderAt('/p/gone1234');
    expect(await screen.findByRole('heading', { name: 'Poll not found' })).toBeInTheDocument();
  });

  it('refreshes live results every few seconds', async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    let total = 4;
    mockApi({
      'GET /api/polls/abc12345': basePoll,
      'GET /api/polls/abc12345/results': () => ({ ...results, total_votes: total }),
    });
    renderAt('/p/abc12345');
    expect(await screen.findByText('4 votes')).toBeInTheDocument();

    total = 9;
    await act(() => vi.advanceTimersByTimeAsync(5000));
    expect(await screen.findByText('9 votes')).toBeInTheDocument();
  });
});
