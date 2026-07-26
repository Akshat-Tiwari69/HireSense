import { Navigate, useLocation } from 'react-router-dom';

import { useAuth } from '../contexts/AuthContext';
import LoadingScreen from './common/LoadingScreen';

const ProtectedRoute = ({ element, allowedRoles = [] }) => {
  const location = useLocation();
  const { status, user } = useAuth();

  if (status === 'checking') {
    return <LoadingScreen message="Verifying your session..." />;
  }

  if (status !== 'authenticated') {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  }

  if (allowedRoles.length > 0 && !allowedRoles.includes(user?.role)) {
    return <Navigate to="/login" replace state={{ accessDenied: true }} />;
  }

  return element;
};

export default ProtectedRoute;
