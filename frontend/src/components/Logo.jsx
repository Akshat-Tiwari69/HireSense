const Logo = ({ className = '', size = 'default', variant = 'full' }) => {
  const sizes = {
    small: { icon: 26, text: 'text-base' },
    default: { icon: 32, text: 'text-xl' },
    large: { icon: 40, text: 'text-2xl' },
    hero: { icon: 46, text: 'text-3xl' },
  };
  const currentSize = sizes[size] || sizes.default;

  const mark = (
    <svg
      aria-hidden="true"
      width={currentSize.icon}
      height={currentSize.icon}
      viewBox="0 0 40 40"
      fill="none"
      className="shrink-0"
    >
      <rect width="40" height="40" rx="11" fill="hsl(var(--primary))" />
      <path
        d="M12 12.5V27.5M28 12.5V27.5M12.5 20H27.5"
        stroke="white"
        strokeWidth="3"
        strokeLinecap="round"
      />
      <circle cx="20" cy="20" r="2.75" fill="white" />
    </svg>
  );

  if (variant === 'icon') {
    return <span className={`inline-flex ${className}`} aria-label="HireSense">{mark}</span>;
  }

  return (
    <span className={`inline-flex items-center gap-2.5 text-foreground ${className}`} aria-label="HireSense">
      {mark}
      <span className={`font-semibold tracking-[-0.025em] text-current ${currentSize.text}`}>
        HireSense
      </span>
    </span>
  );
};

export default Logo;
