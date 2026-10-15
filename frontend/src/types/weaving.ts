export type Severity = 'HIGH' | 'MEDIUM' | 'LOW';

export interface WeavingKpis {
  fabric_m: number;
  target_m: number;
  achievement_pct: number;
  efficiency_pct: number;
  grade_a_pct: number;
  loss_lakhs: number;
  loss_m: number;
  revenue_lakhs: number;
  fabric_change_pct: number;
  efficiency_change_pts: number;
  grade_a_change_pts: number;
  loss_change_pct: number;
  looms_total: number;
  looms_running: number;
  looms_stopped: number;
  looms_idle: number;
}

export interface WeavingDecision {
  id: string;
  severity: Severity;
  title: string;
  why: string;
  action: string;
  owner: string;
  impact_lakhs: number;
  link: string;
}

export interface WeavingTrendPoint {
  date_label: string;
  actual_m: number;
  target_m: number;
  efficiency_pct: number;
  grade_a_pct: number;
  loss_lakhs: number;
}

export interface WeavingShiftRow {
  shift: string;
  actual_m: number;
  target_m: number;
  efficiency_pct: number;
  grade_a_pct: number;
  top_stop_reason: string;
}

export interface WeavingGroupRow {
  loom_type: string;
  looms: number;
  actual_m: number;
  target_m: number;
  efficiency_pct: number;
  grade_a_pct: number;
  loss_lakhs: number;
}

export interface WeavingLoom {
  loom_id: string;
  loom_type: string;
  style: string;
  status: 'RUNNING' | 'STOPPED' | 'IDLE';
  health: 'NORMAL' | 'ATTENTION' | 'CRITICAL';
  rpm: number;
  efficiency_pct: number;
  actual_m: number;
  target_m: number;
  loss_m: number;
  loss_lakhs: number;
  grade_a_pct: number;
  defects_per_100m: number;
  stops: number;
  stop_reason: string | null;
  stopped_since_min: number;
  weaver: string;
  fitter: string;
  main_issue: string;
  trend: number[];
}

export interface WeavingStopCause {
  cause: string;
  minutes: number;
  stops: number;
  loss_lakhs: number;
  share_pct: number;
  advice: string;
}

export interface WeavingQuality {
  grade_a_pct: number;
  grade_b_pct: number;
  grade_c_pct: number;
  defects_per_100m: number;
  rejected_m: number;
  downgrade_loss_lakhs: number;
  defect_types: { defect: string; count: number; share_pct: number }[];
  worst_looms: { loom_id: string; style: string; defects_per_100m: number; grade_a_pct: number; weaver: string }[];
}

export type StyleCall = 'PUSH' | 'HOLD' | 'REPRICE' | 'STOP';

export interface WeavingStyle {
  style: string;
  fabric: string;
  meters: number;
  rate_per_m: number;
  cost_per_m: number;
  margin_pct: number;
  profit_lakhs: number;
  grade_a_pct: number;
  efficiency_pct: number;
  recommendation: StyleCall;
  reason: string;
}

export interface WeavingPeople {
  headcount: number;
  available_today: number;
  absenteeism_pct: number;
  departments: { department: string; required: number; available: number; gap: number; avg_grade: string; status: string }[];
  grades: { grade: string; count: number }[];
  shifts: { shift: string; looms_per_weaver: number; output_per_weaver_m: number; absent: number; status: string }[];
  promotion_ready: number;
  needs_training: number;
}

export interface WeavingPmItem {
  loom_id: string;
  task: string;
  due_date: string;
  days_overdue: number;
  status: 'OVERDUE' | 'DUE_SOON' | 'OK';
}

export interface WeavingMaintenance {
  mtbf_hours: number;
  mttr_min: number;
  breakdowns: number;
  pm_overdue: number;
  pm_due_soon: number;
  pm_compliance_pct: number;
  items: WeavingPmItem[];
}

export interface WeavingAction {
  id: string;
  issue: string;
  action: string;
  owner: string;
  due: string;
  status: 'OPEN' | 'IN_PROGRESS' | 'COMPLETED';
  impact_lakhs: number;
}

export interface WeavingModuleData {
  data_source: 'MOCK' | 'LIVE';
  period: string;
  period_label: string;
  days: number;
  verdict: string;
  kpis: WeavingKpis;
  decisions: WeavingDecision[];
  trend: WeavingTrendPoint[];
  shifts: WeavingShiftRow[];
  groups: WeavingGroupRow[];
  looms: WeavingLoom[];
  stop_causes: WeavingStopCause[];
  quality: WeavingQuality;
  styles: WeavingStyle[];
  people: WeavingPeople;
  maintenance: WeavingMaintenance;
  actions: WeavingAction[];
}
