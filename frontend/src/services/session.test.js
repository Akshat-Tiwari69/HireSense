import { describe, expect, it } from 'vitest';

import {
  STAFF_SESSION_KEY,
  clearStaffSession,
  getStaffSession,
  saveStaffSession,
} from './session';

const validSession = {
  token: 'signed-token',
  user: {
    id: 9,
    email: 'interviewer@example.test',
    name: 'Avery Interviewer',
    role: 'interviewer',
    sector_id: null,
  },
};

describe('staff session storage', () => {
  it('persists only to the current tab session', () => {
    saveStaffSession(validSession);

    expect(getStaffSession()).toEqual(validSession);
    expect(window.sessionStorage.getItem(STAFF_SESSION_KEY)).not.toBeNull();
    expect(window.localStorage.length).toBe(0);
  });

  it.each([
    null,
    {},
    { token: '', user: validSession.user },
    { token: 'token', user: { role: '' } },
  ])('rejects malformed sessions: %j', (session) => {
    expect(() => saveStaffSession(session)).toThrow('valid staff session');
  });

  it('fails closed and removes corrupted storage', () => {
    window.sessionStorage.setItem(STAFF_SESSION_KEY, '{not-json');

    expect(getStaffSession()).toBeNull();
    expect(window.sessionStorage.getItem(STAFF_SESSION_KEY)).toBeNull();
  });

  it('clears the complete session', () => {
    saveStaffSession(validSession);
    clearStaffSession();

    expect(getStaffSession()).toBeNull();
  });

  it.each(['recruiter', 'sector_admin'])('preserves sector scope for %s sessions', (role) => {
    const scopedSession = {
      token: 'signed-token',
      user: { ...validSession.user, role, sector_id: 12 },
    };

    expect(saveStaffSession(scopedSession)).toEqual(scopedSession);
    expect(getStaffSession()).toEqual(scopedSession);
  });

  it.each(['recruiter', 'sector_admin'])('rejects %s sessions without a sector', (role) => {
    expect(() => saveStaffSession({
      token: 'signed-token',
      user: { ...validSession.user, role, sector_id: null },
    })).toThrow('valid staff session');
  });
});
