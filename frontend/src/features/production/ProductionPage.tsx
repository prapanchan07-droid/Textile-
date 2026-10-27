import React from 'react';
import { useProduction } from '../../api/mill';
import { QueryView } from '../../design/QueryView';
import { ChartPanel } from '../../design/ChartPanel';
import { ColumnChart } from '../../design/charts/Charts';
import { Heatmap } from '../../design/viz/Heatmap';
import { goodHigh } from '../../design/viz/palette';
import { DataTable } from '../../design/DataTable';
import { Card, CardBody, CardHeader, Kpi, KpiGrid } from '../../design/ui';
import { meters, pct } from '../../lib/format';
import { FilterBar, useFilters } from '../common/filters';
import { FreshnessLine, NoData, PageTitle, fmt } from '../common/parts';

interface Cell { date: string; shift: string; meters: number | null; kilopicks: number | null; efficiency_pct: number | null; warp_stops_cmpx: number | null; weft_stops_cmpx: number | null; loom_shifts: number }

export const ProductionPage: React.FC = () => {
  const filters = useFilters();
  const q = useProduction(filters);
  return (
    <>
      <PageTitle title="Production and shift analytics" subtitle="Day × shift output, efficiency and stop rates, and the style mix behind them." actions={<FilterBar show={['category', 'shift', 'source', 'group']} />} />
      <QueryView query={q}>
        {(d) => {
          const cells: Cell[] = d.by_day_shift;
          const days: string[] = [...new Set(cells.map((c) => c.date))].sort();
          const perDay = days.map((day) => {
            const o: Record<string, unknown> = { date: day, day: day.slice(5) };
            cells.filter((c) => c.date === day).forEach((c) => { o[`m_${c.shift}`] = c.meters; o[`e_${c.shift}`] = c.efficiency_pct; });
            return o;
          });
          const heat = ['A', 'B', 'C'].map((s) => ({ label: `Shift ${s}`, values: days.map((day) => cells.find((c) => c.date === day && c.shift === s)?.efficiency_pct ?? null) }));
          const effVals = cells.map((c) => c.efficiency_pct).filter((v): v is number => v != null);
          const lo = effVals.length ? Math.min(...effVals) : 0;
          const hi = effVals.length ? Math.max(...effVals, lo + 1) : 100;
          const t = d.totals;
          return (
            <div className="space-y-5">
              <FreshnessLine freshness={d.freshness} period={d.period} />
              {t.loom_shifts === 0 && <NoData />}
              <KpiGrid>
                <Kpi label="Meters" value={t.meters == null ? '—' : `${fmt.n(t.meters)} m`} hint={`${fmt.n(t.coverage.meters)} loom-shifts with meters`} />
                <Kpi label="Kilopicks" value={fmt.n(t.kilopicks)} />
                <Kpi label="Efficiency" value={pct(t.efficiency_pct)} hint="time-weighted" />
                <Kpi label="m per loom-shift" value={fmt.n(t.meters_per_loom_shift, 1)} hint="per 480-minute shift" />
                <Kpi label="Warp /100k picks" value={fmt.rate(t.warp_stops_cmpx)} hint={`${fmt.n(t.coverage.warp_stops)} loom-shifts with warp counts`} />
                <Kpi label="Weft /100k picks" value={fmt.rate(t.weft_stops_cmpx)} />
              </KpiGrid>
              <ChartPanel title="Meters by day and shift" subtitle="Sum of loom-shifts"
                chart={<ColumnChart data={perDay} xKey="day" series={[{ key: 'm_A', label: 'Shift A', color: 0 }, { key: 'm_B', label: 'Shift B', color: 1 }, { key: 'm_C', label: 'Shift C', color: 2 }]} format={(v) => meters(v)} height={240} />}
                rows={cells} rowKey={(c) => `${c.date}${c.shift}`} exportName="production-day-shift"
                columns={[
                  { key: 'd', header: 'Date', render: (c) => fmt.date(c.date), value: (c) => c.date },
                  { key: 's', header: 'Shift', render: (c) => c.shift, value: (c) => c.shift },
                  { key: 'm', header: 'Meters', align: 'right', render: (c) => fmt.n(c.meters), value: (c) => c.meters },
                  { key: 'kp', header: 'Kilopicks', align: 'right', render: (c) => fmt.n(c.kilopicks), value: (c) => c.kilopicks },
                  { key: 'e', header: 'Efficiency', align: 'right', render: (c) => pct(c.efficiency_pct), value: (c) => c.efficiency_pct },
                  { key: 'w', header: 'Warp /100k', align: 'right', render: (c) => fmt.rate(c.warp_stops_cmpx), value: (c) => c.warp_stops_cmpx },
                  { key: 'f', header: 'Weft /100k', align: 'right', render: (c) => fmt.rate(c.weft_stops_cmpx), value: (c) => c.weft_stops_cmpx },
                  { key: 'n', header: 'Loom-shifts', align: 'right', render: (c) => c.loom_shifts, value: (c) => c.loom_shifts },
                ]} />
              {days.length > 1 && (
                <Card>
                  <CardHeader title="Efficiency heatmap" subtitle="Each cell: time-weighted efficiency of all looms in that shift, coloured from the period's lowest to highest." />
                  <CardBody><Heatmap rows={heat} columns={days.map((x) => x.slice(5))} format={(v) => pct(v, 1)} showValues={days.length <= 31} cell={34} columnEvery={days.length > 20 ? 2 : 1}
                    color={(v) => goodHigh(v, lo, hi)} legend={{ low: pct(lo, 0), high: pct(hi, 0), swatches: [goodHigh(lo, lo, hi), goodHigh((lo + hi) / 2, lo, hi), goodHigh(hi, lo, hi)] }} /></CardBody>
                </Card>
              )}
              <div className="grid gap-4 xl:grid-cols-2">
                <Card>
                  <CardHeader title="Category × shift" subtitle="Compare shifts within a category; categories differ in machine type and width" />
                  <CardBody>
                    <DataTable dense rows={d.by_category_shift} rowKey={(r: { category: string; shift: string }) => r.category + r.shift} exportName="category-shift"
                      columns={[
                        { key: 'c', header: 'Category', render: (r: any) => r.category, value: (r: any) => r.category },
                        { key: 's', header: 'Shift', render: (r: any) => r.shift, value: (r: any) => r.shift },
                        { key: 'e', header: 'Efficiency', align: 'right', render: (r: any) => pct(r.efficiency_pct), value: (r: any) => r.efficiency_pct },
                        { key: 'm', header: 'Meters', align: 'right', render: (r: any) => fmt.n(r.meters), value: (r: any) => r.meters },
                        { key: 'w', header: 'Warp /100k', align: 'right', render: (r: any) => fmt.rate(r.warp_stops_cmpx), value: (r: any) => r.warp_stops_cmpx },
                        { key: 'f', header: 'Weft /100k', align: 'right', render: (r: any) => fmt.rate(r.weft_stops_cmpx), value: (r: any) => r.weft_stops_cmpx },
                      ]} />
                  </CardBody>
                </Card>
                <Card>
                  <CardHeader title="Style mix" subtitle="Fabric descriptions as grouped in the mill report" />
                  <CardBody>
                    <DataTable dense rows={d.by_style} rowKey={(r: any) => String(r.style)} exportName="styles" searchable={(r: any) => `${r.style} ${r.description ?? ''}`}
                      columns={[
                        { key: 's', header: 'Style', render: (r: any) => <span title={r.description ?? ''}>{r.style ?? '—'}</span>, value: (r: any) => r.style },
                        { key: 'cat', header: 'On', render: (r: any) => r.categories.join(', '), value: (r: any) => r.categories.join(',') },
                        { key: 'l', header: 'Looms', align: 'right', render: (r: any) => r.looms, value: (r: any) => r.looms },
                        { key: 'm', header: 'Meters', align: 'right', render: (r: any) => fmt.n(r.meters), value: (r: any) => r.meters },
                        { key: 'e', header: 'Efficiency', align: 'right', render: (r: any) => pct(r.efficiency_pct), value: (r: any) => r.efficiency_pct },
                        { key: 'f', header: 'Weft /100k', align: 'right', render: (r: any) => fmt.rate(r.weft_stops_cmpx), value: (r: any) => r.weft_stops_cmpx, hideBelow: 'md' },
                      ]} />
                  </CardBody>
                </Card>
              </div>
            </div>
          );
        }}
      </QueryView>
    </>
  );
};
