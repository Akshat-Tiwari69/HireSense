import { Navigate } from 'react-router-dom';

const ProtectedRoute = ({ element, allowedRoles = [] }) => {
  const token = localStorage.getItem('authToken');
  const userRole = localStorage.getItem('userRole');

  if (!token) {
    return <Navigate to="/login" replace />;
  }

  if (allowedRoles.length > 0 && !allowedRoles.includes(userRole)) {
    return <Navigate to="/login" replace />;
  }

  return element;
};

export default ProtectedRoute;
