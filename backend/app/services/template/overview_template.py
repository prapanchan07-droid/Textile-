"""Factory Overview built from uploaded template data."""
from typing import List, Optional

from sqlalchemy.orm import Session

from app.schemas.overview import (
    FactoryOverviewResponse, TimePeriod, ComparisonPeriod, PerformanceStatus, ExecutiveSummaryData,
    ProductionSummary, ProductionVariance, ProductionTrendItem, LossContributor, PeriodComparisonMetric,
    MachineAttentionItem, LowEfficiencyMachine, AIInsightData, ImpactProjectionData,
    RecommendedInvestigationData,
)
from app.services.template.factory_data import (
    Aggregate, aggregate_window, comparison_window, current_window, date_label,
    loss_breakdown, status_for_efficiency, _shift_key,
)

_PERIOD_LABEL = {
    ComparisonPeriod.PREVIOUS_SHIFT: "previous shift",
    ComparisonPeriod.PREVIOUS_DAY: "previous day",
    ComparisonPeriod.PREVIOUS_WEEK: "previous week",
    ComparisonPeriod.PREVIOUS_MONTH: "previous month",
    ComparisonPeriod.THREE_MONTH_AVG: "3-month average",
}


def _metric(name: str, cur: Optional[float], prev: Optional[float], unit: str, higher_is_better: bool,
            decimals: int = 0) -> PeriodComparisonMetric:
    def fmt(v: float) -> str:
        return f"{v:,.{decimals}f}{'' if unit == '%' else ' '}{unit}"

    if cur is None:
        return PeriodComparisonMetric(metric=name, current="Data unavailable", previous="Data unavailable",
                                      change_text="N/A", change_pct=0.0, trend="neutral")
    if prev is None:
        return PeriodComparisonMetric(metric=name, current=fmt(cur), previous="No data", change_text="N/A",
                                      change_pct=0.0, trend="neutral")
    diff = cur - prev
    pct = round(diff / prev * 100, 1) if prev else 0.0
    if abs(pct) < 0.5:
        trend = "neutral"
    elif diff > 0:
        trend = "up_good" if higher_is_better else "up_bad"
    else:
        trend = "down_good" if not higher_is_better else "down_bad"
    sign = "+" if diff > 0 else ""
    change_unit = " % pts" if unit == "%" else f" {unit}"
    return PeriodComparisonMetric(metric=name, current=fmt(cur), previous=fmt(prev),
                                  change_text=f"{sign}{diff:,.{decimals}f}{change_unit}", change_pct=pct, trend=trend)


def overview_from_template(db: Session, period: TimePeriod, comparison: ComparisonPeriod, unit_id: Optional[str],
                           user_role: str, section_access: Optional[str]) -> FactoryOverviewResponse:
    w = current_window(db, period.value)
    cur = aggregate_window(db, w, unit_id, section_access) or Aggregate({}, 0, [])
    prev = aggregate_window(db, comparison_window(db, w, comparison.value), unit_id, section_access,
                            scale_days=max(cur.n_days, 1))

    target, actual, loss = round(cur.target, 1), round(cur.actual, 1), round(cur.loss, 1)
    variance_kg = round(actual - target, 1)
    variance_pct = round(variance_kg / target * 100, 2) if target > 0 else 0.0
    ranked = cur.ranked_by_loss()
    top = ranked[0] if ranked else None
    breakdown = loss_breakdown(cur) if cur.machines else []
    prev_label = _PERIOD_LABEL.get(comparison, "previous period")

    # ---- executive summary
    if target <= 0:
        status_text = "No production data for the selected period"
    elif variance_kg >= 0:
        status_text = f"Production On Target (+{variance_pct:.1f}%)"
    else:
        status_text = f"Production Below Target ({variance_pct:.1f}%)"
    affected = "N/A"
    if top and loss > 0:
        others = [m.machine_id for m in ranked[1:2] if m.loss > 0]
        affected = f"{top.machine_type} (Machine {' & '.join([top.machine_id] + others)})"
    executive_summary = ExecutiveSummaryData(
        factory_status=status_text,
        main_issue=breakdown[0].category if breakdown else "No production loss recorded",
        affected_entity=affected,
        impact_kg=loss,
        recommended_action=f"Investigate {top.machine_id}: {top.main_issue}." if top and loss > 0
        else "Maintain current performance.",
    )

    production_summary = ProductionSummary(
        target_kg=target, actual_kg=actual, loss_kg=loss, achievement_pct=cur.achievement,
        efficiency_pct=cur.avg_efficiency, unit="kg")
    variance = ProductionVariance(
        target_kg=target, actual_kg=actual, variance_kg=variance_kg, variance_pct=variance_pct,
        is_statistically_significant=abs(variance_pct) > 5.0,
        display_note="Variance exceeds 5% operational alert threshold." if abs(variance_pct) > 5.0
        else "Variance is within the 5% operational tolerance.")

    # ---- trend: by shift for a single day, otherwise by date
    groups = {}
    single_day = bool(w) and w.start == w.end
    for r in cur.rows:
        key = (r.shift or "Full Day") if single_day else r.report_date
        g = groups.setdefault(key, [0.0, 0.0])
        g[0] += r.target_kg
        g[1] += r.actual_kg
    keys = sorted(groups, key=(lambda k: _shift_key(k)) if single_day else (lambda k: k))
    trend: List[ProductionTrendItem] = []
    for k in keys:
        t, a = groups[k]
        trend.append(ProductionTrendItem(
            label=k if single_day else date_label(k), target_kg=round(t, 1), actual_kg=round(a, 1),
            loss_kg=round(max(0.0, t - a), 1), efficiency_pct=round(a / t * 100, 1) if t > 0 else 0.0))

    # ---- loss contributors
    contributors: List[LossContributor] = []
    for c in breakdown:
        if c.category == "Efficiency Loss":
            evidence = f"Below-target output on {len(c.machine_ids)} machine(s) beyond recorded downtime."
        else:
            evidence = f"{c.minutes:.0f} min downtime across {len(c.machine_ids)} machine(s)."
            if c.events:
                evidence += f" {c.events} power event(s) logged."
        contributors.append(LossContributor(category=c.category, impact_kg=c.kg, percentage=c.percentage, evidence=evidence))

    # ---- comparison with the selected reference period
    period_comparison = [
        _metric("Production Volume", cur.actual, prev.actual if prev else None, "kg", True),
        _metric("Factory Efficiency", cur.avg_efficiency, prev.avg_efficiency if prev else None, "%", True, 1),
        _metric("Total Downtime", cur.downtime_min, prev.downtime_min if prev else None, "min", False),
        _metric("Energy Consumption / kg", cur.energy_per_kg, prev.energy_per_kg if prev else None, "kWh/kg", False, 2),
        _metric("Quality Rating", cur.quality, prev.quality if prev else None, "%", True, 1),
    ]

    # ---- machines needing attention
    machines: List[MachineAttentionItem] = []
    for m in ranked[:4]:
        pm = prev.machines.get(m.machine_id) if prev else None
        machines.append(MachineAttentionItem(
            machine_id=m.machine_id, machine_type=m.machine_type, section_id=m.section, efficiency_pct=m.efficiency,
            loss_kg=round(m.loss, 1), downtime_minutes=int(round(m.downtime_min)),
            change_pct=round(m.efficiency - pm.efficiency, 1) if pm else 0.0,
            status=PerformanceStatus(status_for_efficiency(m.efficiency)), primary_issue=m.main_issue))

    with_target = [m for m in cur.machines.values() if m.target > 0]
    lowest = min(with_target, key=lambda m: m.efficiency) if with_target else None
    if lowest:
        low_spot = LowEfficiencyMachine(
            machine_id=lowest.machine_id, efficiency_pct=lowest.efficiency, factory_avg_pct=cur.avg_efficiency,
            gap_points=round(lowest.efficiency - cur.avg_efficiency, 1),
            historical_status=f"Lowest efficiency among {len(with_target)} machine(s) in the selected period")
    else:
        low_spot = LowEfficiencyMachine(machine_id="N/A", efficiency_pct=0.0, factory_avg_pct=0.0, gap_points=0.0,
                                        historical_status="No machine data for the selected period")

    # ---- AI insight (deterministic, evidence-based)
    if target > 0:
        direction = "below" if variance_kg < 0 else "above"
        summary = f"Production is {abs(variance_pct):.1f}% {direction} target"
        if prev and prev.actual > 0:
            chg = (cur.actual - prev.actual) / prev.actual * 100
            summary += f" and {abs(chg):.1f}% {'below' if chg < 0 else 'above'} the {prev_label}."
        else:
            summary += "."
    else:
        summary = "No production data is available for the selected period."
    observations: List[str] = []
    if breakdown and loss > 0:
        observations.append(f"The largest observed contributor is {breakdown[0].category} ({breakdown[0].kg:,.0f} kg loss).")
    if top and loss > 0:
        observations.append(f"Machine {top.machine_id} recorded {top.downtime_min:.0f} min downtime at {top.efficiency}% efficiency.")
    if cur.power_events:
        observations.append(f"{cur.power_events} power event(s) were logged in the selected period.")
    evidence_found = [f"{m.machine_id}: {m.downtime_min:.0f} min downtime, {m.efficiency}% efficiency." for m in ranked[:2] if m.loss > 0]
    steps = []
    if top and loss > 0:
        steps.append(f"1. Review '{top.main_issue}' on {top.machine_id} ({top.section}).")
        steps.append(f"2. Audit maintenance history of {top.machine_id}"
                     + (f" (last serviced {top.last_maintenance})." if top.last_maintenance else "."))
        if cur.power_events:
            steps.append("3. Cross-check power quality logs against the recorded power events.")
    ai_insight = AIInsightData(
        summary=summary, observations=observations,
        contributors=[f"{c.category} ({c.percentage}% of total loss)" for c in breakdown[:3]],
        recommended_investigation=steps, evidence_found=evidence_found,
        confidence="HIGH (UPLOADED TEMPLATE DATA)")

    # ---- projection & investigation
    n_days = max(cur.n_days, 1)
    daily_gap = round(loss / n_days, 1)
    impact = ImpactProjectionData(
        is_sufficient_data=loss > 0, daily_gap_kg=daily_gap, projected_7d_gap_kg=round(daily_gap * 7, 1),
        projected_30d_gap_kg=round(daily_gap * 30, 1),
        assumptions_note="Linear projection based on the average daily gap in the selected period continuing unmitigated.",
        insufficient_data_reason=None if loss > 0 else "No production shortfall recorded in the selected period.")
    if top and loss > 0:
        rec = RecommendedInvestigationData(
            priority="HIGH" if status_for_efficiency(top.efficiency) == "CRITICAL" else "MEDIUM",
            area=f"{top.machine_type} - {top.section}", machine_id=top.machine_id,
            observed_issue=f"{top.downtime_min:.0f} min downtime & {top.efficiency}% efficiency",
            recommended_next_step=f"Review downtime events and maintenance history for {top.machine_id}.")
    else:
        rec = RecommendedInvestigationData(priority="LOW", area="N/A", machine_id="N/A",
                                           observed_issue="No shortfall detected", recommended_next_step="No action required.")

    return FactoryOverviewResponse(
        company_name="Ashok Textiles", selected_unit=unit_id or "All Units", selected_period=period,
        selected_comparison=comparison, data_frequency="DAILY", user_role=user_role, permitted_section=section_access,
        executive_summary=executive_summary, production_summary=production_summary, variance=variance,
        trend=trend, loss_contributors=contributors, period_comparison=period_comparison,
        machines_requiring_attention=machines, low_efficiency_spotlight=low_spot, ai_insight=ai_insight,
        impact_projection=impact, recommended_investigation=rec)
