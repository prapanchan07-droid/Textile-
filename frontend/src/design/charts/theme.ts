import { useMemo } from 'react';
import { useTheme } from '../../app/state';

export interface ChartTheme {
  surface: string;
  grid: string;
  axis: string;
  label: string;
  ink: string;
  series: [string, string, string];
  muted: string;
  critical: string;
}

const read = (name: string) => getComputedStyle(document.documentElement).getPropertyValue(name).trim();

/** Chart colors come from CSS tokens so light/dark stay defined in one place (index.css). */
export function useChartTheme(): ChartTheme {
  const [, , resolved] = useTheme();
  return useMemo(
    () => ({
      surface: read('--chart-surface'),
      grid: read('--chart-grid'),
      axis: read('--chart-axis'),
      label: read('--chart-label'),
      ink: read('--chart-ink'),
      series: [read('--series-1'), read('--series-2'), read('--series-3')],
      muted: read('--series-muted'),
      critical: read('--status-critical'),
    }),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [resolved],
  );
}

export const axisTick = (t: ChartTheme) => ({ fill: t.label, fontSize: 11 });
