from typing import List, Optional
from pydantic import BaseModel

class RevenueCurrentSummary(BaseModel):
    revenue_amount_lakhs: float
    previous_period_lakhs: float
    change_lakhs: float
    change_pct: float
    currency_symbol: str = "₹"

class RevenueTrendPoint(BaseModel):
    date_label: str
    revenue_lakhs: float
    previous_lakhs: float
    change_pct: float

class DispatchOrdersData(BaseModel):
    orders_meters: int
    dispatched_meters: int
    pending_meters: int
    fulfillment_pct: float

class MoneyPositionData(BaseModel):
    outstanding_lakhs: float
    collected_lakhs: float
    collection_rate_pct: float
    currency_symbol: str = "₹"

class StockCategoryItem(BaseModel):
    category: str
    current_value_lakhs: float
    limit_value_lakhs: float
    unit: str = "₹"
    status: str  # 'NORMAL' | 'ATTENTION' | 'CRITICAL'

class BusinessPerformanceSummary(BaseModel):
    revenue_lakhs: float
    orders_meters: int
    dispatched_meters: int
    collected_lakhs: float
    outstanding_lakhs: float
    total_stock_lakhs: float

class BusinessAttentionItem(BaseModel):
    severity: str  # 'HIGH' | 'MEDIUM' | 'LOW'
    title: str
    detail: str

class RevenueLossModuleResponse(BaseModel):
    company_name: str = "Ashok Textiles"
    period: str = "THIS_MONTH"
    revenue_summary: RevenueCurrentSummary
    revenue_trend: List[RevenueTrendPoint]
    dispatch_orders: DispatchOrdersData
    money_position: MoneyPositionData
    stock_position: List[StockCategoryItem]
    business_performance: BusinessPerformanceSummary
    needs_attention: List[BusinessAttentionItem]
