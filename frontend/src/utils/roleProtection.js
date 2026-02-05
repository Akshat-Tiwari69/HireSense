import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

/**
 * Higher-order component for role-based route protection
 * Redirects users to appropriate dashboard based on their role
 */
export const withRoleProtection = (Component, allowedRoles = []) => {
    return (props) => {
        const navigate = useNavigate();

        useEffect(() => {
            const token = localStorage.getItem('authToken');
            const userRole = localStorage.getItem('userRole');

            if (!token) {
                navigate('/login');
                return;
            }

            if (allowedRoles.length > 0 && !allowedRoles.includes(userRole)) {
                // Redirect to appropriate dashboard based on role
                switch (userRole) {
                    case 'admin':
                        navigate('/admin');
                        break;
                    case 'proctor':
                        navigate('/proctor');
                        break;
                    case 'interviewer':
                    default:
                        navigate('/dashboard');
                        break;
                }
            }
        }, [navigate]);

        return <Component {...props} />;
    };
};

/**
 * Hook for role-based navigation
 * Returns a function to navigate to role-appropriate dashboard
 */
export const useRoleNavigation = () => {
    const navigate = useNavigate();

    const navigateToDashboard = (role = null) => {
        const userRole = role || localStorage.getItem('userRole');

        switch (userRole) {
            case 'admin':
                navigate('/admin');
                break;
            case 'proctor':
                navigate('/proctor');
                break;
            case 'interviewer':
            default:
                navigate('/dashboard');
                break;
        }
    };

    const navigateAfterLogin = (userRole) => {
        localStorage.setItem('userRole', userRole);
        navigateToDashboard(userRole);
    };

    return {
        navigateToDashboard,
        navigateAfterLogin,
    };
};

/**
 * Component to automatically redirect to dashboard based on role
 */
export const RoleRedirect = () => {
    const { navigateToDashboard } = useRoleNavigation();

    useEffect(() => {
        navigateToDashboard();
    }, []);

    return null;
};

export default withRoleProtection;
