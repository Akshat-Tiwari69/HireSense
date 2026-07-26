import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import UserModal from './UserModal';

vi.mock('../../ui/select', () => ({
  Select: ({ children }) => <div>{children}</div>,
  SelectContent: ({ children }) => <div>{children}</div>,
  SelectItem: ({ children }) => <div>{children}</div>,
  SelectTrigger: ({ children, id }) => <div id={id}>{children}</div>,
  SelectValue: () => null,
}));

const renderModal = ({
  role = 'interviewer',
  currentUserRole = 'admin',
  sectorId = '',
} = {}) => render(
  <UserModal
    userModalOpen
    setUserModalOpen={vi.fn()}
    editingUser={null}
    userForm={{
      name: '',
      email: '',
      password: '',
      role,
      sector_id: sectorId,
    }}
    setUserForm={vi.fn()}
    savingUser={false}
    handleSaveUser={vi.fn()}
    sectors={[{ id: 12, name: 'Engineering' }]}
    currentUserRole={currentUserRole}
  />,
);

describe('UserModal role provisioning', () => {
  it('offers the four non-admin staff roles to regular admins', () => {
    renderModal();

    expect(screen.getByText('Interviewer')).toBeInTheDocument();
    expect(screen.getByText('Proctor')).toBeInTheDocument();
    expect(screen.getByText('Recruiter')).toBeInTheDocument();
    expect(screen.getByText('Sector administrator')).toBeInTheDocument();
    expect(screen.queryByText('Administrator')).not.toBeInTheDocument();
  });

  it('offers privileged roles only to super admins', () => {
    renderModal({ currentUserRole: 'super_admin' });

    expect(screen.getByText('Administrator')).toBeInTheDocument();
    expect(screen.getByText('Super administrator')).toBeInTheDocument();
  });

  it.each(['recruiter', 'sector_admin'])('requires a sector for %s', (role) => {
    renderModal({ role });

    expect(screen.getByText('Engineering')).toBeInTheDocument();
    expect(screen.getByText('Sector')).toBeInTheDocument();
    expect(screen.getByText('A sector assignment is required for this role.')).toBeInTheDocument();
  });
});
