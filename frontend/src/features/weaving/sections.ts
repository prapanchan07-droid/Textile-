import {
  Activity, BadgeIndianRupee, BrainCircuit, CalendarClock, ClipboardList, Cpu, Crown, FlaskConical, GitCompareArrows, Factory, Gauge, ListChecks, MonitorPlay, NotebookPen, Users, Wrench,
  type LucideIcon,
} from 'lucide-react';
import type { AuthUser, WeavingSection } from '../../types/auth';

export interface SectionDef {
  slug: WeavingSection;
  path: string;
  label: string;
  icon: LucideIcon;
  keywords: string;
  /** Sidebar group it belongs to */
  group: 'Overview' | 'Operations' | 'Intelligence' | 'Planning' | 'Follow-up';
}

/** Every weaving page. Which of them a person sees is decided by their role on the server (`user.sections`). */
export const SECTIONS: SectionDef[] = [
  { slug: 'owner', path: '/weaving/owner', label: 'Owner Brief', icon: Crown, group: 'Overview', keywords: 'owner md money profit decisions delivery customers brief' },
  { slug: 'command', path: '/weaving/command', label: 'Command Centre', icon: Gauge, group: 'Overview', keywords: 'gm manager live floor overview morning brief' },
  { slug: 'cockpit', path: '/weaving/cockpit', label: 'Shift Cockpit', icon: MonitorPlay, group: 'Overview', keywords: 'supervisor shift live floor stopped looms roster' },
  { slug: 'maintenance', path: '/weaving/maintenance', label: 'Maintenance Desk', icon: Wrench, group: 'Overview', keywords: 'maintenance priorities pm breakdown mtbf mttr work' },
  { slug: 'quality', path: '/weaving/quality', label: 'Quality Desk', icon: FlaskConical, group: 'Overview', keywords: 'quality defects yarn lot shift inspection grade' },
  { slug: 'production', path: '/weaving/production', label: 'Production', icon: Factory, group: 'Operations', keywords: 'output efficiency utilization energy heatmap forecast waterfall' },
  { slug: 'stoppages', path: '/weaving/stoppages', label: 'Stoppages', icon: Activity, group: 'Operations', keywords: 'downtime warp weft pareto breaks heatmap causes' },
  { slug: 'machines', path: '/weaving/machines', label: 'Machines', icon: Cpu, group: 'Operations', keywords: 'loom machine health abnormality sensors vibration temperature specs' },
  { slug: 'workforce', path: '/weaving/workforce', label: 'Workforce', icon: Users, group: 'Operations', keywords: 'employees weavers fitters attendance skills absenteeism shift crew' },
  { slug: 'handover', path: '/weaving/handover', label: 'Shift Handover', icon: NotebookPen, group: 'Operations', keywords: 'handover notes shift summary report' },
  { slug: 'orders', path: '/weaving/orders', label: 'Orders & Profit', icon: BadgeIndianRupee, group: 'Planning', keywords: 'orders delivery customers due date profit margin style' },
  { slug: 'scheduler', path: '/weaving/scheduler', label: 'AI Scheduler', icon: CalendarClock, group: 'Planning', keywords: 'schedule plan allocation looms orders optimise ai' },
  { slug: 'insights', path: '/weaving/insights', label: 'AI Insights', icon: BrainCircuit, group: 'Intelligence', keywords: 'ai findings root cause evidence hypotheses anomalies' },
  { slug: 'compare', path: '/weaving/compare', label: 'Compare', icon: GitCompareArrows, group: 'Intelligence', keywords: 'compare looms styles shifts suppliers yarn lots custom recommended' },
  { slug: 'actions', path: '/weaving/actions', label: 'Action Tracker', icon: ListChecks, group: 'Follow-up', keywords: 'actions tasks owner due outcome verified cause' },
];

export const sectionsFor = (user: AuthUser | null): SectionDef[] =>
  user ? user.sections.map((s) => SECTIONS.find((d) => d.slug === s)).filter((d): d is SectionDef => !!d) : [];

export const landingPath = (user: AuthUser): string => sectionsFor(user)[0]?.path ?? '/weaving/actions';
