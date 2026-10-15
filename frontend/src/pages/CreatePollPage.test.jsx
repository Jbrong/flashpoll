import { screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it } from 'vitest';
import { apiError, mockApi } from '../test/mockApi';
import { renderAt } from '../test/renderAt';

const created = {
  poll_id: 'abc12345',
  admin_token: 'secret-token',
  share_url: 'https://flashpoll.dev/p/abc12345',
  admin_url: 'https://flashpoll.dev/admin#secret-token',
  expires_at: '2026-10-16T18:00:00Z',
};

async function fillBasics(user) {
  await user.type(screen.getByLabelText('Question'), '  Lunch?  ');
  await user.type(screen.getByLabelText('Option 1'), 'Pizza');
  await user.type(screen.getByLabelText('Option 2'), 'Tacos');
}

describe('CreatePollPage', () => {
  it('creates a poll and shows the share and admin links', async () => {
    const api = mockApi({ 'POST /api/polls': { status: 201, body: created } });
    const user = userEvent.setup();
    renderAt('/');

    await fillBasics(user);
    await user.click(screen.getByLabelText('1 hour'));
    await user.click(screen.getByText('After voting'));
    await user.click(screen.getByText('One per network'));
    await user.click(screen.getByRole('button', { name: 'Create poll' }));

    expect(await screen.findByText('Your poll is live')).toBeInTheDocument();
    expect(api.requests[0].body).toEqual({
      question: 'Lunch?',
      options: ['Pizza', 'Tacos'],
      expires_in_minutes: 60,
      vote_control: 'one_per_ip',
      results_visibility: 'after_voting',
    });
    expect(screen.getByLabelText('Share link')).toHaveValue(created.share_url);
    expect(screen.getByLabelText('Admin link')).toHaveValue(created.admin_url);
  });

  it('defaults to one day, one per browser, live results', async () => {
    const api = mockApi({ 'POST /api/polls': { status: 201, body: created } });
    const user = userEvent.setup();
    renderAt('/');
    await fillBasics(user);
    await user.click(screen.getByRole('button', { name: 'Create poll' }));
    await screen.findByText('Your poll is live');
    expect(api.requests[0].body).toMatchObject({
      expires_in_minutes: 1440,
      vote_control: 'one_per_browser',
      results_visibility: 'live',
    });
  });

  it('adds options up to six and removes down to two', async () => {
    mockApi({});
    const user = userEvent.setup();
    renderAt('/');

    expect(screen.queryByLabelText('Remove option 1')).not.toBeInTheDocument();
    for (let i = 0; i < 4; i += 1) await user.click(screen.getByText('+ Add option'));
    expect(screen.getByLabelText('Option 6')).toBeInTheDocument();
    expect(screen.queryByText('+ Add option')).not.toBeInTheDocument();

    for (let i = 0; i < 4; i += 1) await user.click(screen.getByLabelText('Remove option 1'));
    expect(screen.queryByLabelText('Option 3')).not.toBeInTheDocument();
    expect(screen.queryByLabelText('Remove option 1')).not.toBeInTheDocument();
  });

  it('converts a custom expiry to minutes', async () => {
    const api = mockApi({ 'POST /api/polls': { status: 201, body: created } });
    const user = userEvent.setup();
    renderAt('/');
    await fillBasics(user);
    await user.click(screen.getByLabelText('Custom'));
    await user.clear(screen.getByLabelText('Custom duration'));
    await user.type(screen.getByLabelText('Custom duration'), '3');
    await user.selectOptions(screen.getByLabelText('Custom duration unit'), 'days');
    await user.click(screen.getByRole('button', { name: 'Create poll' }));
    await screen.findByText('Your poll is live');
    expect(api.requests[0].body.expires_in_minutes).toBe(3 * 1440);
  });

  it.each([
    ['an empty question', async () => {}, 'Enter a question.'],
    [
      'duplicate options',
      async (user) => {
        await user.type(screen.getByLabelText('Question'), 'Q');
        await user.type(screen.getByLabelText('Option 1'), 'Same');
        await user.type(screen.getByLabelText('Option 2'), 'same');
      },
      'Each option must be different.',
    ],
    [
      'a custom expiry under 15 minutes',
      async (user) => {
        await fillBasics(user);
        await user.click(screen.getByLabelText('Custom'));
        await user.clear(screen.getByLabelText('Custom duration'));
        await user.type(screen.getByLabelText('Custom duration'), '10');
        await user.selectOptions(screen.getByLabelText('Custom duration unit'), 'minutes');
      },
      'Polls can run from 15 minutes to 15 days.',
    ],
  ])('blocks %s without calling the API', async (_, fill, message) => {
    const api = mockApi({});
    const user = userEvent.setup();
    renderAt('/');
    await fill(user);
    await user.click(screen.getByRole('button', { name: 'Create poll' }));
    expect(screen.getByRole('alert')).toHaveTextContent(message);
    expect(api).not.toHaveBeenCalled();
  });

  it('shows server errors', async () => {
    mockApi({ 'POST /api/polls': apiError(500, 'internal_error', 'Something went wrong') });
    const user = userEvent.setup();
    renderAt('/');
    await fillBasics(user);
    await user.click(screen.getByRole('button', { name: 'Create poll' }));
    expect(await screen.findByRole('alert')).toHaveTextContent('Something went wrong');
  });
});
