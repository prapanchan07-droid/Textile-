import React, { useState } from 'react';
import { BarChart3, Table2 } from 'lucide-react';
import { Card, CardBody, CardHeader, Segmented } from './ui';
import { DataTable, type Column } from './DataTable';

/**
 * A card that shows a chart with a one-click table view of the same rows,
 * so no value is only reachable by hovering and every chart is exportable.
 */
export function ChartPanel<T>({
  title,
  subtitle,
  actions,
  chart,
  rows,
  columns,
  rowKey,
  exportName,
  className,
}: {
  title: React.ReactNode;
  subtitle?: React.ReactNode;
  actions?: React.ReactNode;
  chart: React.ReactNode;
  rows: T[];
  columns: Column<T>[];
  rowKey: (r: T) => string;
  exportName?: string;
  className?: string;
}) {
  const [view, setView] = useState<'chart' | 'table'>('chart');
  return (
    <Card className={className}>
      <CardHeader
        title={title}
        subtitle={subtitle}
        actions={
          <>
            {actions}
            <Segmented
              size="sm"
              ariaLabel="View as"
              value={view}
              onChange={setView}
              options={[
                { value: 'chart', label: <BarChart3 className="size-3.5" aria-label="Chart" /> },
                { value: 'table', label: <Table2 className="size-3.5" aria-label="Table" /> },
              ]}
            />
          </>
        }
      />
      {view === 'chart' ? (
        <CardBody>{chart}</CardBody>
      ) : (
        <div className="pb-2">
          <DataTable rows={rows} columns={columns} rowKey={rowKey} exportName={exportName} dense />
        </div>
      )}
    </Card>
  );
}
