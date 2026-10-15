import React from 'react';
import { LayoutGrid, Table2 } from 'lucide-react';
import { useParam } from '../../app/state';
import { cn, inrFromLakhs, meters, minutes, num, pct } from '../../lib/format';
import { Card, CardHeader, Kpi, KpiGrid, Meter, Notice, Segmented, Select, StatusPill } from '../../design/ui';
import { DataTable } from '../../design/DataTable';
import { Drawer } from '../../design/Drawer';
import { TrendChart } from '../../design/charts/Charts';
import type { WeavingLoom, WeavingModuleData } from '../../types/weaving';
import { effTone, sevTone, WeavingPage } from './shared';

const tileClass = (l: WeavingLoom) => {
  if (l.status === 'STOPPED') return 'border-bad/50 bg-bad-soft';
  if (l.status === 'IDLE') return 'border-line bg-muted';
  if (l.health === 'CRITICAL') return 'border-bad/50 bg-bad-soft';
  if (l.health === 'ATTENTION') return 'border-warn/50 bg-warn-soft';
  return 'border-ok/30 bg-ok-soft';
};

const statusWord = (l: WeavingLoom) =>
  l.status === 'STOPPED' ? 'Stopped' : l.status === 'IDLE' ? 'Idle' : l.health === 'CRITICAL' ? 'Running · critical' : l.health === 'ATTENTION' ? 'Running · watch' : 'Running';

export const LoomsPage: React.FC = () => (
  <WeavingPage description="Every loom with its live status and its result for the selected period">
    {(d) => <LoomsBody d={d} />}
  </WeavingPage>
);

const LoomsBody: React.FC<{ d: WeavingModuleData }> = ({ d }) => {
  const [selected, setSelected] = useParam('loom', '');
  const [type, setType] = useParam('type', 'ALL');
  const [status, setStatus] = useParam('show', 'ALL');
  const [mode, setMode] = useParam('mode', 'grid');
  const rows = d.looms.filter(
    (l) =>
      (type === 'ALL' || l.loom_type === type) &&
      (status === 'ALL' || (status === 'ATTENTION' ? l.health !== 'NORMAL' || l.status === 'STOPPED' : l.status === status)),
  );
  const loom = d.looms.find((l) => l.loom_id === selected);
  const k = d.kpis;
  return (
    <>
      <KpiGrid>
        <Kpi label="Running" value={num(k.looms_running)} status="ok" />
        <Kpi label="Stopped" value={num(k.looms_stopped)} status={k.looms_stopped ? 'bad' : 'ok'} />
        <Kpi label="Idle" value={num(k.looms_idle)} />
        <Kpi label="Need attention" value={num(d.looms.filter((l) => l.health !== 'NORMAL').length)} hint={`for ${d.period_label.toLowerCase()}`} status="warn" />
        <Kpi label="Floor efficiency" value={pct(k.efficiency_pct)} status={effTone(k.efficiency_pct)} />
        <Kpi label="Looms" value={num(k.looms_total)} hint="36 Airjet · 12 Sulzer" />
      </KpiGrid>

      <Card>
        <CardHeader
          title="Loom floor"
          subtitle="Select a loom for its trend, cause and who is on it. Status is live; efficiency is for the selected period."
          actions={
            <>
              <Select
                aria-label="Loom type"
                value={type}
                onChange={(e) => setType(e.target.value)}
                options={[
                  { value: 'ALL', label: 'All types' },
                  { value: 'Airjet', label: 'Airjet' },
                  { value: 'Sulzer', label: 'Sulzer' },
                ]}
              />
              <Select
                aria-label="Show"
                value={status}
                onChange={(e) => setStatus(e.target.value)}
                options={[
                  { value: 'ALL', label: 'All looms' },
                  { value: 'ATTENTION', label: 'Needs attention' },
                  { value: 'STOPPED', label: 'Stopped' },
                  { value: 'IDLE', label: 'Idle' },
                  { value: 'RUNNING', label: 'Running' },
                ]}
              />
              <Segmented
                size="sm"
                ariaLabel="Layout"
                value={mode}
                onChange={setMode}
                options={[
                  { value: 'grid', label: <LayoutGrid className="size-3.5" aria-label="Grid" /> },
                  { value: 'table', label: <Table2 className="size-3.5" aria-label="Table" /> },
                ]}
              />
            </>
          }
        />
        {mode === 'table' ? (
          <DataTable<WeavingLoom>
            rows={rows}
            rowKey={(r) => r.loom_id}
            selectedKey={selected || null}
            onRowClick={(r) => setSelected(r.loom_id)}
            searchable={(r) => `${r.loom_id} ${r.style} ${r.main_issue} ${r.weaver}`}
            searchPlaceholder="Search loom, style or issue"
            exportName="weaving-looms"
            initialSort={{ key: 'loss', dir: 'desc' }}
            columns={[
              { key: 'id', header: 'Loom', value: (r) => r.loom_id, render: (r) => <div><div className="font-medium">{r.loom_id}</div><div className="text-xs text-ink-3">{r.loom_type} · {r.style}</div></div> },
              { key: 'st', header: 'Status', value: (r) => r.status, render: (r) => <StatusPill tone={r.status === 'STOPPED' ? 'bad' : r.status === 'IDLE' ? 'neutral' : sevTone(r.health)} label={statusWord(r)} /> },
              {
                key: 'eff',
                header: 'Efficiency',
                value: (r) => r.efficiency_pct,
                render: (r) => (
                  <div className="flex w-32 items-center gap-2">
                    <Meter value={r.efficiency_pct} max={100} tone={effTone(r.efficiency_pct, r.loom_type)} />
                    <span className="num w-11 text-right text-xs">{pct(r.efficiency_pct)}</span>
                  </div>
                ),
              },
              { key: 'a', header: 'Output', align: 'right', hideBelow: 'lg', value: (r) => r.actual_m, render: (r) => meters(r.actual_m) },
              { key: 'g', header: 'First grade', align: 'right', hideBelow: 'md', value: (r) => r.grade_a_pct, render: (r) => pct(r.grade_a_pct) },
              { key: 'i', header: 'Main issue', hideBelow: 'md', value: (r) => r.main_issue, render: (r) => r.main_issue },
              { key: 'loss', header: 'Margin lost', align: 'right', value: (r) => r.loss_lakhs, render: (r) => inrFromLakhs(r.loss_lakhs) },
            ]}
          />
        ) : (
          <div className="px-5 pb-5">
            <div className="grid grid-cols-3 gap-2 sm:grid-cols-4 md:grid-cols-6 xl:grid-cols-8">
              {rows.map((l) => (
                <button
                  key={l.loom_id}
                  onClick={() => setSelected(l.loom_id)}
                  className={cn('rounded-lg border p-2.5 text-left transition-shadow hover:shadow-md', tileClass(l), selected === l.loom_id && 'ring-2 ring-accent')}
                  aria-label={`${l.loom_id}, ${statusWord(l)}, efficiency ${pct(l.efficiency_pct)}`}
                >
                  <div className="text-sm font-semibold text-ink">{l.loom_id}</div>
                  <div className="num text-xs text-ink-2">{pct(l.efficiency_pct, 0)}</div>
                  <div className="mt-0.5 truncate text-2xs text-ink-2">{l.status === 'STOPPED' ? `${l.stop_reason} · ${minutes(l.stopped_since_min)}` : statusWord(l)}</div>
                </button>
              ))}
            </div>
            {rows.length === 0 && <p className="py-8 text-center text-sm text-ink-3">No looms match this filter.</p>}
            <p className="mt-3 text-xs text-ink-3">Colour is always paired with a word on the tile: green is normal, amber is watch, red is critical or stopped, grey is idle.</p>
          </div>
        )}
      </Card>

      <Drawer open={!!loom} onClose={() => setSelected(null)} title={loom ? `Loom ${loom.loom_id}` : ''} subtitle={loom ? `${loom.loom_type} · style ${loom.style}` : ''}>
        {loom && <LoomDetail l={loom} d={d} />}
      </Drawer>
    </>
  );
};

const LoomDetail: React.FC<{ l: WeavingLoom; d: WeavingModuleData }> = ({ l, d }) => {
  const trend = l.trend.map((v, i) => ({ day: `D${i + 1 - l.trend.length}`, efficiency: v }));
  const advice = d.stop_causes.find((c) => c.cause === l.main_issue)?.advice;
  const style = d.styles.find((s) => s.style === l.style);
  return (
    <div className="space-y-4">
      {l.status === 'STOPPED' && (
        <Notice tone="bad">
          Stopped for {minutes(l.stopped_since_min)}: {l.stop_reason}. Fitter on duty: {l.fitter}.
        </Notice>
      )}
      <div className="grid grid-cols-2 gap-3">
        <Kpi label="Efficiency" value={pct(l.efficiency_pct)} status={effTone(l.efficiency_pct, l.loom_type)} hint="target 92%" />
        <Kpi label="Margin lost" value={inrFromLakhs(l.loss_lakhs)} hint={`${num(l.loss_m)} m short`} status={l.loss_lakhs > 0.3 ? 'warn' : undefined} />
        <Kpi label="Output" value={meters(l.actual_m)} hint={`target ${meters(l.target_m)}`} />
        <Kpi label="First grade" value={pct(l.grade_a_pct)} hint={`${l.defects_per_100m} defects / 100 m`} status={l.defects_per_100m > 3.2 ? 'warn' : undefined} />
      </div>
      <div>
        <h3 className="mb-1 text-xs font-medium text-ink-3">Efficiency, last 14 days</h3>
        <TrendChart data={trend} xKey="day" format={(v) => `${v.toFixed(1)}%`} series={[{ key: 'efficiency', label: 'Efficiency', color: 0 }]} reference={{ value: 92, label: 'Target' }} height={200} />
      </div>
      <dl className="grid grid-cols-2 gap-x-4 gap-y-2 text-sm">
        <dt className="text-ink-3">Main issue</dt>
        <dd className="text-ink">{l.main_issue}</dd>
        <dt className="text-ink-3">Speed</dt>
        <dd className="num text-ink">{l.rpm ? `${l.rpm} rpm` : 'Not running'}</dd>
        <dt className="text-ink-3">Weaver</dt>
        <dd className="text-ink">{l.weaver}</dd>
        <dt className="text-ink-3">Fitter</dt>
        <dd className="text-ink">{l.fitter}</dd>
        <dt className="text-ink-3">Style</dt>
        <dd className="text-ink">{style ? `${style.style} · ${style.fabric}` : l.style}</dd>
      </dl>
      {advice && l.health !== 'NORMAL' && (
        <Notice tone="warn">
          <b>What to do:</b> {advice}
        </Notice>
      )}
    </div>
  );
};
