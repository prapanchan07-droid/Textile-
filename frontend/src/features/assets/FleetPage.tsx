import React from 'react';
import { Wrench } from 'lucide-react';
import { useMachines } from '../../api/queries';
import { useParam, usePeriod } from '../../app/state';
import { kg, kgExact, minutes, num, pct } from '../../lib/format';
import type { MachinePerformanceItem, MachinesModuleData } from '../../types/machines';
import { QueryView } from '../../design/QueryView';
import { Card, CardBody, CardHeader, Kpi, KpiGrid, Meter, Select, StatusPill, toneOf } from '../../design/ui';
import { Clip, DataTable } from '../../design/DataTable';
import { RankedBars, SplitBar } from '../../design/charts/Charts';
import { AssetsHeader } from './AssetsLayout';
import { MachineDrawer } from './MachineDrawer';

export const FleetPage: React.FC = () => {
  const [period] = usePeriod();
  const [type, setType] = useParam('type', 'ALL');
  const [machine, setMachine] = useParam('machine');
  const query = useMachines(period, type);

  return (
    <>
      <AssetsHeader />
      <QueryView query={query}>
        {(d) => <FleetBody data={d} type={type} onType={setType} selected={machine} onSelect={setMachine} />}
      </QueryView>
      <MachineDrawer machineId={machine || null} onClose={() => setMachine(null)} />
    </>
  );
};

const FleetBody: React.FC<{
  data: MachinesModuleData;
  type: string;
  onType: (t: string) => void;
  selected: string;
  onSelect: (id: string) => void;
}> = ({ data, type, onType, selected, onSelect }) => {
  const machines = data.all_machines;
  const critical = machines.filter((m) => m.status === 'CRITICAL').length;
  const attention = machines.filter((m) => m.status === 'ATTENTION').length;
  const totalLoss = machines.reduce((s, m) => s + m.loss_kg, 0);
  const avgEff = machines.length ? machines.reduce((s, m) => s + m.efficiency_pct, 0) / machines.length : 0;
  const dk = data.downtime_kpis;

  return (
    <div className="space-y-4">
      <KpiGrid>
        <Kpi
          label="Machines"
          value={num(machines.length)}
          hint={`${critical} critical · ${attention} attention`}
          status={critical ? 'bad' : attention ? 'warn' : 'ok'}
        />
        <Kpi label="Avg. efficiency" value={pct(avgEff)} hint="simple average" />
        <Kpi label="Production loss" value={kg(totalLoss)} />
        <Kpi label="Downtime" value={minutes(dk.total_downtime_min)} hint={`${num(dk.stoppage_count)} stoppages`} />
        <Kpi
          label="Unplanned downtime"
          value={minutes(dk.unplanned_downtime_min)}
          hint={dk.total_downtime_min ? `${Math.round((dk.unplanned_downtime_min / dk.total_downtime_min) * 100)}% of total` : undefined}
          status={dk.total_downtime_min && dk.unplanned_downtime_min / dk.total_downtime_min > 0.6 ? 'warn' : undefined}
        />
        <Kpi label="Planned downtime" value={minutes(dk.planned_downtime_min)} />
      </KpiGrid>

      <Card>
        <CardHeader title="Machine register" subtitle="Select a machine for trend, maintenance and quality details" />
        <DataTable<MachinePerformanceItem>
          rows={machines}
          rowKey={(r) => r.machine_id}
          selectedKey={selected || null}
          onRowClick={(r) => onSelect(r.machine_id)}
          searchable={(r) => `${r.machine_id} ${r.machine_type} ${r.main_issue}`}
          searchPlaceholder="Search machine or issue"
          exportName="machine-register"
          initialSort={{ key: 'loss', dir: 'desc' }}
          toolbar={
            <Select
              aria-label="Machine type"
              value={type}
              onChange={(e) => onType(e.target.value)}
              options={data.machine_types.map((t) => ({
                value: t.toUpperCase() === 'ALL' ? 'ALL' : t,
                label: t.toUpperCase() === 'ALL' ? 'All types' : t,
              }))}
            />
          }
          columns={[
            {
              key: 'id',
              header: 'Machine',
              value: (r) => r.machine_id,
              render: (r) => (
                <div>
                  <div className="font-medium">{r.machine_id}</div>
                  <div className="text-xs text-ink-3">{r.machine_type}</div>
                </div>
              ),
            },
            { key: 'status', header: 'Status', value: (r) => r.status, render: (r) => <StatusPill status={r.status} /> },
            {
              key: 'eff',
              header: 'Efficiency',
              value: (r) => r.efficiency_pct,
              render: (r) => (
                <div className="flex w-32 items-center gap-2">
                  <Meter value={r.efficiency_pct} max={100} tone={toneOf(r.status)} />
                  <span className="num w-11 shrink-0 text-right text-xs">{pct(r.efficiency_pct)}</span>
                </div>
              ),
            },
            {
              key: 'actual',
              header: 'Actual / target',
              align: 'right',
              hideBelow: 'lg',
              value: (r) => r.actual_kg,
              render: (r) => `${kgExact(r.actual_kg)} / ${kgExact(r.target_kg)}`,
            },
            { key: 'loss', header: 'Loss', align: 'right', value: (r) => r.loss_kg, render: (r) => kgExact(r.loss_kg) },
            {
              key: 'down',
              header: 'Downtime',
              align: 'right',
              hideBelow: 'sm',
              value: (r) => r.downtime_min,
              render: (r) => minutes(r.downtime_min),
            },
            {
              key: 'issue',
              header: 'Main issue',
              hideBelow: 'md',
              value: (r) => r.main_issue,
              render: (r) => <Clip text={r.main_issue} />,
            },
          ]}
        />
      </Card>

      <Card>
        <CardHeader
          title={
            <span className="inline-flex items-center gap-1.5">
              <Wrench className="size-4 text-ink-3" /> Downtime analysis
            </span>
          }
          subtitle={`${minutes(dk.total_downtime_min)} across ${num(dk.stoppage_count)} stoppages`}
        />
        <CardBody className="grid gap-6 lg:grid-cols-2">
          <SplitBar
            format={minutes}
            parts={[
              { label: 'Unplanned', value: dk.unplanned_downtime_min, color: 1 },
              { label: 'Planned', value: dk.planned_downtime_min, color: 'muted' },
            ]}
          />
          <div>
            <div className="mb-2 text-2xs font-medium uppercase tracking-wide text-ink-3">By cause</div>
            <RankedBars
              format={minutes}
              items={data.downtime_reasons.map((r) => ({ label: r.category, value: r.downtime_min, share: r.percentage }))}
            />
          </div>
        </CardBody>
      </Card>
    </div>
  );
};
