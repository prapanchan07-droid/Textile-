import React from 'react';
import { Link } from 'react-router-dom';
import { Database, FlaskConical, Radio, RadioTower, Sigma, Unplug } from 'lucide-react';
import { Badge, Notice, StatusPill, type Tone } from '../../design/ui';
import { cn, relativeTime } from '../../lib/format';
import type { Basis, Freshness, PeriodMeta, Severity, Source } from '../../types/mill';

export const PageTitle: React.FC<{ title: string; subtitle?: React.ReactNode; actions?: React.ReactNode }> = ({ title, subtitle, actions }) => (
  <div className="mb-5 flex flex-wrap items-end justify-between gap-3">
    <div className="min-w-0">
      <h1 className="text-xl font-semibold tracking-tight text-ink">{title}</h1>
      {subtitle && <p className="mt-1 text-sm text-ink-3">{subtitle}</p>}
    </div>
    {actions && <div className="flex flex-wrap items-center gap-2">{actions}</div>}
  </div>
);

const fmtDate = (d: string | null | undefined) =>
  d ? new Date(`${d}T00:00:00`).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' }) : '—';

export const periodText = (p?: { date_from: string | null; date_to: string | null }) =>
  !p?.date_from ? 'No data yet' : p.date_from === p.date_to ? fmtDate(p.date_from) : `${fmtDate(p.date_from)} – ${fmtDate(p.date_to)}`;

const SOURCE_LABEL: Record<Source, string> = { MILL_REPORT: 'Mill report', MACHINE_EXPORT: 'Machine export' };

export const SourceBadge: React.FC<{ source: Source | string }> = ({ source }) => (
  <Badge tone={source === 'MACHINE_EXPORT' ? 'info' : 'neutral'}>{SOURCE_LABEL[source as Source] ?? source}</Badge>
);

const BASIS: Record<Basis, { label: string; tone: Tone; title: string }> = {
  MEASURED: { label: 'Measured', tone: 'ok', title: 'Read from a report or machine' },
  CALCULATED: { label: 'Calculated', tone: 'neutral', title: 'Computed from measured values with a documented formula' },
  STATISTICAL: { label: 'Statistical', tone: 'info', title: 'An unusual value compared with history; not a diagnosis' },
  MODELED: { label: 'Modeled estimate', tone: 'warn', title: 'Depends on stated assumptions; a potential, not a realised value' },
  DATA: { label: 'Data gap', tone: 'neutral', title: 'Needed data is missing' },
};

export const BasisBadge: React.FC<{ basis: Basis }> = ({ basis }) => {
  const b = BASIS[basis] ?? BASIS.CALCULATED;
  return (
    <span title={b.title}>
      <Badge tone={b.tone}>
        {basis === 'MODELED' ? <FlaskConical className="mr-1 size-3" /> : basis === 'CALCULATED' ? <Sigma className="mr-1 size-3" /> : null}
        {b.label}
      </Badge>
    </span>
  );
};

export const SeverityPill: React.FC<{ severity: Severity }> = ({ severity }) => (
  <StatusPill tone={severity === 'CRITICAL' ? 'bad' : severity === 'WARNING' ? 'warn' : 'info'} label={severity === 'INFO' ? 'Info' : severity === 'WARNING' ? 'Warning' : 'Critical'} />
);

/** Live machine state. Only a fresh reading through a configured connection is ever shown as "live". */
export const LiveState: React.FC<{ state: string; origin?: string | null; machineState?: string | null; compact?: boolean }> = ({ state, origin, machineState, compact }) => {
  const map: Record<string, { tone: Tone; label: string }> = {
    CONNECTED: { tone: 'ok', label: machineState === 'STOPPED' ? 'Stopped (live)' : machineState === 'RUNNING' ? 'Running (live)' : 'Connected' },
    STALE: { tone: 'warn', label: 'Data stale' },
    OFFLINE: { tone: 'bad', label: 'Offline' },
    ERROR: { tone: 'bad', label: 'Connection error' },
    AWAITING_VENDOR_INFO: { tone: 'neutral', label: 'Awaiting vendor info' },
    CONFIGURED: { tone: 'neutral', label: 'Configured, not polling' },
    NOT_CONFIGURED: { tone: 'neutral', label: 'No live feed' },
  };
  const m = map[state] ?? { tone: 'neutral' as Tone, label: state };
  if (state === 'CONNECTED' && machineState === 'STOPPED') m.tone = 'bad';
  return (
    <span className="inline-flex items-center gap-1">
      {!compact && (state === 'NOT_CONFIGURED' ? <Unplug className="size-3 text-ink-3" /> : <Radio className="size-3 text-ink-3" />)}
      <StatusPill tone={m.tone} label={m.label} />
      {origin === 'SIMULATED' && <Badge tone="warn">Simulated</Badge>}
    </span>
  );
};

/** Where the numbers come from and how fresh they are. Imported data is never presented as live. */
export const FreshnessLine: React.FC<{ freshness?: Freshness; period?: PeriodMeta; className?: string }> = ({ freshness, period, className }) => {
  if (!freshness) return null;
  const latest = Object.entries(freshness.latest_by_category)
    .map(([cat, s]) => `${cat} ${Object.values(s).sort().slice(-1)[0] ?? '—'}`)
    .join(' · ');
  return (
    <div className={cn('flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-ink-3', className)}>
      {period && (
        <span className="inline-flex items-center gap-1">
          <Database className="size-3.5" /> {periodText(period)} · {period.days_with_data} day(s) with data
          {Object.keys(period.sources).length > 0 && (
            <span className="ml-1 inline-flex gap-1">
              {Object.keys(period.sources).map((s) => (
                <SourceBadge key={s} source={s} />
              ))}
            </span>
          )}
        </span>
      )}
      <span>Latest data: {latest || 'none imported'}</span>
      <span>Last import: {relativeTime(freshness.last_import_at) ?? 'never'}</span>
      <span className="inline-flex items-center gap-1">
        <RadioTower className="size-3.5" />
        {freshness.live_feed === 'NONE' ? 'No live machine feed' : freshness.live_feed === 'SIMULATED' ? 'Live feed: simulator only' : 'Live feed connected'}
      </span>
    </div>
  );
};

export const NoData: React.FC<{ what?: string }> = ({ what = 'production data' }) => (
  <Notice tone="info" action={<Link to="/imports" className="text-sm font-medium text-accent hover:underline">Import reports</Link>}>
    No {what} for this selection. Import the mill's reports or widen the period.
  </Notice>
);

export const Field: React.FC<{ label: string; children: React.ReactNode; hint?: string }> = ({ label, children, hint }) => (
  <label className="block">
    <span className="mb-1 block text-xs font-medium text-ink-2">{label}</span>
    {children}
    {hint && <span className="mt-1 block text-2xs text-ink-3">{hint}</span>}
  </label>
);

export const inputClass = 'h-9 w-full rounded-lg border border-line bg-surface px-2.5 text-sm text-ink outline-none focus:border-accent focus:ring-2 focus:ring-accent/20';

export const fmt = {
  date: fmtDate,
  dateTime: (d: string | null | undefined) =>
    d ? new Date(d).toLocaleString('en-IN', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' }) : '—',
  n: (v: number | null | undefined, digits = 0) => (v == null ? '—' : v.toLocaleString('en-IN', { maximumFractionDigits: digits, minimumFractionDigits: digits })),
  rate: (v: number | null | undefined) => (v == null ? '—' : v.toFixed(2)),
};
