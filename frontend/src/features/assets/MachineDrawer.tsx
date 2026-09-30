import React from 'react';
import { Link } from 'react-router-dom';
import { GitCompareArrows } from 'lucide-react';
import { useMachines } from '../../api/queries';
import { usePeriod } from '../../app/state';
import { kgExact, minutes, num, pct } from '../../lib/format';
import { Drawer } from '../../design/Drawer';
import { Button, EmptyState, Skeleton, StatusPill } from '../../design/ui';
import { TrendChart } from '../../design/charts/Charts';

/** Machine 360: performance, trend, maintenance and quality in one panel. Deep-linkable via ?machine=ID. */
export const MachineDrawer: React.FC<{ machineId: string | null; onClose: () => void }> = ({ machineId, onClose }) => {
  const [period] = usePeriod();
  const q = useMachines(period, 'ALL', machineId ?? 'ALL');
  const row = q.data?.all_machines.find((m) => m.machine_id === machineId);
  const detail = q.data?.machine_detail?.machine_id === machineId ? q.data.machine_detail : undefined;
  const trend = machineId ? (q.data?.machine_trends_by_id?.[machineId] ?? []) : [];
  const loading = q.isPending || (q.isPlaceholderData && !detail);

  return (
    <Drawer
      open={!!machineId}
      onClose={onClose}
      title={
        <span className="flex items-center gap-2">
          {machineId}
          {row && <StatusPill status={row.status} />}
        </span>
      }
      subtitle={row ? `${row.machine_type} · ${row.main_issue}` : undefined}
      footer={
        <Link to={`/assets/benchmark?m=${encodeURIComponent(machineId ?? '')}`}>
          <Button size="sm" icon={<GitCompareArrows className="size-3.5" />}>
            Compare with other machines
          </Button>
        </Link>
      }
    >
      {loading ? (
        <div className="space-y-3">
          <Skeleton className="h-20" />
          <Skeleton className="h-48" />
          <Skeleton className="h-32" />
        </div>
      ) : !row ? (
        <EmptyState title="Machine not found" description={`${machineId} has no data for this period.`} />
      ) : (
        <div className="space-y-6">
          <dl className="grid grid-cols-2 gap-3 sm:grid-cols-4">
            <Stat label="Efficiency" value={pct(row.efficiency_pct)} />
            <Stat label="Output" value={kgExact(row.actual_kg)} sub={`of ${kgExact(row.target_kg)}`} />
            <Stat label="Loss" value={kgExact(row.loss_kg)} />
            <Stat label="Downtime" value={minutes(row.downtime_min)} sub={detail ? `${num(detail.stoppage_count)} stoppages` : undefined} />
          </dl>

          {trend.length > 1 && (
            <section>
              <h3 className="mb-2 text-sm font-semibold text-ink">Efficiency trend</h3>
              <TrendChart
                data={trend}
                xKey="date_label"
                format={(v) => `${v.toFixed(0)}%`}
                series={[{ key: 'efficiency_pct', label: 'Efficiency', color: 0 }]}
                area
                height={180}
              />
            </section>
          )}

          {detail && (
            <>
              <Section title="Maintenance">
                <Row label="Main downtime reason" value={detail.main_reason} />
                <Row label="Last maintenance" value={detail.last_maintenance} />
                <Row label="Next maintenance" value={detail.next_maintenance} />
                <Row label="Recent event" value={detail.recent_event} />
              </Section>
              <Section title="Power">
                <Row label="Power events" value={num(detail.power_events)} />
                <Row label="Downtime from power" value={minutes(detail.power_downtime_min)} />
              </Section>
              <Section title="Quality">
                <Row label="Status" value={detail.quality_status} />
              </Section>
            </>
          )}
        </div>
      )}
    </Drawer>
  );
};

const Stat: React.FC<{ label: string; value: string; sub?: string }> = ({ label, value, sub }) => (
  <div className="rounded-md border border-line p-3">
    <dt className="text-xs text-ink-3">{label}</dt>
    <dd className="mt-0.5 text-base font-semibold text-ink">{value}</dd>
    {sub && <dd className="text-2xs text-ink-3">{sub}</dd>}
  </div>
);

const Section: React.FC<{ title: string; children: React.ReactNode }> = ({ title, children }) => (
  <section>
    <h3 className="mb-1 text-sm font-semibold text-ink">{title}</h3>
    <dl className="divide-y divide-line">{children}</dl>
  </section>
);

const Row: React.FC<{ label: string; value: React.ReactNode }> = ({ label, value }) => (
  <div className="flex justify-between gap-4 py-2 text-sm">
    <dt className="text-ink-3">{label}</dt>
    <dd className="text-right text-ink">{value}</dd>
  </div>
);
