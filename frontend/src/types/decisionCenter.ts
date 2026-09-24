export interface TopPriorityData {
  priority_level: string;
  badge_label: string;
  title: string;
  sub_highlight: string;
  main_contributor: string;
  most_affected_machine_type: string;
  most_affected_machine_id: string;
  actual_kg: number;
  target_kg: number;
  gap_kg: number;
  target_tab: string;
}

export interface WhyContributor {
  category: string;
  percentage: number;
  status_color: string; // "RED" | "ORANGE" | "YELLOW"
  detail_text?: string;
}

export interface SecondaryMachineContributor {
  machine_id: string;
  machine_type: string;
  loss_kg: number;
  status_color: string;
}

export interface WhereLocationData {
  primary_machine_id: string;
  primary_machine_type: string;
  primary_section: string;
  production_loss_kg: number;
  efficiency_pct: number;
  downtime_minutes: number;
  status: string;
  secondary_machines: SecondaryMachineContributor[];
}

export interface RecommendedAction {
  id: string;
  step_number: number;
  action_text: string;
  button_label: string;
  target_tab: string;
  target_id?: string;
}

export interface IfContinuesData {
  current_daily_gap_kg: number;
  projected_7d_gap_kg: number;
  projected_30d_gap_kg: number;
  label: string;
  disclaimer_note: string;
}

export interface OtherIssueItem {
  id: string;
  status_icon: string;
  category: string;
  location_or_area: string;
  impact_detail: string;
  target_tab?: string;
}

export interface ActionTrackerItem {
  id: string;
  issue: string;
  action: string;
  owner: string;
  status: string; // "OPEN" | "IN_PROGRESS" | "COMPLETED"
  status_badge: string;
  created_date: string;
}

export interface AIInsightData {
  summary_paragraph: string;
  recommended_focus: string;
  evidence_confidence: string;
  facts: string[];
  projections: string[];
}

export interface DecisionCenterData {
  company_name: string;
  selected_unit: string;
  selected_period: string;
  user_role: string;
  permitted_section?: string;
  
  top_priority: TopPriorityData;
  why_contributors: WhyContributor[];
  where_location: WhereLocationData;
  recommended_actions: RecommendedAction[];
  if_continues: IfContinuesData;
  other_issues: OtherIssueItem[];
  action_tracker: ActionTrackerItem[];
  ai_insight: AIInsightData;
}
