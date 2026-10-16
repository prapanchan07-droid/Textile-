import React from 'react';
import { Link } from 'react-router-dom';
import { useQuality } from '../../../api/weaving';
import { usePeriod } from '../../../app/state';
import { cn, num, pct } from '../../../lib/format';
import { PageHeader } from '../../../layout/PageHeader';
import { Card, CardBody, CardHeader } from '../../../design/ui';
import { DataTable } from '../../../design/DataTable';
import { TrendChart } from '../../../design/charts/Charts';
import { StatGrid } from '../../../design/viz/StatTile';
import { StackedColumns } from '../../../design/viz/charts2';
import { Heatmap } from '../../../design/viz/Heatmap';
import { badHigh, catColor } from '../../../design/viz/palette';
import { FindingCard } from '../../../design/viz/parts';
import { Hero, Load, Pill, Section } from '../common';

const GRADE: Record<string, 'ok' | 'warn' | 'bad'> = { A: 'ok', B: 'warn', C: 'bad', REJECT: 'bad' };

export const QualityPage: React.FC = () => {
  const [period] = usePeriod('LAST_7_DAYS');
  const q = useQuality(period);
  return (
    <>
      <PageHeader title="Quality Desk" description="Where defects come from: which shift, which style, which yarn, which loom." showPeriod defaultPeriod="LAST_7_DAYS" />
      <Load q={q}>
        {(d) => {
          const types = d.defect_types;
          const stackRows = d.by_shift.map((r) => ({ label: String(r.shift), ...Object.fromEntries(types.map((t) => [t, Number(r[t] ?? 0)])) }));
          const flagged = d.yarn_lots.filter((l) => l.flagged);
          return (
            <>
              <Hero
                eyebrow="Quality brief"
                tone={d.findings.some((f) => f.severity === 'HIGH') ? 'bad' : 'ok'}
                title={d.findings.length ? d.findings[0].title + '.' : 'No unusual defect pattern right now.'}
                aside={flagged.length ? <div className="rounded-2xl bg-white/[0.09] p-4 text-sm text-white/90 backdrop-blur"><div className="mb-1 text-xs font-medium uppercase tracking-wide text-white/70">Yarn lot under suspicion</div><b className="text-lg">{flagged.map((l) => l.lot).join(', ')}</b><p className="mt-1 text-xs leading-5 text-white/75">{flagged[0].supplier}: strength {flagged[0].strength_cn_tex} cN/tex, CV {flagged[0].cv_pct}%, size pick-up {flagged[0].size_pickup_pct}%. A weaker lot is evidence worth testing, not proof.</p></div> : undefined}
              />
              <StatGrid items={d.kpis} />
              <div className="grid gap-4 xl:grid-cols-2">
                <Card>
                  <CardHeader title="Defects per 100 m, day by day" subtitle="Inspected rolls only" />
                  <CardBody><TrendChart data={d.trend} xKey="label" series={[{ key: 'defects_per_100m', label: 'Defects per 100 m', color: 1 }]} format={(v) => v.toFixed(2)} area /></CardBody>
                </Card>
                <Card>
                  <CardHeader title="What the defects are, by shift" subtitle="Defects per 100 m inspected, stacked by type" />
                  <CardBody><StackedColumns rows={stackRows} categories={types} xKey="label" unit="/100 m" labels={Object.fromEntries(types.map((t) => [t, t]))} /></CardBody>
                </Card>
              </div>
              <Card>
                <CardHeader title="Style against shift" subtitle="Defects per 100 m. One hot cell in a style's row means that shift handles that style differently." />
                <CardBody>
                  <Heatmap
                    columns={d.style_shift.shifts}
                    rows={d.style_shift.rows.map((r) => ({ label: r.style, values: d.style_shift.shifts.map((s) => r.cells[s] ?? null) }))}
                    color={(v) => badHigh(v, 1.5, 6)}
                    format={(v) => v.toFixed(2)}
                    cell={92}
                    labelWidth={64}
                    showValues
                    legend={{ low: '1.5', high: '6+', swatches: [badHigh(1.5, 1.5, 6), badHigh(3, 1.5, 6), badHigh(4.5, 1.5, 6), badHigh(6, 1.5, 6)] }}
                  />
                </CardBody>
              </Card>
              <Section title="Yarn lots" hint={`incoming tests next to what happened on the loom, last 14 days · worst ${d.yarn_lots.length} of ${d.yarn_lots_total}`}>
                <Card>
                  <DataTable dense rows={d.yarn_lots} rowKey={(r) => r.lot} initialSort={{ key: 'w', dir: 'desc' }} columns={[
                    { key: 'l', header: 'Lot', value: (r) => r.lot, render: (r) => <span className="font-semibold">{r.lot} {r.flagged && <Pill tone="bad">flagged</Pill>}</span> },
                    { key: 's', header: 'Supplier', value: (r) => r.supplier ?? '', render: (r) => r.supplier, hideBelow: 'md' },
                    { key: 'st', header: 'Style', value: (r) => r.style ?? '', render: (r) => r.style, hideBelow: 'md' },
                    { key: 'sg', header: 'Strength (cN/tex)', value: (r) => r.strength_cn_tex, render: (r) => r.strength_cn_tex?.toFixed(1), align: 'right' },
                    { key: 'cv', header: 'CV %', value: (r) => r.cv_pct, render: (r) => r.cv_pct?.toFixed(1), align: 'right', hideBelow: 'md' },
                    { key: 'sp', header: 'Size pick-up %', value: (r) => r.size_pickup_pct, render: (r) => r.size_pickup_pct?.toFixed(1) ?? '—', align: 'right', hideBelow: 'md' },
                    { key: 'b', header: 'Beams', value: (r) => r.beams, render: (r) => r.beams, align: 'right', hideBelow: 'lg' },
                    { key: 'w', header: 'Warp stops / 100k', value: (r) => r.warp_stops_per_100k, render: (r) => <b className={cn(r.flagged && 'text-bad')}>{r.warp_stops_per_100k?.toFixed(2)}</b>, align: 'right' },
                    { key: 'e', header: 'Efficiency', value: (r) => r.efficiency_pct, render: (r) => pct(r.efficiency_pct), align: 'right', hideBelow: 'lg' },
                  ]} />
                </Card>
              </Section>
              <div className="grid gap-4 xl:grid-cols-2">
                <Card>
                  <CardHeader title="Looms with the most defects" subtitle="At least 150 m inspected" />
                  <DataTable dense rows={d.worst_looms} rowKey={(r) => r.loom} columns={[
                    { key: 'l', header: 'Loom', value: (r) => r.loom, render: (r) => <Link to={`/weaving/machines?loom=${r.loom}`} className="font-semibold hover:text-accent">{r.loom}</Link> },
                    { key: 'd', header: 'Defects / 100 m', value: (r) => r.defects_per_100m, render: (r) => r.defects_per_100m?.toFixed(2), align: 'right' },
                    { key: 'g', header: 'First grade', value: (r) => r.grade_a_pct, render: (r) => pct(r.grade_a_pct, 0), align: 'right' },
                    { key: 'i', header: 'Inspected', value: (r) => r.inspected_m, render: (r) => `${num(r.inspected_m)} m`, align: 'right', hideBelow: 'md' },
                  ]} />
                </Card>
                <Card>
                  <CardHeader title="Recent rolls below first grade" />
                  <DataTable dense rows={d.recent_rolls} rowKey={(r) => r.roll_no} columns={[
                    { key: 'r', header: 'Roll', value: (r) => r.roll_no, render: (r) => <span className="font-medium">{r.roll_no}</span> },
                    { key: 's', header: 'Style · shift', value: (r) => r.style, render: (r) => <span className="text-ink-2">{r.style} · {r.shift}</span>, hideBelow: 'md' },
                    { key: 'd', header: 'Defects', value: (r) => r.defects, render: (r) => `${r.defects} (${r.points} pts)`, align: 'right' },
                    { key: 'g', header: 'Grade', value: (r) => r.grade, render: (r) => <Pill tone={GRADE[r.grade]}>{r.grade}</Pill> },
                  ]} />
                </Card>
              </div>
              {d.findings.length > 0 && (
                <Section title="What the AI found" ai hint="with the evidence behind each">
                  <div className="space-y-2.5">{d.findings.map((f, i) => <FindingCard key={f.key} f={f} defaultOpen={i === 0} showMoney={false} />)}</div>
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
