import React from 'react';
import { Link } from 'react-router-dom';
import { useManpowerQuality } from '../../api/queries';
import { useParam, usePeriod } from '../../app/state';
import { num, pct } from '../../lib/format';
import type { AttentionItem, ManpowerQualityModuleData, QualityParameterItem } from '../../types/manpowerQuality';
import { PageHeader } from '../../layout/PageHeader';
import { QueryView } from '../../design/QueryView';
import { Card, CardBody, CardHeader, Kpi, KpiGrid, Meter, StatusPill, toneOf } from '../../design/ui';
import { DataTable } from '../../design/DataTable';
import { ChartPanel } from '../../design/ChartPanel';
import { TrendChart } from '../../design/charts/Charts';

/** The backend returns one attention list for people and quality; split it by subject. */
export const isQualityItem = (a: AttentionItem) => /quality|thick|thin|neps|u%|cv|limit|spec|yarn|defect/i.test(`${a.title} ${a.detail}`);

const fmtVal = (v: number, unit: string) => `${Number.isInteger(v) ? v : v.toFixed(1)}${unit === '%' ? '%' : ` ${unit}`}`;

export const QualityPage: React.FC = () => {
  const [period] = usePeriod();
  const query = useManpowerQuality(period);
  return (
    <>
      <PageHeader title="Quality" description="Yarn test results against specification limits" showPeriod />
      <QueryView query={query}>{(d) => <QualityBody data={d} />}</QueryView>
    </>
  );
};

const QualityBody: React.FC<{ data: ManpowerQualityModuleData }> = ({ data }) => {
  const qs = data.quality_status;
  const params = data.quality_parameters;
  const outOfLimit = params.filter((p) => p.status === 'OUT OF LIMIT').length;
  const trendKeys = Object.keys(data.quality_trends_by_param);
  // Default to the worst parameter so the chart opens on the problem.
  const worst = params.find((p) => p.status === 'OUT OF LIMIT') ?? params.find((p) => p.status === 'ATTENTION') ?? params[0];
  const [param, setParam] = useParam('param', worst?.parameter ?? trendKeys[0] ?? '');
  const selected = params.find((p) => p.parameter === param);
  const trend = data.quality_trends_by_param[param] ?? [];
  const alerts = data.needs_attention.filter(isQualityItem);

  return (
    <div className="space-y-4">
      <KpiGrid>
        <Kpi label="Quality status" value={<StatusPill status={qs.status} className="text-xs" />} hint={qs.main_issue} />
        <Kpi label="Samples tested" value={num(qs.samples_tested)} />
        <Kpi
          label="Pass rate"
          value={pct(qs.pass_rate_pct)}
          status={qs.pass_rate_pct >= 98 ? 'ok' : qs.pass_rate_pct >= 95 ? 'warn' : 'bad'}
        />
        <Kpi label="Defect rate" value={pct(qs.defect_rate_pct)} />
        <Kpi label="Out of limit" value={`${outOfLimit} of ${params.length}`} hint="parameters" status={outOfLimit ? 'bad' : 'ok'} />
        <Kpi label="Machines flagged" value={num(data.quality_issues_by_machine.filter((m) => m.status !== 'NORMAL').length)} />
      </KpiGrid>

      <div className="grid gap-4 lg:grid-cols-5">
        <Card className="lg:col-span-2">
          <CardHeader title="Parameters vs limit" subtitle="Select a parameter to see its trend" />
          <DataTable<QualityParameterItem>
            rows={params}
            rowKey={(r) => r.parameter}
            selectedKey={param}
            onRowClick={(r) => trendKeys.includes(r.parameter) && setParam(r.parameter)}
            columns={[
              { key: 'p', header: 'Parameter', render: (r) => <span className="font-medium">{r.label}</span> },
              {
                key: 'v',
                header: 'Value / limit',
                render: (r) => (
                  <div className="w-36 space-y-1">
                    <div className="num flex justify-between text-xs">
                      <span className="text-ink">{fmtVal(r.value, r.unit)}</span>
                      <span className="text-ink-3">≤ {fmtVal(r.limit, r.unit)}</span>
                    </div>
                    <Meter value={r.value} max={Math.max(r.value, r.limit) * 1.15} marker={r.limit} tone={toneOf(r.status)} />
                  </div>
                ),
              },
              {
                key: 's',
                header: 'Status',
                render: (r) => <StatusPill status={r.status} label={r.status === 'OUT OF LIMIT' ? 'Out of limit' : undefined} />,
              },
            ]}
          />
        </Card>

        <ChartPanel
          className="lg:col-span-3"
          title={`${selected?.label ?? param} trend`}
          subtitle="Daily test average against the specification limit"
          rows={trend}
          rowKey={(r) => r.date_label}
          exportName={`quality-${param}`}
          chart={
            <TrendChart
              data={trend}
              xKey="date_label"
              format={(v) => fmtVal(v, selected?.unit ?? '')}
              series={[{ key: 'value', label: selected?.label ?? param, color: 0 }]}
              reference={trend[0] ? { value: trend[0].limit, label: 'Spec limit' } : undefined}
              height={280}
            />
          }
          columns={[
            { key: 'd', header: 'Date', value: (r) => r.date_label, render: (r) => r.date_label },
            { key: 'v', header: 'Value', align: 'right', value: (r) => r.value, render: (r) => fmtVal(r.value, selected?.unit ?? '') },
            { key: 'l', header: 'Limit', align: 'right', value: (r) => r.limit, render: (r) => fmtVal(r.limit, selected?.unit ?? '') },
          ]}
        />
      </div>

      <div className="grid gap-4 lg:grid-cols-5">
        <Card className="lg:col-span-3">
          <CardHeader title="Issues by machine" subtitle="Latest test result per machine and parameter" />
          <DataTable
            rows={data.quality_issues_by_machine}
            rowKey={(r) => `${r.machine_process}-${r.quality_issue}`}
            exportName="quality-by-machine"
            columns={[
              {
                key: 'm',
                header: 'Machine',
                value: (r) => r.machine_process,
                render: (r) => {
                  const id = r.machine_process.split(' ').slice(-1)[0];
                  return (
                    <Link
                      to={`/assets?machine=${encodeURIComponent(id)}`}
                      onClick={(e) => e.stopPropagation()}
                      className="font-medium hover:underline"
                    >
                      {r.machine_process}
                    </Link>
                  );
                },
              },
              { key: 'p', header: 'Parameter', value: (r) => r.quality_issue, render: (r) => r.quality_issue },
              { key: 'v', header: 'Value', align: 'right', value: (r) => r.current_value, render: (r) => fmtVal(r.current_value, r.unit) },
              { key: 'l', header: 'Limit', align: 'right', value: (r) => r.limit, render: (r) => fmtVal(r.limit, r.unit) },
              {
                key: 's',
                header: 'Status',
                value: (r) => r.status,
                render: (r) => <StatusPill status={r.status} label={r.status === 'OUT OF LIMIT' ? 'Out of limit' : undefined} />,
              },
            ]}
          />
        </Card>
        <AttentionList title="Quality alerts" items={alerts} />
      </div>
    </div>
  );
};

export const AttentionList: React.FC<{ title: string; items: AttentionItem[]; className?: string }> = ({
  title,
  items,
  className = 'lg:col-span-2',
}) => (
  <Card className={className}>
    <CardHeader title={title} />
    {items.length ? (
      <ul className="divide-y divide-line border-t border-line">
        {items.map((a) => (
          <li key={a.title} className="flex gap-3 px-4 py-3">
            <StatusPill tone={toneOf(a.severity)} label={a.severity === 'HIGH' ? 'High' : a.severity === 'MEDIUM' ? 'Medium' : 'Low'} />
            <div>
              <div className="text-sm font-medium text-ink">{a.title}</div>
              <div className="text-xs text-ink-3">{a.detail}</div>
            </div>
          </li>
        ))}
      </ul>
    ) : (
      <CardBody>
        <p className="py-4 text-center text-xs text-ink-3">Nothing needs attention.</p>
      </CardBody>
    )}
  </Card>
);
