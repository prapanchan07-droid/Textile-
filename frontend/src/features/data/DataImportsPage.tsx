import React, { useEffect, useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import { ChevronDown, Download, FileSpreadsheet, FileText, FolderOpen, RotateCcw, Trash2, UploadCloud } from 'lucide-react';
import { downloadTemplate, useImportHistory, useImportJob, useStartImport, type ImportHistoryItem } from '../../api/queries';
import { cn, relativeTime } from '../../lib/format';
import { PageHeader } from '../../layout/PageHeader';
import { Badge, Button, Card, CardBody, CardHeader, Meter, Notice, StatusPill, titleCase } from '../../design/ui';
import { DataTable } from '../../design/DataTable';

const ACCEPT = '.xlsx,.xls,.csv,.pdf,.jpg,.jpeg,.png';

const REPORT_TYPES = [
  'PRODUCTION',
  'PREPARATORY_PRODUCTION',
  'SPINNING_PRODUCTION',
  'WEAVING',
  'QUALITY',
  'DOWNTIME',
  'ENERGY',
  'MAINTENANCE',
  'MANPOWER',
  'BUSINESS',
];

/** Which template sheet feeds which page, so admins know what an upload will change. */
const SHEETS: { sheet: string; pages: string }[] = [
  { sheet: 'Machine_Data', pages: 'Control Tower, Production, Machines, Action Center' },
  { sheet: 'Manpower', pages: 'Workforce' },
  { sheet: 'Quality', pages: 'Quality' },
  { sheet: 'Business', pages: 'Sales & Finance' },
  { sheet: 'Stock', pages: 'Sales & Finance' },
  { sheet: 'Actions', pages: 'Action Center' },
];

const fileSize = (b: number) => (b < 1024 * 1024 ? `${(b / 1024).toFixed(0)} KB` : `${(b / 1024 / 1024).toFixed(1)} MB`);

export const DataImportsPage: React.FC = () => {
  const history = useImportHistory();
  const templateRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (window.location.hash === '#template') templateRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  return (
    <>
      <PageHeader title="Data Imports" description="Upload factory reports. Every dashboard recalculates from what you import." />
      <div className="grid gap-4 xl:grid-cols-3">
        <div className="xl:col-span-2">
          <Uploader />
        </div>
        <div ref={templateRef} id="template">
          <TemplateCard />
        </div>
      </div>

      <Card className="mt-4">
        <CardHeader title="Import history" subtitle="Every file processed, newest first" />
        <DataTable<ImportHistoryItem>
          rows={history.data ?? []}
          rowKey={(r) => r.id}
          searchable={(r) => `${r.filename} ${r.report_type}`}
          searchPlaceholder="Search file or type"
          exportName="import-history"
          initialSort={{ key: 'uploaded', dir: 'desc' }}
          emptyTitle={history.isLoading ? 'Loading…' : history.isError ? 'Could not load history' : 'No reports imported yet'}
          emptyDescription={
            history.isError ? (history.error as Error).message : 'Imported files appear here with their detected type and report date.'
          }
          columns={[
            {
              key: 'file',
              header: 'File',
              value: (r) => r.filename,
              render: (r) => (
                <span className="flex items-center gap-2">
                  <FileText className="size-4 shrink-0 text-ink-3" />
                  <span className="truncate font-medium">{r.filename}</span>
                </span>
              ),
            },
            { key: 'type', header: 'Detected type', value: (r) => r.report_type, render: (r) => <Badge>{titleCase(r.report_type)}</Badge> },
            { key: 'date', header: 'Report date', hideBelow: 'sm', value: (r) => r.report_date ?? '', render: (r) => r.report_date ?? '—' },
            {
              key: 'conf',
              header: 'Confidence',
              align: 'right',
              hideBelow: 'md',
              value: (r) => r.confidence_score,
              render: (r) => `${Math.round(r.confidence_score <= 1 ? r.confidence_score * 100 : r.confidence_score)}%`,
            },
            { key: 'status', header: 'Status', value: (r) => r.status, render: (r) => <StatusPill status={r.status} /> },
            {
              key: 'uploaded',
              header: 'Uploaded',
              align: 'right',
              value: (r) => r.upload_timestamp,
              render: (r) => relativeTime(r.upload_timestamp),
            },
          ]}
        />
      </Card>
    </>
  );
};

const Uploader: React.FC = () => {
  const [files, setFiles] = useState<File[]>([]);
  const [dragging, setDragging] = useState(false);
  const [showOptions, setShowOptions] = useState(false);
  const [reportType, setReportType] = useState('');
  const [reportDate, setReportDate] = useState('');
  const [replace, setReplace] = useState(false);
  const [jobId, setJobId] = useState<string | null>(null);
  const input = useRef<HTMLInputElement>(null);
  const start = useStartImport();
  const job = useImportJob(jobId);
  const history = useImportHistory();

  const running = start.isPending || job.data?.status === 'PROCESSING' || (!!jobId && job.isPending);
  const done = job.data && job.data.status !== 'PROCESSING';

  useEffect(() => {
    if (done) history.refetch();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [done]);

  const add = (list: FileList | File[]) => {
    const incoming = Array.from(list);
    setFiles((prev) => {
      const seen = new Set(prev.map((f) => f.name + f.size));
      return [...prev, ...incoming.filter((f) => !seen.has(f.name + f.size))];
    });
  };

  const submit = () =>
    start.mutate(
      { files, reportType: reportType || undefined, reportDate: reportDate || undefined, forceReplace: replace },
      { onSuccess: (r) => setJobId(r.job_id) },
    );

  const reset = () => {
    setFiles([]);
    setJobId(null);
    start.reset();
    if (input.current) input.current.value = '';
  };

  const statusFor = (name: string) => job.data?.file_statuses.find((f) => f.filename === name);

  return (
    <Card>
      <CardHeader
        title="Upload reports"
        subtitle="Excel, CSV, PDF or photos of printed reports. Type and date are detected automatically."
      />
      <CardBody className="space-y-4">
        <input
          ref={input}
          type="file"
          multiple
          accept={ACCEPT}
          className="hidden"
          onChange={(e) => e.target.files && add(e.target.files)}
        />

        {!jobId && (
          <div
            onDragOver={(e) => {
              e.preventDefault();
              setDragging(true);
            }}
            onDragLeave={() => setDragging(false)}
            onDrop={(e) => {
              e.preventDefault();
              setDragging(false);
              add(e.dataTransfer.files);
            }}
            onClick={() => input.current?.click()}
            onKeyDown={(e) => (e.key === 'Enter' || e.key === ' ') && input.current?.click()}
            role="button"
            tabIndex={0}
            className={cn(
              'flex cursor-pointer flex-col items-center justify-center rounded-lg border-2 border-dashed px-6 py-8 text-center transition-colors',
              dragging ? 'border-accent bg-accent-soft' : 'border-line-strong bg-subtle hover:border-accent/60',
            )}
          >
            <UploadCloud className="mb-2 size-7 text-ink-3" />
            <div className="text-sm font-medium text-ink">Drop files here or click to browse</div>
            <div className="mt-0.5 text-xs text-ink-3">XLSX, XLS, CSV, PDF, JPG, PNG · multiple files at once</div>
          </div>
        )}

        {files.length > 0 && (
          <ul className="divide-y divide-line rounded-md border border-line">
            {files.map((f, i) => {
              const st = statusFor(f.name);
              return (
                <li key={f.name + f.size} className="flex items-center gap-3 px-3 py-2">
                  <FileText className="size-4 shrink-0 text-ink-3" />
                  <div className="min-w-0 flex-1">
                    <div className="truncate text-sm text-ink">{f.name}</div>
                    <div className="truncate text-2xs text-ink-3">{st?.message ?? fileSize(f.size)}</div>
                  </div>
                  {st ? (
                    <StatusPill status={st.status} label={st.status === 'SUCCESS' ? 'Imported' : titleCase(st.status)} />
                  ) : jobId ? (
                    <StatusPill tone="neutral" label="Queued" />
                  ) : (
                    <button
                      onClick={() => setFiles((p) => p.filter((_, j) => j !== i))}
                      className="rounded p-1 text-ink-3 hover:bg-muted hover:text-bad"
                      aria-label={`Remove ${f.name}`}
                    >
                      <Trash2 className="size-3.5" />
                    </button>
                  )}
                </li>
              );
            })}
          </ul>
        )}

        {files.length > 0 && !jobId && (
          <div className="rounded-md border border-line">
            <button
              onClick={() => setShowOptions((s) => !s)}
              className="flex w-full items-center justify-between px-3 py-2 text-xs font-medium text-ink-2"
            >
              Advanced options
              <ChevronDown className={cn('size-3.5 transition-transform', showOptions && 'rotate-180')} />
            </button>
            {showOptions && (
              <div className="grid gap-3 border-t border-line p-3 sm:grid-cols-3">
                <label className="space-y-1 text-xs text-ink-3">
                  <span>Report type</span>
                  <select
                    value={reportType}
                    onChange={(e) => setReportType(e.target.value)}
                    className="h-8 w-full rounded-md border border-line bg-surface px-2 text-sm text-ink"
                  >
                    <option value="">Detect automatically</option>
                    {REPORT_TYPES.map((t) => (
                      <option key={t} value={t}>
                        {titleCase(t)}
                      </option>
                    ))}
                  </select>
                </label>
                <label className="space-y-1 text-xs text-ink-3">
                  <span>Report date</span>
                  <input
                    type="date"
                    value={reportDate}
                    onChange={(e) => setReportDate(e.target.value)}
                    className="h-8 w-full rounded-md border border-line bg-surface px-2 text-sm text-ink"
                  />
                </label>
                <label className="flex items-center gap-2 self-end pb-1.5 text-xs text-ink-2">
                  <input
                    type="checkbox"
                    checked={replace}
                    onChange={(e) => setReplace(e.target.checked)}
                    className="accent-[rgb(var(--accent))]"
                  />
                  Replace existing data for the same date
                </label>
              </div>
            )}
          </div>
        )}

        {job.data && (
          <div className="space-y-1.5">
            <div className="flex justify-between text-xs">
              <span className="text-ink-2">
                {job.data.status === 'PROCESSING'
                  ? `Processing ${job.data.processed_count} of ${job.data.total_files}…`
                  : `${job.data.success_count} imported · ${job.data.duplicate_count} duplicate · ${job.data.failed_count} failed`}
              </span>
              <span className="num text-ink-3">{job.data.progress_pct}%</span>
            </div>
            <Meter value={job.data.progress_pct} max={100} tone={job.data.failed_count ? 'warn' : 'info'} />
          </div>
        )}

        {start.isError && <Notice tone="bad">{(start.error as Error).message}</Notice>}
        {done && job.data!.success_count > 0 && (
          <Notice
            tone="ok"
            action={
              <Link to="/" className="text-xs font-medium underline">
                View Control Tower
              </Link>
            }
          >
            Dashboards have been refreshed with the new data.
          </Notice>
        )}
        {done && job.data!.duplicate_count > 0 && (
          <Notice tone="warn">Some files were already imported. Upload again with “Replace existing data” to overwrite them.</Notice>
        )}

        <div className="flex items-center justify-end gap-2">
          {jobId ? (
            <Button onClick={reset} disabled={running} icon={<RotateCcw className="size-3.5" />}>
              Import more files
            </Button>
          ) : (
            <>
              {files.length > 0 && (
                <Button variant="ghost" onClick={() => input.current?.click()} icon={<FolderOpen className="size-3.5" />}>
                  Add files
                </Button>
              )}
              <Button
                variant="primary"
                disabled={!files.length}
                loading={running}
                onClick={submit}
                icon={<UploadCloud className="size-4" />}
              >
                Import {files.length ? `${files.length} file${files.length > 1 ? 's' : ''}` : ''}
              </Button>
            </>
          )}
        </div>
      </CardBody>
    </Card>
  );
};

const TemplateCard: React.FC = () => {
  const [busy, setBusy] = useState<'template' | 'sample' | null>(null);
  const [error, setError] = useState<string | null>(null);
  const get = async (sample: boolean) => {
    setBusy(sample ? 'sample' : 'template');
    setError(null);
    try {
      await downloadTemplate(sample);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Download failed');
    } finally {
      setBusy(null);
    }
  };
  return (
    <Card className="h-full">
      <CardHeader
        title={
          <span className="inline-flex items-center gap-1.5">
            <FileSpreadsheet className="size-4 text-ok" /> Standard data template
          </span>
        }
        subtitle="One workbook, one sheet per data set. Fill it in and upload it here."
      />
      <CardBody className="space-y-4">
        <div className="flex gap-2">
          <Button
            variant="primary"
            size="sm"
            loading={busy === 'template'}
            onClick={() => get(false)}
            icon={<Download className="size-3.5" />}
          >
            Blank template
          </Button>
          <Button size="sm" loading={busy === 'sample'} onClick={() => get(true)} icon={<Download className="size-3.5" />}>
            With 7 days of sample data
          </Button>
        </div>
        {error && <Notice tone="bad">{error}</Notice>}
        <div>
          <div className="mb-1.5 text-2xs font-medium uppercase tracking-wide text-ink-3">What each sheet updates</div>
          <dl className="divide-y divide-line rounded-md border border-line text-xs">
            {SHEETS.map((s) => (
              <div key={s.sheet} className="flex justify-between gap-3 px-3 py-2">
                <dt className="font-mono text-ink">{s.sheet}</dt>
                <dd className="text-right text-ink-3">{s.pages}</dd>
              </div>
            ))}
          </dl>
          <p className="mt-2 text-xs text-ink-3">
            A page switches to your data only once its sheet is uploaded. Re-uploading replaces earlier template data for the same dates.
          </p>
        </div>
      </CardBody>
    </Card>
  );
};
