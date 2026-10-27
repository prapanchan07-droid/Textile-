import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Users } from 'lucide-react';
import { useDashboard, useMillMutation, api } from '../../api/mill';
import { QueryView } from '../../design/QueryView';
import { ChartPanel } from '../../design/ChartPanel';
import { TrendChart, ColumnChart, type Series } from '../../design/charts/Charts';
import { DataTable, type Column } from '../../design/DataTable';
import { Button, Card, CardBody, CardHeader, EmptyState, Kpi, KpiGrid, Notice } from '../../design/ui';
import { FilterBar, useFilters } from '../common/filters';
import { FindingCard } from '../common/FindingCard';
import { FreshnessLine, NoData, PageTitle, SeverityPill, fmt } from '../common/parts';
import { TaskDrawer, type TaskDraft } from '../common/TaskDrawer';
import type { Dashboard, GroupRow, Kpis } from '../../types/mill';
import { meters, pct } from '../../lib/format';

const CAT_SERIES: Series[] = [
  { key: 'eff_TY', label: 'TY · Toyota', color: 0 },
  { key: 'eff_TS', label: 'TS · Tsudakoma', color: 1 },
  { key: 'eff_SZ', label: 'SZ · Sulzer', color: 2 },
];

const kpiCols: Column<[string, Kpis]>[] = [
  { key: 'k', header: '', render: ([k]) => <span className="font-medium text-ink">{k}</span>, value: ([k]) => k },
  { key: 'looms', header: 'Looms', align: 'right', render: ([, v]) => v.looms, value: ([, v]) => v.looms },
  { key: 'meters', header: 'Meters', align: 'right', render: ([, v]) => fmt.n(v.meters), value: ([, v]) => v.meters },
  { key: 'kp', header: 'Kilopicks', align: 'right', render: ([, v]) => fmt.n(v.kilopicks), value: ([, v]) => v.kilopicks, hideBelow: 'md' },
  { key: 'eff', header: 'Efficiency', align: 'right', render: ([, v]) => pct(v.efficiency_pct), value: ([, v]) => v.efficiency_pct },
  { key: 'warp', header: 'Warp /100k picks', align: 'right', render: ([, v]) => fmt.rate(v.warp_stops_cmpx), value: ([, v]) => v.warp_stops_cmpx },
  { key: 'weft', header: 'Weft /100k picks', align: 'right', render: ([, v]) => fmt.rate(v.weft_stops_cmpx), value: ([, v]) => v.weft_stops_cmpx },
  { key: 'mps', header: 'm / loom-shift', align: 'right', render: ([, v]) => fmt.n(v.meters_per_loom_shift, 1), value: ([, v]) => v.meters_per_loom_shift, hideBelow: 'lg' },
];

const groupCols: Column<GroupRow>[] = [
  { key: 'name', header: 'Group', render: (g) => <Link to={`/groups?id=${g.id}`} className="font-medium text-ink hover:text-accent">{g.name}</Link>, value: (g) => g.code },
  { key: 'leader', header: 'Leader', render: (g) => g.leader ?? '—', value: (g) => g.leader, hideBelow: 'md' },
  { key: 'looms', header: 'Looms', align: 'right', render: (g) => g.looms, value: (g) => g.looms },
  { key: 'meters', header: 'Meters', align: 'right', render: (g) => fmt.n(g.meters), value: (g) => g.meters },
  { key: 'eff', header: 'Efficiency', align: 'right', render: (g) => pct(g.efficiency_pct), value: (g) => g.efficiency_pct },
  { key: 'open', header: 'Open tasks', align: 'right', render: (g) => g.open_tasks, value: (g) => g.open_tasks },
  { key: 'blocked', header: 'Blocked', align: 'right', render: (g) => (g.blocked_tasks ? <span className="text-bad">{g.blocked_tasks}</span> : 0), value: (g) => g.blocked_tasks },
  { key: 'alerts', header: 'Open alerts', align: 'right', render: (g) => g.open_alerts, value: (g) => g.open_alerts },
];

export const CommandCenterPage: React.FC = () => {
  const filters = useFilters();
  const q = useDashboard(filters);
  const [draft, setDraft] = useState<TaskDraft | null>(null);
  return (
    <>
      <PageTitle title="Weaving command centre" subtitle="What is happening, what is going wrong, who needs to act and what to report." actions={<FilterBar show={['category', 'shift', 'source', 'group']} />} />
      <QueryView query={q}>{(d) => <Body d={d} onTask={setDraft} />}</QueryView>
      <TaskDrawer open={!!draft} onClose={() => setDraft(null)} draft={draft ?? undefined} />
    </>
  );
};

const Body: React.FC<{ d: Dashboard; onTask: (t: TaskDraft) => void }> = ({ d, onTask }) => {
  const navigate = useNavigate();
  const k = d.kpis;
  const bootstrap = useMillMutation(() => api.post('/mill/groups/bootstrap?count=11', {}));
  const alerts = (k.open_alerts.CRITICAL ?? 0) + (k.open_alerts.WARNING ?? 0) + (k.open_alerts.INFO ?? 0);
  const shiftEntries = Object.entries(d.by_shift).sort();
  return (
    <div className="space-y-5">
      <FreshnessLine freshness={d.freshness} period={d.period} />
      {k.loom_shifts === 0 && <NoData />}
      <KpiGrid>
        <Kpi label="Production" value={k.meters == null ? '—' : `${fmt.n(k.meters)} m`}
             hint={k.target_meters ? `${pct(((k.meters ?? 0) / k.target_meters) * 100, 0)} of ${meters(k.target_meters)} target` : 'No target configured'}
             status={k.target_meters && k.meters != null ? (k.meters >= k.target_meters ? 'ok' : 'warn') : undefined} onClick={() => navigate('/production')} />
        <Kpi label="Efficiency (time-weighted)" value={pct(k.efficiency_pct)}
             hint={shiftEntries.map(([s, v]) => `${s} ${pct(v.efficiency_pct, 1)}`).join(' · ') || '—'} onClick={() => navigate('/production')} />
        <Kpi label="Kilopicks" value={fmt.n(k.kilopicks)} hint={`${fmt.n(k.loom_shifts)} loom-shifts`} />
        <Kpi label="Warp / weft stops" value={`${fmt.rate(k.warp_stops_cmpx)} / ${fmt.rate(k.weft_stops_cmpx)}`}
             hint={`per 100k picks · ${fmt.n(k.warp_stops)} warp, ${fmt.n(k.weft_stops)} weft`} onClick={() => navigate('/compare')} />
        <Kpi label="Looms reporting" value={`${k.reporting_looms} / ${k.registered_looms}`}
             hint={k.not_reporting_looms.length ? `No records: ${k.not_reporting_looms.slice(0, 4).join(', ')}${k.not_reporting_looms.length > 4 ? '…' : ''}` : 'All registered looms reported'}
             status={k.not_reporting_looms.length ? 'warn' : 'ok'} onClick={() => navigate('/looms')} />
        <Kpi label="Open alerts · tasks" value={`${alerts} · ${k.open_tasks}`}
             hint={`${k.open_alerts.CRITICAL ?? 0} critical · ${k.overdue_tasks} overdue tasks · ${k.open_work_orders} work orders`}
             status={(k.open_alerts.CRITICAL ?? 0) > 0 || k.overdue_tasks > 0 ? 'bad' : alerts ? 'warn' : 'ok'} onClick={() => navigate('/alerts')} />
      </KpiGrid>

      <div className="grid gap-4 xl:grid-cols-3">
        <ChartPanel
          className="xl:col-span-2"
          title="Efficiency by day"
          subtitle="Time-weighted efficiency per machine category. Categories differ in machine type and width."
          chart={d.daily.length ? <TrendChart data={d.daily} xKey="date" series={CAT_SERIES.filter((s) => d.daily.some((x) => x[s.key] != null))} format={(v) => pct(v)} height={260} /> : <EmptyState title="No days in this period" />}
          rows={d.daily}
          rowKey={(r) => r.date}
          exportName="efficiency-by-day"
          columns={[
            { key: 'date', header: 'Date', render: (r) => fmt.date(r.date), value: (r) => r.date },
            ...CAT_SERIES.map((s) => ({ key: s.key, header: s.label, align: 'right' as const, render: (r: Dashboard['daily'][number]) => pct(r[s.key] as number | null), value: (r: Dashboard['daily'][number]) => r[s.key] as number | null })),
            { key: 'src', header: 'Source', render: (r) => r.sources.join(', ') },
          ]}
        />
        <Card>
          <CardHeader title="Needs attention" subtitle="Open alerts, most severe first" actions={<Link to="/alerts" className="text-xs text-accent hover:underline">All alerts</Link>} />
          <CardBody>
            {d.top_alerts.length === 0 ? (
              <EmptyState title="No open alerts" description="Rules are evaluated after every import." />
            ) : (
              <ul className="space-y-2">
                {d.top_alerts.map((a) => (
                  <li key={a.id} className="flex items-start gap-2 rounded-lg border border-line px-3 py-2">
                    <SeverityPill severity={a.severity} />
                    <div className="min-w-0 flex-1">
                      <Link to={`/alerts?id=${a.id}`} className="block truncate text-sm text-ink hover:text-accent">{a.title}</Link>
                      <p className="text-2xs text-ink-3">{a.period ?? ''} · {a.status.toLowerCase()}{a.escalation_level ? ` · escalated ×${a.escalation_level}` : ''}</p>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </CardBody>
        </Card>
      </div>

      <ChartPanel
        title="Production by day"
        subtitle="Meters woven per category (sum of loom-shifts with a meter value)"
        chart={<ColumnChart data={d.daily.map((x) => ({ ...x, day: x.date.slice(5) }))} xKey="day" series={[{ key: 'meters_TY', label: 'TY', color: 0 }, { key: 'meters_TS', label: 'TS', color: 1 }, { key: 'meters_SZ', label: 'SZ', color: 2 }].filter((s) => d.daily.some((x) => x[s.key] != null)) as Series[]} format={(v) => meters(v)} height={220} />}
        rows={d.daily}
        rowKey={(r) => r.date}
        exportName="meters-by-day"
        columns={[
          { key: 'date', header: 'Date', render: (r) => fmt.date(r.date), value: (r) => r.date },
          { key: 'm', header: 'Meters', align: 'right', render: (r) => fmt.n(r.meters), value: (r) => r.meters },
        ]}
      />

      <div className="grid gap-4 xl:grid-cols-2">
        <Card>
          <CardHeader title="By machine category" subtitle={d.comparability} />
          <CardBody><DataTable rows={Object.entries(d.by_category)} columns={kpiCols} rowKey={([c]) => c} dense exportName="by-category" /></CardBody>
        </Card>
        <Card>
          <CardHeader title="By shift" subtitle="A 06:00–14:00 · B 14:00–22:00 · C 22:00–06:00" />
          <CardBody><DataTable rows={shiftEntries} columns={kpiCols} rowKey={([s]) => s} dense exportName="by-shift" /></CardBody>
        </Card>
      </div>

      <Card>
        <CardHeader title="Where output is being lost" subtitle="Evidence-backed findings for the period. Causes are not guessed: each one says what to check." actions={<Link to="/compare" className="text-xs text-accent hover:underline">Compare looms</Link>} />
        <CardBody>
          {d.findings.length === 0 ? (
            <EmptyState title="No findings" description="Nothing stands out against peers, own history or other shifts for this selection." />
          ) : (
            <ul className="grid gap-3 lg:grid-cols-2">
              {d.findings.map((f) => (
                <FindingCard key={f.id} f={f} onTask={(x) => onTask({ title: x.title, description: `${x.implication}\n\nNext: ${x.next_step}`, loom_id: x.loom_id, priority: x.severity === 'CRITICAL' ? 'HIGH' : 'MEDIUM' })} />
              ))}
            </ul>
          )}
        </CardBody>
      </Card>

      <Card>
        <CardHeader title="Groups" subtitle="Production counts for a group only while a loom was assigned to it" actions={<Link to="/groups" className="text-xs text-accent hover:underline">Manage groups</Link>} />
        <CardBody>
          {d.groups.length === 0 ? (
            <EmptyState icon={<Users className="size-5" />} title="No groups set up yet"
              description="Create the mill's 11 groups, then assign looms and people from the Groups page."
              action={<Button variant="primary" loading={bootstrap.isPending} onClick={() => bootstrap.mutate(undefined)}>Create 11 groups</Button>} />
          ) : (
            <DataTable rows={d.groups} columns={groupCols} rowKey={(g) => String(g.id)} dense exportName="groups" />
          )}
          {bootstrap.isError && <Notice tone="bad">{(bootstrap.error as Error).message}</Notice>}
        </CardBody>
      </Card>
    </div>
  );
};
