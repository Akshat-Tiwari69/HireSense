import { render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { api } from '../services/api';
import { getStaffSession, saveStaffSession } from '../services/session';
import { AuthProvider, useAuth } from './AuthContext';

vi.mock('../services/api', () => ({
  api: { get: vi.fn() },
}));

const Probe = () => {
  const { status, user } = useAuth();
  return <div>{`${status}:${user?.name || 'none'}`}</div>;
};

beforeEach(() => {
  api.get.mockReset();
});

describe('AuthProvider', () => {
  it('verifies a stored tab session before authenticating it', async () => {
    saveStaffSession({
      token: 'staff-token',
      user: { id: 3, role: 'interviewer', name: 'Stored Name' },
    });
    api.get.mockResolvedValue({
      data: {
        data: { user_id: 3, role: 'interviewer', name: 'Verified Name' },
      },
    });

    render(
      <AuthProvider>
        <Probe />
      </AuthProvider>,
    );

    expect(screen.getByText('checking:Stored Name')).toBeInTheDocument();
    expect(await screen.findByText('authenticated:Verified Name')).toBeInTheDocument();
    expect(api.get).toHaveBeenCalledWith('/api/auth/verify');
  });

  it('fails closed when server verification rejects a stored token', async () => {
    saveStaffSession({
      token: 'expired-token',
      user: { id: 3, role: 'admin', name: 'Old Admin' },
    });
    api.get.mockRejectedValue(new Error('expired'));

    render(
      <AuthProvider>
        <Probe />
      </AuthProvider>,
    );

    expect(await screen.findByText('anonymous:none')).toBeInTheDocument();
    await waitFor(() => expect(getStaffSession()).toBeNull());
  });

  it('starts anonymous without making a verification request', () => {
    render(
      <AuthProvider>
        <Probe />
      </AuthProvider>,
    );

    expect(screen.getByText('anonymous:none')).toBeInTheDocument();
    expect(api.get).not.toHaveBeenCalled();
  });
});
