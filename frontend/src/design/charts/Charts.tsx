import React from 'react';
import {
  Area,
  Bar,
  BarChart,
  CartesianGrid,
  ComposedChart,
  Line,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  type TooltipProps,
} from 'recharts';
import { cn } from '../../lib/format';
import { axisTick, useChartTheme, type ChartTheme } from './theme';

export interface Series {
  key: string;
  label: string;
  /** Categorical slot (0-2) or 'muted' for a reference series such as target / previous period. */
  color: 0 | 1 | 2 | 'muted';
}

const colorOf = (t: ChartTheme, c: Series['color']) => (c === 'muted' ? t.muted : t.series[c]);

/* ------------------------------------------------------------------ Legend */

export const Legend: React.FC<{ items: { label: string; color: string; kind?: 'line' | 'box' | 'dash' }[] }> = ({ items }) => (
  <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-ink-2">
    {items.map((i) => (
      <span key={i.label} className="inline-flex items-center gap-1.5">
        {i.kind === 'line' ? (
          <span className="h-0.5 w-3.5 rounded-full" style={{ background: i.color }} />
        ) : i.kind === 'dash' ? (
          <span className="h-0 w-3.5 border-t-2 border-dotted" style={{ borderColor: i.color }} />
        ) : (
          <span className="size-2.5 rounded-sm" style={{ background: i.color }} />
        )}
        {i.label}
      </span>
    ))}
  </div>
);

/* ------------------------------------------------------------------ Tooltip */

const ChartTooltip: React.FC<TooltipProps<number, string> & { format: (v: number) => string; labels: Record<string, string> }> = ({
  active,
  payload,
  label,
  format,
  labels,
}) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="min-w-36 rounded-md border border-line bg-surface px-3 py-2 text-xs shadow-pop">
      <div className="mb-1 font-medium text-ink">{label}</div>
      {payload
        .filter((p) => labels[String(p.dataKey)])
        .map((p) => (
          <div key={String(p.dataKey)} className="flex items-center justify-between gap-4 py-0.5">
            <span className="inline-flex items-center gap-1.5 text-ink-2">
              <span className="size-2 rounded-full" style={{ background: p.color }} />
              {labels[String(p.dataKey)]}
            </span>
            <span className="num font-medium text-ink">{format(Number(p.value))}</span>
          </div>
        ))}
    </div>
  );
};

/* ------------------------------------------------------------------ Trend (line) */

export interface TrendChartProps<T> {
  data: T[];
  xKey: keyof T & string;
  series: Series[];
  format: (v: number) => string;
  /** Tick formatter; defaults to `format`. */
  axisFormat?: (v: number) => string;
  /** Horizontal reference such as a spec limit or factory average. */
  reference?: { value: number; label: string };
  height?: number;
  /** Fill a light wash under a single series. */
  area?: boolean;
  yDomain?: [number | 'auto' | 'dataMin', number | 'auto' | 'dataMax'];
}

export function TrendChart<T>({
  data,
  xKey,
  series,
  format,
  axisFormat = format,
  reference,
  height = 240,
  area,
  yDomain,
}: TrendChartProps<T>) {
  const t = useChartTheme();
  const labels = Object.fromEntries(series.map((s) => [s.key, s.label]));
  const legendItems = [
    ...series.map((s) => ({ label: s.label, color: colorOf(t, s.color), kind: 'line' as const })),
    ...(reference ? [{ label: reference.label, color: t.critical, kind: 'dash' as const }] : []),
  ];
  const lastIndex = data.length - 1;

  return (
    <div className="space-y-2">
      {legendItems.length > 1 && <Legend items={legendItems} />}
      <div style={{ height }}>
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={data} margin={{ top: 8, right: 12, bottom: 0, left: 0 }}>
            <CartesianGrid vertical={false} stroke={t.grid} />
            <XAxis dataKey={xKey} tick={axisTick(t)} tickLine={false} axisLine={{ stroke: t.axis }} minTickGap={16} />
            <YAxis
              tick={axisTick(t)}
              tickLine={false}
              axisLine={false}
              width={56}
              tickFormatter={(v) => axisFormat(Number(v))}
              domain={yDomain ?? ['auto', 'auto']}
            />
            <Tooltip cursor={{ stroke: t.axis, strokeWidth: 1 }} content={<ChartTooltip format={format} labels={labels} />} />
            {reference && (
              <ReferenceLine y={reference.value} stroke={t.critical} strokeWidth={1.5} strokeDasharray="2 3" ifOverflow="extendDomain" />
            )}
            {area && series.length === 1 && (
              <Area
                dataKey={series[0].key}
                stroke="none"
                fill={colorOf(t, series[0].color)}
                fillOpacity={0.1}
                isAnimationActive={false}
                activeDot={false}
                tooltipType="none"
              />
            )}
            {series.map((s) => (
              <Line
                key={s.key}
                dataKey={s.key}
                stroke={colorOf(t, s.color)}
                strokeWidth={2}
                strokeLinecap="round"
                strokeLinejoin="round"
                isAnimationActive={false}
                // Only the latest point gets a marker; the rest is the line.
                dot={(p: { index: number; cx: number; cy: number }) =>
                  p.index === lastIndex ? (
                    <circle key={p.index} cx={p.cx} cy={p.cy} r={4} fill={colorOf(t, s.color)} stroke={t.surface} strokeWidth={2} />
                  ) : (
                    <g key={p.index} />
                  )
                }
                activeDot={{ r: 5, fill: colorOf(t, s.color), stroke: t.surface, strokeWidth: 2 }}
              />
            ))}
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ Columns */

export interface ColumnChartProps<T> {
  data: T[];
  xKey: keyof T & string;
  series: Series[];
  format: (v: number) => string;
  axisFormat?: (v: number) => string;
  height?: number;
}

/** Grouped columns, typically actual (slot 1) beside target (muted). */
export function ColumnChart<T>({ data, xKey, series, format, axisFormat = format, height = 240 }: ColumnChartProps<T>) {
  const t = useChartTheme();
  const labels = Object.fromEntries(series.map((s) => [s.key, s.label]));
  return (
    <div className="space-y-2">
      {series.length > 1 && <Legend items={series.map((s) => ({ label: s.label, color: colorOf(t, s.color) }))} />}
      <div style={{ height }}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} margin={{ top: 8, right: 12, bottom: 0, left: 0 }} barGap={2} barCategoryGap="28%">
            <CartesianGrid vertical={false} stroke={t.grid} />
            <XAxis dataKey={xKey} tick={axisTick(t)} tickLine={false} axisLine={{ stroke: t.axis }} interval={0} />
            <YAxis tick={axisTick(t)} tickLine={false} axisLine={false} width={56} tickFormatter={(v) => axisFormat(Number(v))} />
            <Tooltip cursor={{ fill: t.grid, fillOpacity: 0.5 }} content={<ChartTooltip format={format} labels={labels} />} />
            {series.map((s) => (
              <Bar key={s.key} dataKey={s.key} fill={colorOf(t, s.color)} radius={[4, 4, 0, 0]} maxBarSize={24} isAnimationActive={false} />
            ))}
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ Ranked bars (HTML) */

export interface RankedItem {
  label: string;
  value: number;
  /** Optional share of total, shown after the value. */
  share?: number;
  sublabel?: string;
}

/**
 * Horizontal ranked bars for "what contributes most" (loss reasons, downtime causes).
 * One series, one color: length already encodes magnitude, so hue stays constant.
 */
export const RankedBars: React.FC<{
  items: RankedItem[];
  format: (v: number) => string;
  className?: string;
}> = ({ items, format, className }) => {
  const t = useChartTheme();
  const max = Math.max(...items.map((i) => i.value), 0);
  return (
    <ul className={cn('space-y-3', className)}>
      {items.map((i) => (
        <li key={i.label} title={`${i.label}: ${format(i.value)}${i.share != null ? ` (${i.share.toFixed(1)}%)` : ''}`}>
          <div className="mb-1 flex items-baseline justify-between gap-3 text-sm">
            <span className="truncate text-ink">{i.label}</span>
            <span className="num shrink-0 text-ink">
              {format(i.value)}
              {i.share != null && <span className="ml-1.5 text-xs text-ink-3">{i.share.toFixed(1)}%</span>}
            </span>
          </div>
          <div className="h-2 w-full rounded-full bg-muted">
            <div
              className="h-full rounded-r-[4px] rounded-l-full"
              style={{ width: `${max > 0 ? (i.value / max) * 100 : 0}%`, background: t.series[0] }}
            />
          </div>
          {i.sublabel && <p className="mt-1 text-xs text-ink-3">{i.sublabel}</p>}
        </li>
      ))}
    </ul>
  );
};

/** A stacked bar that splits one total into parts (planned vs unplanned downtime). */
export const SplitBar: React.FC<{
  parts: { label: string; value: number; color: 0 | 1 | 2 | 'muted' }[];
  format: (v: number) => string;
}> = ({ parts, format }) => {
  const t = useChartTheme();
  const total = parts.reduce((s, p) => s + p.value, 0);
  return (
    <div className="space-y-2">
      <div className="flex h-2.5 w-full gap-0.5 overflow-hidden rounded-full">
        {parts.map((p) => (
          <div
            key={p.label}
            title={`${p.label}: ${format(p.value)}`}
            style={{ width: `${total ? (p.value / total) * 100 : 0}%`, background: colorOf(t, p.color) }}
          />
        ))}
      </div>
      <Legend
        items={parts.map((p) => ({
          label: `${p.label} · ${format(p.value)}${total ? ` (${Math.round((p.value / total) * 100)}%)` : ''}`,
          color: colorOf(t, p.color),
        }))}
      />
    </div>
  );
};
