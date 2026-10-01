import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

export const cn = (...inputs: ClassValue[]) => twMerge(clsx(inputs));

const nf0 = new Intl.NumberFormat('en-IN', { maximumFractionDigits: 0 });
const nf1 = new Intl.NumberFormat('en-IN', { maximumFractionDigits: 1 });

/** Indian grouping (1,23,456) because every user of this system reads lakhs/crores. */
export const num = (v: number | null | undefined, digits: 0 | 1 = 0) =>
  v == null || Number.isNaN(v) ? '—' : (digits ? nf1 : nf0).format(v);

/** Weight: switches to tonnes above 10,000 kg so large spinning volumes stay readable. */
export const kg = (v: number | null | undefined) => {
  if (v == null) return '—';
  const abs = Math.abs(v);
  if (abs >= 10_000) return `${nf1.format(v / 1000)} t`;
  return `${nf0.format(v)} kg`;
};

/** Chart axes use one unit for every tick, so a scale never mixes kg and t. */
export const tonnesAxis = (v: number) => (v === 0 ? '0' : `${nf1.format(v / 1000)} t`);

export const kgExact = (v: number | null | undefined) => (v == null ? '—' : `${nf0.format(v)} kg`);

export const pct = (v: number | null | undefined, digits = 1) => (v == null || Number.isNaN(v) ? '—' : `${v.toFixed(digits)}%`);

export const signed = (v: number, fmt: (n: number) => string) => `${v > 0 ? '+' : v < 0 ? '−' : ''}${fmt(Math.abs(v))}`;

/** Backend money fields are in lakhs. Show crores once a value crosses ₹1 Cr. */
export const inrFromLakhs = (lakhs: number | null | undefined) => {
  if (lakhs == null) return '—';
  const abs = Math.abs(lakhs);
  if (abs >= 100) return `₹${nf1.format(lakhs / 100)} Cr`;
  return `₹${nf1.format(lakhs)} L`;
};

export const minutes = (m: number | null | undefined) => {
  if (m == null) return '—';
  if (m < 60) return `${nf0.format(m)} min`;
  const h = Math.floor(m / 60);
  const r = Math.round(m % 60);
  return r ? `${h}h ${r}m` : `${h}h`;
};

export const meters = (v: number | null | undefined) => {
  if (v == null) return '—';
  if (Math.abs(v) >= 100_000) return `${nf1.format(v / 100_000)} L m`;
  return `${nf0.format(v)} m`;
};

export const relativeTime = (iso: string | null | undefined) => {
  if (!iso) return null;
  const t = new Date(iso.includes('T') || iso.includes('Z') ? iso : iso.replace(' ', 'T'));
  if (Number.isNaN(t.getTime())) return iso;
  const s = Math.round((Date.now() - t.getTime()) / 1000);
  if (s < 60) return 'just now';
  if (s < 3600) return `${Math.floor(s / 60)} min ago`;
  if (s < 86400) return `${Math.floor(s / 3600)} h ago`;
  return t.toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' });
};

/** Strips emoji the backend embeds in labels ("🔴 HIGH PRIORITY"); status is shown with our own pill. */
export const stripEmoji = (s: string) => s.replace(/[\u{1F300}-\u{1FAFF}\u{2600}-\u{27BF}]️?/gu, '').trim();
