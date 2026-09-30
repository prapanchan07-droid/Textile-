import React from 'react';
import { Link } from 'react-router-dom';
import { RefreshCw } from 'lucide-react';
import { useHealth, useImportHistory } from '../../api/queries';
import { relativeTime } from '../../lib/format';
import { PageHeader } from '../../layout/PageHeader';
import { Button, Card, CardHeader, EmptyState, StatusPill } from '../../design/ui';

export const SystemStatusPage: React.FC = () => {
  const health = useHealth();
  const history = useImportHistory();
  const h = health.data;
  const last = history.data
    ?.map((x) => x.upload_timestamp)
    .sort()
    .slice(-1)[0];

  const rows: [string, React.ReactNode][] = h
    ? [
        [
          'API',
          <StatusPill
            key="api"
            status={h.status === 'healthy' ? 'HEALTHY' : 'CRITICAL'}
            label={h.status === 'healthy' ? 'Operational' : titleOf(h.status)}
          />,
        ],
        [
          'Database',
          <StatusPill
            key="db"
            status={h.database.status === 'healthy' ? 'HEALTHY' : 'CRITICAL'}
            label={`${h.database.database_type ?? 'unknown'} · ${h.database.status}`}
          />,
        ],
        ['Version', h.version],
        ['Environment', h.environment],
        ['Reports imported', history.data ? String(history.data.length) : '—'],
        ['Last import', last ? relativeTime(last) : 'Never'],
      ]
    : [];

  return (
    <>
      <PageHeader
        title="System Status"
        description="Service health and data freshness"
        actions={
          <Button size="sm" onClick={() => health.refetch()} loading={health.isFetching} icon={<RefreshCw className="size-3.5" />}>
            Check again
          </Button>
        }
      />
      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader title="Services" />
          {health.isError ? (
            <EmptyState title="API unreachable" description={(health.error as Error).message} />
          ) : (
            <dl className="divide-y divide-line border-t border-line">
              {rows.map(([k, v]) => (
                <div key={k} className="flex items-center justify-between px-4 py-2.5 text-sm">
                  <dt className="text-ink-3">{k}</dt>
                  <dd className="text-ink">{v}</dd>
                </div>
              ))}
            </dl>
          )}
        </Card>
        <Card>
          <CardHeader title="Data sources" subtitle="Where dashboard numbers come from" />
          <div className="space-y-3 px-4 pb-4 text-sm text-ink-2">
            <p>
              Pages show built-in sample data until the matching sheet of the standard template, or a recognised factory report, is
              imported. Production is the exception: it only ever shows imported production reports.
            </p>
            <Link to="/data" className="text-sm font-medium text-accent-ink hover:underline">
              Go to Data Imports
            </Link>
          </div>
        </Card>
      </div>
    </>
  );
};

const titleOf = (s: string) => s.charAt(0).toUpperCase() + s.slice(1);
