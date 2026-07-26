import { afterEach, beforeEach, describe, expect, it } from 'vitest';

import { api, isRelativeApiUrl } from './api';
import { clearStaffSession, saveStaffSession } from './session';

const originalAdapter = api.defaults.adapter;

const echoAdapter = async (config) => ({
  config,
  data: { headers: config.headers.toJSON() },
  headers: {},
  status: 200,
  statusText: 'OK',
});

beforeEach(() => {
  api.defaults.adapter = echoAdapter;
  saveStaffSession({
    token: 'staff-token',
    user: { id: 4, role: 'admin', name: 'Admin' },
  });
  window.sessionStorage.setItem('assessmentToken', 'assessment-token');
});

afterEach(() => {
  api.defaults.adapter = originalAdapter;
  clearStaffSession();
});

describe('API request boundary', () => {
  it.each([
    '/api/auth/verify',
    '/api/interviewee/session',
    'api/jobs/postings',
  ])('accepts relative API paths: %s', (url) => {
    expect(isRelativeApiUrl(url)).toBe(true);
  });

  it.each([
    'https://evil.example/collect',
    '//evil.example/collect',
    'data:text/plain,hello',
  ])('rejects absolute or protocol-relative paths: %s', (url) => {
    expect(isRelativeApiUrl(url)).toBe(false);
  });

  it('sends the staff bearer only to a relative API request', async () => {
    const response = await api.get('/api/admin/users');

    expect(response.data.headers.Authorization).toBe('Bearer staff-token');
    expect(response.data.headers['X-Assessment-Token']).toBeUndefined();
  });

  it('scopes assessment capabilities to interviewee endpoints', async () => {
    const interviewee = await api.get('/api/interviewee/session');
    const publicJobs = await api.get('/api/jobs/postings');

    expect(interviewee.data.headers['X-Assessment-Token']).toBe(
      'assessment-token',
    );
    expect(publicJobs.data.headers['X-Assessment-Token']).toBeUndefined();
  });

  it('refuses an absolute request before the adapter can send it', async () => {
    await expect(api.get('https://evil.example/collect')).rejects.toThrow(
      'relative /api URL',
    );
  });
});
