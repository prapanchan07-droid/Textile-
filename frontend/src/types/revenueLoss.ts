export interface RevenueCurrentSummary {
  revenue_amount_lakhs: number;
  previous_period_lakhs: number;
  change_lakhs: number;
  change_pct: number;
  currency_symbol: string;
}

export interface RevenueTrendPoint {
  date_label: string;
  revenue_lakhs: number;
  previous_lakhs: number;
  change_pct: number;
}

export interface DispatchOrdersData {
  orders_meters: number;
  dispatched_meters: number;
  pending_meters: number;
  fulfillment_pct: number;
}

export interface MoneyPositionData {
  outstanding_lakhs: number;
  collected_lakhs: number;
  collection_rate_pct: number;
  currency_symbol: string;
}

export interface StockCategoryItem {
  category: string;
  current_value_lakhs: number;
  limit_value_lakhs: number;
  unit: string;
  status: 'NORMAL' | 'ATTENTION' | 'CRITICAL';
}

export interface BusinessPerformanceSummary {
  revenue_lakhs: number;
  orders_meters: number;
  dispatched_meters: number;
  collected_lakhs: number;
  outstanding_lakhs: number;
  total_stock_lakhs: number;
}

export interface BusinessAttentionItem {
  severity: 'HIGH' | 'MEDIUM' | 'LOW';
  title: string;
  detail: string;
}

export interface RevenueLossModuleData {
  company_name: string;
  period: string;
  revenue_summary: RevenueCurrentSummary;
  revenue_trend: RevenueTrendPoint[];
  dispatch_orders: DispatchOrdersData;
  money_position: MoneyPositionData;
  stock_position: StockCategoryItem[];
  business_performance: BusinessPerformanceSummary;
  needs_attention: BusinessAttentionItem[];
}
