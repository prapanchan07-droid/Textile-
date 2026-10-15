import React from 'react';
import { Link } from 'react-router-dom';
import { inrFromLakhs, minutes, num, pct } from '../../lib/format';
import { Card, CardBody, CardHeader, Kpi, KpiGrid } from '../../design/ui';
import { DataTable } from '../../design/DataTable';
import { ChartPanel } from '../../design/ChartPanel';
import { RankedBars, TrendChart } from '../../design/charts/Charts';
import type { WeavingModuleData, WeavingStopCause } from '../../types/weaving';
import { WeavingPage } from './shared';

export const StoppagesPage: React.FC = () => (
  <WeavingPage description="Why looms stop, how long, and what each cause costs">{(d) => <Body d={d} />}</WeavingPage>
);

const Body: React.FC<{ d: WeavingModuleData }> = ({ d }) => {
  const total = d.stop_causes.reduce((s, c) => s + c.minutes, 0);
  const stops = d.stop_causes.reduce((s, c) => s + c.stops, 0);
  const top = d.stop_causes[0];
  const byLoss = [...d.stop_causes].sort((a, b) => b.loss_lakhs - a.loss_lakhs);
  const worst = [...d.looms].sort((a, b) => b.loss_lakhs - a.loss_lakhs).slice(0, 8);
  return (
    <>
      <KpiGrid>
        <Kpi label="Stop time" value={minutes(total)} hint={`${d.period_label.toLowerCase()}, all looms`} />
        <Kpi label="Stops" value={num(stops)} hint={`about ${Math.round(total / Math.max(stops, 1))} min each`} />
        <Kpi label="Margin lost" value={inrFromLakhs(d.kpis.loss_lakhs)} status="bad" />
        <Kpi label="Biggest cause" value={top.cause} hint={`${pct(top.share_pct)} of stop time`} status="warn" />
        <Kpi label="Breakdowns" value={num(d.maintenance.breakdowns)} hint="mechanical + electrical" />
        <Kpi label="Mean repair time" value={`${d.maintenance.mttr_min} min`} hint="per breakdown" />
      </KpiGrid>

      <div className="grid gap-4 lg:grid-cols-5">
        <Card className="lg:col-span-2">
          <CardHeader title="Causes ranked by money lost" subtitle="Fix the top bars first" />
          <CardBody>
            <RankedBars items={byLoss.map((c) => ({ label: c.cause, value: c.loss_lakhs, share: c.share_pct }))} format={(v) => inrFromLakhs(v)} />
          </CardBody>
        </Card>
        <ChartPanel
          className="lg:col-span-3"
          title="Margin lost per day"
          subtitle="A rising line means stoppages are getting worse"
          rows={d.trend}
          rowKey={(r) => r.date_label}
          exportName="weaving-loss-trend"
          chart={<TrendChart data={d.trend} xKey="date_label" format={(v) => inrFromLakhs(v)} series={[{ key: 'loss_lakhs', label: 'Margin lost', color: 2 }]} area height={280} />}
          columns={[
            { key: 'd', header: 'Date', value: (r) => r.date_label, render: (r) => r.date_label },
            { key: 'l', header: 'Margin lost', align: 'right', value: (r) => r.loss_lakhs, render: (r) => inrFromLakhs(r.loss_lakhs) },
            { key: 'e', header: 'Efficiency', align: 'right', value: (r) => r.efficiency_pct, render: (r) => pct(r.efficiency_pct) },
          ]}
        />
      </div>

      <Card>
        <CardHeader title="Cause by cause: what to do" subtitle="Each cause with its cost and the recommended first step" />
        <DataTable<WeavingStopCause>
          rows={d.stop_causes}
          rowKey={(r) => r.cause}
          exportName="weaving-stop-causes"
          columns={[
            { key: 'c', header: 'Cause', value: (r) => r.cause, render: (r) => <span className="font-medium">{r.cause}</span> },
            { key: 'm', header: 'Time', align: 'right', value: (r) => r.minutes, render: (r) => minutes(r.minutes) },
            { key: 's', header: 'Share', align: 'right', value: (r) => r.share_pct, render: (r) => pct(r.share_pct) },
            { key: 'n', header: 'Stops', align: 'right', hideBelow: 'md', value: (r) => r.stops, render: (r) => num(r.stops) },
            { key: 'l', header: 'Margin lost', align: 'right', value: (r) => r.loss_lakhs, render: (r) => inrFromLakhs(r.loss_lakhs) },
            { key: 'a', header: 'First step', wrap: true, hideBelow: 'lg', value: (r) => r.advice, render: (r) => <span className="text-ink-2">{r.advice}</span> },
          ]}
        />
      </Card>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader title="Loss by shift" subtitle="Main stop reason in each shift" />
          <DataTable
            rows={d.shifts}
            rowKey={(r) => r.shift}
            dense
            columns={[
              { key: 's', header: 'Shift', value: (r) => r.shift, render: (r) => <span className="font-medium">{r.shift}</span> },
              { key: 'e', header: 'Efficiency', align: 'right', value: (r) => r.efficiency_pct, render: (r) => pct(r.efficiency_pct) },
              { key: 'x', header: 'Main stop reason', value: (r) => r.top_stop_reason, render: (r) => r.top_stop_reason },
            ]}
          />
        </Card>
        <Card>
          <CardHeader title="Looms losing the most" subtitle="Open a loom to see its cause and trend" />
          <DataTable
            rows={worst}
            rowKey={(r) => r.loom_id}
            dense
            columns={[
              { key: 'l', header: 'Loom', value: (r) => r.loom_id, render: (r) => <Link to={{ pathname: '/weaving/looms', search: `?loom=${r.loom_id}` }} className="font-medium hover:underline">{r.loom_id}</Link> },
              { key: 'i', header: 'Main issue', value: (r) => r.main_issue, render: (r) => r.main_issue },
              { key: 'e', header: 'Efficiency', align: 'right', value: (r) => r.efficiency_pct, render: (r) => pct(r.efficiency_pct) },
              { key: 'x', header: 'Lost', align: 'right', value: (r) => r.loss_lakhs, render: (r) => inrFromLakhs(r.loss_lakhs) },
            ]}
          />
        </Card>
      </div>
    </>
  );
};
