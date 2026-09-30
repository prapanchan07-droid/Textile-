import React, { useEffect, useMemo, useRef, useState } from 'react';
import { createPortal } from 'react-dom';
import { useNavigate } from 'react-router-dom';
import { Cpu, CornerDownLeft, FileSpreadsheet, Moon, Search, Sun, UploadCloud } from 'lucide-react';
import { cn } from '../lib/format';
import { useMachines } from '../api/queries';
import { useTheme } from '../app/state';
import { ALL_NAV } from './nav';

interface Command {
  id: string;
  group: string;
  label: string;
  hint?: string;
  keywords?: string;
  icon: React.ReactNode;
  run: () => void;
}

/** ⌘K / Ctrl+K: jump to any page or machine, or run a common action. */
export const CommandPalette: React.FC<{ open: boolean; onClose: () => void }> = ({ open, onClose }) => {
  const navigate = useNavigate();
  const [, setTheme, resolved] = useTheme();
  const [query, setQuery] = useState('');
  const [active, setActive] = useState(0);
  const input = useRef<HTMLInputElement>(null);
  // Month-to-date is the widest window, so it lists every machine in the master.
  const machines = useMachines('THIS_MONTH');

  useEffect(() => {
    if (open) {
      setQuery('');
      setActive(0);
      requestAnimationFrame(() => input.current?.focus());
    }
  }, [open]);

  const commands = useMemo<Command[]>(() => {
    const go = (path: string) => () => navigate(path);
    return [
      ...ALL_NAV.map((n) => ({
        id: `nav:${n.to}`,
        group: 'Pages',
        label: n.label,
        keywords: n.keywords,
        icon: <n.icon className="size-4" />,
        run: go(n.to),
      })),
      ...(machines.data?.all_machines ?? []).map((m) => ({
        id: `m:${m.machine_id}`,
        group: 'Machines',
        label: m.machine_id,
        hint: m.machine_type,
        keywords: m.machine_type,
        icon: <Cpu className="size-4" />,
        run: go(`/assets?machine=${encodeURIComponent(m.machine_id)}`),
      })),
      {
        id: 'act:import',
        group: 'Actions',
        label: 'Import factory reports',
        keywords: 'upload excel csv',
        icon: <UploadCloud className="size-4" />,
        run: go('/data'),
      },
      {
        id: 'act:template',
        group: 'Actions',
        label: 'Get the data template',
        keywords: 'download xlsx',
        icon: <FileSpreadsheet className="size-4" />,
        run: go('/data#template'),
      },
      {
        id: 'act:theme',
        group: 'Actions',
        label: resolved === 'dark' ? 'Switch to light theme' : 'Switch to dark theme',
        keywords: 'dark light mode appearance',
        icon: resolved === 'dark' ? <Sun className="size-4" /> : <Moon className="size-4" />,
        run: () => setTheme(resolved === 'dark' ? 'light' : 'dark'),
      },
    ];
  }, [machines.data, navigate, resolved, setTheme]);

  const results = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return commands;
    return commands.filter((c) => `${c.label} ${c.hint ?? ''} ${c.keywords ?? ''}`.toLowerCase().includes(q));
  }, [commands, query]);

  useEffect(() => setActive(0), [query]);

  if (!open) return null;

  const runAt = (i: number) => {
    const c = results[i];
    if (!c) return;
    onClose();
    c.run();
  };

  const onKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setActive((a) => Math.min(results.length - 1, a + 1));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setActive((a) => Math.max(0, a - 1));
    } else if (e.key === 'Enter') {
      e.preventDefault();
      runAt(active);
    } else if (e.key === 'Escape') {
      onClose();
    }
  };

  let lastGroup = '';
  return createPortal(
    <div className="fixed inset-0 z-[60] flex items-start justify-center px-4 pt-[12vh]">
      <div className="absolute inset-0 animate-fade-in bg-black/40" onClick={onClose} />
      <div
        role="dialog"
        aria-modal="true"
        aria-label="Command palette"
        className="relative w-full max-w-lg overflow-hidden rounded-xl border border-line bg-surface shadow-pop"
        onKeyDown={onKeyDown}
      >
        <div className="flex items-center gap-2 border-b border-line px-3.5">
          <Search className="size-4 text-ink-3" />
          <input
            ref={input}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search pages, machines, actions…"
            className="h-11 flex-1 bg-transparent text-sm text-ink placeholder:text-ink-3 focus-visible:ring-0 focus-visible:ring-offset-0"
            role="combobox"
            aria-expanded="true"
            aria-controls="cmdk-list"
            aria-activedescendant={results[active] ? `cmdk-${results[active].id}` : undefined}
          />
          <kbd className="rounded border border-line px-1.5 text-2xs text-ink-3">Esc</kbd>
        </div>
        <ul id="cmdk-list" role="listbox" className="max-h-80 overflow-y-auto p-1.5">
          {results.length === 0 && <li className="px-3 py-6 text-center text-xs text-ink-3">No results for “{query}”</li>}
          {results.map((c, i) => {
            const header = c.group !== lastGroup ? c.group : null;
            lastGroup = c.group;
            return (
              <React.Fragment key={c.id}>
                {header && <li className="px-2.5 pb-1 pt-2 text-2xs font-medium uppercase tracking-wide text-ink-3">{header}</li>}
                <li
                  id={`cmdk-${c.id}`}
                  role="option"
                  aria-selected={i === active}
                  onMouseMove={() => setActive(i)}
                  onClick={() => runAt(i)}
                  className={cn(
                    'flex h-9 cursor-pointer items-center gap-2.5 rounded-md px-2.5 text-sm',
                    i === active ? 'bg-muted text-ink' : 'text-ink-2',
                  )}
                >
                  <span className="text-ink-3">{c.icon}</span>
                  <span className="flex-1 truncate">{c.label}</span>
                  {c.hint && <span className="text-xs text-ink-3">{c.hint}</span>}
                  {i === active && <CornerDownLeft className="size-3.5 text-ink-3" />}
                </li>
              </React.Fragment>
            );
          })}
        </ul>
      </div>
    </div>,
    document.body,
  );
};
