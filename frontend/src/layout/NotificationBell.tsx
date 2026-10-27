import React, { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Bell } from 'lucide-react';
import { useQueryClient } from '@tanstack/react-query';
import { api, mk, useNotifications } from '../api/mill';
import { cn, relativeTime } from '../lib/format';

/** In-app notifications (the only configured channel). The dot shows only when something is unread. */
export const NotificationBell: React.FC = () => {
  const q = useNotifications();
  const qc = useQueryClient();
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);
  const box = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (!open) return;
    const close = (e: MouseEvent) => box.current && !box.current.contains(e.target as Node) && setOpen(false);
    window.addEventListener('mousedown', close);
    return () => window.removeEventListener('mousedown', close);
  }, [open]);
  const unread = q.data?.unread ?? 0;
  const markAll = async () => {
    await api.post('/mill/notifications/read', null);
    qc.invalidateQueries({ queryKey: mk.view('notifications') });
  };
  return (
    <div className="relative" ref={box}>
      <button onClick={() => setOpen((o) => !o)} className="relative rounded-lg p-2 text-ink-2 transition-colors hover:bg-muted hover:text-ink"
        aria-label={unread ? `${unread} unread notifications` : 'Notifications'}>
        <Bell className="size-4" />
        {unread > 0 && <span className="absolute right-1 top-1 min-w-4 rounded-full bg-bad px-1 text-[10px] font-semibold leading-4 text-white">{unread > 99 ? '99+' : unread}</span>}
      </button>
      {open && (
        <div className="absolute right-0 z-50 mt-2 w-80 overflow-hidden rounded-xl border border-line bg-surface shadow-pop">
          <div className="flex items-center justify-between border-b border-line px-3 py-2">
            <span className="text-sm font-semibold text-ink">Notifications</span>
            {unread > 0 && <button className="text-xs text-accent hover:underline" onClick={markAll}>Mark all read</button>}
          </div>
          <ul className="max-h-96 overflow-y-auto">
            {(q.data?.items ?? []).length === 0 && <li className="px-3 py-6 text-center text-xs text-ink-3">Nothing yet.</li>}
            {(q.data?.items ?? []).map((n) => (
              <li key={n.id}>
                <button className={cn('block w-full px-3 py-2 text-left hover:bg-subtle', !n.read_at && 'bg-accent-soft/40')}
                  onClick={async () => {
                    setOpen(false);
                    if (!n.read_at) {
                      await api.post('/mill/notifications/read', [n.id]);
                      qc.invalidateQueries({ queryKey: mk.view('notifications') });
                    }
                    if (n.link) navigate(n.link);
                  }}>
                  <span className={cn('block text-sm', n.severity === 'CRITICAL' ? 'text-bad' : 'text-ink')}>{n.title}</span>
                  {n.body && <span className="block truncate text-xs text-ink-3">{n.body}</span>}
                  <span className="text-2xs text-ink-3">{relativeTime(n.created_at)}</span>
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};
