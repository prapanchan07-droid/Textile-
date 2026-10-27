import React from 'react';
import { createBrowserRouter, Link, useRouteError } from 'react-router-dom';
import { AppShell } from '../layout/AppShell';
import { Button, Card, EmptyState } from '../design/ui';
import { LoginPage } from '../auth/LoginPage';
import { RequireAuth } from '../auth/guards';
import { CommandCenterPage } from '../features/command/CommandCenterPage';
import { LoomsPage } from '../features/looms/LoomsPage';
import { LoomDetailPage } from '../features/looms/LoomDetailPage';
import { ProductionPage } from '../features/production/ProductionPage';
import { ComparePage } from '../features/compare/ComparePage';
import { EnergyPage } from '../features/energy/EnergyPage';
import { AlertsPage } from '../features/alerts/AlertsPage';
import { TasksPage } from '../features/tasks/TasksPage';
import { GroupsPage } from '../features/groups/GroupsPage';
import { MaintenancePage } from '../features/maintenance/MaintenancePage';
import { ReportsPage } from '../features/reports/ReportsPage';
import { ReportPage } from '../features/reports/ReportPage';
import { ImportsPage } from '../features/imports/ImportsPage';
import { ConnectivityPage } from '../features/connectivity/ConnectivityPage';
import { SettingsPage } from '../features/settings/SettingsPage';

const NotFound: React.FC = () => (
  <Card>
    <EmptyState
      title="Page not found"
      description="This address doesn't match any page."
      action={
        <Link to="/">
          <Button>Go home</Button>
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
              { path: '/', element: <CommandCenterPage /> },
              { path: '/looms', element: <LoomsPage /> },
              { path: '/looms/:id', element: <LoomDetailPage /> },
              { path: '/production', element: <ProductionPage /> },
              { path: '/compare', element: <ComparePage /> },
              { path: '/energy', element: <EnergyPage /> },
              { path: '/alerts', element: <AlertsPage /> },
              { path: '/tasks', element: <TasksPage /> },
              { path: '/groups', element: <GroupsPage /> },
              { path: '/maintenance', element: <MaintenancePage /> },
              { path: '/reports', element: <ReportsPage /> },
              { path: '/reports/:id', element: <ReportPage /> },
              { path: '/imports', element: <ImportsPage /> },
              { path: '/connectivity', element: <ConnectivityPage /> },
              { path: '/settings', element: <SettingsPage /> },
              { path: '*', element: <NotFound /> },
            ],
          },
        ],
      },
    ],
  },
]);
