import React, { useState } from 'react';
import { CheckCircle2, Send } from 'lucide-react';
import { useCreateNote, useResolveNote } from '../../../api/weaving';
import { cn } from '../../../lib/format';
import { Button } from '../../../design/ui';
import type { Note } from '../../../types/pages';

const SEV = { INFO: 'bg-accent-soft text-accent-ink', WARNING: 'bg-warn-soft text-warn', URGENT: 'bg-bad-soft text-bad' } as const;
const CAT: Record<string, string> = { HANDOVER: 'Hand-over', ISSUE: 'Issue', MAINTENANCE_REQUEST: 'Maintenance request', QUALITY: 'Quality' };

export const NoteComposer: React.FC<{ looms: string[] }> = ({ looms }) => {
  const [body, setBody] = useState('');
  const [loom, setLoom] = useState('');
  const [category, setCategory] = useState('HANDOVER');
  const [severity, setSeverity] = useState('INFO');
  const create = useCreateNote();
  const field = 'h-8 rounded-lg border border-line bg-surface px-2 text-sm outline-none focus:border-accent';
  return (
    <div className="space-y-2 rounded-xl border border-line/80 bg-subtle p-3">
      <textarea value={body} onChange={(e) => setBody(e.target.value)} rows={2} placeholder="Write what the next shift, or maintenance, needs to know…" className="w-full rounded-lg border border-line bg-surface p-2 text-sm outline-none focus:border-accent" />
      <div className="flex flex-wrap items-center gap-2">
        <select value={category} onChange={(e) => setCategory(e.target.value)} className={field} aria-label="Type">{Object.entries(CAT).map(([v, l]) => <option key={v} value={v}>{l}</option>)}</select>
        <select value={severity} onChange={(e) => setSeverity(e.target.value)} className={field} aria-label="Severity"><option value="INFO">Info</option><option value="WARNING">Warning</option><option value="URGENT">Urgent</option></select>
        <select value={loom} onChange={(e) => setLoom(e.target.value)} className={field} aria-label="Loom"><option value="">No particular loom</option>{looms.map((l) => <option key={l} value={l}>{l}</option>)}</select>
        <Button size="sm" variant="primary" icon={<Send className="size-3.5" />} loading={create.isPending} disabled={body.trim().length < 3}
          onClick={() => create.mutate({ body: body.trim(), loom: loom || null, category, severity }, { onSuccess: () => setBody('') })}>Add note</Button>
        {create.isError && <span className="text-xs text-bad">Could not save the note.</span>}
      </div>
    </div>
  );
};

export const NoteList: React.FC<{ notes: Note[]; empty?: string }> = ({ notes, empty = 'No notes.' }) => {
  const resolve = useResolveNote();
  if (!notes.length) return <p className="py-3 text-sm text-ink-3">{empty}</p>;
  return (
    <ul className="space-y-2">
      {notes.map((n) => (
        <li key={n.id} className={cn('rounded-xl border p-3 text-sm', n.resolved ? 'border-line/60 opacity-70' : n.severity === 'URGENT' ? 'border-bad/40' : 'border-line/80')}>
          <div className="mb-1 flex flex-wrap items-center gap-2 text-xs">
            <span className={cn('rounded-md px-1.5 py-0.5 font-semibold', SEV[n.severity])}>{n.severity === 'INFO' ? 'Info' : n.severity === 'WARNING' ? 'Warning' : 'Urgent'}</span>
            <span className="font-medium text-ink-2">{CAT[n.category]}</span>
            {n.loom && <span className="rounded-md bg-muted px-1.5 py-0.5 font-medium text-ink-2">{n.loom}</span>}
            <span className="text-ink-3">{n.shift} · {new Date(n.date).toLocaleDateString('en-GB', { day: '2-digit', month: 'short' })} · {n.author}</span>
            {!n.resolved && !n.this_shift && <span className="rounded-md bg-warn-soft px-1.5 py-0.5 font-semibold text-warn">carried over</span>}
          </div>
          <p className="leading-5 text-ink">{n.body}</p>
          {!n.resolved ? (
            <button onClick={() => resolve.mutate(n.id)} className="mt-1.5 inline-flex items-center gap-1 text-xs font-medium text-accent hover:underline"><CheckCircle2 className="size-3.5" /> Mark resolved</button>
          ) : <div className="mt-1 text-xs text-ok">Resolved</div>}
        </li>
      ))}
    </ul>
  );
};
