import React, { useMemo, useState } from 'react';
import { ArrowRight, Check, X } from 'lucide-react';
import { useScheduler, useSchedulerDecision } from '../../../api/weaving';
import { cn, num } from '../../../lib/format';
import { PageHeader } from '../../../layout/PageHeader';
import { Button, Card, CardBody, CardHeader, Notice, Segmented } from '../../../design/ui';
import { DataTable } from '../../../design/DataTable';
import { AiBadge, Gantt, PriorityDot, orderPalette } from '../../../design/viz/parts';
import { Hero, Load, Pill, Section, shortDate } from '../common';
import type { SchedulerData } from '../../../types/pages';

const Delta: React.FC<{ label: string; from: string | number; to: string | number; good?: boolean }> = ({ label, from, to, good }) => (
  <div className="rounded-xl bg-white/[0.09] px-4 py-3 backdrop-blur">
    <div className="text-xs text-white/70">{label}</div>
    <div className="mt-1 flex items-baseline gap-2"><span className="num text-base text-white/60 line-through decoration-white/30">{from}</span><ArrowRight className="size-3.5 text-white/60" /><span className={cn('num text-2xl font-semibold', good ? 'text-[#7ee2c4]' : 'text-white')}>{to}</span></div>
  </div>
);

const Body: React.FC<{ d: SchedulerData }> = ({ d }) => {
  const [mode, setMode] = useState<'proposed' | 'baseline'>('proposed');
  const [note, setNote] = useState('');
  const [confirm, setConfirm] = useState<null | 'APPROVE' | 'REJECT'>(null);
  const decide = useSchedulerDecision();
  const colorOf = useMemo(() => orderPalette(d.orders.map((o) => o.order_no)), [d.orders]);
  const rows = Object.keys(d.timeline[mode]).sort().map((loom) => ({ loom, segs: d.timeline[mode][loom] }));
  const today = new Date(d.today);
  const dueMarks = d.orders.filter((o) => o.due).map((o) => ({ order: o.order_no, day: Math.round((new Date(o.due!).getTime() - today.getTime()) / 86400000) }));
  const b = d.baseline, p = d.proposed;
  const moved = new Set(d.moves.map((m) => m.loom)).size;
  return (
    <>
      <Hero
        eyebrow="AI proposal · nothing changes until you approve"
        tone={p.late_orders < b.late_orders ? 'ok' : 'warn'}
        title={b.late_orders === p.late_orders ? `The current plan already gives the best result found: ${p.late_orders} order(s) late.` : `Moving ${moved} looms would cut late orders from ${b.late_orders} to ${p.late_orders} over the next ${d.horizon_days} days.`}
        aside={
          <div className="grid grid-cols-2 gap-2.5">
            <Delta label="Orders late" from={b.late_orders} to={p.late_orders} good={p.late_orders < b.late_orders} />
            <Delta label="Days late, total" from={b.total_late_days} to={p.total_late_days} good={p.total_late_days < b.total_late_days} />
            <Delta label="Style changes" from={b.changeovers} to={p.changeovers} />
            <Delta label="Capacity booked" from={`${b.capacity_booked_pct}%`} to={`${p.capacity_booked_pct}%`} />
          </div>
        }
      >
        <ul className="space-y-1 text-sm text-white/85">{d.summary.map((s, i) => <li key={i} className="flex gap-2"><span className="mt-2 size-1.5 shrink-0 rounded-full bg-white/50" />{s}</li>)}</ul>
      </Hero>

      <Card>
        <CardHeader title="Order by order" subtitle="Expected completion if nothing changes, against the proposed plan" />
        <DataTable dense rows={d.orders} rowKey={(r) => r.order_no} columns={[
          { key: 'o', header: 'Order', value: (r) => r.order_no, render: (r) => <span className="inline-flex items-center gap-2 font-semibold"><span className="size-2.5 rounded-sm" style={{ background: colorOf(r.order_no) }} />{r.order_no}<PriorityDot p={r.priority} /></span> },
          { key: 'c', header: 'Customer · style', value: (r) => r.customer ?? '', render: (r) => <span className="text-ink-2">{r.customer} · {r.style}</span>, hideBelow: 'md' },
          { key: 'r', header: 'Left', value: (r) => r.remaining_m, render: (r) => `${num(r.remaining_m)} m`, align: 'right', hideBelow: 'md' },
          { key: 'd', header: 'Due', value: (r) => r.due ?? '', render: (r) => shortDate(r.due), align: 'right' },
          { key: 'b', header: 'As booked', value: (r) => r.baseline_eta ?? '', render: (r) => <span className={cn(r.baseline_late && 'font-semibold text-bad')}>{r.baseline_eta ? shortDate(r.baseline_eta) : 'beyond horizon'}{r.baseline_slack_days != null && ` (${r.baseline_slack_days > 0 ? '+' : ''}${r.baseline_slack_days})`}</span>, align: 'right' },
          { key: 'p', header: 'Proposed', value: (r) => r.proposed_eta ?? '', render: (r) => <span className={cn(r.proposed_late ? 'font-semibold text-bad' : r.improved ? 'font-semibold text-ok' : '')}>{r.proposed_eta ? shortDate(r.proposed_eta) : 'beyond horizon'}{r.proposed_slack_days != null && ` (${r.proposed_slack_days > 0 ? '+' : ''}${r.proposed_slack_days})`}</span>, align: 'right' },
          { key: 'i', header: '', value: (r) => (r.improved ? 1 : 0), render: (r) => (r.improved ? <Pill tone="ok">better</Pill> : r.proposed_late ? <Pill tone="bad">still late</Pill> : null) },
        ]} />
      </Card>

      <Card>
        <CardHeader title="Loom timeline" subtitle={`Which loom weaves which order over the next ${d.horizon_days} days. Triangles mark due dates.`}
          actions={<Segmented size="sm" value={mode} onChange={setMode} ariaLabel="Plan" options={[{ value: 'proposed', label: 'Proposed' }, { value: 'baseline', label: 'As booked' }]} />} />
        <CardBody>
          <Gantt rows={rows} horizon={d.horizon_days} orderColor={colorOf} startDate={d.today} dueMarks={dueMarks} />
          <div className="mt-3 flex flex-wrap gap-x-4 gap-y-1 text-xs text-ink-2">{d.orders.map((o) => <span key={o.order_no} className="inline-flex items-center gap-1.5"><span className="size-2.5 rounded-sm" style={{ background: colorOf(o.order_no) }} />{o.order_no} · {o.style}</span>)}</div>
        </CardBody>
      </Card>

      <Section title={`The moves, ${d.moves.length}`} hint="each with the reason and what happens to both orders" ai>
        <div className="grid gap-2.5 lg:grid-cols-2">
          {d.moves.map((m, i) => (
            <Card key={i} className="p-4">
              <div className="flex items-center justify-between gap-2">
                <div className="flex items-center gap-2 text-sm"><b className="text-base text-ink">{m.loom}</b><span className="text-ink-3">{m.from_order ?? 'no order'}</span><ArrowRight className="size-3.5 text-ink-3" /><b style={{ color: colorOf(m.to_order) }}>{m.to_order}</b></div>
                <span className="text-xs text-ink-3">{shortDate(m.date)}</span>
              </div>
              <p className="mt-1.5 text-sm leading-5 text-ink-2">{m.reason}</p>
              <div className="mt-2 flex flex-wrap gap-2 text-xs"><Pill tone="info">{num(m.gain_m_per_day)} m/day on the new order</Pill><Pill>{m.loom_eff_pct}% efficiency</Pill>{m.changeover && <Pill tone="warn">style change</Pill>}</div>
            </Card>
          ))}
          {d.moves.length === 0 && <Card><p className="p-6 text-center text-sm text-ink-3">No loom move would reduce lateness enough to be worth the disruption.</p></Card>}
        </div>
      </Section>

      {d.can_decide ? (
        <Card className="border-accent/30">
          <CardHeader title="Your decision" subtitle="Approving records this plan and raises one action per move for the supervisors. It does not move any loom by itself." />
          <CardBody className="space-y-3">
            {decide.isSuccess && <Notice tone="info">Plan {decide.data.plan_ref} {decide.data.status.toLowerCase()}{decide.data.actions_created ? `. ${decide.data.actions_created} actions are now in the Action Tracker.` : '.'}</Notice>}
            {decide.isError && <Notice tone="warn">{(decide.error as Error).message}</Notice>}
            {!decide.isSuccess && (
              <>
                <textarea value={note} onChange={(e) => setNote(e.target.value)} rows={2} placeholder="Optional note for the record" className="w-full rounded-lg border border-line bg-surface p-2 text-sm outline-none focus:border-accent" />
                <div className="flex flex-wrap items-center gap-2">
                  <Button variant="primary" icon={<Check className="size-4" />} loading={decide.isPending && confirm === 'APPROVE'} onClick={() => { setConfirm('APPROVE'); decide.mutate({ decision: 'APPROVE', signature: d.signature, note: note || undefined }); }}>Approve this plan</Button>
                  <Button icon={<X className="size-4" />} loading={decide.isPending && confirm === 'REJECT'} onClick={() => { setConfirm('REJECT'); decide.mutate({ decision: 'REJECT', signature: d.signature, note: note || undefined }); }}>Reject</Button>
                </div>
              </>
            )}
          </CardBody>
        </Card>
      ) : (
        <Notice tone="info">Only the owner or weaving manager can approve a plan.</Notice>
      )}
      {d.decisions.length > 0 && (
        <Card>
          <CardHeader title="Earlier decisions" />
          <div className="divide-y divide-line/60 px-5 pb-3 text-sm">{d.decisions.map((x) => <div key={x.id} className="flex items-center justify-between py-2"><span className="text-ink-2">{x.plan_ref} · {x.moves} moves{x.decision_note && ` · ${x.decision_note}`}</span><Pill tone={x.status === 'APPROVED' ? 'ok' : 'neutral'}>{x.status.toLowerCase()}</Pill></div>)}</div>
        </Card>
      )}
      <Card>
        <CardHeader title="How the plan is made" subtitle={<span className="inline-flex items-center gap-1.5"><AiBadge /> A transparent planner, not a black box</span>} />
        <CardBody>
          <p className="mb-2 text-sm text-ink-2">{d.objective}</p>
          <ul className="list-disc space-y-1 pl-5 text-sm text-ink-2">{d.assumptions.map((a, i) => <li key={i}>{a}</li>)}</ul>
        </CardBody>
      </Card>
    </>
  );
};

export const SchedulerPage: React.FC = () => {
  const q = useScheduler();
  return (
    <>
      <PageHeader title="AI Scheduler" description="Which looms should weave which orders so more orders ship on time. You review, you decide." />
      <Load q={q}>{(d) => <Body d={d} />}</Load>
    </>
  );
};
