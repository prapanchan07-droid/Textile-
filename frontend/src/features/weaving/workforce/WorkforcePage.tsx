import React, { useMemo, useState } from 'react';
import { Phone, Search } from 'lucide-react';
import { useWorkforce } from '../../../api/weaving';
import { useParam } from '../../../app/state';
import { cn, num, pct } from '../../../lib/format';
import { PageHeader } from '../../../layout/PageHeader';
import { Card, CardBody, CardHeader, Segmented, StatusPill } from '../../../design/ui';
import { DataTable } from '../../../design/DataTable';
import { Drawer } from '../../../design/Drawer';
import { ColumnChart } from '../../../design/charts/Charts';
import { Heatmap } from '../../../design/viz/Heatmap';
import { badHigh } from '../../../design/viz/palette';
import { AiBadge } from '../../../design/viz/parts';
import { Load, Pill, Section, shortDate } from '../common';
import type { DirectoryRow } from '../../../types/pages';

const ROLE = { WEAVER: 'Weaver', FITTER: 'Fitter', SUPERVISOR: 'Supervisor', INSPECTOR: 'Inspector', TECHNICIAN: 'Technician' } as const;

export const WorkforcePage: React.FC = () => {
  const q = useWorkforce();
  const [open, setOpen] = useParam('emp', '');
  const [role, setRole] = useState('ALL');
  return (
    <>
      <PageHeader title="Workforce" description="Who is on the floor, how often they are present, and where cover or skills are thin. No pay data is held here." />
      <Load q={q}>
        {(d) => {
          const rows = d.directory.filter((r) => role === 'ALL' || r.role === role);
          const person = d.directory.find((r) => r.code === open) ?? null;
          const k = d.kpis;
          return (
            <>
              <div className="grid grid-cols-2 gap-3 lg:grid-cols-5">
                {[
                  ['People', num(k.headcount), `${k.by_role.WEAVER ?? 0} weavers · ${k.by_role.FITTER ?? 0} fitters`],
                  ['Present today', `${k.present_today}/${k.tracked_today}`, 'weavers and fitters on shifts so far'],
                  ['Absenteeism, 14 days', pct(k.absenteeism_14d_pct), 'absent or on leave'],
                  ['Permanent staff', pct(k.permanent_pct, 0), `${100 - Math.round(k.permanent_pct ?? 0)}% on contract`],
                  ['Average experience', k.avg_experience_years != null ? `${k.avg_experience_years} yrs` : '—', 'across the floor'],
                ].map(([l, v, h]) => (
                  <div key={l} className="rounded-2xl border border-line/80 bg-surface p-4 shadow-card"><div className="text-xs font-medium text-ink-3">{l}</div><div className="num mt-1 text-[26px] font-semibold leading-8">{v}</div><div className="mt-0.5 truncate text-xs text-ink-3">{h}</div></div>
                ))}
              </div>
              <div className="grid gap-4 xl:grid-cols-3">
                <Card>
                  <CardHeader title="Cover today" subtitle="Present against what the loom count needs" />
                  <div className="space-y-2 px-5 pb-4">
                    {d.coverage.map((c, i) => (
                      <div key={i} className="flex items-center justify-between rounded-lg bg-subtle px-3 py-2 text-sm">
                        <span className="text-ink-2">{c.shift} · {c.role}</span>
                        <span className="inline-flex items-center gap-2"><b className="num">{c.present}/{c.required}</b>{c.absent > 0 && <span className="text-xs text-ink-3">{c.absent} off</span>}<StatusPill status={c.status} /></span>
                      </div>
                    ))}
                    {d.coverage.length === 0 && <p className="text-sm text-ink-3">No shift has started yet.</p>}
                  </div>
                </Card>
                <Card>
                  <CardHeader title="Absence by day" subtitle="Share of crew records marked absent or on leave" />
                  <CardBody><ColumnChart data={d.absenteeism_daily.map((a) => ({ label: String(new Date(a.date).getDate()), absent_pct: a.absent_pct ?? 0 }))} xKey="label" series={[{ key: 'absent_pct', label: 'Absent', color: 2 }]} format={(v) => `${v.toFixed(1)}%`} height={190} /></CardBody>
                </Card>
                <Card>
                  <CardHeader title="Which shifts lose people, and when" subtitle="Absence rate by weekday and shift" />
                  <CardBody>
                    <Heatmap
                      columns={Object.keys(d.absenteeism_heat[0]?.values ?? {})}
                      rows={d.absenteeism_heat.map((r) => ({ label: r.weekday, values: Object.values(r.values) }))}
                      color={(v) => badHigh(v, 0, 25)}
                      format={(v) => `${v.toFixed(0)}%`}
                      cell={58}
                      labelWidth={40}
                      showValues
                    />
                  </CardBody>
                </Card>
              </div>
              <div className="grid gap-4 xl:grid-cols-2">
                <Card>
                  <CardHeader title="Skills cover" subtitle="Weavers qualified on each loom type, per shift. Thin cover means one absence can idle a bank." />
                  <div className="space-y-3 px-5 pb-4">
                    {d.skills.map((s) => (
                      <div key={s.skill}>
                        <div className="mb-1 flex items-center justify-between text-sm"><span className="font-medium text-ink">{s.skill}</span>{s.thin && <Pill tone="warn">thin in one shift</Pill>}</div>
                        <div className="grid grid-cols-3 gap-2">
                          {Object.entries(s.per_shift).map(([sh, n]) => (
                            <div key={sh} className={cn('rounded-lg px-3 py-2 text-center', n < 4 ? 'bg-warn-soft text-warn' : 'bg-subtle text-ink')}><div className="num text-lg font-semibold">{n}</div><div className="text-[11px] opacity-80">{sh}</div></div>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                </Card>
                <Card>
                  <CardHeader title="Where a little support would help" subtitle={<span className="inline-flex items-center gap-1.5"><AiBadge /> Only where stops are clearly above what anyone gets on the same looms</span>} />
                  <div className="space-y-2 px-5 pb-4">
                    {d.coaching.length === 0 && <p className="py-4 text-sm text-ink-3">No one stands out once the looms they ran are allowed for.</p>}
                    {d.coaching.map((c) => (
                      <button key={c.code + c.topic} onClick={() => setOpen(c.code)} className="block w-full rounded-xl border border-line/80 p-3 text-left hover:bg-subtle">
                        <div className="flex items-center justify-between text-sm"><b className="text-ink">{c.name}</b><span className="text-xs text-ink-3">{c.shift} · {c.grade} · {c.experience_years} yrs</span></div>
                        <div className="mt-1 text-xs text-ink-2">{c.observed}</div>
                        <div className="mt-1 text-xs text-ink-3">{c.suggestion}</div>
                      </button>
                    ))}
                  </div>
                </Card>
              </div>
              <Section title="Employee directory" hint={`${rows.length} people`}>
                <div className="flex flex-wrap items-center gap-2">
                  <Segmented value={role} onChange={setRole} ariaLabel="Role" options={[{ value: 'ALL', label: 'Everyone' }, ...Object.entries(ROLE).map(([v, l]) => ({ value: v, label: l + 's' }))]} />
                </div>
                <Card>
                  <DataTable
                    rows={rows}
                    rowKey={(r) => r.code}
                    onRowClick={(r) => setOpen(r.code)}
                    searchable={(r) => `${r.name} ${r.code} ${r.designation} ${r.shift} ${r.skills.join(' ')}`}
                    searchPlaceholder="Search name, code, skill, shift"
                    exportName="workforce"
                    columns={[
                      { key: 'n', header: 'Name', value: (r) => r.name ?? r.code, render: (r) => <div><div className="font-medium text-ink">{r.name}</div><div className="text-xs text-ink-3">{r.code} · {r.designation}</div></div> },
                      { key: 's', header: 'Shift', value: (r) => r.shift ?? '', render: (r) => r.shift, hideBelow: 'md' },
                      { key: 'g', header: 'Grade', value: (r) => r.grade ?? '', render: (r) => r.grade, hideBelow: 'md' },
                      { key: 'x', header: 'Experience', value: (r) => r.experience_years, render: (r) => (r.experience_years != null ? `${r.experience_years} yrs` : '—'), align: 'right', hideBelow: 'lg' },
                      { key: 'k', header: 'Skills', value: (r) => r.skills.join(','), render: (r) => <span className="text-ink-2">{r.skills.join(', ')}</span>, hideBelow: 'lg' },
                      { key: 'a', header: 'Attendance', value: (r) => r.attendance_pct, render: (r) => (r.attendance_pct == null ? '—' : <span className={cn(r.attendance_pct < 90 && 'font-semibold text-bad')}>{r.attendance_pct}%</span>), align: 'right' },
                      { key: 'e', header: 'Loom efficiency', value: (r) => r.efficiency_pct ?? null, render: (r) => (r.efficiency_pct != null ? `${r.efficiency_pct}%` : '—'), align: 'right', hideBelow: 'md' },
                    ]}
                  />
                </Card>
              </Section>
              <p className="text-xs text-ink-3">{d.notes.join(' ')}</p>
              <Drawer open={!!person} onClose={() => setOpen(null)} title={person?.name ?? ''} subtitle={person ? `${person.designation} · ${person.code}` : ''}>
                {person && <Profile p={person} />}
              </Drawer>
            </>
          );
        }}
      </Load>
    </>
  );
};

const Row: React.FC<{ k: string; v: React.ReactNode }> = ({ k, v }) => (
  <div className="flex items-baseline justify-between gap-3 border-b border-line/60 py-2 text-sm last:border-0"><span className="text-ink-3">{k}</span><span className="text-right font-medium text-ink">{v ?? '—'}</span></div>
);

const Profile: React.FC<{ p: DirectoryRow }> = ({ p }) => (
  <div className="space-y-5">
    <div className="rounded-xl border border-line/80 px-4">
      <Row k="Department" v={p.department} />
      <Row k="Shift" v={p.shift} />
      <Row k="Grade" v={p.grade} />
      <Row k="Contract" v={p.contract === 'PERMANENT' ? 'Permanent' : 'Contract'} />
      <Row k="Joined" v={p.joined_on ? shortDate(p.joined_on) : null} />
      <Row k="Experience" v={p.experience_years != null ? `${p.experience_years} years` : null} />
      <Row k="Skills" v={p.skills.join(', ')} />
      {p.phone && <Row k="Phone" v={<span className="inline-flex items-center gap-1"><Phone className="size-3.5" />{p.phone}</span>} />}
    </div>
    <div>
      <h3 className="mb-2 text-sm font-semibold text-ink">Attendance, last 14 days</h3>
      <div className="grid grid-cols-3 gap-2 text-center">
        <div className="rounded-xl bg-subtle py-3"><div className="num text-xl font-semibold">{p.attendance_pct ?? '—'}{p.attendance_pct != null && '%'}</div><div className="text-[11px] text-ink-3">present</div></div>
        <div className="rounded-xl bg-subtle py-3"><div className="num text-xl font-semibold">{p.absent_days}</div><div className="text-[11px] text-ink-3">days off</div></div>
        <div className="rounded-xl bg-subtle py-3"><div className="num text-xl font-semibold">{p.days_tracked}</div><div className="text-[11px] text-ink-3">shifts rostered</div></div>
      </div>
    </div>
    {p.efficiency_pct != null && (
      <div>
        <h3 className="mb-2 text-sm font-semibold text-ink">The looms they ran, last 14 days</h3>
        <div className="grid grid-cols-2 gap-2 text-center">
          <div className="rounded-xl bg-subtle py-3"><div className="num text-xl font-semibold">{p.efficiency_pct}%</div><div className="text-[11px] text-ink-3">efficiency ({p.vs_floor_pts != null && p.vs_floor_pts >= 0 ? '+' : ''}{p.vs_floor_pts} vs floor)</div></div>
          <div className="rounded-xl bg-subtle py-3"><div className="num text-xl font-semibold">{num(p.meters_per_shift ?? 0)} m</div><div className="text-[11px] text-ink-3">per shift</div></div>
          <div className="rounded-xl bg-subtle py-3"><div className="num text-xl font-semibold">{p.warp_stops_per_100k}</div><div className="text-[11px] text-ink-3">warp stops / 100k picks</div></div>
          <div className="rounded-xl bg-subtle py-3"><div className="num text-xl font-semibold">{p.weft_stops_per_100k}</div><div className="text-[11px] text-ink-3">weft stops / 100k picks</div></div>
        </div>
        <p className="mt-2 text-xs text-ink-3">Looms: {p.looms?.join(', ')}. These figures describe the looms, which differ in age, style and condition. Use them to start a conversation, not to judge.</p>
      </div>
    )}
  </div>
);
