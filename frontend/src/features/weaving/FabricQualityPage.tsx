import React from 'react';
import { Link } from 'react-router-dom';
import { inrFromLakhs, meters, pct } from '../../lib/format';
import { Card, CardBody, CardHeader, Kpi, KpiGrid, StatusPill } from '../../design/ui';
import { DataTable } from '../../design/DataTable';
import { ChartPanel } from '../../design/ChartPanel';
import { RankedBars, SplitBar, TrendChart } from '../../design/charts/Charts';
import type { WeavingModuleData } from '../../types/weaving';
import { WeavingPage } from './shared';

export const FabricQualityPage: React.FC = () => (
  <WeavingPage description="First-grade share, defects, and which looms or styles are costing you grade">{(d) => <Body d={d} />}</WeavingPage>
);

const Body: React.FC<{ d: WeavingModuleData }> = ({ d }) => {
  const q = d.quality;
  const worstStyles = [...d.styles].sort((a, b) => a.grade_a_pct - b.grade_a_pct);
  return (
    <>
      <KpiGrid>
        <Kpi label="First grade (A)" value={pct(q.grade_a_pct)} status={q.grade_a_pct >= 94 ? 'ok' : 'warn'} hint="target 94%" />
        <Kpi label="Second grade (B)" value={pct(q.grade_b_pct)} />
        <Kpi label="Third grade / reject (C)" value={pct(q.grade_c_pct)} status={q.grade_c_pct > 2 ? 'bad' : undefined} />
        <Kpi label="Defects per 100 m" value={q.defects_per_100m.toFixed(2)} status={q.defects_per_100m > 2.8 ? 'warn' : 'ok'} />
        <Kpi label="Rejected fabric" value={meters(q.rejected_m)} />
        <Kpi label="Lost to downgrading" value={inrFromLakhs(q.downgrade_loss_lakhs)} hint="B sells ~18% lower, C ~45%" status="bad" />
      </KpiGrid>

      <div className="grid gap-4 lg:grid-cols-5">
        <Card className="lg:col-span-2">
          <CardHeader title="Grade split" subtitle={d.period_label} />
          <CardBody className="space-y-6">
            <SplitBar
              format={(v) => `${v.toFixed(1)}%`}
              parts={[
                { label: 'A', value: q.grade_a_pct, color: 1 },
                { label: 'B', value: q.grade_b_pct, color: 0 },
                { label: 'C', value: q.grade_c_pct, color: 2 },
              ]}
            />
            <div>
              <h3 className="mb-2 text-xs font-medium text-ink-3">Defect types</h3>
              <RankedBars items={q.defect_types.map((x) => ({ label: x.defect, value: x.count, share: x.share_pct }))} format={(v) => `${v.toLocaleString('en-IN')}`} />
            </div>
          </CardBody>
        </Card>
        <ChartPanel
          className="lg:col-span-3"
          title="First-grade share by day"
          subtitle="Against the 94% target"
          rows={d.trend}
          rowKey={(r) => r.date_label}
          exportName="weaving-grade-trend"
          chart={<TrendChart data={d.trend} xKey="date_label" format={(v) => `${v.toFixed(1)}%`} series={[{ key: 'grade_a_pct', label: 'First grade', color: 1 }]} reference={{ value: 94, label: 'Target' }} yDomain={[88, 98]} height={280} />}
          columns={[
            { key: 'd', header: 'Date', value: (r) => r.date_label, render: (r) => r.date_label },
            { key: 'g', header: 'First grade', align: 'right', value: (r) => r.grade_a_pct, render: (r) => pct(r.grade_a_pct) },
          ]}
        />
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader title="Looms with the most defects" subtitle="A single bad loom often points to a reed, beam or setting problem" />
          <DataTable
            rows={q.worst_looms}
            rowKey={(r) => r.loom_id}
            dense
            exportName="weaving-defect-looms"
            columns={[
              { key: 'l', header: 'Loom', value: (r) => r.loom_id, render: (r) => <Link to={{ pathname: '/weaving/looms', search: `?loom=${r.loom_id}` }} className="font-medium hover:underline">{r.loom_id}</Link> },
              { key: 's', header: 'Style', hideBelow: 'sm', value: (r) => r.style, render: (r) => r.style },
              { key: 'd', header: 'Defects / 100 m', align: 'right', value: (r) => r.defects_per_100m, render: (r) => r.defects_per_100m.toFixed(2) },
              { key: 'g', header: 'First grade', align: 'right', value: (r) => r.grade_a_pct, render: (r) => pct(r.grade_a_pct) },
              { key: 'x', header: '', render: (r) => (r.defects_per_100m > 3.5 ? <StatusPill tone="bad" label="Hold rolls" /> : r.defects_per_100m > 3.0 ? <StatusPill tone="warn" label="Watch" /> : null) },
            ]}
          />
        </Card>
        <Card>
          <CardHeader title="First grade by style" subtitle="Lowest first. A weak style may be a yarn or sizing issue." />
          <DataTable
            rows={worstStyles}
            rowKey={(r) => r.style}
            dense
            columns={[
              { key: 's', header: 'Style', value: (r) => r.style, render: (r) => <div><div className="font-medium">{r.style}</div><div className="text-xs text-ink-3">{r.fabric}</div></div> },
              { key: 'g', header: 'First grade', align: 'right', value: (r) => r.grade_a_pct, render: (r) => pct(r.grade_a_pct) },
              { key: 'm', header: 'Output', align: 'right', hideBelow: 'sm', value: (r) => r.meters, render: (r) => meters(r.meters) },
            ]}
          />
        </Card>
      </div>
    </>
  );
};
