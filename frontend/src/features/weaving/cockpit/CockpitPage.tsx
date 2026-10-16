import React from 'react';
import { Link } from 'react-router-dom';
import { useCockpit } from '../../../api/weaving';
import { useParam } from '../../../app/state';
import { cn } from '../../../lib/format';
import { PageHeader } from '../../../layout/PageHeader';
import { Card, CardBody, CardHeader, StatusPill } from '../../../design/ui';
import { StatGrid } from '../../../design/viz/StatTile';
import { PlanVsActual } from '../../../design/viz/charts2';
import { AiBadge, AlertCard, FindingCard, FloorStrip } from '../../../design/viz/parts';
import { CATEGORY_COLORS } from '../../../design/viz/palette';
import { Load, Pill, Section, shortDate } from '../common';
import { MachineDrawer } from '../machines/MachineDrawer';
import { NoteComposer, NoteList } from './Notes';

export const CockpitPage: React.FC = () => {
  const q = useCockpit();
  const [open, setOpen] = useParam('loom', '');
  return (
    <>
      <PageHeader title="Shift Cockpit" description="Your shift, live: what is stopped, who is on, and what the next shift needs to hear." />
      <Load q={q}>
        {(d) => {
          const hot = d.stopped_now.filter((s) => !s.planned);
          const totalCause = Math.max(1, ...d.top_causes.map((c) => c.downtime_min));
          return (
            <>
              <Card className="overflow-hidden border-0 bg-gradient-to-r from-[#0b2f4a] to-[#0a6d8f] p-5 text-white shadow-lift">
                <div className="flex flex-wrap items-center justify-between gap-4">
                  <div>
                    <div className="text-2xs font-semibold uppercase tracking-[0.16em] text-white/70">Shift in progress</div>
                    <div className="mt-1 text-2xl font-semibold">{d.shift.name} <span className="text-base font-normal text-white/70">· {d.shift.start} to {d.shift.end}</span></div>
                  </div>
                  <div className="min-w-[220px] flex-1 sm:max-w-sm">
                    <div className="mb-1 flex justify-between text-xs text-white/75"><span>{d.shift.elapsed_pct}% of the shift gone</span><span>{hot.length} stopped now</span></div>
                    <div className="h-2.5 overflow-hidden rounded-full bg-white/15"><div className="h-full rounded-full bg-[#35d0a8]" style={{ width: `${d.shift.elapsed_pct}%` }} /></div>
                  </div>
                </div>
              </Card>
              <StatGrid items={d.kpis} />
              <div className="grid gap-4 xl:grid-cols-3">
                <Card className="xl:col-span-2">
                  <CardHeader title="This shift against plan" subtitle="Cumulative metres, hour by hour" />
                  <CardBody>{d.chart.length ? <PlanVsActual rows={d.chart} /> : <p className="py-8 text-center text-sm text-ink-3">The shift has no readings yet.</p>}</CardBody>
                </Card>
                <Card>
                  <CardHeader title={`Stopped now · ${hot.length}`} subtitle="Go to the longest first" />
                  <div className="divide-y divide-line/70 px-5 pb-3">
                    {hot.length === 0 && <p className="py-6 text-center text-sm text-ink-3">Everything is weaving.</p>}
                    {hot.slice(0, 7).map((s) => (
                      <button key={s.loom} onClick={() => setOpen(s.loom)} className="block w-full py-2.5 text-left">
                        <div className="flex items-center justify-between"><span className="text-sm font-semibold text-ink">{s.loom}</span><span className={cn('num text-sm font-semibold', s.minutes > 20 ? 'text-bad' : 'text-warn')}>{s.minutes} min</span></div>
                        <div className="text-xs text-ink-3">{s.reason}{s.fitter ? ` · fitter ${s.fitter}` : ''}</div>
                        {s.hint && s.minutes > 10 && <div className="mt-0.5 text-xs text-ink-2">Check: {s.hint}</div>}
                      </button>
                    ))}
                  </div>
                </Card>
              </div>
              <Card>
                <CardHeader title="The floor" subtitle="Every loom: tap one for its machine record" />
                <CardBody><FloorStrip looms={d.floor.map((f) => ({ ...f, efficiency_pct: f.efficiency_pct, stopped_min: f.stopped_min }))} onSelect={(l) => setOpen(l)} /></CardBody>
              </Card>
              <div className="grid gap-4 xl:grid-cols-3">
                <Card>
                  <CardHeader title="Why looms stopped this shift" subtitle="Minutes lost" />
                  <div className="space-y-2.5 px-5 pb-4">
                    {d.top_causes.length === 0 && <p className="text-sm text-ink-3">No stops yet.</p>}
                    {d.top_causes.map((c) => (
                      <div key={c.cause}>
                        <div className="flex justify-between text-sm"><span className="text-ink-2">{c.cause}</span><span className="num font-medium">{c.downtime_min} min · {c.stops}</span></div>
                        <div className="mt-1 h-1.5 overflow-hidden rounded-full bg-muted"><div className="h-full rounded-full bg-accent" style={{ width: `${(c.downtime_min / totalCause) * 100}%` }} /></div>
                      </div>
                    ))}
                  </div>
                </Card>
                <div className="space-y-3 xl:col-span-2">
                  <div className="flex items-center gap-2 text-base font-semibold text-ink">Machine watch <AiBadge /></div>
                  {d.watch.length === 0 && <Card><p className="p-5 text-sm text-ink-3">No machine needs a closer look.</p></Card>}
                  <div className="grid gap-2.5 md:grid-cols-2">
                    {d.watch.map((w, i) => (
                      <button key={i} onClick={() => setOpen(w.loom)} className="rounded-xl border border-line/80 bg-surface p-3 text-left shadow-card hover:shadow-lift">
                        <div className="flex items-center gap-2"><b className="text-sm text-ink">{w.title}</b><Pill tone={w.level === 'CRITICAL' ? 'bad' : 'warn'}>{w.level.toLowerCase()}</Pill></div>
                        <p className="mt-1 text-xs leading-5 text-ink-2">{w.fact}</p>
                      </button>
                    ))}
                  </div>
                </div>
              </div>
              <div className="grid gap-4 xl:grid-cols-3">
                <Card>
                  <CardHeader title="Crew on this shift" subtitle={`${d.roster.present} present · ${d.roster.absent} absent`} />
                  <div className="max-h-96 divide-y divide-line/60 overflow-auto px-5 pb-3">
                    {d.roster.overloaded.map((o) => <div key={o.code} className="my-2 rounded-lg bg-warn-soft px-3 py-2 text-xs text-warn"><b>{o.name}</b> is covering {o.looms.length} looms ({o.looms.join(', ')}).</div>)}
                    {d.roster.people.filter((p) => p.role !== 'INSPECTOR').map((p) => (
                      <div key={p.code} className="flex items-center justify-between py-2 text-sm">
                        <div className="min-w-0"><div className={cn('truncate font-medium', p.status !== 'PRESENT' && 'text-ink-3 line-through')}>{p.name}</div><div className="truncate text-xs text-ink-3">{p.designation}{p.looms.length ? ` · ${p.looms.slice(0, 4).join(', ')}${p.looms.length > 4 ? '…' : ''}` : ''}</div></div>
                        {p.status !== 'PRESENT' ? <Pill tone="bad">{p.status.toLowerCase()}</Pill> : <Pill tone="ok">present</Pill>}
                      </div>
                    ))}
                  </div>
                </Card>
                <Card className="xl:col-span-2">
                  <CardHeader title="Notes and hand-over" subtitle="What you write here is what the next shift, and maintenance, will see." />
                  <div className="space-y-3 px-5 pb-5">
                    <NoteComposer looms={d.floor.map((f) => f.loom)} />
                    <NoteList notes={d.notes} empty="No notes yet for this shift." />
                  </div>
                </Card>
              </div>
              {d.findings.length > 0 && (
                <Section title="What the AI found for your shift" ai>
                  <div className="space-y-2.5">{d.findings.map((f) => <FindingCard key={f.key} f={f} />)}</div>
                </Section>
              )}
              <Card>
                <CardHeader title="Open actions" actions={<Link to="/weaving/actions" className="text-xs font-medium text-accent">Action tracker</Link>} />
                <div className="divide-y divide-line/60 px-5 pb-3">
                  {d.actions.map((a) => <div key={a.ref} className="flex items-center justify-between gap-3 py-2 text-sm"><span className="text-ink-2">{a.issue}</span><span className="shrink-0 text-xs text-ink-3">{a.owner} · due {shortDate(a.due)}</span></div>)}
                  {d.actions.length === 0 && <p className="py-3 text-sm text-ink-3">Nothing open.</p>}
                </div>
              </Card>
            </>
          );
        }}
      </Load>
      <MachineDrawer loom={open || null} onClose={() => setOpen(null)} />
    </>
  );
};
