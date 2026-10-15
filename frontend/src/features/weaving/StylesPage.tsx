import React from 'react';
import { inrFromLakhs, meters, pct } from '../../lib/format';
import { Card, CardHeader, Kpi, KpiGrid, Meter, StatusPill } from '../../design/ui';
import { DataTable } from '../../design/DataTable';
import { ChartPanel } from '../../design/ChartPanel';
import { ColumnChart } from '../../design/charts/Charts';
import type { WeavingModuleData, WeavingStyle } from '../../types/weaving';
import { CALL_LABEL, callTone, WeavingPage } from './shared';

export const StylesPage: React.FC = () => (
  <WeavingPage description="Cost, margin and a clear call for every fabric style">{(d) => <Body d={d} />}</WeavingPage>
);

const Body: React.FC<{ d: WeavingModuleData }> = ({ d }) => {
  const total = d.styles.reduce((s, x) => s + x.profit_lakhs, 0);
  const best = d.styles[0];
  const worst = d.styles[d.styles.length - 1];
  const act = d.styles.filter((s) => s.recommendation === 'STOP' || s.recommendation === 'REPRICE');
  return (
    <>
      <KpiGrid>
        <Kpi label="Weaving profit" value={inrFromLakhs(total)} hint={`${d.period_label.toLowerCase()}, after cost`} status={total > 0 ? 'ok' : 'bad'} />
        <Kpi label="Best style" value={best.style} hint={`${pct(best.margin_pct)} margin`} status="ok" />
        <Kpi label="Weakest style" value={worst.style} hint={`${pct(worst.margin_pct)} margin`} status={worst.margin_pct < 3 ? 'bad' : 'warn'} />
        <Kpi label="Need a pricing call" value={String(act.length)} hint="reprice or stop" status={act.length ? 'warn' : 'ok'} />
        <Kpi label="Styles running" value={String(d.styles.length)} />
        <Kpi label="Fabric made" value={meters(d.kpis.fabric_m)} />
      </KpiGrid>

      <Card>
        <CardHeader
          title="Style scorecard"
          subtitle="Cost includes the fixed share, which rises when looms run below target. Margin is after downgrading losses."
        />
        <DataTable<WeavingStyle>
          rows={d.styles}
          rowKey={(r) => r.style}
          exportName="weaving-styles"
          columns={[
            { key: 's', header: 'Style', value: (r) => r.style, render: (r) => <div><div className="font-medium">{r.style}</div><div className="text-xs text-ink-3">{r.fabric}</div></div> },
            { key: 'o', header: 'Output', align: 'right', hideBelow: 'md', value: (r) => r.meters, render: (r) => meters(r.meters) },
            { key: 'r', header: 'Rate / m', align: 'right', hideBelow: 'sm', value: (r) => r.rate_per_m, render: (r) => `₹${r.rate_per_m.toFixed(0)}` },
            { key: 'c', header: 'Cost / m', align: 'right', hideBelow: 'sm', value: (r) => r.cost_per_m, render: (r) => `₹${r.cost_per_m.toFixed(0)}` },
            {
              key: 'm',
              header: 'Margin',
              value: (r) => r.margin_pct,
              render: (r) => (
                <div className="flex w-36 items-center gap-2">
                  <Meter value={Math.max(r.margin_pct, 0)} max={30} tone={callTone(r.recommendation) === 'neutral' ? 'info' : callTone(r.recommendation)} />
                  <span className="num w-12 text-right text-xs">{pct(r.margin_pct)}</span>
                </div>
              ),
            },
            { key: 'p', header: 'Profit', align: 'right', value: (r) => r.profit_lakhs, render: (r) => inrFromLakhs(r.profit_lakhs) },
            { key: 'e', header: 'Loom eff.', align: 'right', hideBelow: 'lg', value: (r) => r.efficiency_pct, render: (r) => pct(r.efficiency_pct) },
            { key: 'k', header: 'Call', value: (r) => r.recommendation, render: (r) => <StatusPill tone={callTone(r.recommendation)} label={CALL_LABEL[r.recommendation]} /> },
          ]}
        />
      </Card>

      <div className="grid gap-4 lg:grid-cols-5">
        <ChartPanel
          className="lg:col-span-3"
          title="Rate against cost per metre"
          subtitle="The gap between the bars is your margin"
          rows={d.styles}
          rowKey={(r) => r.style}
          exportName="weaving-rate-cost"
          chart={
            <ColumnChart
              // Not `style`: recharts copies row fields onto SVG elements, and a string `style` crashes React.
              data={d.styles.map((s) => ({ name: s.style, rate_per_m: s.rate_per_m, cost_per_m: s.cost_per_m }))}
              xKey="name"
              format={(v) => `₹${v.toFixed(0)}`}
              series={[
                { key: 'rate_per_m', label: 'Rate', color: 1 },
                { key: 'cost_per_m', label: 'Cost', color: 'muted' },
              ]}
            />
          }
          columns={[
            { key: 's', header: 'Style', value: (r) => r.style, render: (r) => r.style },
            { key: 'r', header: 'Rate', align: 'right', value: (r) => r.rate_per_m, render: (r) => `₹${r.rate_per_m.toFixed(0)}` },
            { key: 'c', header: 'Cost', align: 'right', value: (r) => r.cost_per_m, render: (r) => `₹${r.cost_per_m.toFixed(0)}` },
          ]}
        />
        <Card className="lg:col-span-2">
          <CardHeader title="What to do about each style" />
          <ul className="divide-y divide-line border-t border-line">
            {d.styles.map((s) => (
              <li key={s.style} className="px-5 py-3">
                <div className="flex items-center justify-between gap-2">
                  <span className="text-sm font-medium text-ink">
                    {s.style} <span className="font-normal text-ink-3">{s.fabric}</span>
                  </span>
                  <StatusPill tone={callTone(s.recommendation)} label={CALL_LABEL[s.recommendation]} />
                </div>
                <p className="mt-1 text-xs text-ink-3">{s.reason}</p>
              </li>
            ))}
          </ul>
        </Card>
      </div>
    </>
  );
};
