import React from 'react';
import { Link } from 'react-router-dom';
import { ClipboardPlus } from 'lucide-react';
import { Button } from '../../design/ui';
import type { Finding } from '../../types/mill';
import { BasisBadge, SeverityPill, fmt } from './parts';

const label = (k: string) => k.replace(/_/g, ' ').replace(/pct/g, '%').replace(/cmpx/g, '/100k picks');

const show = (v: unknown): string => {
  if (v == null) return '—';
  if (typeof v === 'number') return fmt.n(v, 2);
  if (typeof v === 'object') return Object.entries(v as Record<string, unknown>).map(([k, x]) => `${label(k)} ${show(x)}`).join(', ');
  return String(v);
};

/** One finding with its evidence, basis and next step. */
export const FindingCard: React.FC<{ f: Finding; onTask?: (f: Finding) => void }> = ({ f, onTask }) => (
  <li className="rounded-xl border border-line p-3.5">
    <div className="flex flex-wrap items-center gap-2">
      <SeverityPill severity={f.severity} />
      <BasisBadge basis={f.basis} />
      {f.loom_id ? (
        <Link to={`/looms/${f.loom_id}`} className="text-sm font-semibold text-ink hover:text-accent">{f.title}</Link>
      ) : (
        <span className="text-sm font-semibold text-ink">{f.title}</span>
      )}
    </div>
    <dl className="mt-2 grid gap-x-4 gap-y-0.5 text-xs text-ink-2 sm:grid-cols-2">
      {Object.entries(f.evidence).map(([k, v]) => (
        <div key={k} className="flex gap-1.5">
          <dt className="text-ink-3">{label(k)}:</dt>
          <dd className="num">{show(v)}</dd>
        </div>
      ))}
    </dl>
    {f.impact?.meters_gap != null && (
      <p className="mt-2 text-xs text-ink-2">
        <span className="font-medium text-warn">Estimated gap {fmt.n(f.impact.meters_gap)} m</span> in the period. {f.impact.assumption}
      </p>
    )}
    <p className="mt-2 text-xs text-ink-3">{f.implication}</p>
    <div className="mt-2 flex items-start justify-between gap-3">
      <p className="text-xs text-ink"><span className="font-medium">Next:</span> {f.next_step}</p>
      {onTask && (
        <Button size="sm" icon={<ClipboardPlus className="size-3.5" />} onClick={() => onTask(f)}>Task</Button>
      )}
    </div>
  </li>
);
