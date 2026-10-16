import React from 'react';
import { Link } from 'react-router-dom';
import { useOrders } from '../../../api/weaving';
import { cn, inrFromLakhs, num, pct } from '../../../lib/format';
import { PageHeader } from '../../../layout/PageHeader';
import { Card, CardBody, CardHeader } from '../../../design/ui';
import { DataTable } from '../../../design/DataTable';
import { PriorityDot, RiskChip } from '../../../design/viz/parts';
import { ProgressBar } from '../../../design/viz/charts2';
import { Load, Pill, Section, shortDate } from '../common';

const REC: Record<string, { label: string; tone: 'ok' | 'warn' | 'bad' | 'neutral' }> = { PUSH: { label: 'Take more orders', tone: 'ok' }, HOLD: { label: 'Keep as is', tone: 'neutral' }, REPRICE: { label: 'Reprice', tone: 'warn' }, STOP: { label: 'Stop new orders', tone: 'bad' } };

export const OrdersPage: React.FC = () => {
  const q = useOrders();
  return (
    <>
      <PageHeader title="Orders & Profit" description="Will each order be delivered on time, who is waiting, and which styles earn their place." />
      <Load q={q}>
        {(d) => {
          const s = d.summary;
          return (
            <>
              <div className="grid grid-cols-2 gap-3 lg:grid-cols-5">
                {[
                  ['Late', s.LATE, 'bg-bad', 'projected to miss the due date'],
                  ['At risk', s.AT_RISK, 'bg-warn', 'under 2 days of slack, or late if pace dips'],
                  ['On track', s.ON_TRACK, 'bg-ok', ''],
                  ['Not on a loom', s.UNSCHEDULED, 'bg-line-strong', 'booked, no looms yet'],
                  ['Value at risk', d.money_visible ? inrFromLakhs(s.value_at_risk_lakhs) : '—', 'bg-accent', 'on late and at-risk orders'],
                ].map(([l, v, bar, h]) => (
                  <div key={String(l)} className="relative overflow-hidden rounded-2xl border border-line/80 bg-surface p-4 shadow-card">
                    <span className={cn('absolute inset-x-0 top-0 h-[3px]', String(bar))} />
                    <div className="text-xs font-medium text-ink-3">{l}</div>
                    <div className="num mt-1 text-[26px] font-semibold leading-8 text-ink">{v}</div>
                    <div className="truncate text-xs text-ink-3">{h}</div>
                  </div>
                ))}
              </div>
              <Card>
                <CardHeader title="Order book" subtitle="Progress and expected completion from each order's own pace over the last 7 complete days" actions={<Link to="/weaving/scheduler" className="text-xs font-medium text-accent">AI Scheduler</Link>} />
                <DataTable
                  rows={d.orders}
                  rowKey={(r) => r.order_no}
                  searchable={(r) => `${r.order_no} ${r.customer} ${r.style}`}
                  searchPlaceholder="Search order, customer or style"
                  exportName="orders"
                  columns={[
                    { key: 'o', header: 'Order', value: (r) => r.order_no, render: (r) => <div className="flex items-center gap-2"><PriorityDot p={r.priority} /><div><div className="font-semibold text-ink">{r.order_no}</div><div className="text-xs text-ink-3">{r.style} · {r.fabric}</div></div></div> },
                    { key: 'c', header: 'Customer', value: (r) => r.customer ?? '', render: (r) => <span>{r.customer} {r.tier === 'A' && <Pill tone="info">A</Pill>}</span>, hideBelow: 'md' },
                    { key: 'p', header: 'Progress', value: (r) => r.progress_pct, render: (r) => <div className="w-36"><ProgressBar pct={r.progress_pct} tone={r.risk === 'LATE' ? 'bad' : r.risk === 'AT_RISK' ? 'warn' : 'ok'} /><div className="mt-1 text-xs text-ink-3">{num(r.produced_m)} / {num(r.ordered_m)} m · {pct(r.progress_pct, 0)}</div></div> },
                    { key: 'l', header: 'Looms', value: (r) => r.looms.length, render: (r) => (r.looms.length ? r.looms.length : '—'), align: 'right', hideBelow: 'lg' },
                    { key: 'v', header: 'Pace', value: (r) => r.pace_m_per_day, render: (r) => (r.pace_m_per_day ? `${num(r.pace_m_per_day)} m/d` : '—'), align: 'right', hideBelow: 'lg' },
                    { key: 'd', header: 'Due', value: (r) => r.due_date ?? '', render: (r) => shortDate(r.due_date), align: 'right' },
                    { key: 'e', header: 'Expected', value: (r) => r.eta ?? r.completed_on ?? '', render: (r) => <span title={r.eta_early && r.eta_late ? `Likely between ${shortDate(r.eta_early)} and ${shortDate(r.eta_late)}` : ''}>{shortDate(r.eta ?? r.completed_on)}</span>, align: 'right' },
                    { key: 'sl', header: 'Slack', value: (r) => r.slack_days, render: (r) => (r.slack_days == null ? '—' : <b className={cn(r.slack_days < 0 ? 'text-bad' : r.slack_days <= 2 ? 'text-warn' : 'text-ok')}>{r.slack_days > 0 ? '+' : ''}{r.slack_days} d</b>), align: 'right' },
                    { key: 'r', header: 'Status', value: (r) => r.risk, render: (r) => <RiskChip risk={r.risk} /> },
                  ]}
                />
              </Card>
              <div className="grid gap-4 xl:grid-cols-2">
                <Card>
                  <CardHeader title="Customers" subtitle="Who is waiting on what" />
                  <DataTable dense rows={d.customers} rowKey={(r) => r.customer} columns={[
                    { key: 'c', header: 'Customer', value: (r) => r.customer, render: (r) => <span className="font-medium">{r.customer} {r.tier === 'A' && <Pill tone="info">Tier A</Pill>}</span> },
                    { key: 'o', header: 'Open', value: (r) => r.open_orders, render: (r) => r.open_orders, align: 'right' },
                    { key: 'r', header: 'Still to weave', value: (r) => r.remaining_m, render: (r) => `${num(r.remaining_m)} m`, align: 'right' },
                    { key: 'l', header: 'Late / at risk', value: (r) => r.late * 2 + r.at_risk, render: (r) => <span><b className={r.late ? 'text-bad' : ''}>{r.late}</b> / <b className={r.at_risk ? 'text-warn' : ''}>{r.at_risk}</b></span>, align: 'right' },
                    { key: 't', header: 'Delivered on time', value: (r) => r.completed_on_time, render: (r) => (r.completed ? `${r.completed_on_time}/${r.completed}` : '—'), align: 'right', hideBelow: 'md' },
                  ]} />
                </Card>
                {d.styles.length > 0 && (
                  <Card>
                    <CardHeader title="Style profitability" subtitle="Margin at the efficiency actually achieved" />
                    <DataTable dense rows={d.styles} rowKey={(r) => r.style} columns={[
                      { key: 's', header: 'Style', value: (r) => r.style, render: (r) => <div><div className="font-medium">{r.style}</div><div className="text-xs text-ink-3">{r.fabric}</div></div> },
                      { key: 'r', header: 'Rate', value: (r) => r.rate_per_m, render: (r) => `₹${r.rate_per_m}`, align: 'right', hideBelow: 'md' },
                      { key: 'c', header: 'Cost', value: (r) => r.cost_per_m, render: (r) => `₹${r.cost_per_m}`, align: 'right', hideBelow: 'md' },
                      { key: 'm', header: 'Margin', value: (r) => r.margin_pct, render: (r) => <b className={cn((r.margin_pct ?? 0) < 10 && 'text-bad')}>{pct(r.margin_pct)}</b>, align: 'right' },
                      { key: 'p', header: 'Profit', value: (r) => r.profit_lakhs, render: (r) => inrFromLakhs(r.profit_lakhs), align: 'right' },
                      { key: 'rc', header: 'Call', value: (r) => r.recommendation, render: (r) => (r.recommendation ? <Pill tone={REC[r.recommendation].tone}>{REC[r.recommendation].label}</Pill> : '—') },
                    ]} />
                  </Card>
                )}
              </div>
              <p className="text-xs text-ink-3">{d.notes.join(' ')}</p>
            </>
          );
        }}
      </Load>
    </>
  );
};
