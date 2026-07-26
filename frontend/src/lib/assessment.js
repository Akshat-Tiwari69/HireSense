const MCQ_LETTERS = ['A', 'B', 'C', 'D'];

const STATUS_LABELS = {
  applied: 'Applied',
  pending: 'Pending',
  scheduled: 'Scheduled',
  in_progress: 'In Progress',
  completed: 'Completed',
  under_review: 'Under Review',
  rejected: 'Rejected',
  hired: 'Hired',
};

const normalizeStatus = (status) => STATUS_LABELS[String(status || '').toLowerCase()]
  || status
  || 'Pending';

export const resolveCandidateStatus = (candidateStatus, assessmentStatus) => {
  const candidate = String(candidateStatus || '').toLowerCase();
  if (candidate === 'hired' || candidate === 'rejected') return normalizeStatus(candidate);

  const assessment = String(assessmentStatus || '').toLowerCase();
  if (['scheduled', 'in_progress', 'completed'].includes(assessment)) {
    return normalizeStatus(assessment);
  }

  return normalizeStatus(candidateStatus);
};

const normalizeIndexMap = (answers, parser) => Object.fromEntries(
  Object.entries(answers || {}).flatMap(([questionId, answer]) => {
    const normalized = parser(answer);
    return normalized === null ? [] : [[questionId, normalized]];
  }),
);

export const normalizeSavedMcqAnswers = (answers) => normalizeIndexMap(answers, (answer) => {
  if (Number.isInteger(answer) && answer >= 0 && answer <= 3) return answer;
  const letterIndex = MCQ_LETTERS.indexOf(String(answer).trim().toUpperCase());
  return letterIndex >= 0 ? letterIndex : null;
});

export const normalizeSavedPsychometricAnswers = (answers) => normalizeIndexMap(answers, (answer) => {
  const value = Number(answer);
  return Number.isInteger(value) && value >= 0 ? value : null;
});

export const CODE_LANGUAGE_OPTIONS = [
  ['python', 'Python'],
  ['javascript', 'JavaScript'],
];

export const getCodeLanguages = (problem) => CODE_LANGUAGE_OPTIONS
  .map(([language]) => language)
  .filter((language) => {
    const source = problem?.starter_code?.[language];
    return typeof source === 'string' && Boolean(source.trim());
  });

export const getStarterCode = (problem, language) => {
  const supplied = problem?.starter_code?.[language];
  if (typeof supplied === 'string' && supplied.trim()) return supplied;
  return '';
};

export const formatAssessmentTime = (seconds) => {
  const total = Math.max(0, Math.floor(Number(seconds) || 0));
  const minutes = Math.floor(total / 60);
  const remainder = total % 60;
  return `${String(minutes).padStart(2, '0')}:${String(remainder).padStart(2, '0')}`;
};

export const finalizeAssessmentSubmission = async ({
  automatic = false,
  shouldSaveCode = false,
  saveCode,
  complete,
}) => {
  let saveError = null;
  if (shouldSaveCode) {
    try {
      await saveCode({ quiet: true });
    } catch (error) {
      saveError = error;
      if (!automatic) throw error;
    }
  }

  const result = await complete();
  return { result, saveError };
};

export const resolveAssessmentToken = (routeToken, storage = window.sessionStorage) => {
  const supplied = typeof routeToken === 'string' ? routeToken.trim() : '';
  if (supplied) {
    storage.setItem('assessmentToken', supplied);
    return supplied;
  }
  return storage.getItem('assessmentToken')?.trim() || '';
};
