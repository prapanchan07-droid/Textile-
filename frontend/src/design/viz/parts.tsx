import React, { useState } from 'react';
import { AlertTriangle, ArrowRight, CheckCircle2, ChevronDown, AlertCircle, FlaskConical, Info, Lightbulb, Plus, ShieldQuestion, Sparkles, Thermometer, Wrench } from 'lucide-react';
import { Link } from 'react-router-dom';
import { cn, inrFromLakhs } from '../../lib/format';
import { useCreateAction } from '../../api/weaving';
import type { Finding, SensorAlert } from '../../types/pages';
import { Button } from '../ui';
import { BAND, catColor } from './palette';

/* ------------------------------------------------------------------ small labels */

export const AiBadge: React.FC<{ label?: string; title?: string; className?: string }> = ({ label = 'AI', title = 'Computed by the platform from your data using statistical models. Not a person’s opinion.', className }) => (
  <span title={title} className={cn('inline-flex items-center gap-1 rounded-full bg-gradient-to-r from-accent to-[#7c6bd6] px-2 py-0.5 text-[10px] font-semibold tracking-wide text-white', className)}>
    <Sparkles className="size-3" /> {label}
  </span>
);

const SEV: Record<string, string> = { HIGH: 'bg-bad-soft text-bad border-bad/30', MEDIUM: 'bg-warn-soft text-warn border-warn/30', LOW: 'bg-muted text-ink-3 border-line' };
const SEV_LABEL: Record<string, string> = { HIGH: 'Urgent', MEDIUM: 'Important', LOW: 'Low' };
export const SeverityChip: React.FC<{ s: string }> = ({ s }) => <span className={cn('inline-flex rounded-md border px-1.5 py-0.5 text-2xs font-semibold', SEV[s] ?? SEV.LOW)}>{SEV_LABEL[s] ?? s}</span>;

const LEVEL: Record<string, string> = { CRITICAL: 'bg-bad text-white', WARNING: 'bg-warn text-white', WATCH: 'bg-accent-soft text-accent-ink' };
export const LevelChip: React.FC<{ level: string }> = ({ level }) => <span className={cn('inline-flex rounded-md px-1.5 py-0.5 text-2xs font-semibold', LEVEL[level] ?? 'bg-muted text-ink-3')}>{level.charAt(0) + level.slice(1).toLowerCase()}</span>;

const RISK: Record<string, [string, string]> = {
  LATE: ['Late', 'bg-bad-soft text-bad'],
  AT_RISK: ['At risk', 'bg-warn-soft text-warn'],
  ON_TRACK: ['On track', 'bg-ok-soft text-ok'],
  UNSCHEDULED: ['Not scheduled', 'bg-muted text-ink-2'],
  STALLED: ['Stalled', 'bg-bad-soft text-bad'],
  UNKNOWN: ['No estimate', 'bg-muted text-ink-3'],
  DONE: ['Done', 'bg-ok-soft text-ok'],
};
export const RiskChip: React.FC<{ risk: string }> = ({ risk }) => {
  const [label, cls] = RISK[risk] ?? [risk, 'bg-muted text-ink-3'];
  return <span className={cn('inline-flex rounded-md px-2 py-0.5 text-2xs font-semibold', cls)}>{label}</span>;
};

export const PriorityDot: React.FC<{ p: 'A' | 'B' | 'C' }> = ({ p }) => (
  <span title={`Priority ${p}`} className={cn('inline-grid size-5 place-items-center rounded-md text-[10px] font-bold', p === 'A' ? 'bg-bad-soft text-bad' : p === 'B' ? 'bg-warn-soft text-warn' : 'bg-muted text-ink-3')}>{p}</span>
);

export const ConfidencePill: React.FC<{ level: 'HIGH' | 'MEDIUM' | 'LOW'; reasons?: string[] }> = ({ level, reasons }) => {
  const n = level === 'HIGH' ? 3 : level === 'MEDIUM' ? 2 : 1;
  return (
    <span title={reasons?.join('\n')} className="inline-flex items-center gap-1.5 text-xs text-ink-2">
      <span className="inline-flex gap-0.5">
        {[1, 2, 3].map((i) => (
          <span key={i} className={cn('h-3 w-1.5 rounded-sm', i <= n ? (level === 'LOW' ? 'bg-warn' : 'bg-ok') : 'bg-muted')} />
        ))}
      </span>
      {level.charAt(0) + level.slice(1).toLowerCase()} confidence
    </span>
  );
};

/* ------------------------------------------------------------------ health ring */

export const HealthRing: React.FC<{ score: number | null; band?: string | null; size?: number; label?: boolean }> = ({ score, band, size = 56, label = true }) => {
  const s = score ?? 0;
  const color = BAND[(band as keyof typeof BAND) ?? (s >= 80 ? 'HEALTHY' : s >= 60 ? 'WATCH' : 'AT_RISK')];
  const r = size / 2 - 5;
  const c = 2 * Math.PI * r;
  return (
    <div className="relative inline-grid place-items-center" style={{ width: size, height: size }} title={score == null ? 'No health score' : `Health score ${score} of 100`}>
      <svg width={size} height={size} className="-rotate-90">
        <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="rgb(var(--muted))" strokeWidth="5" />
        <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke={color} strokeWidth="5" strokeLinecap="round" strokeDasharray={`${(s / 100) * c} ${c}`} />
      </svg>
      {label && <span className="num absolute font-semibold text-ink" style={{ fontSize: Math.max(10, size * 0.3) }}>{score ?? '—'}</span>}
    </div>
  );
};

/* ------------------------------------------------------------------ floor strip */

export const FloorStrip: React.FC<{
  looms: { loom: string; type: string; status: 'RUNNING' | 'STOPPED' | 'IDLE'; efficiency_pct: number | null; health?: number | null; alerts?: string[]; reason?: string | null; stopped_min?: number }[];
  onSelect?: (loom: string) => void;
}> = ({ looms, onSelect }) => (
  <div>
    <div className="grid gap-1.5" style={{ gridTemplateColumns: 'repeat(auto-fill, minmax(58px, 1fr))' }}>
      {looms.map((l) => {
        const hot = l.alerts?.includes('CRITICAL');
        const warn = l.alerts?.some((a) => a === 'WARNING' || a === 'WATCH');
        return (
          <button
            key={l.loom}
            onClick={onSelect ? () => onSelect(l.loom) : undefined}
            title={`${l.loom} · ${l.type}\n${l.status === 'STOPPED' ? `Stopped ${l.stopped_min} min: ${l.reason}` : l.status === 'IDLE' ? 'No order' : 'Running'}${l.efficiency_pct != null ? `\nEfficiency ${l.efficiency_pct}%` : ''}${l.health != null ? `\nHealth ${l.health}` : ''}${l.alerts?.length ? `\nAlerts: ${l.alerts.join(', ')}` : ''}`}
            className={cn(
              'relative flex h-12 flex-col items-center justify-center rounded-lg border text-[10px] font-semibold leading-tight transition-transform hover:-translate-y-0.5',
              l.status === 'STOPPED' ? 'border-bad/50 bg-bad-soft text-bad' : l.status === 'IDLE' ? 'border-line bg-muted text-ink-3' : 'border-ok/30 bg-ok-soft text-ok',
            )}
          >
            <span>{l.loom}</span>
            <span className="num text-[9px] font-medium opacity-80">{l.status === 'STOPPED' ? `${l.stopped_min}m` : l.efficiency_pct != null ? `${Math.round(l.efficiency_pct)}%` : '–'}</span>
            {(hot || warn) && <span className={cn('absolute -right-1 -top-1 size-2.5 rounded-full ring-2 ring-surface', hot ? 'bg-bad' : 'bg-warn')} />}
          </button>
        );
      })}
    </div>
    <div className="mt-2 flex flex-wrap items-center gap-x-4 gap-y-1 text-[11px] text-ink-3">
      <span className="inline-flex items-center gap-1"><span className="size-2.5 rounded-sm bg-ok-soft ring-1 ring-ok/40" /> Running</span>
      <span className="inline-flex items-center gap-1"><span className="size-2.5 rounded-sm bg-bad-soft ring-1 ring-bad/50" /> Stopped (minutes)</span>
      <span className="inline-flex items-center gap-1"><span className="size-2.5 rounded-sm bg-muted ring-1 ring-line" /> No order</span>
      <span className="inline-flex items-center gap-1"><span className="size-2 rounded-full bg-warn" /> machine watch</span>
    </div>
  </div>
);

/* ------------------------------------------------------------------ Gantt timeline */

export const Gantt: React.FC<{
  rows: { loom: string; segs: { order: string | null; style: string | null; start_day: number; end_day: number; metres: number }[] }[];
  horizon: number;
  orderColor: (order: string) => string;
  startDate: string;
  dueMarks?: { order: string; day: number }[];
}> = ({ rows, horizon, orderColor, startDate, dueMarks = [] }) => {
  const d0 = new Date(startDate);
  const ticks = Array.from({ length: Math.floor(horizon / 7) + 1 }, (_, i) => i * 7).filter((d) => d < horizon);
  const label = (d: number) => {
    const x = new Date(d0);
    x.setDate(x.getDate() + d);
    return x.toLocaleDateString('en-GB', { day: '2-digit', month: 'short' });
  };
  return (
    <div className="overflow-x-auto">
      <div className="min-w-[640px]">
        <div className="relative ml-14 h-5 text-[10px] text-ink-3">
          {ticks.map((d) => (
            <span key={d} className="absolute -translate-x-1/2" style={{ left: `${(d / horizon) * 100}%` }}>{label(d)}</span>
          ))}
        </div>
        <div className="space-y-[3px]">
          {rows.map((r) => (
            <div key={r.loom} className="flex items-center">
              <div className="w-14 shrink-0 pr-2 text-xs font-medium text-ink-2">{r.loom}</div>
              <div className="relative h-5 flex-1 overflow-hidden rounded bg-muted/60">
                {ticks.map((d) => (
                  <span key={d} className="absolute inset-y-0 w-px bg-line/70" style={{ left: `${(d / horizon) * 100}%` }} />
                ))}
                {r.segs
                  .filter((s) => s.order)
                  .map((s, i) => (
                    <div
                      key={i}
                      title={`${r.loom}: ${s.order} (${s.style}) · ${label(s.start_day)} to ${label(s.end_day)} · about ${s.metres.toLocaleString('en-IN')} m`}
                      className="absolute inset-y-0.5 overflow-hidden rounded-[4px] px-1 text-[9px] font-semibold leading-4 text-white"
                      style={{ left: `${(s.start_day / horizon) * 100}%`, width: `${((s.end_day - s.start_day) / horizon) * 100}%`, background: orderColor(s.order!) }}
                    >
                      {s.end_day - s.start_day >= 3 ? s.order : ''}
                    </div>
                  ))}
              </div>
            </div>
          ))}
        </div>
        {dueMarks.length > 0 && (
          <div className="relative ml-14 mt-1 h-5 text-[9px] text-ink-3">
            {dueMarks.map((d) => (
              <span key={d.order} title={`${d.order} due ${label(d.day)}`} className="absolute -translate-x-1/2 whitespace-nowrap" style={{ left: `${(Math.min(d.day, horizon) / horizon) * 100}%`, color: orderColor(d.order) }}>
                ▲ {d.order.replace('SO-', '')}
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

/* ------------------------------------------------------------------ machine alert card */

const SENSOR_ICON: Record<string, React.ElementType> = { temperature: Thermometer, vibration: Wrench, pressure: AlertCircle, power: AlertTriangle, all: ShieldQuestion };
export const AlertCard: React.FC<{ a: SensorAlert; to?: string; compact?: boolean }> = ({ a, to, compact }) => {
  const Icon = SENSOR_ICON[a.sensor] ?? AlertTriangle;
  const body = (
    <div className={cn('rounded-xl border bg-surface p-3.5 transition-shadow hover:shadow-lift', a.level === 'CRITICAL' ? 'border-bad/40' : a.level === 'WARNING' ? 'border-warn/40' : 'border-line')}>
      <div className="flex items-start gap-3">
        <span className={cn('grid size-8 shrink-0 place-items-center rounded-lg', a.level === 'CRITICAL' ? 'bg-bad-soft text-bad' : a.level === 'WARNING' ? 'bg-warn-soft text-warn' : 'bg-accent-soft text-accent-ink')}>
          <Icon className="size-4" />
        </span>
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-sm font-semibold text-ink">{a.title}</span>
            <LevelChip level={a.level} />
            {a.days_to_alarm != null && <span className="text-2xs font-medium text-bad">alarm level in ~{Math.round(a.days_to_alarm)} d at this rate</span>}
          </div>
          <p className="mt-1 text-xs leading-5 text-ink-2">{a.facts[0]}</p>
          {!compact && a.hypothesis && (
            <p className="mt-1.5 flex gap-1.5 text-xs text-ink-3">
              <Lightbulb className="mt-0.5 size-3.5 shrink-0" />
              <span>
                <b className="font-medium text-ink-2">Worth checking (unverified):</b> {a.hypothesis}
              </span>
            </p>
          )}
        </div>
      </div>
    </div>
  );
  return to ? <Link to={to} className="block">{body}</Link> : body;
};

/* ------------------------------------------------------------------ finding card: evidence first */

export const FindingCard: React.FC<{ f: Finding; defaultOpen?: boolean; showMoney?: boolean; canAct?: boolean }> = ({ f, defaultOpen = false, showMoney = true, canAct = true }) => {
  const [open, setOpen] = useState(defaultOpen);
  const [form, setForm] = useState(false);
  const [text, setText] = useState(f.next_steps[0] ?? '');
  const create = useCreateAction();
  const impact = f.evidence.estimated_impact?.lost_lakhs;
  const verified = f.verified_cause;
  return (
    <div className={cn('overflow-hidden rounded-2xl border bg-surface shadow-card', f.severity === 'HIGH' ? 'border-bad/30' : 'border-line/80')}>
      <button onClick={() => setOpen((o) => !o)} className="flex w-full items-start gap-3 px-5 py-4 text-left">
        <span className={cn('mt-0.5 grid size-9 shrink-0 place-items-center rounded-xl', f.severity === 'HIGH' ? 'bg-bad-soft text-bad' : f.severity === 'MEDIUM' ? 'bg-warn-soft text-warn' : 'bg-muted text-ink-3')}>
          <FlaskConical className="size-4.5" />
        </span>
        <span className="min-w-0 flex-1">
          <span className="flex flex-wrap items-center gap-2">
            <SeverityChip s={f.severity} />
            <AiBadge label="AI finding" />
            {verified && <span className="inline-flex items-center gap-1 rounded-md bg-ok-soft px-1.5 py-0.5 text-2xs font-semibold text-ok"><CheckCircle2 className="size-3" /> Cause verified</span>}
          </span>
          <span className="mt-1.5 block text-[15px] font-semibold leading-snug text-ink">{f.title}</span>
          <span className="mt-1 block text-sm leading-5 text-ink-2">{f.facts[0]}</span>
          <span className="mt-2 flex flex-wrap items-center gap-x-4 gap-y-1">
            <ConfidencePill level={f.confidence.level} reasons={f.confidence.reasons} />
            {showMoney && impact != null && <span className="text-xs font-medium text-bad">≈ {inrFromLakhs(impact)} at stake</span>}
            {f.actions && f.actions.length > 0 && <span className="text-xs text-ink-3">{f.actions.length} action{f.actions.length > 1 ? 's' : ''} raised</span>}
          </span>
        </span>
        <ChevronDown className={cn('mt-1 size-4 shrink-0 text-ink-3 transition-transform', open && 'rotate-180')} />
      </button>
      {open && (
        <div className="space-y-5 border-t border-line/70 bg-subtle px-5 py-4 text-sm">
          <section>
            <h4 className="mb-1.5 text-xs font-semibold uppercase tracking-wide text-ink-3">What the data shows</h4>
            <ul className="space-y-1.5">
              {f.facts.map((x, i) => (
                <li key={i} className="flex gap-2 leading-5 text-ink-2"><span className="mt-2 size-1 shrink-0 rounded-full bg-accent" />{x}</li>
              ))}
            </ul>
            <div className="mt-2 text-xs text-ink-3">
              Period {f.evidence.period} · {f.evidence.n_observations} observations{f.evidence.scope && ` · ${Object.entries(f.evidence.scope).map(([k, v]) => `${k}: ${v}`).join(' · ')}`}
            </div>
          </section>
          {f.signals.length > 0 && (
            <section>
              <h4 className="mb-1.5 text-xs font-semibold uppercase tracking-wide text-ink-3">Statistical signal</h4>
              {f.signals.map((s, i) => (
                <div key={i} className="text-xs leading-5 text-ink-2">
                  <b className="font-medium text-ink">{s.name}</b>{s.statistic != null && ` · statistic ${s.statistic}`}{s.p_value != null && ` · p ≈ ${s.p_value < 0.0001 ? s.p_value.toExponential(1) : s.p_value.toFixed(4)}`}
                  <div className="text-ink-3">{s.method}. A signal says a difference is unlikely to be chance. It does not say why.</div>
                </div>
              ))}
            </section>
          )}
          {f.hypotheses.length > 0 && (
            <section>
              <h4 className="mb-1.5 flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wide text-ink-3"><ShieldQuestion className="size-3.5" /> Possible explanations, not verified</h4>
              <ul className="space-y-2">
                {f.hypotheses.map((h, i) => (
                  <li key={i} className="rounded-lg border border-dashed border-line-strong bg-surface px-3 py-2">
                    <div className="text-ink">{h.statement}</div>
                    <div className="mt-0.5 text-xs text-ink-3"><b className="font-medium text-ink-2">How to check:</b> {h.how_to_check}</div>
                  </li>
                ))}
              </ul>
            </section>
          )}
          {f.next_steps.length > 0 && (
            <section>
              <h4 className="mb-1.5 text-xs font-semibold uppercase tracking-wide text-ink-3">Suggested next steps</h4>
              <ol className="list-decimal space-y-1 pl-5 text-ink-2">{f.next_steps.map((x, i) => <li key={i}>{x}</li>)}</ol>
            </section>
          )}
          {f.confidence.missing_information.length > 0 && (
            <section className="flex gap-2 text-xs text-ink-3"><Info className="mt-0.5 size-3.5 shrink-0" /><span><b className="font-medium text-ink-2">Not known:</b> {f.confidence.missing_information.join(' ')}</span></section>
          )}
          {f.evidence.limitations.length > 0 && <section className="text-xs text-ink-3"><b className="font-medium text-ink-2">Limits of this analysis:</b> {f.evidence.limitations.join(' ')}</section>}
          {verified && <section className="rounded-lg bg-ok-soft px-3 py-2 text-ok"><b>Verified cause (recorded by a person):</b> {verified}</section>}
          {f.actions && f.actions.length > 0 && (
            <section>
              <h4 className="mb-1.5 text-xs font-semibold uppercase tracking-wide text-ink-3">Actions raised</h4>
              {f.actions.map((a) => (
                <div key={a.ref} className="flex items-center justify-between gap-3 border-b border-line/60 py-1.5 text-xs last:border-0">
                  <span className="text-ink-2">{a.action}</span>
                  <span className="shrink-0 text-ink-3">{a.owner} · {a.status.toLowerCase().replace('_', ' ')}</span>
                </div>
              ))}
            </section>
          )}
          <div className="flex flex-wrap items-center gap-2 pt-1">
            {canAct && !form && !create.isSuccess && (
              <Button size="sm" variant="primary" icon={<Plus className="size-3.5" />} onClick={() => setForm(true)}>Raise an action</Button>
            )}
            <Link to={f.link}><Button size="sm" icon={<ArrowRight className="size-3.5" />}>See the evidence in context</Button></Link>
          </div>
          {form && !create.isSuccess && (
            <div className="space-y-2 rounded-xl border border-line bg-surface p-3">
              <label className="block text-xs font-medium text-ink-2">What should happen
                <textarea value={text} onChange={(e) => setText(e.target.value)} rows={2} className="mt-1 w-full rounded-lg border border-line bg-surface p-2 text-sm outline-none focus:border-accent" />
              </label>
              <div className="flex items-center gap-2">
                <Button size="sm" variant="primary" loading={create.isPending} disabled={text.trim().length < 3}
                  onClick={() => create.mutate({ issue: f.title, action: text.trim(), finding_key: f.key, owner_role: f.audiences[0], expected_impact_lakhs: impact ?? 0 })}>Save action</Button>
                <Button size="sm" variant="ghost" onClick={() => setForm(false)}>Cancel</Button>
                {create.isError && <span className="text-xs text-bad">Could not save. Try again.</span>}
              </div>
            </div>
          )}
          {create.isSuccess && (
            <div className="rounded-lg bg-ok-soft px-3 py-2 text-xs text-ok">
              Action {create.data.ref} saved{create.data.requires_approval ? '. It will count once the weaving manager or owner approves it.' : '.'} <Link to="/weaving/actions" className="font-semibold underline">Open the tracker</Link>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export const orderPalette = (orders: string[]) => {
  const m = new Map<string, string>();
  [...orders].sort().forEach((o, i) => m.set(o, catColor(i)));
  return (o: string) => m.get(o) ?? '#8a99a8';
};
