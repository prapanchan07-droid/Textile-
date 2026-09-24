export type TimePeriod = 'TODAY' | 'SHIFT' | 'YESTERDAY' | 'THIS_WEEK' | 'THIS_MONTH';

export type ComparisonPeriod = 
  | 'PREVIOUS_SHIFT'
  | 'PREVIOUS_DAY'
  | 'PREVIOUS_WEEK'
  | 'PREVIOUS_MONTH'
  | 'THREE_MONTH_AVG';

export type PerformanceStatus = 'CRITICAL' | 'ATTENTION' | 'NORMAL' | 'HEALTHY';

export interface ProductionSummary {
  target_kg: number;
  actual_kg: number;
  loss_kg: number;
  achievement_pct: number;
  efficiency_pct: number;
  unit: string;
}

export interface ProductionVariance {
  target_kg: number;
  actual_kg: number;
  variance_kg: number;
  variance_pct: number;
  is_statistically_significant: boolean;
  display_note: string;
}

export interface ProductionTrendItem {
  label: string;
  target_kg: number;
  actual_kg: number;
  loss_kg: number;
  efficiency_pct: number;
}

export interface LossContributor {
  category: string;
  impact_kg: number;
  percentage: number;
  evidence: string;
}

export interface PeriodComparisonMetric {
  metric: string;
  current: string;
  previous: string;
  change_text: string;
  change_pct: number;
  trend: 'down_bad' | 'up_bad' | 'up_good' | 'down_good' | 'neutral';
}

export interface MachineAttentionItem {
  machine_id: string;
  machine_type: string;
  section_id: string;
  efficiency_pct: number;
  loss_kg: number;
  downtime_minutes: number;
  change_pct: number;
  status: PerformanceStatus;
  primary_issue: string;
}

export interface LowEfficiencyMachine {
  machine_id: string;
  efficiency_pct: number;
  factory_avg_pct: number;
  gap_points: number;
  historical_status: string;
}

export interface AIInsightData {
  summary: string;
  observations: string[];
  contributors: string[];
  recommended_investigation: string[];
  evidence_found: string[];
  confidence: string;
}

export interface ImpactProjectionData {
  is_sufficient_data: boolean;
  daily_gap_kg: number;
  projected_7d_gap_kg: number;
  projected_30d_gap_kg: number;
  assumptions_note: string;
  insufficient_data_reason?: string;
}

export interface RecommendedInvestigationData {
  priority: string;
  area: string;
  machine_id: string;
  observed_issue: string;
  recommended_next_step: string;
}

export interface ExecutiveSummaryData {
  factory_status: string;
  main_issue: string;
  affected_entity: string;
  impact_kg: number;
  recommended_action: string;
}

export interface FactoryOverviewData {
  company_name: string;
  selected_unit: string;
  selected_period: TimePeriod;
  selected_comparison: ComparisonPeriod;
  data_frequency: string;
  user_role: string;
  permitted_section?: string;
  
  executive_summary: ExecutiveSummaryData;
  production_summary: ProductionSummary;
  variance: ProductionVariance;
  trend: ProductionTrendItem[];
  loss_contributors: LossContributor[];
  period_comparison: PeriodComparisonMetric[];
  machines_requiring_attention: MachineAttentionItem[];
  low_efficiency_spotlight: LowEfficiencyMachine;
  ai_insight: AIInsightData;
  impact_projection: ImpactProjectionData;
  recommended_investigation: RecommendedInvestigationData;
}
