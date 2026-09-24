import React from 'react';

interface StatusDotProps {
  status: 'healthy' | 'unhealthy' | 'degraded' | 'active' | 'inactive';
}

export const StatusDot: React.FC<StatusDotProps> = ({ status }) => {
  const colorMap = {
    healthy: 'bg-emerald-500 shadow-emerald-500/50',
    active: 'bg-emerald-500 shadow-emerald-500/50',
    degraded: 'bg-amber-500 shadow-amber-500/50',
    unhealthy: 'bg-rose-500 shadow-rose-500/50',
    inactive: 'bg-slate-500 shadow-slate-500/50',
  };

  return (
    <span className="relative flex h-2.5 w-2.5 items-center justify-center">
      <span className={`animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 ${colorMap[status]}`} />
      <span className={`relative inline-flex rounded-full h-2 w-2 ${colorMap[status]}`} />
    </span>
  );
};
