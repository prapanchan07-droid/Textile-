import React from 'react';
import { usePeriod } from '../app/state';
import { PERIODS } from '../lib/period';
import { Segmented } from '../design/ui';

/**
 * Title row for every page. Pages that respond to the reporting period opt in
 * with `showPeriod`; pages that don't (e.g. Production, which reports a single
 * report date) simply don't render the control, so no filter pretends to work.
 */
export const PageHeader: React.FC<{
  title: string;
  description?: React.ReactNode;
  showPeriod?: boolean;
  actions?: React.ReactNode;
  tabs?: React.ReactNode;
}> = ({ title, description, showPeriod, actions, tabs }) => {
  const [period, setPeriod] = usePeriod();
  return (
    <div className="mb-5 space-y-4">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div className="min-w-0">
          <h1 className="text-xl font-semibold tracking-tight text-ink">{title}</h1>
          {description && <p className="mt-0.5 text-sm text-ink-3">{description}</p>}
        </div>
        <div className="flex flex-wrap items-center gap-2">
          {actions}
          {showPeriod && (
            <Segmented
              ariaLabel="Reporting period"
              value={period}
              onChange={setPeriod}
              options={PERIODS.map((p) => ({ value: p.value, label: p.label }))}
            />
          )}
        </div>
      </div>
      {tabs}
    </div>
  );
};
