import { describe, expect, it } from 'vitest';

import { toJobClosingInputValue } from './jobs';

describe('toJobClosingInputValue', () => {
  it('converts stored UTC timestamps to the IST wall time expected by the form', () => {
    expect(toJobClosingInputValue('2026-07-16T10:00:00Z')).toBe('2026-07-16T15:30');
  });

  it('keeps empty and invalid values out of datetime-local inputs', () => {
    expect(toJobClosingInputValue(null)).toBe('');
    expect(toJobClosingInputValue('not-a-date')).toBe('');
  });
});
