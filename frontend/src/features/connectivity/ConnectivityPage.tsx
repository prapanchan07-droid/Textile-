import React, { useState } from 'react';
import { PlayCircle, ShieldCheck } from 'lucide-react';
import { api, useConnectivity, useMillMutation } from '../../api/mill';
import { QueryView } from '../../design/QueryView';
import { DataTable } from '../../design/DataTable';
import { Drawer } from '../../design/Drawer';
import { Button, Card, CardBody, CardHeader, Notice } from '../../design/ui';
import { Field, LiveState, PageTitle, fmt, inputClass } from '../common/parts';
import type { Connection } from '../../types/mill';

export const ConnectivityPage: React.FC = () => {
  const q = useConnectivity();
  const [edit, setEdit] = useState<Connection | null>(null);
  const collect = useMillMutation(() => api.post<Record<string, number>>('/mill/connectivity/collect-once', {}));
  return (
    <>
      <PageTitle title="Machine connectivity" subtitle="Per-loom readiness for live data. An IP address alone does not tell us what a loom exposes; vendor adapters stay disabled until the OEM interface is confirmed."
        actions={<Button icon={<PlayCircle className="size-4" />} loading={collect.isPending} onClick={() => collect.mutate(undefined)}>Poll once now</Button>} />
      {collect.data && <Notice tone="info">Polling cycle: {Object.entries(collect.data).map(([k, v]) => `${v} ${k.replace('_', ' ')}`).join(', ') || 'no enabled connections'}.</Notice>}
      <QueryView query={q}>
        {(d) => (
          <div className="space-y-4">
            <div className="grid gap-4 lg:grid-cols-2">
              <Card>
                <CardHeader title={<span className="inline-flex items-center gap-1.5"><ShieldCheck className="size-4" /> Security policy</span>} />
                <CardBody><ul className="list-disc space-y-1 pl-5 text-sm text-ink-2">{d.policy.map((p) => <li key={p}>{p}</li>)}</ul></CardBody>
              </Card>
              <Card>
                <CardHeader title="Adapters and what each needs" />
                <CardBody><ul className="space-y-2 text-sm">{Object.entries(d.adapters).map(([k, v]) => <li key={k}><span className="font-medium text-ink">{k}</span><span className="block text-xs text-ink-3">{v}</span></li>)}</ul></CardBody>
              </Card>
            </div>
            <Card>
              <CardHeader title="Looms" subtitle="Click a loom to configure. The simulator produces readings marked SIMULATED, for testing the pipeline only." />
              <CardBody>
                <DataTable rows={d.connections} rowKey={(c) => String(c.loom.id)} onRowClick={setEdit} exportName="connectivity" searchable={(c) => `${c.loom.code} ${c.adapter} ${c.state}`}
                  columns={[
                    { key: 'l', header: 'Loom', render: (c) => <span className="font-medium text-ink">{c.loom.code}</span>, value: (c) => c.loom.code },
                    { key: 'm', header: 'Manufacturer', render: (c) => `${c.loom.manufacturer}${c.loom.model ? ` ${c.loom.model}` : ''}`, value: (c) => c.loom.manufacturer, hideBelow: 'md' },
                    { key: 'a', header: 'Adapter', render: (c) => c.adapter, value: (c) => c.adapter },
                    { key: 'h', header: 'Host', render: (c) => c.host ?? '—', value: (c) => c.host, hideBelow: 'md' },
                    { key: 's', header: 'State', render: (c) => <LiveState state={c.state} origin={c.adapter === 'SIMULATOR' ? 'SIMULATED' : null} />, value: (c) => c.state },
                    { key: 'ok', header: 'Last reading', render: (c) => fmt.dateTime(c.last_success_at), value: (c) => c.last_success_at, hideBelow: 'lg' },
                    { key: 'e', header: 'Last error', render: (c) => <span className="text-xs text-ink-3">{c.last_error ?? ''}</span>, value: (c) => c.last_error, wrap: true, hideBelow: 'xl' },
                  ]} />
              </CardBody>
            </Card>
          </div>
        )}
      </QueryView>
      {edit && <ConnDrawer c={edit} onClose={() => setEdit(null)} />}
    </>
  );
};

const ConnDrawer: React.FC<{ c: Connection; onClose: () => void }> = ({ c, onClose }) => {
  const vendor = c.loom.category === 'TY' ? 'TOYOTA_TMS' : c.loom.category === 'TS' ? 'TSUDAKOMA_TISS' : null;
  const [f, setF] = useState({ adapter: c.adapter, host: c.host ?? '', port: c.port?.toString() ?? '', credentials_env: c.credentials_env ?? '', poll_seconds: String(c.poll_seconds ?? 60), enabled: c.enabled, notes: c.notes ?? '' });
  const save = useMillMutation((b: object) => api.put(`/mill/connectivity/${c.loom.id}`, b));
  return (
    <Drawer open onClose={onClose} title={`${c.loom.code} connection`} subtitle={`${c.loom.manufacturer} · currently ${c.state.toLowerCase().replace(/_/g, ' ')}`}
      footer={<div className="flex justify-end gap-2"><Button onClick={onClose}>Cancel</Button>
        <Button variant="primary" loading={save.isPending} onClick={() => save.mutate({ adapter: f.adapter, host: f.host || null, port: f.port ? Number(f.port) : null, credentials_env: f.credentials_env || null,
                                                                                        poll_seconds: Number(f.poll_seconds), enabled: f.enabled, notes: f.notes || null }, { onSuccess: onClose })}>Save</Button></div>}>
      <div className="space-y-3">
        {save.isError && <Notice tone="bad">{(save.error as Error).message}</Notice>}
        <Field label="Adapter">
          <select className={inputClass} value={f.adapter} onChange={(e) => setF({ ...f, adapter: e.target.value })}>
            <option value="NONE">None</option><option value="SIMULATOR">Simulator (test data, marked simulated)</option>
            {vendor && <option value={vendor}>{vendor} (awaiting vendor interface)</option>}
          </select>
        </Field>
        <div className="grid grid-cols-3 gap-3">
          <Field label="Host / IP"><input className={inputClass} value={f.host} onChange={(e) => setF({ ...f, host: e.target.value })} /></Field>
          <Field label="Port"><input className={inputClass} value={f.port} onChange={(e) => setF({ ...f, port: e.target.value })} /></Field>
          <Field label="Poll every (s)"><input type="number" min={10} className={inputClass} value={f.poll_seconds} onChange={(e) => setF({ ...f, poll_seconds: e.target.value })} /></Field>
        </div>
        <Field label="Credentials environment variable" hint="The name of a variable on the collector host (e.g. TOYOTA_TMS_TOKEN). Secrets are never stored here.">
          <input className={inputClass} value={f.credentials_env} onChange={(e) => setF({ ...f, credentials_env: e.target.value.toUpperCase() })} />
        </Field>
        <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={f.enabled} onChange={(e) => setF({ ...f, enabled: e.target.checked })} /> Enabled (polled by the collector)</label>
        <Field label="Notes"><textarea className={`${inputClass} h-16 py-2`} value={f.notes} onChange={(e) => setF({ ...f, notes: e.target.value })} /></Field>
      </div>
    </Drawer>
  );
};
