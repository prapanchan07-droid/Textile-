import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { ArrowRight, ChevronRight, MapPin } from 'lucide-react';
import { useDecisionCenter } from '../../api/queries';
import { usePeriod } from '../../app/state';
import { periodLabel } from '../../lib/period';
import { kg, kgExact, minutes, pct, stripEmoji } from '../../lib/format';
import { routeFor } from '../../lib/links';
import type { ActionTrackerItem, DecisionCenterData } from '../../types/decisionCenter';
import { PageHeader } from '../../layout/PageHeader';
import { QueryView } from '../../design/QueryView';
import { Button, Card, CardBody, CardHeader, Meter, Notice, Segmented, StatusPill, toneOf, type Tone } from '../../design/ui';
import { DataTable } from '../../design/DataTable';
import { RankedBars } from '../../design/charts/Charts';

export const ActionCenterPage: React.FC = () => {
  const [period] = usePeriod();
  const query = useDecisionCenter(period);
  return (
    <>
      <PageHeader
        title="Action Center"
        description={`The top issue for ${periodLabel(period).toLowerCase()}, why it happened, and what to do next`}
        showPeriod
      />
      <QueryView query={query}>{(d) => <ActionCenterBody data={d} />}</QueryView>
    </>
  );
};

const ActionCenterBody: React.FC<{ data: DecisionCenterData }> = ({ data }) => {
  const top = data.top_priority;
  const where = data.where_location;
  const gap = Math.abs(top.gap_kg);
  const priorityTone: Tone = toneOf(top.priority_level);

  return (
    <div className="space-y-4">
      {/* Top priority: the one thing leadership should look at first */}
      <Card className="overflow-hidden">
        <div className="grid lg:grid-cols-5">
          <div className="space-y-4 p-5 lg:col-span-3">
            <div className="flex flex-wrap items-center gap-2">
              <StatusPill
                tone={priorityTone}
                label={`${top.priority_level.toLowerCase()} priority`.replace(/^\w/, (c) => c.toUpperCase())}
              />
              <span className="text-xs text-ink-3">Top priority</span>
            </div>
            <div>
              <h2 className="text-lg font-semibold text-ink">{top.title}</h2>
              <p className="mt-0.5 text-sm text-ink-2">{top.sub_highlight}</p>
            </div>
            <dl className="grid grid-cols-2 gap-x-6 gap-y-3 text-sm sm:grid-cols-3">
              <Fact label="Main contributor" value={top.main_contributor} />
              <Fact label="Most affected" value={`${top.most_affected_machine_id} · ${top.most_affected_machine_type}`} />
              <Fact label="Projected 30-day gap" value={kg(Math.abs(data.if_continues.projected_30d_gap_kg))} />
            </dl>
            <div className="space-y-1.5">
              <div className="flex justify-between text-xs text-ink-3">
                <span>
                  Actual <span className="num font-medium text-ink">{kgExact(top.actual_kg)}</span>
                </span>
                <span>
                  Target <span className="num font-medium text-ink">{kgExact(top.target_kg)}</span>
                </span>
              </div>
              <Meter value={top.actual_kg} max={top.target_kg} tone={priorityTone} />
              {gap > 0 && <div className="text-xs text-ink-3">{kgExact(gap)} short of target</div>}
            </div>
          </div>
          <div className="border-t border-line bg-subtle p-5 lg:col-span-2 lg:border-l lg:border-t-0">
            <div className="mb-2 text-2xs font-medium uppercase tracking-wide text-ink-3">Evidence</div>
            <ul className="space-y-2 text-sm text-ink-2">
              {data.ai_insight.facts.map((f) => (
                <li key={f} className="flex gap-2">
                  <span className="mt-2 size-1 shrink-0 rounded-full bg-ink-3" />
                  {f}
                </li>
              ))}
            </ul>
            <Link to={`/assets?machine=${encodeURIComponent(top.most_affected_machine_id)}`} className="mt-4 inline-block">
              <Button variant="primary" size="sm">
                Investigate {top.most_affected_machine_id} <ArrowRight className="size-3.5" />
              </Button>
            </Link>
          </div>
        </div>
      </Card>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader title="Why it happened" subtitle="Share of the production gap by cause" />
          <CardBody>
            <RankedBars
              format={(v) => `${v.toFixed(0)}%`}
              items={data.why_contributors.map((c) => ({ label: c.category, value: c.percentage, sublabel: c.detail_text }))}
            />
          </CardBody>
        </Card>

        <Card>
          <CardHeader title="Where it happened" subtitle="Machines contributing to the gap" />
          <CardBody className="space-y-3">
            <Link
              to={`/assets?machine=${encodeURIComponent(where.primary_machine_id)}`}
              className="block rounded-md border border-line p-3 hover:border-line-strong"
            >
              <div className="flex items-center justify-between gap-2">
                <div className="flex items-center gap-2">
                  <MapPin className="size-4 text-ink-3" />
                  <span className="font-semibold text-ink">{where.primary_machine_id}</span>
                  <span className="text-xs text-ink-3">
                    {where.primary_machine_type} · {where.primary_section}
                  </span>
                </div>
                <StatusPill status={stripEmoji(where.status)} />
              </div>
              <div className="mt-3 grid grid-cols-3 gap-3 text-sm">
                <Fact label="Loss" value={kgExact(Math.abs(where.production_loss_kg))} />
                <Fact label="Efficiency" value={pct(where.efficiency_pct)} />
                <Fact label="Downtime" value={minutes(where.downtime_minutes)} />
              </div>
            </Link>
            <ul className="divide-y divide-line rounded-md border border-line">
              {where.secondary_machines.map((m) => (
                <li key={m.machine_id}>
                  <Link
                    to={`/assets?machine=${encodeURIComponent(m.machine_id)}`}
                    className="flex h-10 items-center justify-between gap-3 px-3 text-sm hover:bg-subtle"
                  >
                    <span className="flex items-center gap-2">
                      <StatusPill tone={toneOf(m.status_color)} label={toneOf(m.status_color) === 'bad' ? 'Critical' : 'Attention'} />
                      <span className="font-medium text-ink">{m.machine_id}</span>
                      <span className="text-xs text-ink-3">{m.machine_type}</span>
                    </span>
                    <span className="num text-ink-2">{kgExact(Math.abs(m.loss_kg))}</span>
                  </Link>
                </li>
              ))}
            </ul>
          </CardBody>
        </Card>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader title="Recommended next steps" subtitle={data.ai_insight.recommended_focus} />
          <ol className="divide-y divide-line border-t border-line">
            {data.recommended_actions.map((a) => (
              <li key={a.id} className="flex items-center gap-3 px-4 py-3">
                <span className="num flex size-6 shrink-0 items-center justify-center rounded-full bg-accent-soft text-xs font-semibold text-accent-ink">
                  {a.step_number}
                </span>
                <span className="flex-1 text-sm text-ink">{a.action_text}</span>
                <Link to={routeFor(a.target_tab, a.target_id, a.action_text)}>
                  <Button size="sm" variant="ghost">
                    {a.button_label} <ChevronRight className="size-3.5" />
                  </Button>
                </Link>
              </li>
            ))}
          </ol>
        </Card>

        <Card>
          <CardHeader title="Other open issues" subtitle="Across quality, people, energy and finance" />
          <ul className="divide-y divide-line border-t border-line">
            {data.other_issues.map((i) => (
              <li key={i.id}>
                <Link
                  to={routeFor(i.target_tab, undefined, `${i.category} ${i.location_or_area} ${i.impact_detail}`)}
                  className="flex items-center gap-3 px-4 py-3 hover:bg-subtle"
                >
                  <StatusPill tone={i.status_icon.includes('🟡') ? 'warn' : 'bad'} label={i.status_icon.includes('🟡') ? 'Watch' : 'Act'} />
                  <div className="min-w-0 flex-1">
                    <div className="text-sm font-medium text-ink">{i.category}</div>
                    <div className="truncate text-xs text-ink-3">
                      {i.location_or_area} · {i.impact_detail}
                    </div>
                  </div>
                  <ChevronRight className="size-4 text-ink-3" />
                </Link>
              </li>
            ))}
          </ul>
        </Card>
      </div>

      <ActionLog items={data.action_tracker} />
    </div>
  );
};

const Fact: React.FC<{ label: string; value: React.ReactNode }> = ({ label, value }) => (
  <div className="min-w-0">
    <dt className="text-xs text-ink-3">{label}</dt>
    <dd className="truncate font-medium text-ink">{value}</dd>
  </div>
);

type StatusFilter = 'ALL' | 'OPEN' | 'IN_PROGRESS' | 'COMPLETED';

const ActionLog: React.FC<{ items: ActionTrackerItem[] }> = ({ items }) => {
  const [filter, setFilter] = useState<StatusFilter>('ALL');
  const count = (s: StatusFilter) => items.filter((i) => s === 'ALL' || i.status === s).length;
  const rows = items.filter((i) => filter === 'ALL' || i.status === filter);
  return (
    <Card>
      <CardHeader
        title="Action log"
        subtitle="Corrective actions and their owners"
        actions={
          <Segmented
            size="sm"
            value={filter}
            onChange={setFilter}
            options={[
              { value: 'ALL', label: `All ${count('ALL')}` },
              { value: 'OPEN', label: `Open ${count('OPEN')}` },
              { value: 'IN_PROGRESS', label: `In progress ${count('IN_PROGRESS')}` },
              { value: 'COMPLETED', label: `Done ${count('COMPLETED')}` },
            ]}
          />
        }
      />
      <div className="px-4 pb-3">
        <Notice tone="info">
          Read-only: the API has no endpoint to create or update actions yet, so status changes here would be lost on refresh.
        </Notice>
      </div>
      <DataTable
        rows={rows}
        rowKey={(r) => r.id}
        exportName="action-log"
        columns={[
          { key: 'issue', header: 'Issue', value: (r) => r.issue, render: (r) => <span className="font-medium">{r.issue}</span> },
          {
            key: 'action',
            header: 'Action',
            wrap: true,
            value: (r) => r.action,
            render: (r) => <span className="text-ink-2">{r.action}</span>,
          },
          { key: 'owner', header: 'Owner', hideBelow: 'md', value: (r) => r.owner, render: (r) => r.owner },
          { key: 'status', header: 'Status', value: (r) => r.status, render: (r) => <StatusPill status={r.status} /> },
          { key: 'date', header: 'Raised', align: 'right', hideBelow: 'sm', value: (r) => r.created_date, render: (r) => r.created_date },
        ]}
      />
    </Card>
  );
};
