import React from 'react';
import { useMachine } from '../../../api/weaving';
import { Drawer } from '../../../design/Drawer';
import { ErrorState, Skeleton } from '../../../design/ui';
import { TrendChart } from '../../../design/charts/Charts';
import { SensorChart } from '../../../design/viz/charts2';
import { AlertCard, AiBadge, HealthRing } from '../../../design/viz/parts';
import { CATEGORY_COLORS } from '../../../design/viz/palette';
import { cn } from '../../../lib/format';
import { Pill, shortDate } from '../common';

const Spec: React.FC<{ k: string; v: React.ReactNode }> = ({ k, v }) => (
  <div className="flex items-baseline justify-between gap-3 border-b border-line/60 py-1.5 text-sm last:border-0">
    <span className="text-ink-3">{k}</span>
    <span className="text-right font-medium text-ink">{v ?? '—'}</span>
  </div>
);

export const MachineDrawer: React.FC<{ loom: string | null; onClose: () => void }> = ({ loom, onClose }) => {
  const q = useMachine(loom);
  const d = q.data;
  const s = d?.spec;
  return (
    <Drawer
      open={!!loom}
      onClose={onClose}
      width="max-w-3xl"
      title={
        <span className="flex items-center gap-3">
          {d?.health && <HealthRing score={d.health.score} band={d.health.band} size={52} />}
          <span>
            {loom}
            {s && <span className="ml-2 text-sm font-normal text-ink-3">{s.make} {s.model} · {s.bay}</span>}
          </span>
        </span>
      }
      subtitle={s ? `${s.type} · ${s.style} · ${s.status === 'STOPPED' ? `stopped ${s.stopped_min} min (${s.stop_reason})` : s.status === 'IDLE' ? 'no order' : 'running'}` : undefined}
    >
      {q.isPending && <div className="space-y-3"><Skeleton className="h-24" /><Skeleton className="h-48" /><Skeleton className="h-48" /></div>}
      {q.isError && <ErrorState error={q.error} onRetry={() => q.refetch()} />}
      {d && s && (
        <div className="space-y-6">
          {d.alerts.length > 0 && (
            <section className="space-y-2">
              <h3 className="flex items-center gap-2 text-sm font-semibold text-ink">Machine watch <AiBadge /></h3>
              {d.alerts.map((a, i) => <AlertCard key={i} a={a} />)}
            </section>
          )}
          {d.health && (
            <section>
              <h3 className="mb-2 text-sm font-semibold text-ink">Why the health score is {d.health.score}</h3>
              {d.health.components.length === 0 ? <p className="text-sm text-ink-3">Nothing is pulling the score down.</p> : (
                <ul className="space-y-1.5">
                  {d.health.components.map((c) => (
                    <li key={c.factor} className="flex items-center justify-between gap-3 rounded-lg bg-subtle px-3 py-2 text-sm">
                      <span><b className="font-medium text-ink">{c.factor}</b> <span className="text-ink-3">· {c.detail}</span></span>
                      <span className="num font-semibold text-bad">{c.points}</span>
                    </li>
                  ))}
                </ul>
              )}
              <p className="mt-1.5 text-xs text-ink-3">{d.health.note}</p>
            </section>
          )}
          {d.sensors.length > 0 && (
            <section>
              <h3 className="mb-2 text-sm font-semibold text-ink">Sensors against this machine's own normal</h3>
              <div className="grid gap-3 md:grid-cols-2">
                {d.sensors.map((c) => {
                  const last = c.points[c.points.length - 1];
                  const off = c.normal && last ? (c.worse === 'low' ? last.value < c.normal.low : last.value > c.normal.high) : false;
                  return (
                    <div key={c.key} className="rounded-xl border border-line/80 p-3">
                      <div className="mb-1 flex items-baseline justify-between">
                        <span className="text-sm font-medium text-ink">{c.label}</span>
                        <span className={cn('num text-sm font-semibold', off ? 'text-bad' : 'text-ink')}>{last?.value.toFixed(2)} <span className="text-xs font-normal text-ink-3">{c.unit}</span></span>
                      </div>
                      <SensorChart points={c.points} unit={c.unit} normal={c.normal} alarm={c.alarm} color={off ? 'rgb(var(--bad))' : undefined} />
                    </div>
                  );
                })}
              </div>
              <p className="mt-1.5 text-xs text-ink-3">Shaded band: this machine's normal range (centre line = its usual level). Dashed red line: alarm level.</p>
            </section>
          )}
          <section>
            <h3 className="mb-2 text-sm font-semibold text-ink">Performance, last 14 days</h3>
            <div className="grid gap-3 md:grid-cols-2">
              <TrendChart data={d.performance} xKey="label" series={[{ key: 'efficiency_pct', label: 'Efficiency', color: 0 }]} format={(v) => `${v.toFixed(1)}%`} height={160} area />
              <TrendChart data={d.performance} xKey="label" series={[{ key: 'stops_per_100k', label: 'Stops per 100k picks', color: 1 }]} format={(v) => v.toFixed(2)} height={160} area />
            </div>
          </section>
          <section className="grid gap-6 md:grid-cols-2">
            <div>
              <h3 className="mb-2 text-sm font-semibold text-ink">Machine record</h3>
              <div className="rounded-xl border border-line/80 px-3">
                <Spec k="Make and model" v={`${s.make ?? ''} ${s.model ?? ''}`} />
                <Spec k="Serial number" v={s.serial_no} />
                <Spec k="Year / age" v={s.year ? `${s.year} · ${s.age_years} yrs` : null} />
                <Spec k="Shedding / colours" v={`${s.shedding ?? '—'} · ${s.colours ?? '—'}`} />
                <Spec k="Reed space" v={s.reed_space_cm ? `${s.reed_space_cm} cm` : null} />
                <Spec k="Rated speed" v={`${s.rated_rpm} picks/min`} />
                <Spec k="Rated power" v={s.power_kw ? `${s.power_kw} kW` : null} />
                <Spec k="Last overhaul" v={s.last_overhaul ? `${shortDate(s.last_overhaul)} (${s.days_since_overhaul} days ago)` : null} />
                <Spec k="Warranty until" v={s.warranty_until ? shortDate(s.warranty_until) : 'Out of warranty'} />
                <Spec k="Current order" v={d.order ? `${d.order.order_no} · ${d.order.customer}` : 'None'} />
              </div>
            </div>
            <div>
              <h3 className="mb-2 text-sm font-semibold text-ink">Reliability</h3>
              <div className="grid grid-cols-3 gap-2 text-center">
                {[['Breakdowns', d.reliability.breakdowns_14d, '14 days'], ['MTBF', d.reliability.mtbf_hours ?? '—', 'hours'], ['MTTR', d.reliability.mttr_min ?? '—', 'minutes']].map(([a, b, c]) => (
                  <div key={String(a)} className="rounded-xl bg-subtle px-2 py-3"><div className="num text-xl font-semibold text-ink">{b}</div><div className="text-[11px] text-ink-3">{a} · {c}</div></div>
                ))}
              </div>
              <h3 className="mb-2 mt-4 text-sm font-semibold text-ink">Stops in 14 days</h3>
              <ul className="space-y-1">
                {d.causes.slice(0, 6).map((c) => (
                  <li key={c.cause} className="flex items-center justify-between text-sm">
                    <span className="inline-flex items-center gap-2 text-ink-2"><span className="size-2.5 rounded-sm" style={{ background: CATEGORY_COLORS[c.category] ?? '#8a99a8' }} />{c.cause}{c.planned && <Pill>planned</Pill>}</span>
                    <span className="num text-ink">{c.stops} · {c.downtime_min} min</span>
                  </li>
                ))}
              </ul>
            </div>
          </section>
          <section className="grid gap-6 md:grid-cols-2">
            <div>
              <h3 className="mb-2 text-sm font-semibold text-ink">Maintenance</h3>
              <ul className="space-y-1.5 text-sm">
                {d.maintenance.preventive.map((p, i) => (
                  <li key={i} className="flex items-center justify-between gap-2 rounded-lg bg-subtle px-3 py-1.5">
                    <span className="text-ink-2">{p.task} <span className="text-ink-3">· {shortDate(p.planned_for)}</span></span>
                    {p.overdue_days > 0 ? <Pill tone="bad">{p.overdue_days} d overdue</Pill> : <Pill tone={p.status === 'COMPLETED' ? 'ok' : 'neutral'}>{p.status.toLowerCase()}</Pill>}
                  </li>
                ))}
              </ul>
            </div>
            <div>
              <h3 className="mb-2 text-sm font-semibold text-ink">Recent stops</h3>
              <ul className="space-y-1 text-sm">
                {d.recent_stops.slice(0, 8).map((r, i) => (
                  <li key={i} className="flex items-center justify-between text-ink-2"><span>{new Date(r.started_at).toLocaleString('en-GB', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' })} · {r.reason}</span><span className="num">{r.open ? 'open' : `${r.minutes} min`}</span></li>
                ))}
              </ul>
            </div>
          </section>
        </div>
      )}
    </Drawer>
  );
};
