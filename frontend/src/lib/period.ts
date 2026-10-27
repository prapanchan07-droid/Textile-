/**
 * Reporting periods. They are anchored on the latest date that has data (imported reports lag the calendar),
 * so "Latest day" means the most recent production day in the database, not today.
 */
export type Period = 'latest' | '7d' | '30d' | 'month' | 'custom';

export const PERIODS: { value: Period; label: string; short: string }[] = [
  { value: 'latest', label: 'Latest day', short: 'Day' },
  { value: '7d', label: 'Last 7 days', short: '7D' },
  { value: '30d', label: 'Last 30 days', short: '30D' },
  { value: 'month', label: 'Month to date', short: 'MTD' },
  { value: 'custom', label: 'Custom', short: 'Custom' },
];

export const isPeriod = (v: string | null): v is Period => PERIODS.some((p) => p.value === v);

export const periodLabel = (p: Period) => PERIODS.find((x) => x.value === p)?.label ?? p;
