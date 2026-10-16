import React from 'react';
import { createBrowserRouter, Link, useRouteError } from 'react-router-dom';
import { AppShell } from '../layout/AppShell';
import { Button, Card, EmptyState } from '../design/ui';
import { LoginPage } from '../auth/LoginPage';
import { HomeRedirect, RequireAuth, RequireSection } from '../auth/guards';
import { CommandPage } from '../features/weaving/command/CommandPage';
import { OwnerPage } from '../features/weaving/owner/OwnerPage';
import { ProductionPage } from '../features/weaving/production/ProductionPage';
import { StoppagesPage } from '../features/weaving/stoppages/StoppagesPage';
import { MachinesPage } from '../features/weaving/machines/MachinesPage';
import { MaintenancePage } from '../features/weaving/maintenance/MaintenancePage';
import { WorkforcePage } from '../features/weaving/workforce/WorkforcePage';
import { CockpitPage } from '../features/weaving/cockpit/CockpitPage';
import { HandoverPage } from '../features/weaving/handover/HandoverPage';
import { OrdersPage } from '../features/weaving/orders/OrdersPage';
import { SchedulerPage } from '../features/weaving/scheduler/SchedulerPage';
import { InsightsPage } from '../features/weaving/insights/InsightsPage';
import { ComparePage } from '../features/weaving/compare/ComparePage';
import { QualityPage } from '../features/weaving/quality/QualityPage';
import { ActionsPage } from '../features/weaving/actions/ActionsPage';
import { DataImportsPage } from '../features/data/DataImportsPage';
import { SystemStatusPage } from '../features/admin/SystemStatusPage';

const NotFound: React.FC = () => (
  <Card>
    <EmptyState
      title="Page not found"
      description="This address doesn't match any page."
      action={
        <Link to="/">
          <Button>Go to my home page</Button>
        </Link>
      }
    />
  </Card>
);

/** A crash inside one page shouldn't take down navigation. */
const PageError: React.FC = () => {
  const err = useRouteError();
  return (
    <Card>
      <EmptyState
        title="Something went wrong on this page"
        description={err instanceof Error ? err.message : 'Unexpected error'}
        action={<Button onClick={() => window.location.reload()}>Reload</Button>}
      />
    </Card>
  );
};

const section = (slug: Parameters<typeof RequireSection>[0]['section'], page: React.ReactNode) => (
  <RequireSection section={slug}>{page}</RequireSection>
);

export const router = createBrowserRouter([
  { path: '/login', element: <LoginPage /> },
  {
    element: <RequireAuth />,
    children: [
      {
        element: <AppShell />,
        children: [
          {
            errorElement: <PageError />,
            children: [
              { path: '/', element: <HomeRedirect /> },
              { path: '/weaving', element: <HomeRedirect /> },
              { path: '/weaving/owner', element: section('owner', <OwnerPage />) },
              { path: '/weaving/command', element: section('command', <CommandPage />) },
              { path: '/weaving/cockpit', element: section('cockpit', <CockpitPage />) },
              { path: '/weaving/maintenance', element: section('maintenance', <MaintenancePage />) },
              { path: '/weaving/quality', element: section('quality', <QualityPage />) },
              { path: '/weaving/production', element: section('production', <ProductionPage />) },
              { path: '/weaving/stoppages', element: section('stoppages', <StoppagesPage />) },
              { path: '/weaving/machines', element: section('machines', <MachinesPage />) },
              { path: '/weaving/workforce', element: section('workforce', <WorkforcePage />) },
              { path: '/weaving/handover', element: section('handover', <HandoverPage />) },
              { path: '/weaving/orders', element: section('orders', <OrdersPage />) },
              { path: '/weaving/scheduler', element: section('scheduler', <SchedulerPage />) },
              { path: '/weaving/insights', element: section('insights', <InsightsPage />) },
              { path: '/weaving/compare', element: section('compare', <ComparePage />) },
              { path: '/weaving/actions', element: section('actions', <ActionsPage />) },
              { path: '/data', element: <DataImportsPage /> },
              { path: '/admin/system', element: <SystemStatusPage /> },
              { path: '*', element: <NotFound /> },
            ],
          },
        ],
      },
    ],
  },
]);
