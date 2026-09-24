export interface MachinePerformanceItem {
  machine_id: string;
  machine_type: string;
  actual_kg: number;
  target_kg: number;
  efficiency_pct: number;
  loss_kg: number;
  downtime_min: number;
  status: 'CRITICAL' | 'ATTENTION' | 'NORMAL';
  main_issue: string;
}

export interface SpotlightMachine {
  machine_id: string;
  machine_type: string;
  loss_kg: number;
  efficiency_pct: number;
  downtime_min: number;
  main_issue: string;
}

export interface DowntimeKpi {
  total_downtime_min: number;
  unplanned_downtime_min: number;
  planned_downtime_min: number;
  stoppage_count: number;
}

export interface DowntimeReasonItem {
  category: string;
  downtime_min: number;
  percentage: number;
}

export interface MachineTrendPoint {
  date_label: string;
  efficiency_pct: number;
  loss_kg: number;
}

export interface MachineDetailData {
  machine_id: string;
  machine_type: string;
  actual_kg: number;
  target_kg: number;
  efficiency_pct: number;
  loss_kg: number;
  total_downtime_min: number;
  stoppage_count: number;
  main_reason: string;
  last_maintenance: string;
  next_maintenance: string;
  recent_event: string;
  power_events: number;
  power_downtime_min: number;
  quality_status: string;
}

export interface MachinesModuleData {
  company_name: string;
  period: string;
  selected_machine_type: string;
  selected_machine_id: string;
  machine_types: string[];
  all_machines: MachinePerformanceItem[];
  spotlight_machine: SpotlightMachine;
  downtime_kpis: DowntimeKpi;
  downtime_reasons: DowntimeReasonItem[];
  machine_trend: MachineTrendPoint[];
  machine_trends_by_id?: Record<string, MachineTrendPoint[]>;
  machine_detail?: MachineDetailData;
}
