import { describe, expect, it } from 'vitest';
import { formatDuration } from './time';

describe('formatDuration', () => {
  it.each([
    [30_000, 'less than a minute'],
    [12 * 60_000, '12m'],
    [2 * 3_600_000, '2h'],
    [2 * 3_600_000 + 15 * 60_000, '2h 15m'],
    [3 * 86_400_000 + 4 * 3_600_000, '3d 4h'],
    [15 * 86_400_000, '15d'],
  ])('%i ms -> %s', (ms, text) => {
    expect(formatDuration(ms)).toBe(text);
  });
});
