import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import { Tabs } from '../../ui/tabs';
import JobPostingsTab from './JobPostingsTab';

const renderTab = (overrides = {}) => {
  const props = {
    jobPostings: [],
    sectors: [],
    expandedJob: null,
    setExpandedJob: vi.fn(),
    deletingJob: null,
    selectedJobForCandidates: 10,
    jobCandidates: [{
      id: 99,
      candidate_id: 7,
      name: 'Ada Lovelace',
      email: 'ada@example.test',
      match_score: 92,
      skill_match_score: 95,
      experience_match_score: 88,
      ai_reasoning: 'Strong fit',
      status: 'confirmed',
      reviewed_at: '2026-07-16T10:00:00Z',
    }],
    setSectorModalOpen: vi.fn(),
    setEditingJob: vi.fn(),
    setJobForm: vi.fn(),
    setJobModalOpen: vi.fn(),
    openEditJob: vi.fn(),
    handleDeleteJob: vi.fn(),
    fetchJobCandidates: vi.fn(),
    handleReviewCandidateMatch: vi.fn(),
    reviewingMatch: null,
    ...overrides,
  };

  render(
    <Tabs value="job-postings">
      <JobPostingsTab {...props} />
    </Tabs>,
  );
  return props;
};

describe('JobPostingsTab candidate review', () => {
  it('shows the stored review state and sends decisions with canonical ids', () => {
    const props = renderTab();

    expect(screen.getByText('confirmed')).toBeInTheDocument();
    expect(screen.getByText(/Reviewed/)).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'Reject Ada Lovelace match' }));

    expect(props.handleReviewCandidateMatch).toHaveBeenCalledWith(7, 10, 'rejected');
  });
});
