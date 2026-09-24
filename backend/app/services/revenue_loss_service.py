from typing import List, Optional
from app.schemas.revenue_loss import (
    RevenueLossModuleResponse,
    RevenueCurrentSummary,
    RevenueTrendPoint,
    DispatchOrdersData,
    MoneyPositionData,
    StockCategoryItem,
    BusinessPerformanceSummary,
    BusinessAttentionItem
)

class RevenueLossService:
    @staticmethod
    def get_revenue_loss_data(period: str = "THIS_MONTH") -> RevenueLossModuleResponse:
        # 1. Revenue Current Summary
        revenue_summary = RevenueCurrentSummary(
            revenue_amount_lakhs=28.5,
            previous_period_lakhs=30.6,
            change_lakhs=-2.1,
            change_pct=-6.9,
            currency_symbol="₹"
        )

        # 2. Revenue Trend Points
        revenue_trend = [
            RevenueTrendPoint(date_label="Sep 16", revenue_lakhs=3.9, previous_lakhs=4.1, change_pct=-4.9),
            RevenueTrendPoint(date_label="Sep 17", revenue_lakhs=4.2, previous_lakhs=4.3, change_pct=-2.3),
            RevenueTrendPoint(date_label="Sep 18", revenue_lakhs=4.5, previous_lakhs=4.2, change_pct=7.1),
            RevenueTrendPoint(date_label="Sep 19", revenue_lakhs=3.6, previous_lakhs=4.5, change_pct=-20.0),
            RevenueTrendPoint(date_label="Sep 20", revenue_lakhs=4.1, previous_lakhs=4.2, change_pct=-2.4),
            RevenueTrendPoint(date_label="Sep 21", revenue_lakhs=4.0, previous_lakhs=4.5, change_pct=-11.1),
            RevenueTrendPoint(date_label="Sep 22", revenue_lakhs=4.2, previous_lakhs=4.8, change_pct=-12.5),
        ]

        # 3. Dispatch & Orders Data
        dispatch_orders = DispatchOrdersData(
            orders_meters=216000,
            dispatched_meters=149926,
            pending_meters=66074,
            fulfillment_pct=69.4
        )

        # 4. Money Position Data
        money_position = MoneyPositionData(
            outstanding_lakhs=90.7,
            collected_lakhs=82.9,
            collection_rate_pct=91.4,
            currency_symbol="₹"
        )

        # 5. Stock Position
        stock_position = [
            StockCategoryItem(category="Fabric Stock", current_value_lakhs=12.34, limit_value_lakhs=5.00, unit="₹ L", status="ATTENTION"),
            StockCategoryItem(category="Yarn Stock – Unit I", current_value_lakhs=1.91, limit_value_lakhs=3.00, unit="₹ L", status="NORMAL"),
            StockCategoryItem(category="Yarn Stock – Unit II", current_value_lakhs=2.15, limit_value_lakhs=3.50, unit="₹ L", status="NORMAL"),
        ]

        # 6. Business Performance Summary
        business_performance = BusinessPerformanceSummary(
            revenue_lakhs=28.5,
            orders_meters=216000,
            dispatched_meters=149926,
            collected_lakhs=82.9,
            outstanding_lakhs=90.7,
            total_stock_lakhs=16.40
        )

        # 7. Business Attention Items
        needs_attention = [
            BusinessAttentionItem(severity="HIGH", title="Outstanding is high", detail="₹90.7 L pending collection across major distributor accounts"),
            BusinessAttentionItem(severity="MEDIUM", title="Dispatch below order volume", detail="66,074 m pending dispatch execution"),
            BusinessAttentionItem(severity="MEDIUM", title="Stock above configured limit", detail="Fabric stock currently at ₹12.34 L vs ₹5.00 L limit"),
        ]

        return RevenueLossModuleResponse(
            company_name="Ashok Textiles",
            period=period,
            revenue_summary=revenue_summary,
            revenue_trend=revenue_trend,
            dispatch_orders=dispatch_orders,
            money_position=money_position,
            stock_position=stock_position,
            business_performance=business_performance,
            needs_attention=needs_attention
        )
