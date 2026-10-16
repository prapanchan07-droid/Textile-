import React, { useMemo, useState } from 'react';
import { Search } from 'lucide-react';
import { useFleet } from '../../../api/weaving';
import { useParam } from '../../../app/state';
import { cn } from '../../../lib/format';
import { PageHeader } from '../../../layout/PageHeader';
import { Card, Segmented } from '../../../design/ui';
import { StatGrid } from '../../../design/viz/StatTile';
import { AlertCard, AiBadge, HealthRing } from '../../../design/viz/parts';
import { Load, Pill, Section, shortDate } from '../common';
import { MachineDrawer } from './MachineDrawer';
import type { MachineRow } from '../../../types/pages';

const BAND_TONE = { HEALTHY: 'ok', WATCH: 'warn', AT_RISK: 'bad' } as const;

const Tile: React.FC<{ m: MachineRow; onOpen: () => void }> = ({ m, onOpen }) => (
  <button onClick={onOpen} className="group flex items-center gap-3 rounded-2xl border border-line/80 bg-surface p-3.5 text-left shadow-card transition-all hover:-translate-y-0.5 hover:border-line-strong hover:shadow-lift">
    <HealthRing score={m.health} band={m.band} size={54} />
    <div className="min-w-0 flex-1">
      <div className="flex items-center gap-2">
        <span className="text-[15px] font-semibold text-ink">{m.loom}</span>
        <span className={cn('size-2 rounded-full', m.status === 'STOPPED' ? 'bg-bad' : m.status === 'IDLE' ? 'bg-ink-3' : 'bg-ok')} title={m.status === 'STOPPED' ? `Stopped ${m.stopped_min} min: ${m.stop_reason}` : m.status} />
        {m.alerts.length > 0 && <Pill tone={m.alerts.some((a) => a.level === 'CRITICAL') ? 'bad' : 'warn'}>{m.alerts.length} alert{m.alerts.length > 1 ? 's' : ''}</Pill>}
      </div>
      <div className="truncate text-xs text-ink-3">{m.make} {m.model} · {m.year} · {m.bay}</div>
      <div className="mt-1 flex items-center gap-3 text-xs text-ink-2">
        <span>{m.style}</span>
        <span className="num">{m.efficiency_pct != null ? `${m.efficiency_pct}%` : '—'} eff.</span>
        {m.next_pm && <span className={cn(m.next_pm.overdue_days > 0 ? 'font-medium text-bad' : 'text-ink-3')}>PM {m.next_pm.overdue_days > 0 ? `${m.next_pm.overdue_days} d late` : shortDate(m.next_pm.due)}</span>}
      </div>
    </div>
  </button>
);

export const MachinesPage: React.FC = () => {
  const q = useFleet();
  const [open, setOpen] = useParam('loom', '');
  const [band, setBand] = useState<'ALL' | 'AT_RISK' | 'WATCH' | 'HEALTHY'>('ALL');
  const [type, setType] = useState('ALL');
  const [text, setText] = useState('');
  const filter = useMemo(
    () => (rows: MachineRow[]) =>
      rows.filter((m) => (band === 'ALL' || m.band === band) && (type === 'ALL' || m.type === type) && `${m.loom} ${m.make} ${m.model} ${m.style} ${m.bay}`.toLowerCase().includes(text.toLowerCase())),
    [band, type, text],
  );
  return (
    <>
      <PageHeader title="Machines" description="Every loom's record and health, with an early warning when a machine drifts away from its own normal." />
      <Load q={q}>
        {(d) => {
          const rows = filter(d.looms);
          const types = Array.from(new Set(d.looms.map((l) => l.type)));
          return (
            <>
              <StatGrid items={d.kpis} />
              <Section title="Machine watch" ai hint="vibration, motor temperature, air pressure, power">
                {d.alerts.length === 0 ? (
                  <Card><p className="p-6 text-center text-sm text-ink-3">No machine is drifting from its own normal.</p></Card>
                ) : (
                  <div className="grid gap-2.5 xl:grid-cols-2">
                    {d.alerts.slice(0, 8).map((a, i) => <AlertCard key={i} a={a} to={`/weaving/machines?loom=${a.loom}`} />)}
                  </div>
                )}
                <p className="text-xs text-ink-3">{d.method.join(' ')}</p>
              </Section>
              <Section title="All looms" hint={`${rows.length} of ${d.looms.length}`}>
                <div className="flex flex-wrap items-center gap-2">
                  <Segmented value={band} onChange={setBand} ariaLabel="Health" options={[{ value: 'ALL', label: 'All' }, { value: 'AT_RISK', label: 'At risk' }, { value: 'WATCH', label: 'Watch' }, { value: 'HEALTHY', label: 'Healthy' }]} />
                  <Segmented value={type} onChange={setType} ariaLabel="Type" options={[{ value: 'ALL', label: 'All types' }, ...types.map((t) => ({ value: t, label: t }))]} />
                  <label className="relative ml-auto">
                    <Search className="pointer-events-none absolute left-2.5 top-1/2 size-3.5 -translate-y-1/2 text-ink-3" />
                    <input value={text} onChange={(e) => setText(e.target.value)} placeholder="Search loom, make, style, bay" className="h-8 w-60 rounded-lg border border-line bg-surface pl-8 pr-3 text-sm outline-none focus:border-accent" />
                  </label>
                </div>
                <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
                  {rows.map((m) => <Tile key={m.loom} m={m} onOpen={() => setOpen(m.loom)} />)}
                </div>
                {rows.length === 0 && <Card><p className="p-6 text-center text-sm text-ink-3">No loom matches.</p></Card>}
              </Section>
            </>
          );
        }}
      </Load>
      <MachineDrawer loom={open || null} onClose={() => setOpen(null)} />
    </>
  );
};
