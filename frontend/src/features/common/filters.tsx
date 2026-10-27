import React from 'react';
import { useSearchParams } from 'react-router-dom';
import { CalendarRange } from 'lucide-react';
import { usePeriod } from '../../app/state';
import { useMeta, type FilterQuery } from '../../api/mill';
import { PERIODS, type Period } from '../../lib/period';
import { Segmented, Select } from '../../design/ui';

/** Filters live in the URL so every view can be bookmarked and shared exactly as seen. */
export function useFilters(): FilterQuery & { period: Period } {
  const [period] = usePeriod();
  const [params] = useSearchParams();
  const get = (k: string) => params.get(k) || undefined;
  return {
    period,
    date_from: period === 'custom' ? get('date_from') : undefined,
    date_to: period === 'custom' ? get('date_to') : undefined,
    category: get('category'),
    shift: get('shift'),
    source: get('source'),
    group_id: get('group_id'),
  };
}

const setParam = (setParams: ReturnType<typeof useSearchParams>[1], key: string, v: string | null) =>
  setParams(
    (prev) => {
      const next = new URLSearchParams(prev);
      if (!v) next.delete(key);
      else next.set(key, v);
      return next;
    },
    { replace: true },
  );

export const FilterBar: React.FC<{ show?: ('category' | 'shift' | 'source' | 'group')[]; children?: React.ReactNode }> = ({
  show = ['category', 'shift', 'source'],
  children,
}) => {
  const [period, setPeriod] = usePeriod();
  const [params, setParams] = useSearchParams();
  const meta = useMeta();
  const range = meta.data?.data_range;
  return (
    <div className="flex flex-wrap items-center gap-2">
      <Segmented<Period> size="sm" ariaLabel="Period" value={period} onChange={setPeriod} options={PERIODS.map((p) => ({ value: p.value, label: p.short }))} />
      {period === 'custom' && (
        <span className="inline-flex items-center gap-1 text-xs text-ink-3">
          <CalendarRange className="size-3.5" />
          {(['date_from', 'date_to'] as const).map((k) => (
            <input
              key={k}
              type="date"
              aria-label={k === 'date_from' ? 'From' : 'To'}
              min={range?.first ?? undefined}
              max={range?.last ?? undefined}
              value={params.get(k) ?? ''}
              onChange={(e) => setParam(setParams, k, e.target.value)}
              className="h-7 rounded-md border border-line bg-surface px-2 text-xs text-ink"
            />
          ))}
        </span>
      )}
      {show.includes('category') && (
        <Select
          aria-label="Machine category"
          value={params.get('category') ?? ''}
          onChange={(e) => setParam(setParams, 'category', e.target.value)}
          options={[{ value: '', label: 'All machines' }, ...(meta.data?.categories ?? []).map((c) => ({ value: c.code, label: `${c.code} · ${c.name}` }))]}
        />
      )}
      {show.includes('shift') && (
        <Select
          aria-label="Shift"
          value={params.get('shift') ?? ''}
          onChange={(e) => setParam(setParams, 'shift', e.target.value)}
          options={[{ value: '', label: 'All shifts' }, ...(meta.data?.shifts ?? []).map((s) => ({ value: s.code, label: `Shift ${s.code} (${s.start}–${s.end})` }))]}
        />
      )}
      {show.includes('group') && (meta.data?.groups.length ?? 0) > 0 && (
        <Select
          aria-label="Group"
          value={params.get('group_id') ?? ''}
          onChange={(e) => setParam(setParams, 'group_id', e.target.value)}
          options={[{ value: '', label: 'All groups' }, ...(meta.data?.groups ?? []).map((g) => ({ value: String(g.id), label: g.name }))]}
        />
      )}
      {show.includes('source') && (
        <Select
          aria-label="Data source"
          value={params.get('source') ?? ''}
          onChange={(e) => setParam(setParams, 'source', e.target.value)}
          options={[
            { value: '', label: 'Best source' },
            { value: 'MILL_REPORT', label: 'Mill report only' },
            { value: 'MACHINE_EXPORT', label: 'Machine exports only' },
          ]}
        />
      )}
      {children}
    </div>
  );
};
