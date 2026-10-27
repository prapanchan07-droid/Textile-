import React, { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { ArrowLeft, Download, Printer, RefreshCw, Send } from 'lucide-react';
import { api, useMillMutation, useReport } from '../../api/mill';
import { downloadFile } from '../../api/client';
import { QueryView } from '../../design/QueryView';
import { Badge, Button, Card, CardBody, CardHeader, Kpi, KpiGrid, Notice, StatusPill } from '../../design/ui';
import { meters, pct } from '../../lib/format';
import { BasisBadge, Field, SeverityPill, fmt, inputClass } from '../common/parts';
import type { OwnerReport, ReportSnapshot } from '../../types/mill';

export const ReportPage: React.FC = () => {
  const { id } = useParams();
  const q = useReport(Number(id));
  return (
    <>
      <Link to="/reports" className="mb-3 inline-flex items-center gap-1 text-xs text-ink-3 hover:text-ink print:hidden"><ArrowLeft className="size-3.5" /> Reports</Link>
      <QueryView query={q}>{(r) => <Report r={r} />}</QueryView>
    </>
  );
};

const Section: React.FC<{ n: number; title: string; children: React.ReactNode; subtitle?: string }> = ({ n, title, children, subtitle }) => (
  <Card className="break-inside-avoid">
    <CardHeader title={`${n}. ${title}`} subtitle={subtitle} />
    <CardBody className="text-sm">{children}</CardBody>
  </Card>
);

const Report: React.FC<{ r: OwnerReport }> = ({ r }) => {
  const s = r.snapshot as ReportSnapshot;
  const draft = r.status === 'DRAFT';
  const [text, setText] = useState({ commentary: r.commentary ?? '', decisions_needed: r.decisions_needed ?? '', risks: r.risks ?? '' });
  const [ack, setAck] = useState('');
  useEffect(() => setText({ commentary: r.commentary ?? '', decisions_needed: r.decisions_needed ?? '', risks: r.risks ?? '' }), [r.id, r.commentary, r.decisions_needed, r.risks]);
  const save = useMillMutation((b: object) => api.patch(`/mill/reports/${r.id}`, b));
  const refresh = useMillMutation(() => api.post(`/mill/reports/${r.id}/refresh`, {}));
  const publish = useMillMutation(() => api.post(`/mill/reports/${r.id}/publish`, {}));
  const acknowledge = useMillMutation((b: object) => api.post(`/mill/reports/${r.id}/acknowledge`, b));
  const err = [save, refresh, publish, acknowledge].find((m) => m.isError)?.error as Error | undefined;
  const p = s.production;
  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 className="text-xl font-semibold text-ink">{r.title}</h1>
          <p className="mt-1 text-xs text-ink-3">
            Period {fmt.date(s.meta.period.from)}{s.meta.period.to !== s.meta.period.from ? ` – ${fmt.date(s.meta.period.to)}` : ''}{s.meta.period.shift ? ` · shift ${s.meta.period.shift}` : ''} ·
            generated {fmt.dateTime(s.meta.generated_at)} · {s.meta.days_with_data} day(s) with data · sources {Object.keys(s.meta.sources).join(', ') || 'none'}
          </p>
          <div className="mt-1 flex gap-2"><StatusPill status={draft ? 'IN_PROGRESS' : 'COMPLETED'} label={r.status.toLowerCase()} />
            {r.published_at && <Badge>Published {fmt.dateTime(r.published_at)}</Badge>}{r.acknowledged_at && <Badge tone="ok">Owner acknowledged {fmt.dateTime(r.acknowledged_at)}</Badge>}</div>
        </div>
        <div className="flex flex-wrap gap-2 print:hidden">
          {draft && <Button icon={<RefreshCw className="size-4" />} loading={refresh.isPending} onClick={() => refresh.mutate(undefined)}>Refresh numbers</Button>}
          <Button icon={<Download className="size-4" />} onClick={() => downloadFile(`/mill/reports/${r.id}/export.xlsx`, `weaving-report-${r.id}.xlsx`)}>Excel</Button>
          <Button icon={<Printer className="size-4" />} onClick={() => window.print()}>Print / PDF</Button>
          {draft && <Button variant="primary" icon={<Send className="size-4" />} loading={publish.isPending} disabled={!text.commentary.trim() || text.commentary !== (r.commentary ?? '')} onClick={() => publish.mutate(undefined)}>Publish</Button>}
        </div>
      </div>
      {err && <Notice tone="bad">{err.message}</Notice>}
      <Notice tone="info">{s.meta.freshness.statement}</Notice>

      <Card className="break-inside-avoid">
        <CardHeader title="GM commentary" subtitle={draft ? 'Edit, save, then publish. Commentary is required to publish.' : undefined} />
        <CardBody className="space-y-3">
          {draft ? (
            <>
              <Field label="Summary for the owner"><textarea className={`${inputClass} h-28 py-2`} value={text.commentary} onChange={(e) => setText({ ...text, commentary: e.target.value })} /></Field>
              <Field label="Decisions or support needed from management"><textarea className={`${inputClass} h-20 py-2`} value={text.decisions_needed} onChange={(e) => setText({ ...text, decisions_needed: e.target.value })} /></Field>
              <Field label="Risks and open questions"><textarea className={`${inputClass} h-20 py-2`} value={text.risks} onChange={(e) => setText({ ...text, risks: e.target.value })} /></Field>
              <Button loading={save.isPending} onClick={() => save.mutate(text)}>Save commentary</Button>
            </>
          ) : (
            <div className="space-y-2 whitespace-pre-wrap text-sm text-ink">
              <p>{r.commentary}</p>
              {r.decisions_needed && <p><strong>Decisions needed:</strong> {r.decisions_needed}</p>}
              {r.risks && <p><strong>Risks:</strong> {r.risks}</p>}
            </div>
          )}
        </CardBody>
      </Card>

      <Section n={1} title="Production overview">
        <KpiGrid>
          <Kpi label="Meters" value={meters(p.meters)} />
          <Kpi label="Kilopicks" value={fmt.n(p.kilopicks)} />
          <Kpi label="Efficiency" value={pct(p.efficiency_pct)} hint="time-weighted" />
          <Kpi label="Looms reporting" value={`${p.reporting_looms} / ${p.registered_looms}`} hint={p.not_reporting_looms.length ? `missing: ${p.not_reporting_looms.join(', ')}` : undefined} />
        </KpiGrid>
      </Section>
      <Section n={2} title="Output against target">
        {s.target.target_meters ? <p>{meters(s.target.actual_meters)} against {meters(s.target.target_meters)} ({s.target.vs_target_pct != null ? `${s.target.vs_target_pct > 0 ? '+' : ''}${s.target.vs_target_pct}%` : '—'}).</p> : <p className="text-ink-3">{s.target.note}</p>}
      </Section>
      <Section n={3} title="Efficiency and shift performance">
        <div className="grid gap-2 sm:grid-cols-2">
          <ul>{Object.entries(s.efficiency.by_shift).map(([k, v]) => <li key={k}>Shift {k}: <span className="num">{pct(v)}</span></li>)}</ul>
          <ul>{Object.entries(s.efficiency.by_category).map(([k, v]) => <li key={k}>{k}: <span className="num">{pct(v)}</span> · {meters(p.by_category[k]?.meters)}</li>)}</ul>
        </div>
      </Section>
      <Section n={4} title="Notable machine and group deviations">
        {s.deviations.length === 0 ? <p className="text-ink-3">None stand out.</p> : <ul className="space-y-1">{s.deviations.map((f) => <li key={f.id} className="flex gap-2"><BasisBadge basis={f.basis} />{f.title}</li>)}</ul>}
      </Section>
      <Section n={5} title="Stop-related problems" subtitle={s.stops.note}>
        <p className="mb-1 text-xs text-ink-3">Warp {fmt.rate(s.stops.totals.warp_stops_cmpx)} and weft {fmt.rate(s.stops.totals.weft_stops_cmpx)} stops per 100k picks.</p>
        <ul className="space-y-1">{s.stops.findings.map((f) => <li key={f.id}>{f.title}</li>)}</ul>
      </Section>
      <Section n={6} title="Critical alerts">
        {s.alerts.critical_or_escalated.length === 0 ? <p className="text-ink-3">No critical or escalated alerts. Open: {Object.entries(s.alerts.open_by_severity).map(([k, v]) => `${v} ${k.toLowerCase()}`).join(', ') || 'none'}.</p> : (
          <ul className="space-y-1">{s.alerts.critical_or_escalated.map((a) => <li key={a.id} className="flex gap-2"><SeverityPill severity={a.severity} />{a.title} · {a.status.toLowerCase()}</li>)}</ul>
        )}
      </Section>
      <Section n={7} title="Maintenance and operational work">
        <p>{s.maintenance.completed_in_period.length} work orders completed, {s.maintenance.open.length} open.</p>
        <ul className="mt-1 space-y-0.5 text-xs">{s.maintenance.open.slice(0, 8).map((w) => <li key={w.id}>{w.kind.toLowerCase()}: {w.title} ({w.status.toLowerCase()})</li>)}</ul>
      </Section>
      <Section n={8} title="Progress across groups">
        {s.groups.length === 0 ? <p className="text-ink-3">Groups are not set up yet.</p> : (
          <table className="w-full text-xs"><thead><tr className="text-left text-ink-3"><th>Group</th><th className="text-right">Meters</th><th className="text-right">Efficiency</th><th className="text-right">Open tasks</th><th className="text-right">Blocked</th><th className="text-right">Alerts</th></tr></thead>
            <tbody>{s.groups.map((g) => <tr key={g.id} className="border-t border-line"><td className="py-1">{g.name}</td><td className="num text-right">{fmt.n(g.meters)}</td><td className="num text-right">{pct(g.efficiency_pct)}</td><td className="num text-right">{g.open_tasks}</td><td className="num text-right">{g.blocked_tasks}</td><td className="num text-right">{g.open_alerts}</td></tr>)}</tbody></table>
        )}
      </Section>
      <Section n={9} title="Tasks">
        <p>{s.tasks.completed} completed in the period · {s.tasks.open} open · {s.tasks.blocked} blocked · {s.tasks.overdue.length} overdue.</p>
        <ul className="mt-1 space-y-0.5 text-xs">{s.tasks.overdue.map((t) => <li key={t.id}>Overdue: {t.title} ({t.priority.toLowerCase()})</li>)}</ul>
      </Section>
      <Section n={10} title="Energy and compressed air">
        <p className="text-ink-3">Air: {s.energy.air_status.toLowerCase().replace('_', ' ')} · electricity: {s.energy.energy_status.toLowerCase().replace('_', ' ')}. No figures are reported without measured data.</p>
      </Section>
      <Section n={11} title="Improvement opportunities" subtitle="Modeled estimates with their assumptions: potential, not realised savings">
        {s.opportunities.length === 0 ? <p className="text-ink-3">None quantified for this period.</p> : (
          <ul className="space-y-1">{s.opportunities.map((o, i) => <li key={i}>{o.title}{o.impact?.meters_gap != null ? `: about ${fmt.n(o.impact.meters_gap)} m` : ''} <span className="text-xs text-ink-3">({o.impact?.assumption})</span></li>)}</ul>
        )}
      </Section>
      <Section n={12} title="Decisions needed from management">
        {s.decisions.length === 0 && !r.decisions_needed ? <p className="text-ink-3">None escalated.</p> : <ul className="space-y-1">{s.decisions.map((t) => <li key={t.id}>{t.title} ({t.status.toLowerCase()})</li>)}</ul>}
      </Section>
      <Section n={13} title="Risks and unresolved questions">
        {s.risks.length === 0 ? <p className="text-ink-3">None recorded.</p> : <ul className="list-disc space-y-0.5 pl-5">{s.risks.map((x, i) => <li key={i}>{x}</li>)}</ul>}
      </Section>
      <Card className="break-inside-avoid">
        <CardHeader title="Calculation basis" subtitle="Sources and formulas behind the numbers in this report" />
        <CardBody className="space-y-2 text-xs text-ink-2">
          <ul>{s.meta.import_batches.map((b) => <li key={b.id}>Import #{b.id} {b.filename} ({b.format}) · {b.warnings} warnings · {b.errors} errors</li>)}</ul>
          <ul className="grid gap-x-4 sm:grid-cols-2">{Object.entries(s.meta.definitions).map(([k, v]) => <li key={k}><span className="font-medium">{k}</span>: {v}</li>)}</ul>
        </CardBody>
      </Card>
      {r.status === 'PUBLISHED' && (
        <Card className="print:hidden">
          <CardHeader title="Owner acknowledgement" />
          <CardBody className="space-y-2">
            <Field label="Comment for the GM (optional)"><textarea className={`${inputClass} h-16 py-2`} value={ack} onChange={(e) => setAck(e.target.value)} /></Field>
            <Button variant="primary" loading={acknowledge.isPending} onClick={() => acknowledge.mutate({ comment: ack || null })}>Acknowledge report</Button>
          </CardBody>
        </Card>
      )}
      {r.owner_comment && <Notice tone="info">Owner: {r.owner_comment}</Notice>}
    </div>
  );
};
