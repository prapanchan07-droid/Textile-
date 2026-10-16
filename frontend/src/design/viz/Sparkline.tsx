import React, { useId } from 'react';

/** A tiny trend line with a soft area under it. Shows shape only; the number sits next to it. */
export const Sparkline: React.FC<{ values: number[]; color?: string; width?: number; height?: number; className?: string }> = ({
  values,
  color = 'rgb(var(--accent))',
  width = 84,
  height = 28,
  className,
}) => {
  const id = useId();
  const v = values.filter((x) => Number.isFinite(x));
  if (v.length < 2) return <svg width={width} height={height} className={className} aria-hidden />;
  const min = Math.min(...v);
  const max = Math.max(...v);
  const span = max - min || 1;
  const pad = 3;
  const x = (i: number) => pad + (i / (v.length - 1)) * (width - pad * 2);
  const y = (val: number) => height - pad - ((val - min) / span) * (height - pad * 2);
  const line = v.map((val, i) => `${i === 0 ? 'M' : 'L'}${x(i).toFixed(1)},${y(val).toFixed(1)}`).join(' ');
  const area = `${line} L${x(v.length - 1).toFixed(1)},${height} L${x(0).toFixed(1)},${height} Z`;
  return (
    <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`} className={className} aria-hidden>
      <defs>
        <linearGradient id={id} x1="0" x2="0" y1="0" y2="1">
          <stop offset="0%" stopColor={color} stopOpacity="0.28" />
          <stop offset="100%" stopColor={color} stopOpacity="0" />
        </linearGradient>
      </defs>
      <path d={area} fill={`url(#${id})`} />
      <path d={line} fill="none" stroke={color} strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
      <circle cx={x(v.length - 1)} cy={y(v[v.length - 1])} r="2.4" fill={color} />
    </svg>
  );
};
