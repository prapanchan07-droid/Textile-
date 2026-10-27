import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { Plus } from 'lucide-react';
import { api, useMillMutation, useTask, useTasks } from '../../api/mill';
import { useParam } from '../../app/state';
import { QueryView } from '../../design/QueryView';
import { DataTable, type Column } from '../../design/DataTable';
import { Drawer } from '../../design/Drawer';
import { Badge, Button, Card, CardBody, Notice, StatusPill, Tabs } from '../../design/ui';
import { Field, PageTitle, fmt, inputClass } from '../common/parts';
import { TaskDrawer } from '../common/TaskDrawer';
import type { Task } from '../../types/mill';

const cols: Column<Task>[] = [
  { key: 'id', header: '#', render: (t) => t.id, value: (t) => t.id },
  { key: 'title', header: 'Task', render: (t) => <span className="text-ink">{t.title}</span>, value: (t) => t.title, wrap: true },
  { key: 'status', header: 'Status', render: (t) => <span className="inline-flex gap-1"><StatusPill status={t.status} />{t.overdue && <Badge tone="bad">Overdue</Badge>}{t.escalated_to_owner && <Badge tone="info">Owner</Badge>}</span>, value: (t) => t.status },
  { key: 'pri', header: 'Priority', render: (t) => <StatusPill status={t.priority} />, value: (t) => ({ CRITICAL: 0, HIGH: 1, MEDIUM: 2, LOW: 3 })[t.priority] },
  { key: 'group', header: 'Group', render: (t) => t.group?.name ?? '—', value: (t) => t.group?.name, hideBelow: 'md' },
  { key: 'who', header: 'Person', render: (t) => t.assignee?.name ?? '—', value: (t) => t.assignee?.name, hideBelow: 'lg' },
  { key: 'loom', header: 'Loom', render: (t) => (t.loom ? <Link to={`/looms/${t.loom.id}`} className="hover:text-accent">{t.loom.code}</Link> : '—'), value: (t) => t.loom?.code, hideBelow: 'lg' },
  { key: 'due', header: 'Due', render: (t) => fmt.dateTime(t.due_at), value: (t) => t.due_at },
];

const NEXT: Record<Task['status'], Task['status'][]> = {
  PENDING: ['IN_PROGRESS', 'BLOCKED', 'COMPLETED'], IN_PROGRESS: ['BLOCKED', 'COMPLETED', 'PENDING'], BLOCKED: ['IN_PROGRESS', 'PENDING', 'COMPLETED'],
  COMPLETED: ['REOPENED'], REOPENED: ['IN_PROGRESS', 'BLOCKED', 'COMPLETED'],
};

export const TasksPage: React.FC = () => {
  const [tab, setTab] = useParam('status', 'OPEN');
  const [id, setId] = useParam('id');
  const q = useTasks({ status: tab === 'OVERDUE' ? 'OPEN' : tab || undefined, overdue: tab === 'OVERDUE' ? 'true' : undefined, page_size: 300 });
  const [creating, setCreating] = useState(false);
  return (
    <>
      <PageTitle title="Tasks" subtitle="Work assigned by the GM to groups and people, with its history. Completing needs a note of what was done."
        actions={<Button variant="primary" icon={<Plus className="size-4" />} onClick={() => setCreating(true)}>Task</Button>} />
      <div className="mb-3"><Tabs value={tab} onChange={setTab} tabs={[{ value: 'OPEN', label: 'Open' }, { value: 'OVERDUE', label: 'Overdue' }, { value: 'BLOCKED', label: 'Blocked' }, { value: 'COMPLETED', label: 'Completed' }, { value: '', label: 'All' }]} /></div>
      <QueryView query={q}>
        {(d) => <Card><CardBody className="pt-4"><DataTable rows={d.items} columns={cols} rowKey={(t) => String(t.id)} onRowClick={(t) => setId(String(t.id))} selectedKey={id}
          searchable={(t) => `${t.title} ${t.group?.name ?? ''} ${t.loom?.code ?? ''}`} exportName="tasks" emptyTitle="No tasks here" /></CardBody></Card>}
      </QueryView>
      <TaskDrawer open={creating} onClose={() => setCreating(false)} />
      {id && <TaskDetail id={Number(id)} onClose={() => setId(null)} />}
    </>
  );
};

const TaskDetail: React.FC<{ id: number; onClose: () => void }> = ({ id, onClose }) => {
  const q = useTask(id);
  const t = q.data;
  const [note, setNote] = useState('');
  const [done, setDone] = useState('');
  const patch = useMillMutation((b: object) => api.patch<Task>(`/mill/tasks/${id}`, b));
  const go = (b: object) => patch.mutate(b, { onSuccess: () => { setNote(''); q.refetch(); } });
  return (
    <Drawer open onClose={onClose} title={t ? `#${t.id} ${t.title}` : 'Task'} subtitle={t ? `${t.group?.name ?? 'No group'} · ${t.assignee?.name ?? 'no person'} · due ${fmt.dateTime(t.due_at)}` : undefined}>
      {t && (
        <div className="space-y-4 text-sm">
          {patch.isError && <Notice tone="bad">{(patch.error as Error).message}</Notice>}
          <div className="flex flex-wrap gap-2"><StatusPill status={t.status} /><StatusPill status={t.priority} />{t.overdue && <Badge tone="bad">Overdue</Badge>}
            {t.loom && <Link to={`/looms/${t.loom.id}`} className="text-xs text-accent hover:underline">{t.loom.code}</Link>}
            {t.alert_id && <Link to={`/alerts?id=${t.alert_id}`} className="text-xs text-accent hover:underline">Alert #{t.alert_id}</Link>}</div>
          {t.description && <p className="whitespace-pre-wrap text-ink-2">{t.description}</p>}
          {t.expected_outcome && <p className="text-xs"><span className="text-ink-3">Expected outcome:</span> {t.expected_outcome}</p>}
          {t.completion_notes && <Notice tone="ok">Done: {t.completion_notes}</Notice>}
          <Field label="Note" hint="Required to block a task; added to the history">
            <textarea className={`${inputClass} h-16 py-2`} value={note} onChange={(e) => setNote(e.target.value)} />
          </Field>
          {NEXT[t.status].includes('COMPLETED') && (
            <Field label="Completion notes" hint="What was done (required to complete)"><textarea className={`${inputClass} h-16 py-2`} value={done} onChange={(e) => setDone(e.target.value)} /></Field>
          )}
          <div className="flex flex-wrap gap-2">
            {NEXT[t.status].map((s) => (
              <Button key={s} size="sm" variant={s === 'COMPLETED' ? 'primary' : 'secondary'} loading={patch.isPending}
                onClick={() => go({ status: s, note: note || null, ...(s === 'COMPLETED' ? { completion_notes: done || null } : {}) })}>{s.replace('_', ' ').toLowerCase()}</Button>
            ))}
            <Button size="sm" disabled={!note.trim()} onClick={() => go({ note })}>Comment</Button>
            {!t.escalated_to_owner && t.status !== 'COMPLETED' && <Button size="sm" onClick={() => go({ escalated_to_owner: true, note: note || 'Escalated to the owner' })}>Escalate to owner</Button>}
          </div>
          <div>
            <h3 className="mb-1 text-xs font-semibold text-ink-2">History</h3>
            <ol className="space-y-1 border-l border-line pl-3 text-xs">
              {(t.events ?? []).map((e, i) => <li key={i}><span className="font-medium text-ink">{e.kind === 'STATUS' ? `${e.from?.toLowerCase()} → ${e.to?.toLowerCase()}` : e.kind.toLowerCase()}</span> · {fmt.dateTime(e.at)}{e.note ? ` · ${e.note}` : ''}</li>)}
            </ol>
          </div>
        </div>
      )}
    </Drawer>
  );
};
