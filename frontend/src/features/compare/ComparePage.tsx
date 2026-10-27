import React from 'react';
import { Link } from 'react-router-dom';
import { useCompare } from '../../api/mill';
import { useParam } from '../../app/state';
import { QueryView } from '../../design/QueryView';
import { DataTable, type Column } from '../../design/DataTable';
import { Card, CardBody, CardHeader, Notice, Segmented } from '../../design/ui';
import { pct } from '../../lib/format';
import { FilterBar, useFilters } from '../common/filters';
import { PageTitle, SourceBadge, fmt, periodText } from '../common/parts';

type Dim = 'loom' | 'shift' | 'style' | 'category' | 'width' | 'group' | 'date';

interface Row {
  key: string; loom_id: number | null; cohort: string | null; sources: string[]; loom_shifts: number; looms: number; meters: number | null; kilopicks: number | null;
  efficiency_pct: number | null; warp_stops_cmpx: number | null; weft_stops_cmpx: number | null; meters_per_loom_shift: number | null;
  cohort_size?: number; vs_cohort_pts?: number | null; coverage: Record<string, number>;
}

export const ComparePage: React.FC = () => {
  const filters = useFilters();
  const [dim, setDim] = useParam('by', 'loom');
  const q = useCompare({ ...filters, dimension: dim });
  const cols: Column<Row>[] = [
    { key: 'key', header: dim === 'loom' ? 'Loom' : dim[0].toUpperCase() + dim.slice(1),
      render: (r) => (r.loom_id ? <Link to={`/looms/${r.loom_id}`} className="font-medium text-ink hover:text-accent">{r.key}</Link> : <span className="font-medium text-ink">{dim === 'date' ? fmt.date(r.key) : r.key}</span>), value: (r) => r.key },
    ...(dim === 'loom' ? [
      { key: 'cohort', header: 'Peer group', render: (r: Row) => <span className="text-xs text-ink-3">{r.cohort}</span>, value: (r: Row) => r.cohort, hideBelow: 'lg' as const },
      { key: 'vs', header: 'vs peers', align: 'right' as const, render: (r: Row) => (r.vs_cohort_pts == null ? <span className="text-ink-3" title="Fewer than 3 comparable looms">n/a</span> : <span className={r.vs_cohort_pts <= -3 ? 'text-bad' : r.vs_cohort_pts >= 3 ? 'text-ok' : ''}>{r.vs_cohort_pts > 0 ? '+' : ''}{r.vs_cohort_pts.toFixed(1)} pts</span>), value: (r: Row) => r.vs_cohort_pts },
    ] : [{ key: 'looms', header: 'Looms', align: 'right' as const, render: (r: Row) => r.looms, value: (r: Row) => r.looms }]),
    { key: 'eff', header: 'Efficiency', align: 'right', render: (r) => pct(r.efficiency_pct), value: (r) => r.efficiency_pct },
    { key: 'm', header: 'Meters', align: 'right', render: (r) => fmt.n(r.meters), value: (r) => r.meters },
    { key: 'mps', header: 'm / loom-shift', align: 'right', render: (r) => fmt.n(r.meters_per_loom_shift, 1), value: (r) => r.meters_per_loom_shift, hideBelow: 'md' },
    { key: 'kp', header: 'Kilopicks', align: 'right', render: (r) => fmt.n(r.kilopicks), value: (r) => r.kilopicks, hideBelow: 'lg' },
    { key: 'w', header: 'Warp /100k picks', align: 'right', render: (r) => fmt.rate(r.warp_stops_cmpx), value: (r) => r.warp_stops_cmpx },
    { key: 'f', header: 'Weft /100k picks', align: 'right', render: (r) => fmt.rate(r.weft_stops_cmpx), value: (r) => r.weft_stops_cmpx },
    { key: 'n', header: 'Loom-shifts', align: 'right', render: (r) => r.loom_shifts, value: (r) => r.loom_shifts, hideBelow: 'md' },
    { key: 'src', header: 'Source', render: (r) => <span className="inline-flex gap-1">{r.sources.map((s) => <SourceBadge key={s} source={s} />)}</span>, value: (r) => r.sources.join(','), hideBelow: 'xl' },
  ];
  return (
    <>
      <PageTitle title="Machine comparison" subtitle="Fair comparisons: looms are ranked against peers on the same category, width, style and source, not on raw output."
        actions={<FilterBar show={['category', 'shift', 'source', 'group']} />} />
      <div className="mb-3">
        <Segmented<Dim> size="sm" ariaLabel="Compare by" value={dim as Dim} onChange={setDim}
          options={[{ value: 'loom', label: 'Looms' }, { value: 'shift', label: 'Shifts' }, { value: 'style', label: 'Styles' }, { value: 'width', label: 'Width' },
                    { value: 'category', label: 'Categories' }, { value: 'group', label: 'Groups' }, { value: 'date', label: 'Days' }]} />
      </div>
      <QueryView query={q}>
        {(d) => (
          <Card>
            <CardHeader title={`${d.rows.length} rows · ${periodText(d.period)}`} subtitle="Efficiency is time-weighted; stop rates are ratios of sums over loom-shifts that have both values." />
            <CardBody className="space-y-3">
              {d.warnings.map((w: string) => <Notice key={w} tone="warn">{w}</Notice>)}
              <DataTable rows={d.rows as Row[]} columns={cols} rowKey={(r) => r.key} exportName={`compare-${dim}`} searchable={(r) => `${r.key} ${r.cohort ?? ''}`}
                initialSort={dim === 'loom' ? { key: 'vs', dir: 'asc' } : undefined} />
            </CardBody>
          </Card>
        )}
      </QueryView>
    </>
  );
};
