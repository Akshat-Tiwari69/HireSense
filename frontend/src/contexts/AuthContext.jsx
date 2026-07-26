import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from 'react';

import { api } from '../services/api';
import {
  clearLegacyPersistentSession,
  clearStaffSession,
  getStaffSession,
  saveStaffSession,
} from '../services/session';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [initialSession] = useState(() => getStaffSession());
  const [session, setSession] = useState(initialSession);
  const [status, setStatus] = useState(initialSession ? 'checking' : 'anonymous');

  const signOut = useCallback(() => {
    clearStaffSession();
    setSession(null);
    setStatus('anonymous');
  }, []);

  const signIn = useCallback((nextSession) => {
    const saved = saveStaffSession(nextSession);
    setSession(saved);
    setStatus('authenticated');
    return saved;
  }, []);

  useEffect(() => {
    clearLegacyPersistentSession();

    const onExpired = () => signOut();
    window.addEventListener('hiresense:session-expired', onExpired);
    return () => window.removeEventListener('hiresense:session-expired', onExpired);
  }, [signOut]);

  useEffect(() => {
    if (!session?.token || status !== 'checking') return undefined;

    let active = true;
    api.get('/api/auth/verify')
      .then(({ data }) => {
        if (!active) return;
        const verified = data?.data;
        const nextSession = saveStaffSession({
          token: session.token,
          user: {
            ...session.user,
            id: verified?.user_id ?? session.user.id,
            role: verified?.role,
            name: verified?.name ?? session.user.name,
          },
        });
        setSession(nextSession);
        setStatus('authenticated');
      })
      .catch(() => {
        if (active) signOut();
      });

    return () => {
      active = false;
    };
  }, [session, signOut, status]);

  const value = useMemo(() => ({
    session,
    status,
    token: session?.token ?? null,
    user: session?.user ?? null,
    signIn,
    signOut,
  }), [session, signIn, signOut, status]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used inside AuthProvider');
  }
  return context;
};
