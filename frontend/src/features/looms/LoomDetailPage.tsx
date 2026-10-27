import React, { useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { ArrowLeft, ClipboardPlus, Wrench } from 'lucide-react';
import { useLoom } from '../../api/mill';
import { QueryView } from '../../design/QueryView';
import { ChartPanel } from '../../design/ChartPanel';
import { TrendChart, ColumnChart, RankedBars } from '../../design/charts/Charts';
import { DataTable, type Column } from '../../design/DataTable';
import { Badge, Button, Card, CardBody, CardHeader, EmptyState, Kpi, KpiGrid, Notice, StatusPill } from '../../design/ui';
import { pct } from '../../lib/format';
import { FilterBar, useFilters } from '../common/filters';
import { FindingCard } from '../common/FindingCard';
import { BasisBadge, LiveState, PageTitle, SeverityPill, SourceBadge, fmt, periodText } from '../common/parts';
import { TaskDrawer, type TaskDraft } from '../common/TaskDrawer';
import { WorkOrderDrawer } from '../maintenance/WorkOrderDrawer';
import type { LoomDetail, ProductionRecord } from '../../types/mill';

const recordCols: Column<ProductionRecord>[] = [
  { key: 'd', header: 'Date', render: (r) => fmt.date(r.prod_date), value: (r) => `${r.prod_date}${r.shift}` },
  { key: 's', header: 'Shift', render: (r) => r.shift, value: (r) => r.shift },
  { key: 'src', header: 'Source', render: (r) => <SourceBadge source={r.source_kind} />, value: (r) => r.source_kind, hideBelow: 'md' },
  { key: 'style', header: 'Style', render: (r) => r.style_code ?? '—', value: (r) => r.style_code, hideBelow: 'lg' },
  { key: 'rpm', header: 'RPM', align: 'right', render: (r) => fmt.n(r.rpm), value: (r) => r.rpm },
  { key: 'eff', header: 'Efficiency', align: 'right', render: (r) => pct(r.efficiency_pct), value: (r) => r.efficiency_pct },
  { key: 'kp', header: 'Kilopicks', align: 'right', render: (r) => fmt.n(r.kilopicks, 1), value: (r) => r.kilopicks },
  { key: 'm', header: 'Meters', align: 'right', render: (r) => fmt.n(r.meters, 1), value: (r) => r.meters },
  { key: 'w', header: 'Warp', align: 'right', render: (r) => fmt.n(r.warp_stops), value: (r) => r.warp_stops },
  { key: 'f', header: 'Weft', align: 'right', render: (r) => fmt.n(r.weft_stops), value: (r) => r.weft_stops },
  { key: 'run', header: 'Run / stop min', align: 'right', render: (r) => (r.run_min != null ? `${fmt.n(r.run_min)} / ${fmt.n(r.stop_min)}` : '—'), value: (r) => r.run_min, hideBelow: 'xl' },
  { key: 'b', header: 'Import', align: 'right', render: (r) => (r.batch_id ? <Link to={`/imports?id=${r.batch_id}`} className="text-accent hover:underline">#{r.batch_id}</Link> : '—'), value: (r) => r.batch_id, hideBelow: 'xl' },
];

export const LoomDetailPage: React.FC = () => {
  const { id } = useParams();
  const filters = useFilters();
  const q = useLoom(Number(id), filters);
  return (
    <>
      <Link to="/looms" className="mb-3 inline-flex items-center gap-1 text-xs text-ink-3 hover:text-ink"><ArrowLeft className="size-3.5" /> Loom floor</Link>
      <QueryView query={q}>{(d) => <Body d={d} />}</QueryView>
    </>
  );
};

const Body: React.FC<{ d: LoomDetail }> = ({ d }) => {
  const [task, setTask] = useState<TaskDraft | null>(null);
  const [wo, setWo] = useState(false);
  const l = d.loom;
  const k = d.kpis;
  const shifts = Object.entries(d.by_shift).sort();
  return (
    <div className="space-y-5">
      <PageTitle
        title={`${l.code} · ${l.manufacturer}${l.model ? ` ${l.model}` : ''}`}
        subtitle={<>Loom {l.loom_no}{l.width_cm ? ` · ${l.width_cm} cm` : ''}{l.style ? ` · style ${l.style}` : ''}{l.style_description ? ` (${l.style_description})` : ''} · {periodText(d.period)}</>}
        actions={
          <>
            <FilterBar show={['shift', 'source']} />
            <Button icon={<ClipboardPlus className="size-4" />} onClick={() => setTask({ title: `${l.code}: `, loom_id: l.id })}>Task</Button>
            <Button icon={<Wrench className="size-4" />} onClick={() => setWo(true)}>Work order</Button>
          </>
        }
      />
      <div className="flex flex-wrap items-center gap-3 text-xs text-ink-3">
        <LiveState state={d.live_state} origin={d.telemetry[0]?.origin} machineState={d.telemetry[0]?.state} />
        {d.connection?.last_success_at && <span>Last reading {fmt.dateTime(d.connection.last_success_at)}</span>}
        {d.connection?.last_error && <span className="text-bad">{d.connection.last_error}</span>}
        {Object.keys(d.period.sources).map((s) => <SourceBadge key={s} source={s} />)}
        {typeof l.attributes.toyota_panel_factor === 'number' && l.attributes.toyota_panel_factor !== 1 && (
          <Badge tone="warn">Monitoring counts ×{String(l.attributes.toyota_panel_factor)} in the mill report</Badge>
        )}
      </div>
      {d.missing_note && <Notice tone="info">{d.missing_note}</Notice>}
      {Object.keys(d.period.sources).length > 1 && (
        <Notice tone="warn">
          This period mixes the mill report and a machine export. Efficiency compares fine; meters, kilopicks and stop rates should be read within one
          source (use the source filter){typeof l.attributes.toyota_panel_factor === 'number' && l.attributes.toyota_panel_factor !== 1 ? ': the mill report counts this loom ×2' : ''}.
        </Notice>
      )}
      {d.records.length === 0 && <Notice tone="info">No records for this loom in the selected period.</Notice>}

      <KpiGrid>
        <Kpi label="Efficiency" value={pct(k.efficiency_pct)} hint={d.peers?.valid ? `Peer median ${pct(d.peers.median_efficiency_pct)} · rank ${d.peers.rank} of ${d.peers.size}` : d.peers?.note ?? '—'}
             status={d.peers?.valid && k.efficiency_pct != null && d.peers.median_efficiency_pct != null ? (k.efficiency_pct < d.peers.median_efficiency_pct - 3 ? 'warn' : 'ok') : undefined} />
        <Kpi label="Meters" value={fmt.n(k.meters)} hint={`${fmt.n(k.meters_per_loom_shift, 1)} m per shift`} />
        <Kpi label="Kilopicks" value={fmt.n(k.kilopicks)} hint={`${k.loom_shifts} shifts`} />
        <Kpi label="Warp stops" value={fmt.rate(k.warp_stops_cmpx)} hint={`per 100k picks · ${fmt.n(k.warp_stops)} total`} />
        <Kpi label="Weft stops" value={fmt.rate(k.weft_stops_cmpx)} hint={`per 100k picks · ${fmt.n(k.weft_stops)} total`} />
        <Kpi label="Open alerts" value={d.alerts.filter((a) => a.status !== 'RESOLVED').length} hint={`${d.work_orders.filter((w) => !['COMPLETED', 'CANCELLED'].includes(w.status)).length} open work orders`} />
      </KpiGrid>

      <div className="grid gap-4 xl:grid-cols-3">
        <ChartPanel className="xl:col-span-2" title="Daily efficiency and output" subtitle="Each day's time-weighted efficiency"
          chart={d.daily.length ? <TrendChart data={d.daily} xKey="date" series={[{ key: 'efficiency_pct', label: 'Efficiency', color: 0 }]} format={(v) => pct(v)} area height={220}
            reference={d.peers?.valid && d.peers.median_efficiency_pct != null ? { value: d.peers.median_efficiency_pct, label: 'peer median' } : undefined} /> : <EmptyState title="No data" />}
          rows={d.daily} rowKey={(r) => r.date} exportName={`${l.code}-daily`}
          columns={[
            { key: 'd', header: 'Date', render: (r) => fmt.date(r.date), value: (r) => r.date },
            { key: 'e', header: 'Efficiency', align: 'right', render: (r) => pct(r.efficiency_pct), value: (r) => r.efficiency_pct },
            { key: 'm', header: 'Meters', align: 'right', render: (r) => fmt.n(r.meters, 1), value: (r) => r.meters },
            { key: 'w', header: 'Warp', align: 'right', render: (r) => fmt.n(r.warp_stops), value: (r) => r.warp_stops },
            { key: 'f', header: 'Weft', align: 'right', render: (r) => fmt.n(r.weft_stops), value: (r) => r.weft_stops },
          ]} />
        <Card>
          <CardHeader title="By shift" subtitle="Same loom, same period" />
          <CardBody>
            {shifts.length ? <ColumnChart data={shifts.map(([s, v]) => ({ shift: s, eff: v.efficiency_pct }))} xKey="shift" series={[{ key: 'eff', label: 'Efficiency', color: 1 }]} format={(v) => pct(v)} height={180} /> : <EmptyState title="No data" />}
            <ul className="mt-3 space-y-1 text-xs">
              {shifts.map(([s, v]) => <li key={s} className="flex justify-between"><span>Shift {s}</span><span className="num">{pct(v.efficiency_pct)} · {fmt.n(v.meters)} m · warp {fmt.rate(v.warp_stops_cmpx)} · weft {fmt.rate(v.weft_stops_cmpx)}</span></li>)}
            </ul>
          </CardBody>
        </Card>
      </div>

      <div className="grid gap-4 xl:grid-cols-2">
        <Card>
          <CardHeader title="Peers" subtitle={d.peers ? `Same category, width (${d.peers.cohort.width_cm ?? '?'} cm), style ${d.peers.cohort.style ?? '?'} and source` : 'No records'} />
          <CardBody>
            {d.peers?.note && <Notice tone="info">{d.peers.note}</Notice>}
            {d.peers && (
              <DataTable dense rows={d.peers.peers} rowKey={(p) => String(p.loom_id)}
                columns={[
                  { key: 'c', header: 'Loom', render: (p) => (p.loom_id === l.id ? <strong>{p.loom_code}</strong> : <Link to={`/looms/${p.loom_id}`} className="hover:text-accent">{p.loom_code}</Link>), value: (p) => p.loom_code },
                  { key: 'e', header: 'Efficiency', align: 'right', render: (p) => pct(p.efficiency_pct), value: (p) => p.efficiency_pct },
                  { key: 'm', header: 'Meters', align: 'right', render: (p) => fmt.n(p.meters), value: (p) => p.meters },
                  { key: 'w', header: 'Warp /100k', align: 'right', render: (p) => fmt.rate(p.warp_stops_cmpx), value: (p) => p.warp_stops_cmpx },
                  { key: 'f', header: 'Weft /100k', align: 'right', render: (p) => fmt.rate(p.weft_stops_cmpx), value: (p) => p.weft_stops_cmpx },
                ]} />
            )}
          </CardBody>
        </Card>
        <Card>
          <CardHeader title="Stops by sensor" subtitle="Counts from the Tsudakoma export (the only source with a per-sensor breakdown)" />
          <CardBody>
            {d.stop_causes.length ? <RankedBars items={d.stop_causes.slice(0, 10).map((c) => ({ label: c.cause, value: c.count }))} format={(v) => fmt.n(v)} /> : <EmptyState title="No per-sensor data" description={d.stop_causes_note ?? undefined} />}
          </CardBody>
        </Card>
      </div>

      <Card>
        <CardHeader title="Findings, anomalies and next steps" subtitle="Unusual readings are not diagnoses; recommendations are for people to decide." />
        <CardBody className="space-y-4">
          {d.findings.length > 0 && <ul className="grid gap-3 lg:grid-cols-2">{d.findings.map((f) => <FindingCard key={f.id} f={f} onTask={(x) => setTask({ title: x.title, description: x.next_step, loom_id: l.id })} />)}</ul>}
          {d.anomalies.length > 0 && (
            <div>
              <h3 className="mb-2 text-xs font-semibold text-ink-2">Statistically unusual shifts <BasisBadge basis="STATISTICAL" /></h3>
              <ul className="space-y-1 text-xs">
                {d.anomalies.map((a) => (
                  <li key={`${a.prod_date}${a.shift}`} className="num">{fmt.date(a.prod_date)} {a.shift}: {pct(a.efficiency_pct)} vs median {pct(a.baseline_median)} of {a.points} earlier shifts (robust z {a.robust_z})</li>
                ))}
              </ul>
            </div>
          )}
          <ul className="space-y-1.5">
            {d.recommendations.map((r, i) => (
              <li key={i} className="flex items-start gap-2 text-sm"><BasisBadge basis={r.basis} /><span><span className="text-ink">{r.action}</span> <span className="text-xs text-ink-3">({r.why})</span></span></li>
            ))}
          </ul>
        </CardBody>
      </Card>

      <div className="grid gap-4 xl:grid-cols-3">
        <Card>
          <CardHeader title="Alerts" />
          <CardBody>
            {d.alerts.length === 0 ? <EmptyState title="No alerts" /> : (
              <ul className="space-y-2 text-sm">{d.alerts.map((a) => (
                <li key={a.id} className="flex items-center gap-2"><SeverityPill severity={a.severity} /><Link to={`/alerts?id=${a.id}`} className="truncate hover:text-accent">{a.title}</Link><StatusPill status={a.status} /></li>
              ))}</ul>
            )}
          </CardBody>
        </Card>
        <Card>
          <CardHeader title="Tasks" />
          <CardBody>
            {d.tasks.length === 0 ? <EmptyState title="No tasks" /> : (
              <ul className="space-y-2 text-sm">{d.tasks.map((t) => <li key={t.id} className="flex items-center gap-2"><Link to={`/tasks?id=${t.id}`} className="truncate hover:text-accent">{t.title}</Link><StatusPill status={t.status} /></li>)}</ul>
            )}
          </CardBody>
        </Card>
        <Card>
          <CardHeader title="Maintenance and group history" />
          <CardBody className="space-y-3 text-sm">
            {d.work_orders.length === 0 ? <p className="text-xs text-ink-3">No work orders recorded.</p> : (
              <ul className="space-y-1">{d.work_orders.map((w) => <li key={w.id} className="flex justify-between gap-2"><span className="truncate">{w.kind.toLowerCase()}: {w.title}</span><StatusPill status={w.status} /></li>)}</ul>
            )}
            <ul className="space-y-1 text-xs text-ink-3">
              {d.group_history.length === 0 ? <li>Not assigned to a group.</li> : d.group_history.map((g, i) => <li key={i}>{g.group}: {fmt.date(g.valid_from)} – {g.valid_to ? fmt.date(g.valid_to) : 'now'}</li>)}
            </ul>
          </CardBody>
        </Card>
      </div>

      <Card>
        <CardHeader title="Shift records" subtitle="One row per loom-shift; the mill report is used where both sources exist (change with the source filter)" />
        <CardBody><DataTable rows={d.records} columns={recordCols} rowKey={(r) => String(r.id)} dense exportName={`${l.code}-records`} initialSort={{ key: 'd', dir: 'desc' }} /></CardBody>
      </Card>
      <TaskDrawer open={!!task} onClose={() => setTask(null)} draft={task ?? undefined} />
      <WorkOrderDrawer open={wo} onClose={() => setWo(false)} loomId={l.id} />
    </div>
  );
};
