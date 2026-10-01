import {
  Activity,
  BadgeIndianRupee,
  Gauge,
  Cog,
  Factory,
  FlaskConical,
  ListChecks,
  UploadCloud,
  Users,
  type LucideIcon,
} from 'lucide-react';

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
 * Grouped by who uses it: leadership (Command), plant heads (Operations),
 * functional owners (Quality, People, Commercial), and admins (Data, Admin).
 */
export const NAV: NavGroup[] = [
  {
    label: 'Command',
    items: [
      { to: '/', label: 'Control Tower', icon: Gauge, keywords: 'overview dashboard home summary' },
      { to: '/actions', label: 'Action Center', icon: ListChecks, keywords: 'decision priority tasks tracker' },
    ],
  },
  {
    label: 'Operations',
    items: [
      { to: '/production', label: 'Production', icon: Factory, keywords: 'output shift kg target' },
      { to: '/assets', label: 'Machines & Downtime', icon: Activity, keywords: 'assets maintenance oee stoppage benchmark compare' },
    ],
  },
  {
    label: 'Functions',
    items: [
      { to: '/quality', label: 'Quality', icon: FlaskConical, keywords: 'lab yarn uster thick neps cv' },
      { to: '/workforce', label: 'Workforce', icon: Users, keywords: 'manpower attendance hr shortage' },
      { to: '/commercial', label: 'Sales & Finance', icon: BadgeIndianRupee, keywords: 'revenue dispatch receivables stock orders' },
    ],
  },
  {
    label: 'Platform',
    items: [
      { to: '/data', label: 'Data Imports', icon: UploadCloud, keywords: 'upload report template ingestion excel' },
      { to: '/admin/system', label: 'System Status', icon: Cog, keywords: 'health settings version database' },
    ],
  },
];

export const ALL_NAV = NAV.flatMap((g) => g.items);

export const findNav = (pathname: string) =>
  ALL_NAV.filter((i) => (i.to === '/' ? pathname === '/' : pathname.startsWith(i.to))).sort((a, b) => b.to.length - a.to.length)[0];
