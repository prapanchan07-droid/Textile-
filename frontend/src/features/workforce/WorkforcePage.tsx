import React from 'react';
import { useManpowerQuality } from '../../api/queries';
import { usePeriod } from '../../app/state';
import { num, pct } from '../../lib/format';
import type { DepartmentManpowerItem, ManpowerQualityModuleData } from '../../types/manpowerQuality';
import { PageHeader } from '../../layout/PageHeader';
import { QueryView } from '../../design/QueryView';
import { Card, CardHeader, Kpi, KpiGrid, Meter, type Tone } from '../../design/ui';
import { DataTable } from '../../design/DataTable';
import { ChartPanel } from '../../design/ChartPanel';
import { TrendChart } from '../../design/charts/Charts';
import { AttentionList, isQualityItem } from '../quality/QualityPage';

const attendanceTone = (a: number): Tone => (a >= 97 ? 'ok' : a >= 94 ? 'warn' : 'bad');

export const WorkforcePage: React.FC = () => {
  const [period] = usePeriod();
  const query = useManpowerQuality(period);
  return (
    <>
      <PageHeader title="Workforce" description="Sanctioned strength, availability and attendance by department" showPeriod />
      <QueryView query={query}>{(d) => <WorkforceBody data={d} />}</QueryView>
    </>
  );
};

const WorkforceBody: React.FC<{ data: ManpowerQualityModuleData }> = ({ data }) => {
  const s = data.manpower_summary;
  const worst = [...data.department_gaps].sort((a, b) => a.gap - b.gap)[0];
  return (
    <div className="space-y-4">
      <KpiGrid className="xl:grid-cols-5">
        <Kpi label="Sanctioned strength" value={num(s.required)} hint="workers required" />
        <Kpi label="Available" value={num(s.available)} />
        <Kpi
          label="Shortage"
          value={num(s.shortage)}
          status={s.shortage > 0 ? 'warn' : 'ok'}
          hint={s.required ? `${((s.shortage / s.required) * 100).toFixed(1)}% of strength` : undefined}
        />
        <Kpi label="Attendance" value={pct(s.attendance_pct)} status={attendanceTone(s.attendance_pct)} />
        <Kpi label="Largest gap" value={worst ? worst.department : '—'} hint={worst ? `${num(Math.abs(worst.gap))} short` : undefined} />
      </KpiGrid>

      <div className="grid gap-4 lg:grid-cols-5">
        <Card className="lg:col-span-3">
          <CardHeader title="By department" subtitle="Largest shortfall first" />
          <DataTable<DepartmentManpowerItem>
            rows={data.department_gaps}
            rowKey={(r) => r.department}
            exportName="manpower-by-department"
            initialSort={{ key: 'gap', dir: 'asc' }}
            columns={[
              {
                key: 'dept',
                header: 'Department',
                value: (r) => r.department,
                render: (r) => <span className="font-medium">{r.department}</span>,
              },
              { key: 'req', header: 'Required', align: 'right', value: (r) => r.required, render: (r) => num(r.required) },
              { key: 'avail', header: 'Available', align: 'right', value: (r) => r.available, render: (r) => num(r.available) },
              {
                key: 'gap',
                header: 'Gap',
                align: 'right',
                value: (r) => r.gap,
                render: (r) => (
                  <span className={r.gap < -10 ? 'font-medium text-bad' : r.gap < 0 ? 'text-warn' : ''}>
                    {r.gap < 0 ? `−${Math.abs(r.gap)}` : r.gap}
                  </span>
                ),
              },
              {
                key: 'att',
                header: 'Attendance',
                value: (r) => r.attendance_pct,
                render: (r) => (
                  <div className="flex w-32 items-center gap-2">
                    <Meter value={r.attendance_pct} max={100} tone={attendanceTone(r.attendance_pct)} />
                    <span className="num w-11 shrink-0 text-right text-xs">{pct(r.attendance_pct)}</span>
                  </div>
                ),
              },
            ]}
          />
        </Card>
        <AttentionList title="People alerts" items={data.needs_attention.filter((a) => !isQualityItem(a))} />
      </div>

      <ChartPanel
        title="Availability trend"
        subtitle="Workers available against sanctioned strength"
        rows={data.manpower_trend}
        rowKey={(r) => r.date_label}
        exportName="manpower-trend"
        chart={
          <TrendChart
            data={data.manpower_trend}
            xKey="date_label"
            format={(v) => num(v)}
            series={[
              { key: 'available', label: 'Available', color: 0 },
              { key: 'required', label: 'Required', color: 'muted' },
            ]}
            height={240}
          />
        }
        columns={[
          { key: 'd', header: 'Date', value: (r) => r.date_label, render: (r) => r.date_label },
          { key: 'r', header: 'Required', align: 'right', value: (r) => r.required, render: (r) => num(r.required) },
          { key: 'a', header: 'Available', align: 'right', value: (r) => r.available, render: (r) => num(r.available) },
          { key: 's', header: 'Shortage', align: 'right', value: (r) => r.shortage, render: (r) => num(r.shortage) },
          { key: 'att', header: 'Attendance', align: 'right', value: (r) => r.attendance_pct, render: (r) => pct(r.attendance_pct) },
        ]}
      />
    </div>
  );
};
