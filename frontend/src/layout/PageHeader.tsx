import React from 'react';
import { usePeriod } from '../app/state';
import { PERIODS, type Period } from '../lib/period';
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
  /** Period shown when the address has none (pages that need a longer window than today). */
  defaultPeriod?: Period;
  actions?: React.ReactNode;
  tabs?: React.ReactNode;
}> = ({ title, description, showPeriod, defaultPeriod, actions, tabs }) => {
  const [period, setPeriod] = usePeriod(defaultPeriod);
  return (
    <div className="mb-6 space-y-4">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div className="min-w-0">
          <h1 className="flex items-center gap-3 text-2xl font-semibold tracking-tight text-ink sm:text-[28px]">
            <span aria-hidden className="h-7 w-1.5 rounded-full bg-gradient-to-b from-accent to-ok" />
            {title}
          </h1>
          {description && <p className="mt-1.5 pl-[18px] text-sm text-ink-3">{description}</p>}
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
