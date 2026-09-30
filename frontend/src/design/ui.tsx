import React from 'react';
import { AlertTriangle, ArrowDownRight, ArrowUpRight, CheckCircle2, Inbox, Loader2, AlertOctagon, RefreshCw } from 'lucide-react';
import { cn } from '../lib/format';

/* ------------------------------------------------------------------ Button */

type ButtonVariant = 'primary' | 'secondary' | 'ghost' | 'danger';
type ButtonSize = 'sm' | 'md';

const buttonVariants: Record<ButtonVariant, string> = {
  primary: 'bg-accent text-white hover:bg-accent/90 border border-transparent',
  secondary: 'bg-surface text-ink border border-line hover:bg-subtle hover:border-line-strong',
  ghost: 'text-ink-2 hover:text-ink hover:bg-muted border border-transparent',
  danger: 'bg-bad text-white hover:bg-bad/90 border border-transparent',
};

export const Button = React.forwardRef<
  HTMLButtonElement,
  React.ButtonHTMLAttributes<HTMLButtonElement> & {
    variant?: ButtonVariant;
    size?: ButtonSize;
    loading?: boolean;
    icon?: React.ReactNode;
  }
>(({ variant = 'secondary', size = 'md', loading, icon, className, children, disabled, ...props }, ref) => (
  <button
    ref={ref}
    disabled={disabled || loading}
    className={cn(
      'inline-flex items-center justify-center gap-1.5 rounded-md font-medium whitespace-nowrap transition-colors disabled:opacity-50 disabled:pointer-events-none',
      size === 'sm' ? 'h-7 px-2.5 text-xs' : 'h-8 px-3 text-sm',
      buttonVariants[variant],
      className,
    )}
    {...props}
  >
    {loading ? <Loader2 className="size-3.5 animate-spin" /> : icon}
    {children}
  </button>
));
Button.displayName = 'Button';

/* ------------------------------------------------------------------ Status */

export type Tone = 'ok' | 'warn' | 'bad' | 'neutral' | 'info';

/** Collapses the backend's many status spellings into four tones. */
export const toneOf = (status?: string | null): Tone => {
  const s = (status ?? '').toUpperCase();
  if (/\b(CRITICAL|OUT OF LIMIT|HIGH|RED|OPEN|FAILED)\b/.test(s)) return 'bad';
  if (/\b(ATTENTION|MEDIUM|ORANGE|YELLOW|WARNING|IN_PROGRESS|DUPLICATE)\b/.test(s)) return 'warn';
  if (/\b(NORMAL|HEALTHY|LOW|GREEN|COMPLETED|SUCCESS|OK)\b/.test(s)) return 'ok';
  return 'neutral';
};

const toneClass: Record<Tone, string> = {
  ok: 'bg-ok-soft text-ok',
  warn: 'bg-warn-soft text-warn',
  bad: 'bg-bad-soft text-bad',
  neutral: 'bg-muted text-ink-2',
  info: 'bg-accent-soft text-accent-ink',
};

const ToneIcon: React.FC<{ tone: Tone; className?: string }> = ({ tone, className }) =>
  tone === 'bad' ? (
    <AlertOctagon className={className} />
  ) : tone === 'warn' ? (
    <AlertTriangle className={className} />
  ) : tone === 'ok' ? (
    <CheckCircle2 className={className} />
  ) : null;

/** Status always ships with an icon and a word, never color alone. */
export const StatusPill: React.FC<{ status?: string; tone?: Tone; label?: string; className?: string }> = ({
  status,
  tone,
  label,
  className,
}) => {
  const t = tone ?? toneOf(status);
  const text = label ?? (status ? titleCase(status) : '');
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-2xs font-medium whitespace-nowrap',
        toneClass[t],
        className,
      )}
    >
      <ToneIcon tone={t} className="size-3" />
      {text}
    </span>
  );
};

export const Badge: React.FC<{ tone?: Tone; children: React.ReactNode; className?: string }> = ({
  tone = 'neutral',
  children,
  className,
}) => (
  <span className={cn('inline-flex items-center rounded px-1.5 py-0.5 text-2xs font-medium', toneClass[tone], className)}>{children}</span>
);

export const titleCase = (s: string) =>
  s
    .replace(/_/g, ' ')
    .toLowerCase()
    .replace(/(^|\s)\S/g, (c) => c.toUpperCase());

/* ------------------------------------------------------------------ Card */

export const Card: React.FC<React.HTMLAttributes<HTMLDivElement>> = ({ className, ...props }) => (
  <div className={cn('rounded-lg border border-line bg-surface shadow-card', className)} {...props} />
);

export const CardHeader: React.FC<{
  title: React.ReactNode;
  subtitle?: React.ReactNode;
  actions?: React.ReactNode;
  className?: string;
}> = ({ title, subtitle, actions, className }) => (
  <div className={cn('flex items-start justify-between gap-3 px-4 pt-3.5 pb-3', className)}>
    <div className="min-w-0">
      <h2 className="text-sm font-semibold text-ink">{title}</h2>
      {subtitle && <p className="mt-0.5 text-xs text-ink-3">{subtitle}</p>}
    </div>
    {actions && <div className="flex shrink-0 items-center gap-1.5">{actions}</div>}
  </div>
);

export const CardBody: React.FC<React.HTMLAttributes<HTMLDivElement>> = ({ className, ...props }) => (
  <div className={cn('px-4 pb-4', className)} {...props} />
);

/* ------------------------------------------------------------------ KPI tile */

export interface KpiProps {
  label: string;
  value: React.ReactNode;
  /** Secondary line under the value, e.g. "of 37,000 kg target". */
  hint?: React.ReactNode;
  delta?: { text: string; direction: 'up' | 'down' | 'flat'; good: boolean | null; vs?: string };
  status?: Tone;
  onClick?: () => void;
  className?: string;
}

export const Kpi: React.FC<KpiProps> = ({ label, value, hint, delta, status, onClick, className }) => {
  const Comp = onClick ? 'button' : 'div';
  const deltaTone = delta?.good == null ? 'text-ink-3' : delta.good ? 'text-ok' : 'text-bad';
  return (
    <Comp
      onClick={onClick}
      className={cn(
        'relative flex min-w-0 flex-col gap-1 rounded-lg border border-line bg-surface p-3.5 text-left shadow-card',
        onClick && 'hover:border-line-strong transition-colors',
        className,
      )}
    >
      <div className="flex items-center justify-between gap-2">
        <span className="truncate text-xs font-medium text-ink-3">{label}</span>
        {status && status !== 'neutral' && <ToneIcon tone={status} className={cn('size-3.5 shrink-0', toneClass[status].split(' ')[1])} />}
      </div>
      <div className="truncate text-[22px] font-semibold leading-7 tracking-tight text-ink">{value}</div>
      <div className="flex min-h-4 flex-col gap-0.5 text-xs">
        {delta && (
          <span className={cn('inline-flex items-center gap-0.5 whitespace-nowrap font-medium', deltaTone)}>
            {delta.direction === 'up' ? (
              <ArrowUpRight className="size-3.5" />
            ) : delta.direction === 'down' ? (
              <ArrowDownRight className="size-3.5" />
            ) : null}
            {delta.text}
            {delta.vs && <span className="font-normal text-ink-3">&nbsp;{delta.vs}</span>}
          </span>
        )}
        {hint && <span className="truncate text-ink-3">{hint}</span>}
      </div>
    </Comp>
  );
};

export const KpiGrid: React.FC<{ children: React.ReactNode; className?: string }> = ({ children, className }) => (
  <div className={cn('grid grid-cols-2 gap-3 md:grid-cols-3 xl:grid-cols-6', className)}>{children}</div>
);

/* ------------------------------------------------------------------ Meter */

/** Horizontal progress toward a limit/target. The marker shows where 100% sits. */
export const Meter: React.FC<{ value: number; max: number; tone?: Tone; marker?: number; className?: string }> = ({
  value,
  max,
  tone = 'info',
  marker,
  className,
}) => {
  const w = max > 0 ? Math.max(0, Math.min(100, (value / max) * 100)) : 0;
  const fill = { ok: 'bg-ok', warn: 'bg-warn', bad: 'bg-bad', neutral: 'bg-ink-3', info: 'bg-accent' }[tone];
  return (
    <div className={cn('relative h-1.5 w-full rounded-full bg-muted', className)}>
      <div className={cn('h-full rounded-full', fill)} style={{ width: `${w}%` }} />
      {marker != null && max > 0 && (
        <div
          className="absolute -top-0.5 h-2.5 w-0.5 rounded-full bg-ink"
          style={{ left: `calc(${Math.min(100, (marker / max) * 100)}% - 1px)` }}
        />
      )}
    </div>
  );
};

/* ------------------------------------------------------------------ Segmented control */

export function Segmented<T extends string>({
  value,
  onChange,
  options,
  size = 'md',
  ariaLabel,
}: {
  value: T;
  onChange: (v: T) => void;
  options: { value: T; label: React.ReactNode }[];
  size?: 'sm' | 'md';
  ariaLabel?: string;
}) {
  return (
    <div role="radiogroup" aria-label={ariaLabel} className="inline-flex rounded-md border border-line bg-muted p-0.5">
      {options.map((o) => (
        <button
          key={o.value}
          role="radio"
          aria-checked={value === o.value}
          onClick={() => onChange(o.value)}
          className={cn(
            'rounded px-2.5 font-medium transition-colors',
            size === 'sm' ? 'h-6 text-xs' : 'h-7 text-xs',
            value === o.value ? 'bg-surface text-ink shadow-card' : 'text-ink-3 hover:text-ink',
          )}
        >
          {o.label}
        </button>
      ))}
    </div>
  );
}

/* ------------------------------------------------------------------ Select */

export const Select: React.FC<
  React.SelectHTMLAttributes<HTMLSelectElement> & { options: { value: string; label: string }[]; label?: string }
> = ({ options, label, className, ...props }) => (
  <label className="inline-flex items-center gap-1.5 text-xs text-ink-3">
    {label && <span>{label}</span>}
    <select
      className={cn(
        'h-7 rounded-md border border-line bg-surface pl-2 pr-7 text-xs font-medium text-ink hover:border-line-strong',
        className,
      )}
      {...props}
    >
      {options.map((o) => (
        <option key={o.value} value={o.value}>
          {o.label}
        </option>
      ))}
    </select>
  </label>
);

/* ------------------------------------------------------------------ Tabs */

export function Tabs<T extends string>({
  value,
  onChange,
  tabs,
}: {
  value: T;
  onChange: (v: T) => void;
  tabs: { value: T; label: string; count?: number }[];
}) {
  return (
    <div role="tablist" className="flex gap-4 border-b border-line">
      {tabs.map((t) => (
        <button
          key={t.value}
          role="tab"
          aria-selected={value === t.value}
          onClick={() => onChange(t.value)}
          className={cn(
            '-mb-px flex items-center gap-1.5 border-b-2 pb-2 pt-1 text-sm font-medium transition-colors',
            value === t.value ? 'border-accent text-ink' : 'border-transparent text-ink-3 hover:text-ink',
          )}
        >
          {t.label}
          {t.count != null && <span className="rounded-full bg-muted px-1.5 text-2xs text-ink-2">{t.count}</span>}
        </button>
      ))}
    </div>
  );
}

/* ------------------------------------------------------------------ States */

export const Skeleton: React.FC<{ className?: string }> = ({ className }) => (
  <div className={cn('relative overflow-hidden rounded-md bg-muted', className)}>
    <div className="absolute inset-0 -translate-x-full animate-shimmer bg-gradient-to-r from-transparent via-surface/60 to-transparent" />
  </div>
);

export const PageSkeleton: React.FC = () => (
  <div className="space-y-4" aria-busy="true" aria-label="Loading">
    <div className="grid grid-cols-2 gap-3 md:grid-cols-3 xl:grid-cols-6">
      {Array.from({ length: 6 }).map((_, i) => (
        <Skeleton key={i} className="h-[92px]" />
      ))}
    </div>
    <div className="grid gap-4 lg:grid-cols-3">
      <Skeleton className="h-72 lg:col-span-2" />
      <Skeleton className="h-72" />
    </div>
    <Skeleton className="h-64" />
  </div>
);

export const EmptyState: React.FC<{
  title: string;
  description?: React.ReactNode;
  action?: React.ReactNode;
  icon?: React.ReactNode;
  className?: string;
}> = ({ title, description, action, icon, className }) => (
  <div className={cn('flex flex-col items-center justify-center px-6 py-10 text-center', className)}>
    <div className="mb-3 flex size-10 items-center justify-center rounded-full bg-muted text-ink-3">
      {icon ?? <Inbox className="size-5" />}
    </div>
    <h3 className="text-sm font-semibold text-ink">{title}</h3>
    {description && <p className="mt-1 max-w-sm text-xs text-ink-3">{description}</p>}
    {action && <div className="mt-4">{action}</div>}
  </div>
);

export const ErrorState: React.FC<{ error: unknown; onRetry?: () => void; title?: string }> = ({
  error,
  onRetry,
  title = 'Could not load this page',
}) => (
  <Card>
    <EmptyState
      icon={<AlertOctagon className="size-5 text-bad" />}
      title={title}
      description={error instanceof Error ? error.message : String(error)}
      action={
        onRetry && (
          <Button onClick={onRetry} icon={<RefreshCw className="size-3.5" />}>
            Try again
          </Button>
        )
      }
    />
  </Card>
);

/** Inline banner for data caveats (unreconciled totals, no data for the period). */
export const Notice: React.FC<{ tone?: Tone; children: React.ReactNode; action?: React.ReactNode }> = ({
  tone = 'info',
  children,
  action,
}) => (
  <div className={cn('flex items-center gap-2.5 rounded-lg px-3.5 py-2.5 text-xs', toneClass[tone])}>
    <ToneIcon tone={tone} className="size-4 shrink-0" />
    <div className="flex-1">{children}</div>
    {action}
  </div>
);
