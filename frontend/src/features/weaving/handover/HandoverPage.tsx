import React from 'react';
import { Printer } from 'lucide-react';
import { useHandover } from '../../../api/weaving';
import { useParam } from '../../../app/state';
import { num, pct } from '../../../lib/format';
import { PageHeader } from '../../../layout/PageHeader';
import { Button, Card, CardBody, CardHeader, Segmented } from '../../../design/ui';
import { AiBadge } from '../../../design/viz/parts';
import { Load, Pill, shortDate } from '../common';
import { NoteComposer, NoteList } from '../cockpit/Notes';

export const HandoverPage: React.FC = () => {
  const [which, setWhich] = useParam('shift', 'current');
  const q = useHandover(which === 'previous' ? 'previous' : 'current');
  return (
    <>
      <PageHeader
        title="Shift Handover"
        description="A summary of the shift, drafted from the data, for whoever takes over."
        actions={
          <>
            <Segmented value={which === 'previous' ? 'previous' : 'current'} onChange={(v) => setWhich(v)} ariaLabel="Shift" options={[{ value: 'current', label: 'This shift' }, { value: 'previous', label: 'Last shift' }]} />
            <Button icon={<Printer className="size-4" />} onClick={() => window.print()}>Print</Button>
          </>
        }
      />
      <Load q={q}>
        {(d) => (
          <div className="mx-auto max-w-4xl space-y-4">
            <Card className="p-6">
              <div className="flex flex-wrap items-center justify-between gap-2 border-b border-line pb-4">
                <div>
                  <div className="text-xs font-semibold uppercase tracking-[0.14em] text-ink-3">Shift hand-over</div>
                  <h2 className="text-2xl font-semibold text-ink">{d.shift.name} <span className="text-base font-normal text-ink-3">· {shortDate(d.shift.date)} · {d.shift.start} to {d.shift.end}</span></h2>
                </div>
                <Pill tone={d.complete ? 'ok' : 'warn'}>{d.complete ? 'Shift complete' : 'Draft: shift still running'}</Pill>
              </div>
              <div className="mt-4">
                <h3 className="mb-2 flex items-center gap-2 text-sm font-semibold text-ink">The shift in a few lines <AiBadge label="drafted from data" /></h3>
                <ul className="space-y-2">
                  {d.narrative.map((n, i) => (
                    <li key={i} className="flex gap-2.5 text-[15px] leading-6 text-ink-2"><span className="mt-2.5 size-1.5 shrink-0 rounded-full bg-accent" />{n}</li>
                  ))}
                </ul>
              </div>
              <div className="mt-5 grid grid-cols-2 gap-3 md:grid-cols-4">
                {[
                  ['Woven', `${num(d.kpis.meters)} m`, `plan ${num(d.kpis.plan_m)} m`],
                  ['Against plan', pct(d.kpis.achievement_pct), ''],
                  ['Efficiency', pct(d.kpis.efficiency_pct), ''],
                  ['Stops', String(d.kpis.stops), `${d.kpis.avg_stop_min ?? '—'} min average · ${d.kpis.downtime_min} min lost`],
                ].map(([l, v, h]) => (
                  <div key={l} className="rounded-xl bg-subtle px-4 py-3"><div className="text-xs text-ink-3">{l}</div><div className="num text-xl font-semibold text-ink">{v}</div><div className="truncate text-[11px] text-ink-3">{h}</div></div>
                ))}
              </div>
            </Card>
            <div className="grid gap-4 md:grid-cols-2">
              <Card>
                <CardHeader title="Longest stops" />
                <div className="divide-y divide-line/60 px-5 pb-3">
                  {d.longest_stops.map((s, i) => <div key={i} className="flex items-center justify-between py-2 text-sm"><span><b className="text-ink">{s.loom}</b> <span className="text-ink-3">{s.reason} · {s.at}</span></span><span className="num font-semibold text-ink">{s.minutes} min{s.open && <span className="ml-1 text-bad">open</span>}</span></div>)}
                  {d.longest_stops.length === 0 && <p className="py-3 text-sm text-ink-3">No unplanned stops.</p>}
                </div>
              </Card>
              <Card>
                <CardHeader title="Looms to watch" subtitle="Lowest efficiency this shift, and machine alerts" />
                <div className="divide-y divide-line/60 px-5 pb-3">
                  {d.weakest.map((w) => <div key={w.loom} className="flex items-center justify-between py-2 text-sm"><b className="text-ink">{w.loom}</b><span className="num text-ink-2">{pct(w.efficiency_pct, 0)}</span></div>)}
                  {d.watch.map((w, i) => <div key={i} className="py-2 text-sm text-warn">{w.title}</div>)}
                </div>
              </Card>
            </div>
            <Card>
              <CardHeader title="Carry over to the next shift" subtitle="Unresolved warnings and urgent notes" />
              <div className="px-5 pb-4"><NoteList notes={d.carry_over} empty="Nothing carried over." /></div>
            </Card>
            <div className="grid gap-4 md:grid-cols-2">
              <Card>
                <CardHeader title="Crew" subtitle={`${d.roster.present} present · ${d.roster.absent} absent`} />
                <div className="divide-y divide-line/60 px-5 pb-3 text-sm">
                  {d.roster.people.filter((p) => p.status !== 'PRESENT').map((p) => <div key={p.code} className="flex justify-between py-2"><span className="text-ink-2">{p.name} <span className="text-ink-3">· {p.designation}</span></span><Pill tone="bad">{p.status.toLowerCase()}</Pill></div>)}
                  {d.roster.absent === 0 && <p className="py-3 text-ink-3">Full crew.</p>}
                  {d.roster.overloaded.map((o) => <div key={o.code} className="py-2 text-warn">{o.name} covers {o.looms.length} looms.</div>)}
                </div>
              </Card>
              <Card>
                <CardHeader title="Open actions" />
                <div className="divide-y divide-line/60 px-5 pb-3 text-sm">
                  {d.actions.map((a) => <div key={a.ref} className="flex justify-between gap-3 py-2"><span className="text-ink-2">{a.issue}</span><span className="shrink-0 text-xs text-ink-3">{a.owner}</span></div>)}
                  {d.actions.length === 0 && <p className="py-3 text-ink-3">None.</p>}
                </div>
              </Card>
            </div>
            <Card className="print:hidden">
              <CardHeader title="Add to the hand-over" subtitle="Notes are saved to the current shift." />
              <CardBody className="space-y-3">
                <NoteComposer looms={[]} />
                <NoteList notes={d.notes} empty="No notes written for this shift." />
              </CardBody>
            </Card>
          </div>
        )}
      </Load>
    </>
  );
};
