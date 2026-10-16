import React from 'react';
import {
  Area, Bar, BarChart, CartesianGrid, Cell, ComposedChart, Legend as RLegend, Line, LabelList, PolarAngleAxis, PolarGrid, PolarRadiusAxis, Radar, RadarChart, ReferenceLine,
  ResponsiveContainer, Tooltip, XAxis, YAxis,
} from 'recharts';
import { cn } from '../../lib/format';
import { axisTick, useChartTheme } from '../charts/theme';
import { catColor, CATEGORY_COLORS } from './palette';

/** Compact tooltip in the app's own tokens (recharts' default ignores dark mode). */
const Tip: React.FC<any> = ({ active, payload, label, format = (v: number) => String(v), names }) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="rounded-lg border border-line bg-surface px-3 py-2 text-xs shadow-pop">
      {label != null && <div className="mb-1 font-medium text-ink">{label}</div>}
      {payload
        .filter((p: any) => p.value != null && !String(p.dataKey).startsWith('_'))
        .map((p: any) => (
          <div key={String(p.dataKey)} className="flex items-center justify-between gap-4 py-0.5">
            <span className="inline-flex items-center gap-1.5 text-ink-2">
              <span className="size-2 rounded-full" style={{ background: p.color || p.fill }} />
              {names?.[p.dataKey] ?? p.name ?? p.dataKey}
            </span>
            <span className="num font-medium text-ink">{Array.isArray(p.value) ? p.value.map((x: number) => format(x)).join(' – ') : format(Number(p.value))}</span>
          </div>
        ))}
    </div>
  );
};

/* ------------------------------------------------------------------ Pareto */

export const Pareto: React.FC<{
  items: { label: string; value: number; cumulative: number; planned?: boolean; color?: string }[];
  valueLabel: string;
  height?: number;
}> = ({ items, valueLabel, height = 280 }) => {
  const t = useChartTheme();
  return (
    <div style={{ height }}>
      <ResponsiveContainer width="100%" height="100%">
        <ComposedChart data={items} margin={{ top: 8, right: 8, bottom: 0, left: 0 }}>
          <CartesianGrid vertical={false} stroke={t.grid} />
          <XAxis dataKey="label" tick={axisTick(t)} tickLine={false} axisLine={{ stroke: t.axis }} interval={0} angle={-18} textAnchor="end" height={54} />
          <YAxis yAxisId="l" tick={axisTick(t)} tickLine={false} axisLine={false} width={44} />
          <YAxis yAxisId="r" orientation="right" domain={[0, 100]} tick={axisTick(t)} tickLine={false} axisLine={false} width={36} tickFormatter={(v) => `${v}%`} />
          <Tooltip content={<Tip names={{ value: valueLabel, cumulative: 'Cumulative share' }} format={(v: number) => (v <= 100 && v % 1 !== 0 ? `${v.toFixed(1)}` : Math.round(v).toLocaleString('en-IN'))} />} cursor={{ fill: t.grid, opacity: 0.5 }} />
          <ReferenceLine yAxisId="r" y={80} stroke={t.axis} strokeDasharray="3 4" />
          <Bar yAxisId="l" dataKey="value" radius={[5, 5, 0, 0]} maxBarSize={44} isAnimationActive={false}>
            {items.map((it, i) => (
              <Cell key={i} fill={it.color ?? (it.planned ? t.muted : catColor(0))} />
            ))}
          </Bar>
          <Line yAxisId="r" dataKey="cumulative" stroke={t.ink} strokeWidth={2} dot={{ r: 3, fill: t.surface, stroke: t.ink, strokeWidth: 1.6 }} isAnimationActive={false} />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
};

/* ------------------------------------------------------------------ Waterfall */

export const Waterfall: React.FC<{ items: { label: string; value: number; kind: 'total' | 'loss' }[]; format: (v: number) => string; height?: number }> = ({ items, format, height = 300 }) => {
  const t = useChartTheme();
  let running = 0;
  const data = items.map((it) => {
    if (it.kind === 'total') {
      running = it.value;
      return { label: it.label, base: 0, bar: it.value, kind: it.kind, shown: it.value };
    }
    const top = running;
    running += it.value; // value is negative
    return { label: it.label, base: running, bar: -it.value, kind: it.kind, shown: it.value, top };
  });
  return (
    <div style={{ height }}>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={{ top: 22, right: 8, bottom: 0, left: 0 }}>
          <CartesianGrid vertical={false} stroke={t.grid} />
          <XAxis dataKey="label" tick={axisTick(t)} tickLine={false} axisLine={{ stroke: t.axis }} interval={0} angle={-20} textAnchor="end" height={64} />
          <YAxis tick={axisTick(t)} tickLine={false} axisLine={false} width={48} tickFormatter={(v) => format(Number(v))} />
          <Tooltip content={<Tip format={format} names={{ bar: 'Amount' }} />} cursor={{ fill: t.grid, opacity: 0.4 }} />
          <Bar dataKey="base" stackId="w" fill="transparent" isAnimationActive={false} />
          <Bar dataKey="bar" stackId="w" radius={[4, 4, 0, 0]} maxBarSize={52} isAnimationActive={false}>
            {data.map((d, i) => (
              <Cell key={i} fill={d.kind === 'total' ? catColor(1) : 'rgb(var(--bad))'} fillOpacity={d.kind === 'total' ? 1 : 0.85} />
            ))}
            <LabelList dataKey="shown" position="top" formatter={(v: number) => (v < 0 ? `−${format(Math.abs(v))}` : format(v))} style={{ fontSize: 11, fill: t.ink, fontWeight: 600 }} />
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
};

/* ------------------------------------------------------------------ Stacked columns (downtime by category per day) */

export const StackedColumns: React.FC<{ rows: Record<string, number | string>[]; categories: string[]; xKey?: string; unit?: string; height?: number; labels?: Record<string, string> }> = ({
  rows,
  categories,
  xKey = 'label',
  unit = 'min',
  height = 260,
  labels,
}) => {
  const t = useChartTheme();
  return (
    <div className="space-y-2">
      <div className="flex flex-wrap gap-x-4 gap-y-1 text-xs text-ink-2">
        {categories.map((c) => (
          <span key={c} className="inline-flex items-center gap-1.5">
            <span className="size-2.5 rounded-sm" style={{ background: CATEGORY_COLORS[c] ?? '#8a99a8' }} />
            {labels?.[c] ?? c.charAt(0) + c.slice(1).toLowerCase().replace(/_/g, ' ')}
          </span>
        ))}
      </div>
      <div style={{ height }}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={rows} margin={{ top: 6, right: 8, bottom: 0, left: 0 }}>
            <CartesianGrid vertical={false} stroke={t.grid} />
            <XAxis dataKey={xKey} tick={axisTick(t)} tickLine={false} axisLine={{ stroke: t.axis }} minTickGap={10} />
            <YAxis tick={axisTick(t)} tickLine={false} axisLine={false} width={42} />
            <Tooltip content={<Tip format={(v: number) => `${Math.round(v)} ${unit}`} />} cursor={{ fill: t.grid, opacity: 0.4 }} />
            {categories.map((c, i) => (
              <Bar key={c} dataKey={c} stackId="s" fill={CATEGORY_COLORS[c] ?? catColor(i)} isAnimationActive={false} radius={i === categories.length - 1 ? [3, 3, 0, 0] : 0} />
            ))}
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

/* ------------------------------------------------------------------ Plan vs actual (cumulative) */

export const PlanVsActual: React.FC<{ rows: { hour: string; cum_actual_m: number; cum_plan_m: number }[]; height?: number }> = ({ rows, height = 220 }) => {
  const t = useChartTheme();
  return (
    <div style={{ height }}>
      <ResponsiveContainer width="100%" height="100%">
        <ComposedChart data={rows} margin={{ top: 6, right: 10, bottom: 0, left: 0 }}>
          <CartesianGrid vertical={false} stroke={t.grid} />
          <XAxis dataKey="hour" tick={axisTick(t)} tickLine={false} axisLine={{ stroke: t.axis }} minTickGap={14} />
          <YAxis tick={axisTick(t)} tickLine={false} axisLine={false} width={50} tickFormatter={(v) => `${Math.round(Number(v) / 100) / 10}k`} />
          <Tooltip content={<Tip format={(v: number) => `${Math.round(v).toLocaleString('en-IN')} m`} names={{ cum_actual_m: 'Woven', cum_plan_m: 'Plan' }} />} />
          <Area dataKey="cum_actual_m" stroke="none" fill={catColor(0)} fillOpacity={0.12} isAnimationActive={false} />
          <Line dataKey="cum_plan_m" stroke={t.muted} strokeWidth={2} strokeDasharray="4 4" dot={false} isAnimationActive={false} />
          <Line dataKey="cum_actual_m" stroke={catColor(0)} strokeWidth={2.4} dot={false} isAnimationActive={false} />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
};

/* ------------------------------------------------------------------ Sensor chart with the machine's own normal band */

export const SensorChart: React.FC<{
  points: { label: string; value: number }[];
  unit: string;
  normal: { center: number; low: number; high: number } | null;
  alarm: number | null;
  height?: number;
  color?: string;
}> = ({ points, unit, normal, alarm, height = 170, color }) => {
  const t = useChartTheme();
  const data = points.map((p) => ({ ...p, band: normal ? [normal.low, normal.high] : undefined }));
  const vals = points.map((p) => p.value);
  const lo = Math.min(...vals, normal?.low ?? Infinity, ...(alarm != null && alarm < Math.min(...vals) ? [alarm] : []));
  const hi = Math.max(...vals, normal?.high ?? -Infinity, ...(alarm != null && alarm <= Math.max(...vals) * 1.35 ? [alarm] : []));
  const pad = (hi - lo) * 0.12 || 0.5;
  return (
    <div style={{ height }}>
      <ResponsiveContainer width="100%" height="100%">
        <ComposedChart data={data} margin={{ top: 6, right: 14, bottom: 0, left: 0 }}>
          <CartesianGrid vertical={false} stroke={t.grid} />
          <XAxis dataKey="label" tick={axisTick(t)} tickLine={false} axisLine={{ stroke: t.axis }} minTickGap={16} />
          <YAxis tick={axisTick(t)} tickLine={false} axisLine={false} width={40} domain={[lo - pad, hi + pad]} tickFormatter={(v) => Number(v).toFixed(1)} />
          <Tooltip content={<Tip format={(v: number) => `${v.toFixed(2)} ${unit}`} names={{ value: 'Daily average', band: 'Normal range' }} />} />
          {normal && <Area dataKey="band" stroke="none" fill={catColor(2)} fillOpacity={0.16} isAnimationActive={false} activeDot={false} />}
          {normal && <ReferenceLine y={normal.center} stroke={catColor(2)} strokeDasharray="3 4" strokeOpacity={0.8} />}
          {alarm != null && <ReferenceLine y={alarm} stroke="rgb(var(--bad))" strokeDasharray="5 4" label={{ value: `alarm ${alarm}`, position: 'insideTopRight', fontSize: 10, fill: 'rgb(var(--bad))' }} />}
          <Line dataKey="value" stroke={color ?? t.ink} strokeWidth={2.2} dot={{ r: 2.5, fill: t.surface, stroke: color ?? t.ink, strokeWidth: 1.5 }} isAnimationActive={false} />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
};

/* ------------------------------------------------------------------ Radar for comparisons */

export const RadarCompare: React.FC<{ rows: Record<string, any>[]; keys: { key: string; label: string }[]; height?: number }> = ({ rows, keys, height = 300 }) => (
  <div style={{ height }}>
    <ResponsiveContainer width="100%" height="100%">
      <RadarChart data={rows} outerRadius="58%" margin={{ top: 10, right: 40, bottom: 10, left: 40 }}>
        <PolarGrid stroke="rgb(var(--line))" />
        <PolarAngleAxis dataKey="metric" tick={{ fontSize: 11, fill: 'rgb(var(--ink-2))' }} />
        <PolarRadiusAxis domain={[0, 100]} tick={false} axisLine={false} />
        {keys.map((k, i) => (
          <Radar key={k.key} name={k.label} dataKey={k.key} stroke={catColor(i)} fill={catColor(i)} fillOpacity={0.14} strokeWidth={2} isAnimationActive={false} />
        ))}
        <RLegend wrapperStyle={{ fontSize: 12 }} />
        <Tooltip content={<Tip format={(v: number) => `${Math.round(v)}/100`} />} />
      </RadarChart>
    </ResponsiveContainer>
  </div>
);

/* ------------------------------------------------------------------ Progress bar for orders */

export const ProgressBar: React.FC<{ pct: number; tone?: 'ok' | 'warn' | 'bad' | 'info'; className?: string }> = ({ pct, tone = 'info', className }) => (
  <div className={cn('h-2 w-full overflow-hidden rounded-full bg-muted', className)}>
    <div className={cn('h-full rounded-full', { ok: 'bg-ok', warn: 'bg-warn', bad: 'bg-bad', info: 'bg-accent' }[tone])} style={{ width: `${Math.max(0, Math.min(100, pct))}%` }} />
  </div>
);

/* ------------------------------------------------------------------ output bars with target and a forecast with its band */

export const ForecastChart: React.FC<{
  history: { label: string; meters: number; target_m: number; complete: boolean }[];
  forecast: { points: number[]; low: number[]; high: number[]; mape_pct: number | null } | null;
  height?: number;
}> = ({ history, forecast, height = 260 }) => {
  const t = useChartTheme();
  const last = history[history.length - 1];
  const rows: any[] = history.map((h) => ({ label: h.label, actual: h.complete ? h.meters : null, partial: h.complete ? null : h.meters, target: h.target_m }));
  if (forecast) {
    const lastDate = last ? new Date() : new Date();
    forecast.points.forEach((p, i) => {
      const d = new Date(lastDate);
      d.setDate(d.getDate() + i + 1);
      rows.push({ label: d.toLocaleDateString('en-GB', { day: '2-digit', month: 'short' }), forecast: Math.round(p), band: [Math.round(forecast.low[i]), Math.round(forecast.high[i])] });
    });
  }
  return (
    <div className="space-y-2">
      <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-ink-2">
        <span className="inline-flex items-center gap-1.5"><span className="size-2.5 rounded-sm" style={{ background: catColor(0) }} /> Woven</span>
        <span className="inline-flex items-center gap-1.5"><span className="h-0 w-4 border-t-2 border-dashed" style={{ borderColor: t.muted }} /> Target</span>
        {forecast && <span className="inline-flex items-center gap-1.5"><span className="h-0 w-4 border-t-2 border-dotted" style={{ borderColor: catColor(5) }} /> Forecast (80% band){forecast.mape_pct != null && <span className="text-ink-3"> · past error {forecast.mape_pct}%</span>}</span>}
      </div>
      <div style={{ height }}>
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={rows} margin={{ top: 6, right: 8, bottom: 0, left: 0 }}>
            <CartesianGrid vertical={false} stroke={t.grid} />
            <XAxis dataKey="label" tick={axisTick(t)} tickLine={false} axisLine={{ stroke: t.axis }} minTickGap={12} />
            <YAxis tick={axisTick(t)} tickLine={false} axisLine={false} width={48} tickFormatter={(v) => `${Math.round(Number(v) / 100) / 10}k`} />
            <Tooltip content={<Tip format={(v: number) => `${Math.round(v).toLocaleString('en-IN')} m`} names={{ actual: 'Woven', partial: 'Today so far', target: 'Target', forecast: 'Forecast', band: 'Likely range' }} />} cursor={{ fill: t.grid, opacity: 0.4 }} />
            <Area dataKey="band" stroke="none" fill={catColor(5)} fillOpacity={0.14} isAnimationActive={false} activeDot={false} />
            <Bar dataKey="actual" fill={catColor(0)} radius={[4, 4, 0, 0]} maxBarSize={26} isAnimationActive={false} />
            <Bar dataKey="partial" fill={catColor(0)} fillOpacity={0.35} radius={[4, 4, 0, 0]} maxBarSize={26} isAnimationActive={false} />
            <Line dataKey="target" stroke={t.muted} strokeWidth={2} strokeDasharray="4 4" dot={false} isAnimationActive={false} />
            <Line dataKey="forecast" stroke={catColor(5)} strokeWidth={2.2} strokeDasharray="2 4" dot={{ r: 3, fill: t.surface, stroke: catColor(5), strokeWidth: 1.6 }} isAnimationActive={false} />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};
