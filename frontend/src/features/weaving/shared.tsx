import React from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useWeaving } from '../../api/queries';
import { usePeriod } from '../../app/state';
import { comparisonLabel, type Period } from '../../lib/period';
import { PageHeader } from '../../layout/PageHeader';
import { QueryView } from '../../design/QueryView';
import { Notice, Tabs, type KpiProps, type Tone } from '../../design/ui';
import type { StyleCall, WeavingModuleData } from '../../types/weaving';

const TABS = [
  { value: '/weaving', label: 'Overview' },
  { value: '/weaving/looms', label: 'Looms' },
  { value: '/weaving/stoppages', label: 'Stoppages' },
  { value: '/weaving/quality', label: 'Fabric quality' },
  { value: '/weaving/styles', label: 'Styles & profit' },
  { value: '/weaving/people', label: 'People & maintenance' },
];

/** Shared frame for every weaving page: header, tabs, mock-data notice, and the one data query. */
export const WeavingPage: React.FC<{
  description: string;
  actions?: React.ReactNode;
  children: (data: WeavingModuleData, period: Period) => React.ReactNode;
}> = ({ description, actions, children }) => {
  const [period] = usePeriod();
  const query = useWeaving(period);
  const { pathname, search } = useLocation();
  const navigate = useNavigate();
  const period_q = new URLSearchParams(search).get('period');
  const tab = TABS.find((t) => t.value !== '/weaving' && pathname.startsWith(t.value))?.value ?? '/weaving';
  return (
    <>
      <PageHeader
        title="Weaving"
        description={description}
        showPeriod
        actions={actions}
        tabs={
          <Tabs
            value={tab}
            onChange={(t) => navigate({ pathname: t, search: period_q ? `?period=${period_q}` : '' })}
            tabs={TABS}
          />
        }
      />
      <QueryView query={query}>
        {(d) => (
          <div className="space-y-4">
            {d.data_source === 'MOCK' && (
              <Notice tone="info">
                <b>Sample data.</b> Weaving numbers on this page are generated for demonstration and do not come from your
                mill. Real data will replace them once weaving reports are uploaded.
              </Notice>
            )}
            {children(d, period)}
          </div>
        )}
      </QueryView>
    </>
  );
};

/** KPI delta against the previous window. `goodWhenUp` says which direction is an improvement. */
export const delta = (v: number, unit: string, goodWhenUp: boolean, period: Period): KpiProps['delta'] => ({
  text: `${v > 0 ? '+' : v < 0 ? '−' : ''}${Math.abs(v).toFixed(1)}${unit}`,
  direction: v > 0.05 ? 'up' : v < -0.05 ? 'down' : 'flat',
  good: Math.abs(v) < 0.05 ? null : v > 0 === goodWhenUp,
  vs: `vs ${comparisonLabel(period)}`,
});

export const effTone = (eff: number, loomType?: string): Tone => {
  const [crit, warn] = loomType === 'Sulzer' ? [77, 82] : loomType === 'Airjet' ? [80, 86] : [82, 88];
  return eff < crit ? 'bad' : eff < warn ? 'warn' : 'ok';
};

export const sevTone = (s: string): Tone => (s === 'HIGH' || s === 'CRITICAL' ? 'bad' : s === 'MEDIUM' || s === 'ATTENTION' ? 'warn' : 'ok');

export const callTone = (c: StyleCall): Tone => (c === 'STOP' ? 'bad' : c === 'REPRICE' ? 'warn' : c === 'PUSH' ? 'ok' : 'neutral');

export const CALL_LABEL: Record<StyleCall, string> = { PUSH: 'Take more orders', HOLD: 'Keep as is', REPRICE: 'Reprice', STOP: 'Stop new orders' };

export const SEV_LABEL: Record<string, string> = { HIGH: 'Urgent', MEDIUM: 'Important', LOW: 'Low' };
