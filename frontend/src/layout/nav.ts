import { Home, type LucideIcon } from 'lucide-react';
import type { AuthUser } from '../types/auth';

export interface NavItem {
  to: string;
  label: string;
  icon: LucideIcon;
}

export interface NavGroup {
  label: string;
  items: NavItem[];
}

/** Add new pages here as they are built. */
export const buildNav = (user: AuthUser | null): NavGroup[] =>
  user ? [{ label: 'Main', items: [{ to: '/', label: 'Home', icon: Home }] }] : [];

export const findNav = (groups: NavGroup[], pathname: string) =>
  groups
    .flatMap((g) => g.items)
    .filter((i) => (i.to === '/' ? pathname === '/' : pathname.startsWith(i.to)))
    .sort((a, b) => b.to.length - a.to.length)[0];
