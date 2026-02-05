import React from 'react';
import { Loader2 } from 'lucide-react';

export const LoadingSpinner = ({ size = 'default', text = 'Loading...' }) => {
    const sizeClasses = {
        sm: 'w-4 h-4',
        default: 'w-8 h-8',
        lg: 'w-12 h-12',
    };

    return (
        <div className="flex flex-col items-center justify-center p-8">
            <Loader2 className={`${sizeClasses[size]} text-indigo-600 animate-spin`} />
            {text && <p className="mt-4 text-slate-600 text-sm">{text}</p>}
        </div>
    );
};

export const FullPageLoading = ({ text = 'Loading...' }) => {
    return (
        <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50 flex items-center justify-center">
            <div className="text-center">
                <Loader2 className="w-16 h-16 text-indigo-600 animate-spin mx-auto" />
                <p className="mt-6 text-slate-700 text-lg font-medium">{text}</p>
            </div>
        </div>
    );
};

export const SkeletonCard = () => {
    return (
        <div className="bg-white p-6 rounded-lg shadow-md border-none animate-pulse">
            <div className="h-4 bg-slate-200 rounded w-3/4 mb-4"></div>
            <div className="h-3 bg-slate-200 rounded w-1/2 mb-2"></div>
            <div className="h-3 bg-slate-200 rounded w-2/3"></div>
        </div>
    );
};

export const SkeletonTable = ({ rows = 5 }) => {
    return (
        <div className="animate-pulse">
            {Array.from({ length: rows }).map((_, i) => (
                <div key={i} className="flex gap-4 mb-4 p-4 bg-white rounded-lg shadow-sm">
                    <div className="h-4 bg-slate-200 rounded flex-1"></div>
                    <div className="h-4 bg-slate-200 rounded flex-1"></div>
                    <div className="h-4 bg-slate-200 rounded flex-1"></div>
                </div>
            ))}
        </div>
    );
};

export default LoadingSpinner;
