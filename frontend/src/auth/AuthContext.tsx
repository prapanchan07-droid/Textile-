import React, { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { getData, postJson, UNAUTHORIZED_EVENT } from '../api/client';
import type { AuthUser, LoginResult } from '../types/auth';
import { clearToken, getToken, setToken } from './token';

interface AuthState {
  user: AuthUser | null;
  /** True while a stored token is being checked on first load. */
  loading: boolean;
  login: (username: string, password: string) => Promise<AuthUser>;
  logout: () => void;
}

const AuthContext = createContext<AuthState | null>(null);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const queryClient = useQueryClient();
  const [user, setUser] = useState<AuthUser | null>(null);
  const [loading, setLoading] = useState(() => getToken() != null);

  // Restore the session from a stored token.
  useEffect(() => {
    if (!getToken()) return;
    let live = true;
    getData<AuthUser>('/auth/me')
      .then((u) => live && setUser(u))
      .catch(() => clearToken())
      .finally(() => live && setLoading(false));
    return () => {
      live = false;
    };
  }, []);

  const logout = useCallback(() => {
    clearToken();
    setUser(null);
    queryClient.clear(); // never show one user's data to the next
  }, [queryClient]);

  useEffect(() => {
    window.addEventListener(UNAUTHORIZED_EVENT, logout);
    return () => window.removeEventListener(UNAUTHORIZED_EVENT, logout);
  }, [logout]);

  const login = useCallback(
    async (username: string, password: string) => {
      const res = await postJson<LoginResult>('/auth/login', { username, password });
      queryClient.clear();
      setToken(res.access_token);
      setUser(res.user);
      return res.user;
    },
    [queryClient],
  );

  const value = useMemo(() => ({ user, loading, login, logout }), [user, loading, login, logout]);
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = (): AuthState => {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used inside AuthProvider');
  return ctx;
};
