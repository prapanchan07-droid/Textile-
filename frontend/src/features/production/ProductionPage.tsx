import React from 'react';
import { Link } from 'react-router-dom';
import { ArrowDownRight, ArrowUpRight, CalendarDays, UploadCloud, X } from 'lucide-react';
import { useProduction } from '../../api/queries';
import { useParam } from '../../app/state';
import { kg, kgExact, tonnesAxis, pct, signed } from '../../lib/format';
import type { MachineTypePerformanceItem, ProductionModuleData } from '../../types/production';
import { PageHeader } from '../../layout/PageHeader';
import { QueryView } from '../../design/QueryView';
import { Button, Card, CardBody, CardHeader, EmptyState, Kpi, KpiGrid, Meter, Notice, StatusPill, toneOf } from '../../design/ui';
import { DataTable } from '../../design/DataTable';
import { ChartPanel } from '../../design/ChartPanel';
import { ColumnChart, RankedBars, TrendChart } from '../../design/charts/Charts';
import { achievementTone } from '../control-tower/ControlTowerPage';

type ProductionData = ProductionModuleData & { is_reconciled?: boolean; data_quality_warning?: string | null };

export const ProductionPage: React.FC = () => {
  const [date, setDate] = useParam('date');
  const query = useProduction(date || undefined);

  return (
    <>
      <PageHeader
        title="Production"
        description="Output by shift, machine type and loss reason, from imported production reports"
        actions={
          <div className="flex items-center gap-1.5">
            <label className="relative flex items-center">
              <CalendarDays className="pointer-events-none absolute left-2 size-3.5 text-ink-3" />
              <input
                type="date"
                value={date}
                onChange={(e) => setDate(e.target.value || null)}
                aria-label="Report date"
                className="h-7 rounded-md border border-line bg-surface pl-7 pr-2 text-xs text-ink hover:border-line-strong"
              />
            </label>
            {date ? (
              <Button size="sm" variant="ghost" onClick={() => setDate(null)} icon={<X className="size-3.5" />}>
                Latest
              </Button>
            ) : (
              <span className="text-xs text-ink-3">Showing latest report</span>
            )}
          </div>
        }
      />
      <QueryView query={query}>{(d) => <ProductionBody data={d} />}</QueryView>
    </>
  );
};

const ProductionBody: React.FC<{ data: ProductionData }> = ({ data }) => {
  const noData = data.actual_kg === 0 && data.target_kg === 0;
  if (noData) {
    return (
      <Card>
        <EmptyState
          icon={<UploadCloud className="size-5" />}
          title="No production report for this date"
          description="Production figures here come only from imported production reports, so they can be traced back to a file, sheet and row. Import a report, or pick another date."
          action={
            <Link to="/data">
              <Button variant="primary" icon={<UploadCloud className="size-4" />}>
                Import reports
              </Button>
            </Link>
          }
        />
      </Card>
    );
  }

  const shortfall = Math.max(0, data.target_kg - data.actual_kg);
  const shifts = data.shift_performance ?? [];
  const cmp = data.comparison;

  return (
    <div className="space-y-4">
      {data.is_reconciled === false && (
        <Notice tone="warn">
          {data.data_quality_warning ||
            'Shift totals do not add up to the report total. Check the source report before relying on these numbers.'}
        </Notice>
      )}

      <KpiGrid className="xl:grid-cols-4">
        <Kpi
          label="Actual output"
          value={kg(data.actual_kg)}
          hint={cmp && cmp.reference_kg > 0 ? `${cmp.reference_period}: ${kg(cmp.reference_kg)}` : undefined}
          delta={
            cmp && cmp.reference_kg > 0
              ? {
                  text: signed(cmp.difference_pct, (v) => `${v.toFixed(1)}%`),
                  direction: cmp.difference_pct > 0 ? 'up' : cmp.difference_pct < 0 ? 'down' : 'flat',
                  good: cmp.difference_pct >= 0,
                }
              : undefined
          }
        />
        <Kpi label="Target" value={kg(data.target_kg)} />
        <Kpi
          label="Shortfall"
          value={kgExact(shortfall)}
          status={shortfall > 0 ? 'bad' : 'ok'}
          hint={shortfall > 0 ? 'below target' : 'Target met'}
        />
        <Kpi label="Achievement" value={pct(data.achievement_pct)} status={achievementTone(data.achievement_pct)} />
      </KpiGrid>

      <div className="grid gap-4 lg:grid-cols-5">
        <ChartPanel
          className="lg:col-span-3"
          title="Shift performance"
          subtitle="Actual against target for each shift"
          rows={shifts}
          rowKey={(r) => r.shift_name}
          exportName="shift-performance"
          chart={
            shifts.length ? (
              <ColumnChart
                data={shifts}
                xKey="shift_name"
                format={kgExact}
                axisFormat={tonnesAxis}
                height={260}
                series={[
                  { key: 'actual_kg', label: 'Actual', color: 0 },
                  { key: 'target_kg', label: 'Target', color: 'muted' },
                ]}
              />
            ) : (
              <EmptyState title="No shift breakdown in this report" />
            )
          }
          columns={[
            { key: 'shift', header: 'Shift', value: (r) => r.shift_name, render: (r) => r.shift_name },
            { key: 'actual', header: 'Actual', align: 'right', value: (r) => r.actual_kg, render: (r) => kgExact(r.actual_kg) },
            { key: 'target', header: 'Target', align: 'right', value: (r) => r.target_kg, render: (r) => kgExact(r.target_kg) },
            { key: 'ach', header: 'Achievement', align: 'right', value: (r) => r.achievement_pct, render: (r) => pct(r.achievement_pct) },
          ]}
        />
        <Card className="lg:col-span-2">
          <CardHeader title="Loss by reason" subtitle={`${kgExact(shortfall)} below target`} />
          <CardBody>
            {data.loss_reasons.length ? (
              <RankedBars
                format={kgExact}
                items={data.loss_reasons.map((r) => ({ label: r.category, value: r.impact_kg, share: r.percentage }))}
              />
            ) : (
              <EmptyState title="No loss reasons recorded" description="The report did not include downtime or loss categories." />
            )}
          </CardBody>
        </Card>
      </div>

      {data.trend.length > 1 && (
        <ChartPanel
          title="Output trend"
          rows={data.trend}
          rowKey={(r) => r.date_label}
          exportName="production-trend"
          chart={
            <TrendChart
              data={data.trend}
              xKey="date_label"
              format={kgExact}
              axisFormat={tonnesAxis}
              series={[
                { key: 'actual_kg', label: 'Actual', color: 0 },
                { key: 'target_kg', label: 'Target', color: 'muted' },
              ]}
            />
          }
          columns={[
            { key: 'd', header: 'Date', value: (r) => r.date_label, render: (r) => r.date_label },
            { key: 'a', header: 'Actual', align: 'right', value: (r) => r.actual_kg, render: (r) => kgExact(r.actual_kg) },
            { key: 't', header: 'Target', align: 'right', value: (r) => r.target_kg, render: (r) => kgExact(r.target_kg) },
            { key: 'g', header: 'Gap', align: 'right', value: (r) => r.gap_kg, render: (r) => kgExact(r.gap_kg) },
          ]}
        />
      )}

      <div className="grid gap-4 lg:grid-cols-5">
        <Card className="lg:col-span-3">
          <CardHeader title="By machine type" subtitle="Where output fell short, by process" />
          <DataTable<MachineTypePerformanceItem>
            rows={data.machine_type_performance}
            rowKey={(r) => r.machine_type}
            exportName="production-by-machine-type"
            initialSort={{ key: 'loss', dir: 'desc' }}
            emptyTitle="No machine-type breakdown in this report"
            columns={[
              {
                key: 'type',
                header: 'Machine type',
                value: (r) => r.machine_type,
                render: (r) => <span className="font-medium">{r.machine_type}</span>,
              },
              { key: 'status', header: 'Status', value: (r) => r.status, render: (r) => <StatusPill status={r.status} /> },
              {
                key: 'eff',
                header: 'Efficiency',
                value: (r) => r.efficiency_pct,
                render: (r) => (
                  <div className="flex w-36 items-center gap-2">
                    <Meter value={r.efficiency_pct} max={100} tone={toneOf(r.status)} />
                    <span className="num w-12 shrink-0 text-right text-xs">{pct(r.efficiency_pct)}</span>
                  </div>
                ),
              },
              {
                key: 'actual',
                header: 'Actual',
                align: 'right',
                hideBelow: 'md',
                value: (r) => r.actual_kg,
                render: (r) => kgExact(r.actual_kg),
              },
              { key: 'loss', header: 'Loss', align: 'right', value: (r) => r.loss_kg, render: (r) => kgExact(r.loss_kg) },
            ]}
          />
        </Card>

        <Card className="lg:col-span-2">
          <CardHeader title="Contributing factors" subtitle="Reported alongside output" />
          {data.production_factors?.length ? (
            <ul className="divide-y divide-line border-t border-line">
              {data.production_factors.map((f) => (
                <li key={f.name} className="flex items-center justify-between gap-3 px-4 py-2.5 text-sm">
                  <span className="text-ink">{f.name}</span>
                  <span className="flex items-center gap-2">
                    <span className="num inline-flex items-center gap-0.5 text-ink-2">
                      {f.direction === 'UP' ? <ArrowUpRight className="size-3.5" /> : <ArrowDownRight className="size-3.5" />}
                      {f.display_value}
                    </span>
                    <StatusPill status={f.status} />
                  </span>
                </li>
              ))}
            </ul>
          ) : (
            <EmptyState
              title="Not in this report"
              description="Downtime, power and manpower factors appear when the report includes them."
            />
          )}
        </Card>
      </div>
    </div>
  );
};
