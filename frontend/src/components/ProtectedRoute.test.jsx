import { render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { describe, expect, it, vi } from 'vitest';

import { useAuth } from '../contexts/AuthContext';
import ProtectedRoute from './ProtectedRoute';
import { HIRING_REVIEW_ROLES } from '../services/session';

vi.mock('../contexts/AuthContext', () => ({
  useAuth: vi.fn(),
}));

const renderRoute = (allowedRoles = ['admin']) => render(
  <MemoryRouter initialEntries={['/admin']}>
    <Routes>
      <Route
        path="/admin"
        element={<ProtectedRoute allowedRoles={allowedRoles} element={<div>Admin workspace</div>} />}
      />
      <Route path="/login" element={<div>Sign in</div>} />
    </Routes>
  </MemoryRouter>,
);

describe('ProtectedRoute', () => {
  it('waits for server verification before rendering protected content', () => {
    useAuth.mockReturnValue({ status: 'checking', user: { role: 'admin' } });

    renderRoute();

    expect(screen.getByText('Verifying your session...')).toBeInTheDocument();
    expect(screen.queryByText('Admin workspace')).not.toBeInTheDocument();
  });

  it('redirects anonymous users to sign in', () => {
    useAuth.mockReturnValue({ status: 'anonymous', user: null });

    renderRoute();

    expect(screen.getByText('Sign in')).toBeInTheDocument();
  });

  it('rejects an authenticated user with the wrong role', () => {
    useAuth.mockReturnValue({ status: 'authenticated', user: { role: 'proctor' } });

    renderRoute();

    expect(screen.getByText('Sign in')).toBeInTheDocument();
  });

  it('renders after authentication and role authorization', () => {
    useAuth.mockReturnValue({ status: 'authenticated', user: { role: 'admin' } });

    renderRoute();

    expect(screen.getByText('Admin workspace')).toBeInTheDocument();
  });

  it.each(['recruiter', 'sector_admin'])('permits %s in the hiring review workspace', (role) => {
    useAuth.mockReturnValue({ status: 'authenticated', user: { role } });

    renderRoute(HIRING_REVIEW_ROLES);

    expect(screen.getByText('Admin workspace')).toBeInTheDocument();
  });
});
