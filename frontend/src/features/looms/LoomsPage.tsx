import React, { useMemo, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { AlertTriangle, LayoutGrid, Table2, Wrench } from 'lucide-react';
import { useLoomGrid } from '../../api/mill';
import { QueryView } from '../../design/QueryView';
import { DataTable, type Column } from '../../design/DataTable';
import { Card, CardBody, CardHeader, Segmented } from '../../design/ui';
import { Sparkline } from '../../design/viz/Sparkline';
import { cn, pct } from '../../lib/format';
import { FilterBar, useFilters } from '../common/filters';
import { FreshnessLine, LiveState, PageTitle, SourceBadge, fmt } from '../common/parts';
import type { LoomCard } from '../../types/mill';

/** Standing against peers on the same style and width: points below the peer median. */
const standing = (l: LoomCard) => {
  const e = l.period?.efficiency_pct;
  const m = l.period?.peer_median_efficiency_pct;
  if (e == null || m == null) return null;
  return e - m;
};

const tone = (gap: number | null) => (gap == null ? 'border-line' : gap <= -8 ? 'border-bad/60 bg-bad-soft/40' : gap <= -3 ? 'border-warn/60 bg-warn-soft/40' : 'border-line');

const columns: Column<LoomCard>[] = [
  { key: 'code', header: 'Loom', render: (l) => <Link to={`/looms/${l.id}`} className="font-medium text-ink hover:text-accent">{l.code}</Link>, value: (l) => l.code },
  { key: 'width', header: 'Width', align: 'right', render: (l) => (l.width_cm ? `${l.width_cm} cm` : '—'), value: (l) => l.width_cm, hideBelow: 'md' },
  { key: 'group', header: 'Group', render: (l) => l.group?.name ?? '—', value: (l) => l.group?.name, hideBelow: 'md' },
  { key: 'style', header: 'Style', render: (l) => l.period?.style ?? '—', value: (l) => l.period?.style, hideBelow: 'lg' },
  { key: 'eff', header: 'Efficiency', align: 'right', render: (l) => pct(l.period?.efficiency_pct), value: (l) => l.period?.efficiency_pct },
  { key: 'peer', header: 'vs peers', align: 'right', render: (l) => { const g = standing(l); return g == null ? '—' : <span className={g <= -3 ? 'text-bad' : 'text-ink-2'}>{g > 0 ? '+' : ''}{g.toFixed(1)} pts</span>; }, value: standing },
  { key: 'meters', header: 'Meters', align: 'right', render: (l) => fmt.n(l.period?.meters), value: (l) => l.period?.meters },
  { key: 'warp', header: 'Warp /100k', align: 'right', render: (l) => fmt.rate(l.period?.warp_stops_cmpx), value: (l) => l.period?.warp_stops_cmpx, hideBelow: 'lg' },
  { key: 'weft', header: 'Weft /100k', align: 'right', render: (l) => fmt.rate(l.period?.weft_stops_cmpx), value: (l) => l.period?.weft_stops_cmpx, hideBelow: 'lg' },
  { key: 'latest', header: 'Latest record', render: (l) => (l.latest ? <span className="whitespace-nowrap">{fmt.date(l.latest.date)} {l.latest.shift} <SourceBadge source={l.latest.source} /></span> : '—'), value: (l) => l.latest?.date },
  { key: 'live', header: 'Live', render: (l) => <LiveState compact state={l.live.state} origin={l.live.origin} machineState={l.live.machine_state} />, value: (l) => l.live.state, hideBelow: 'xl' },
  { key: 'alerts', header: 'Alerts', align: 'right', render: (l) => l.open_alerts || '—', value: (l) => l.open_alerts },
];

export const LoomsPage: React.FC = () => {
  const filters = useFilters();
  const q = useLoomGrid(filters);
  const [mode, setMode] = useState<'grid' | 'table'>('grid');
  return (
    <>
      <PageTitle
        title="Loom floor"
        subtitle="Every registered loom with its period performance, latest imported record and live state. Imported records are history, not live status."
        actions={
          <FilterBar show={['category', 'shift', 'source', 'group']}>
            <Segmented size="sm" value={mode} onChange={setMode} ariaLabel="View" options={[{ value: 'grid', label: <LayoutGrid className="size-3.5" /> }, { value: 'table', label: <Table2 className="size-3.5" /> }]} />
          </FilterBar>
        }
      />
      <QueryView query={q}>
        {(d) => (
          <div className="space-y-4">
            <FreshnessLine freshness={d.freshness} period={d.period} />
            {mode === 'table' ? (
              <Card><CardBody className="pt-4"><DataTable rows={d.looms} columns={columns} rowKey={(l) => String(l.id)} searchable={(l) => `${l.code} ${l.group?.name ?? ''} ${l.period?.style ?? ''}`} exportName="looms" /></CardBody></Card>
            ) : (
              <Floor looms={d.looms} />
            )}
          </div>
        )}
      </QueryView>
    </>
  );
};

const Floor: React.FC<{ looms: LoomCard[] }> = ({ looms }) => {
  const navigate = useNavigate();
  const byCat = useMemo(() => {
    const m = new Map<string, LoomCard[]>();
    looms.forEach((l) => m.set(l.category, [...(m.get(l.category) ?? []), l]));
    return [...m.entries()];
  }, [looms]);
  return (
    <div className="space-y-4">
      <p className="flex flex-wrap gap-4 text-xs text-ink-3">
        <span className="inline-flex items-center gap-1"><span className="size-3 rounded border border-warn/60 bg-warn-soft" /> 3–8 pts below peers</span>
        <span className="inline-flex items-center gap-1"><span className="size-3 rounded border border-bad/60 bg-bad-soft" /> more than 8 pts below peers</span>
        <span>Peers: same category, width and style (3 or more looms)</span>
      </p>
      {byCat.map(([cat, ls]) => (
        <Card key={cat}>
          <CardHeader title={`${cat} · ${ls[0].manufacturer}`} subtitle={`${ls.length} looms`} />
          <CardBody>
            <ul className="grid grid-cols-2 gap-2 sm:grid-cols-4 md:grid-cols-6 xl:grid-cols-8">
              {ls.map((l) => {
                const gap = standing(l);
                return (
                  <li key={l.id}>
                    <button onClick={() => navigate(`/looms/${l.id}`)}
                      className={cn('w-full rounded-xl border p-2.5 text-left transition-colors hover:border-accent', tone(gap))}
                      title={`${l.code}: ${pct(l.period?.efficiency_pct)} efficiency${gap != null ? `, ${gap.toFixed(1)} pts vs peers` : ''}`}>
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-semibold text-ink">{l.code}</span>
                        <span className="flex items-center gap-1 text-2xs">
                          {l.open_alerts > 0 && <span className="inline-flex items-center text-warn"><AlertTriangle className="size-3" />{l.open_alerts}</span>}
                          {l.open_work_orders > 0 && <span className="inline-flex items-center text-ink-3"><Wrench className="size-3" />{l.open_work_orders}</span>}
                        </span>
                      </div>
                      <div className="num mt-1 text-lg font-semibold text-ink">{pct(l.period?.efficiency_pct, 1)}</div>
                      <div className="text-2xs text-ink-3">{gap == null ? 'no peer group' : `${gap > 0 ? '+' : ''}${gap.toFixed(1)} vs peers`}</div>
                      {l.period?.trend && l.period.trend.filter((x) => x != null).length > 2 && (
                        <Sparkline values={l.period.trend.filter((x): x is number => x != null)} width={100} height={18} className="mt-1" />
                      )}
                      <div className="mt-1 truncate text-2xs text-ink-3">{l.latest ? `${fmt.date(l.latest.date)} ${l.latest.shift}` : 'no records'}{l.group ? ` · ${l.group.code}` : ''}</div>
                      {l.live.state !== 'NOT_CONFIGURED' && <div className="mt-1"><LiveState compact state={l.live.state} origin={l.live.origin} machineState={l.live.machine_state} /></div>}
                    </button>
                  </li>
                );
              })}
            </ul>
          </CardBody>
        </Card>
      ))}
    </div>
  );
};
