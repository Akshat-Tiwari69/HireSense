import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import JobModal from './JobModal';

vi.mock('../../ui/select', () => ({
  Select: ({ children }) => <div>{children}</div>,
  SelectContent: ({ children }) => <div>{children}</div>,
  SelectItem: ({ children }) => <div>{children}</div>,
  SelectTrigger: ({ children, id }) => <div id={id}>{children}</div>,
  SelectValue: () => null,
}));

const renderModal = () => render(
  <JobModal
    jobModalOpen
    setJobModalOpen={vi.fn()}
    editingJob={null}
    jobForm={{
      title: '',
      description: '',
      required_skills: '',
      preferred_skills: '',
      min_experience: 0,
      max_experience: '',
      department: '',
      work_mode: 'On-Site',
      sector_id: '',
      status: 'draft',
      employment_type: 'full-time',
      experience_level: 'mid',
      salary_range: '',
      closes_at: '',
      role_complexity_level: 'intermediate',
    }}
    setJobForm={vi.fn()}
    savingJob={false}
    enhancingJob={false}
    setEnhancingJob={vi.fn()}
    sectors={[]}
    handleSaveJob={vi.fn()}
  />,
);

describe('JobModal posting controls', () => {
  it('exposes the canonical work mode and supported publishing fields on create', () => {
    renderModal();

    expect(screen.getByText('Work mode')).toBeInTheDocument();
    expect(screen.getByText('On-site')).toBeInTheDocument();
    expect(screen.getByText('Draft')).toBeInTheDocument();
    expect(screen.getByText('Role complexity')).toBeInTheDocument();
    expect(screen.getByLabelText('Applications close')).toHaveAttribute('type', 'datetime-local');
  });
});
