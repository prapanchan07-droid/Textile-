import React from 'react';
import { Lightbulb, Plus, X } from 'lucide-react';
import { useMachineComparison } from '../../api/queries';
import { useParam, usePeriod } from '../../app/state';
import { cn } from '../../lib/format';
import type { MachineComparisonResponse, MachineMetricValue } from '../../types/machineComparison';
import { QueryView } from '../../design/QueryView';
import { Card, CardBody, CardHeader, EmptyState, Select, StatusPill, toneOf } from '../../design/ui';
import { DataTable } from '../../design/DataTable';
import { useChartTheme } from '../../design/charts/theme';
import { AssetsHeader } from './AssetsLayout';

const METRICS = [
  { value: 'EFFICIENCY', label: 'Efficiency' },
  { value: 'PRODUCTION', label: 'Production' },
  { value: 'PRODUCTION_LOSS', label: 'Production loss' },
  { value: 'DOWNTIME', label: 'Downtime' },
  { value: 'UTILIZATION', label: 'Utilization' },
  { value: 'ENERGY_PER_KG', label: 'Energy per kg' },
  { value: 'QUALITY', label: 'Quality rating' },
];

const REFERENCES = [
  { value: 'FACTORY_AVG', label: 'Factory average' },
  { value: 'TARGET', label: 'Target' },
  { value: 'NONE', label: 'No reference' },
];

export const BenchmarkPage: React.FC = () => {
  const [period] = usePeriod();
  const [m, setM] = useParam('m');
  const [metric, setMetric] = useParam('metric', 'EFFICIENCY');
  const [reference, setReference] = useParam('ref', 'FACTORY_AVG');
  const selected = m ? m.split(',').filter(Boolean) : [];
  const query = useMachineComparison({ machines: selected, metric, period, machineType: 'ALL', reference });

  // With nothing chosen the API picks a default set; show that set as the selection.
  const effective = selected.length ? selected : (query.data?.selected_machine_ids ?? []);
  const setSelection = (ids: string[]) => setM(ids.join(','));

  return (
    <>
      <AssetsHeader
        actions={
          <>
            <Select aria-label="Metric" value={metric} onChange={(e) => setMetric(e.target.value)} options={METRICS} />
            <Select aria-label="Reference" value={reference} onChange={(e) => setReference(e.target.value)} options={REFERENCES} />
          </>
        }
      />
      <QueryView query={query}>
        {(d) => (
          <BenchmarkBody
            data={d}
            selected={effective}
            onChange={setSelection}
            metricLabel={METRICS.find((x) => x.value === metric)?.label ?? metric}
          />
        )}
      </QueryView>
    </>
  );
};

const BenchmarkBody: React.FC<{
  data: MachineComparisonResponse;
  selected: string[];
  onChange: (ids: string[]) => void;
  metricLabel: string;
}> = ({ data, selected, onChange, metricLabel }) => {
  const toggle = (id: string) => onChange(selected.includes(id) ? selected.filter((x) => x !== id) : [...selected, id]);
  const available = data.all_master_machines.filter((x) => !selected.includes(x.machine_id));

  return (
    <div className="space-y-4">
      <Card className="flex flex-wrap items-center gap-2 p-3">
        <span className="mr-1 text-xs text-ink-3">Comparing</span>
        {selected.map((id) => (
          <span
            key={id}
            className="inline-flex h-7 items-center gap-1 rounded-md border border-line bg-subtle pl-2.5 pr-1 text-xs font-medium text-ink"
          >
            {id}
            <button
              onClick={() => toggle(id)}
              aria-label={`Remove ${id}`}
              className="rounded p-0.5 text-ink-3 hover:bg-muted hover:text-ink"
            >
              <X className="size-3" />
            </button>
          </span>
        ))}
        {available.length > 0 && (
          <label className="relative inline-flex h-7 items-center gap-1 rounded-md border border-dashed border-line-strong px-2 text-xs text-ink-2 hover:text-ink">
            <Plus className="size-3" /> Add machine
            <select
              aria-label="Add machine"
              value=""
              onChange={(e) => e.target.value && toggle(e.target.value)}
              className="absolute inset-0 cursor-pointer opacity-0"
            >
              <option value="">Add machine</option>
              {available.map((x) => (
                <option key={x.machine_id} value={x.machine_id}>
                  {x.machine_id} — {x.machine_type}, {x.section}
                </option>
              ))}
            </select>
          </label>
        )}
      </Card>

      {selected.length === 0 ? (
        <Card>
          <EmptyState
            title="Pick machines to compare"
            description="Add two or more machines to rank them on one metric and see every metric side by side."
          />
        </Card>
      ) : (
        <>
          <div className="grid gap-4 lg:grid-cols-5">
            <Card className="lg:col-span-3">
              <CardHeader
                title={`${metricLabel} by machine`}
                subtitle={data.reference_type !== 'NONE' ? `Reference: ${data.reference_formatted}` : undefined}
              />
              <CardBody>
                <MetricRanking
                  metrics={data.primary_metrics}
                  reference={data.reference_type !== 'NONE' ? data.reference_value : undefined}
                />
              </CardBody>
            </Card>
            <Card className="lg:col-span-2">
              <CardHeader
                title={
                  <span className="inline-flex items-center gap-1.5">
                    <Lightbulb className="size-4 text-ink-3" /> Findings
                  </span>
                }
              />
              <CardBody className="space-y-3 text-sm">
                <p className="text-ink">{data.insight.summary_text}</p>
                <ul className="space-y-1.5 text-ink-2">
                  {data.insight.key_observations.map((o) => (
                    <li key={o} className="flex gap-2">
                      <span className="mt-2 size-1 shrink-0 rounded-full bg-ink-3" />
                      {o}
                    </li>
                  ))}
                </ul>
              </CardBody>
            </Card>
          </div>

          <Card>
            <CardHeader
              title="All metrics"
              subtitle={selected.length === 2 && data.head_to_head ? 'Head-to-head, with the leader on each metric' : 'Side by side'}
            />
            {selected.length === 2 && data.head_to_head ? (
              <DataTable
                rows={data.head_to_head}
                rowKey={(r) => r.metric_key}
                columns={[
                  { key: 'metric', header: 'Metric', render: (r) => r.metric_name },
                  ...[0, 1].map((i) => ({
                    key: `m${i}`,
                    header: selected[i],
                    align: 'right' as const,
                    render: (r: NonNullable<MachineComparisonResponse['head_to_head']>[number]) => (
                      <span className={cn(r.leader_machine_id === selected[i] && 'font-semibold text-ok')}>
                        {i === 0 ? r.machine1_formatted : r.machine2_formatted}
                      </span>
                    ),
                  })),
                  { key: 'delta', header: 'Difference', align: 'right', render: (r) => <span className="text-ink-2">{r.delta_text}</span> },
                ]}
              />
            ) : (
              <DataTable
                rows={data.multi_metric_matrix}
                rowKey={(r) => r.metric_name}
                exportName="machine-benchmark"
                columns={[
                  { key: 'metric', header: 'Metric', value: (r) => r.metric_name, render: (r) => r.metric_name },
                  ...selected.map((id) => ({
                    key: id,
                    header: id,
                    align: 'right' as const,
                    value: (r: { values: Record<string, string> }) => r.values[id] ?? '',
                    render: (r: { values: Record<string, string> }) => r.values[id] ?? '—',
                  })),
                ]}
              />
            )}
          </Card>
        </>
      )}
    </div>
  );
};

/** Ranked horizontal bars with a reference tick; the same hue for every machine, status shown as a pill. */
const MetricRanking: React.FC<{ metrics: MachineMetricValue[]; reference?: number }> = ({ metrics, reference }) => {
  const t = useChartTheme();
  const max = Math.max(...metrics.map((x) => x.value), reference ?? 0) * 1.05 || 1;
  const sorted = [...metrics].sort((a, b) => b.value - a.value);
  return (
    <ul className="space-y-3.5">
      {sorted.map((x) => (
        <li key={x.machine_id} className="grid grid-cols-[72px_1fr_210px] items-center gap-3">
          <div>
            <div className="text-sm font-medium text-ink">{x.machine_id}</div>
            <div className="text-2xs text-ink-3">{x.machine_type}</div>
          </div>
          <div className="relative h-2.5 rounded-full bg-muted" title={`${x.machine_id}: ${x.formatted_value}`}>
            <div
              className="h-full rounded-r-[4px] rounded-l-full"
              style={{ width: `${(x.value / max) * 100}%`, background: t.series[0] }}
            />
            {reference != null && (
              <div
                className="absolute -top-1 h-[18px] w-0.5 rounded-full bg-ink"
                style={{ left: `${(reference / max) * 100}%` }}
                title={`Reference ${reference}`}
              />
            )}
          </div>
          <div className="flex items-center justify-end gap-2">
            <div className="text-right">
              <div className="num text-sm font-medium text-ink">{x.formatted_value}</div>
              {x.variance_label && <div className="num text-2xs text-ink-3">{x.variance_label}</div>}
            </div>
            <StatusPill tone={toneOf(x.status)} label={x.status === 'NORMAL' ? 'OK' : x.status === 'ATTENTION' ? 'Watch' : 'Critical'} />
          </div>
        </li>
      ))}
    </ul>
  );
};
