import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { FilePlus2 } from 'lucide-react';
import { api, useMeta, useMillMutation, useReports } from '../../api/mill';
import { QueryView } from '../../design/QueryView';
import { DataTable } from '../../design/DataTable';
import { Drawer } from '../../design/Drawer';
import { Button, Card, CardBody, Notice, StatusPill } from '../../design/ui';
import { Field, PageTitle, fmt, inputClass } from '../common/parts';
import type { OwnerReport } from '../../types/mill';

export const ReportsPage: React.FC = () => {
  const q = useReports();
  const [open, setOpen] = useState(false);
  return (
    <>
      <PageTitle title="GM-to-owner reports" subtitle="A decision-oriented update for the owner. Numbers are frozen when the GM publishes; later imports never change a published report."
        actions={<Button variant="primary" icon={<FilePlus2 className="size-4" />} onClick={() => setOpen(true)}>New report</Button>} />
      <QueryView query={q}>
        {(d) => (
          <Card><CardBody className="pt-4">
            <DataTable rows={d.items} rowKey={(r) => String(r.id)} exportName="reports" emptyTitle="No reports yet" emptyDescription="Create the first daily report from the imported data."
              columns={[
                { key: 't', header: 'Report', render: (r: OwnerReport) => <Link to={`/reports/${r.id}`} className="font-medium text-ink hover:text-accent">{r.title}</Link>, value: (r) => r.title },
                { key: 'p', header: 'Period', render: (r) => `${fmt.date(r.period_start)}${r.period_end !== r.period_start ? ` – ${fmt.date(r.period_end)}` : ''}${r.shift ? ` · ${r.shift}` : ''}`, value: (r) => r.period_end },
                { key: 's', header: 'Status', render: (r) => <StatusPill status={r.status === 'DRAFT' ? 'IN_PROGRESS' : 'COMPLETED'} label={r.status.toLowerCase()} />, value: (r) => r.status },
                { key: 'g', header: 'Generated', render: (r) => fmt.dateTime(r.generated_at), value: (r) => r.generated_at, hideBelow: 'md' },
                { key: 'pub', header: 'Published', render: (r) => fmt.dateTime(r.published_at), value: (r) => r.published_at, hideBelow: 'md' },
                { key: 'ack', header: 'Owner', render: (r) => (r.acknowledged_at ? `acknowledged ${fmt.dateTime(r.acknowledged_at)}` : '—'), value: (r) => r.acknowledged_at, hideBelow: 'lg' },
              ]} />
          </CardBody></Card>
        )}
      </QueryView>
      <NewReport open={open} onClose={() => setOpen(false)} />
    </>
  );
};

const NewReport: React.FC<{ open: boolean; onClose: () => void }> = ({ open, onClose }) => {
  const meta = useMeta();
  const last = meta.data?.data_range.last ?? '';
  const [f, setF] = useState({ period_start: '', period_end: '', shift: '' });
  const navigate = useNavigate();
  const save = useMillMutation((b: object) => api.post<OwnerReport>('/mill/reports', b));
  const start = f.period_start || last;
  const end = f.period_end || last;
  return (
    <Drawer open={open} onClose={onClose} title="New owner report" subtitle={last ? `Latest data: ${fmt.date(last)}` : 'No data imported yet'}
      footer={<div className="flex justify-end gap-2"><Button onClick={onClose}>Cancel</Button>
        <Button variant="primary" loading={save.isPending} disabled={!start || !end}
          onClick={() => save.mutate({ period_start: start, period_end: end, shift: f.shift || null }, { onSuccess: (r) => navigate(`/reports/${r.id}`) })}>Create draft</Button></div>}>
      <div className="space-y-3">
        {save.isError && <Notice tone="bad">{(save.error as Error).message}</Notice>}
        <div className="grid grid-cols-2 gap-3">
          <Field label="From"><input type="date" className={inputClass} value={start} onChange={(e) => setF({ ...f, period_start: e.target.value })} /></Field>
          <Field label="To"><input type="date" className={inputClass} value={end} onChange={(e) => setF({ ...f, period_end: e.target.value })} /></Field>
        </div>
        <Field label="Shift" hint="Leave empty for the whole day(s)">
          <select className={inputClass} value={f.shift} onChange={(e) => setF({ ...f, shift: e.target.value })}><option value="">All shifts</option>{['A', 'B', 'C'].map((s) => <option key={s}>{s}</option>)}</select>
        </Field>
        <p className="text-xs text-ink-3">The draft is computed from the stored data now. You can refresh it until you publish.</p>
      </div>
    </Drawer>
  );
};
