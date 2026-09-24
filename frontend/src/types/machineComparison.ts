export interface MachineMasterOption {
  machine_id: string;
  machine_type: string;
  section: string;
}

export interface MachineMetricValue {
  machine_id: string;
  machine_type: string;
  value: number;
  formatted_value: string;
  unit: string;
  status: 'CRITICAL' | 'ATTENTION' | 'NORMAL';
  variance_vs_reference?: number;
  variance_label?: string;
}

export interface MultiMetricRow {
  metric_name: string;
  unit: string;
  values: Record<string, string>;
}

export interface HeadToHeadMetric {
  metric_key: string;
  metric_name: string;
  unit: string;
  machine1_value: number;
  machine1_formatted: string;
  machine2_value: number;
  machine2_formatted: string;
  delta_text: string;
  leader_machine_id?: string;
}

export interface ComparisonInsightData {
  summary_text: string;
  key_observations: string[];
}

export interface MachineComparisonResponse {
  company_name: string;
  selected_period: string;
  selected_metric: string;
  selected_machine_type: string;
  selected_machine_ids: string[];
  available_machine_types: string[];
  all_master_machines: MachineMasterOption[];
  
  reference_type: string;
  reference_value: number;
  reference_formatted: string;
  
  primary_metrics: MachineMetricValue[];
  multi_metric_matrix: MultiMetricRow[];
  head_to_head?: HeadToHeadMetric[];
  insight: ComparisonInsightData;
}
