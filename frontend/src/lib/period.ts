/**
 * One period vocabulary for the whole app. The backend endpoints grew different
 * spellings for the same window, so each API hook maps through here rather than
 * each page inventing its own options.
 */
export type Period = 'TODAY' | 'YESTERDAY' | 'LAST_7_DAYS' | 'THIS_MONTH';

export const PERIODS: { value: Period; label: string; short: string }[] = [
  { value: 'TODAY', label: 'Today', short: 'Today' },
  { value: 'YESTERDAY', label: 'Yesterday', short: 'Yesterday' },
  { value: 'LAST_7_DAYS', label: 'Last 7 days', short: '7D' },
  { value: 'THIS_MONTH', label: 'Month to date', short: 'MTD' },
];

export const isPeriod = (v: string | null): v is Period => PERIODS.some((p) => p.value === v);

export const periodLabel = (p: Period) => PERIODS.find((x) => x.value === p)?.label ?? p;

/** /overview and /decision-center use an enum with THIS_WEEK instead of LAST_7_DAYS. */
export const toOverviewPeriod = (p: Period) => (p === 'LAST_7_DAYS' ? 'THIS_WEEK' : p);

/** /overview compares against the equivalent previous window. */
export const toComparison = (p: Period) => (p === 'LAST_7_DAYS' ? 'PREVIOUS_WEEK' : p === 'THIS_MONTH' ? 'PREVIOUS_MONTH' : 'PREVIOUS_DAY');

export const comparisonLabel = (p: Period) =>
  p === 'LAST_7_DAYS' ? 'previous 7 days' : p === 'THIS_MONTH' ? 'previous month' : 'previous day';
