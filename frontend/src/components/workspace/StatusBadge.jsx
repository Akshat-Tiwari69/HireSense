import { Badge } from '../ui/badge';

const normalize = (value) => String(value || 'pending').trim().toLowerCase().replace(/[_\s]+/g, '-');

const StatusBadge = ({ status }) => {
  const value = normalize(status);
  const className = value.includes('no-hire') || value.includes('reject') || value === 'critical' || value === 'failed'
    ? 'border-red-200 bg-red-50 text-red-700'
    : value.includes('hire') || value === 'completed' || value === 'clear'
      ? 'border-emerald-200 bg-emerald-50 text-emerald-700'
      : value.includes('progress') || value.includes('scheduled') || value === 'active'
        ? 'border-blue-200 bg-blue-50 text-blue-700'
        : value === 'high' || value === 'medium' || value.includes('review')
          ? 'border-amber-200 bg-amber-50 text-amber-700'
          : 'border-slate-200 bg-slate-50 text-slate-700';

  return <Badge variant="outline" className={`${className} capitalize`}>{value.replace(/-/g, ' ')}</Badge>;
};

export default StatusBadge;
