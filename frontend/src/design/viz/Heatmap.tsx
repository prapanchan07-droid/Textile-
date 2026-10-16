import React from 'react';
import { cn } from '../../lib/format';

/** Dark text on pale cells, white on deep ones, so every printed value stays readable. */
const textOn = (bg: string) => {
  const m = bg.match(/\d+/g);
  if (!m || m.length < 3) return 'rgb(255 255 255 / 0.95)';
  const [r, g, b] = m.slice(0, 3).map(Number);
  return (0.299 * r + 0.587 * g + 0.114 * b) / 255 > 0.62 ? 'rgb(23 34 42 / 0.9)' : 'rgb(255 255 255 / 0.95)';
};

export interface HeatRow {
  label: string;
  sublabel?: string;
  values: (number | null)[];
}

/** A grid of coloured cells: loom x day, weekday x hour, style x shift. Every cell is readable by hover, and the legend says what the colours mean. */
export const Heatmap: React.FC<{
  columns: string[];
  rows: HeatRow[];
  color: (v: number) => string;
  format: (v: number) => string;
  cell?: number;
  labelWidth?: number;
  showValues?: boolean;
  legend?: { low: string; high: string; swatches: string[] };
  onRowClick?: (label: string) => void;
  columnEvery?: number;
}> = ({ columns, rows, color, format, cell = 26, labelWidth = 72, showValues = false, legend, onRowClick, columnEvery = 1 }) => (
  <div className="space-y-2">
    <div className="overflow-x-auto pb-1">
      <div style={{ minWidth: labelWidth + columns.length * (cell + 2) }}>
        <div className="flex items-end" style={{ paddingLeft: labelWidth }}>
          {columns.map((c, i) => (
            <div key={c + i} style={{ width: cell, marginRight: 2 }} className="shrink-0 truncate text-center text-[10px] leading-4 text-ink-3" title={c}>
              {i % columnEvery === 0 ? c : ''}
            </div>
          ))}
        </div>
        {rows.map((r) => (
          <div key={r.label} className="mt-[2px] flex items-center">
            <button
              type="button"
              onClick={onRowClick ? () => onRowClick(r.label) : undefined}
              style={{ width: labelWidth }}
              className={cn('shrink-0 truncate pr-2 text-left text-xs font-medium text-ink-2', onRowClick ? 'hover:text-accent' : 'cursor-default')}
              title={r.sublabel ? `${r.label} · ${r.sublabel}` : r.label}
            >
              {r.label}
            </button>
            {r.values.map((v, i) => (
              <div
                key={i}
                title={`${r.label} · ${columns[i]}: ${v == null ? 'no data' : format(v)}`}
                style={{ width: cell, height: cell * 0.78, marginRight: 2, ...(v == null ? {} : { background: color(v), color: textOn(color(v)) }) }}
                className={cn('flex shrink-0 items-center justify-center rounded-[4px] text-[9px] font-medium', v == null && 'bg-muted')}
              >
                {showValues && v != null ? format(v) : ''}
              </div>
            ))}
          </div>
        ))}
      </div>
    </div>
    {legend && (
      <div className="flex items-center gap-2 text-[11px] text-ink-3">
        <span>{legend.low}</span>
        <span className="flex overflow-hidden rounded">
          {legend.swatches.map((s) => (
            <span key={s} style={{ background: s }} className="h-2.5 w-6" />
          ))}
        </span>
        <span>{legend.high}</span>
        <span className="ml-2 inline-flex items-center gap-1">
          <span className="inline-block h-2.5 w-4 rounded-sm bg-muted" /> no data
        </span>
      </div>
    )}
  </div>
);
