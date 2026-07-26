export const STAFF_SESSION_KEY = 'hiresense.staff-session.v1';
export const HIRING_REVIEW_ROLES = ['interviewer', 'recruiter', 'sector_admin'];

const STAFF_ROLES = new Set([
  'admin',
  'proctor',
  'super_admin',
  ...HIRING_REVIEW_ROLES,
]);

const LEGACY_STORAGE_KEYS = [
  'authToken',
  'userEmail',
  'userRole',
  'user_id',
  'desiredSkills',
];

const normalizeSession = (session) => {
  const token = session?.token;
  const user = session?.user;
  const role = user?.role;
  const sectorId = user?.sector_id ?? null;

  if (
    typeof token !== 'string'
    || token.trim().length === 0
    || !user
    || typeof role !== 'string'
    || !STAFF_ROLES.has(role)
    || (
      ['recruiter', 'sector_admin'].includes(role)
      && (!Number.isInteger(sectorId) || sectorId <= 0)
    )
  ) {
    throw new TypeError('A valid staff session is required');
  }

  return {
    token: token.trim(),
    user: {
      id: user.id ?? null,
      email: typeof user.email === 'string' ? user.email : '',
      name: typeof user.name === 'string' ? user.name : '',
      role,
      sector_id: sectorId,
    },
  };
};

export const saveStaffSession = (session) => {
  const normalized = normalizeSession(session);
  window.sessionStorage.setItem(STAFF_SESSION_KEY, JSON.stringify(normalized));
  return normalized;
};

export const getStaffSession = () => {
  const serialized = window.sessionStorage.getItem(STAFF_SESSION_KEY);
  if (!serialized) return null;

  try {
    return normalizeSession(JSON.parse(serialized));
  } catch {
    window.sessionStorage.removeItem(STAFF_SESSION_KEY);
    return null;
  }
};

export const clearStaffSession = () => {
  window.sessionStorage.removeItem(STAFF_SESSION_KEY);
};

export const clearLegacyPersistentSession = () => {
  for (const key of LEGACY_STORAGE_KEYS) {
    window.localStorage.removeItem(key);
  }
};
