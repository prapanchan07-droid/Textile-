export interface ManpowerSummary {
  required: number;
  available: number;
  shortage: number;
  attendance_pct: number;
}

export interface DepartmentManpowerItem {
  department: string;
  required: number;
  available: number;
  gap: number;
  attendance_pct: number;
}

export interface ManpowerTrendPoint {
  date_label: string;
  required: number;
  available: number;
  shortage: number;
  attendance_pct: number;
}

export interface QualityStatusData {
  status: 'NORMAL' | 'ATTENTION' | 'CRITICAL';
  samples_tested: number;
  pass_rate_pct: number;
  defect_rate_pct: number;
  main_issue: string;
}

export interface QualityParameterItem {
  parameter: string;
  label: string;
  value: number;
  limit: number;
  unit: string;
  status: 'NORMAL' | 'ATTENTION' | 'OUT OF LIMIT';
}

export interface QualityTrendPoint {
  date_label: string;
  value: number;
  limit: number;
}

export interface QualityMachineItem {
  machine_process: string;
  quality_issue: string;
  current_value: number;
  limit: number;
  unit: string;
  status: 'NORMAL' | 'ATTENTION' | 'OUT OF LIMIT';
}

export interface AttentionItem {
  severity: 'HIGH' | 'MEDIUM' | 'LOW';
  title: string;
  detail: string;
}

export interface ManpowerQualityModuleData {
  company_name: string;
  period: string;
  manpower_summary: ManpowerSummary;
  department_gaps: DepartmentManpowerItem[];
  manpower_trend: ManpowerTrendPoint[];
  quality_status: QualityStatusData;
  quality_parameters: QualityParameterItem[];
  quality_trends_by_param: Record<string, QualityTrendPoint[]>;
  quality_issues_by_machine: QualityMachineItem[];
  needs_attention: AttentionItem[];
}
