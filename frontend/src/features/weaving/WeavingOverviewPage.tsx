import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { AlertOctagon, AlertTriangle, ArrowRight, CheckCircle2, IndianRupee, Layers, Shirt, Sparkles, type LucideIcon } from 'lucide-react';
import { useParam } from '../../app/state';
import { inrFromLakhs, meters, minutes, num, pct } from '../../lib/format';
import { Card, CardBody, CardHeader, Kpi, KpiGrid, Meter, Segmented, StatusPill } from '../../design/ui';
import { DataTable } from '../../design/DataTable';
import { ChartPanel } from '../../design/ChartPanel';
import { ColumnChart, TrendChart } from '../../design/charts/Charts';
import type { WeavingModuleData } from '../../types/weaving';
import type { Period } from '../../lib/period';
import { effTone, SEV_LABEL, sevTone, WeavingPage } from './shared';

type View = 'owner' | 'manager';

export const WeavingOverviewPage: React.FC = () => {
  const [view, setView] = useParam('view', 'owner');
  return (
    <WeavingPage
      description={
        view === 'owner'
          ? 'Owner view: is weaving making money, and what needs your decision?'
          : 'Manager view: what is wrong on the floor right now, and who fixes it?'
      }
      actions={
        <Segmented<View>
          ariaLabel="View"
          value={view as View}
          onChange={setView}
          options={[
            { value: 'owner', label: 'Owner' },
            { value: 'manager', label: 'Manager' },
          ]}
        />
      }
    >
      {(d, period) => (view === 'manager' ? <ManagerView d={d} /> : <OwnerView d={d} period={period} />)}
    </WeavingPage>
  );
};

/* ------------------------------------------------------------------ Owner */

const BIG_TONE = { ok: 'text-ok', warn: 'text-warn', bad: 'text-bad', neutral: 'text-ink', info: 'text-ink' } as const;
const CHIP_TONE = { ok: 'bg-ok-soft text-ok', warn: 'bg-warn-soft text-warn', bad: 'bg-bad-soft text-bad', neutral: 'bg-muted text-ink-2', info: 'bg-accent-soft text-accent-ink' } as const;

/** One large number with a plain-language label. The owner view uses only four of these. */
const BigNumber: React.FC<{ icon: LucideIcon; label: string; value: string; note: string; tone?: keyof typeof BIG_TONE }> = ({
  icon: Icon,
  label,
  value,
  note,
  tone = 'neutral',
}) => (
  <Card className="p-5 transition-shadow hover:shadow-lift">
    <div className="flex items-center gap-2.5">
      <span className={`flex size-9 items-center justify-center rounded-xl ${CHIP_TONE[tone]}`}>
        <Icon className="size-[18px]" />
      </span>
      <span className="text-sm font-medium text-ink-2">{label}</span>
    </div>
    <div className={`mt-3 text-[34px] font-semibold leading-none tracking-tight ${BIG_TONE[tone]}`}>{value}</div>
    <div className="mt-2 text-sm text-ink-3">{note}</div>
  </Card>
);

const firstSentence = (t: string) => t.split(/(?<=\.)\s/)[0];

/**
 * Deliberately short: one headline, four numbers, up to three decisions and one chart.
 * Everything else lives in the Manager view and the other tabs.
 */
const OwnerView: React.FC<{ d: WeavingModuleData; period: Period }> = ({ d }) => {
  const { search } = useLocation();
  const k = d.kpis;
  const [, setView] = useParam('view', 'owner');
  const tone = k.achievement_pct >= 98 ? 'ok' : k.achievement_pct >= 94 ? 'warn' : 'bad';
  const headline = tone === 'ok' ? 'Weaving is on track' : tone === 'warn' ? 'Weaving is a little behind target' : 'Weaving is behind target';
  const banner = {
    ok: 'from-ok-soft via-surface to-surface border-ok/30',
    warn: 'from-warn-soft via-surface to-surface border-warn/30',
    bad: 'from-bad-soft via-surface to-surface border-bad/30',
  }[tone];
  const StatusIcon = tone === 'ok' ? CheckCircle2 : tone === 'warn' ? AlertTriangle : AlertOctagon;
  const border = { HIGH: 'border-l-bad', MEDIUM: 'border-l-warn', LOW: 'border-l-ok' };
  const decisions = d.decisions.slice(0, 3);
  return (
    <>
      <div className={`flex items-start gap-4 rounded-2xl border bg-gradient-to-r p-6 shadow-card ${banner}`}>
        <span className={`flex size-12 shrink-0 items-center justify-center rounded-2xl ${CHIP_TONE[tone]}`}>
          <StatusIcon className="size-6" />
        </span>
        <div>
          <p className="text-xs font-semibold uppercase tracking-widest text-ink-3">{d.period_label}</p>
          <h2 className="mt-1 text-2xl font-semibold tracking-tight text-ink sm:text-[28px]">{headline}</h2>
          <p className="mt-1.5 max-w-3xl text-base text-ink-2">
            {meters(k.fabric_m)} of fabric made against {meters(k.target_m)} planned. About {inrFromLakhs(k.loss_lakhs)} of profit was lost
            because looms stopped or ran slow.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        <BigNumber icon={Shirt} label="Fabric made" value={meters(k.fabric_m)} note={`${pct(k.achievement_pct, 0)} of plan`} tone={tone} />
        <BigNumber icon={IndianRupee} label="Profit lost" value={inrFromLakhs(k.loss_lakhs)} note="from stops and slow looms" tone="bad" />
        <BigNumber icon={Sparkles} label="Good-quality fabric" value={pct(k.grade_a_pct, 0)} note="sold at full price" tone={k.grade_a_pct >= 94 ? 'ok' : 'warn'} />
        <BigNumber icon={Layers} label="Looms running" value={`${k.looms_running} of ${k.looms_total}`} note={`${k.looms_stopped} stopped right now`} tone={k.looms_stopped > 4 ? 'bad' : 'ok'} />
      </div>

      <section aria-label="Decisions for you">
        <h2 className="mb-3 text-lg font-semibold tracking-tight text-ink">
          {decisions.length ? 'What needs your decision' : 'Nothing needs your decision today'}
        </h2>
        <div className="space-y-3">
          {decisions.map((x, i) => (
            <Card key={x.id} className={`flex flex-wrap items-center gap-4 border-l-4 p-5 transition-shadow hover:shadow-lift ${border[x.severity]}`}>
              <div className="flex size-9 shrink-0 items-center justify-center rounded-full bg-accent-soft text-sm font-semibold text-accent-ink">{i + 1}</div>
              <div className="min-w-0 flex-1 basis-64">
                <div className="flex flex-wrap items-center gap-2">
                  <h3 className="text-base font-semibold text-ink">{x.title}</h3>
                  <StatusPill tone={sevTone(x.severity)} label={SEV_LABEL[x.severity]} />
                </div>
                <p className="mt-1 text-sm text-ink-3">{firstSentence(x.why)}</p>
                <p className="mt-1 text-sm text-ink">
                  <span className="font-medium">Do this:</span> {x.action}
                </p>
              </div>
              <div className="text-right">
                <div className="text-lg font-semibold text-bad">{inrFromLakhs(x.impact_lakhs)}</div>
                <div className="text-xs text-ink-3">at stake · {x.owner}</div>
                <Link
                  to={{ pathname: x.link.split('?')[0], search: x.link.includes('?') ? `?${x.link.split('?')[1]}` : search }}
                  className="mt-1 inline-flex items-center gap-1 text-xs font-medium text-accent-ink hover:underline"
                >
                  See why <ArrowRight className="size-3.5" />
                </Link>
              </div>
            </Card>
          ))}
        </div>
      </section>

      <Card>
        <CardHeader title="Fabric made each day" subtitle="Blue is what you made, grey is the plan" />
        <CardBody>
          <ColumnChart
            data={d.trend}
            xKey="date_label"
            format={(v) => `${num(v)} m`}
            axisFormat={(v) => `${Math.round(v / 1000)}k`}
            series={[
              { key: 'actual_m', label: 'Made', color: 1 },
              { key: 'target_m', label: 'Plan', color: 'muted' },
            ]}
          />
        </CardBody>
      </Card>

      <p className="text-center text-sm text-ink-3">
        Want the floor details?{' '}
        <button onClick={() => setView('manager')} className="text-accent-ink hover:underline">
          Open the Manager view
        </button>
      </p>
    </>
  );
};

/* ------------------------------------------------------------------ Manager */

const ManagerView: React.FC<{ d: WeavingModuleData }> = ({ d }) => {
  const { search } = useLocation();
  const k = d.kpis;
  const stopped = d.looms.filter((l) => l.status === 'STOPPED').sort((a, b) => b.stopped_since_min - a.stopped_since_min);
  const problem = d.looms.filter((l) => l.health !== 'NORMAL').sort((a, b) => b.loss_lakhs - a.loss_lakhs).slice(0, 6);
  const openActions = d.actions.filter((a) => a.status !== 'COMPLETED');
  const escalations = d.decisions.filter((x) => x.severity !== 'LOW').slice(0, 4);
  const loomLink = (id: string) => ({ pathname: '/weaving/looms', search: `?loom=${id}` });
  return (
    <>
      <KpiGrid>
        <Kpi label="Running now" value={`${k.looms_running} of ${k.looms_total}`} hint="looms" status={k.looms_running / k.looms_total >= 0.85 ? 'ok' : 'warn'} />
        <Kpi label="Stopped now" value={num(k.looms_stopped)} hint="need a fitter" status={k.looms_stopped > 4 ? 'bad' : k.looms_stopped ? 'warn' : 'ok'} />
        <Kpi label="Idle (no order)" value={num(k.looms_idle)} />
        <Kpi label={`Efficiency · ${d.period_label.toLowerCase()}`} value={pct(k.efficiency_pct)} hint="target 92%" status={effTone(k.efficiency_pct)} />
        <Kpi label="Achievement" value={pct(k.achievement_pct)} hint={`${meters(k.fabric_m)} of ${meters(k.target_m)}`} />
        <Kpi label="First grade" value={pct(k.grade_a_pct)} status={k.grade_a_pct >= 94 ? 'ok' : 'warn'} />
      </KpiGrid>

      <Card>
        <CardHeader title={`Stopped right now · ${stopped.length}`} subtitle="Longest stops first. This is the live floor, not the selected period." />
        <DataTable
          rows={stopped}
          rowKey={(r) => r.loom_id}
          dense
          emptyTitle="Every loom is running or idle"
          columns={[
            { key: 'l', header: 'Loom', value: (r) => r.loom_id, render: (r) => <Link to={loomLink(r.loom_id)} className="font-medium hover:underline">{r.loom_id}</Link> },
            { key: 'r', header: 'Reason', value: (r) => r.stop_reason ?? '', render: (r) => r.stop_reason },
            {
              key: 's',
              header: 'Stopped for',
              align: 'right',
              value: (r) => r.stopped_since_min,
              render: (r) => <span className={r.stopped_since_min >= 60 ? 'font-semibold text-bad' : ''}>{minutes(r.stopped_since_min)}</span>,
            },
            { key: 'f', header: 'Fitter', hideBelow: 'md', value: (r) => r.fitter, render: (r) => r.fitter },
            { key: 'w', header: 'Weaver', hideBelow: 'md', value: (r) => r.weaver, render: (r) => r.weaver },
          ]}
        />
      </Card>

      <div className="grid gap-4 lg:grid-cols-5">
        <Card className="lg:col-span-3">
          <CardHeader title="Shift performance" subtitle={`${d.period_label}. Compare shifts to see where output slips.`} />
          <DataTable
            rows={d.shifts}
            rowKey={(r) => r.shift}
            dense
            columns={[
              { key: 's', header: 'Shift', value: (r) => r.shift, render: (r) => <span className="font-medium">{r.shift}</span> },
              { key: 'a', header: 'Output', align: 'right', value: (r) => r.actual_m, render: (r) => meters(r.actual_m) },
              {
                key: 'e',
                header: 'Efficiency',
                value: (r) => r.efficiency_pct,
                render: (r) => (
                  <div className="flex w-32 items-center gap-2">
                    <Meter value={r.efficiency_pct} max={100} tone={effTone(r.efficiency_pct)} />
                    <span className="num w-11 text-right text-xs">{pct(r.efficiency_pct)}</span>
                  </div>
                ),
              },
              { key: 'g', header: 'First grade', align: 'right', hideBelow: 'sm', value: (r) => r.grade_a_pct, render: (r) => pct(r.grade_a_pct) },
              { key: 'x', header: 'Main stop reason', hideBelow: 'md', value: (r) => r.top_stop_reason, render: (r) => r.top_stop_reason },
            ]}
          />
        </Card>
        <Card className="lg:col-span-2">
          <CardHeader title="Airjet vs Sulzer" />
          <DataTable
            rows={d.groups}
            rowKey={(r) => r.loom_type}
            dense
            columns={[
              {
                key: 't',
                header: 'Type',
                value: (r) => r.loom_type,
                render: (r) => (
                  <div>
                    <div className="font-medium">{r.loom_type}</div>
                    <div className="text-xs text-ink-3">{r.looms} looms</div>
                  </div>
                ),
              },
              { key: 'e', header: 'Efficiency', align: 'right', value: (r) => r.efficiency_pct, render: (r) => pct(r.efficiency_pct) },
              { key: 'l', header: 'Margin lost', align: 'right', value: (r) => r.loss_lakhs, render: (r) => inrFromLakhs(r.loss_lakhs) },
            ]}
          />
        </Card>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader title="Looms to fix first" subtitle="Largest margin loss among looms outside the normal range" />
          <DataTable
            rows={problem}
            rowKey={(r) => r.loom_id}
            dense
            emptyTitle="No problem looms"
            columns={[
              { key: 'l', header: 'Loom', value: (r) => r.loom_id, render: (r) => <Link to={loomLink(r.loom_id)} className="font-medium hover:underline">{r.loom_id}</Link> },
              { key: 'e', header: 'Efficiency', align: 'right', value: (r) => r.efficiency_pct, render: (r) => pct(r.efficiency_pct) },
              { key: 'i', header: 'Issue', value: (r) => r.main_issue, render: (r) => r.main_issue },
              { key: 'x', header: 'Lost', align: 'right', value: (r) => r.loss_lakhs, render: (r) => inrFromLakhs(r.loss_lakhs) },
              { key: 'h', header: '', render: (r) => <StatusPill tone={sevTone(r.health)} label={r.health === 'CRITICAL' ? 'Critical' : 'Watch'} /> },
            ]}
          />
        </Card>
        <Card>
          <CardHeader
            title="Open actions"
            subtitle="Assigned work still to be finished"
            actions={
              <Link to={{ pathname: '/weaving/people', search: '?tab=actions' }} className="text-xs text-accent-ink hover:underline">
                All
              </Link>
            }
          />
          <ul className="divide-y divide-line border-t border-line">
            {openActions.map((a) => (
              <li key={a.id} className="flex items-start justify-between gap-3 px-5 py-3">
                <div className="min-w-0">
                  <div className="text-sm font-medium text-ink">{a.issue}</div>
                  <div className="text-xs text-ink-3">{a.action}</div>
                  <div className="mt-0.5 text-xs text-ink-3">
                    {a.owner} · due {a.due}
                  </div>
                </div>
                <StatusPill status={a.status} label={a.status === 'OPEN' ? 'Open' : 'In progress'} />
              </li>
            ))}
          </ul>
        </Card>
      </div>

      {escalations.length > 0 && (
        <Card>
          <CardHeader title="Escalations to the owner" subtitle="The same decisions the owner sees. Resolve them, or raise them early." />
          <ul className="divide-y divide-line border-t border-line">
            {escalations.map((x) => (
              <li key={x.id} className="flex items-center gap-3 px-5 py-3">
                <StatusPill tone={sevTone(x.severity)} label={SEV_LABEL[x.severity]} />
                <div className="min-w-0 flex-1">
                  <div className="text-sm font-medium text-ink">{x.title}</div>
                  <div className="truncate text-xs text-ink-3">{x.action}</div>
                </div>
                <Link
                  to={{ pathname: x.link.split('?')[0], search: x.link.includes('?') ? `?${x.link.split('?')[1]}` : search }}
                  className="shrink-0 text-xs text-accent-ink hover:underline"
                >
                  Evidence
                </Link>
              </li>
            ))}
          </ul>
        </Card>
      )}

      <ChartPanel
        title="Efficiency and first-grade trend"
        subtitle="Daily, with the 92% efficiency target"
        rows={d.trend}
        rowKey={(r) => r.date_label}
        exportName="weaving-efficiency"
        chart={
          <TrendChart
            data={d.trend}
            xKey="date_label"
            format={(v) => `${v.toFixed(1)}%`}
            series={[
              { key: 'efficiency_pct', label: 'Efficiency', color: 0 },
              { key: 'grade_a_pct', label: 'First grade', color: 1 },
            ]}
            reference={{ value: 92, label: 'Target' }}
            yDomain={[80, 100]}
            height={240}
          />
        }
        columns={[
          { key: 'd', header: 'Date', value: (r) => r.date_label, render: (r) => r.date_label },
          { key: 'e', header: 'Efficiency', align: 'right', value: (r) => r.efficiency_pct, render: (r) => pct(r.efficiency_pct) },
          { key: 'g', header: 'First grade', align: 'right', value: (r) => r.grade_a_pct, render: (r) => pct(r.grade_a_pct) },
        ]}
      />
    </>
  );
};
