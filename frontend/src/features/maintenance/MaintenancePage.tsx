import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { Plus } from 'lucide-react';
import { api, useMillMutation, useWorkOrders } from '../../api/mill';
import { QueryView } from '../../design/QueryView';
import { DataTable, type Column } from '../../design/DataTable';
import { Drawer } from '../../design/Drawer';
import { Badge, Button, Card, CardBody, Notice, StatusPill, Tabs } from '../../design/ui';
import { Field, PageTitle, fmt, inputClass } from '../common/parts';
import { WorkOrderDrawer } from './WorkOrderDrawer';
import type { WorkOrder } from '../../types/mill';

const cols: Column<WorkOrder>[] = [
  { key: 'id', header: '#', render: (w) => w.id, value: (w) => w.id },
  { key: 'loom', header: 'Loom', render: (w) => <Link to={`/looms/${w.loom.id}`} className="hover:text-accent">{w.loom.code}</Link>, value: (w) => w.loom.code },
  { key: 'kind', header: 'Type', render: (w) => w.kind.toLowerCase(), value: (w) => w.kind },
  { key: 'title', header: 'Work', render: (w) => <span className="text-ink">{w.title}</span>, value: (w) => w.title, wrap: true },
  { key: 'pri', header: 'Priority', render: (w) => <StatusPill status={w.priority} />, value: (w) => w.priority },
  { key: 'status', header: 'Status', render: (w) => <span className="inline-flex gap-1"><StatusPill status={w.status} />{w.overdue && <Badge tone="bad">Overdue</Badge>}</span>, value: (w) => w.status },
  { key: 'who', header: 'Technician', render: (w) => w.assignee?.name ?? '—', value: (w) => w.assignee?.name, hideBelow: 'md' },
  { key: 'due', header: 'Planned', render: (w) => fmt.date(w.due_date), value: (w) => w.due_date, hideBelow: 'lg' },
  { key: 'rep', header: 'Reported', render: (w) => fmt.dateTime(w.reported_at), value: (w) => w.reported_at, hideBelow: 'lg' },
  { key: 'dt', header: 'Downtime', align: 'right', render: (w) => (w.downtime_min != null ? `${fmt.n(w.downtime_min)} min` : '—'), value: (w) => w.downtime_min, hideBelow: 'xl' },
];

export const MaintenancePage: React.FC = () => {
  const [tab, setTab] = useState<'OPEN' | 'COMPLETED' | ''>('OPEN');
  const q = useWorkOrders({ status: tab || undefined, page_size: 200 });
  const [creating, setCreating] = useState(false);
  const [sel, setSel] = useState<WorkOrder | null>(null);
  return (
    <>
      <PageTitle title="Maintenance and work orders" subtitle="Breakdowns, preventive work and inspections per loom. Downtime and causes are entered by maintenance, never inferred."
        actions={<Button variant="primary" icon={<Plus className="size-4" />} onClick={() => setCreating(true)}>Work order</Button>} />
      <div className="mb-3"><Tabs value={tab} onChange={setTab} tabs={[{ value: 'OPEN', label: 'Open' }, { value: 'COMPLETED', label: 'Completed' }, { value: '', label: 'All' }]} /></div>
      <QueryView query={q}>
        {(d) => <Card><CardBody className="pt-4"><DataTable rows={d.items} columns={cols} rowKey={(w) => String(w.id)} onRowClick={setSel} searchable={(w) => `${w.loom.code} ${w.title}`} exportName="work-orders" emptyTitle="No work orders" /></CardBody></Card>}
      </QueryView>
      <WorkOrderDrawer open={creating} onClose={() => setCreating(false)} />
      {sel && <Edit wo={sel} onClose={() => setSel(null)} />}
    </>
  );
};

const Edit: React.FC<{ wo: WorkOrder; onClose: () => void }> = ({ wo, onClose }) => {
  const [f, setF] = useState({ status: wo.status, downtime_min: wo.downtime_min?.toString() ?? '', cause: wo.cause ?? '', resolution: wo.resolution ?? '' });
  const save = useMillMutation((body: object) => api.patch(`/mill/work-orders/${wo.id}`, body));
  const set = (k: keyof typeof f) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => setF((x) => ({ ...x, [k]: e.target.value }));
  return (
    <Drawer open onClose={onClose} title={`#${wo.id} ${wo.title}`} subtitle={`${wo.loom.code} · ${wo.kind.toLowerCase()} · reported ${fmt.dateTime(wo.reported_at)}`}
      footer={<div className="flex justify-end gap-2"><Button onClick={onClose}>Close</Button>
        <Button variant="primary" loading={save.isPending} onClick={() => save.mutate({ status: f.status, downtime_min: f.downtime_min === '' ? null : Number(f.downtime_min),
                                                                                      cause: f.cause || null, resolution: f.resolution || null }, { onSuccess: onClose })}>Save</Button></div>}>
      <div className="space-y-3">
        {save.isError && <Notice tone="bad">{(save.error as Error).message}</Notice>}
        {wo.description && <p className="text-sm text-ink-2">{wo.description}</p>}
        <Field label="Status">
          <select className={inputClass} value={f.status} onChange={set('status')}>{['OPEN', 'IN_PROGRESS', 'ON_HOLD', 'COMPLETED', 'CANCELLED'].map((s) => <option key={s}>{s}</option>)}</select>
        </Field>
        <Field label="Downtime (minutes)" hint="Measured or recorded by maintenance"><input type="number" min={0} className={inputClass} value={f.downtime_min} onChange={set('downtime_min')} /></Field>
        <Field label="Confirmed cause"><textarea className={`${inputClass} h-16 py-2`} value={f.cause} onChange={set('cause')} /></Field>
        <Field label="Work done" hint="Required to complete"><textarea className={`${inputClass} h-20 py-2`} value={f.resolution} onChange={set('resolution')} /></Field>
        <p className="text-2xs text-ink-3">Started {fmt.dateTime(wo.started_at)} · completed {fmt.dateTime(wo.completed_at)}</p>
      </div>
    </Drawer>
  );
};
