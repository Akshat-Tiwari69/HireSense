const MetricCard = ({ label, value, hint, icon: Icon, tone = 'primary' }) => {
  const tones = {
    primary: 'bg-accent text-primary',
    success: 'bg-emerald-50 text-success',
    warning: 'bg-amber-50 text-warning',
    neutral: 'bg-muted text-muted-foreground',
  };
  return (
    <div className="surface-card rounded-xl bg-card p-5">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-sm font-medium text-muted-foreground">{label}</p>
          <p className="mt-2 text-3xl font-semibold tracking-[-0.04em] tabular-nums">{value ?? 0}</p>
          {hint && <p className="mt-2 text-xs text-muted-foreground">{hint}</p>}
        </div>
        {Icon && <span className={`flex h-10 w-10 items-center justify-center rounded-lg ${tones[tone] || tones.primary}`}><Icon className="h-5 w-5" /></span>}
      </div>
    </div>
  );
};

export default MetricCard;
