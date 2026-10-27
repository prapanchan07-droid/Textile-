import React from 'react';
import { NavLink, useSearchParams } from 'react-router-dom';
import { ChevronsLeft, ChevronsRight, CircleDot, X } from 'lucide-react';
import { cn } from '../lib/format';
import { useAuth } from '../auth/AuthContext';
import { buildNav } from './nav';
import { useMeta } from '../api/mill';
import { AshokLogo } from './AshokLogo';

export const Sidebar: React.FC<{
  collapsed: boolean;
  onToggleCollapsed: () => void;
  mobileOpen: boolean;
  onCloseMobile: () => void;
}> = ({ collapsed, onToggleCollapsed, mobileOpen, onCloseMobile }) => {
  const { user } = useAuth();
  const nav = React.useMemo(() => buildNav(user), [user]);
  const meta = useMeta();
  const last = meta.data?.data_range.last;
  const [params] = useSearchParams();
  // Carry the reporting period across pages; drop page-specific params.
  const period = params.get('period');
  const search = period ? `?period=${period}` : '';

  const body = (isMobile: boolean) => {
    const narrow = collapsed && !isMobile;
    return (
      <div className="flex h-full flex-col border-t-[3px] border-[#5a3828] bg-sidebar text-sidebar-ink">
        <div className={cn('flex h-[66px] shrink-0 items-center gap-2.5 border-b border-line px-4', narrow && 'justify-center px-0')}>
          <AshokLogo compact={narrow} />
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

        <nav className="flex-1 space-y-6 overflow-y-auto px-3 py-5" aria-label="Main">
          {nav.map((group) => (
            <div key={group.label}>
              {!narrow ? (
                <div className="mb-2 px-2 text-2xs font-semibold uppercase tracking-[0.14em] text-sidebar-ink-2/70">{group.label}</div>
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
                          'flex h-9 items-center gap-2.5 rounded-lg px-2.5 text-sm transition-all',
                          narrow && 'justify-center px-0',
                          isActive
                            ? 'bg-sidebar-active font-semibold text-white shadow-sm'
                            : 'text-sidebar-ink-2 hover:bg-sidebar-hover hover:text-sidebar-ink',
                        )
                      }
                    >
                      {({ isActive }) => (
                        <>
                          <item.icon className={cn('size-4 shrink-0', isActive && 'text-white')} />
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
          <div className={cn('m-3 rounded-xl border border-line bg-subtle p-2.5', narrow && 'border-0 bg-transparent p-0')}>
            {!narrow && <div className="mb-2 flex items-center gap-1.5 text-2xs text-sidebar-ink-2"><CircleDot className="size-3 text-ink-3" /> {last ? `Imported data to ${last}` : 'No data imported yet'}</div>}
            <button
              onClick={onToggleCollapsed}
              className={cn('flex h-7 w-full items-center gap-2 rounded-md px-1 text-xs text-sidebar-ink-2 hover:bg-sidebar-hover hover:text-sidebar-ink', narrow && 'justify-center')}
              aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
            >
              {collapsed ? <ChevronsRight className="size-4" /> : <ChevronsLeft className="size-4" />}
              {!narrow && 'Collapse sidebar'}
            </button>
          </div>
        )}
      </div>
    );
  };

  return (
    <>
      <aside className={cn('hidden shrink-0 transition-[width] duration-150 lg:block', collapsed ? 'w-[60px]' : 'w-64')}>
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
