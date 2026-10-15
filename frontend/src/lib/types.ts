// API contract types. Mirror backend/flashpoll/models.py and docs/spec.md, section 2.

export type VoteControl = 'open' | 'one_per_browser' | 'one_per_ip';
export type ResultsVisibility = 'live' | 'after_voting' | 'private';
export type PollStatus = 'open' | 'closed';

export interface CreatePollRequest {
  question: string;
  options: string[];
  expires_in_minutes: number;
  vote_control: VoteControl;
  results_visibility: ResultsVisibility;
}

export interface CreatePollResponse {
  poll_id: string;
  admin_token: string;
  share_url: string;
  admin_url: string;
  expires_at: string;
}

export interface Results {
  total_votes: number;
  counts: number[];
}

export interface ResultsResponse extends Results {
  status: PollStatus;
}

export interface Poll {
  poll_id: string;
  question: string;
  options: string[];
  vote_control: VoteControl;
  results_visibility: ResultsVisibility;
  created_at: string;
  expires_at: string;
  status: PollStatus;
  has_voted: boolean;
  results_available: boolean;
}

export interface AdminPoll extends Poll {
  results: Results;
  deletes_at: string;
}

export interface VoteResponse {
  results: Results | null;
}

export type ErrorCode =
  | 'unauthorized'
  | 'results_hidden'
  | 'poll_not_found'
  | 'not_found'
  | 'poll_closed'
  | 'already_voted'
  | 'invalid_request'
  | 'busy'
  | 'forbidden'
  | 'internal_error'
  | 'network_error';

export interface FieldError {
  loc: string[];
  message: string;
}
