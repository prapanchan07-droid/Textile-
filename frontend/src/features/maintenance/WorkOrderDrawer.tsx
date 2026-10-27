import React, { useEffect, useState } from 'react';
import { Drawer } from '../../design/Drawer';
import { Button, Notice } from '../../design/ui';
import { api, useMeta, useMillMutation, usePeople } from '../../api/mill';
import { Field, inputClass } from '../common/parts';

export const WorkOrderDrawer: React.FC<{ open: boolean; onClose: () => void; loomId?: number; alertId?: number; title?: string }> = ({ open, onClose, loomId, alertId, title }) => {
  const meta = useMeta();
  const people = usePeople();
  const [f, setF] = useState({ loom_id: '', kind: 'BREAKDOWN', title: '', description: '', priority: 'MEDIUM', assignee_id: '', due_date: '' });
  useEffect(() => {
    if (open) setF({ loom_id: loomId ? String(loomId) : '', kind: 'BREAKDOWN', title: title ?? '', description: '', priority: 'MEDIUM', assignee_id: '', due_date: '' });
  }, [open, loomId, title]);
  const save = useMillMutation((body: object) => api.post('/mill/work-orders', body));
  const set = (k: keyof typeof f) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => setF((x) => ({ ...x, [k]: e.target.value }));
  return (
    <Drawer open={open} onClose={onClose} title="New work order" subtitle={alertId ? `From alert #${alertId}` : 'Maintenance work on one loom'}
      footer={<div className="flex justify-end gap-2"><Button onClick={onClose}>Cancel</Button>
        <Button variant="primary" loading={save.isPending} disabled={!f.title.trim() || !f.loom_id}
          onClick={() => save.mutate({ loom_id: Number(f.loom_id), kind: f.kind, title: f.title.trim(), description: f.description || null, priority: f.priority,
                                       assignee_id: f.assignee_id ? Number(f.assignee_id) : null, alert_id: alertId ?? null, due_date: f.due_date || null },
                                     { onSuccess: onClose })}>Create</Button></div>}>
      <div className="space-y-3">
        {save.isError && <Notice tone="bad">{(save.error as Error).message}</Notice>}
        <Field label="Loom">
          <select className={inputClass} value={f.loom_id} onChange={set('loom_id')} disabled={!!loomId}>
            <option value="">Choose a loom</option>
            {(meta.data?.looms ?? []).map((l) => <option key={l.id} value={l.id}>{l.code}</option>)}
          </select>
        </Field>
        <div className="grid grid-cols-2 gap-3">
          <Field label="Type">
            <select className={inputClass} value={f.kind} onChange={set('kind')}>
              {['BREAKDOWN', 'PREVENTIVE', 'INSPECTION', 'ADJUSTMENT'].map((k) => <option key={k}>{k}</option>)}
            </select>
          </Field>
          <Field label="Priority">
            <select className={inputClass} value={f.priority} onChange={set('priority')}>{['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'].map((k) => <option key={k}>{k}</option>)}</select>
          </Field>
        </div>
        <Field label="Title"><input className={inputClass} value={f.title} onChange={set('title')} /></Field>
        <Field label="Details"><textarea className={`${inputClass} h-20 py-2`} value={f.description} onChange={set('description')} /></Field>
        <div className="grid grid-cols-2 gap-3">
          <Field label="Technician">
            <select className={inputClass} value={f.assignee_id} onChange={set('assignee_id')}>
              <option value="">—</option>
              {(people.data ?? []).filter((p) => p.is_active).map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}
            </select>
          </Field>
          <Field label="Planned date" hint="For preventive work; overdue PM raises an alert"><input type="date" className={inputClass} value={f.due_date} onChange={set('due_date')} /></Field>
        </div>
      </div>
    </Drawer>
  );
};
