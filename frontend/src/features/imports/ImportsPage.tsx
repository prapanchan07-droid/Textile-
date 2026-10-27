import React, { useRef, useState } from 'react';
import { CheckCircle2, FileSpreadsheet, UploadCloud, XCircle } from 'lucide-react';
import { useQueryClient } from '@tanstack/react-query';
import { api, mk, useImport, useImportIssues, useImports, useMillMutation } from '../../api/mill';
import { useParam } from '../../app/state';
import { QueryView } from '../../design/QueryView';
import { DataTable } from '../../design/DataTable';
import { Badge, Button, Card, CardBody, CardHeader, Notice, Select, StatusPill } from '../../design/ui';
import { cn } from '../../lib/format';
import { PageTitle, fmt } from '../common/parts';
import type { ImportBatch } from '../../types/mill';

const statusTone = (s: ImportBatch['status']) => (s === 'COMMITTED' ? 'ok' : s === 'FAILED' ? 'bad' : s === 'DUPLICATE' || s === 'DISCARDED' ? 'neutral' : 'warn');

export const ImportsPage: React.FC = () => {
  const [id, setId] = useParam('id');
  const history = useImports();
  const qc = useQueryClient();
  const input = useRef<HTMLInputElement>(null);
  const [drag, setDrag] = useState(false);
  const upload = useMillMutation((f: File) => api.upload(f));
  const send = (files: FileList | null) => {
    if (!files) return;
    [...files].forEach((f) => upload.mutate(f, { onSuccess: (b) => { setId(String(b.id)); qc.invalidateQueries({ queryKey: mk.all }); } }));
  };
  return (
    <>
      <PageTitle title="Data imports and quality" subtitle="Upload the mill's reports. Each file is previewed, checked and reconciled against its own totals before anything is stored. Originals are kept unchanged." />
      <Card className="mb-4">
        <CardBody className="pt-5">
          <div
            onDragOver={(e) => { e.preventDefault(); setDrag(true); }}
            onDragLeave={() => setDrag(false)}
            onDrop={(e) => { e.preventDefault(); setDrag(false); send(e.dataTransfer.files); }}
            className={cn('flex flex-col items-center justify-center gap-2 rounded-2xl border-2 border-dashed px-6 py-8 text-center', drag ? 'border-accent bg-accent-soft' : 'border-line')}>
            <UploadCloud className="size-7 text-ink-3" />
            <p className="text-sm text-ink">Drop .xls / .xlsx / .csv files here, or</p>
            <Button variant="primary" loading={upload.isPending} onClick={() => input.current?.click()}>Choose files</Button>
            <input ref={input} type="file" multiple accept=".xls,.xlsx,.csv" className="hidden" onChange={(e) => { send(e.target.files); e.target.value = ''; }} />
            <p className="text-xs text-ink-3">Recognised by structure: the mill's daily TY/TS/SZ workbook, the Tsudakoma "Report by term" export (PICK or MTR) and the Toyota "Shift Report".</p>
          </div>
          {upload.isError && <Notice tone="bad">{(upload.error as Error).message}</Notice>}
        </CardBody>
      </Card>
      {id && <BatchDetail id={Number(id)} onClose={() => setId(null)} />}
      <QueryView query={history}>
        {(d) => (
          <Card>
            <CardHeader title="Import history" subtitle={`${d.total} uploads`} />
            <CardBody>
              <DataTable rows={d.items} rowKey={(b) => String(b.id)} onRowClick={(b) => setId(String(b.id))} selectedKey={id} exportName="imports" emptyTitle="Nothing imported yet"
                columns={[
                  { key: 'id', header: '#', render: (b) => b.id, value: (b) => b.id },
                  { key: 'f', header: 'File', render: (b) => <span className="inline-flex items-center gap-1.5"><FileSpreadsheet className="size-3.5 text-ink-3" />{b.filename}</span>, value: (b) => b.filename },
                  { key: 'fmt', header: 'Format', render: (b) => b.format_label ?? '—', value: (b) => b.source_format, hideBelow: 'lg' },
                  { key: 's', header: 'Status', render: (b) => <StatusPill tone={statusTone(b.status)} label={b.status.toLowerCase()} />, value: (b) => b.status },
                  { key: 'p', header: 'Period', render: (b) => (b.period_start ? `${fmt.date(b.period_start)}${b.period_end !== b.period_start ? ` – ${fmt.date(b.period_end)}` : ''}` : '—'), value: (b) => b.period_start, hideBelow: 'md' },
                  { key: 'n', header: 'Records', align: 'right', render: (b) => (b.status === 'COMMITTED' ? `${b.records_inserted} new · ${b.records_updated} upd` : fmt.n(b.records_parsed)), value: (b) => b.records_parsed },
                  { key: 'q', header: 'Checks', render: (b) => <span className="inline-flex gap-1">{b.error_count > 0 && <Badge tone="bad">{b.error_count} err</Badge>}{b.warning_count > 0 && <Badge tone="warn">{b.warning_count} warn</Badge>}{(b.reconciliation_summary.MISMATCH ?? 0) > 0 && <Badge tone="warn">{b.reconciliation_summary.MISMATCH} mismatch</Badge>}</span>, value: (b) => b.warning_count },
                  { key: 'at', header: 'Uploaded', render: (b) => fmt.dateTime(b.created_at), value: (b) => b.created_at, hideBelow: 'md' },
                ]} />
            </CardBody>
          </Card>
        )}
      </QueryView>
    </>
  );
};

const BatchDetail: React.FC<{ id: number; onClose: () => void }> = ({ id, onClose }) => {
  const q = useImport(id);
  const [sev, setSev] = useState('');
  const [page, setPage] = useState(1);
  const issues = useImportIssues(id, sev, page);
  const commit = useMillMutation(() => api.post(`/mill/imports/${id}/commit`, {}));
  const discard = useMillMutation(() => api.post(`/mill/imports/${id}/discard`, {}));
  const b = q.data;
  if (!b) return null;
  const plan = b.summary?.plan;
  const dq = b.summary?.data_quality;
  const recon = b.reconciliation ?? [];
  const mismatches = recon.filter((c) => c.status !== 'MATCH');
  return (
    <Card className="mb-4">
      <CardHeader title={`#${b.id} ${b.filename}`} subtitle={`${b.format_label ?? 'Unrecognised'} · ${fmt.n(b.size_bytes / 1024)} KB · parser ${b.summary ? '' : ''}`}
        actions={<Button size="sm" variant="ghost" onClick={onClose}>Close</Button>} />
      <CardBody className="space-y-4 text-sm">
        <div className="flex flex-wrap items-center gap-2"><StatusPill tone={statusTone(b.status)} label={b.status.toLowerCase()} />
          {b.period_start && <span className="text-xs text-ink-3">Data for {fmt.date(b.period_start)}{b.period_end !== b.period_start ? ` – ${fmt.date(b.period_end)}` : ''} · historical, not live</span>}</div>
        {b.status === 'FAILED' && <Notice tone="bad">{b.error}</Notice>}
        {b.status === 'DUPLICATE' && <Notice tone="info">{b.summary?.message}</Notice>}
        {b.status === 'PROCESSING' && <Notice tone="info">Importing… this page updates when it is done.</Notice>}
        {plan && b.status === 'PREVIEWED' && (
          <Notice tone={b.error_count ? 'warn' : 'info'} action={<span className="flex gap-2">
            <Button size="sm" icon={<XCircle className="size-3.5" />} loading={discard.isPending} onClick={() => discard.mutate(undefined)}>Discard</Button>
            <Button size="sm" variant="primary" icon={<CheckCircle2 className="size-3.5" />} loading={commit.isPending} onClick={() => commit.mutate(undefined)}>Import {fmt.n(b.records_parsed)} records</Button></span>}>
            Preview: {plan.insert} new, {plan.update} updated, {plan.unchanged} unchanged loom-shift records{plan.new_looms ? `; ${plan.new_looms} new looms will be registered` : ''}. {b.error_count} errors, {b.warning_count} warnings.
          </Notice>
        )}
        {b.status === 'COMMITTED' && <Notice tone="ok">Imported {fmt.dateTime(b.committed_at)}: {b.records_inserted} new, {b.records_updated} updated, {b.records_unchanged} unchanged. Alert rules were evaluated afterwards.</Notice>}
        {(commit.isError || discard.isError) && <Notice tone="bad">{((commit.error || discard.error) as Error).message}</Notice>}
        {dq && (
          <div className="grid gap-4 lg:grid-cols-2">
            <div>
              <h3 className="mb-1 text-xs font-semibold text-ink-2">Field completeness</h3>
              <ul className="grid grid-cols-2 gap-x-4 text-xs">{Object.entries(dq.completeness_pct).map(([k, v]) => (
                <li key={k} className="flex justify-between"><span className="text-ink-3">{k}</span><span className={cn('num', v < 100 && 'text-warn')}>{v}%</span></li>
              ))}</ul>
            </div>
            <div>
              <h3 className="mb-1 text-xs font-semibold text-ink-2">Reconciliation with the file's own totals</h3>
              <p className="text-xs text-ink-2">{dq.reconciliation.MATCH ?? 0} match · {dq.reconciliation.MISMATCH ?? 0} mismatch · {dq.reconciliation.NOT_COMPARABLE ?? 0} not comparable</p>
              <ul className="mt-1 text-xs text-ink-3">{Object.entries(dq.issues).map(([k, v]) => <li key={k}>{k}: {v}</li>)}</ul>
            </div>
          </div>
        )}
        {mismatches.length > 0 && (
          <div>
            <h3 className="mb-1 text-xs font-semibold text-ink-2">Reconciliation differences ({mismatches.length})</h3>
            <DataTable dense rows={mismatches} rowKey={(c) => c.scope + c.metric} exportName={`import-${b.id}-reconciliation`}
              columns={[
                { key: 's', header: 'Scope', render: (c) => c.scope, value: (c) => c.scope },
                { key: 'm', header: 'Check', render: (c) => c.metric, value: (c) => c.metric, wrap: true },
                { key: 'src', header: 'File says', align: 'right', render: (c) => fmt.n(c.source_value, 2), value: (c) => c.source_value },
                { key: 'cmp', header: 'Imported rows give', align: 'right', render: (c) => fmt.n(c.computed_value, 2), value: (c) => c.computed_value },
                { key: 'n', header: 'Note', render: (c) => <span className="text-xs text-ink-3">{c.note}</span>, value: (c) => c.note, wrap: true },
              ]} />
          </div>
        )}
        <div>
          <div className="mb-1 flex items-center justify-between">
            <h3 className="text-xs font-semibold text-ink-2">Row-level issues</h3>
            <Select aria-label="Severity" value={sev} onChange={(e) => { setSev(e.target.value); setPage(1); }} options={[{ value: '', label: 'All' }, { value: 'ERROR', label: 'Errors' }, { value: 'WARNING', label: 'Warnings' }, { value: 'INFO', label: 'Info' }]} />
          </div>
          {issues.data && (
            <>
              <DataTable dense rows={issues.data.items} rowKey={(i) => String(i.id)} exportName={`import-${b.id}-issues`} emptyTitle="No issues"
                columns={[
                  { key: 'sev', header: '', render: (i) => <StatusPill tone={i.severity === 'ERROR' ? 'bad' : i.severity === 'WARNING' ? 'warn' : 'info'} label={i.severity.toLowerCase()} />, value: (i) => i.severity },
                  { key: 'code', header: 'Code', render: (i) => <code className="text-2xs">{i.code}</code>, value: (i) => i.code },
                  { key: 'msg', header: 'Message', render: (i) => i.message, value: (i) => i.message, wrap: true },
                  { key: 'where', header: 'Where', render: (i) => [i.sheet, i.row && `row ${i.row}`, i.column].filter(Boolean).join(' · ') || '—', value: (i) => `${i.sheet}${i.row}` },
                  { key: 'raw', header: 'Value', render: (i) => i.raw_value ?? '', value: (i) => i.raw_value, hideBelow: 'lg' },
                ]} />
              {issues.data.total > issues.data.page_size && (
                <div className="mt-2 flex items-center justify-end gap-2 text-xs">
                  <Button size="sm" disabled={page <= 1} onClick={() => setPage(page - 1)}>Previous</Button>
                  <span>Page {page} of {Math.ceil(issues.data.total / issues.data.page_size)}</span>
                  <Button size="sm" disabled={page * issues.data.page_size >= issues.data.total} onClick={() => setPage(page + 1)}>Next</Button>
                </div>
              )}
            </>
          )}
        </div>
      </CardBody>
    </Card>
  );
};
