import React from 'react';
import { ArrowDownRight, ArrowUpRight, Minus } from 'lucide-react';
import { cn, inrFromLakhs } from '../../lib/format';
import type { KpiData } from '../../types/pages';
import { Sparkline } from './Sparkline';

const nf0 = new Intl.NumberFormat('en-IN', { maximumFractionDigits: 0 });

export const formatKpi = (k: Pick<KpiData, 'value' | 'unit'>, decimals?: number) => {
  if (k.value == null) return '—';
  const d = decimals ?? (Math.abs(k.value) >= 100 || Number.isInteger(k.value) ? 0 : Math.abs(k.value) >= 10 ? 1 : 2);
  const n = k.value.toLocaleString('en-IN', { minimumFractionDigits: d, maximumFractionDigits: d });
  if (k.unit === '₹ L') return inrFromLakhs(k.value);
  if (k.unit === '%') return `${n}%`;
  return n;
};

const unitSuffix = (u: string) => (u && u !== '%' && u !== '₹ L' && !u.startsWith('of ') ? u : '');

/** Headline number with its change against the comparison period and a sparkline. The change is coloured by whether it is good, not just by direction. */
export const StatTile: React.FC<{ k: KpiData; className?: string; onClick?: () => void }> = ({ k, className, onClick }) => {
  const up = k.delta != null && k.delta > 0.0001;
  const down = k.delta != null && k.delta < -0.0001;
  const good = k.delta == null ? null : !up && !down ? null : (up && k.good_when === 'up') || (down && k.good_when === 'down');
  const deltaText = k.delta == null ? null : `${k.delta > 0 ? '+' : k.delta < 0 ? '−' : ''}${Math.abs(k.delta).toFixed(k.delta_unit === 'pts' ? 1 : Math.abs(k.delta) < 10 ? 1 : 0)}${k.delta_unit === 'pts' ? ' pts' : '%'}`;
  const bar = k.status === 'ok' ? 'bg-ok' : k.status === 'warn' ? 'bg-warn' : k.status === 'bad' ? 'bg-bad' : 'bg-accent/50';
  const Comp = onClick ? 'button' : 'div';
  return (
    <Comp
      onClick={onClick}
      className={cn(
        'group relative flex min-w-0 flex-col gap-1.5 overflow-hidden rounded-2xl border border-line/80 bg-surface p-4 text-left shadow-card',
        onClick && 'transition-all hover:-translate-y-0.5 hover:border-line-strong hover:shadow-lift',
        className,
      )}
    >
      <span aria-hidden className={cn('absolute inset-x-0 top-0 h-[3px]', bar)} />
      <div className="flex items-start justify-between gap-2">
        <span className="min-w-0 truncate text-xs font-medium text-ink-3">{k.label}</span>
        {k.spark.length > 1 && <Sparkline values={k.spark} color={good === false ? 'rgb(var(--bad))' : 'rgb(var(--accent))'} width={64} height={22} className="-mt-0.5 shrink-0 opacity-90" />}
      </div>
      <div className="flex items-baseline gap-1">
        <span className="num text-[28px] font-semibold leading-9 tracking-tight text-ink">{formatKpi(k)}</span>
        {unitSuffix(k.unit) && <span className="text-xs font-medium text-ink-3">{unitSuffix(k.unit)}</span>}
        {k.unit.startsWith('of ') && <span className="text-xs font-medium text-ink-3">{k.unit}</span>}
      </div>
      <div className="flex min-h-4 flex-col gap-0.5">
        {deltaText && (
          <span className={cn('inline-flex items-center gap-0.5 whitespace-nowrap text-xs font-medium', good == null ? 'text-ink-3' : good ? 'text-ok' : 'text-bad')}>
            {up ? <ArrowUpRight className="size-3.5" /> : down ? <ArrowDownRight className="size-3.5" /> : <Minus className="size-3.5" />}
            {deltaText}
            <span className="font-normal text-ink-3">&nbsp;vs prior</span>
          </span>
        )}
        {k.hint && <span className="truncate text-xs text-ink-3" title={k.hint}>{k.hint}</span>}
      </div>
    </Comp>
  );
};

export const StatGrid: React.FC<{ items: KpiData[]; className?: string }> = ({ items, className }) => (
  <div className={cn('grid grid-cols-2 gap-3 lg:grid-cols-3', items.length >= 5 ? 'xl:grid-cols-5' : items.length === 4 ? 'xl:grid-cols-4' : '', items.length >= 6 && 'xl:grid-cols-6', className)}>
    {items.map((k) => (
      <StatTile key={k.label} k={k} />
    ))}
  </div>
);
