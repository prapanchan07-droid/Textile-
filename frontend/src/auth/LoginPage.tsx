import React, { useState } from 'react';
import { Navigate, useLocation, useNavigate } from 'react-router-dom';
import { Eye, EyeOff, Lock, LogIn, Sparkles, TrendingUp, User, Wrench } from 'lucide-react';
import { Button } from '../design/ui';
import { AshokLogo } from '../layout/AshokLogo';
import { useAuth } from './AuthContext';

const PITCH = [
  { icon: TrendingUp, title: 'Know what weaving earns', text: 'Efficiency, grade-A yield and margin per style, in rupees, not jargon.' },
  { icon: Wrench, title: 'Fix the right loom first', text: 'Stoppages ranked by money lost, with the likely cause and who owns the fix.' },
  { icon: Sparkles, title: 'See problems before they cost you', text: 'AI flags looms drifting down and PM that is about to be missed.' },
];

export const LoginPage: React.FC = () => {
  const { user, login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const from = (location.state as { from?: string } | null)?.from;

  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [show, setShow] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  if (user) return <Navigate to={from && from !== '/login' ? from : '/'} replace />;

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setBusy(true);
    try {
      await login(username.trim(), password);
      navigate(from && from !== '/login' ? from : '/', { replace: true });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not sign in');
    } finally {
      setBusy(false);
    }
  };

  const fieldClass =
    'h-11 w-full rounded-xl border border-line bg-surface pl-10 pr-3 text-sm text-ink outline-none transition-colors placeholder:text-ink-3 focus:border-accent focus:ring-2 focus:ring-accent/20';

  return (
    <div className="grid min-h-full bg-canvas lg:grid-cols-[1.05fr_1fr]">
      <aside className="relative hidden overflow-hidden bg-sidebar p-12 text-sidebar-ink lg:flex lg:flex-col lg:justify-between">
        <div
          aria-hidden
          className="pointer-events-none absolute inset-0 opacity-[0.07]"
          style={{ backgroundImage: 'repeating-linear-gradient(90deg,#fff 0 1px,transparent 1px 14px),repeating-linear-gradient(0deg,#fff 0 1px,transparent 1px 14px)' }}
        />
        <AshokLogo className="relative" />
        <div className="relative max-w-md">
          <p className="text-2xs font-semibold uppercase tracking-[0.18em] text-sidebar-ink-2">Weaving operations</p>
          <h1 className="mt-3 text-4xl font-semibold leading-tight tracking-tight">Every loom, every shift, every rupee in one place.</h1>
          <ul className="mt-10 space-y-6">
            {PITCH.map((p) => (
              <li key={p.title} className="flex gap-4">
                <span className="grid size-10 shrink-0 place-items-center rounded-xl bg-white/10">
                  <p.icon className="size-5" />
                </span>
                <div>
                  <div className="text-sm font-semibold">{p.title}</div>
                  <div className="mt-0.5 text-sm text-sidebar-ink-2">{p.text}</div>
                </div>
              </li>
            ))}
          </ul>
        </div>
        <p className="relative text-xs text-sidebar-ink-2">© Ashok Textile Mills Pvt Ltd</p>
      </aside>

      <main className="flex items-center justify-center px-5 py-12 sm:px-10">
        <div className="w-full max-w-[400px]">
          <div className="mb-8 lg:hidden">
            <div className="rounded-xl bg-sidebar p-3">
              <AshokLogo />
            </div>
          </div>
          <h2 className="text-2xl font-semibold tracking-tight text-ink">Sign in</h2>
          <p className="mt-1.5 text-sm text-ink-3">Use your mill account. </p>

          <form onSubmit={submit} className="mt-7 space-y-4" noValidate>
            <label className="block">
              <span className="mb-1.5 block text-xs font-medium text-ink-2">Username</span>
              <span className="relative block">
                <User className="pointer-events-none absolute left-3.5 top-1/2 size-4 -translate-y-1/2 text-ink-3" />
                <input
                  className={fieldClass}
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  autoComplete="username"
                  autoFocus
                  placeholder="e.g. admin"
                />
              </span>
            </label>
            <label className="block">
              <span className="mb-1.5 block text-xs font-medium text-ink-2">Password</span>
              <span className="relative block">
                <Lock className="pointer-events-none absolute left-3.5 top-1/2 size-4 -translate-y-1/2 text-ink-3" />
                <input
                  className={`${fieldClass} pr-11`}
                  type={show ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  autoComplete="current-password"
                  placeholder="Your password"
                />
                <button
                  type="button"
                  onClick={() => setShow((s) => !s)}
                  className="absolute right-2 top-1/2 -translate-y-1/2 rounded-md p-1.5 text-ink-3 hover:bg-muted hover:text-ink"
                  aria-label={show ? 'Hide password' : 'Show password'}
                >
                  {show ? <EyeOff className="size-4" /> : <Eye className="size-4" />}
                </button>
              </span>
            </label>

            {error && (
              <div role="alert" className="rounded-lg border border-bad/30 bg-bad-soft px-3 py-2 text-sm text-bad">
                {error}
              </div>
            )}

            <Button type="submit" variant="primary" loading={busy} disabled={!username.trim() || !password} icon={<LogIn className="size-4" />} className="!h-11 w-full !text-sm">
              Sign in
            </Button>
          </form>

        </div>
      </main>
    </div>
  );
};
