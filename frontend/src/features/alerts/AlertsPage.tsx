import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { CheckCheck, ClipboardPlus, PlayCircle, Wrench } from 'lucide-react';
import { api, useAlert, useAlerts, useChannels, useGroups, useMillMutation, usePeople, useRules } from '../../api/mill';
import { useParam } from '../../app/state';
import { QueryView } from '../../design/QueryView';
import { DataTable, type Column } from '../../design/DataTable';
import { Drawer } from '../../design/Drawer';
import { Badge, Button, Card, CardBody, CardHeader, Notice, StatusPill, Tabs } from '../../design/ui';
import { Field, PageTitle, SeverityPill, SourceBadge, fmt, inputClass } from '../common/parts';
import { TaskDrawer, type TaskDraft } from '../common/TaskDrawer';
import { WorkOrderDrawer } from '../maintenance/WorkOrderDrawer';
import type { Alert, AlertRule } from '../../types/mill';

const cols: Column<Alert>[] = [
  { key: 'sev', header: 'Severity', render: (a) => <SeverityPill severity={a.severity} />, value: (a) => ({ CRITICAL: 0, WARNING: 1, INFO: 2 })[a.severity] },
  { key: 'title', header: 'Alert', render: (a) => <span className="text-ink">{a.title}</span>, value: (a) => a.title, wrap: true },
  { key: 'period', header: 'Shift / period', render: (a) => a.period ?? '—', value: (a) => a.period },
  { key: 'obs', header: 'Observed', align: 'right', render: (a) => fmt.n(a.observed, 2), value: (a) => a.observed, hideBelow: 'md' },
  { key: 'thr', header: 'Limit', align: 'right', render: (a) => fmt.n(a.threshold, 2), value: (a) => a.threshold, hideBelow: 'md' },
  { key: 'n', header: 'Times', align: 'right', render: (a) => a.occurrences, value: (a) => a.occurrences, hideBelow: 'lg' },
  { key: 'status', header: 'Status', render: (a) => <span className="inline-flex flex-wrap gap-1"><StatusPill status={a.status} />{a.condition_cleared_at && a.status !== 'RESOLVED' && <Badge tone="ok">Condition cleared</Badge>}{a.escalation_level > 0 && <Badge tone="bad">Escalated ×{a.escalation_level}</Badge>}</span>, value: (a) => a.status },
  { key: 'src', header: 'Source', render: (a) => <SourceBadge source={a.source} />, value: (a) => a.source, hideBelow: 'xl' },
  { key: 'seen', header: 'Last seen', render: (a) => fmt.dateTime(a.last_seen_at), value: (a) => a.last_seen_at, hideBelow: 'lg' },
];

export const AlertsPage: React.FC = () => {
  const [tab, setTab] = useParam('tab', 'ACTIVE');
  const [selected, setSelected] = useParam('id');
  const q = useAlerts({ status: tab === 'RULES' ? 'ACTIVE' : tab, page_size: 200 });
  const evaluate = useMillMutation(() => api.post<Record<string, number>>('/mill/alerts/evaluate', {}));
  return (
    <>
      <PageTitle title="Alerts and incidents" subtitle="Rule breaches with their evidence, owner and history. One alert per rule and loom; repeats update it instead of flooding."
        actions={<Button icon={<PlayCircle className="size-4" />} loading={evaluate.isPending} onClick={() => evaluate.mutate(undefined)}>Evaluate rules now</Button>} />
      {evaluate.data && <Notice tone="info">Evaluated {evaluate.data.evaluated} loom-rule checks: {evaluate.data.opened} opened, {evaluate.data.refreshed} refreshed, {evaluate.data.cleared} cleared, {evaluate.data.escalated} escalated.</Notice>}
      <div className="my-3">
        <Tabs value={tab} onChange={setTab} tabs={[{ value: 'ACTIVE', label: 'Active' }, { value: 'OPEN', label: 'Unacknowledged' }, { value: 'RESOLVED', label: 'Resolved' }, { value: 'RULES', label: 'Rules & channels' }]} />
      </div>
      {tab === 'RULES' ? <Rules /> : (
        <QueryView query={q}>
          {(d) => <Card><CardBody className="pt-4"><DataTable rows={d.items} columns={cols} rowKey={(a) => String(a.id)} onRowClick={(a) => setSelected(String(a.id))}
            selectedKey={selected} searchable={(a) => `${a.title} ${a.rule_code}`} exportName="alerts" emptyTitle="No alerts here" /></CardBody></Card>}
        </QueryView>
      )}
      {selected && <AlertDrawer id={Number(selected)} onClose={() => setSelected(null)} />}
    </>
  );
};

const AlertDrawer: React.FC<{ id: number; onClose: () => void }> = ({ id, onClose }) => {
  const q = useAlert(id);
  const groups = useGroups();
  const people = usePeople();
  const [note, setNote] = useState('');
  const [task, setTask] = useState<TaskDraft | null>(null);
  const [wo, setWo] = useState(false);
  const act = useMillMutation(({ action, body }: { action: string; body: object }) => api.post<Alert>(`/mill/alerts/${id}/${action}`, body));
  const a = q.data;
  const run = (action: string, body: object = {}) => act.mutate({ action, body }, { onSuccess: () => { setNote(''); q.refetch(); } });
  return (
    <Drawer open onClose={onClose} title={a?.title ?? 'Alert'} subtitle={a ? `${a.rule_code} · ${a.period ?? ''} · first seen ${fmt.dateTime(a.first_seen_at)}` : undefined} width="max-w-2xl"
      footer={a && a.status !== 'RESOLVED' ? (
        <div className="flex flex-wrap justify-end gap-2">
          <Button icon={<ClipboardPlus className="size-4" />} onClick={() => setTask({ title: a.title, alert_id: a.id, loom_id: a.loom?.id, group_id: a.assigned_group_id ?? a.group_id, priority: a.severity === 'CRITICAL' ? 'HIGH' : 'MEDIUM' })}>Create task</Button>
          <Button icon={<Wrench className="size-4" />} disabled={!a.loom} onClick={() => setWo(true)}>Work order</Button>
          {a.status === 'OPEN' && <Button loading={act.isPending} onClick={() => run('acknowledge', { note: note || null })}>Acknowledge</Button>}
          <Button variant="primary" icon={<CheckCheck className="size-4" />} loading={act.isPending} disabled={!note.trim()} onClick={() => run('resolve', { note })}>Resolve</Button>
        </div>
      ) : a ? <div className="flex justify-end"><Button onClick={() => run('reopen')}>Reopen</Button></div> : null}>
      {a && (
        <div className="space-y-4 text-sm">
          {act.isError && <Notice tone="bad">{(act.error as Error).message}</Notice>}
          <div className="flex flex-wrap gap-2"><SeverityPill severity={a.severity} /><StatusPill status={a.status} /><SourceBadge source={a.source} />{a.data_origin === 'SIMULATED' && <Badge tone="warn">Simulated data</Badge>}
            {a.loom && <Link to={`/looms/${a.loom.id}`} className="text-xs text-accent hover:underline">Open {a.loom.code}</Link>}</div>
          <dl className="grid grid-cols-3 gap-2 rounded-xl bg-subtle p-3 text-xs">
            <div><dt className="text-ink-3">Observed</dt><dd className="num text-base text-ink">{fmt.n(a.observed, 2)}</dd></div>
            <div><dt className="text-ink-3">Limit</dt><dd className="num text-base text-ink">{fmt.n(a.threshold, 2)}</dd></div>
            <div><dt className="text-ink-3">Baseline</dt><dd className="num text-base text-ink">{fmt.n(a.baseline, 2)}</dd></div>
          </dl>
          {a.evidence && (
            <div>
              <h3 className="mb-1 text-xs font-semibold text-ink-2">Evidence</h3>
              {Array.isArray((a.evidence as { records?: unknown[] }).records) && (
                <ul className="mb-2 space-y-0.5 text-xs">
                  {((a.evidence as { records: { period: string; value: number; source: string; efficiency_pct: number | null; meters: number | null }[] }).records).map((r) => (
                    <li key={r.period} className="num">{r.period}: value {fmt.n(r.value, 2)} · efficiency {fmt.n(r.efficiency_pct, 1)}% · {fmt.n(r.meters, 1)} m · {r.source}</li>
                  ))}
                </ul>
              )}
              <pre className="max-h-40 overflow-auto rounded-lg bg-subtle p-2 text-2xs text-ink-2">{JSON.stringify({ ...a.evidence, records: undefined }, null, 2)}</pre>
            </div>
          )}
          <div className="grid grid-cols-2 gap-3">
            <Field label="Responsible group">
              <select className={inputClass} value={a.assigned_group_id ?? ''} onChange={(e) => run('assign', { group_id: e.target.value ? Number(e.target.value) : null, person_id: a.assigned_person_id })}>
                <option value="">—</option>{(groups.data ?? []).map((g) => <option key={g.id} value={g.id}>{g.name}</option>)}
              </select>
            </Field>
            <Field label="Responsible person">
              <select className={inputClass} value={a.assigned_person_id ?? ''} onChange={(e) => run('assign', { group_id: a.assigned_group_id, person_id: e.target.value ? Number(e.target.value) : null })}>
                <option value="">—</option>{(people.data ?? []).map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}
              </select>
            </Field>
          </div>
          {a.status !== 'RESOLVED' && (
            <Field label="Note" hint="Required to resolve: what was found or done">
              <textarea className={`${inputClass} h-20 py-2`} value={note} onChange={(e) => setNote(e.target.value)} />
            </Field>
          )}
          {a.status !== 'RESOLVED' && <Button size="sm" disabled={!note.trim()} onClick={() => run('comment', { note })}>Add comment</Button>}
          {a.resolution_notes && <Notice tone="ok">Resolved: {a.resolution_notes}</Notice>}
          {a.tasks && a.tasks.length > 0 && (
            <div><h3 className="mb-1 text-xs font-semibold text-ink-2">Linked tasks</h3>
              <ul className="space-y-1">{a.tasks.map((t) => <li key={t.id} className="flex gap-2"><Link to={`/tasks?id=${t.id}`} className="hover:text-accent">{t.title}</Link><StatusPill status={t.status} /></li>)}</ul></div>
          )}
          <div>
            <h3 className="mb-1 text-xs font-semibold text-ink-2">History</h3>
            <ol className="space-y-1 border-l border-line pl-3 text-xs">
              {(a.events ?? []).map((e, i) => <li key={i}><span className="font-medium text-ink">{e.kind.toLowerCase()}</span> · {fmt.dateTime(e.at)}{e.note ? ` · ${e.note}` : ''}</li>)}
            </ol>
          </div>
        </div>
      )}
      <TaskDrawer open={!!task} onClose={() => setTask(null)} draft={task ?? undefined} onCreated={() => q.refetch()} />
      {a?.loom && <WorkOrderDrawer open={wo} onClose={() => setWo(false)} loomId={a.loom.id} alertId={a.id} title={a.title} />}
    </Drawer>
  );
};

const Rules: React.FC = () => {
  const q = useRules();
  const channels = useChannels();
  const [edit, setEdit] = useState<AlertRule | null>(null);
  return (
    <div className="space-y-4">
      <QueryView query={q}>
        {(rules) => (
          <Card>
            <CardHeader title="Alert rules" subtitle="Limits apply per loom-shift record. Only metrics a source provides are evaluated (e.g. no stop rules for SZ)." />
            <CardBody>
              <DataTable dense rows={rules} rowKey={(r) => String(r.id)} onRowClick={setEdit}
                columns={[
                  { key: 'on', header: 'On', render: (r) => (r.enabled ? <StatusPill tone="ok" label="On" /> : <StatusPill tone="neutral" label="Off" />), value: (r) => Number(r.enabled) },
                  { key: 'name', header: 'Rule', render: (r) => <span><span className="text-ink">{r.name}</span><span className="block text-2xs text-ink-3">{r.description}</span></span>, value: (r) => r.name, wrap: true },
                  { key: 'cond', header: 'Condition', render: (r) => `${r.metric} ${r.comparator === 'lt' ? '<' : '>'} ${r.threshold ?? '—'}`, value: (r) => r.metric },
                  { key: 'n', header: 'In a row', align: 'right', render: (r) => r.consecutive, value: (r) => r.consecutive },
                  { key: 'sev', header: 'Severity', render: (r) => <SeverityPill severity={r.severity} />, value: (r) => r.severity },
                  { key: 'esc', header: 'Escalate after', align: 'right', render: (r) => (r.escalate_after_hours ? `${r.escalate_after_hours} h` : '—'), value: (r) => r.escalate_after_hours },
                  { key: 'cool', header: 'Cooldown', align: 'right', render: (r) => `${r.cooldown_hours} h`, value: (r) => r.cooldown_hours },
                ]} />
            </CardBody>
          </Card>
        )}
      </QueryView>
      <Card>
        <CardHeader title="Notification channels" subtitle="Only configured and tested channels deliver. In-app notifications appear under the bell." />
        <CardBody>
          <ul className="space-y-1 text-sm">{(channels.data ?? []).map((c) => (
            <li key={c.channel} className="flex items-center gap-2">{c.configured ? <StatusPill tone="ok" label="Configured" /> : <StatusPill tone="neutral" label="Not configured" />}<span className="text-ink">{c.channel}</span><span className="text-xs text-ink-3">{c.note}</span></li>
          ))}</ul>
        </CardBody>
      </Card>
      {edit && <RuleDrawer rule={edit} onClose={() => setEdit(null)} />}
    </div>
  );
};

const RuleDrawer: React.FC<{ rule: AlertRule; onClose: () => void }> = ({ rule, onClose }) => {
  const [f, setF] = useState({ threshold: rule.threshold?.toString() ?? '', consecutive: String(rule.consecutive), cooldown_hours: String(rule.cooldown_hours),
                               escalate_after_hours: rule.escalate_after_hours?.toString() ?? '', severity: rule.severity, enabled: rule.enabled, categories: rule.categories ?? '' });
  const save = useMillMutation((body: object) => api.patch(`/mill/alert-rules/${rule.id}`, body));
  const set = (k: keyof typeof f) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => setF((x) => ({ ...x, [k]: e.target.value }));
  return (
    <Drawer open onClose={onClose} title={rule.name} subtitle={rule.description ?? undefined}
      footer={<div className="flex justify-end gap-2"><Button onClick={onClose}>Cancel</Button><Button variant="primary" loading={save.isPending}
        onClick={() => save.mutate({ threshold: f.threshold === '' ? null : Number(f.threshold), consecutive: Number(f.consecutive), cooldown_hours: Number(f.cooldown_hours),
                                     escalate_after_hours: f.escalate_after_hours === '' ? null : Number(f.escalate_after_hours), severity: f.severity, enabled: f.enabled,
                                     categories: f.categories || null }, { onSuccess: onClose })}>Save</Button></div>}>
      <div className="space-y-3">
        {save.isError && <Notice tone="bad">{(save.error as Error).message}</Notice>}
        <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={f.enabled} onChange={(e) => setF((x) => ({ ...x, enabled: e.target.checked }))} /> Enabled</label>
        <Field label={`Limit (${rule.metric} ${rule.comparator === 'lt' ? 'below' : 'above'})`}><input type="number" step="any" className={inputClass} value={f.threshold} onChange={set('threshold')} /></Field>
        <div className="grid grid-cols-3 gap-3">
          <Field label="Breaches in a row"><input type="number" min={1} className={inputClass} value={f.consecutive} onChange={set('consecutive')} /></Field>
          <Field label="Cooldown (h)"><input type="number" min={0} className={inputClass} value={f.cooldown_hours} onChange={set('cooldown_hours')} /></Field>
          <Field label="Escalate after (h)"><input type="number" min={1} className={inputClass} value={f.escalate_after_hours} onChange={set('escalate_after_hours')} /></Field>
        </div>
        <Field label="Severity"><select className={inputClass} value={f.severity} onChange={set('severity')}>{['INFO', 'WARNING', 'CRITICAL'].map((s) => <option key={s}>{s}</option>)}</select></Field>
        <Field label="Categories" hint="Comma list (TY,TS,SZ); empty = all"><input className={inputClass} value={f.categories} onChange={set('categories')} /></Field>
      </div>
    </Drawer>
  );
};
