import React from 'react';
import { Link, Navigate, Outlet, useLocation } from 'react-router-dom';
import { ShieldAlert } from 'lucide-react';
import { Button, Card, EmptyState } from '../design/ui';
import { landingPath } from '../features/weaving/sections';
import type { WeavingSection } from '../types/auth';
import { useAuth } from './AuthContext';

/** Sends signed-out visitors to the login page and brings them back to where they were headed. */
export const RequireAuth: React.FC = () => {
  const { user, loading } = useAuth();
  const location = useLocation();
  if (loading) return <div className="grid h-full place-items-center text-sm text-ink-3">Restoring your session…</div>;
  if (!user) return <Navigate to="/login" replace state={{ from: location.pathname + location.search }} />;
  return <Outlet />;
};

/** Blocks a weaving page the user's role has no access to. */
export const RequireSection: React.FC<{ section: WeavingSection; children: React.ReactNode }> = ({ section, children }) => {
  const { user } = useAuth();
  if (user && user.sections.includes(section)) return <>{children}</>;
  return (
    <Card>
      <EmptyState
        icon={<ShieldAlert className="size-5" />}
        title="This page isn't part of your role"
        description={`You are signed in as ${user?.role_label ?? 'a guest'}. Ask your administrator if you need access.`}
        action={
          user ? (
            <Link to={landingPath(user)}>
              <Button>Go to my home page</Button>
            </Link>
          ) : undefined
        }
      />
    </Card>
  );
};

/** `/` goes to the signed-in user's own landing page. */
export const HomeRedirect: React.FC = () => {
  const { user } = useAuth();
  return <Navigate to={user ? landingPath(user) : '/login'} replace />;
};
