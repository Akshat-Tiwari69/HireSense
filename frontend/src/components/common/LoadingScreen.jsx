import React from 'react';
import LoadingSpinner from './LoadingSpinner';

/**
 * LoadingScreen - Full-page loading overlay with spinner and message
 * @param {string} message - Loading message to display
 */
const LoadingScreen = ({ message = 'Loading...' }) => {
    return (
        <div className="fixed inset-0 bg-gradient-to-br from-slate-50 to-slate-100 flex items-center justify-center z-50">
            <div className="text-center">
                <div className="mb-6 flex justify-center">
                    <div className="relative">
                        {/* Outer pulsing ring */}
                        <div className="absolute inset-0 rounded-full bg-indigo-200 animate-ping opacity-75"></div>

                        {/* Inner spinner */}
                        <div className="relative bg-white rounded-full p-6 shadow-lg">
                            <LoadingSpinner size="xl" className="text-indigo-600" />
                        </div>
                    </div>
                </div>

                <h2 className="text-2xl font-bold text-slate-800 mb-2">
                    {message}
                </h2>

                <p className="text-slate-600 animate-pulse">
                    Please wait a moment...
                </p>

                {/* Progress dots */}
                <div className="flex justify-center gap-2 mt-6">
                    <div className="w-2 h-2 bg-indigo-600 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                    <div className="w-2 h-2 bg-indigo-600 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                    <div className="w-2 h-2 bg-indigo-600 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                </div>
            </div>
        </div>
    );
};

export default LoadingScreen;
