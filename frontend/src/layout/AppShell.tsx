import React, { useEffect, useState } from 'react';
import { Link, Outlet, useLocation } from 'react-router-dom';
import { Menu, Monitor, Moon, Search, Sun, UploadCloud } from 'lucide-react';
import { cn, relativeTime } from '../lib/format';
import { useHealth, useImportHistory } from '../api/queries';
import { useTheme, type ThemePref } from '../app/state';
import { Button } from '../design/ui';
import { Sidebar } from './Sidebar';
import { CommandPalette } from './CommandPalette';

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
  const [paletteOpen, setPaletteOpen] = useState(false);
  const location = useLocation();

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        setPaletteOpen((o) => !o);
      }
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, []);

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
    <div className="flex h-full overflow-hidden">
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
        <Topbar onOpenMenu={() => setMobileOpen(true)} onOpenPalette={() => setPaletteOpen(true)} />
        <div id="main-scroll" className="flex-1 overflow-y-auto">
          <main id="main" className="mx-auto w-full max-w-[1440px] px-4 pb-12 pt-5 sm:px-6">
            <Outlet />
          </main>
        </div>
      </div>
      <CommandPalette open={paletteOpen} onClose={() => setPaletteOpen(false)} />
    </div>
  );
};

const Topbar: React.FC<{ onOpenMenu: () => void; onOpenPalette: () => void }> = ({ onOpenMenu, onOpenPalette }) => {
  const health = useHealth();
  const history = useImportHistory();
  const lastImport = history.data
    ?.map((h) => h.upload_timestamp)
    .sort()
    .slice(-1)[0];
  const online = health.isSuccess && health.data.status === 'healthy';
  const isMac = typeof navigator !== 'undefined' && /Mac/.test(navigator.platform);

  return (
    <header className="flex h-14 shrink-0 items-center gap-3 border-b border-line bg-surface px-4 sm:px-6">
      <button onClick={onOpenMenu} className="rounded-md p-1.5 text-ink-2 hover:bg-muted lg:hidden" aria-label="Open menu">
        <Menu className="size-5" />
      </button>

      <button
        onClick={onOpenPalette}
        className="flex h-8 w-full max-w-sm items-center gap-2 rounded-md border border-line bg-subtle px-2.5 text-sm text-ink-3 hover:border-line-strong"
      >
        <Search className="size-4" />
        <span className="flex-1 truncate text-left">Search pages, machines…</span>
        <kbd className="hidden rounded border border-line bg-surface px-1.5 text-2xs sm:inline">{isMac ? '⌘' : 'Ctrl'} K</kbd>
      </button>

      <div className="flex-1" />

      <Link
        to="/admin/system"
        className="hidden items-center gap-2 whitespace-nowrap rounded-md px-2 py-1 text-xs text-ink-3 hover:bg-muted md:flex"
        title={online ? 'API connected' : 'API unreachable'}
      >
        <span className={cn('size-2 rounded-full', health.isLoading ? 'bg-ink-3' : online ? 'bg-ok' : 'bg-bad')} />
        <span className="hidden lg:inline">
          {health.isLoading
            ? 'Connecting…'
            : !online
              ? 'API offline'
              : lastImport
                ? `Data imported ${relativeTime(lastImport)}`
                : 'No reports imported yet'}
        </span>
      </Link>

      <ThemeToggle />

      <Link to="/data">
        <Button variant="primary" icon={<UploadCloud className="size-4" />}>
          <span className="hidden sm:inline">Import data</span>
        </Button>
      </Link>
    </header>
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
      className="rounded-md p-1.5 text-ink-2 hover:bg-muted hover:text-ink"
      aria-label={`Theme: ${pref}. Switch to ${next}`}
      title={`Theme: ${pref}`}
    >
      <Icon className="size-4" />
    </button>
  );
};
