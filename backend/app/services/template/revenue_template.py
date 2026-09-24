"""Revenue & Loss page built from uploaded template data."""
from datetime import datetime, timedelta
from typing import Dict, List

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.template_data import BusinessDailyRecord, StockRecord
from app.schemas.revenue_loss import (
    RevenueLossModuleResponse, RevenueCurrentSummary, RevenueTrendPoint, DispatchOrdersData, MoneyPositionData,
    StockCategoryItem, BusinessPerformanceSummary, BusinessAttentionItem,
)
from app.services.template.factory_data import date_label

_FMT = "%Y-%m-%d"
_WINDOW_DAYS = {"TODAY": 1, "YESTERDAY": 1, "THIS_WEEK": 7, "LAST_7_DAYS": 7, "SEVEN_DAYS": 7, "THIS_MONTH": 30}


def _sum(rows: List[BusinessDailyRecord], attr: str) -> float:
    return sum(getattr(r, attr) for r in rows)


def _pct(part: float, whole: float) -> float:
    return round(part / whole * 100, 1) if whole else 0.0


def revenue_from_template(db: Session, period: str) -> RevenueLossModuleResponse:
    all_rows: List[BusinessDailyRecord] = db.query(BusinessDailyRecord).order_by(BusinessDailyRecord.report_date).all()
    latest = all_rows[-1].report_date if all_rows else None
    days = _WINDOW_DAYS.get(period.upper(), 30)

    def in_range(rows, start, end):
        return [r for r in rows if start <= r.report_date <= end]

    cur, prev = [], []
    if latest:
        end = datetime.strptime(latest, _FMT)
        if period.upper() == "YESTERDAY" and len(all_rows) > 1:
            end = datetime.strptime(all_rows[-2].report_date, _FMT)
        start = end - timedelta(days=days - 1)
        cur = in_range(all_rows, start.strftime(_FMT), end.strftime(_FMT))
        prev = in_range(all_rows, (start - timedelta(days=days)).strftime(_FMT), (start - timedelta(days=1)).strftime(_FMT))

    revenue = round(_sum(cur, "revenue_lakhs"), 2)
    prev_revenue = round(_sum(prev, "revenue_lakhs"), 2)
    change = round(revenue - prev_revenue, 2)
    revenue_summary = RevenueCurrentSummary(
        revenue_amount_lakhs=revenue, previous_period_lakhs=prev_revenue, change_lakhs=change,
        change_pct=_pct(change, prev_revenue), currency_symbol="₹")

    # Trend: last 7 dates, each compared with the record before it
    trend: List[RevenueTrendPoint] = []
    for i in range(max(0, len(all_rows) - 7), len(all_rows)):
        r = all_rows[i]
        before = all_rows[i - 1].revenue_lakhs if i > 0 else r.revenue_lakhs
        trend.append(RevenueTrendPoint(date_label=date_label(r.report_date), revenue_lakhs=r.revenue_lakhs,
                                       previous_lakhs=before, change_pct=_pct(r.revenue_lakhs - before, before)))

    orders, dispatched = _sum(cur, "orders_meters"), _sum(cur, "dispatched_meters")
    dispatch = DispatchOrdersData(orders_meters=int(orders), dispatched_meters=int(dispatched),
                                  pending_meters=int(max(0, orders - dispatched)), fulfillment_pct=_pct(dispatched, orders))

    collected = round(_sum(cur, "collected_lakhs"), 2)
    outstanding = round(all_rows[-1].outstanding_lakhs, 2) if all_rows else 0.0
    money = MoneyPositionData(outstanding_lakhs=outstanding, collected_lakhs=collected,
                              collection_rate_pct=_pct(collected, collected + outstanding), currency_symbol="₹")

    # Stock: latest as-on date per category
    stock_items: List[StockCategoryItem] = []
    stock_date = db.query(func.max(StockRecord.report_date)).scalar()
    if stock_date:
        for s in db.query(StockRecord).filter(StockRecord.report_date == stock_date).all():
            if s.limit_value_lakhs > 0 and s.current_value_lakhs > 2 * s.limit_value_lakhs:
                st = "CRITICAL"
            elif s.limit_value_lakhs > 0 and s.current_value_lakhs > s.limit_value_lakhs:
                st = "ATTENTION"
            else:
                st = "NORMAL"
            stock_items.append(StockCategoryItem(category=s.category, current_value_lakhs=s.current_value_lakhs,
                                                 limit_value_lakhs=s.limit_value_lakhs, unit="₹ L", status=st))
    total_stock = round(sum(s.current_value_lakhs for s in stock_items), 2)

    attention: List[BusinessAttentionItem] = []
    if outstanding > 0 and outstanding > collected:
        attention.append(BusinessAttentionItem(
            severity="HIGH", title="Outstanding is high",
            detail=f"₹{outstanding:.1f} L pending collection vs ₹{collected:.1f} L collected in the period"))
    if orders > 0 and dispatch.fulfillment_pct < 80:
        attention.append(BusinessAttentionItem(
            severity="HIGH" if dispatch.fulfillment_pct < 60 else "MEDIUM", title="Dispatch below order volume",
            detail=f"{dispatch.pending_meters:,} m pending dispatch ({dispatch.fulfillment_pct}% fulfilled)"))
    for s in stock_items:
        if s.status != "NORMAL":
            attention.append(BusinessAttentionItem(
                severity="HIGH" if s.status == "CRITICAL" else "MEDIUM", title=f"{s.category} above configured limit",
                detail=f"Currently ₹{s.current_value_lakhs:.2f} L vs ₹{s.limit_value_lakhs:.2f} L limit"))
    if prev_revenue > 0 and revenue_summary.change_pct <= -5:
        attention.append(BusinessAttentionItem(
            severity="HIGH" if revenue_summary.change_pct <= -15 else "MEDIUM", title="Revenue below previous period",
            detail=f"₹{revenue:.1f} L vs ₹{prev_revenue:.1f} L ({revenue_summary.change_pct}%)"))
    attention.sort(key=lambda a: {"HIGH": 0, "MEDIUM": 1, "LOW": 2}[a.severity])

    return RevenueLossModuleResponse(
        company_name="Ashok Textiles", period=period, revenue_summary=revenue_summary, revenue_trend=trend,
        dispatch_orders=dispatch, money_position=money, stock_position=stock_items,
        business_performance=BusinessPerformanceSummary(
            revenue_lakhs=revenue, orders_meters=int(orders), dispatched_meters=int(dispatched), collected_lakhs=collected,
            outstanding_lakhs=outstanding, total_stock_lakhs=total_stock),
        needs_attention=attention)
