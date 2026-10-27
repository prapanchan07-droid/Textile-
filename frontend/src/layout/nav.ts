import {
  Activity, BellRing, ClipboardList, Cog, Cpu, FileText, GitCompareArrows, Gauge, PlugZap, UploadCloud, Users, Wind, Wrench, type LucideIcon,
} from 'lucide-react';
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

/** One role (ADMIN) today: everyone signed in sees every page. Role-based menus come back when roles are added. */
export const buildNav = (user: AuthUser | null): NavGroup[] =>
  user
    ? [
        { label: 'Overview', items: [
          { to: '/', label: 'Command centre', icon: Gauge },
          { to: '/looms', label: 'Loom floor', icon: Cpu },
        ] },
        { label: 'Analysis', items: [
          { to: '/production', label: 'Production & shifts', icon: Activity },
          { to: '/compare', label: 'Compare machines', icon: GitCompareArrows },
          { to: '/energy', label: 'Air & energy', icon: Wind },
        ] },
        { label: 'Action', items: [
          { to: '/alerts', label: 'Alerts', icon: BellRing },
          { to: '/tasks', label: 'Tasks', icon: ClipboardList },
          { to: '/groups', label: 'Groups', icon: Users },
          { to: '/maintenance', label: 'Maintenance', icon: Wrench },
        ] },
        { label: 'Reporting', items: [{ to: '/reports', label: 'Owner reports', icon: FileText }] },
        { label: 'Data & setup', items: [
          { to: '/imports', label: 'Data imports', icon: UploadCloud },
          { to: '/connectivity', label: 'Connectivity', icon: PlugZap },
          { to: '/settings', label: 'Targets & audit', icon: Cog },
        ] },
      ]
    : [];

export const findNav = (groups: NavGroup[], pathname: string) =>
  groups
    .flatMap((g) => g.items)
    .filter((i) => (i.to === '/' ? pathname === '/' : pathname.startsWith(i.to)))
    .sort((a, b) => b.to.length - a.to.length)[0];
