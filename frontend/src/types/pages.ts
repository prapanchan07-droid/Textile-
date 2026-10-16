/** Payloads of the weaving pages (backend/app/weaving/pages). One interface per page. */
export type Severity = 'HIGH' | 'MEDIUM' | 'LOW';
export type Tone = 'ok' | 'warn' | 'bad' | 'neutral';

export interface KpiData {
  label: string;
  value: number | null;
  unit: string;
  delta: number | null;
  delta_unit: string;
  good_when: 'up' | 'down';
  spark: number[];
  hint: string;
  status: Tone | null;
}

export interface TrendPoint {
  date: string;
  label: string;
  meters: number;
  target_m: number;
  efficiency_pct: number | null;
  utilization_pct: number | null;
  stops_per_100k: number | null;
  downtime_min: number;
  complete: boolean;
}

export interface ForecastData {
  method: string;
  points: number[];
  low: number[];
  high: number[];
  mape_pct: number | null;
  backtest_days: number;
  note: string;
}

export interface Evidence {
  period: string;
  scope: Record<string, string>;
  observed: Record<string, string | number | boolean | null>;
  baseline: Record<string, string | number | boolean | null>;
  n_observations: number;
  estimated_impact: { lost_m: number; lost_lakhs: number | null; assumptions: string[] } | null;
  limitations: string[];
}

export interface Finding {
  key: string;
  kind: string;
  severity: Severity;
  title: string;
  facts: string[];
  evidence: Evidence;
  signals: { name: string; method: string; statistic: number | null; p_value: number | null; note: string | null }[];
  hypotheses: { statement: string; status: string; how_to_check: string }[];
  next_steps: string[];
  confidence: { level: 'HIGH' | 'MEDIUM' | 'LOW'; reasons: string[]; missing_information: string[] };
  priority_score: number;
  requires_human_approval: boolean;
  verified_cause: string | null;
  audiences: string[];
  link: string;
  actions?: { ref: string; action: string; owner: string | null; status: string; due: string | null; outcome_note: string | null; verified_cause: string | null }[];
}

export interface SensorAlert {
  loom_id: number;
  loom: string;
  kind: 'DRIFT' | 'SHIFT_POWER' | 'SENSOR_OFFLINE';
  sensor: string;
  level: 'CRITICAL' | 'WARNING' | 'WATCH';
  title: string;
  facts: string[];
  recent: number | null;
  normal: number | null;
  unit: string;
  z: number | null;
  slope_per_day: number | null;
  days_to_alarm: number | null;
  started_on: string | null;
  hypothesis: string | null;
  n_days: number;
  limitations: string[];
}

export interface StoppedNow {
  loom: string;
  reason: string;
  category: string;
  minutes: number;
  planned: boolean;
  weaver: string | null;
  fitter: string | null;
  hint: string | null;
  watch: string | null;
}

export interface BriefLine {
  severity: Severity;
  text: string;
  link: string;
  kind: string;
  impact_lakhs: number | null;
}

export interface OrderRow {
  order_no: string;
  style: string;
  fabric: string;
  customer: string | null;
  customer_code: string | null;
  tier: string | null;
  priority: 'A' | 'B' | 'C';
  ordered_m: number;
  produced_m: number;
  remaining_m: number;
  progress_pct: number;
  due_date: string | null;
  rate_per_m: number | null;
  looms: string[];
  started_on: string | null;
  state: 'COMPLETED' | 'QUEUED' | 'STALLED' | 'RUNNING';
  risk: 'DONE' | 'UNSCHEDULED' | 'STALLED' | 'UNKNOWN' | 'LATE' | 'AT_RISK' | 'ON_TRACK';
  eta: string | null;
  eta_early?: string;
  eta_late?: string;
  slack_days: number | null;
  pace_m_per_day: number | null;
  completed_on: string | null;
  explain: string;
  revenue_at_stake_lakhs: number | null;
}

export interface CoverageRow {
  shift: string;
  role: string;
  required: number;
  present: number;
  absent: number;
  gap: number;
  status: 'NORMAL' | 'ATTENTION' | 'CRITICAL';
}

export interface ShiftRow {
  shift: string;
  meters: number;
  target_m: number;
  efficiency_pct: number | null;
  utilization_pct?: number | null;
  defects_per_100m?: number | null;
  stops_per_100k?: number | null;
  grade_a_pct?: number | null;
}

export interface DayProgress {
  day: string;
  hours: { hour: string; shift: string; actual_m: number; plan_m: number; cum_actual_m: number; cum_plan_m: number; running_pct: number | null }[];
  actual_m: number;
  plan_m: number;
  achievement_pct: number | null;
}

export interface CommandData {
  as_of: string;
  period: string;
  headline: string;
  kpis: KpiData[];
  live: { running: number; stopped: number; idle: number; total: number; stopped_now: StoppedNow[] };
  day_progress: DayProgress;
  trend: TrendPoint[];
  forecast: ForecastData | null;
  brief: BriefLine[];
  alerts: SensorAlert[];
  findings: Finding[];
  orders: OrderRow[];
  staffing: CoverageRow[];
  shifts: ShiftRow[];
  health_summary: { at_risk: number; watch: number; healthy: number };
}

export interface StyleEconomics {
  style: string;
  fabric: string;
  meters: number;
  efficiency_pct: number | null;
  target_efficiency_pct: number;
  grade_a_pct: number | null;
  rate_per_m: number | null;
  cost_per_m: number | null;
  margin_pct: number | null;
  profit_lakhs: number | null;
  recommendation: 'PUSH' | 'HOLD' | 'REPRICE' | 'STOP' | null;
  reason: string | null;
}

export interface CustomerRow {
  customer: string;
  tier: string | null;
  orders: number;
  open_orders: number;
  ordered_m: number;
  remaining_m: number;
  late: number;
  at_risk: number;
  completed: number;
  completed_on_time: number;
  revenue_at_stake_lakhs: number | null;
}

export interface OrdersSummary {
  LATE: number;
  AT_RISK: number;
  ON_TRACK: number;
  UNSCHEDULED: number;
  STALLED: number;
  UNKNOWN: number;
  open: number;
  completed: number;
  completed_on_time: number;
  value_at_risk_lakhs: number | null;
  remaining_m: number;
}

export interface OwnerData {
  as_of: string;
  period: string;
  money_visible: boolean;
  headline: string;
  kpis: KpiData[];
  decisions: { kind: string; severity: Severity; title: string; why: string; action: string; link: string; impact_lakhs: number | null; confidence: string; needs_approval: boolean }[];
  waterfall: { label: string; value: number; kind: 'total' | 'loss' }[];
  orders_summary: OrdersSummary;
  orders: OrderRow[];
  customers: CustomerRow[];
  styles: StyleEconomics[];
  revenue_trend: { label: string; revenue_lakhs: number | null; efficiency_pct: number | null }[];
  capacity: { free_loom_days: number; capacity_booked_pct: number; horizon_days: number; late_now: number; late_with_plan: number; moves: number } | null;
}

export interface OrdersData {
  as_of: string;
  money_visible: boolean;
  summary: OrdersSummary;
  orders: OrderRow[];
  customers: CustomerRow[];
  styles: StyleEconomics[];
  notes: string[];
}

export interface WaterfallRow {
  label: string;
  value: number;
  kind: 'total' | 'loss';
}

export interface LoomPerf {
  loom: string;
  type: string;
  style: string;
  meters: number;
  target_m: number;
  achievement_pct: number | null;
  efficiency_pct: number | null;
  utilization_pct: number | null;
  stops_per_100k: number | null;
  kwh_per_100m: number | null;
  health: number | null;
}

export interface ProductionData {
  as_of: string;
  period: string;
  complete: boolean;
  kpis: KpiData[];
  trend: TrendPoint[];
  forecast: ForecastData | null;
  waterfall: WaterfallRow[];
  shifts: ShiftRow[];
  loom_types: { type: string; looms: number; meters: number; efficiency_pct: number | null; utilization_pct: number | null }[];
  styles: { style: string; fabric: string; meters: number; target_m: number; efficiency_pct: number | null; target_efficiency_pct: number | null; achievement_pct: number | null }[];
  leaders: LoomPerf[];
  laggards: LoomPerf[];
  looms: LoomPerf[];
  heatmap: { days: string[]; rows: { loom: string; type: string; values: (number | null)[] }[] };
}

export interface StoppagesData {
  as_of: string;
  period: string;
  kpis: KpiData[];
  pareto: { cause: string; category: string; planned: boolean; stops: number; downtime_min: number; share_pct: number; cumulative_pct: number; avg_min: number | null; per_100k: number | null; est_lost_m: number; est_lost_lakhs: number | null; hint: string | null }[];
  daily_by_category: { categories: string[]; rows: Record<string, number | string>[] };
  heatmap: { days: string[]; hours: number[]; grid: number[][]; window: string };
  matrix: { categories: string[]; rows: { loom: string; total_min: number; cells: Record<string, number> }[] };
  by_shift: { categories: string[]; rows: { shift: string; cells: Record<string, number> }[] };
  open_now: StoppedNow[];
  repeat: Finding[];
  trend: TrendPoint[];
  notes: string[];
}

export interface MachineRow {
  loom: string;
  type: string;
  make: string | null;
  model: string | null;
  serial_no: string | null;
  year: number | null;
  age_years: number | null;
  bay: string | null;
  shedding: string | null;
  colours: number | null;
  reed_space_cm: number | null;
  rated_rpm: number;
  power_kw: number | null;
  last_overhaul: string | null;
  days_since_overhaul: number | null;
  warranty_until: string | null;
  status: 'RUNNING' | 'STOPPED' | 'IDLE';
  stopped_min: number;
  stop_reason: string | null;
  style: string;
  efficiency_pct: number | null;
  stops_per_100k: number | null;
  health: number | null;
  band: 'HEALTHY' | 'WATCH' | 'AT_RISK' | null;
  alerts: { level: string; title: string; kind: string }[];
  next_pm: { task: string; due: string; overdue_days: number } | null;
  running_hours_14d: number | null;
}

export interface FleetData {
  as_of: string;
  kpis: KpiData[];
  alerts: SensorAlert[];
  looms: MachineRow[];
  method: string[];
}

export interface HealthComponent {
  factor: string;
  points: number;
  detail: string;
}

export interface MachineDetail {
  as_of: string;
  spec: MachineRow | null;
  health: { score: number; band: string; components: HealthComponent[]; note: string } | null;
  alerts: SensorAlert[];
  sensors: { key: string; label: string; unit: string; alarm: number | null; worse: string; normal: { center: number; low: number; high: number } | null; points: { date: string; label: string; value: number }[] }[];
  performance: { label: string; efficiency_pct: number | null; stops_per_100k: number | null }[];
  causes: { cause: string; category: string; planned: boolean; stops: number; downtime_min: number }[];
  order: { order_no: string; customer: string | null } | null;
  reliability: { breakdowns_14d: number; mtbf_hours: number | null; mttr_min: number | null };
  maintenance: { preventive: { task: string; planned_for: string | null; status: string; overdue_days: number }[]; breakdowns: { task: string; started_at: string | null; minutes: number | null; status: string }[] };
  recent_stops: { started_at: string; minutes: number | null; open: boolean; reason: string; category: string }[];
}

export interface MaintenanceData {
  as_of: string;
  kpis: KpiData[];
  priorities: { loom: string; score: number; severity: Severity; confidence: string; facts: string[]; steps: string[]; link: string; health: number | null }[];
  alerts: SensorAlert[];
  pm_board: { loom: string; task: string; due: string; days: number; state: 'OVERDUE' | 'TODAY' | 'UPCOMING'; health: number | null }[];
  breakdowns: { loom: string; task: string; started_at: string; minutes: number | null; status: string }[];
  breakdown_trend: { label: string; breakdowns: number; downtime_min: number }[];
  watchlist: { loom: string; health: number }[];
  notes: string[];
}

export interface DirectoryRow {
  code: string;
  name: string | null;
  role: string;
  designation: string | null;
  department: string | null;
  grade: string | null;
  shift: string | null;
  contract: string | null;
  experience_years: number | null;
  skills: string[];
  joined_on: string | null;
  attendance_pct: number | null;
  days_tracked: number;
  absent_days: number;
  phone: string | null;
  efficiency_pct?: number | null;
  vs_floor_pts?: number | null;
  meters?: number;
  shifts_worked?: number;
  meters_per_shift?: number;
  looms?: string[];
  stops_per_100k?: number | null;
  weft_stops_per_100k?: number | null;
  warp_stops_per_100k?: number | null;
}

export interface WorkforceData {
  as_of: string;
  scope: string;
  period: string;
  days: number;
  kpis: { headcount: number; by_role: Record<string, number>; permanent_pct: number | null; present_today: number; tracked_today: number; absenteeism_14d_pct: number | null; avg_experience_years: number | null };
  coverage: CoverageRow[];
  absenteeism_daily: { date: string; absent_pct: number | null; absent: number; records: number }[];
  absenteeism_heat: { weekday: string; values: Record<string, number | null> }[];
  skills: { skill: string; per_shift: Record<string, number>; thin: boolean }[];
  directory: DirectoryRow[];
  top_weavers: string[];
  coaching: { code: string; name: string | null; shift: string | null; grade: string | null; experience_years: number | null; topic: string; observed: string; suggestion: string }[];
  notes: string[];
}

export interface Note {
  id: number;
  ref: string;
  shift: string;
  date: string;
  loom: string | null;
  category: string;
  severity: 'INFO' | 'WARNING' | 'URGENT';
  body: string;
  author: string | null;
  created_at: string;
  resolved: boolean;
  this_shift: boolean;
}

export interface RosterPerson {
  code: string;
  name: string | null;
  role: string;
  designation: string | null;
  status: string;
  looms: string[];
  grade: string | null;
}

export interface Roster {
  people: RosterPerson[];
  present: number;
  absent: number;
  overloaded: { name: string | null; code: string; looms: string[] }[];
}

export interface ActionBrief {
  ref: string;
  issue: string;
  action?: string;
  owner: string | null;
  due: string | null;
  status: string;
}

export interface CockpitData {
  as_of: string;
  shift: { name: string; date: string; start: string; end: string; elapsed_pct: number };
  kpis: KpiData[];
  chart: { hour: string; actual_m: number; plan_m: number; cum_actual_m: number; cum_plan_m: number }[];
  floor: { loom: string; type: string; status: 'RUNNING' | 'STOPPED' | 'IDLE'; efficiency_pct: number | null; weaver: string | null; reason: string | null; stopped_min: number; health: number | null; alerts: string[] }[];
  stopped_now: StoppedNow[];
  top_causes: { cause: string; downtime_min: number; stops: number }[];
  watch: { loom: string; title: string; level: string; fact: string }[];
  roster: Roster;
  notes: Note[];
  actions: ActionBrief[];
  findings: Finding[];
}

export interface HandoverData {
  as_of: string;
  which: 'current' | 'previous';
  complete: boolean;
  shift: { name: string; date: string; start: string; end: string };
  narrative: string[];
  kpis: { meters: number; plan_m: number; achievement_pct: number | null; efficiency_pct: number | null; stops: number; avg_stop_min: number | null; downtime_min: number };
  top_causes: { cause: string; downtime_min: number; stops: number }[];
  longest_stops: { loom: string; reason: string; minutes: number; open: boolean; at: string }[];
  weakest: { loom: string; efficiency_pct: number | null }[];
  roster: Roster;
  notes: Note[];
  carry_over: Note[];
  actions: ActionBrief[];
  watch: { loom: string; title: string; level: string }[];
}

export interface SchedulerOrder {
  order_no: string;
  style: string;
  customer: string | null;
  priority: 'A' | 'B' | 'C';
  due: string | null;
  remaining_m: number;
  baseline_eta: string | null;
  baseline_slack_days: number | null;
  baseline_late: boolean;
  proposed_eta: string | null;
  proposed_slack_days: number | null;
  proposed_late: boolean;
  improved: boolean;
}

export interface SchedulerMove {
  loom: string;
  from_order: string | null;
  to_order: string;
  from_style: string | null;
  to_style: string;
  day: number;
  date: string;
  changeover: boolean;
  gain_m_per_day: number;
  loom_eff_pct: number;
  reason: string;
  lateness_cut: number;
  to_before: number | null;
  to_after: number | null;
  from_before: number | null;
  from_after: number | null;
}

export interface TimelineSeg {
  order: string | null;
  style: string | null;
  start: string;
  end: string;
  start_day: number;
  end_day: number;
  metres: number;
}

export interface PlanSummary {
  orders: { order_no: string; eta: string | null; slack_days: number | null; late: boolean; beyond_horizon: boolean }[];
  late_orders: number;
  total_late_days: number;
  changeovers: number;
  capacity_booked_pct: number;
  free_loom_days: number;
  output_m: number;
  revenue_late_lakhs?: number;
}

export interface SchedulerData {
  signature: string;
  generated_at: string;
  today: string;
  horizon_days: number;
  objective: string;
  assumptions: string[];
  baseline: PlanSummary;
  proposed: PlanSummary;
  orders: SchedulerOrder[];
  moves: SchedulerMove[];
  summary: string[];
  timeline: { proposed: Record<string, TimelineSeg[]>; baseline: Record<string, TimelineSeg[]> };
  looms: Record<string, { type: string; eff_pct: number; health: number; style: string | null; order: string | null }>;
  decisions: { id: number; plan_ref: string; status: string; created_at: string; decided_at: string | null; decision_note: string | null; moves: number }[];
  can_decide: boolean;
}

export interface InsightsData {
  as_of: string;
  role: string;
  money_visible: boolean;
  lens_days: number;
  findings: Finding[];
  alerts: SensorAlert[];
  summary: { total: number; high: number; by_kind: Record<string, number>; with_actions: number };
  method: string[];
}

export interface CompareOption {
  key: string;
  label: string;
  group: string;
}

export interface Recommended {
  id: string;
  title: string;
  why: string;
  type: string;
  keys: string[];
  style: string | null;
  metrics: string[];
  source: string;
}

export interface CompareMeta {
  as_of: string;
  types: { key: string; label: string }[];
  metrics: { key: string; label: string; unit: string; better: 'high' | 'low' }[];
  default_metrics: string[];
  options: Record<string, CompareOption[]>;
  recommended: Recommended[];
}

export interface CompareResult {
  type: string;
  period: string;
  days: number;
  style_filter: string | null;
  metrics: { key: string; label: string; unit: string; better: 'high' | 'low' }[];
  reference: string | null;
  entities: {
    key: string;
    label: string;
    subtitle: string;
    metrics: Record<string, number | null>;
    vs_reference: Record<string, { ratio?: number | null; diff?: number; t?: number; p_value: number; direction: 'higher' | 'lower'; significant: boolean; events?: number[] }>;
    daily: { efficiency_pct: { date: string; value: number | null }[]; stops_per_100k: { date: string; value: number | null }[] };
  }[];
  highlights: string[];
  radar: ({ metric: string; key: string } & Record<string, number | string | null>)[];
  not_found: string[];
  notes: string[];
}

export interface QualityData {
  as_of: string;
  period: string;
  kpis: KpiData[];
  trend: { label: string; defects_per_100m: number | null; grade_a_pct: number | null; inspected_m: number }[];
  defect_types: string[];
  by_shift: Record<string, number | string | null>[];
  style_shift: { shifts: string[]; rows: { style: string; cells: Record<string, number | null> }[] };
  yarn_lots_total: number;
  yarn_lots: { lot: string; supplier: string | null; style: string | null; strength_cn_tex: number | null; elongation_pct: number | null; cv_pct: number | null; size_pickup_pct: number | null; beams: number; warp_stops_per_100k: number | null; efficiency_pct: number | null; flagged: boolean }[];
  recent_rolls: { roll_no: string; loom: string; style: string; shift: string; grade: string; length_m: number; defects: number; points: number }[];
  worst_looms: { loom: string; defects_per_100m: number | null; grade_a_pct: number | null; inspected_m: number }[];
  findings: Finding[];
  notes: string[];
}

export interface ActionItem {
  ref: string;
  issue: string;
  action: string;
  owner_role: string | null;
  owner: string | null;
  due: string | null;
  overdue: boolean;
  status: 'OPEN' | 'IN_PROGRESS' | 'COMPLETED' | 'CANCELLED';
  finding_key: string | null;
  requires_approval: boolean;
  approved: boolean;
  expected_impact_lakhs: number | null;
  outcome_note: string | null;
  verified_cause: string | null;
  completed_at: string | null;
  created_at: string | null;
}

export interface ActionsData {
  as_of: string;
  money_visible: boolean;
  can_approve: boolean;
  summary: { open: number; in_progress: number; completed: number; overdue: number; value_open_lakhs: number | null };
  actions: ActionItem[];
  owner_roles: string[];
}
