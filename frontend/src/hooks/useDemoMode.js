import { useEffect, useState } from 'react';

import { api } from '../services/api';

// The backend advertises DEMO_MODE on its liveness endpoint; anything else means "no demo".
export const useDemoMode = () => {
  const [demoMode, setDemoMode] = useState(false);

  useEffect(() => {
    let active = true;
    api.get('/api/health')
      .then(({ data }) => { if (active) setDemoMode(data?.demo_mode === true); })
      .catch(() => {});
    return () => { active = false; };
  }, []);

  return demoMode;
};
