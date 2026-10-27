import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { Plus, UserPlus, Users } from 'lucide-react';
import { api, useDailyBoard, useGroup, useGroups, useMeta, useMillMutation, usePeople } from '../../api/mill';
import { useParam } from '../../app/state';
import { QueryView } from '../../design/QueryView';
import { Drawer } from '../../design/Drawer';
import { Badge, Button, Card, CardBody, CardHeader, EmptyState, Notice, StatusPill, Tabs } from '../../design/ui';
import { Field, PageTitle, SeverityPill, fmt, inputClass } from '../common/parts';
import { TaskDrawer, type TaskDraft } from '../common/TaskDrawer';
import type { Group } from '../../types/mill';

const today = () => new Date().toISOString().slice(0, 10);

export const GroupsPage: React.FC = () => {
  const [tab, setTab] = useParam('tab', 'board');
  const [id, setId] = useParam('id');
  const groups = useGroups();
  const bootstrap = useMillMutation(() => api.post('/mill/groups/bootstrap?count=11', {}));
  const [people, setPeople] = useState(false);
  return (
    <>
      <PageTitle title="Groups and work allocation" subtitle="The GM's groups: their looms, people, tasks and issues. Loom and people assignments are dated, so history is never re-attributed."
        actions={<><Button icon={<UserPlus className="size-4" />} onClick={() => setPeople(true)}>People</Button><GroupCreate /></>} />
      <QueryView query={groups}>
        {(gs) => gs.length === 0 ? (
          <Card><EmptyState icon={<Users className="size-5" />} title="No groups yet" description="Start with the mill's 11 groups (named Group 1–11; rename them and set leaders afterwards)."
            action={<Button variant="primary" loading={bootstrap.isPending} onClick={() => bootstrap.mutate(undefined)}>Create 11 groups</Button>} /></Card>
        ) : (
          <>
            <div className="mb-3"><Tabs value={tab} onChange={setTab} tabs={[{ value: 'board', label: 'Daily board' }, { value: 'groups', label: `Groups (${gs.length})` }]} /></div>
            {tab === 'board' ? <Board onOpen={(g) => setId(String(g))} /> : (
              <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
                {gs.map((g) => (
                  <Card key={g.id} className="cursor-pointer transition-colors hover:border-accent" onClick={() => setId(String(g.id))}>
                    <CardHeader title={`${g.name}`} subtitle={`${g.code} · leader ${g.leader?.name ?? 'not set'} · shifts ${g.shift_coverage ?? '—'}`} />
                    <CardBody className="text-xs text-ink-2">
                      <p>{g.looms.length} looms{g.looms.length ? `: ${g.looms.slice(0, 10).map((l) => l.code).join(', ')}${g.looms.length > 10 ? '…' : ''}` : ''}</p>
                      <p className="mt-1">{g.members.length} people</p>
                    </CardBody>
                  </Card>
                ))}
              </div>
            )}
          </>
        )}
      </QueryView>
      {id && <GroupDrawer id={Number(id)} onClose={() => setId(null)} />}
      {people && <PeopleDrawer onClose={() => setPeople(false)} />}
    </>
  );
};

const Board: React.FC<{ onOpen: (id: number) => void }> = ({ onOpen }) => {
  const q = useDailyBoard();
  return (
    <QueryView query={q}>
      {(rows) => (
        <div className="grid gap-3 lg:grid-cols-2">
          {rows.map((r: any) => (
            <Card key={r.group.id ?? 'none'}>
              <CardHeader title={r.group.id ? <button className="hover:text-accent" onClick={() => onOpen(r.group.id)}>{r.group.name}</button> : r.group.name}
                subtitle={r.group.leader ? `Leader: ${r.group.leader}` : undefined}
                actions={<span className="flex gap-1">{r.overdue > 0 && <Badge tone="bad">{r.overdue} overdue</Badge>}{r.blocked > 0 && <Badge tone="warn">{r.blocked} blocked</Badge>}{r.escalated_to_owner > 0 && <Badge tone="info">{r.escalated_to_owner} to owner</Badge>}</span>} />
              <CardBody className="space-y-2 text-sm">
                {r.open.length === 0 && r.open_alerts.length === 0 && r.completed_last_24h.length === 0 && <p className="text-xs text-ink-3">Nothing open.</p>}
                {r.open.slice(0, 6).map((t: any) => (
                  <div key={t.id} className="flex items-center gap-2"><StatusPill status={t.status} /><Link to={`/tasks?id=${t.id}`} className="truncate hover:text-accent">{t.title}</Link>
                    {t.overdue && <Badge tone="bad">Overdue</Badge>}<span className="ml-auto text-2xs text-ink-3">{t.priority.toLowerCase()}</span></div>
                ))}
                {r.open_alerts.slice(0, 4).map((a: any) => (
                  <div key={a.id} className="flex items-center gap-2"><SeverityPill severity={a.severity} /><Link to={`/alerts?id=${a.id}`} className="truncate hover:text-accent">{a.title}</Link></div>
                ))}
                {r.completed_last_24h.length > 0 && <p className="text-xs text-ok">{r.completed_last_24h.length} completed in the last 24 h</p>}
              </CardBody>
            </Card>
          ))}
        </div>
      )}
    </QueryView>
  );
};

const GroupCreate: React.FC = () => {
  const [open, setOpen] = useState(false);
  const [f, setF] = useState({ code: '', name: '' });
  const save = useMillMutation((b: object) => api.post('/mill/groups', b));
  return (
    <>
      <Button variant="primary" icon={<Plus className="size-4" />} onClick={() => setOpen(true)}>Group</Button>
      <Drawer open={open} onClose={() => setOpen(false)} title="New group"
        footer={<div className="flex justify-end"><Button variant="primary" loading={save.isPending} disabled={!f.code || !f.name} onClick={() => save.mutate({ ...f, shift_coverage: 'A,B,C' }, { onSuccess: () => setOpen(false) })}>Create</Button></div>}>
        {save.isError && <Notice tone="bad">{(save.error as Error).message}</Notice>}
        <div className="space-y-3">
          <Field label="Code"><input className={inputClass} value={f.code} onChange={(e) => setF({ ...f, code: e.target.value })} placeholder="G12" /></Field>
          <Field label="Name"><input className={inputClass} value={f.name} onChange={(e) => setF({ ...f, name: e.target.value })} /></Field>
        </div>
      </Drawer>
    </>
  );
};

const GroupDrawer: React.FC<{ id: number; onClose: () => void }> = ({ id, onClose }) => {
  const q = useGroup(id);
  const meta = useMeta();
  const people = usePeople();
  const [task, setTask] = useState<TaskDraft | null>(null);
  const g = q.data;
  const [form, setForm] = useState<Partial<Group> | null>(null);
  const [assign, setAssign] = useState({ loom_ids: [] as number[], effective_from: today() });
  const [member, setMember] = useState({ person_id: '', shift: '', effective_from: today() });
  const save = useMillMutation((b: object) => api.put(`/mill/groups/${id}`, b));
  const addLooms = useMillMutation((b: object) => api.post(`/mill/groups/${id}/looms`, b));
  const addMember = useMillMutation((b: object) => api.post(`/mill/groups/${id}/members`, b));
  const release = useMillMutation((loomId: number) => api.post(`/mill/groups/${id}/looms/${loomId}/release?effective_from=${today()}`, {}));
  const endMember = useMillMutation((aid: number) => api.post(`/mill/groups/${id}/members/${aid}/end?effective_from=${today()}`, {}));
  const err = [save, addLooms, addMember, release, endMember].find((m) => m.isError)?.error as Error | undefined;
  const f = form ?? g;
  return (
    <Drawer open onClose={onClose} title={g?.name ?? 'Group'} subtitle={g ? `${g.code} · ${g.looms.length} looms · ${g.members.length} people` : undefined} width="max-w-2xl"
      footer={g && <div className="flex justify-between"><Button onClick={() => setTask({ group_id: g.id, title: '' })}>New task for this group</Button>
        <Button variant="primary" loading={save.isPending} disabled={!form} onClick={() => save.mutate({ code: f!.code, name: f!.name, leader_id: f!.leader_id ?? null, responsibilities: f!.responsibilities ?? null,
                                                                                                           shift_coverage: f!.shift_coverage ?? null, is_active: f!.is_active ?? true }, { onSuccess: () => setForm(null) })}>Save group</Button></div>}>
      {g && f && (
        <div className="space-y-5 text-sm">
          {err && <Notice tone="bad">{err.message}</Notice>}
          <div className="grid grid-cols-2 gap-3">
            <Field label="Name"><input className={inputClass} value={f.name ?? ''} onChange={(e) => setForm({ ...f, name: e.target.value })} /></Field>
            <Field label="Leader">
              <select className={inputClass} value={f.leader_id ?? ''} onChange={(e) => setForm({ ...f, leader_id: e.target.value ? Number(e.target.value) : null })}>
                <option value="">—</option>{(people.data ?? []).map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}
              </select>
            </Field>
            <Field label="Shift coverage"><input className={inputClass} value={f.shift_coverage ?? ''} onChange={(e) => setForm({ ...f, shift_coverage: e.target.value })} /></Field>
            <Field label="Responsibilities"><input className={inputClass} value={f.responsibilities ?? ''} onChange={(e) => setForm({ ...f, responsibilities: e.target.value })} /></Field>
          </div>
          <section>
            <h3 className="mb-2 text-xs font-semibold text-ink-2">Looms</h3>
            <div className="mb-2 flex flex-wrap gap-1">{g.looms.map((l) => (
              <span key={l.id} className="inline-flex items-center gap-1 rounded-md border border-line px-1.5 py-0.5 text-xs">{l.code}
                <button className="text-ink-3 hover:text-bad" title={`Release ${l.code} from today`} onClick={() => release.mutate(l.id)}>×</button></span>
            ))}{g.looms.length === 0 && <span className="text-xs text-ink-3">No looms assigned.</span>}</div>
            <div className="flex flex-wrap items-end gap-2">
              <Field label="Add looms (moves them from their current group)">
                <select multiple className={`${inputClass} h-28`} value={assign.loom_ids.map(String)} onChange={(e) => setAssign({ ...assign, loom_ids: [...e.target.selectedOptions].map((o) => Number(o.value)) })}>
                  {(meta.data?.looms ?? []).filter((l) => !g.looms.some((x) => x.id === l.id)).map((l) => <option key={l.id} value={l.id}>{l.code}</option>)}
                </select>
              </Field>
              <Field label="From"><input type="date" className={inputClass} value={assign.effective_from} onChange={(e) => setAssign({ ...assign, effective_from: e.target.value })} /></Field>
              <Button disabled={!assign.loom_ids.length} loading={addLooms.isPending} onClick={() => addLooms.mutate(assign, { onSuccess: () => setAssign({ ...assign, loom_ids: [] }) })}>Assign</Button>
            </div>
          </section>
          <section>
            <h3 className="mb-2 text-xs font-semibold text-ink-2">People</h3>
            <ul className="mb-2 space-y-1">{g.members.map((m) => (
              <li key={m.assignment_id} className="flex items-center gap-2 text-xs"><span className="text-ink">{m.name}</span><span className="text-ink-3">{m.role.toLowerCase()}{m.shift ? ` · shift ${m.shift}` : ''} · since {fmt.date(m.valid_from)}</span>
                <button className="ml-auto text-ink-3 hover:text-bad" onClick={() => endMember.mutate(m.assignment_id)}>End</button></li>
            ))}</ul>
            <div className="flex flex-wrap items-end gap-2">
              <Field label="Person"><select className={inputClass} value={member.person_id} onChange={(e) => setMember({ ...member, person_id: e.target.value })}>
                <option value="">Choose</option>{(people.data ?? []).filter((p) => p.is_active).map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}</select></Field>
              <Field label="Shift"><select className={inputClass} value={member.shift} onChange={(e) => setMember({ ...member, shift: e.target.value })}><option value="">Any</option>{['A', 'B', 'C'].map((s) => <option key={s}>{s}</option>)}</select></Field>
              <Field label="From"><input type="date" className={inputClass} value={member.effective_from} onChange={(e) => setMember({ ...member, effective_from: e.target.value })} /></Field>
              <Button disabled={!member.person_id} loading={addMember.isPending} onClick={() => addMember.mutate({ person_id: Number(member.person_id), shift: member.shift || null, effective_from: member.effective_from })}>Add</Button>
            </div>
          </section>
          <section>
            <h3 className="mb-2 text-xs font-semibold text-ink-2">Tasks ({g.tasks?.length ?? 0})</h3>
            <ul className="space-y-1">{(g.tasks ?? []).slice(0, 15).map((t) => <li key={t.id} className="flex gap-2 text-xs"><StatusPill status={t.status} /><Link to={`/tasks?id=${t.id}`} className="truncate hover:text-accent">{t.title}</Link></li>)}</ul>
          </section>
          {g.loom_history && g.loom_history.length > 0 && (
            <section><h3 className="mb-1 text-xs font-semibold text-ink-2">Loom assignment history</h3>
              <ul className="max-h-40 space-y-0.5 overflow-auto text-2xs text-ink-3">{g.loom_history.map((h, i) => <li key={i}>{h.loom}: {fmt.date(h.valid_from)} – {h.valid_to ? fmt.date(h.valid_to) : 'now'}</li>)}</ul></section>
          )}
        </div>
      )}
      <TaskDrawer open={!!task} onClose={() => setTask(null)} draft={task ?? undefined} onCreated={() => q.refetch()} />
    </Drawer>
  );
};

const PeopleDrawer: React.FC<{ onClose: () => void }> = ({ onClose }) => {
  const people = usePeople();
  const [f, setF] = useState({ name: '', role: 'OPERATOR', employee_code: '', phone: '' });
  const add = useMillMutation((b: object) => api.post('/mill/people', b));
  return (
    <Drawer open onClose={onClose} title="People" subtitle="Operators, group leaders, supervisors and maintenance staff">
      <div className="space-y-4">
        {add.isError && <Notice tone="bad">{(add.error as Error).message}</Notice>}
        <div className="grid grid-cols-2 gap-2">
          <Field label="Name"><input className={inputClass} value={f.name} onChange={(e) => setF({ ...f, name: e.target.value })} /></Field>
          <Field label="Role"><select className={inputClass} value={f.role} onChange={(e) => setF({ ...f, role: e.target.value })}>{['OPERATOR', 'GROUP_LEADER', 'SUPERVISOR', 'MAINTENANCE', 'FITTER', 'OTHER'].map((r) => <option key={r}>{r}</option>)}</select></Field>
          <Field label="Employee code"><input className={inputClass} value={f.employee_code} onChange={(e) => setF({ ...f, employee_code: e.target.value })} /></Field>
          <Field label="Phone"><input className={inputClass} value={f.phone} onChange={(e) => setF({ ...f, phone: e.target.value })} /></Field>
        </div>
        <Button variant="primary" disabled={!f.name.trim()} loading={add.isPending}
          onClick={() => add.mutate({ name: f.name.trim(), role: f.role, employee_code: f.employee_code || null, phone: f.phone || null }, { onSuccess: () => setF({ ...f, name: '', employee_code: '', phone: '' }) })}>Add person</Button>
        <ul className="divide-y divide-line text-sm">{(people.data ?? []).map((p) => (
          <li key={p.id} className="flex justify-between py-1.5"><span>{p.name}</span><span className="text-xs text-ink-3">{p.role.toLowerCase()}{p.employee_code ? ` · ${p.employee_code}` : ''}</span></li>
        ))}</ul>
      </div>
    </Drawer>
  );
};
