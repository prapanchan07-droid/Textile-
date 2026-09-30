import React from 'react';
import { createBrowserRouter, Link, useRouteError } from 'react-router-dom';
import { AppShell } from '../layout/AppShell';
import { Button, Card, EmptyState } from '../design/ui';
import { ControlTowerPage } from '../features/control-tower/ControlTowerPage';
import { ActionCenterPage } from '../features/actions/ActionCenterPage';
import { ProductionPage } from '../features/production/ProductionPage';
import { FleetPage } from '../features/assets/FleetPage';
import { BenchmarkPage } from '../features/assets/BenchmarkPage';
import { QualityPage } from '../features/quality/QualityPage';
import { WorkforcePage } from '../features/workforce/WorkforcePage';
import { CommercialPage } from '../features/commercial/CommercialPage';
import { DataImportsPage } from '../features/data/DataImportsPage';
import { SystemStatusPage } from '../features/admin/SystemStatusPage';

const NotFound: React.FC = () => (
  <Card>
    <EmptyState
      title="Page not found"
      description="This address doesn't match any page."
      action={
        <Link to="/">
          <Button>Go to Control Tower</Button>
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

export const router = createBrowserRouter([
  {
    element: <AppShell />,
    children: [
      {
        errorElement: <PageError />,
        children: [
          { path: '/', element: <ControlTowerPage /> },
          { path: '/actions', element: <ActionCenterPage /> },
          { path: '/production', element: <ProductionPage /> },
          { path: '/assets', element: <FleetPage /> },
          { path: '/assets/benchmark', element: <BenchmarkPage /> },
          { path: '/quality', element: <QualityPage /> },
          { path: '/workforce', element: <WorkforcePage /> },
          { path: '/commercial', element: <CommercialPage /> },
          { path: '/data', element: <DataImportsPage /> },
          { path: '/admin/system', element: <SystemStatusPage /> },
          { path: '*', element: <NotFound /> },
        ],
      },
    ],
  },
]);
