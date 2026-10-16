import React from 'react';
import { Link } from 'react-router-dom';
import { ArrowRight, Sparkles } from 'lucide-react';
import type { UseQueryResult } from '@tanstack/react-query';
import { cn } from '../../lib/format';
import { QueryView } from '../../design/QueryView';
import { Card } from '../../design/ui';
import { AiBadge } from '../../design/viz/parts';

/** Loading, error and data handling for a page-level query. */
export function Load<T>({ q, children }: { q: UseQueryResult<T>; children: (d: T) => React.ReactNode }) {
  return <QueryView query={q}>{(d) => <div className="space-y-4">{children(d)}</div>}</QueryView>;
}

/** The big banner at the top of a role's landing page: one sentence that says how things are, then what to do about it. */
export const Hero: React.FC<{ eyebrow: string; title: React.ReactNode; aside?: React.ReactNode; children?: React.ReactNode; tone?: 'neutral' | 'warn' | 'bad' | 'ok' }> = ({ eyebrow, title, aside, children, tone = 'neutral' }) => (
  <Card className={cn('relative overflow-hidden border-0 bg-gradient-to-br from-[#0b2f4a] via-[#0d4366] to-[#0a6d8f] p-6 text-white shadow-lift')}>
    <div aria-hidden className="pointer-events-none absolute -right-16 -top-16 size-64 rounded-full bg-white/[0.06]" />
    <div aria-hidden className="pointer-events-none absolute -bottom-24 right-24 size-72 rounded-full bg-white/[0.05]" />
    <div className="relative grid gap-6 lg:grid-cols-[1.6fr_1fr]">
      <div className="min-w-0">
        <div className="mb-2 flex items-center gap-2 text-2xs font-semibold uppercase tracking-[0.16em] text-white/70">
          <Sparkles className="size-3.5" /> {eyebrow}
          <span className={cn('ml-1 size-2 rounded-full', tone === 'bad' ? 'bg-bad' : tone === 'warn' ? 'bg-warn' : tone === 'ok' ? 'bg-[#35d0a8]' : 'bg-white/50')} />
        </div>
        <h2 className="text-[22px] font-semibold leading-snug tracking-tight">{title}</h2>
        {children && <div className="mt-4">{children}</div>}
      </div>
      {aside && <div className="min-w-0">{aside}</div>}
    </div>
  </Card>
);

export const BriefList: React.FC<{ lines: { severity: string; text: string; link: string; kind: string }[]; max?: number }> = ({ lines, max = 6 }) => (
  <ul className="space-y-2">
    {lines.slice(0, max).map((l, i) => (
      <li key={i}>
        <Link to={l.link} className="group flex items-start gap-2.5 rounded-xl bg-white/[0.08] px-3 py-2 text-sm leading-5 text-white/95 transition-colors hover:bg-white/[0.15]">
          <span className={cn('mt-1.5 size-2 shrink-0 rounded-full', l.severity === 'HIGH' ? 'bg-[#ff6b6b]' : l.severity === 'MEDIUM' ? 'bg-[#ffc75f]' : 'bg-[#7ee2c4]')} />
          <span className="min-w-0 flex-1">{l.text}</span>
          <ArrowRight className="mt-0.5 size-4 shrink-0 opacity-0 transition-opacity group-hover:opacity-100" />
        </Link>
      </li>
    ))}
  </ul>
);

export const LiveCounts: React.FC<{ running: number; stopped: number; idle: number; total: number; health?: { at_risk: number; watch: number; healthy: number } }> = ({ running, stopped, idle, total, health }) => (
  <div className="space-y-3">
  <div className="rounded-2xl bg-white/[0.09] p-4 backdrop-blur">
    <div className="mb-3 flex items-center justify-between text-xs text-white/70">
      <span className="font-medium uppercase tracking-wide">Floor right now</span>
      <span className="inline-flex items-center gap-1.5"><span className="size-1.5 animate-pulse rounded-full bg-[#35d0a8]" /> live</span>
    </div>
    <div className="grid grid-cols-3 gap-3 text-center">
      {[['Running', running, '#35d0a8'], ['Stopped', stopped, '#ff6b6b'], ['No order', idle, '#9fb3c4']].map(([l, n, c]) => (
        <div key={String(l)}>
          <div className="num text-3xl font-semibold" style={{ color: String(c) }}>{n}</div>
          <div className="text-[11px] text-white/70">{l}</div>
        </div>
      ))}
    </div>
    <div className="mt-3 flex h-2 overflow-hidden rounded-full bg-white/10">
      <span style={{ width: `${(running / total) * 100}%`, background: '#35d0a8' }} />
      <span style={{ width: `${(stopped / total) * 100}%`, background: '#ff6b6b' }} />
      <span style={{ width: `${(idle / total) * 100}%`, background: '#9fb3c4' }} />
    </div>
    <div className="mt-1.5 text-center text-[11px] text-white/60">{total} looms</div>
  </div>
  {health && (
    <div className="rounded-2xl bg-white/[0.09] p-4 backdrop-blur">
      <div className="mb-2 text-xs font-medium uppercase tracking-wide text-white/70">Machine health</div>
      <div className="grid grid-cols-3 gap-3 text-center">
        {[['Healthy', health.healthy, '#35d0a8'], ['Watch', health.watch, '#ffc75f'], ['At risk', health.at_risk, '#ff6b6b']].map(([l, n, c]) => (
          <div key={String(l)}><div className="num text-2xl font-semibold" style={{ color: String(c) }}>{n}</div><div className="text-[11px] text-white/70">{l}</div></div>
        ))}
      </div>
    </div>
  )}
  </div>
);

export const Section: React.FC<{ title: string; hint?: string; ai?: boolean; children: React.ReactNode; className?: string }> = ({ title, hint, ai, children, className }) => (
  <section className={cn('space-y-3', className)}>
    <div className="flex items-baseline gap-2">
      <h2 className="text-base font-semibold tracking-tight text-ink">{title}</h2>
      {ai && <AiBadge />}
      {hint && <span className="text-xs text-ink-3">{hint}</span>}
    </div>
    {children}
  </section>
);

export const shortDate = (iso: string | null | undefined) => (iso ? new Date(iso).toLocaleDateString('en-GB', { day: '2-digit', month: 'short' }) : '—');
export const timeOf = (iso: string) => new Date(iso).toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' });
export const m = (v: number | null | undefined) => (v == null ? '—' : `${Math.round(v).toLocaleString('en-IN')} m`);
export const dash = (v: number | null | undefined, d = 1, suffix = '') => (v == null ? '—' : `${v.toFixed(d)}${suffix}`);

export const Pill: React.FC<{ tone?: 'ok' | 'warn' | 'bad' | 'info' | 'neutral'; children: React.ReactNode; className?: string }> = ({ tone = 'neutral', children, className }) => (
  <span className={cn('inline-flex items-center rounded-md px-2 py-0.5 text-2xs font-semibold', { ok: 'bg-ok-soft text-ok', warn: 'bg-warn-soft text-warn', bad: 'bg-bad-soft text-bad', info: 'bg-accent-soft text-accent-ink', neutral: 'bg-muted text-ink-2' }[tone], className)}>{children}</span>
);
