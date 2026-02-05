import React from 'react';
import { Loader2 } from 'lucide-react';

/**
 * LoadingSpinner - Reusable animated spinner
 * @param {string} size - Size: 'sm' | 'md' | 'lg' | 'xl'
 * @param {string} className - Additional CSS classes
 */
const LoadingSpinner = ({ size = 'md', className = '' }) => {
    const sizeClasses = {
        sm: 'w-4 h-4',
        md: 'w-6 h-6',
        lg: 'w-8 h-8',
        xl: 'w-12 h-12'
    };

    return (
        <Loader2
            className={`animate-spin ${sizeClasses[size]} ${className}`}
            aria-label="Loading"
        />
    );
};

export default LoadingSpinner;
