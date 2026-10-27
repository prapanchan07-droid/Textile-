/** Shapes returned by /api/v1/mill. Numbers are null when the source does not provide them (never 0 for "missing"). */

export type Source = 'MILL_REPORT' | 'MACHINE_EXPORT';
export type Severity = 'INFO' | 'WARNING' | 'CRITICAL';
export type Basis = 'MEASURED' | 'CALCULATED' | 'MODELED' | 'STATISTICAL' | 'DATA';

export interface Kpis {
  loom_shifts: number;
  looms: number;
  meters: number | null;
  kilopicks: number | null;
  efficiency_pct: number | null;
  warp_stops: number | null;
  weft_stops: number | null;
  warp_stops_cmpx: number | null;
  weft_stops_cmpx: number | null;
  meters_per_loom_shift: number | null;
  coverage: Record<string, number>;
}

export interface PeriodMeta {
  filters: Record<string, unknown>;
  date_from: string | null;
  date_to: string | null;
  days_with_data: number;
  sources: Partial<Record<Source, number>>;
}

export interface Freshness {
  latest_by_category: Record<string, Partial<Record<Source, string>>>;
  last_import_at: string | null;
  live_connections: Record<string, number>;
  live_feed: 'NONE' | 'LIVE' | 'SIMULATED';
  statement: string;
}

export interface Finding {
  id: string;
  kind: string;
  basis: Basis;
  severity: Severity;
  title: string;
  loom_id: number | null;
  loom_code: string | null;
  category?: string;
  period: { from: string | null; to: string | null };
  evidence: Record<string, unknown>;
  impact: { meters_gap?: number | null; metric?: string; assumption?: string } | null;
  implication: string;
  next_step: string;
}

export interface GroupRow {
  id: number;
  code: string;
  name: string;
  leader: string | null;
  looms: number;
  meters: number | null;
  efficiency_pct: number | null;
  loom_shifts: number;
  open_tasks: number;
  blocked_tasks: number;
  completed_tasks: number;
  open_alerts: number;
}

export interface AlertBrief {
  id: number;
  title: string;
  severity: Severity;
  status: string;
  period: string | null;
  loom_id: number | null;
  observed: number | null;
  threshold: number | null;
  source: string;
  escalation_level: number;
}

export interface Dashboard {
  period: PeriodMeta;
  freshness: Freshness;
  kpis: Kpis & {
    registered_looms: number;
    reporting_looms: number;
    not_reporting_looms: string[];
    target_meters: number | null;
    open_alerts: Partial<Record<Severity, number>>;
    open_tasks: number;
    overdue_tasks: number;
    open_work_orders: number;
  };
  by_category: Record<string, Kpis>;
  by_shift: Record<string, Kpis>;
  daily: ({ date: string; meters: number | null; efficiency_pct: number | null; sources: Source[] } & Record<string, unknown>)[];
  findings: Finding[];
  groups: GroupRow[];
  top_alerts: AlertBrief[];
  comparability: string;
}

export interface LoomCard {
  id: number;
  code: string;
  category: string;
  manufacturer: string;
  loom_no: number;
  width_cm: number | null;
  group: { id: number; code: string; name: string } | null;
  latest: { date: string; shift: string; efficiency_pct: number | null; meters: number | null; rpm: number | null; style: string | null; source: Source } | null;
  period: {
    efficiency_pct: number | null;
    meters: number | null;
    warp_stops_cmpx: number | null;
    weft_stops_cmpx: number | null;
    loom_shifts: number;
    style: string | null;
    peer_median_efficiency_pct: number | null;
    trend: (number | null)[];
  } | null;
  live: { state: string; origin: string | null; machine_state: string | null; rpm: number | null; sampled_at: string | null };
  open_alerts: number;
  open_work_orders: number;
}

export interface LoomGrid {
  period: PeriodMeta;
  freshness: Freshness;
  looms: LoomCard[];
}

export interface ProductionRecord {
  id: number;
  prod_date: string;
  shift: string;
  source_kind: Source;
  data_origin: string;
  style_code: string | null;
  rpm: number | null;
  efficiency_pct: number | null;
  loom_efficiency_pct: number | null;
  kilopicks: number | null;
  meters: number | null;
  warp_stops: number | null;
  weft_stops: number | null;
  other_stops: number | null;
  run_min: number | null;
  stop_min: number | null;
  batch_id: number | null;
}

export interface Peer {
  loom_id: number;
  loom_code: string;
  efficiency_pct: number | null;
  meters: number | null;
  warp_stops_cmpx: number | null;
  weft_stops_cmpx: number | null;
  loom_shifts: number;
}

export interface LoomDetail {
  loom: {
    id: number; code: string; category: string; manufacturer: string; model: string | null; loom_no: number; width_cm: number | null;
    notes: string | null; attributes: Record<string, unknown>; style: string | null; style_description: string | null;
  };
  period: PeriodMeta;
  kpis: Kpis;
  by_shift: Record<string, Kpis>;
  daily: { date: string; efficiency_pct: number | null; meters: number | null; warp_stops: number | null; weft_stops: number | null; sources: Source[] }[];
  records: ProductionRecord[];
  peers: { cohort: { category: string; width_cm: number | null; style: string | null; source: Source }; size: number; median_efficiency_pct: number | null;
    rank: number | null; peers: Peer[]; valid: boolean; note: string | null } | null;
  anomalies: { prod_date: string; shift: string; efficiency_pct: number; baseline_median: number; robust_z: number; direction: string; points: number; meaning: string }[];
  findings: Finding[];
  stop_causes: { cause: string; count: number }[];
  stop_causes_note: string | null;
  missing_note: string | null;
  connection: { adapter: string; host: string | null; enabled: boolean; state: string; last_success_at: string | null; last_error: string | null } | null;
  live_state: string;
  telemetry: { sampled_at: string; state: string; rpm: number | null; efficiency_pct: number | null; origin: string }[];
  alerts: { id: number; title: string; severity: Severity; status: string; period: string | null; observed: number | null; threshold: number | null;
    first_seen_at: string; resolution_notes: string | null }[];
  tasks: { id: number; title: string; status: string; priority: string; due_at: string | null }[];
  work_orders: { id: number; title: string; kind: string; status: string; reported_at: string; completed_at: string | null; downtime_min: number | null; cause: string | null }[];
  group_history: { group: string; group_id: number; valid_from: string; valid_to: string | null }[];
  recommendations: { action: string; why: string; basis: Basis }[];
}

export interface Meta {
  categories: { code: string; name: string }[];
  shifts: { code: string; start: string; end: string }[];
  styles: { code: string; description: string | null }[];
  groups: { id: number; code: string; name: string }[];
  looms: { id: number; code: string; category: string }[];
  data_range: { first: string | null; last: string | null };
  freshness: Freshness;
}

export interface Page<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}

export interface Alert {
  id: number;
  rule_code: string;
  title: string;
  metric: string;
  observed: number | null;
  threshold: number | null;
  baseline: number | null;
  period: string | null;
  source: string;
  data_origin: string;
  severity: Severity;
  status: 'OPEN' | 'ACKNOWLEDGED' | 'RESOLVED';
  occurrences: number;
  first_seen_at: string;
  last_seen_at: string;
  condition_cleared_at: string | null;
  escalation_level: number;
  loom: { id: number; code: string } | null;
  group_id: number | null;
  assigned_group_id: number | null;
  assigned_person_id: number | null;
  acknowledged_at: string | null;
  resolved_at: string | null;
  resolution_notes: string | null;
  evidence?: Record<string, unknown>;
  events?: { kind: string; note: string | null; at: string }[];
  tasks?: { id: number; title: string; status: string }[];
}

export interface AlertRule {
  id: number;
  code: string;
  name: string;
  description: string | null;
  metric: string;
  comparator: 'lt' | 'gt';
  threshold: number | null;
  baseline_days: number;
  min_baseline_points: number;
  categories: string | null;
  consecutive: number;
  cooldown_hours: number;
  escalate_after_hours: number | null;
  severity: Severity;
  enabled: boolean;
}

export interface Person {
  id: number;
  name: string;
  role: string;
  employee_code: string | null;
  phone: string | null;
  is_active: boolean;
}

export interface Group {
  id: number;
  code: string;
  name: string;
  leader: Person | null;
  leader_id: number | null;
  responsibilities: string | null;
  shift_coverage: string | null;
  is_active: boolean;
  looms: { id: number; code: string; category: string }[];
  members: (Person & { shift: string | null; assignment_id: number; valid_from: string })[];
  loom_history?: { loom: string; valid_from: string; valid_to: string | null }[];
  tasks?: Task[];
  alerts?: { id: number; title: string; severity: Severity; status: string; period: string | null }[];
}

export interface Task {
  id: number;
  title: string;
  description: string | null;
  expected_outcome: string | null;
  status: 'PENDING' | 'IN_PROGRESS' | 'BLOCKED' | 'COMPLETED' | 'REOPENED';
  priority: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  due_at: string | null;
  overdue: boolean;
  group: { id: number; name: string } | null;
  assignee: { id: number; name: string } | null;
  loom: { id: number; code: string } | null;
  alert_id: number | null;
  completion_notes: string | null;
  escalated_to_owner: boolean;
  created_at: string;
  updated_at: string;
  completed_at: string | null;
  events?: { kind: string; from: string | null; to: string | null; note: string | null; at: string }[];
}

export interface WorkOrder {
  id: number;
  loom: { id: number; code: string };
  kind: string;
  title: string;
  description: string | null;
  priority: string;
  status: string;
  assignee: { id: number; name: string } | null;
  alert_id: number | null;
  due_date: string | null;
  overdue: boolean;
  reported_at: string;
  started_at: string | null;
  completed_at: string | null;
  downtime_min: number | null;
  cause: string | null;
  resolution: string | null;
}

export interface ImportBatch {
  id: number;
  filename: string;
  status: 'PREVIEWED' | 'PROCESSING' | 'COMMITTED' | 'FAILED' | 'DUPLICATE' | 'DISCARDED';
  source_format: string | null;
  format_label: string | null;
  size_bytes: number;
  period_start: string | null;
  period_end: string | null;
  records_parsed: number;
  records_inserted: number;
  records_updated: number;
  records_unchanged: number;
  error_count: number;
  warning_count: number;
  error: string | null;
  created_at: string;
  committed_at: string | null;
  reconciliation_summary: Record<string, number>;
  summary?: Record<string, unknown> & {
    plan?: { insert: number; update: number; unchanged: number; new_looms: number };
    data_quality?: { completeness_pct: Record<string, number>; reconciliation: Record<string, number>; issues: Record<string, number> };
    duplicate_of?: number;
    message?: string;
  };
  reconciliation?: { scope: string; metric: string; source_value: number | null; computed_value: number | null; tolerance: number; status: string; note: string }[];
}

export interface ImportIssue {
  id: number;
  severity: 'ERROR' | 'WARNING' | 'INFO';
  code: string;
  message: string;
  sheet: string | null;
  row: number | null;
  column: string | null;
  raw_value: string | null;
}

export interface OwnerReport {
  id: number;
  title: string;
  period_start: string;
  period_end: string;
  shift: string | null;
  status: 'DRAFT' | 'PUBLISHED' | 'ACKNOWLEDGED';
  generated_at: string;
  published_at: string | null;
  acknowledged_at: string | null;
  owner_comment: string | null;
  commentary: string | null;
  decisions_needed: string | null;
  risks: string | null;
  snapshot?: ReportSnapshot;
}

export interface ReportSnapshot {
  meta: { period: { from: string; to: string; shift: string | null }; generated_at: string; freshness: Freshness; sources: Record<string, number>;
    days_with_data: number; import_batches: { id: number; filename: string; format: string; warnings: number; errors: number }[]; definitions: Record<string, string> };
  production: { meters: number | null; kilopicks: number | null; efficiency_pct: number | null; loom_shifts: number; reporting_looms: number; registered_looms: number;
    not_reporting_looms: string[]; by_category: Record<string, Kpis> };
  target: { target_meters: number | null; actual_meters: number | null; vs_target_pct: number | null; note: string | null };
  efficiency: { by_shift: Record<string, number | null>; by_category: Record<string, number | null>; daily: Dashboard['daily'] };
  deviations: Finding[];
  stops: { findings: Finding[]; totals: Record<string, number | null>; note: string };
  alerts: { open_by_severity: Record<string, number>; critical_or_escalated: { id: number; title: string; severity: Severity; status: string; period: string | null; escalation_level: number }[]; resolved_in_period: number };
  maintenance: { open: { id: number; title: string; kind: string; status: string }[]; completed_in_period: { id: number; title: string; kind: string; status: string; downtime_min: number | null }[] };
  groups: GroupRow[];
  tasks: { completed: number; open: number; blocked: number; overdue: { id: number; title: string; status: string; priority: string; due_at: string | null }[];
    escalated_to_owner: { id: number; title: string; status: string; priority: string }[] };
  energy: { air_status: string; energy_status: string; requirements: string[] };
  opportunities: { title: string; impact: Finding['impact']; basis: Basis }[];
  decisions: { id: number; title: string; status: string; priority: string }[];
  risks: string[];
}

export interface Connection {
  loom: { id: number; code: string; category: string; manufacturer: string; model: string | null };
  adapter: string;
  host: string | null;
  port: number | null;
  credentials_env: string | null;
  poll_seconds: number | null;
  enabled: boolean;
  state: string;
  last_attempt_at: string | null;
  last_success_at: string | null;
  consecutive_failures: number;
  last_error: string | null;
  notes: string | null;
}

export interface MetricDef {
  key: string;
  label: string;
  meaning: string;
  formula: string;
  unit: string;
  source_fields: string;
  aggregation: string;
  missing_data: string;
  basis: Basis;
  notes: string;
}

export interface Notification {
  id: number;
  title: string;
  body: string | null;
  severity: Severity;
  link: string | null;
  created_at: string;
  read_at: string | null;
}
