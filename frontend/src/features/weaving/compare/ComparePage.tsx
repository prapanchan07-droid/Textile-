import React, { useEffect, useMemo, useState } from 'react';
import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { Sparkles, X } from 'lucide-react';
import { useCompareMeta, useCompareOptions, useCompareRun } from '../../../api/weaving';
import { cn } from '../../../lib/format';
import { PageHeader } from '../../../layout/PageHeader';
import { Card, CardBody, CardHeader, Select } from '../../../design/ui';
import { RadarCompare } from '../../../design/viz/charts2';
import { AiBadge } from '../../../design/viz/parts';
import { axisTick, useChartTheme } from '../../../design/charts/theme';
import { catColor } from '../../../design/viz/palette';
import { Load, Pill } from '../common';
import type { CompareMeta, CompareResult, Recommended } from '../../../types/pages';

const fmt = (v: number | null | undefined, unit: string) => (v == null ? '—' : `${v.toLocaleString('en-IN', { maximumFractionDigits: v >= 100 ? 0 : 2 })}${unit === '%' ? '%' : unit ? ` ${unit}` : ''}`);

const Results: React.FC<{ r: CompareResult }> = ({ r }) => {
  const t = useChartTheme();
  const dates = Array.from(new Set(r.entities.flatMap((e) => e.daily.efficiency_pct.map((x) => x.date)))).sort();
  const effRows = dates.map((d) => ({ label: new Date(d).toLocaleDateString('en-GB', { day: '2-digit', month: 'short' }), ...Object.fromEntries(r.entities.map((e) => [e.key, e.daily.efficiency_pct.find((x) => x.date === d)?.value ?? null])) }));
  const stopRows = dates.map((d) => ({ label: new Date(d).toLocaleDateString('en-GB', { day: '2-digit', month: 'short' }), ...Object.fromEntries(r.entities.map((e) => [e.key, e.daily.stops_per_100k.find((x) => x.date === d)?.value ?? null])) }));
  const line = (data: any[]) => (
    <div style={{ height: 220 }}>
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={{ top: 6, right: 10, bottom: 0, left: 0 }}>
          <CartesianGrid vertical={false} stroke={t.grid} />
          <XAxis dataKey="label" tick={axisTick(t)} tickLine={false} axisLine={{ stroke: t.axis }} minTickGap={14} />
          <YAxis tick={axisTick(t)} tickLine={false} axisLine={false} width={40} domain={['auto', 'auto']} />
          <Tooltip contentStyle={{ borderRadius: 10, border: '1px solid rgb(var(--line))', background: 'rgb(var(--surface))', fontSize: 12 }} />
          {r.entities.map((e, i) => <Line key={e.key} dataKey={e.key} name={e.label} stroke={catColor(i)} strokeWidth={i === 0 ? 2.8 : 2} dot={false} connectNulls isAnimationActive={false} />)}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
  return (
    <div className="space-y-4">
      <Card>
        <CardHeader title={`${r.entities.length} compared over ${r.days} days`} subtitle={`${r.period}${r.style_filter ? ` · style ${r.style_filter} only` : ''} · reference: ${r.entities[0]?.label}`} />
        <CardBody className="space-y-3">
          <div className="flex flex-wrap gap-2">{r.entities.map((e, i) => <span key={e.key} className="inline-flex items-center gap-2 rounded-full border border-line px-3 py-1 text-sm"><span className="size-2.5 rounded-full" style={{ background: catColor(i) }} /><b className="font-medium text-ink">{e.label}</b>{e.subtitle && <span className="hidden text-xs text-ink-3 md:inline">{e.subtitle}</span>}{i === 0 && <Pill tone="info">reference</Pill>}</span>)}</div>
          <div className="rounded-xl bg-subtle p-4">
            <div className="mb-1.5 flex items-center gap-2 text-sm font-semibold text-ink">What stands out <AiBadge label="tested" title="Each difference is tested against normal variation before it is called out." /></div>
            <ul className="space-y-1.5 text-sm leading-5 text-ink-2">{r.highlights.map((h, i) => <li key={i} className="flex gap-2"><span className="mt-2 size-1.5 shrink-0 rounded-full bg-accent" />{h}</li>)}</ul>
          </div>
        </CardBody>
      </Card>
      <div className="grid gap-4 xl:grid-cols-5">
        <Card className="xl:col-span-3">
          <CardHeader title="Side by side" subtitle="Green and red mark differences from the reference that are larger than normal variation" />
          <div className="overflow-x-auto px-2 pb-4">
            <table className="w-full text-sm">
              <thead><tr className="text-left text-xs text-ink-3"><th className="px-3 py-2 font-medium">Metric</th>{r.entities.map((e, i) => <th key={e.key} className="px-3 py-2 text-right font-medium"><span className="inline-flex items-center gap-1.5"><span className="size-2 rounded-full" style={{ background: catColor(i) }} />{e.label}</span></th>)}</tr></thead>
              <tbody>
                {r.metrics.map((m) => (
                  <tr key={m.key} className="border-t border-line/60">
                    <td className="px-3 py-2 text-ink-2">{m.label}<span className="ml-1 text-[10px] text-ink-3">{m.better === 'high' ? '↑ better' : '↓ better'}</span></td>
                    {r.entities.map((e, i) => {
                      const v = e.vs_reference[m.key];
                      const sig = v?.significant;
                      const good = sig ? (v.direction === 'higher') === (m.better === 'high') : null;
                      return (
                        <td key={e.key} className={cn('num px-3 py-2 text-right', sig && (good ? 'bg-ok-soft font-semibold text-ok' : 'bg-bad-soft font-semibold text-bad'))}>
                          {fmt(e.metrics[m.key], m.unit)}
                          {i > 0 && v?.ratio && sig && <div className="text-[10px] font-normal">{v.ratio.toFixed(1)}×</div>}
                          {i > 0 && v?.diff != null && sig && <div className="text-[10px] font-normal">{v.diff > 0 ? '+' : ''}{v.diff} pts</div>}
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
        <Card className="xl:col-span-2">
          <CardHeader title="Shape of the comparison" subtitle="Each axis is scaled so outward is better" />
          <CardBody>{r.radar.length >= 3 ? <RadarCompare rows={r.radar} keys={r.entities.map((e) => ({ key: e.key, label: e.label }))} /> : <p className="py-10 text-center text-sm text-ink-3">Pick three or more metrics to see the shape.</p>}</CardBody>
        </Card>
      </div>
      <div className="grid gap-4 xl:grid-cols-2">
        <Card><CardHeader title="Efficiency by day" /><CardBody>{line(effRows)}</CardBody></Card>
        <Card><CardHeader title="Stops per 100,000 picks by day" /><CardBody>{line(stopRows)}</CardBody></Card>
      </div>
      <p className="text-xs text-ink-3">{r.notes.join(' ')}</p>
    </div>
  );
};

const Builder: React.FC<{ meta: CompareMeta; type: string; setType: (t: string) => void; keys: string[]; setKeys: (k: string[]) => void; metrics: string[]; setMetrics: (m: string[]) => void; days: number; setDays: (n: number) => void; style: string | null }> = ({ meta, type, setType, keys, setKeys, metrics, setMetrics, days, setDays, style }) => {
  const lazy = useCompareOptions(type, !meta.options[type]);
  const opts = meta.options[type] ?? lazy.data ?? [];
  const [text, setText] = useState('');
  const shown = opts.filter((o) => `${o.label} ${o.group}`.toLowerCase().includes(text.toLowerCase())).slice(0, 60);
  const toggle = (k: string) => setKeys(keys.includes(k) ? keys.filter((x) => x !== k) : keys.length >= 8 ? keys : [...keys, k]);
  const label = (k: string) => opts.find((o) => o.key === k)?.label ?? k;
  return (
    <Card>
      <CardHeader title="Build your own" subtitle="Pick what to compare. The first one you choose is the reference." />
      <CardBody className="space-y-4">
        <div className="flex flex-wrap items-end gap-3">
          <Select label="Compare" value={type} onChange={(e) => { setType(e.target.value); setKeys([]); }} options={meta.types.map((t) => ({ value: t.key, label: t.label }))} />
          <Select label="Over" value={String(days)} onChange={(e) => setDays(Number(e.target.value))} options={[7, 14, 21, 28].map((n) => ({ value: String(n), label: `${n} days` }))} />
          {style && <Pill tone="info">style {style} only</Pill>}
        </div>
        <div className="flex flex-wrap gap-1.5">
          {keys.map((k, i) => <button key={k} onClick={() => toggle(k)} className="inline-flex items-center gap-1.5 rounded-full border border-line bg-surface px-2.5 py-1 text-xs font-medium hover:border-bad"><span className="size-2 rounded-full" style={{ background: catColor(i) }} />{label(k)}<X className="size-3 text-ink-3" /></button>)}
          {keys.length === 0 && <span className="text-xs text-ink-3">Nothing picked yet.</span>}
        </div>
        <input value={text} onChange={(e) => setText(e.target.value)} placeholder={`Search ${meta.types.find((t) => t.key === type)?.label.toLowerCase()}`} className="h-8 w-full rounded-lg border border-line bg-surface px-3 text-sm outline-none focus:border-accent" />
        <div className="flex max-h-40 flex-wrap gap-1.5 overflow-auto">
          {shown.map((o) => <button key={o.key} onClick={() => toggle(o.key)} className={cn('rounded-md border px-2 py-1 text-xs', keys.includes(o.key) ? 'border-accent bg-accent-soft font-semibold text-accent-ink' : 'border-line text-ink-2 hover:bg-subtle')} title={o.group}>{o.label}</button>)}
        </div>
        <div>
          <div className="mb-1.5 text-xs font-medium text-ink-2">Measures</div>
          <div className="flex flex-wrap gap-1.5">
            {meta.metrics.map((m) => <button key={m.key} onClick={() => setMetrics(metrics.includes(m.key) ? metrics.filter((x) => x !== m.key) : [...metrics, m.key])} className={cn('rounded-full border px-2.5 py-1 text-xs', metrics.includes(m.key) ? 'border-accent bg-accent-soft font-semibold text-accent-ink' : 'border-line text-ink-2 hover:bg-subtle')}>{m.label}</button>)}
          </div>
        </div>
      </CardBody>
    </Card>
  );
};

export const ComparePage: React.FC = () => {
  const q = useCompareMeta();
  return (
    <>
      <PageHeader title="Compare" description="Put looms, styles, shifts, yarn lots or suppliers side by side. Differences are tested, so noise is not mistaken for a finding." />
      <Load q={q}>{(meta) => <Body meta={meta} />}</Load>
    </>
  );
};

const Body: React.FC<{ meta: CompareMeta }> = ({ meta }) => {
  const [type, setType] = useState('loom');
  const [keys, setKeys] = useState<string[]>([]);
  const [metrics, setMetrics] = useState<string[]>(meta.default_metrics);
  const [days, setDays] = useState(14);
  const [style, setStyle] = useState<string | null>(null);
  const [rec, setRec] = useState<string | null>(null);
  const [allRec, setAllRec] = useState(false);
  const first = meta.recommended[0];
  useEffect(() => {
    if (first && keys.length === 0 && rec === null) apply(first);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
  const apply = (r: Recommended) => { setType(r.type); setKeys(r.keys); setMetrics(r.metrics); setStyle(r.style); setRec(r.id); };
  const run = useCompareRun({ type, keys, metrics, days, style }, keys.length > 0);
  return (
    <div className="grid gap-4 xl:grid-cols-[360px_1fr]">
      <div className="space-y-4">
        <Card>
          <CardHeader title={<span className="inline-flex items-center gap-2">Recommended for you <AiBadge /></span>} subtitle="The comparisons worth making right now, taken from today's findings" />
          <div className="space-y-2 px-4 pb-4">
            {(allRec ? meta.recommended : meta.recommended.slice(0, 5)).map((r) => (
              <button key={r.id} onClick={() => apply(r)} className={cn('block w-full rounded-xl border p-3 text-left transition-colors', rec === r.id ? 'border-accent bg-accent-soft/50' : 'border-line/80 hover:bg-subtle')}>
                <div className="flex items-center gap-2 text-sm font-semibold text-ink">{r.source === 'finding' && <Sparkles className="size-3.5 text-accent" />}{r.title}</div>
                <p className="mt-0.5 text-xs leading-5 text-ink-3">{r.why}</p>
              </button>
            ))}
            {meta.recommended.length > 5 && <button onClick={() => setAllRec((v) => !v)} className="w-full rounded-lg py-1.5 text-xs font-medium text-accent hover:bg-subtle">{allRec ? 'Show fewer' : `Show ${meta.recommended.length - 5} more`}</button>}
          </div>
        </Card>
        <Builder meta={meta} type={type} setType={(t) => { setType(t); setStyle(null); setRec(null); }} keys={keys} setKeys={(k) => { setKeys(k); setRec(null); }} metrics={metrics} setMetrics={setMetrics} days={days} setDays={setDays} style={style} />
      </div>
      <div className="min-w-0">
        {keys.length === 0 && <Card><p className="p-10 text-center text-sm text-ink-3">Choose a recommended comparison, or pick two or more things to compare.</p></Card>}
        {keys.length > 0 && run.isPending && <Card><p className="p-10 text-center text-sm text-ink-3">Comparing…</p></Card>}
        {run.isError && <Card><p className="p-10 text-center text-sm text-bad">{(run.error as Error).message}</p></Card>}
        {run.data && <Results r={run.data} />}
      </div>
    </div>
  );
};
