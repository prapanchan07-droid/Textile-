export interface MachineTypePerformanceItem {
  machine_type: string;
  efficiency_pct: number;
  loss_kg: number;
  actual_kg: number;
  target_kg: number;
  status: 'ATTENTION' | 'NORMAL' | 'HEALTHY';
}

export interface ProductionTrendPoint {
  date_label: string;
  actual_kg: number;
  target_kg: number;
  gap_kg: number;
  achievement_pct?: number;
}

export interface LossReasonItem {
  rank: number;
  category: string;
  impact_kg: number;
  percentage: number;
}

export interface ShiftPerformanceItem {
  shift_name: string;
  actual_kg: number;
  target_kg: number;
  achievement_pct: number;
}

export interface ProductionFactorItem {
  name: string;
  display_value: string;
  direction: 'UP' | 'DOWN';
  status: 'CRITICAL' | 'ATTENTION' | 'HEALTHY' | 'NORMAL';
}

export interface ProductionComparisonData {
  reference_period: string;
  reference_kg: number;
  current_kg: number;
  difference_kg: number;
  difference_pct: number;
  main_reason: string;
}

export interface AiProductionAnalysisData {
  summary: string;
  affected_machine_type: string;
  main_observed_factor: string;
  recommended_action: string;
}

export interface ProductionModuleData {
  company_name: string;
  selected_period: string;
  actual_kg: number;
  target_kg: number;
  gap_kg: number;
  achievement_pct: number;
  trend: ProductionTrendPoint[];
  machine_type_performance: MachineTypePerformanceItem[];
  loss_reasons: LossReasonItem[];
  shift_performance?: ShiftPerformanceItem[];
  production_factors?: ProductionFactorItem[];
  spotlight_machine_type?: string;
  spotlight_efficiency_pct?: number;
  spotlight_factory_avg_gap?: number;
  spotlight_loss_kg?: number;
  comparison?: ProductionComparisonData;
  ai_analysis?: AiProductionAnalysisData;
}
