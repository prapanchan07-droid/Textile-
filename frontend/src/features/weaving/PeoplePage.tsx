import React from 'react';
import { Link } from 'react-router-dom';
import { useParam } from '../../app/state';
import { inrFromLakhs, meters, num, pct } from '../../lib/format';
import { Card, CardBody, CardHeader, Kpi, KpiGrid, Notice, Segmented, StatusPill } from '../../design/ui';
import { DataTable } from '../../design/DataTable';
import { RankedBars } from '../../design/charts/Charts';
import type { WeavingAction, WeavingModuleData, WeavingPmItem } from '../../types/weaving';
import { sevTone, WeavingPage } from './shared';

type Tab = 'people' | 'maintenance' | 'actions';

export const PeoplePage: React.FC = () => {
  const [tab, setTab] = useParam('tab', 'people');
  return (
    <WeavingPage
      description="Staffing, preventive maintenance and the action list for the weaving floor"
      actions={
        <Segmented<Tab>
          ariaLabel="Section"
          value={tab as Tab}
          onChange={setTab}
          options={[
            { value: 'people', label: 'People' },
            { value: 'maintenance', label: 'Maintenance' },
            { value: 'actions', label: 'Actions' },
          ]}
        />
      }
    >
      {(d) => (tab === 'maintenance' ? <Maintenance d={d} /> : tab === 'actions' ? <Actions d={d} /> : <People d={d} />)}
    </WeavingPage>
  );
};

const People: React.FC<{ d: WeavingModuleData }> = ({ d }) => {
  const p = d.people;
  return (
    <>
      <Notice tone="info">Shown as department and shift totals only. Individual employee pay and grades are not displayed here.</Notice>
      <KpiGrid>
        <Kpi label="Headcount" value={num(p.headcount)} hint="weaving section" />
        <Kpi label="Present today" value={num(p.available_today)} />
        <Kpi label="Absenteeism" value={pct(p.absenteeism_pct)} status={p.absenteeism_pct > 10 ? 'bad' : p.absenteeism_pct > 6 ? 'warn' : 'ok'} hint="target under 6%" />
        <Kpi label="Ready for promotion" value={num(p.promotion_ready)} hint="grade review due" status="ok" />
        <Kpi label="Need training" value={num(p.needs_training)} hint="below grade output" status={p.needs_training ? 'warn' : 'ok'} />
        <Kpi label="Shifts short" value={String(p.shifts.filter((s) => s.status !== 'NORMAL').length)} status="warn" />
      </KpiGrid>
      <div className="grid gap-4 lg:grid-cols-5">
        <Card className="lg:col-span-3">
          <CardHeader title="Staffing by department" subtitle="Required against present today. Largest gap first." />
          <DataTable
            rows={p.departments}
            rowKey={(r) => r.department}
            dense
            initialSort={{ key: 'gap', dir: 'desc' }}
            exportName="weaving-staffing"
            columns={[
              { key: 'd', header: 'Department', value: (r) => r.department, render: (r) => <span className="font-medium">{r.department}</span> },
              { key: 'r', header: 'Required', align: 'right', value: (r) => r.required, render: (r) => r.required },
              { key: 'a', header: 'Present', align: 'right', value: (r) => r.available, render: (r) => r.available },
              { key: 'gap', header: 'Gap', align: 'right', value: (r) => r.gap, render: (r) => <span className={r.gap >= 3 ? 'font-semibold text-bad' : ''}>{r.gap}</span> },
              { key: 'g', header: 'Typical grade', hideBelow: 'md', value: (r) => r.avg_grade, render: (r) => r.avg_grade },
              { key: 's', header: '', render: (r) => <StatusPill tone={sevTone(r.status)} label={r.status === 'NORMAL' ? 'Covered' : r.status === 'CRITICAL' ? 'Short' : 'Thin'} /> },
            ]}
          />
        </Card>
        <Card className="lg:col-span-2">
          <CardHeader title="Skill grades" subtitle="Number of workers in each grade" />
          <CardBody>
            <RankedBars items={p.grades.map((g) => ({ label: g.grade, value: g.count }))} format={(v) => String(v)} />
          </CardBody>
        </Card>
      </div>
      <Card>
        <CardHeader title="Weaver load by shift" subtitle="Looms per weaver. About 2.4 is the safe limit for this mix." />
        <DataTable
          rows={p.shifts}
          rowKey={(r) => r.shift}
          dense
          columns={[
            { key: 's', header: 'Shift', value: (r) => r.shift, render: (r) => <span className="font-medium">{r.shift}</span> },
            { key: 'a', header: 'Absent', align: 'right', value: (r) => r.absent, render: (r) => r.absent },
            { key: 'l', header: 'Looms per weaver', align: 'right', value: (r) => r.looms_per_weaver, render: (r) => r.looms_per_weaver.toFixed(1) },
            { key: 'o', header: 'Output per weaver', align: 'right', value: (r) => r.output_per_weaver_m, render: (r) => meters(r.output_per_weaver_m) },
            { key: 'st', header: '', render: (r) => <StatusPill tone={sevTone(r.status)} label={r.status === 'NORMAL' ? 'OK' : r.status === 'CRITICAL' ? 'Overloaded' : 'Heavy'} /> },
          ]}
        />
      </Card>
    </>
  );
};

const pmTone = (s: WeavingPmItem['status']) => (s === 'OVERDUE' ? 'bad' : s === 'DUE_SOON' ? 'warn' : 'ok');

const Maintenance: React.FC<{ d: WeavingModuleData }> = ({ d }) => {
  const m = d.maintenance;
  return (
    <>
      <KpiGrid>
        <Kpi label="Overdue PM jobs" value={num(m.pm_overdue)} status={m.pm_overdue > 4 ? 'bad' : m.pm_overdue ? 'warn' : 'ok'} />
        <Kpi label="Due in 5 days" value={num(m.pm_due_soon)} />
        <Kpi label="PM compliance" value={pct(m.pm_compliance_pct)} hint="target 95%" status={m.pm_compliance_pct >= 95 ? 'ok' : 'warn'} />
        <Kpi label="Breakdowns" value={num(m.breakdowns)} hint={d.period_label.toLowerCase()} />
        <Kpi label="MTBF" value={`${m.mtbf_hours} h`} hint="running time between breakdowns" />
        <Kpi label="MTTR" value={`${m.mttr_min} min`} hint="average time to repair" />
      </KpiGrid>
      <Card>
        <CardHeader title="Preventive maintenance to do" subtitle="Overdue first. Overdue service on weak looms raises breakdown risk." />
        <DataTable<WeavingPmItem>
          rows={m.items}
          rowKey={(r) => `${r.loom_id}-${r.task}`}
          exportName="weaving-pm"
          searchable={(r) => `${r.loom_id} ${r.task}`}
          columns={[
            { key: 'l', header: 'Loom', value: (r) => r.loom_id, render: (r) => <Link to={{ pathname: '/weaving/looms', search: `?loom=${r.loom_id}` }} className="font-medium hover:underline">{r.loom_id}</Link> },
            { key: 't', header: 'Task', value: (r) => r.task, render: (r) => r.task },
            { key: 'd', header: 'Due', value: (r) => r.due_date, render: (r) => r.due_date },
            { key: 'o', header: 'Days late', align: 'right', value: (r) => r.days_overdue, render: (r) => (r.days_overdue ? r.days_overdue : '—') },
            { key: 's', header: 'Status', value: (r) => r.status, render: (r) => <StatusPill tone={pmTone(r.status)} label={r.status === 'OVERDUE' ? 'Overdue' : 'Due soon'} /> },
          ]}
        />
      </Card>
    </>
  );
};

const Actions: React.FC<{ d: WeavingModuleData }> = ({ d }) => (
  <>
    <Notice tone="info">This list is read-only for now. Status changes will be saved once the actions service is connected.</Notice>
    <Card>
      <CardHeader title="Weaving actions" subtitle={`${d.actions.filter((a) => a.status !== 'COMPLETED').length} open`} />
      <DataTable<WeavingAction>
        rows={d.actions}
        rowKey={(r) => r.id}
        exportName="weaving-actions"
        columns={[
          { key: 'i', header: 'Issue', wrap: true, value: (r) => r.issue, render: (r) => <div><div className="font-medium">{r.issue}</div><div className="text-xs text-ink-3">{r.action}</div></div> },
          { key: 'o', header: 'Owner', hideBelow: 'md', value: (r) => r.owner, render: (r) => r.owner },
          { key: 'd', header: 'Due', value: (r) => r.due, render: (r) => r.due },
          { key: 'm', header: 'At stake', align: 'right', hideBelow: 'sm', value: (r) => r.impact_lakhs, render: (r) => inrFromLakhs(r.impact_lakhs) },
          { key: 's', header: 'Status', value: (r) => r.status, render: (r) => <StatusPill status={r.status} label={r.status === 'OPEN' ? 'Open' : r.status === 'COMPLETED' ? 'Done' : 'In progress'} /> },
        ]}
      />
    </Card>
  </>
);
