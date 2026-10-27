import React, { useState } from 'react';
import { Trash2 } from 'lucide-react';
import { api, useAudit, useDefinitions, useMillMutation, useTargets } from '../../api/mill';
import { useParam } from '../../app/state';
import { QueryView } from '../../design/QueryView';
import { DataTable } from '../../design/DataTable';
import { Button, Card, CardBody, CardHeader, Notice, Tabs } from '../../design/ui';
import { BasisBadge, Field, PageTitle, fmt, inputClass } from '../common/parts';

export const SettingsPage: React.FC = () => {
  const [tab, setTab] = useParam('tab', 'targets');
  return (
    <>
      <PageTitle title="Targets, definitions and audit" subtitle="Production targets, the documented metric formulas and the history of every change." />
      <div className="mb-4"><Tabs value={tab} onChange={setTab} tabs={[{ value: 'targets', label: 'Targets' }, { value: 'definitions', label: 'Metric definitions' }, { value: 'audit', label: 'Audit log' }]} /></div>
      {tab === 'targets' ? <Targets /> : tab === 'definitions' ? <Definitions /> : <Audit />}
    </>
  );
};

const Targets: React.FC = () => {
  const q = useTargets();
  const [f, setF] = useState({ scope: 'CATEGORY', scope_ref: 'TY', metric: 'meters_per_shift', value: '', effective_from: new Date().toISOString().slice(0, 10) });
  const add = useMillMutation((b: object) => api.post('/mill/targets', b));
  const del = useMillMutation((id: number) => api.del(`/mill/targets/${id}`));
  return (
    <div className="space-y-4">
      <Card>
        <CardHeader title="Add a target" subtitle="The most specific target applies: loom > group > category > mill. Meters targets are per loom per shift." />
        <CardBody>
          {add.isError && <Notice tone="bad">{(add.error as Error).message}</Notice>}
          <div className="grid gap-3 sm:grid-cols-3 lg:grid-cols-6">
            <Field label="Scope"><select className={inputClass} value={f.scope} onChange={(e) => setF({ ...f, scope: e.target.value })}>{['MILL', 'CATEGORY', 'GROUP', 'LOOM'].map((s) => <option key={s}>{s}</option>)}</select></Field>
            <Field label="Applies to" hint="Category code, group id or loom code"><input className={inputClass} value={f.scope_ref} disabled={f.scope === 'MILL'} onChange={(e) => setF({ ...f, scope_ref: e.target.value })} /></Field>
            <Field label="Metric"><select className={inputClass} value={f.metric} onChange={(e) => setF({ ...f, metric: e.target.value })}>
              <option value="meters_per_shift">Meters per loom-shift</option><option value="efficiency_pct">Efficiency %</option><option value="kilopicks_per_shift">Kilopicks per loom-shift</option></select></Field>
            <Field label="Value"><input type="number" step="any" className={inputClass} value={f.value} onChange={(e) => setF({ ...f, value: e.target.value })} /></Field>
            <Field label="From"><input type="date" className={inputClass} value={f.effective_from} onChange={(e) => setF({ ...f, effective_from: e.target.value })} /></Field>
            <div className="flex items-end"><Button variant="primary" disabled={!f.value} loading={add.isPending}
              onClick={() => add.mutate({ ...f, scope_ref: f.scope === 'MILL' ? null : f.scope_ref, value: Number(f.value) })}>Add</Button></div>
          </div>
        </CardBody>
      </Card>
      <QueryView query={q}>
        {(rows) => (
          <Card><CardBody className="pt-4">
            <DataTable dense rows={rows} rowKey={(t: any) => String(t.id)} emptyTitle="No targets" emptyDescription="Without targets, production-vs-target and the target alert stay off."
              columns={[
                { key: 's', header: 'Scope', render: (t: any) => `${t.scope}${t.scope_ref ? ` ${t.scope_ref}` : ''}`, value: (t: any) => t.scope },
                { key: 'm', header: 'Metric', render: (t: any) => t.metric, value: (t: any) => t.metric },
                { key: 'v', header: 'Value', align: 'right', render: (t: any) => fmt.n(t.value, 1), value: (t: any) => t.value },
                { key: 'f', header: 'From', render: (t: any) => fmt.date(t.effective_from), value: (t: any) => t.effective_from },
                { key: 'to', header: 'To', render: (t: any) => fmt.date(t.effective_to), value: (t: any) => t.effective_to },
                { key: 'x', header: '', render: (t: any) => <button className="text-ink-3 hover:text-bad" aria-label="Delete target" onClick={() => del.mutate(t.id)}><Trash2 className="size-3.5" /></button> },
              ]} />
          </CardBody></Card>
        )}
      </QueryView>
    </div>
  );
};

const Definitions: React.FC = () => {
  const q = useDefinitions();
  return (
    <QueryView query={q}>
      {(defs) => (
        <div className="grid gap-3 lg:grid-cols-2">
          {defs.map((m) => (
            <Card key={m.key}>
              <CardHeader title={<span className="inline-flex items-center gap-2">{m.label} <BasisBadge basis={m.basis} /></span>} subtitle={m.meaning} />
              <CardBody className="space-y-1 text-xs text-ink-2">
                <p><span className="text-ink-3">Formula:</span> <code>{m.formula}</code> ({m.unit})</p>
                <p><span className="text-ink-3">Source fields:</span> {m.source_fields}</p>
                <p><span className="text-ink-3">Aggregation:</span> {m.aggregation}</p>
                <p><span className="text-ink-3">Missing data:</span> {m.missing_data}</p>
                {m.notes && <p><span className="text-ink-3">Note:</span> {m.notes}</p>}
              </CardBody>
            </Card>
          ))}
        </div>
      )}
    </QueryView>
  );
};

const Audit: React.FC = () => {
  const [page, setPage] = useState(1);
  const q = useAudit(page);
  return (
    <QueryView query={q}>
      {(d) => (
        <Card><CardBody className="pt-4">
          <DataTable dense rows={d.items} rowKey={(a: any) => String(a.id)} exportName="audit"
            columns={[
              { key: 'at', header: 'When', render: (a: any) => fmt.dateTime(a.at), value: (a: any) => a.at },
              { key: 'who', header: 'Who', render: (a: any) => a.actor ?? 'system', value: (a: any) => a.actor },
              { key: 'act', header: 'Action', render: (a: any) => a.action, value: (a: any) => a.action },
              { key: 'e', header: 'What', render: (a: any) => `${a.entity}${a.entity_id ? ` ${a.entity_id}` : ''}`, value: (a: any) => a.entity },
              { key: 'ch', header: 'Change', render: (a: any) => <code className="text-2xs">{a.before ? `${JSON.stringify(a.before)} → ` : ''}{JSON.stringify(a.after)}</code>, wrap: true },
            ]} />
          <div className="mt-2 flex items-center justify-end gap-2 text-xs">
            <Button size="sm" disabled={page <= 1} onClick={() => setPage(page - 1)}>Previous</Button>
            <span>Page {page}</span>
            <Button size="sm" disabled={page * d.page_size >= d.total} onClick={() => setPage(page + 1)}>Next</Button>
          </div>
        </CardBody></Card>
      )}
    </QueryView>
  );
};
