import { Cog, UploadCloud, type LucideIcon } from 'lucide-react';
import { sectionsFor } from '../features/weaving/sections';
import type { AuthUser } from '../types/auth';

export interface NavItem {
  to: string;
  label: string;
  icon: LucideIcon;
  /** Extra words the command palette should match. */
  keywords?: string;
}

export interface NavGroup {
  label: string;
  items: NavItem[];
}

/**
 * Navigation is built from the signed-in user's role: weaving pages first
 * (their role's pages only), then platform tools for the people who run them.
 */
export const buildNav = (user: AuthUser | null): NavGroup[] => {
  if (!user) return [];
  const groups: NavGroup[] = [];
  for (const sec of sectionsFor(user)) {
    let g = groups.find((x) => x.label === sec.group);
    if (!g) groups.push((g = { label: sec.group, items: [] }));
    g.items.push({ to: sec.path, label: sec.label, icon: sec.icon, keywords: sec.keywords });
  }
  if (user.role === 'OWNER' || user.role === 'WEAVING_MANAGER') {
    groups.push({
      label: 'Platform',
      items: [
        { to: '/data', label: 'Data Imports', icon: UploadCloud, keywords: 'upload report template ingestion excel' },
        { to: '/admin/system', label: 'System Status', icon: Cog, keywords: 'health settings version database' },
      ],
    });
  }
  return groups;
};

export const findNav = (groups: NavGroup[], pathname: string) =>
  groups
    .flatMap((g) => g.items)
    .filter((i) => pathname.startsWith(i.to))
    .sort((a, b) => b.to.length - a.to.length)[0];
