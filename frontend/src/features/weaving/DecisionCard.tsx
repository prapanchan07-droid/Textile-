import React from 'react';
import { Link } from 'react-router-dom';
import { ArrowRight } from 'lucide-react';
import { inrFromLakhs } from '../../lib/format';
import { Card, StatusPill } from '../../design/ui';
import type { WeavingDecision } from '../../types/weaving';
import { SEV_LABEL, sevTone } from './shared';

/** One decision: what is wrong, why we think so, what to do, who owns it, what it costs. */
export const DecisionCard: React.FC<{ d: WeavingDecision; search: string }> = ({ d, search }) => {
  const [path, query] = d.link.split('?');
  const params = new URLSearchParams(search);
  new URLSearchParams(query ?? '').forEach((v, k) => params.set(k, v));
  return (
    <Card className="flex flex-col gap-3 p-4">
      <div className="flex items-start justify-between gap-3">
        <h3 className="text-sm font-semibold text-ink">{d.title}</h3>
        <StatusPill tone={sevTone(d.severity)} label={SEV_LABEL[d.severity]} />
      </div>
      <dl className="space-y-2 text-xs">
        <div>
          <dt className="font-medium text-ink-3">Why</dt>
          <dd className="text-ink-2">{d.why}</dd>
        </div>
        <div>
          <dt className="font-medium text-ink-3">What to do</dt>
          <dd className="text-ink">{d.action}</dd>
        </div>
      </dl>
      <div className="mt-auto flex items-center justify-between gap-2 border-t border-line pt-3 text-xs">
        <span className="text-ink-3">
          Owner: <span className="font-medium text-ink-2">{d.owner}</span>
        </span>
        <span className="num font-medium text-bad">{inrFromLakhs(d.impact_lakhs)} at stake</span>
      </div>
      <Link to={{ pathname: path, search: params.toString() }} className="inline-flex items-center gap-1 text-xs font-medium text-accent-ink hover:underline">
        See the evidence <ArrowRight className="size-3.5" />
      </Link>
    </Card>
  );
};
