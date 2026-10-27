import React from 'react';
import { createBrowserRouter, Link, useRouteError } from 'react-router-dom';
import { AppShell } from '../layout/AppShell';
import { Button, Card, EmptyState } from '../design/ui';
import { LoginPage } from '../auth/LoginPage';
import { RequireAuth } from '../auth/guards';
import { useAuth } from '../auth/AuthContext';

const Home: React.FC = () => {
  const { user } = useAuth();
  return (
    <Card>
      <EmptyState title={`Welcome, ${user?.full_name ?? ''}`} description="No pages yet. Start building from here." />
    </Card>
  );
};

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
              { path: '/', element: <Home /> },
              { path: '*', element: <NotFound /> },
            ],
          },
        ],
      },
    ],
  },
]);
