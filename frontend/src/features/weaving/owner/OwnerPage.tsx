import React from 'react';
import { Link } from 'react-router-dom';
import { ArrowRight, TrendingUp } from 'lucide-react';
import { useOwner } from '../../../api/weaving';
import { usePeriod } from '../../../app/state';
import { cn, inrFromLakhs, num, pct } from '../../../lib/format';
import { PageHeader } from '../../../layout/PageHeader';
import { Card, CardBody, CardHeader } from '../../../design/ui';
import { DataTable } from '../../../design/DataTable';
import { StatGrid } from '../../../design/viz/StatTile';
import { AiBadge, ConfidencePill, PriorityDot, RiskChip, SeverityChip } from '../../../design/viz/parts';
import { RankedBars, TrendChart } from '../../../design/charts/Charts';
import { Hero, Load, Pill, Section, shortDate } from '../common';

const REC: Record<string, { label: string; tone: 'ok' | 'warn' | 'bad' | 'neutral' }> = { PUSH: { label: 'Take more orders', tone: 'ok' }, HOLD: { label: 'Keep as is', tone: 'neutral' }, REPRICE: { label: 'Reprice', tone: 'warn' }, STOP: { label: 'Stop new orders', tone: 'bad' } };

export const OwnerPage: React.FC = () => {
  const [period] = usePeriod('LAST_7_DAYS');
  const q = useOwner(period);
  return (
    <>
      <PageHeader title="Owner Brief" description="Money, delivery promises and the decisions waiting for you." showPeriod defaultPeriod="LAST_7_DAYS" />
      <Load q={q}>
        {(d) => {
          const s = d.orders_summary;
          return (
            <>
              <Hero
                eyebrow="This is how the weaving department is doing"
                tone={s.LATE ? 'bad' : s.AT_RISK ? 'warn' : 'ok'}
                title={d.headline}
                aside={
                  d.capacity && (
                    <div className="rounded-2xl bg-white/[0.09] p-4 backdrop-blur">
                      <div className="mb-1 flex items-center gap-1.5 text-xs font-medium uppercase tracking-wide text-white/70"><TrendingUp className="size-3.5" /> Room to sell</div>
                      <div className="num text-3xl font-semibold">{num(d.capacity.free_loom_days)} <span className="text-base font-medium text-white/70">loom-days free</span></div>
                      <p className="mt-1 text-xs leading-5 text-white/75">
                        Only {d.capacity.capacity_booked_pct}% of loom time in the next {d.capacity.horizon_days} days is booked. {d.capacity.late_now} order(s) are projected late as booked, {d.capacity.late_with_plan} with the AI plan ({d.capacity.moves} loom moves).
                      </p>
                      <Link to="/weaving/scheduler" className="mt-3 inline-flex items-center gap-1 text-sm font-semibold text-white">Review the plan <ArrowRight className="size-4" /></Link>
                    </div>
                  )
                }
              />
              <StatGrid items={d.kpis} />

              <Section title="Decisions waiting for you" ai hint="ranked by what is at stake, each with its evidence one click away">
                <div className="grid gap-3 lg:grid-cols-2 xl:grid-cols-3">
                  {d.decisions.map((x, i) => (
                    <Link key={i} to={x.link} className="group flex flex-col rounded-2xl border border-line/80 bg-surface p-4 shadow-card transition-all hover:-translate-y-0.5 hover:shadow-lift">
                      <div className="mb-2 flex items-center justify-between">
                        <SeverityChip s={x.severity} />
                        {x.impact_lakhs != null && <span className="num text-sm font-semibold text-bad">{inrFromLakhs(x.impact_lakhs)}</span>}
                      </div>
                      <div className="text-[15px] font-semibold leading-snug text-ink">{x.title}</div>
                      <p className="mt-1.5 line-clamp-3 text-sm leading-5 text-ink-2">{x.why}</p>
                      <div className="mt-2 rounded-lg bg-subtle px-2.5 py-2 text-xs leading-5 text-ink-2"><b className="font-medium text-ink">Suggested:</b> {x.action}</div>
                      <div className="mt-3 flex items-center justify-between text-xs text-ink-3">
                        <span>{x.needs_approval ? 'Needs your approval' : 'For information'} · {x.confidence.toLowerCase()} confidence</span>
                        <ArrowRight className="size-4 transition-transform group-hover:translate-x-0.5" />
                      </div>
                    </Link>
                  ))}
                </div>
              </Section>

              <div className="grid gap-4 xl:grid-cols-5">
                <Card className="xl:col-span-3">
                  <CardHeader title="Where the contribution was lost" subtitle="₹ lakh not earned because looms stopped or ran below target speed. An estimate: lost metres × the style's contribution per metre." />
                  <CardBody>
                    {d.waterfall.length ? (
                      <RankedBars
                        items={(() => {
                          const losses = d.waterfall.filter((x) => x.kind === 'loss' && x.value < 0).map((x) => ({ label: x.label, value: -x.value }));
                          const total = losses.reduce((a, b) => a + b.value, 0) || 1;
                          return losses.sort((a, b) => b.value - a.value).map((l) => ({ ...l, share: (l.value / total) * 100 }));
                        })()}
                        format={(v) => `₹${v.toFixed(2)} L`}
                      />
                    ) : (
                      <p className="py-8 text-center text-sm text-ink-3">No data for this period.</p>
                    )}
                    {d.waterfall.length > 0 && <p className="mt-3 text-xs text-ink-3">At target the looms would have contributed ₹{d.waterfall[0].value.toFixed(1)} L this period; they achieved ₹{d.waterfall[d.waterfall.length - 1].value.toFixed(1)} L.</p>}
                  </CardBody>
                </Card>
                <Card className="xl:col-span-2">
                  <CardHeader title="Delivery promises" subtitle={`${s.open} open orders, ${num(s.remaining_m)} m still to weave`} actions={<Link to="/weaving/orders" className="text-xs font-medium text-accent">All orders</Link>} />
                  <CardBody className="space-y-4">
                    <div className="flex h-3 overflow-hidden rounded-full bg-muted">
                      {[['LATE', 'bg-bad', s.LATE], ['AT_RISK', 'bg-warn', s.AT_RISK], ['ON_TRACK', 'bg-ok', s.ON_TRACK], ['UNSCHEDULED', 'bg-line-strong', s.UNSCHEDULED]].map(([k, c, n]) => (
                        <span key={String(k)} className={String(c)} style={{ width: `${(Number(n) / Math.max(s.open, 1)) * 100}%` }} />
                      ))}
                    </div>
                    <div className="grid grid-cols-2 gap-2 text-sm">
                      <div className="flex items-center justify-between rounded-lg bg-bad-soft px-3 py-2 text-bad"><span>Late</span><b className="num">{s.LATE}</b></div>
                      <div className="flex items-center justify-between rounded-lg bg-warn-soft px-3 py-2 text-warn"><span>At risk</span><b className="num">{s.AT_RISK}</b></div>
                      <div className="flex items-center justify-between rounded-lg bg-ok-soft px-3 py-2 text-ok"><span>On track</span><b className="num">{s.ON_TRACK}</b></div>
                      <div className="flex items-center justify-between rounded-lg bg-muted px-3 py-2 text-ink-2"><span>Not on a loom</span><b className="num">{s.UNSCHEDULED}</b></div>
                    </div>
                    {d.money_visible && s.value_at_risk_lakhs != null && <p className="text-sm text-ink-2">About <b className="text-bad">{inrFromLakhs(s.value_at_risk_lakhs)}</b> of fabric value sits on orders that are late or at risk.</p>}
                    <p className="text-xs text-ink-3">Completed so far: {s.completed_on_time} of {s.completed} on time.</p>
                  </CardBody>
                </Card>
              </div>

              <div className="grid gap-4 xl:grid-cols-2">
                <Card>
                  <CardHeader title="Customers with something at stake" subtitle="Ordered by how many of their orders are late or at risk" />
                  <DataTable
                    dense
                    rows={d.customers}
                    rowKey={(r) => r.customer}
                    columns={[
                      { key: 'c', header: 'Customer', value: (r) => r.customer, render: (r) => <span className="font-medium">{r.customer} {r.tier === 'A' && <Pill tone="info">Tier A</Pill>}</span> },
                      { key: 'o', header: 'Open', value: (r) => r.open_orders, render: (r) => r.open_orders, align: 'right' },
                      { key: 'l', header: 'Late', value: (r) => r.late, render: (r) => (r.late ? <b className="text-bad">{r.late}</b> : '0'), align: 'right' },
                      { key: 'a', header: 'At risk', value: (r) => r.at_risk, render: (r) => (r.at_risk ? <b className="text-warn">{r.at_risk}</b> : '0'), align: 'right' },
                      { key: 'v', header: 'At stake', value: (r) => r.revenue_at_stake_lakhs, render: (r) => inrFromLakhs(r.revenue_at_stake_lakhs), align: 'right' },
                    ]}
                  />
                </Card>
                <Card>
                  <CardHeader title="Which styles earn their place" subtitle="Margin at the efficiency the looms actually achieved" />
                  <DataTable
                    dense
                    rows={d.styles}
                    rowKey={(r) => r.style}
                    columns={[
                      { key: 's', header: 'Style', value: (r) => r.style, render: (r) => <div><div className="font-medium">{r.style}</div><div className="text-xs text-ink-3">{r.fabric}</div></div> },
                      { key: 'e', header: 'Efficiency', value: (r) => r.efficiency_pct, render: (r) => `${pct(r.efficiency_pct)} / ${r.target_efficiency_pct}%`, align: 'right', hideBelow: 'md' },
                      { key: 'mg', header: 'Margin', value: (r) => r.margin_pct, render: (r) => <b className={cn((r.margin_pct ?? 0) < 10 ? 'text-bad' : 'text-ink')}>{pct(r.margin_pct)}</b>, align: 'right' },
                      { key: 'p', header: 'Profit', value: (r) => r.profit_lakhs, render: (r) => inrFromLakhs(r.profit_lakhs), align: 'right' },
                      { key: 'r', header: 'Call', value: (r) => r.recommendation, render: (r) => (r.recommendation ? <Pill tone={REC[r.recommendation].tone}>{REC[r.recommendation].label}</Pill> : '—') },
                    ]}
                  />
                </Card>
              </div>

              <Card>
                <CardHeader title="Fabric value per day" subtitle="₹ lakh of fabric woven, with efficiency" />
                <CardBody><TrendChart data={d.revenue_trend} xKey="label" series={[{ key: 'revenue_lakhs', label: 'Fabric value (₹ L)', color: 0 }]} format={(v) => `₹${v.toFixed(1)} L`} area /></CardBody>
              </Card>
            </>
          );
        }}
      </Load>
    </>
  );
};
