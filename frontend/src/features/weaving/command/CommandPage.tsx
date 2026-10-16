import React from 'react';
import { Link } from 'react-router-dom';
import { ArrowRight, CheckCircle2 } from 'lucide-react';
import { useCommand } from '../../../api/weaving';
import { usePeriod } from '../../../app/state';
import { cn, inrFromLakhs, num, pct } from '../../../lib/format';
import { PageHeader } from '../../../layout/PageHeader';
import { Card, CardBody, CardHeader, StatusPill } from '../../../design/ui';
import { DataTable } from '../../../design/DataTable';
import { TrendChart } from '../../../design/charts/Charts';
import { StatGrid } from '../../../design/viz/StatTile';
import { AlertCard, FindingCard, PriorityDot, RiskChip } from '../../../design/viz/parts';
import { ForecastChart, PlanVsActual } from '../../../design/viz/charts2';
import { BriefList, Hero, Load, LiveCounts, Section, Pill, shortDate } from '../common';

export const CommandPage: React.FC = () => {
  const [period] = usePeriod();
  const q = useCommand(period);
  return (
    <>
      <PageHeader title="Command Centre" description="The weaving department at a glance: what is happening, what is going wrong, and what to do first." showPeriod />
      <Load q={q}>
        {(d) => {
          const hot = d.live.stopped_now.filter((s) => !s.planned);
          return (
            <>
              <Hero
                eyebrow="Morning brief"
                tone={d.brief.some((b) => b.severity === 'HIGH') ? 'bad' : 'ok'}
                title={d.headline}
                aside={<LiveCounts running={d.live.running} stopped={d.live.stopped} idle={d.live.idle} total={d.live.total} health={d.health_summary} />}
              >
                <BriefList lines={d.brief} max={6} />
              </Hero>

              <StatGrid items={d.kpis} />

              <div className="grid gap-4 xl:grid-cols-3">
                <Card className="xl:col-span-2">
                  <CardHeader title="Today against plan" subtitle={`Cumulative metres woven through the production day. ${num(d.day_progress.actual_m)} m of ${num(d.day_progress.plan_m)} m planned so far (${pct(d.day_progress.achievement_pct)}).`} />
                  <CardBody>{d.day_progress.hours.length ? <PlanVsActual rows={d.day_progress.hours} /> : <p className="py-8 text-center text-sm text-ink-3">No readings yet today.</p>}</CardBody>
                </Card>
                <Card>
                  <CardHeader title={`Stopped right now · ${hot.length}`} subtitle="Longest first. The live floor, not the selected period." />
                  <div className="divide-y divide-line/70 px-5 pb-3">
                    {hot.length === 0 && <p className="py-6 text-center text-sm text-ink-3">Every running loom is weaving.</p>}
                    {hot.slice(0, 6).map((s) => (
                      <div key={s.loom} className="py-2.5">
                        <div className="flex items-center justify-between">
                          <Link to={`/weaving/machines?loom=${s.loom}`} className="text-sm font-semibold text-ink hover:text-accent">{s.loom}</Link>
                          <span className={cn('num text-sm font-semibold', s.minutes > 20 ? 'text-bad' : 'text-warn')}>{s.minutes} min</span>
                        </div>
                        <div className="text-xs text-ink-3">{s.reason}{s.fitter ? ` · fitter ${s.fitter}` : ''}</div>
                        {s.watch && <div className="mt-0.5 text-xs text-warn">Machine watch: {s.watch}</div>}
                      </div>
                    ))}
                  </div>
                </Card>
              </div>

              <div className="grid gap-4 xl:grid-cols-2">
                <Card>
                  <CardHeader title="Efficiency, last 14 days" subtitle="Picks inserted as a share of what the looms could insert" />
                  <CardBody><TrendChart data={d.trend} xKey="label" series={[{ key: 'efficiency_pct', label: 'Efficiency', color: 0 }]} format={(v) => `${v.toFixed(1)}%`} area yDomain={[75, 100]} /></CardBody>
                </Card>
                <Card>
                  <CardHeader title="Output, target and the next three days" subtitle="Forecast checked against how it would have done on the last five days" />
                  <CardBody><ForecastChart history={d.trend} forecast={d.forecast} /></CardBody>
                </Card>
              </div>

              <div className="grid gap-4 xl:grid-cols-2">
                <Section title="Machine watch" ai hint="vibration, temperature, air pressure, power">
                  <div className="space-y-2.5">
                    {d.alerts.length === 0 && <Card><p className="p-6 text-center text-sm text-ink-3">No machine is drifting from its own normal.</p></Card>}
                    {d.alerts.slice(0, 3).map((a, i) => <AlertCard key={i} a={a} to={`/weaving/machines?loom=${a.loom}`} compact />)}
                    {d.alerts.length > 3 && <Link to="/weaving/machines" className="inline-flex items-center gap-1 text-sm font-medium text-accent">All {d.alerts.length} alerts <ArrowRight className="size-4" /></Link>}
                  </div>
                </Section>
                <Section title="What the AI found" ai hint="facts first, hypotheses marked unverified">
                  <div className="space-y-2.5">
                    {d.findings.map((f) => <FindingCard key={f.key} f={f} />)}
                    <Link to="/weaving/insights" className="inline-flex items-center gap-1 text-sm font-medium text-accent">All findings <ArrowRight className="size-4" /></Link>
                  </div>
                </Section>
              </div>

              <div className="grid gap-4 xl:grid-cols-3">
                <Card className="xl:col-span-2">
                  <CardHeader title="Orders that need attention" subtitle="Projected from each order's own pace" actions={<Link to="/weaving/scheduler" className="text-xs font-medium text-accent">Open AI Scheduler</Link>} />
                  <DataTable
                    dense
                    rows={d.orders}
                    rowKey={(r) => r.order_no}
                    emptyTitle="Every open order is on track"
                    columns={[
                      { key: 'o', header: 'Order', value: (r) => r.order_no, render: (r) => <span className="inline-flex items-center gap-1.5 font-medium"><PriorityDot p={r.priority} />{r.order_no}</span> },
                      { key: 'c', header: 'Customer', value: (r) => r.customer ?? '', render: (r) => <span className="text-ink-2">{r.customer}</span>, hideBelow: 'md' },
                      { key: 'p', header: 'Progress', value: (r) => r.progress_pct, render: (r) => `${r.progress_pct}%`, align: 'right' },
                      { key: 'd', header: 'Due', value: (r) => r.due_date ?? '', render: (r) => shortDate(r.due_date), align: 'right' },
                      { key: 'e', header: 'Expected', value: (r) => r.eta ?? '', render: (r) => shortDate(r.eta), align: 'right' },
                      { key: 'r', header: 'Status', value: (r) => r.risk, render: (r) => <RiskChip risk={r.risk} /> },
                    ]}
                  />
                </Card>
                <Card>
                  <CardHeader title="Crew today" subtitle="Present against what the loom count needs" actions={<Link to="/weaving/workforce" className="text-xs font-medium text-accent">Workforce</Link>} />
                  <div className="space-y-2 px-5 pb-4">
                    {d.staffing.map((c, i) => (
                      <div key={i} className="flex items-center justify-between text-sm">
                        <span className="text-ink-2">{c.shift} · {c.role}</span>
                        <span className="inline-flex items-center gap-2"><span className="num text-ink">{c.present}/{c.required}</span><StatusPill status={c.status} /></span>
                      </div>
                    ))}
                    {d.staffing.length === 0 && <p className="text-sm text-ink-3">No shift has started yet.</p>}
                  </div>
                </Card>
              </div>

              <Card>
                <CardHeader title="Shift comparison" subtitle="Same floor, different crews" />
                <DataTable
                  dense
                  rows={d.shifts}
                  rowKey={(r) => r.shift}
                  columns={[
                    { key: 's', header: 'Shift', value: (r) => r.shift, render: (r) => <span className="font-medium">{r.shift}</span> },
                    { key: 'm', header: 'Output', value: (r) => r.meters, render: (r) => `${num(r.meters)} m`, align: 'right' },
                    { key: 'e', header: 'Efficiency', value: (r) => r.efficiency_pct, render: (r) => pct(r.efficiency_pct), align: 'right' },
                    { key: 'u', header: 'Utilization', value: (r) => r.utilization_pct, render: (r) => pct(r.utilization_pct), align: 'right' },
                    { key: 'st', header: 'Stops / 100k', value: (r) => r.stops_per_100k, render: (r) => r.stops_per_100k?.toFixed(2) ?? '—', align: 'right' },
                    { key: 'df', header: 'Defects / 100 m', value: (r) => r.defects_per_100m, render: (r) => r.defects_per_100m?.toFixed(2) ?? '—', align: 'right' },
                  ]}
                />
              </Card>
            </>
          );
        }}
      </Load>
    </>
  );
};
