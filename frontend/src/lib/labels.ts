import type { ResultsVisibility, VoteControl } from './types';

export const VOTE_CONTROL_LABELS: Record<VoteControl, string> = {
  one_per_browser: 'One per browser',
  one_per_ip: 'One per network',
  open: 'Unlimited',
};

export const VISIBILITY_LABELS: Record<ResultsVisibility, string> = {
  live: 'Live',
  after_voting: 'After voting',
  private: 'Private',
};
