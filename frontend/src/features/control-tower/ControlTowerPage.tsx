import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { ArrowRight, Sparkles } from 'lucide-react';
import { useOverview } from '../../api/queries';
import { usePeriod } from '../../app/state';
import { comparisonLabel, periodLabel } from '../../lib/period';
import { kg, kgExact, tonnesAxis, pct } from '../../lib/format';
import type { FactoryOverviewData, MachineAttentionItem, PeriodComparisonMetric } from '../../types/overview';
import { PageHeader } from '../../layout/PageHeader';
import { QueryView } from '../../design/QueryView';
import { Badge, Button, Card, CardBody, CardHeader, Kpi, KpiGrid, StatusPill, type KpiProps, type Tone } from '../../design/ui';
import { Clip, DataTable } from '../../design/DataTable';
import { ChartPanel } from '../../design/ChartPanel';
import { ColumnChart, RankedBars } from '../../design/charts/Charts';

export const achievementTone = (a: number): Tone => (a >= 98 ? 'ok' : a >= 93 ? 'warn' : 'bad');

/** Turns a backend comparison row into a KPI delta. */
export const deltaOf = (m: PeriodComparisonMetric | undefined): KpiProps['delta'] =>
  m && {
    text: m.change_text,
    direction: m.change_pct > 0 ? 'up' : m.change_pct < 0 ? 'down' : 'flat',
    good: m.trend === 'up_good' || m.trend === 'down_good' ? true : m.trend === 'neutral' ? null : false,
  };

export const ControlTowerPage: React.FC = () => {
  const [period] = usePeriod();
  const query = useOverview(period);
  return (
    <>
      <PageHeader
        title="Control Tower"
        description={`Plant-wide performance · ${periodLabel(period)} vs ${comparisonLabel(period)}`}
        showPeriod
      />
      <QueryView query={query}>{(d) => <ControlTowerBody data={d} />}</QueryView>
    </>
  );
};

const ControlTowerBody: React.FC<{ data: FactoryOverviewData }> = ({ data }) => {
  const navigate = useNavigate();
  const s = data.production_summary;
  const byName = (name: string) => data.period_comparison.find((m) => m.metric.toLowerCase().includes(name));
  const volume = byName('production');
  const others = data.period_comparison.filter((m) => m !== volume && !m.metric.toLowerCase().includes('efficiency'));
  const eff = byName('efficiency');
  const shortfall = Math.max(0, s.target_kg - s.actual_kg);
  const shiftRows = data.trend.map((t) => ({ ...t, short: t.label.split(' (')[0] }));
  const isShiftView = shiftRows.every((r) => r.short.toLowerCase().startsWith('shift'));
  const hasIssue = data.executive_summary.impact_kg > 0;

  return (
    <div className="space-y-4">
      {/* Executive brief: one sentence of what matters, one click to act on it */}
      <Card className="flex flex-col gap-3 p-4 sm:flex-row sm:items-center">
        <StatusPill tone={achievementTone(s.achievement_pct)} label={hasIssue ? 'Below target' : 'On target'} />
        <p className="min-w-0 flex-1 text-sm text-ink">
          <span className="font-medium">{data.executive_summary.factory_status}.</span>{' '}
          {hasIssue && (
            <span className="text-ink-2">
              Main driver: {data.executive_summary.main_issue} — {data.executive_summary.affected_entity}.
            </span>
          )}
        </p>
        <Link to="/actions">
          <Button size="sm" variant="secondary">
            Open Action Center <ArrowRight className="size-3.5" />
          </Button>
        </Link>
      </Card>

      <KpiGrid>
        <Kpi
          label="Production"
          value={kg(s.actual_kg)}
          hint={`of ${kg(s.target_kg)} target`}
          delta={deltaOf(volume)}
          onClick={() => navigate('/production')}
        />
        <Kpi
          label="Target achievement"
          value={pct(s.achievement_pct)}
          status={achievementTone(s.achievement_pct)}
          hint={shortfall > 0 ? `${kgExact(shortfall)} short` : 'Target met'}
        />
        <Kpi label="Efficiency" value={pct(s.efficiency_pct)} delta={deltaOf(eff)} onClick={() => navigate('/assets')} />
        {others.slice(0, 3).map((m) => (
          <Kpi key={m.metric} label={m.metric.replace('Consumption ', '')} value={m.current} delta={deltaOf(m)} />
        ))}
      </KpiGrid>

      <div className="grid gap-4 lg:grid-cols-5">
        <ChartPanel
          className="lg:col-span-3"
          title={isShiftView ? 'Output by shift' : 'Output trend'}
          subtitle="Actual against planned output"
          rows={shiftRows}
          rowKey={(r) => r.label}
          exportName="output-by-shift"
          chart={
            <ColumnChart
              data={shiftRows}
              xKey="short"
              format={kgExact}
              axisFormat={tonnesAxis}
              height={260}
              series={[
                { key: 'actual_kg', label: 'Actual', color: 0 },
                { key: 'target_kg', label: 'Target', color: 'muted' },
              ]}
            />
          }
          columns={[
            { key: 'label', header: 'Period', render: (r) => r.label, value: (r) => r.label },
            { key: 'actual', header: 'Actual', align: 'right', render: (r) => kgExact(r.actual_kg), value: (r) => r.actual_kg },
            { key: 'target', header: 'Target', align: 'right', render: (r) => kgExact(r.target_kg), value: (r) => r.target_kg },
            { key: 'loss', header: 'Shortfall', align: 'right', render: (r) => kgExact(r.loss_kg), value: (r) => r.loss_kg },
            { key: 'eff', header: 'Efficiency', align: 'right', render: (r) => pct(r.efficiency_pct), value: (r) => r.efficiency_pct },
          ]}
        />

        <Card className="lg:col-span-2">
          <CardHeader title="Where the shortfall comes from" subtitle={`${kgExact(s.loss_kg)} lost against target`} />
          <CardBody>
            {data.loss_contributors.length ? (
              <RankedBars
                format={kgExact}
                items={data.loss_contributors.map((c) => ({
                  label: c.category,
                  value: c.impact_kg,
                  share: c.percentage,
                  sublabel: c.evidence,
                }))}
              />
            ) : (
              <p className="py-6 text-center text-xs text-ink-3">No losses recorded for this period.</p>
            )}
          </CardBody>
        </Card>
      </div>

      <div className="grid gap-4 lg:grid-cols-5">
        <Card className="lg:col-span-3">
          <CardHeader
            title="Machines needing attention"
            subtitle={`Factory average efficiency ${pct(data.low_efficiency_spotlight.factory_avg_pct)}`}
            actions={
              <Link to="/assets" className="text-xs font-medium text-accent-ink hover:underline">
                All machines
              </Link>
            }
          />
          <DataTable<MachineAttentionItem>
            rows={data.machines_requiring_attention}
            rowKey={(r) => r.machine_id}
            onRowClick={(r) => navigate(`/assets?machine=${encodeURIComponent(r.machine_id)}`)}
            initialSort={{ key: 'loss', dir: 'desc' }}
            columns={[
              {
                key: 'id',
                header: 'Machine',
                value: (r) => r.machine_id,
                render: (r) => (
                  <div>
                    <div className="font-medium">{r.machine_id}</div>
                    <div className="text-xs text-ink-3">
                      {r.machine_type} · {r.section_id}
                    </div>
                  </div>
                ),
              },
              { key: 'status', header: 'Status', value: (r) => r.status, render: (r) => <StatusPill status={r.status} /> },
              { key: 'eff', header: 'Efficiency', align: 'right', value: (r) => r.efficiency_pct, render: (r) => pct(r.efficiency_pct) },
              { key: 'loss', header: 'Loss', align: 'right', value: (r) => r.loss_kg, render: (r) => kgExact(r.loss_kg) },
              {
                key: 'issue',
                header: 'Primary issue',
                hideBelow: 'md',
                value: (r) => r.primary_issue,
                render: (r) => <Clip text={r.primary_issue} className="max-w-[11rem]" />,
              },
            ]}
          />
        </Card>

        <AnalystBrief data={data} />
      </div>
    </div>
  );
};

/** Condensed AI summary. Projection lives here as one line instead of a whole section. */
const AnalystBrief: React.FC<{ data: FactoryOverviewData }> = ({ data }) => {
  const ai = data.ai_insight;
  const proj = data.impact_projection;
  const confidence = ai.confidence.split(' ')[0];
  return (
    <Card className="lg:col-span-2">
      <CardHeader
        title={
          <span className="inline-flex items-center gap-1.5">
            <Sparkles className="size-4 text-accent" /> Analyst brief
          </span>
        }
        subtitle="Generated from the imported reports"
        actions={<Badge tone="info">{confidence} confidence</Badge>}
      />
      <CardBody className="space-y-4 text-sm">
        <p className="text-ink">{ai.summary}</p>
        {ai.observations.length > 0 && (
          <ul className="space-y-1.5 text-ink-2">
            {ai.observations.map((o) => (
              <li key={o} className="flex gap-2">
                <span className="mt-2 size-1 shrink-0 rounded-full bg-ink-3" />
                {o}
              </li>
            ))}
          </ul>
        )}
        {ai.recommended_investigation.length > 0 && (
          <div>
            <div className="mb-1.5 text-2xs font-medium uppercase tracking-wide text-ink-3">Next steps</div>
            <ol className="space-y-1.5">
              {ai.recommended_investigation.map((r, i) => (
                <li key={r} className="flex gap-2 text-ink-2">
                  <span className="num flex size-5 shrink-0 items-center justify-center rounded bg-muted text-2xs font-medium text-ink">
                    {i + 1}
                  </span>
                  {r.replace(/^\d+\.\s*/, '')}
                </li>
              ))}
            </ol>
          </div>
        )}
        {proj.is_sufficient_data && proj.daily_gap_kg > 0 && (
          <div className="rounded-md bg-subtle px-3 py-2 text-xs text-ink-2">
            If the current daily gap of <span className="font-medium text-ink">{kgExact(proj.daily_gap_kg)}</span> continues:{' '}
            <span className="font-medium text-ink">{kg(proj.projected_7d_gap_kg)}</span> in 7 days,{' '}
            <span className="font-medium text-ink">{kg(proj.projected_30d_gap_kg)}</span> in 30 days.
          </div>
        )}
      </CardBody>
    </Card>
  );
};
