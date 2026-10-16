import React from 'react';
import { Link } from 'react-router-dom';
import { useMaintenance } from '../../../api/weaving';
import { cn } from '../../../lib/format';
import { PageHeader } from '../../../layout/PageHeader';
import { Card, CardBody, CardHeader } from '../../../design/ui';
import { DataTable } from '../../../design/DataTable';
import { ColumnChart } from '../../../design/charts/Charts';
import { StatGrid } from '../../../design/viz/StatTile';
import { AlertCard, ConfidencePill, HealthRing, SeverityChip } from '../../../design/viz/parts';
import { Hero, Load, Pill, Section, shortDate, timeOf } from '../common';

const PM_COL = { OVERDUE: ['Overdue', 'border-bad/40 bg-bad-soft/40', 'text-bad'], TODAY: ['Due today', 'border-warn/40 bg-warn-soft/40', 'text-warn'], UPCOMING: ['Coming up', 'border-line bg-subtle', 'text-ink-3'] } as const;

export const MaintenancePage: React.FC = () => {
  const q = useMaintenance();
  return (
    <>
      <PageHeader title="Maintenance Desk" description="What to fix first, what is due, and which machines are quietly getting worse." />
      <Load q={q}>
        {(d) => (
          <>
            <Hero
              eyebrow="Work for the maintenance team"
              tone={d.priorities.some((p) => p.severity === 'HIGH') ? 'bad' : 'ok'}
              title={d.priorities.length ? `${d.priorities.length} looms need maintenance attention. Start with ${d.priorities[0].loom}.` : 'No loom needs urgent maintenance attention.'}
              aside={
                <div className="rounded-2xl bg-white/[0.09] p-4 backdrop-blur">
                  <div className="mb-2 text-xs font-medium uppercase tracking-wide text-white/70">Watch list: lowest health first</div>
                  <div className="space-y-1.5">
                    {d.watchlist.slice(0, 5).map((w) => (
                      <div key={w.loom} className="flex items-center justify-between text-sm"><span>{w.loom}</span><span className="num font-semibold">{w.health}</span></div>
                    ))}
                    {d.watchlist.length === 0 && <div className="text-sm text-white/80">All looms healthy.</div>}
                  </div>
                </div>
              }
            />
            <StatGrid items={d.kpis} />
            <Section title="Do these first" ai hint="ranked by urgency, repeated faults and estimated production lost">
              <div className="space-y-2.5">
                {d.priorities.length === 0 && <Card><p className="p-6 text-center text-sm text-ink-3">Nothing ranks above routine work.</p></Card>}
                {d.priorities.map((p, i) => (
                  <Card key={p.loom} className="p-4">
                    <div className="flex items-start gap-4">
                      <div className="grid size-8 shrink-0 place-items-center rounded-full bg-accent-soft text-sm font-bold text-accent-ink">{i + 1}</div>
                      <HealthRing score={p.health} size={50} />
                      <div className="min-w-0 flex-1">
                        <div className="flex flex-wrap items-center gap-2">
                          <Link to={`/weaving/machines?loom=${p.loom}`} className="text-base font-semibold text-ink hover:text-accent">{p.loom}</Link>
                          <SeverityChip s={p.severity} />
                          <ConfidencePill level={p.confidence as 'HIGH' | 'MEDIUM' | 'LOW'} />
                        </div>
                        <ul className="mt-1.5 space-y-0.5 text-sm text-ink-2">{p.facts.map((f, j) => <li key={j}>{f}</li>)}</ul>
                        <div className="mt-2 rounded-lg bg-subtle px-3 py-2 text-sm text-ink-2"><b className="font-medium text-ink">Do:</b> {p.steps.join(' ')}</div>
                      </div>
                    </div>
                  </Card>
                ))}
              </div>
            </Section>
            <div className="grid gap-4 xl:grid-cols-3">
              {(['OVERDUE', 'TODAY', 'UPCOMING'] as const).map((st) => {
                const rows = d.pm_board.filter((x) => x.state === st);
                const [label, box, txt] = PM_COL[st];
                return (
                  <div key={st} className={cn('rounded-2xl border p-3', box)}>
                    <div className="mb-2 flex items-center justify-between px-1"><span className={cn('text-sm font-semibold', txt)}>{label}</span><span className="num text-sm text-ink-3">{rows.length}</span></div>
                    <div className="max-h-72 space-y-1.5 overflow-auto">
                      {rows.length === 0 && <div className="px-2 py-4 text-center text-xs text-ink-3">Nothing here</div>}
                      {rows.map((r, i) => (
                        <Link key={i} to={`/weaving/machines?loom=${r.loom}`} className="flex items-center justify-between gap-2 rounded-lg bg-surface px-3 py-2 text-sm shadow-card hover:shadow-lift">
                          <span><b className="font-semibold text-ink">{r.loom}</b> <span className="text-ink-3">{r.task}</span></span>
                          <span className={cn('num text-xs', st === 'OVERDUE' ? 'font-semibold text-bad' : 'text-ink-3')}>{st === 'OVERDUE' ? `${r.days} d late` : shortDate(r.due)}</span>
                        </Link>
                      ))}
                    </div>
                  </div>
                );
              })}
            </div>
            <div className="grid gap-4 xl:grid-cols-2">
              <Card>
                <CardHeader title="Breakdowns per day" subtitle="Mechanical and electrical stops of 30 minutes or more" />
                <CardBody><ColumnChart data={d.breakdown_trend} xKey="label" series={[{ key: 'breakdowns', label: 'Breakdowns', color: 1 }]} format={(v) => String(Math.round(v))} /></CardBody>
              </Card>
              <Card>
                <CardHeader title="Recent breakdowns" />
                <DataTable dense rows={d.breakdowns} rowKey={(r) => r.loom + r.started_at} columns={[
                  { key: 'l', header: 'Loom', value: (r) => r.loom, render: (r) => <Link to={`/weaving/machines?loom=${r.loom}`} className="font-semibold hover:text-accent">{r.loom}</Link> },
                  { key: 't', header: 'Fault', value: (r) => r.task, render: (r) => r.task },
                  { key: 'a', header: 'When', value: (r) => r.started_at, render: (r) => `${shortDate(r.started_at)} ${timeOf(r.started_at)}`, hideBelow: 'md' },
                  { key: 'm', header: 'Repair', value: (r) => r.minutes, render: (r) => (r.minutes == null ? <Pill tone="warn">in progress</Pill> : `${r.minutes} min`), align: 'right' },
                ]} />
              </Card>
            </div>
            <Section title="Machine watch" ai hint="sensor drift from each machine's own normal">
              <div className="grid gap-2.5 xl:grid-cols-2">{d.alerts.slice(0, 8).map((a, i) => <AlertCard key={i} a={a} to={`/weaving/machines?loom=${a.loom}`} />)}</div>
            </Section>
            <p className="text-xs text-ink-3">{d.notes.join(' ')}</p>
          </>
        )}
      </Load>
    </>
  );
};
