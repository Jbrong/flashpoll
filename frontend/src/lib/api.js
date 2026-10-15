import { getVoterToken } from './voterToken';

const BASE_URL = import.meta.env.VITE_API_URL ?? '';

export class ApiError extends Error {
  constructor(status, code, message, fields = []) {
    super(message);
    this.status = status;
    this.code = code;
    this.fields = fields;
  }
}

async function request(path, { method = 'GET', body, headers = {} } = {}) {
  let response;
  try {
    response = await fetch(`${BASE_URL}${path}`, {
      method,
      headers: { ...(body ? { 'Content-Type': 'application/json' } : {}), ...headers },
      body: body ? JSON.stringify(body) : undefined,
    });
  } catch {
    throw new ApiError(0, 'network_error', "Couldn't reach Flashpoll. Check your connection.");
  }

  if (response.status === 204) return null;
  const data = await response.json().catch(() => null);
  if (!response.ok) {
    const error = data?.error ?? {};
    throw new ApiError(
      response.status,
      error.code ?? 'internal_error',
      error.message ?? 'Something went wrong',
      error.fields ?? [],
    );
  }
  return data;
}

const voter = () => ({ 'X-Voter-Token': getVoterToken() });
const admin = (token) => ({ Authorization: `Bearer ${token}` });
const pollPath = (pollId) => `/api/polls/${encodeURIComponent(pollId)}`;

export const api = {
  createPoll: (poll) => request('/api/polls', { method: 'POST', body: poll }),
  getPoll: (pollId) => request(pollPath(pollId), { headers: voter() }),
  getResults: (pollId) => request(`${pollPath(pollId)}/results`, { headers: voter() }),
  vote: (pollId, optionIndex) =>
    request(`${pollPath(pollId)}/votes`, {
      method: 'POST',
      body: { option_index: optionIndex },
      headers: voter(),
    }),
  getAdminPoll: (token) => request('/api/admin/poll', { headers: admin(token) }),
  closePoll: (token) => request('/api/admin/poll/close', { method: 'POST', headers: admin(token) }),
  deletePoll: (token) => request('/api/admin/poll', { method: 'DELETE', headers: admin(token) }),
};
