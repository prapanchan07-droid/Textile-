import React, { useEffect, useState } from 'react';
import { Drawer } from '../../design/Drawer';
import { Button, Notice } from '../../design/ui';
import { api, useGroups, useMillMutation, usePeople } from '../../api/mill';
import type { Task } from '../../types/mill';
import { Field, inputClass } from './parts';

export interface TaskDraft {
  title?: string;
  description?: string;
  loom_id?: number | null;
  alert_id?: number | null;
  group_id?: number | null;
  priority?: string;
}

/** Create a task, optionally linked to a loom, an alert or a finding's context. */
export const TaskDrawer: React.FC<{ open: boolean; onClose: () => void; draft?: TaskDraft; onCreated?: (t: Task) => void }> = ({ open, onClose, draft, onCreated }) => {
  const groups = useGroups();
  const people = usePeople();
  const [form, setForm] = useState({ title: '', description: '', expected_outcome: '', group_id: '', assignee_id: '', priority: 'MEDIUM', due_at: '' });
  useEffect(() => {
    if (open)
      setForm({ title: draft?.title ?? '', description: draft?.description ?? '', expected_outcome: '', group_id: draft?.group_id ? String(draft.group_id) : '',
                assignee_id: '', priority: draft?.priority ?? 'MEDIUM', due_at: '' });
  }, [open, draft]);
  const save = useMillMutation((body: object) => api.post<Task>('/mill/tasks', body));
  const set = (k: keyof typeof form) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => setForm((f) => ({ ...f, [k]: e.target.value }));
  const submit = () =>
    save.mutate(
      {
        title: form.title.trim(), description: form.description || null, expected_outcome: form.expected_outcome || null,
        group_id: form.group_id ? Number(form.group_id) : null, assignee_id: form.assignee_id ? Number(form.assignee_id) : null,
        loom_id: draft?.loom_id ?? null, alert_id: draft?.alert_id ?? null, priority: form.priority,
        due_at: form.due_at ? new Date(form.due_at).toISOString() : null,
      },
      { onSuccess: (t) => { onCreated?.(t); onClose(); } },
    );
  return (
    <Drawer
      open={open}
      onClose={onClose}
      title="New task"
      subtitle={draft?.alert_id ? `Linked to alert #${draft.alert_id}` : draft?.loom_id ? 'Linked to this loom' : 'Assign work to a group or person'}
      footer={
        <div className="flex justify-end gap-2">
          <Button onClick={onClose}>Cancel</Button>
          <Button variant="primary" loading={save.isPending} disabled={!form.title.trim()} onClick={submit}>Create task</Button>
        </div>
      }
    >
      <div className="space-y-3">
        {save.isError && <Notice tone="bad">{(save.error as Error).message}</Notice>}
        <Field label="Title"><input className={inputClass} value={form.title} onChange={set('title')} autoFocus /></Field>
        <Field label="What needs doing"><textarea className={`${inputClass} h-24 py-2`} value={form.description} onChange={set('description')} /></Field>
        <Field label="Expected outcome"><input className={inputClass} value={form.expected_outcome} onChange={set('expected_outcome')} placeholder="e.g. warp stops back under 4 per 100k picks" /></Field>
        <div className="grid grid-cols-2 gap-3">
          <Field label="Group">
            <select className={inputClass} value={form.group_id} onChange={set('group_id')}>
              <option value="">—</option>
              {(groups.data ?? []).map((g) => <option key={g.id} value={g.id}>{g.name}</option>)}
            </select>
          </Field>
          <Field label="Person">
            <select className={inputClass} value={form.assignee_id} onChange={set('assignee_id')}>
              <option value="">—</option>
              {(people.data ?? []).filter((p) => p.is_active).map((p) => <option key={p.id} value={p.id}>{p.name} ({p.role.toLowerCase()})</option>)}
            </select>
          </Field>
          <Field label="Priority">
            <select className={inputClass} value={form.priority} onChange={set('priority')}>
              {['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'].map((p) => <option key={p}>{p}</option>)}
            </select>
          </Field>
          <Field label="Due"><input type="datetime-local" className={inputClass} value={form.due_at} onChange={set('due_at')} /></Field>
        </div>
      </div>
    </Drawer>
  );
};
