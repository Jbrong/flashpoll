import { screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it } from 'vitest';
import { apiError, mockApi } from '../test/mockApi';
import { renderAt } from '../test/renderAt';

const adminPoll = {
  poll_id: 'abc12345',
  question: 'Lunch?',
  options: ['Pizza', 'Tacos'],
  vote_control: 'one_per_browser',
  results_visibility: 'private',
  created_at: '2026-10-15T18:00:00Z',
  expires_at: '2099-01-01T00:00:00Z',
  status: 'open',
  has_voted: false,
  results_available: false,
  results: { total_votes: 3, counts: [2, 1] },
  deletes_at: '2099-01-02T00:00:00Z',
};

describe('AdminPage', () => {
  it('loads with the token from the URL fragment, sent as X-Admin-Token', async () => {
    const api = mockApi({ 'GET /api/admin/poll': adminPoll });
    renderAt('/admin#secret-token');

    expect(await screen.findByRole('heading', { name: 'Lunch?' })).toBeInTheDocument();
    expect(screen.getByText('3 votes')).toBeInTheDocument();
    expect(screen.getByText('Private')).toBeInTheDocument();
    expect(api.requests[0]!.headers['X-Admin-Token']).toBe('secret-token');
  });

  it('rejects a missing token without calling the API', async () => {
    const api = mockApi({});
    renderAt('/admin');
    expect(screen.getByRole('heading', { name: 'Admin link not valid' })).toBeInTheDocument();
    expect(api).not.toHaveBeenCalled();
  });

  it('rejects an invalid token', async () => {
    mockApi({ 'GET /api/admin/poll': apiError(401, 'unauthorized') });
    renderAt('/admin#wrong');
    expect(
      await screen.findByRole('heading', { name: 'Admin link not valid' }),
    ).toBeInTheDocument();
  });

  it('closes voting', async () => {
    mockApi({
      'GET /api/admin/poll': adminPoll,
      'POST /api/admin/poll/close': { ...adminPoll, status: 'closed' },
    });
    const user = userEvent.setup();
    renderAt('/admin#secret-token');
    await user.click(await screen.findByRole('button', { name: 'Close voting now' }));
    expect(await screen.findByText('Voting has closed')).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Close voting now' })).not.toBeInTheDocument();
  });

  it('deletes only after confirmation', async () => {
    const api = mockApi({
      'GET /api/admin/poll': adminPoll,
      'DELETE /api/admin/poll': { status: 204 },
    });
    const user = userEvent.setup();
    renderAt('/admin#secret-token');

    await user.click(await screen.findByRole('button', { name: 'Delete poll' }));
    await user.click(screen.getByRole('button', { name: 'Cancel' }));
    expect(api.requests.some((r) => r.method === 'DELETE')).toBe(false);

    await user.click(screen.getByRole('button', { name: 'Delete poll' }));
    await user.click(screen.getByRole('button', { name: 'Yes, delete forever' }));
    expect(await screen.findByRole('heading', { name: 'Poll deleted' })).toBeInTheDocument();
    expect(api.requests.at(-1)).toMatchObject({ method: 'DELETE', path: '/api/admin/poll' });
  });
});
