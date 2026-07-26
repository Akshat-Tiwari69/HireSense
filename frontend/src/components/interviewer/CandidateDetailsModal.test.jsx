import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import CandidateDetailsModal from './CandidateDetailsModal';

describe('CandidateDetailsModal', () => {
  it('presents the AI recommendation as evidence, not lifecycle status', () => {
    render(
      <CandidateDetailsModal
        open
        onOpenChange={vi.fn()}
        selectedCandidate={{
          id: 7,
          name: 'Ada Candidate',
          email: 'ada@example.com',
          status: 'Applied',
          aiRecommendation: 'High Match',
          aiMatchScore: 91,
          pros: [],
          cons: [],
        }}
        assessmentDetails={null}
        decisionLoading={false}
        onDownloadResume={vi.fn()}
        onFinalDecision={vi.fn()}
      />,
    );

    expect(screen.getByText('AI recommendation')).toBeInTheDocument();
    expect(screen.getByText('High Match')).toBeInTheDocument();
    expect(screen.getByText(/applied/i)).toBeInTheDocument();
  });

  it('shows progress while completed assessment evidence is loading', () => {
    render(
      <CandidateDetailsModal
        open
        onOpenChange={vi.fn()}
        selectedCandidate={{
          id: 7,
          name: 'Ada Candidate',
          email: 'ada@example.com',
          status: 'Completed',
          pros: [],
          cons: [],
        }}
        assessmentDetails={null}
        assessmentLoading
        decisionLoading={false}
        onDownloadResume={vi.fn()}
        onFinalDecision={vi.fn()}
      />,
    );

    expect(screen.getByRole('status', { name: /loading assessment evidence/i })).toBeInTheDocument();
    expect(screen.queryByText(/results are not available/i)).not.toBeInTheDocument();
  });

  it('renders the completed assessment score contract', () => {
    render(
      <CandidateDetailsModal
        open
        onOpenChange={vi.fn()}
        selectedCandidate={{
          id: 7,
          name: 'Ada Candidate',
          email: 'ada@example.com',
          status: 'Completed',
          pros: [],
          cons: [],
        }}
        assessmentDetails={{
          id: 17,
          status: 'completed',
          overall_score: 80,
          technical_score: 82,
          psychometric_score: 74,
          mcq_score: 85,
          coding_score: 79,
          automated_recommendation: 'Recommend for Hire',
          automated_rationale: 'Strong evidence across the assessment.',
        }}
        assessmentLoading={false}
        decisionLoading={false}
        onDownloadResume={vi.fn()}
        onFinalDecision={vi.fn()}
      />,
    );

    expect(screen.getByRole('progressbar', { name: 'Overall' })).toHaveAttribute('aria-valuenow', '80');
    expect(screen.getByText('Strong evidence across the assessment.')).toBeInTheDocument();
    expect(screen.queryByText(/results are not available/i)).not.toBeInTheDocument();
  });
});
