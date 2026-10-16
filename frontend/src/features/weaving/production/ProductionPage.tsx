import React from 'react';
import { Link } from 'react-router-dom';
import { useProduction } from '../../../api/weaving';
import { usePeriod } from '../../../app/state';
import { cn, num, pct } from '../../../lib/format';
import { PageHeader } from '../../../layout/PageHeader';
import { Card, CardBody, CardHeader } from '../../../design/ui';
import { DataTable } from '../../../design/DataTable';
import { TrendChart } from '../../../design/charts/Charts';
import { StatGrid } from '../../../design/viz/StatTile';
import { ForecastChart, Waterfall } from '../../../design/viz/charts2';
import { Heatmap } from '../../../design/viz/Heatmap';
import { goodHigh } from '../../../design/viz/palette';
import { HealthRing } from '../../../design/viz/parts';
import { Load, Section } from '../common';
import type { LoomPerf } from '../../../types/pages';

const LoomRank: React.FC<{ rows: LoomPerf[]; tone: 'good' | 'bad' }> = ({ rows, tone }) => (
  <div className="space-y-2 px-5 pb-4">
    {rows.map((r) => (
      <Link key={r.loom} to={`/weaving/machines?loom=${r.loom}`} className="block rounded-lg px-2 py-1.5 hover:bg-subtle">
        <div className="flex items-center justify-between text-sm">
          <span className="font-medium text-ink">{r.loom} <span className="text-xs font-normal text-ink-3">{r.type} · {r.style}</span></span>
          <span className={cn('num font-semibold', tone === 'good' ? 'text-ok' : 'text-bad')}>{pct(r.efficiency_pct)}</span>
        </div>
        <div className="mt-1 h-1.5 overflow-hidden rounded-full bg-muted"><div className={cn('h-full rounded-full', tone === 'good' ? 'bg-ok' : 'bg-bad')} style={{ width: `${Math.max(0, Math.min(100, ((r.efficiency_pct ?? 0) - 60) * 2.5))}%` }} /></div>
        <div className="mt-0.5 text-xs text-ink-3">{num(r.meters)} m · {r.stops_per_100k?.toFixed(2) ?? '—'} stops per 100k picks</div>
      </Link>
    ))}
  </div>
);

export const ProductionPage: React.FC = () => {
  const [period] = usePeriod();
  const q = useProduction(period);
  return (
    <>
      <PageHeader title="Production" description="Output, efficiency and where the capacity went, from the looms' own pick counters." showPeriod />
      <Load q={q}>
        {(d) => (
          <>
            <StatGrid items={d.kpis} />
            <div className="grid gap-4 xl:grid-cols-2">
              <Card>
                <CardHeader title="Output and the week ahead" subtitle="Metres per production day against the style targets, with a forecast that shows its own past error" />
                <CardBody><ForecastChart history={d.trend} forecast={d.forecast} /></CardBody>
              </Card>
              <Card>
                <CardHeader title="Where the loom-hours went" subtitle="From scheduled hours to effective weaving hours. Every bar is a place to win time back." />
                <CardBody><Waterfall items={d.waterfall} format={(v) => `${Math.round(v).toLocaleString('en-IN')} h`} /></CardBody>
              </Card>
            </div>
            <Card>
              <CardHeader title="Efficiency, loom by loom, day by day" subtitle="Red is low, green is high. A loom that goes red and stays red needs a look; a red column is a floor-wide problem day." />
              <CardBody>
                <Heatmap
                  columns={d.heatmap.days}
                  rows={d.heatmap.rows.map((r) => ({ label: r.loom, sublabel: r.type, values: r.values }))}
                  color={(v) => goodHigh(v, 72, 94)}
                  format={(v) => `${v.toFixed(1)}%`}
                  cell={30}
                  showValues
                  columnEvery={1}
                  legend={{ low: '72%', high: '94%', swatches: [goodHigh(72, 72, 94), goodHigh(80, 72, 94), goodHigh(88, 72, 94), goodHigh(94, 72, 94)] }}
                />
              </CardBody>
            </Card>
            <div className="grid gap-4 xl:grid-cols-2">
              <Card><CardHeader title="Leaders" subtitle="Highest efficiency this period" /><LoomRank rows={d.leaders} tone="good" /></Card>
              <Card><CardHeader title="Needs attention" subtitle="Lowest efficiency this period" /><LoomRank rows={d.laggards} tone="bad" /></Card>
            </div>
            <div className="grid gap-4 xl:grid-cols-3">
              <Card className="xl:col-span-1">
                <CardHeader title="Shifts" />
                <DataTable dense rows={d.shifts} rowKey={(r) => r.shift} columns={[
                  { key: 's', header: 'Shift', value: (r) => r.shift, render: (r) => <span className="font-medium">{r.shift}</span> },
                  { key: 'm', header: 'Output', value: (r) => r.meters, render: (r) => `${num(r.meters)} m`, align: 'right' },
                  { key: 'e', header: 'Eff.', value: (r) => r.efficiency_pct, render: (r) => pct(r.efficiency_pct), align: 'right' },
                ]} />
              </Card>
              <Card className="xl:col-span-1">
                <CardHeader title="Loom types" />
                <DataTable dense rows={d.loom_types} rowKey={(r) => r.type} columns={[
                  { key: 't', header: 'Type', value: (r) => r.type, render: (r) => <span className="font-medium">{r.type} <span className="text-xs font-normal text-ink-3">{r.looms} looms</span></span> },
                  { key: 'm', header: 'Output', value: (r) => r.meters, render: (r) => `${num(r.meters)} m`, align: 'right' },
                  { key: 'e', header: 'Eff.', value: (r) => r.efficiency_pct, render: (r) => pct(r.efficiency_pct), align: 'right' },
                ]} />
              </Card>
              <Card className="xl:col-span-1">
                <CardHeader title="Styles" subtitle="Against each style's own target" />
                <DataTable dense rows={d.styles} rowKey={(r) => r.style} columns={[
                  { key: 's', header: 'Style', value: (r) => r.style, render: (r) => <span className="font-medium">{r.style}</span> },
                  { key: 'm', header: 'Output', value: (r) => r.meters, render: (r) => `${num(r.meters)} m`, align: 'right' },
                  { key: 'a', header: 'vs target', value: (r) => r.achievement_pct, render: (r) => <span className={cn((r.achievement_pct ?? 100) < 96 ? 'text-bad' : 'text-ok')}>{pct(r.achievement_pct)}</span>, align: 'right' },
                ]} />
              </Card>
            </div>
            <Section title="All looms" hint="click a loom to open its machine record">
              <Card>
                <DataTable
                  rows={d.looms}
                  rowKey={(r) => r.loom}
                  searchable={(r) => `${r.loom} ${r.type} ${r.style}`}
                  searchPlaceholder="Search looms"
                  exportName="looms-production"
                  initialSort={{ key: 'e', dir: 'asc' }}
                  columns={[
                    { key: 'l', header: 'Loom', value: (r) => r.loom, render: (r) => <Link to={`/weaving/machines?loom=${r.loom}`} className="font-semibold hover:text-accent">{r.loom}</Link> },
                    { key: 't', header: 'Type', value: (r) => r.type, render: (r) => r.type, hideBelow: 'md' },
                    { key: 'st', header: 'Style', value: (r) => r.style, render: (r) => r.style, hideBelow: 'md' },
                    { key: 'm', header: 'Output', value: (r) => r.meters, render: (r) => `${num(r.meters)} m`, align: 'right' },
                    { key: 'a', header: 'vs target', value: (r) => r.achievement_pct, render: (r) => pct(r.achievement_pct), align: 'right' },
                    { key: 'e', header: 'Efficiency', value: (r) => r.efficiency_pct, render: (r) => <b>{pct(r.efficiency_pct)}</b>, align: 'right' },
                    { key: 'u', header: 'Utilization', value: (r) => r.utilization_pct, render: (r) => pct(r.utilization_pct), align: 'right', hideBelow: 'lg' },
                    { key: 's', header: 'Stops / 100k', value: (r) => r.stops_per_100k, render: (r) => r.stops_per_100k?.toFixed(2) ?? '—', align: 'right', hideBelow: 'lg' },
                    { key: 'k', header: 'kWh / 100 m', value: (r) => r.kwh_per_100m, render: (r) => r.kwh_per_100m?.toFixed(1) ?? '—', align: 'right', hideBelow: 'xl' },
                    { key: 'h', header: 'Health', value: (r) => r.health, render: (r) => <HealthRing score={r.health} size={32} />, align: 'center', hideBelow: 'md' },
                  ]}
                />
              </Card>
            </Section>
          </>
        )}
      </Load>
    </>
  );
};
