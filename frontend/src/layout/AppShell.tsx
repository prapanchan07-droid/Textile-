import React, { useEffect, useState } from 'react';
import { Outlet, useLocation, useNavigate } from 'react-router-dom';
import { LogOut, Menu, Monitor, Moon, Sun } from 'lucide-react';
import { cn } from '../lib/format';
import { useHealth } from '../api/queries';
import { useTheme, type ThemePref } from '../app/state';
import { Sidebar } from './Sidebar';
import { useAuth } from '../auth/AuthContext';
import { buildNav, findNav } from './nav';
import { NotificationBell } from './NotificationBell';

const readCollapsed = () => {
  try {
    return localStorage.getItem('sidebar') === 'collapsed';
  } catch {
    return false;
  }
};

export const AppShell: React.FC = () => {
  const [collapsed, setCollapsed] = useState(readCollapsed);
  const [mobileOpen, setMobileOpen] = useState(false);
  const location = useLocation();

  // Each page owns its scroll position; start new pages at the top.
  useEffect(() => {
    document.getElementById('main-scroll')?.scrollTo({ top: 0 });
  }, [location.pathname]);

  const toggleCollapsed = () =>
    setCollapsed((c) => {
      try {
        localStorage.setItem('sidebar', c ? 'expanded' : 'collapsed');
      } catch {
        /* ignore */
      }
      return !c;
    });

  return (
    <div className="flex h-full overflow-hidden bg-canvas">
      <a
        href="#main"
        className="sr-only focus:not-sr-only focus:absolute focus:z-[70] focus:m-2 focus:rounded focus:bg-surface focus:px-3 focus:py-2"
      >
        Skip to content
      </a>
      <Sidebar
        collapsed={collapsed}
        onToggleCollapsed={toggleCollapsed}
        mobileOpen={mobileOpen}
        onCloseMobile={() => setMobileOpen(false)}
      />
      <div className="flex min-w-0 flex-1 flex-col">
        <Topbar onOpenMenu={() => setMobileOpen(true)} />
        <div id="main-scroll" className="flex-1 overflow-y-auto">
          <main id="main" className="mx-auto w-full max-w-[1500px] px-4 pb-12 pt-6 sm:px-7 lg:px-9">
            <div className="page-enter"><Outlet /></div>
          </main>
        </div>
      </div>
    </div>
  );
};

const Topbar: React.FC<{ onOpenMenu: () => void }> = ({ onOpenMenu }) => {
  const health = useHealth();
  const { user } = useAuth();
  const online = health.isSuccess && health.data.status === 'healthy';
  const activePage = findNav(buildNav(user), location.pathname);

  return (
    <header className="flex h-[66px] shrink-0 items-center gap-3 border-b border-line/80 border-t-[3px] border-t-[#5a3828] bg-surface/95 px-4 backdrop-blur sm:px-7">
      <button onClick={onOpenMenu} className="rounded-md p-1.5 text-ink-2 hover:bg-muted lg:hidden" aria-label="Open menu">
        <Menu className="size-5" />
      </button>

      <div className="hidden min-w-0 flex-1 items-center gap-2 lg:flex">
        <span className="h-5 w-px bg-line" />
        <span className="truncate text-sm font-medium text-ink">{activePage?.label ?? 'Textile'}</span>
      </div>

      <div
        className="hidden items-center gap-2 whitespace-nowrap rounded-lg px-2.5 py-1.5 text-xs text-ink-3 hover:bg-muted md:flex"
        title={online ? 'API connected' : 'API unreachable'}
      >
        <span className={cn('size-2 rounded-full', health.isLoading ? 'bg-ink-3' : online ? 'bg-ok' : 'bg-bad')} />
        <span className="hidden lg:inline">{health.isLoading ? 'Connecting…' : online ? 'Connected' : 'API offline'}</span>
      </div>

      <ThemeToggle />

      <NotificationBell />

      <UserMenu />
    </header>
  );
};

const UserMenu: React.FC = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  if (!user) return null;
  const initials = user.full_name
    .split(' ')
    .map((w) => w[0])
    .slice(0, 2)
    .join('')
    .toUpperCase();
  return (
    <div className="flex items-center gap-2.5 border-l border-line pl-3">
      <div className="hidden text-right leading-tight md:block">
        <div className="text-sm font-medium text-ink">{user.full_name}</div>
        <div className="text-2xs text-ink-3">{user.role_label}</div>
      </div>
      <span className="grid size-8 place-items-center rounded-full bg-accent-soft text-xs font-semibold text-accent" aria-hidden>
        {initials}
      </span>
      <button
        onClick={() => {
          logout();
          navigate('/login', { replace: true });
        }}
        className="rounded-lg p-2 text-ink-2 transition-colors hover:bg-muted hover:text-ink"
        aria-label="Sign out"
        title="Sign out"
      >
        <LogOut className="size-4" />
      </button>
    </div>
  );
};

const ThemeToggle: React.FC = () => {
  const [pref, setTheme] = useTheme();
  const order: ThemePref[] = ['system', 'light', 'dark'];
  const next = order[(order.indexOf(pref) + 1) % order.length];
  const Icon = pref === 'dark' ? Moon : pref === 'light' ? Sun : Monitor;
  return (
    <button
      onClick={() => setTheme(next)}
      className="rounded-lg p-2 text-ink-2 transition-colors hover:bg-muted hover:text-ink"
      aria-label={`Theme: ${pref}. Switch to ${next}`}
      title={`Theme: ${pref}`}
    >
      <Icon className="size-4" />
    </button>
  );
};
