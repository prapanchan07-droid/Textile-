import React from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { PageHeader } from '../../layout/PageHeader';
import { Tabs } from '../../design/ui';

type Tab = '/assets' | '/assets/benchmark';

/** Shared header for the machine views; the tab is part of the URL. */
export const AssetsHeader: React.FC<{ actions?: React.ReactNode }> = ({ actions }) => {
  const { pathname, search } = useLocation();
  const navigate = useNavigate();
  const period = new URLSearchParams(search).get('period');
  const tab: Tab = pathname.startsWith('/assets/benchmark') ? '/assets/benchmark' : '/assets';
  return (
    <PageHeader
      title="Machines & Downtime"
      description="Efficiency, losses and stoppages for every machine"
      showPeriod
      actions={actions}
      tabs={
        <Tabs<Tab>
          value={tab}
          onChange={(t) => navigate({ pathname: t, search: period ? `?period=${period}` : '' })}
          tabs={[
            { value: '/assets', label: 'Fleet' },
            { value: '/assets/benchmark', label: 'Benchmark' },
          ]}
        />
      }
    />
  );
};
