import { describe, expect, it, vi } from 'vitest';

import {
  finalizeAssessmentSubmission,
  formatAssessmentTime,
  getCodeLanguages,
  getStarterCode,
  normalizeSavedMcqAnswers,
  normalizeSavedPsychometricAnswers,
  resolveCandidateStatus,
  resolveAssessmentToken,
} from './assessment';

describe('assessment utilities', () => {
  it('normalizes saved MCQ letters and indices', () => {
    expect(normalizeSavedMcqAnswers({ 1: 'A', 2: 'd', 3: 2, 4: '9' })).toEqual({
      1: 0,
      2: 3,
      3: 2,
    });
  });

  it('normalizes only valid psychometric option indices', () => {
    expect(normalizeSavedPsychometricAnswers({ 1: '2', 2: 0, 3: '-1', 4: 'nope' })).toEqual({
      1: 2,
      2: 0,
    });
  });

  it('only exposes languages backed by assigned starter code', () => {
    const problem = {
      starter_code: {
        python: 'def solve():\n    pass',
        javascript: '   ',
        function_signature: 'def ignored():',
      },
    };

    expect(getCodeLanguages(problem)).toEqual(['python']);
    expect(getStarterCode({ starter_code: { python: 'def solve():\n    pass' } }, 'python'))
      .toBe('def solve():\n    pass');
    expect(getStarterCode(problem, 'javascript')).toBe('');
  });

  it('formats remaining time without producing negative values', () => {
    expect(formatAssessmentTime(65)).toBe('01:05');
    expect(formatAssessmentTime(-10)).toBe('00:00');
  });

  it('prefers a route token and stores it for the tab-scoped session', () => {
    const storage = new Map([['assessmentToken', 'stored-token']]);
    const adapter = {
      getItem: (key) => storage.get(key) || null,
      setItem: (key, value) => storage.set(key, value),
    };

    expect(resolveAssessmentToken(' route-token ', adapter)).toBe('route-token');
    expect(storage.get('assessmentToken')).toBe('route-token');
    expect(resolveAssessmentToken(undefined, adapter)).toBe('route-token');
  });

  it('derives display status from terminal candidate and active assessment states', () => {
    expect(resolveCandidateStatus('hired', 'in_progress')).toBe('Hired');
    expect(resolveCandidateStatus('rejected', 'completed')).toBe('Rejected');
    expect(resolveCandidateStatus('applied', 'scheduled')).toBe('Scheduled');
    expect(resolveCandidateStatus('pending', 'in_progress')).toBe('In Progress');
    expect(resolveCandidateStatus('under_review', 'completed')).toBe('Completed');
  });

  it('ignores cancelled assessments and falls back to candidate state', () => {
    expect(resolveCandidateStatus('under_review', 'cancelled')).toBe('Under Review');
    expect(resolveCandidateStatus(null, 'cancelled')).toBe('Pending');
  });

  it('still completes an automatic timeout submission when final code save fails', async () => {
    const saveCode = vi.fn().mockRejectedValue(new Error('deadline reached'));
    const complete = vi.fn().mockResolvedValue({ status: 'success' });

    const result = await finalizeAssessmentSubmission({
      automatic: true,
      shouldSaveCode: true,
      saveCode,
      complete,
    });

    expect(saveCode).toHaveBeenCalledWith({ quiet: true });
    expect(complete).toHaveBeenCalledOnce();
    expect(result.saveError).toEqual(expect.any(Error));
  });

  it('keeps manual submission retryable when final code save fails', async () => {
    const saveCode = vi.fn().mockRejectedValue(new Error('runner unavailable'));
    const complete = vi.fn();

    await expect(finalizeAssessmentSubmission({
      automatic: false,
      shouldSaveCode: true,
      saveCode,
      complete,
    })).rejects.toThrow('runner unavailable');

    expect(complete).not.toHaveBeenCalled();
  });
});
