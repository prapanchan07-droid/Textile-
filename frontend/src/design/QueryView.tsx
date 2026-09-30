import React from 'react';
import type { UseQueryResult } from '@tanstack/react-query';
import { cn } from '../lib/format';
import { ErrorState, PageSkeleton } from './ui';

/**
 * Standard loading / error / data handling for a page-level query.
 * While a new period loads, the previous data stays on screen, dimmed,
 * instead of flashing a spinner.
 */
export function QueryView<T>({
  query,
  children,
  skeleton = <PageSkeleton />,
}: {
  query: UseQueryResult<T>;
  children: (data: T) => React.ReactNode;
  skeleton?: React.ReactNode;
}) {
  if (query.isPending) return <>{skeleton}</>;
  if (query.isError && !query.data) return <ErrorState error={query.error} onRetry={() => query.refetch()} />;
  if (!query.data) return null;
  return (
    <div className={cn('transition-opacity', query.isPlaceholderData && 'pointer-events-none opacity-60')} aria-busy={query.isFetching}>
      {children(query.data)}
    </div>
  );
}
