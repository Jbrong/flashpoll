import type {
  AdminPoll,
  CreatePollRequest,
  CreatePollResponse,
  ErrorCode,
  FieldError,
  Poll,
  ResultsResponse,
  VoteResponse,
} from './types';
import { getVoterToken } from './voterToken';

const BASE_URL: string = import.meta.env.VITE_API_URL ?? '';

export class ApiError extends Error {
  readonly status: number;
  readonly code: ErrorCode;
  readonly fields: FieldError[];

  constructor(status: number, code: ErrorCode, message: string, fields: FieldError[] = []) {
    super(message);
    this.status = status;
    this.code = code;
    this.fields = fields;
  }
}

interface RequestOptions {
  method?: 'GET' | 'POST' | 'DELETE';
  body?: unknown;
  headers?: Record<string, string>;
}

interface ErrorBody {
  error?: { code?: ErrorCode; message?: string; fields?: FieldError[] };
}

async function request<T>(path: string, { method = 'GET', body, headers = {} }: RequestOptions = {}): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${BASE_URL}${path}`, {
      method,
      headers: { ...(body ? { 'Content-Type': 'application/json' } : {}), ...headers },
      body: body ? JSON.stringify(body) : undefined,
    });
  } catch {
    throw new ApiError(0, 'network_error', "Couldn't reach Flashpoll. Check your connection.");
  }

  if (response.status === 204) return undefined as T;
  const data: unknown = await response.json().catch(() => null);
  if (!response.ok) {
    const error = (data as ErrorBody | null)?.error ?? {};
    throw new ApiError(
      response.status,
      error.code ?? 'internal_error',
      error.message ?? 'Something went wrong',
      error.fields ?? [],
    );
  }
  return data as T;
}

const voter = () => ({ 'X-Voter-Token': getVoterToken() });
const admin = (token: string) => ({ 'X-Admin-Token': token });
const pollPath = (pollId: string) => `/api/polls/${encodeURIComponent(pollId)}`;

export const api = {
  createPoll: (poll: CreatePollRequest) =>
    request<CreatePollResponse>('/api/polls', { method: 'POST', body: poll }),
  getPoll: (pollId: string) => request<Poll>(pollPath(pollId), { headers: voter() }),
  getResults: (pollId: string) =>
    request<ResultsResponse>(`${pollPath(pollId)}/results`, { headers: voter() }),
  vote: (pollId: string, optionIndex: number) =>
    request<VoteResponse>(`${pollPath(pollId)}/votes`, {
      method: 'POST',
      body: { option_index: optionIndex },
      headers: voter(),
    }),
  getAdminPoll: (token: string) => request<AdminPoll>('/api/admin/poll', { headers: admin(token) }),
  closePoll: (token: string) =>
    request<AdminPoll>('/api/admin/poll/close', { method: 'POST', headers: admin(token) }),
  deletePoll: (token: string) =>
    request<void>('/api/admin/poll', { method: 'DELETE', headers: admin(token) }),
};

/** Narrow an unknown caught value to something with a user-facing message. */
export function toError(err: unknown): Error {
  return err instanceof Error ? err : new Error(String(err));
}
