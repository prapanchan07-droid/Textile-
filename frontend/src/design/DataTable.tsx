import React, { useMemo, useState } from 'react';
import { ArrowDown, ArrowUp, ChevronsUpDown, Download, Search } from 'lucide-react';
import { cn } from '../lib/format';
import { Button, EmptyState } from './ui';

/** Single-line text that truncates with the full value on hover. */
export const Clip: React.FC<{ text: string; className?: string }> = ({ text, className }) => (
  <span title={text} className={cn('block max-w-[16rem] truncate text-ink-2', className)}>
    {text}
  </span>
);

export interface Column<T> {
  key: string;
  header: string;
  render: (row: T) => React.ReactNode;
  /** Value used for sorting and CSV export. Omit to make the column unsortable. */
  value?: (row: T) => string | number | null | undefined;
  align?: 'left' | 'right' | 'center';
  className?: string;
  /** Hide below this breakpoint to keep tables readable on tablets. */
  hideBelow?: 'sm' | 'md' | 'lg' | 'xl';
  /** Allow text to wrap (descriptions). Numbers and ids never wrap. */
  wrap?: boolean;
}

interface DataTableProps<T> {
  rows: T[];
  columns: Column<T>[];
  rowKey: (row: T) => string;
  onRowClick?: (row: T) => void;
  selectedKey?: string | null;
  searchable?: (row: T) => string;
  searchPlaceholder?: string;
  exportName?: string;
  initialSort?: { key: string; dir: 'asc' | 'desc' };
  toolbar?: React.ReactNode;
  emptyTitle?: string;
  emptyDescription?: React.ReactNode;
  dense?: boolean;
}

const hideClass = { sm: 'hidden sm:table-cell', md: 'hidden md:table-cell', lg: 'hidden lg:table-cell', xl: 'hidden xl:table-cell' };

const csvCell = (v: unknown) => {
  const s = v == null ? '' : String(v);
  return /[",\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
};

export function DataTable<T>({
  rows,
  columns,
  rowKey,
  onRowClick,
  selectedKey,
  searchable,
  searchPlaceholder = 'Search…',
  exportName,
  initialSort,
  toolbar,
  emptyTitle = 'No records',
  emptyDescription,
  dense,
}: DataTableProps<T>) {
  const [query, setQuery] = useState('');
  const [sort, setSort] = useState(initialSort ?? null);

  const visible = useMemo(() => {
    let out = rows;
    if (searchable && query.trim()) {
      const q = query.trim().toLowerCase();
      out = out.filter((r) => searchable(r).toLowerCase().includes(q));
    }
    if (sort) {
      const col = columns.find((c) => c.key === sort.key);
      if (col?.value) {
        const get = col.value;
        out = [...out].sort((a, b) => {
          const av = get(a);
          const bv = get(b);
          if (av == null) return 1;
          if (bv == null) return -1;
          const cmp = typeof av === 'number' && typeof bv === 'number' ? av - bv : String(av).localeCompare(String(bv));
          return sort.dir === 'asc' ? cmp : -cmp;
        });
      }
    }
    return out;
  }, [rows, query, sort, columns, searchable]);

  const exportCsv = () => {
    const cols = columns.filter((c) => c.value);
    const lines = [cols.map((c) => csvCell(c.header)).join(',')];
    visible.forEach((r) => lines.push(cols.map((c) => csvCell(c.value!(r))).join(',')));
    const blob = new Blob([lines.join('\n')], { type: 'text/csv;charset=utf-8' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = `${exportName}-${new Date().toISOString().slice(0, 10)}.csv`;
    a.click();
    URL.revokeObjectURL(a.href);
  };

  const toggleSort = (key: string) =>
    setSort((s) => (s?.key !== key ? { key, dir: 'desc' } : s.dir === 'desc' ? { key, dir: 'asc' } : null));

  const hasToolbar = searchable || exportName || toolbar;

  return (
    <div>
      {hasToolbar && (
        <div className="flex flex-wrap items-center gap-2 px-4 pb-3">
          {searchable && (
            <div className="relative">
              <Search className="pointer-events-none absolute left-2 top-1/2 size-3.5 -translate-y-1/2 text-ink-3" />
              <input
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder={searchPlaceholder}
                aria-label={searchPlaceholder}
                className="h-7 w-52 rounded-md border border-line bg-surface pl-7 pr-2 text-xs text-ink placeholder:text-ink-3 hover:border-line-strong"
              />
            </div>
          )}
          {toolbar}
          <div className="flex-1" />
          {exportName && (
            <Button size="sm" variant="ghost" onClick={exportCsv} icon={<Download className="size-3.5" />}>
              Export CSV
            </Button>
          )}
        </div>
      )}
      <div className="overflow-x-auto">
        <table className="w-full border-collapse text-sm">
          <thead>
            <tr className="border-y border-line bg-subtle text-left">
              {columns.map((c) => {
                const active = sort?.key === c.key;
                return (
                  <th
                    key={c.key}
                    scope="col"
                    aria-sort={active ? (sort!.dir === 'asc' ? 'ascending' : 'descending') : undefined}
                    className={cn(
                      'h-8 whitespace-nowrap px-4 text-2xs font-medium uppercase tracking-wide text-ink-3',
                      c.align === 'right' && 'text-right',
                      c.align === 'center' && 'text-center',
                      c.hideBelow && hideClass[c.hideBelow],
                    )}
                  >
                    {c.value ? (
                      <button
                        onClick={() => toggleSort(c.key)}
                        className={cn('inline-flex items-center gap-1 hover:text-ink', active && 'text-ink')}
                      >
                        {c.header}
                        {active ? (
                          sort!.dir === 'asc' ? (
                            <ArrowUp className="size-3" />
                          ) : (
                            <ArrowDown className="size-3" />
                          )
                        ) : (
                          <ChevronsUpDown className="size-3 opacity-40" />
                        )}
                      </button>
                    ) : (
                      c.header
                    )}
                  </th>
                );
              })}
            </tr>
          </thead>
          <tbody>
            {visible.map((r) => {
              const k = rowKey(r);
              return (
                <tr
                  key={k}
                  onClick={onRowClick ? () => onRowClick(r) : undefined}
                  onKeyDown={onRowClick ? (e) => e.key === 'Enter' && onRowClick(r) : undefined}
                  tabIndex={onRowClick ? 0 : undefined}
                  className={cn(
                    'border-b border-line last:border-b-0',
                    onRowClick && 'cursor-pointer hover:bg-subtle',
                    selectedKey === k && 'bg-accent-soft hover:bg-accent-soft',
                  )}
                >
                  {columns.map((c) => (
                    <td
                      key={c.key}
                      className={cn(
                        'px-4 align-middle text-ink',
                        c.wrap ? 'min-w-48 py-2' : 'whitespace-nowrap',
                        dense ? 'h-9' : 'h-11',
                        c.align === 'right' && 'num text-right',
                        c.align === 'center' && 'text-center',
                        c.hideBelow && hideClass[c.hideBelow],
                        c.className,
                      )}
                    >
                      {c.render(r)}
                    </td>
                  ))}
                </tr>
              );
            })}
          </tbody>
        </table>
        {visible.length === 0 && (
          <EmptyState title={query ? 'No matches' : emptyTitle} description={query ? `Nothing matches “${query}”.` : emptyDescription} />
        )}
      </div>
    </div>
  );
}
