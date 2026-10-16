import React, { useState } from 'react';
import { useInsights } from '../../../api/weaving';
import { useAuth } from '../../../auth/AuthContext';
import { usePeriod } from '../../../app/state';
import { PageHeader } from '../../../layout/PageHeader';
import { Card, Segmented } from '../../../design/ui';
import { AiBadge, AlertCard, FindingCard } from '../../../design/viz/parts';
import { Hero, Load, Section } from '../common';

const KIND: Record<string, string> = {
  loom_decline: 'Loom decline',
  recurring_stop: 'Repeated stops',
  beam_warp_excess: 'Beams and yarn',
  shift_defect_shift: 'Shift defects',
  maintenance_priority: 'Maintenance',
};

export const InsightsPage: React.FC = () => {
  const [period] = usePeriod('LAST_7_DAYS');
  const { user } = useAuth();
  const q = useInsights(period);
  const [kind, setKind] = useState('ALL');
  return (
    <>
      <PageHeader title="AI Insights" description="What the data says is going wrong, with the evidence. Explanations stay marked unverified until a person confirms them." showPeriod defaultPeriod="LAST_7_DAYS" />
      <Load q={q}>
        {(d) => {
          const list = d.findings.filter((f) => kind === 'ALL' || f.kind === kind);
          const kinds = Object.keys(d.summary.by_kind);
          return (
            <>
              <Hero
                eyebrow={`Findings for ${user?.role_label ?? 'you'}`}
                tone={d.summary.high ? 'bad' : 'ok'}
                title={d.summary.total === 0 ? 'Nothing stands out right now.' : `${d.summary.total} finding${d.summary.total > 1 ? 's' : ''}, ${d.summary.high} urgent. Each one shows what the data says before it says what might be behind it.`}
                aside={
                  <div className="rounded-2xl bg-white/[0.09] p-4 text-sm leading-6 text-white/85 backdrop-blur">
                    <div className="mb-1 flex items-center gap-2 text-xs font-medium uppercase tracking-wide text-white/70"><AiBadge /> How to read these</div>
                    {d.method.map((m, i) => <p key={i} className="mb-1 last:mb-0">{m}</p>)}
                  </div>
                }
              />
              {kinds.length > 1 && <Segmented value={kind} onChange={setKind} ariaLabel="Kind" options={[{ value: 'ALL', label: `All ${d.summary.total}` }, ...kinds.map((k) => ({ value: k, label: `${KIND[k] ?? k} ${d.summary.by_kind[k]}` }))]} />}
              <div className="space-y-3">
                {list.map((f, i) => <FindingCard key={f.key} f={f} defaultOpen={i === 0 && kind === 'ALL'} showMoney={d.money_visible} />)}
                {list.length === 0 && <Card><p className="p-8 text-center text-sm text-ink-3">No findings of this kind.</p></Card>}
              </div>
              {d.alerts.length > 0 && (
                <Section title="Machine watch" ai hint="sensor drift from each machine's own normal">
                  <div className="grid gap-2.5 xl:grid-cols-2">{d.alerts.map((a, i) => <AlertCard key={i} a={a} to={`/weaving/machines?loom=${a.loom}`} />)}</div>
                </Section>
              )}
            </>
          );
        }}
      </Load>
    </>
  );
};
