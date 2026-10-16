import React, { useState } from 'react';
import { Check, Plus } from 'lucide-react';
import { useActions, useApproveAction, useCreateAction, useUpdateAction } from '../../../api/weaving';
import { cn, inrFromLakhs } from '../../../lib/format';
import { PageHeader } from '../../../layout/PageHeader';
import { Button, Card, CardBody, CardHeader, Segmented, StatusPill } from '../../../design/ui';
import { DataTable } from '../../../design/DataTable';
import { Drawer } from '../../../design/Drawer';
import { Load, Pill, shortDate } from '../common';
import type { ActionItem } from '../../../types/pages';

const STATUS = { OPEN: 'Open', IN_PROGRESS: 'In progress', COMPLETED: 'Done', CANCELLED: 'Cancelled' } as const;
const ROLES: Record<string, string> = { OWNER: 'Owner / MD', WEAVING_MANAGER: 'Weaving Manager', SHIFT_SUPERVISOR: 'Shift Supervisor', MAINTENANCE: 'Maintenance', QUALITY: 'Quality' };

const NewAction: React.FC<{ onClose: () => void }> = ({ onClose }) => {
  const [issue, setIssue] = useState('');
  const [action, setAction] = useState('');
  const [role, setRole] = useState('');
  const [owner, setOwner] = useState('');
  const [due, setDue] = useState('');
  const create = useCreateAction();
  const field = 'mt-1 w-full rounded-lg border border-line bg-surface px-3 py-2 text-sm outline-none focus:border-accent';
  return (
    <div className="space-y-3">
      <label className="block text-xs font-medium text-ink-2">What is the problem<input value={issue} onChange={(e) => setIssue(e.target.value)} className={field} placeholder="e.g. SZ-05 gripper noise" /></label>
      <label className="block text-xs font-medium text-ink-2">What should be done<textarea value={action} onChange={(e) => setAction(e.target.value)} rows={3} className={field} /></label>
      <div className="grid grid-cols-2 gap-3">
        <label className="block text-xs font-medium text-ink-2">For which role<select value={role} onChange={(e) => setRole(e.target.value)} className={field}><option value="">Anyone</option>{Object.entries(ROLES).map(([v, l]) => <option key={v} value={v}>{l}</option>)}</select></label>
        <label className="block text-xs font-medium text-ink-2">Owner (name)<input value={owner} onChange={(e) => setOwner(e.target.value)} className={field} /></label>
      </div>
      <label className="block text-xs font-medium text-ink-2">Due<input type="date" value={due} onChange={(e) => setDue(e.target.value)} className={field} /></label>
      {create.isSuccess ? (
        <div className="rounded-lg bg-ok-soft px-3 py-2 text-sm text-ok">Saved as {create.data.ref}{create.data.requires_approval ? '. It counts once the weaving manager or owner approves it.' : '.'}</div>
      ) : (
        <div className="flex items-center gap-2">
          <Button variant="primary" loading={create.isPending} disabled={issue.trim().length < 3 || action.trim().length < 3}
            onClick={() => create.mutate({ issue: issue.trim(), action: action.trim(), owner_role: role || null, owner_name: owner || null, due_date: due || null })}>Save action</Button>
          <Button variant="ghost" onClick={onClose}>Close</Button>
          {create.isError && <span className="text-xs text-bad">Could not save.</span>}
        </div>
      )}
    </div>
  );
};

const Detail: React.FC<{ a: ActionItem }> = ({ a }) => {
  const update = useUpdateAction();
  const [note, setNote] = useState(a.outcome_note ?? '');
  const [cause, setCause] = useState(a.verified_cause ?? '');
  const field = 'mt-1 w-full rounded-lg border border-line bg-surface px-3 py-2 text-sm outline-none focus:border-accent';
  return (
    <div className="space-y-4 text-sm">
      <div><div className="text-xs text-ink-3">Problem</div><div className="font-medium text-ink">{a.issue}</div></div>
      <div><div className="text-xs text-ink-3">Action</div><div className="text-ink-2">{a.action}</div></div>
      <div className="grid grid-cols-2 gap-3 text-xs"><div><span className="text-ink-3">Owner</span><div className="text-sm text-ink">{a.owner ?? ROLES[a.owner_role ?? ''] ?? '—'}</div></div><div><span className="text-ink-3">Due</span><div className="text-sm text-ink">{shortDate(a.due)}</div></div></div>
      {a.finding_key && <div className="text-xs text-ink-3">Raised from the AI finding <code className="rounded bg-muted px-1">{a.finding_key}</code></div>}
      <div>
        <div className="mb-1 text-xs font-medium text-ink-2">Status</div>
        <Segmented value={a.status} onChange={(s) => update.mutate({ ref: a.ref, status: s })} ariaLabel="Status" options={(['OPEN', 'IN_PROGRESS', 'COMPLETED'] as const).map((s) => ({ value: s, label: STATUS[s] }))} />
      </div>
      <div>
        <label className="block text-xs font-medium text-ink-2">What happened (outcome)<textarea value={note} onChange={(e) => setNote(e.target.value)} rows={3} className={field} placeholder="Record the result so the mill learns whether this worked" /></label>
        {a.status === 'COMPLETED' && (
          <label className="mt-3 block text-xs font-medium text-ink-2">Verified cause, only if this outcome confirmed one<input value={cause} onChange={(e) => setCause(e.target.value)} className={field} placeholder="e.g. worn main nozzle; air pressure back to 6.0 bar" /></label>
        )}
        <div className="mt-2 flex items-center gap-2">
          <Button size="sm" variant="primary" loading={update.isPending} onClick={() => update.mutate({ ref: a.ref, outcome_note: note, ...(a.status === 'COMPLETED' && cause ? { verified_cause: cause } : {}) })}>Save outcome</Button>
          {update.isError && <span className="text-xs text-bad">{(update.error as Error).message}</span>}
          {update.isSuccess && <span className="text-xs text-ok">Saved</span>}
        </div>
        <p className="mt-2 text-xs text-ink-3">A cause is marked verified only here, by a person, on a completed action. The AI never marks one itself.</p>
      </div>
    </div>
  );
};

export const ActionsPage: React.FC = () => {
  const q = useActions();
  const approve = useApproveAction();
  const [filter, setFilter] = useState<'ALL' | 'OPEN' | 'IN_PROGRESS' | 'COMPLETED'>('ALL');
  const [sel, setSel] = useState<string | null>(null);
  const [creating, setCreating] = useState(false);
  return (
    <>
      <PageHeader title="Action Tracker" description="Who is fixing what, by when, and whether it worked." actions={<Button variant="primary" icon={<Plus className="size-4" />} onClick={() => setCreating(true)}>New action</Button>} />
      <Load q={q}>
        {(d) => {
          const rows = d.actions.filter((a) => filter === 'ALL' || a.status === filter);
          const cur = d.actions.find((a) => a.ref === sel) ?? null;
          return (
            <>
              <div className="grid grid-cols-2 gap-3 lg:grid-cols-5">
                {[['Open', d.summary.open, 'bg-warn'], ['In progress', d.summary.in_progress, 'bg-accent'], ['Done', d.summary.completed, 'bg-ok'], ['Overdue', d.summary.overdue, 'bg-bad'], ['Value still open', d.money_visible ? inrFromLakhs(d.summary.value_open_lakhs) : '—', 'bg-line-strong']].map(([l, v, c]) => (
                  <div key={String(l)} className="relative overflow-hidden rounded-2xl border border-line/80 bg-surface p-4 shadow-card"><span className={cn('absolute inset-x-0 top-0 h-[3px]', String(c))} /><div className="text-xs font-medium text-ink-3">{l}</div><div className="num mt-1 text-[26px] font-semibold leading-8">{v}</div></div>
                ))}
              </div>
              <Card>
                <CardHeader title="Actions" actions={<Segmented size="sm" value={filter} onChange={setFilter} ariaLabel="Filter" options={[{ value: 'ALL', label: 'All' }, { value: 'OPEN', label: 'Open' }, { value: 'IN_PROGRESS', label: 'In progress' }, { value: 'COMPLETED', label: 'Done' }]} />} />
                <DataTable
                  rows={rows}
                  rowKey={(r) => r.ref}
                  onRowClick={(r) => setSel(r.ref)}
                  searchable={(r) => `${r.issue} ${r.action} ${r.owner}`}
                  exportName="actions"
                  columns={[
                    { key: 's', header: 'Status', value: (r) => r.status, render: (r) => <StatusPill status={r.status} label={STATUS[r.status]} /> },
                    { key: 'i', header: 'Problem', value: (r) => r.issue, render: (r) => <div><div className="font-medium text-ink">{r.issue}</div><div className="max-w-md truncate text-xs text-ink-3">{r.action}</div></div> },
                    { key: 'o', header: 'Owner', value: (r) => r.owner ?? '', render: (r) => r.owner ?? ROLES[r.owner_role ?? ''] ?? '—', hideBelow: 'md' },
                    { key: 'd', header: 'Due', value: (r) => r.due ?? '', render: (r) => <span className={cn(r.overdue && 'font-semibold text-bad')}>{shortDate(r.due)}{r.overdue && ' · overdue'}</span>, align: 'right' },
                    { key: 'v', header: 'Worth', value: (r) => r.expected_impact_lakhs, render: (r) => inrFromLakhs(r.expected_impact_lakhs), align: 'right', hideBelow: 'lg' },
                    { key: 'a', header: 'Approval', value: (r) => (r.approved ? 1 : 0), render: (r) => r.requires_approval && !r.approved ? (
                      d.can_approve ? <Button size="sm" icon={<Check className="size-3.5" />} loading={approve.isPending && approve.variables === r.ref} onClick={(e) => { e.stopPropagation(); approve.mutate(r.ref); }}>Approve</Button> : <Pill tone="warn">awaiting</Pill>
                    ) : <span className="text-xs text-ink-3">{r.approved ? 'approved' : '—'}</span>, hideBelow: 'md' },
                    { key: 'c', header: 'Cause verified', value: (r) => r.verified_cause ?? '', render: (r) => (r.verified_cause ? <Pill tone="ok">yes</Pill> : <span className="text-ink-3">—</span>), hideBelow: 'lg' },
                  ]}
                />
              </Card>
              <Drawer open={!!cur} onClose={() => setSel(null)} title={cur?.ref ?? ''} subtitle={cur ? STATUS[cur.status] : ''}>{cur && <Detail a={cur} key={cur.ref + cur.status} />}</Drawer>
              <Drawer open={creating} onClose={() => setCreating(false)} title="New action" subtitle="Record what needs doing and who owns it"><NewAction onClose={() => setCreating(false)} /></Drawer>
            </>
          );
        }}
      </Load>
    </>
  );
};
