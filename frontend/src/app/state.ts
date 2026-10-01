import { useCallback, useEffect, useState, useSyncExternalStore } from 'react';
import { useSearchParams } from 'react-router-dom';
import { isPeriod, type Period } from '../lib/period';

const safeGet = (k: string) => {
  try {
    return localStorage.getItem(k);
  } catch {
    return null;
  }
};
const safeSet = (k: string, v: string) => {
  try {
    localStorage.setItem(k, v);
  } catch {
    /* storage unavailable: preference just won't persist */
  }
};

/**
 * The reporting period is a URL parameter so any view can be shared or bookmarked
 * exactly as seen. The last choice is remembered as the default for new visits.
 */
export function usePeriod(): [Period, (p: Period) => void] {
  const [params, setParams] = useSearchParams();
  const raw = params.get('period');
  const stored = safeGet('period');
  const period: Period = isPeriod(raw) ? raw : isPeriod(stored) ? stored : 'TODAY';

  const setPeriod = useCallback(
    (p: Period) => {
      safeSet('period', p);
      setParams(
        (prev) => {
          const next = new URLSearchParams(prev);
          next.set('period', p);
          return next;
        },
        { replace: true },
      );
    },
    [setParams],
  );
  return [period, setPeriod];
}

/** Update one search param without dropping the others (period, tabs, selections). */
export function useParam(key: string, fallback = ''): [string, (v: string | null) => void] {
  const [params, setParams] = useSearchParams();
  const value = params.get(key) ?? fallback;
  const set = useCallback(
    (v: string | null) =>
      setParams(
        (prev) => {
          const next = new URLSearchParams(prev);
          if (v == null || v === '' || v === fallback) next.delete(key);
          else next.set(key, v);
          return next;
        },
        { replace: true },
      ),
    [key, fallback, setParams],
  );
  return [value, set];
}

export type ThemePref = 'light' | 'dark' | 'system';

const themeListeners = new Set<() => void>();
const readTheme = (): ThemePref => {
  const t = safeGet('theme');
  return t === 'light' || t === 'dark' ? t : 'system';
};

export function useTheme(): [ThemePref, (t: ThemePref) => void, 'light' | 'dark'] {
  const pref = useSyncExternalStore((cb) => {
    themeListeners.add(cb);
    return () => themeListeners.delete(cb);
  }, readTheme);
  const [systemDark, setSystemDark] = useState(() => window.matchMedia('(prefers-color-scheme: dark)').matches);
  useEffect(() => {
    const mq = window.matchMedia('(prefers-color-scheme: dark)');
    const on = () => setSystemDark(mq.matches);
    mq.addEventListener('change', on);
    return () => mq.removeEventListener('change', on);
  }, []);

  const setTheme = useCallback((t: ThemePref) => {
    if (t === 'system') {
      try {
        localStorage.removeItem('theme');
      } catch {
        /* ignore */
      }
      delete document.documentElement.dataset.theme;
    } else {
      safeSet('theme', t);
      document.documentElement.dataset.theme = t;
    }
    themeListeners.forEach((l) => l());
  }, []);

  const resolved = pref === 'system' ? (systemDark ? 'dark' : 'light') : pref;
  return [pref, setTheme, resolved];
}
