import React from 'react';
import { Link } from 'react-router-dom';
import { useStoppages } from '../../../api/weaving';
import { usePeriod } from '../../../app/state';
import { cn } from '../../../lib/format';
import { PageHeader } from '../../../layout/PageHeader';
import { Card, CardBody, CardHeader } from '../../../design/ui';
import { DataTable } from '../../../design/DataTable';
import { StatGrid } from '../../../design/viz/StatTile';
import { Pareto, StackedColumns } from '../../../design/viz/charts2';
import { Heatmap } from '../../../design/viz/Heatmap';
import { CATEGORY_COLORS, sequential } from '../../../design/viz/palette';
import { FindingCard } from '../../../design/viz/parts';
import { Load, Section, Pill } from '../common';

const label = (c: string) => c.charAt(0) + c.slice(1).toLowerCase().replace(/_/g, ' ');

export const StoppagesPage: React.FC = () => {
  const [period] = usePeriod();
  const q = useStoppages(period);
  return (
    <>
      <PageHeader title="Stoppages" description="Why the looms stop, when, where, and what to fix first." showPeriod />
      <Load q={q}>
        {(d) => {
          const maxHeat = Math.max(1, ...d.heatmap.grid.flat());
          const maxCell = Math.max(1, ...d.matrix.rows.flatMap((r) => Object.values(r.cells)));
          return (
            <>
              <StatGrid items={d.kpis} />
              <div className="grid gap-4 xl:grid-cols-5">
                <Card className="xl:col-span-3">
                  <CardHeader title="Pareto of downtime" subtitle="Minutes lost by cause. The line shows the running share: the few causes left of the dotted 80% line are where the effort belongs." />
                  <CardBody>
                    <Pareto items={d.pareto.map((p) => ({ label: p.cause, value: p.downtime_min, cumulative: p.cumulative_pct, planned: p.planned, color: CATEGORY_COLORS[p.category] }))} valueLabel="Minutes" />
                  </CardBody>
                </Card>
                <Card className="xl:col-span-2">
                  <CardHeader title="Cause by cause" subtitle="Rate, length and the estimated loss" />
                  <div className="max-h-[360px] overflow-auto">
                    <DataTable dense rows={d.pareto} rowKey={(r) => r.cause} columns={[
                      { key: 'c', header: 'Cause', value: (r) => r.cause, render: (r) => <span className="font-medium">{r.cause} {r.planned && <Pill>planned</Pill>}</span> },
                      { key: 'n', header: 'Stops', value: (r) => r.stops, render: (r) => r.stops.toLocaleString('en-IN'), align: 'right' },
                      { key: 'a', header: 'Avg min', value: (r) => r.avg_min, render: (r) => r.avg_min?.toFixed(1) ?? '—', align: 'right' },
                      { key: 'k', header: '/ 100k', value: (r) => r.per_100k, render: (r) => r.per_100k?.toFixed(2) ?? '—', align: 'right' },
                      { key: 'l', header: 'Lost m', value: (r) => r.est_lost_m, render: (r) => r.est_lost_m.toLocaleString('en-IN'), align: 'right' },
                    ]} />
                  </div>
                </Card>
              </div>
              <div className="grid gap-4 xl:grid-cols-2">
                <Card>
                  <CardHeader title="Downtime by day" subtitle="Unplanned minutes, stacked by cause family" />
                  <CardBody><StackedColumns rows={d.daily_by_category.rows} categories={d.daily_by_category.categories} /></CardBody>
                </Card>
                <Card>
                  <CardHeader title="When stops happen" subtitle={`Stops by hour of the day (mill time) and weekday, ${d.heatmap.window}. Darker means more.`} />
                  <CardBody>
                    <Heatmap
                      columns={d.heatmap.hours.map((h) => String(h).padStart(2, '0'))}
                      rows={d.heatmap.days.map((day, i) => ({ label: day, values: d.heatmap.grid[i] }))}
                      color={(v) => sequential(v, maxHeat)}
                      format={(v) => `${v} stops`}
                      cell={21}
                      labelWidth={40}
                      columnEvery={2}
                      legend={{ low: 'few', high: 'many', swatches: [sequential(0, 4), sequential(1, 4), sequential(2, 4), sequential(3, 4), sequential(4, 4)] }}
                    />
                  </CardBody>
                </Card>
              </div>
              <div className="grid gap-4 xl:grid-cols-2">
                <Card>
                  <CardHeader title="Worst looms by cause" subtitle="Downtime minutes. Look for one dark cell in a row: that is a loom with one problem, and a fault to fix." />
                  <CardBody>
                    <Heatmap
                      columns={d.matrix.categories.map(label)}
                      rows={d.matrix.rows.map((r) => ({ label: r.loom, values: d.matrix.categories.map((c) => r.cells[c] ?? 0) }))}
                      color={(v) => sequential(v, maxCell)}
                      format={(v) => `${v} min`}
                      cell={62}
                      labelWidth={56}
                      showValues
                    />
                  </CardBody>
                </Card>
                <Card>
                  <CardHeader title="Shift by cause" subtitle="Do the shifts lose time to the same things?" />
                  <CardBody>
                    <Heatmap
                      columns={d.by_shift.categories.map(label)}
                      rows={d.by_shift.rows.map((r) => ({ label: r.shift, values: d.by_shift.categories.map((c) => r.cells[c] ?? 0) }))}
                      color={(v) => sequential(v, Math.max(1, ...d.by_shift.rows.flatMap((r) => Object.values(r.cells))))}
                      format={(v) => `${v} min`}
                      cell={62}
                      labelWidth={64}
                      showValues
                    />
                  </CardBody>
                </Card>
              </div>
              <Section title={`Stopped right now · ${d.open_now.length}`}>
                <Card>
                  <DataTable dense rows={d.open_now} rowKey={(r) => r.loom} emptyTitle="No loom is stopped" columns={[
                    { key: 'l', header: 'Loom', value: (r) => r.loom, render: (r) => <Link to={`/weaving/machines?loom=${r.loom}`} className="font-semibold hover:text-accent">{r.loom}</Link> },
                    { key: 'r', header: 'Reason', value: (r) => r.reason, render: (r) => <span>{r.reason} {r.planned && <Pill>planned</Pill>}</span> },
                    { key: 'm', header: 'Stopped for', value: (r) => r.minutes, render: (r) => <b className={cn(r.minutes > 20 && !r.planned && 'text-bad')}>{r.minutes} min</b>, align: 'right' },
                    { key: 'f', header: 'Fitter', value: (r) => r.fitter ?? '', render: (r) => r.fitter ?? '—', hideBelow: 'md' },
                    { key: 'w', header: 'Machine watch', value: (r) => r.watch ?? '', render: (r) => (r.watch ? <span className="text-warn">{r.watch}</span> : <span className="text-ink-3">—</span>), hideBelow: 'lg' },
                  ]} />
                </Card>
              </Section>
              {d.repeat.length > 0 && (
                <Section title="Repeat offenders" ai hint="the same loom stopping for the same reason, day after day">
                  <div className="space-y-2.5">{d.repeat.map((f) => <FindingCard key={f.key} f={f} />)}</div>
                </Section>
              )}
              <p className="text-xs text-ink-3">{d.notes.join(' ')}</p>
            </>
          );
        }}
      </Load>
    </>
  );
};
