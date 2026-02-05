import React from 'react';

const Logo = ({ className = '', size = 'default', variant = 'full' }) => {
  const sizes = {
    small: { icon: 24, text: 'text-lg' },
    default: { icon: 32, text: 'text-2xl' },
    large: { icon: 40, text: 'text-3xl' },
    hero: { icon: 48, text: 'text-4xl' }
  };

  const currentSize = sizes[size];

  // Check if we need white text (for dark backgrounds like footer)
  const isWhiteText = className.includes('text-white');
  const textColor = isWhiteText ? 'text-white' : 'text-slate-900';
  const strokeColor = isWhiteText ? '#ffffff' : '#4F46E5';

  const LogoIcon = () => (
    <svg
      width={currentSize.icon}
      height={currentSize.icon}
      viewBox="0 0 40 40"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
    >
      {/* Layered hexagons representing filtering/selection */}
      <path
        d="M20 2L35 11V29L20 38L5 29V11L20 2Z"
        fill={isWhiteText ? '#ffffff' : '#4F46E5'}
        fillOpacity="0.1"
        stroke={strokeColor}
        strokeWidth="1.5"
      />
      <path
        d="M20 8L30 14V26L20 32L10 26V14L20 8Z"
        fill={isWhiteText ? '#ffffff' : '#4F46E5'}
        fillOpacity="0.2"
        stroke={strokeColor}
        strokeWidth="1.5"
      />
      <circle
        cx="20"
        cy="20"
        r="6"
        fill={isWhiteText ? '#ffffff' : '#4F46E5'}
        stroke={isWhiteText ? '#e5e7eb' : '#6366F1'}
        strokeWidth="2"
      />
      {/* AI pulse indicator */}
      <circle
        cx="20"
        cy="20"
        r="3"
        fill={isWhiteText ? '#e5e7eb' : '#818CF8'}
      />
    </svg>
  );

  if (variant === 'icon') {
    return <LogoIcon />;
  }

  return (
    <div className={`flex items-center gap-2 ${className}`}>
      <LogoIcon />
      <span className={`font-bold ${textColor} ${currentSize.text}`}>
        HireSense
      </span>
    </div>
  );
};

export default Logo;
