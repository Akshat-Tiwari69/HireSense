import React from 'react'

/**
 * Visual indicator showing realtime connection status
 */
const RealtimeIndicator = ({ isConnected, className = '' }) => {
    return (
        <div className={`flex items-center gap-2 ${className}`}>
            <div className="relative">
                <div
                    className={`w-2 h-2 rounded-full transition-colors duration-300 ${isConnected ? 'bg-emerald-500' : 'bg-slate-400'
                        }`}
                />
                {isConnected && (
                    <div className="absolute inset-0 w-2 h-2 rounded-full bg-emerald-500 animate-ping opacity-75" />
                )}
            </div>
            <span className={`text-sm font-medium ${isConnected ? 'text-emerald-600' : 'text-slate-500'
                }`}>
                {isConnected ? 'Live' : 'Reconnecting...'}
            </span>
        </div>
    )
}

export default RealtimeIndicator
