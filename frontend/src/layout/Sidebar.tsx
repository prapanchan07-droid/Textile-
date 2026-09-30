import React from 'react';
import { NavLink, useSearchParams } from 'react-router-dom';
import { ChevronsLeft, ChevronsRight, X } from 'lucide-react';
import { cn } from '../lib/format';
import { NAV } from './nav';

export const Sidebar: React.FC<{
  collapsed: boolean;
  onToggleCollapsed: () => void;
  mobileOpen: boolean;
  onCloseMobile: () => void;
}> = ({ collapsed, onToggleCollapsed, mobileOpen, onCloseMobile }) => {
  const [params] = useSearchParams();
  // Carry the reporting period across pages; drop page-specific params.
  const period = params.get('period');
  const search = period ? `?period=${period}` : '';

  const body = (isMobile: boolean) => {
    const narrow = collapsed && !isMobile;
    return (
      <div className="flex h-full flex-col bg-sidebar text-sidebar-ink">
        <div className={cn('flex h-14 shrink-0 items-center gap-2.5 px-4', narrow && 'justify-center px-0')}>
          <div className="flex size-7 shrink-0 items-center justify-center rounded-md bg-accent text-xs font-bold text-white">AT</div>
          {!narrow && (
            <div className="min-w-0 leading-tight">
              <div className="truncate text-sm font-semibold">Ashok Textiles</div>
              <div className="truncate text-2xs text-sidebar-ink-2">Operations Platform</div>
            </div>
          )}
          {isMobile && (
            <button
              onClick={onCloseMobile}
              className="ml-auto rounded p-1 text-sidebar-ink-2 hover:text-sidebar-ink"
              aria-label="Close menu"
            >
              <X className="size-4" />
            </button>
          )}
        </div>

        <nav className="flex-1 space-y-5 overflow-y-auto px-2.5 py-3" aria-label="Main">
          {NAV.map((group) => (
            <div key={group.label}>
              {!narrow ? (
                <div className="mb-1 px-2 text-2xs font-medium uppercase tracking-wider text-sidebar-ink-2/80">{group.label}</div>
              ) : (
                <div className="mx-auto mb-2 h-px w-6 bg-sidebar-hover" />
              )}
              <ul className="space-y-0.5">
                {group.items.map((item) => (
                  <li key={item.to}>
                    <NavLink
                      to={{ pathname: item.to, search }}
                      end={item.to === '/'}
                      onClick={isMobile ? onCloseMobile : undefined}
                      title={narrow ? item.label : undefined}
                      className={({ isActive }) =>
                        cn(
                          'flex h-8 items-center gap-2.5 rounded-md px-2 text-sm transition-colors',
                          narrow && 'justify-center px-0',
                          isActive
                            ? 'bg-sidebar-active font-medium text-sidebar-ink'
                            : 'text-sidebar-ink-2 hover:bg-sidebar-hover hover:text-sidebar-ink',
                        )
                      }
                    >
                      {({ isActive }) => (
                        <>
                          <item.icon className={cn('size-4 shrink-0', isActive && 'text-[rgb(var(--accent))]')} />
                          {!narrow && <span className="truncate">{item.label}</span>}
                        </>
                      )}
                    </NavLink>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </nav>

        {!isMobile && (
          <button
            onClick={onToggleCollapsed}
            className={cn(
              'm-2.5 flex h-8 items-center gap-2 rounded-md px-2 text-xs text-sidebar-ink-2 hover:bg-sidebar-hover hover:text-sidebar-ink',
              narrow && 'justify-center',
            )}
            aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          >
            {collapsed ? <ChevronsRight className="size-4" /> : <ChevronsLeft className="size-4" />}
            {!narrow && 'Collapse'}
          </button>
        )}
      </div>
    );
  };

  return (
    <>
      <aside className={cn('hidden shrink-0 transition-[width] duration-150 lg:block', collapsed ? 'w-[60px]' : 'w-60')}>
        {body(false)}
      </aside>
      {mobileOpen && (
        <div className="fixed inset-0 z-50 lg:hidden">
          <div className="absolute inset-0 animate-fade-in bg-black/40" onClick={onCloseMobile} />
          <aside className="relative h-full w-64 animate-slide-in">{body(true)}</aside>
        </div>
      )}
    </>
  );
};
