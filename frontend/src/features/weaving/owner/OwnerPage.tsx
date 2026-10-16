import React from 'react';
import { Link } from 'react-router-dom';
import { ArrowRight, CalendarClock, CheckCircle2, Coins, Gauge, ShieldCheck, Sparkles, TrendingUp, Wallet } from 'lucide-react';
import { useOwner } from '../../../api/weaving';
import { usePeriod } from '../../../app/state';
import { cn, inrFromLakhs, num, pct } from '../../../lib/format';
import { PageHeader } from '../../../layout/PageHeader';
import { Card, CardBody, CardHeader } from '../../../design/ui';
import { DataTable } from '../../../design/DataTable';
import { StatGrid } from '../../../design/viz/StatTile';
import { RiskChip, SeverityChip } from '../../../design/viz/parts';
import { TrendChart } from '../../../design/charts/Charts';
import { Waterfall } from '../../../design/viz/charts2';
import { Load, Pill, Section, shortDate } from '../common';
import type { OwnerData } from '../../../types/pages';

const REC: Record<string, { label: string; tone: 'ok' | 'warn' | 'bad' | 'neutral' }> = {
  PUSH: { label: 'Take more orders', tone: 'ok' },
  HOLD: { label: 'Keep as is', tone: 'neutral' },
  REPRICE: { label: 'Reprice', tone: 'warn' },
  STOP: { label: 'Stop new orders', tone: 'bad' },
};

const kpiOf = (d: OwnerData, label: string) => d.kpis.find((k) => k.label === label);

/** One number the owner can repeat to someone else, with a plain sentence under it. */
const BigFigure: React.FC<{ icon: React.ReactNode; label: string; value: string; note: string; tone?: 'bad' | 'ok' | 'neutral' }> = ({ icon, label, value, note, tone = 'neutral' }) => (
  <div className="rounded-2xl bg-white/[0.09] p-4 backdrop-blur">
    <div className="mb-1.5 flex items-center gap-1.5 text-xs font-medium uppercase tracking-wide text-white/70">{icon} {label}</div>
    <div className={cn('num text-[32px] font-semibold leading-9', tone === 'bad' ? 'text-[#ff9b9b]' : tone === 'ok' ? 'text-[#7ee2c4]' : 'text-white')}>{value}</div>
    <p className="mt-1 text-xs leading-5 text-white/75">{note}</p>
  </div>
);

/** What the platform contributes, in terms an owner cares about. Every figure comes from the same payload as the rest of the page. */
const ValueCard: React.FC<{ icon: React.ReactNode; title: string; value: string; text: string; to?: string; cta?: string }> = ({ icon, title, value, text, to, cta }) => (
  <div className="flex flex-col rounded-2xl border border-line/80 bg-surface p-4 shadow-card">
    <div className="mb-2 flex items-center gap-2 text-xs font-medium text-ink-3">
      <span className="grid size-7 place-items-center rounded-lg bg-accent-soft text-accent-ink">{icon}</span>
      {title}
    </div>
    <div className="num text-2xl font-semibold tracking-tight text-ink">{value}</div>
    <p className="mt-1 flex-1 text-sm leading-5 text-ink-2">{text}</p>
    {to && (
      <Link to={to} className="mt-3 inline-flex items-center gap-1 text-sm font-semibold text-accent">
        {cta} <ArrowRight className="size-4" />
      </Link>
    )}
  </div>
);

export const OwnerPage: React.FC = () => {
  const [period] = usePeriod('LAST_7_DAYS');
  const q = useOwner(period);
  return (
    <>
      <PageHeader title="Owner Brief" description="How the mill is doing, what it is costing you, and what needs your decision." showPeriod defaultPeriod="LAST_7_DAYS" />
      <Load q={q}>
        {(d) => {
          const s = d.orders_summary;
          const money = d.money_visible;
          const tone = s.LATE ? 'bad' : s.AT_RISK ? 'warn' : 'ok';
          const verdict = s.LATE ? 'Needs attention' : s.AT_RISK ? 'Watch closely' : 'On track';

          const woven = kpiOf(d, 'Fabric woven');
          const value = kpiOf(d, 'Fabric value');
          const lost = kpiOf(d, 'Contribution lost');
          const eff = kpiOf(d, 'Efficiency');

          const losses = d.waterfall.filter((x) => x.kind === 'loss' && x.value < 0).map((x) => ({ label: x.label, value: -x.value })).sort((a, b) => b.value - a.value);
          const lossTotal = losses.reduce((a, b) => a + b.value, 0);
          const topLoss = losses[0];
          const needApproval = d.decisions.filter((x) => x.needs_approval).length;
          const decisionValue = d.decisions.reduce((a, x) => a + (x.impact_lakhs ?? 0), 0);
          const c = d.capacity;
          const ordersRecovered = c ? Math.max(c.late_now - c.late_with_plan, 0) : 0;
          const onTimePct = s.completed ? Math.round((s.completed_on_time / s.completed) * 100) : null;
          const bestStyle = [...d.styles].filter((x) => x.recommendation === 'PUSH').sort((a, b) => (b.margin_pct ?? 0) - (a.margin_pct ?? 0))[0];
          const worstStyle = d.styles.find((x) => x.recommendation === 'STOP' || x.recommendation === 'REPRICE');

          return (
            <>
              {/* 1. The verdict: one sentence, three numbers */}
              <Card className="relative overflow-hidden border-0 bg-gradient-to-br from-[#0b2f4a] via-[#0d4366] to-[#0a6d8f] p-6 text-white shadow-lift">
                <div aria-hidden className="pointer-events-none absolute -right-16 -top-16 size-64 rounded-full bg-white/[0.06]" />
                <div aria-hidden className="pointer-events-none absolute -bottom-24 right-24 size-72 rounded-full bg-white/[0.05]" />
                <div className="relative space-y-5">
                  <div className="flex flex-wrap items-center gap-3">
                    <span className="inline-flex items-center gap-1.5 text-2xs font-semibold uppercase tracking-[0.16em] text-white/70"><Sparkles className="size-3.5" /> Weaving department · {d.period}</span>
                    <span className={cn('inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-semibold', tone === 'bad' ? 'bg-bad/90' : tone === 'warn' ? 'bg-warn/90' : 'bg-[#1aa97f]')}>
                      <span className="size-1.5 rounded-full bg-white" /> {verdict}
                    </span>
                  </div>
                  <h2 className="max-w-4xl text-[22px] font-semibold leading-snug tracking-tight">{d.headline}</h2>
                  <div className="grid gap-3 md:grid-cols-3">
                    <BigFigure
                      icon={<Wallet className="size-3.5" />}
                      label="Fabric woven"
                      value={money ? inrFromLakhs(value?.value) : `${num(woven?.value)} m`}
                      note={money ? `${num(woven?.value)} m at ${pct(eff?.value)} efficiency this period.` : `${pct(eff?.value)} efficiency this period.`}
                    />
                    {money && (
                      <BigFigure
                        icon={<Coins className="size-3.5" />}
                        label="Earnings left on the table"
                        value={inrFromLakhs(lost?.value)}
                        tone="bad"
                        note={topLoss ? `Mostly ${topLoss.label.toLowerCase()} (${Math.round((topLoss.value / (lossTotal || 1)) * 100)}% of it).` : 'Lost to stops and slow running.'}
                      />
                    )}
                    <BigFigure
                      icon={<CalendarClock className="size-3.5" />}
                      label="Delivery promises at risk"
                      value={`${s.LATE + s.AT_RISK} of ${s.open}`}
                      tone={s.LATE + s.AT_RISK ? 'bad' : 'ok'}
                      note={money && s.value_at_risk_lakhs != null ? `${inrFromLakhs(s.value_at_risk_lakhs)} of fabric value rides on them.` : `${s.LATE} late, ${s.AT_RISK} at risk.`}
                    />
                  </div>
                </div>
              </Card>

              {/* 2. What the platform is doing for you */}
              <Section title="What this system is doing for you" hint="every figure below is computed from your own looms, orders and stop records">
                <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
                  <ValueCard
                    icon={<Coins className="size-4" />}
                    title="Money traced to its cause"
                    value={money ? inrFromLakhs(lossTotal) : `${losses.length} causes`}
                    text={topLoss ? `Lost earnings are split by cause, so you can see that “${topLoss.label}” is the biggest leak instead of guessing.` : 'No losses to explain in this period.'}
                    to="/weaving/insights"
                    cta="See the evidence"
                  />
                  <ValueCard
                    icon={<ShieldCheck className="size-4" />}
                    title="Orders the AI plan can rescue"
                    value={c ? `${ordersRecovered} of ${c.late_now}` : '—'}
                    text={c ? (c.late_now ? `Late orders if nothing changes: ${c.late_now}. With the proposed plan (${c.moves} loom moves): ${c.late_with_plan}. Nothing moves until you approve.` : 'No order is projected late as booked.') : 'The planner could not run for this period.'}
                    to="/weaving/scheduler"
                    cta="Review the plan"
                  />
                  <ValueCard
                    icon={<TrendingUp className="size-4" />}
                    title="Room to sell"
                    value={c ? `${num(c.free_loom_days)} loom-days` : '—'}
                    text={c ? `Only ${c.capacity_booked_pct}% of loom time in the next ${c.horizon_days} days is booked. ${bestStyle ? `${bestStyle.style} ${bestStyle.fabric} earns ${pct(bestStyle.margin_pct)} margin — the best use of it.` : 'Sales can fill this.'}` : 'Capacity could not be calculated.'}
                    to="/weaving/orders"
                    cta="See orders and margins"
                  />
                  <ValueCard
                    icon={<CheckCircle2 className="size-4" />}
                    title="Decisions ready for you"
                    value={`${d.decisions.length}`}
                    text={`${needApproval} need your approval${money && decisionValue > 0 ? `, together about ${inrFromLakhs(decisionValue)} at stake` : ''}. Each one comes with the evidence and a suggested action.`}
                  />
                </div>
              </Section>

              {/* 3. Decisions */}
              <Section title="Decisions waiting for you" ai hint="ranked by what is at stake">
                {d.decisions.length === 0 ? (
                  <Card><CardBody className="py-8 text-center text-sm text-ink-3">Nothing needs a decision from you right now.</CardBody></Card>
                ) : (
                  <div className="space-y-3">
                    {d.decisions.map((x, i) => (
                      <Link key={i} to={x.link} className="group grid gap-3 rounded-2xl border border-line/80 bg-surface p-4 shadow-card transition-all hover:-translate-y-0.5 hover:shadow-lift md:grid-cols-[2.25rem_1fr_auto] md:items-center">
                        <span className="hidden size-9 place-items-center rounded-full bg-subtle text-sm font-semibold text-ink-2 md:grid">{i + 1}</span>
                        <div className="min-w-0">
                          <div className="flex flex-wrap items-center gap-2">
                            <SeverityChip s={x.severity} />
                            <span className="text-[15px] font-semibold leading-snug text-ink">{x.title}</span>
                          </div>
                          <p className="mt-1 text-sm leading-5 text-ink-2">{x.why}</p>
                          <p className="mt-1.5 text-sm leading-5 text-ink"><b className="font-semibold">Suggested:</b> {x.action}</p>
                          <p className="mt-1 text-xs text-ink-3">{x.needs_approval ? 'Needs your approval' : 'For information'} · {x.confidence.toLowerCase()} confidence</p>
                        </div>
                        <div className="flex items-center justify-between gap-4 md:flex-col md:items-end">
                          {x.impact_lakhs != null && (
                            <div className="text-right">
                              <div className="num text-lg font-semibold text-bad">{inrFromLakhs(x.impact_lakhs)}</div>
                              <div className="text-2xs text-ink-3">at stake</div>
                            </div>
                          )}
                          <span className="inline-flex items-center gap-1 text-sm font-semibold text-accent">Open <ArrowRight className="size-4 transition-transform group-hover:translate-x-0.5" /></span>
                        </div>
                      </Link>
                    ))}
                  </div>
                )}
              </Section>

              {/* 4. Headline numbers */}
              <StatGrid items={d.kpis} />

              {/* 5. Where the money went + delivery promises */}
              <div className="grid gap-4 xl:grid-cols-5">
                <Card className="xl:col-span-3">
                  <CardHeader title="From what looms could earn to what they did" subtitle="₹ lakh of contribution. Stops and slow running are the steps down. An estimate: lost metres × the style's contribution per metre." />
                  <CardBody>
                    {money && d.waterfall.length ? (
                      <Waterfall items={d.waterfall} format={(v) => `₹${v.toFixed(1)} L`} height={300} />
                    ) : (
                      <p className="py-8 text-center text-sm text-ink-3">{money ? 'No data for this period.' : 'Money figures are not shown for your role.'}</p>
                    )}
                  </CardBody>
                </Card>
                <Card className="xl:col-span-2">
                  <CardHeader title="Delivery promises" subtitle={`${s.open} open orders, ${num(s.remaining_m)} m still to weave`} actions={<Link to="/weaving/orders" className="text-xs font-medium text-accent">All orders</Link>} />
                  <CardBody className="space-y-4">
                    <div className="flex h-3 overflow-hidden rounded-full bg-muted">
                      {[['LATE', 'bg-bad', s.LATE], ['AT_RISK', 'bg-warn', s.AT_RISK], ['ON_TRACK', 'bg-ok', s.ON_TRACK], ['UNSCHEDULED', 'bg-line-strong', s.UNSCHEDULED]].map(([k, cl, n]) => (
                        <span key={String(k)} className={String(cl)} style={{ width: `${(Number(n) / Math.max(s.open, 1)) * 100}%` }} />
                      ))}
                    </div>
                    <div className="grid grid-cols-2 gap-2 text-sm">
                      <div className="flex items-center justify-between rounded-lg bg-bad-soft px-3 py-2 text-bad"><span>Late</span><b className="num">{s.LATE}</b></div>
                      <div className="flex items-center justify-between rounded-lg bg-warn-soft px-3 py-2 text-warn"><span>At risk</span><b className="num">{s.AT_RISK}</b></div>
                      <div className="flex items-center justify-between rounded-lg bg-ok-soft px-3 py-2 text-ok"><span>On track</span><b className="num">{s.ON_TRACK}</b></div>
                      <div className="flex items-center justify-between rounded-lg bg-muted px-3 py-2 text-ink-2"><span>Not on a loom</span><b className="num">{s.UNSCHEDULED}</b></div>
                    </div>
                    {d.orders.length > 0 && (
                      <ul className="divide-y divide-line/70 rounded-xl border border-line/70">
                        {d.orders.slice(0, 4).map((o) => (
                          <li key={o.order_no} className="flex items-center justify-between gap-3 px-3 py-2 text-sm">
                            <div className="min-w-0">
                              <div className="truncate font-medium text-ink">{o.customer ?? o.order_no} <span className="font-normal text-ink-3">· {o.order_no}</span></div>
                              <div className="text-xs text-ink-3">due {shortDate(o.due_date)}{o.eta ? ` · expected ${shortDate(o.eta)}` : ''}</div>
                            </div>
                            <div className="flex shrink-0 flex-col items-end gap-1">
                              <RiskChip risk={o.risk} />
                              {money && o.revenue_at_stake_lakhs != null && <span className="num text-xs text-ink-2">{inrFromLakhs(o.revenue_at_stake_lakhs)}</span>}
                            </div>
                          </li>
                        ))}
                      </ul>
                    )}
                    <p className="text-xs text-ink-3">
                      <Gauge className="mr-1 inline size-3.5" />
                      Finished so far: {s.completed_on_time} of {s.completed} on time{onTimePct != null ? ` (${onTimePct}%)` : ''}.
                    </p>
                  </CardBody>
                </Card>
              </div>

              {/* 6. Customers and styles */}
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
                  <CardHeader
                    title="Which styles earn their place"
                    subtitle={worstStyle ? `${worstStyle.style} ${worstStyle.fabric} is the one to act on: ${worstStyle.reason ?? 'margin is thin'}` : 'Margin at the efficiency the looms actually achieved'}
                  />
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

              {/* 7. Trend */}
              <Card>
                <CardHeader title="Fabric value per day" subtitle="₹ lakh of fabric woven, last two weeks of complete days" />
                <CardBody>
                  {money ? (
                    <TrendChart data={d.revenue_trend} xKey="label" series={[{ key: 'revenue_lakhs', label: 'Fabric value (₹ L)', color: 0 }]} format={(v) => `₹${v.toFixed(1)} L`} area />
                  ) : (
                    <TrendChart data={d.revenue_trend} xKey="label" series={[{ key: 'efficiency_pct', label: 'Efficiency (%)', color: 0 }]} format={(v) => `${v.toFixed(1)}%`} area />
                  )}
                </CardBody>
              </Card>

              {/* 8. Trust note */}
              <p className="px-1 text-xs leading-5 text-ink-3">
                How to read this page: figures marked as estimates multiply lost metres by each style's contribution per metre. Delivery dates use each order's own recent pace and assume it keeps its looms.
                The AI plan is a proposal only; no loom moves until you approve it. Updated {new Date(d.as_of).toLocaleString('en-GB', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' })}.
              </p>
            </>
          );
        }}
      </Load>
    </>
  );
};
