"""Decision Center built from uploaded template data."""
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.template_data import ActionItemRecord
from app.schemas.decision_center import (
    DecisionCenterData, TopPriorityData, WhyContributor, WhereLocationData, SecondaryMachineContributor,
    RecommendedAction, IfContinuesData, OtherIssueItem, ActionTrackerItem, AIInsightData,
)
from app.services.template.factory_data import (
    Aggregate, aggregate_window, comparison_window, current_window, has_business_data, loss_breakdown,
    status_for_efficiency,
)
from app.services.template.manpower_quality_template import manpower_by_date, quality_snapshot
from app.services.template.revenue_template import revenue_from_template

_PERIOD_WORD = {"TODAY": "Today's", "YESTERDAY": "Yesterday's", "SHIFT": "This shift's",
                "THIS_WEEK": "This week's", "THIS_MONTH": "This month's"}
_PERIOD_SUFFIX = {"THIS_WEEK": " (Week)", "THIS_MONTH": " (Month)", "SHIFT": " (Shift)"}
_STATUS_BADGE = {"OPEN": "🔴 OPEN", "IN_PROGRESS": "🟠 IN PROGRESS", "COMPLETED": "🟢 COMPLETED"}
_STATUS_LABEL = {"CRITICAL": "🔴 Critical", "ATTENTION": "🟠 Attention", "NORMAL": "🟢 Normal"}
_STATUS_COLOR = {"CRITICAL": "RED", "ATTENTION": "ORANGE", "NORMAL": "YELLOW"}


def decision_center_from_template(db: Session, period: str, comparison: str, unit: str, user_role: str,
                                  section_access: str) -> DecisionCenterData:
    p = period.upper()
    section = None if not section_access or section_access == "ALL" else section_access
    w = current_window(db, p)
    cur = aggregate_window(db, w, unit, section) or Aggregate({}, 0, [])
    prev = aggregate_window(db, comparison_window(db, w, comparison), unit, section, scale_days=max(cur.n_days, 1))

    target, actual, loss = round(cur.target, 1), round(cur.actual, 1), round(cur.loss, 1)
    ranked = [m for m in cur.ranked_by_loss() if m.loss > 0]
    top = ranked[0] if ranked else None
    breakdown = loss_breakdown(cur) if cur.machines else []
    n_days = max(cur.n_days, 1)
    daily_gap = loss / n_days
    ach = cur.achievement

    # ---- top priority
    if loss <= 0:
        level, badge, title = "MEDIUM", "🟡 MONITOR", "Production is on target"
    elif ach < 85:
        level, badge, title = "CRITICAL", "🔴 CRITICAL PRIORITY", "Production is well below target"
    elif ach < 95:
        level, badge, title = "HIGH", "🔴 HIGH PRIORITY", "Production is below target"
    else:
        level, badge, title = "MEDIUM", "🟡 MEDIUM PRIORITY", "Production is slightly below target"
    top_priority = TopPriorityData(
        priority_level=level, badge_label=badge, title=title,
        sub_highlight=f"Short by {loss:,.0f} kg{_PERIOD_SUFFIX.get(p, '')}" if loss > 0 else "No production shortfall",
        main_contributor=breakdown[0].category if breakdown else "None",
        most_affected_machine_type=top.machine_type if top else "N/A",
        most_affected_machine_id=top.machine_id if top else "N/A",
        actual_kg=actual, target_kg=target, gap_kg=round(actual - target, 1), target_tab="production")

    # ---- why / where
    colors = ["RED", "ORANGE", "YELLOW"]
    why = [WhyContributor(category=c.category, percentage=c.percentage, status_color=colors[i],
                          detail_text=f"{c.percentage:.0f}% of total production gap attributable to {c.category.lower()}")
           for i, c in enumerate(breakdown[:3])]
    if top:
        st = status_for_efficiency(top.efficiency)
        where = WhereLocationData(
            primary_machine_id=top.machine_id, primary_machine_type=top.machine_type, primary_section=top.section,
            production_loss_kg=-round(top.loss, 1), efficiency_pct=top.efficiency,
            downtime_minutes=int(round(top.downtime_min)), status=_STATUS_LABEL[st],
            secondary_machines=[
                SecondaryMachineContributor(machine_id=m.machine_id, machine_type=m.machine_type,
                                            loss_kg=-round(m.loss, 1), status_color=_STATUS_COLOR[status_for_efficiency(m.efficiency)])
                for m in ranked[1:3]])
    else:
        where = WhereLocationData(primary_machine_id="N/A", primary_machine_type="N/A", primary_section="N/A",
                                  production_loss_kg=0.0, efficiency_pct=0.0, downtime_minutes=0,
                                  status="🟢 Normal", secondary_machines=[])

    # ---- recommended actions
    if top:
        actions = [RecommendedAction(id="rec-1", step_number=1,
                                     action_text=f"Investigate '{top.main_issue}' on {top.machine_id}",
                                     button_label="View Machine", target_tab="machines", target_id=top.machine_id)]
        if cur.power_events:
            actions.append(RecommendedAction(id="rec-2", step_number=2,
                                             action_text="Check power fluctuation events during affected shifts",
                                             button_label="View Power", target_tab="overview", target_id="power-events"))
        elif breakdown:
            actions.append(RecommendedAction(id="rec-2", step_number=2,
                                             action_text=f"Address {breakdown[0].category.lower()} across {len(breakdown[0].machine_ids)} machine(s)",
                                             button_label="View Production", target_tab="production", target_id=None))
        actions.append(RecommendedAction(id=f"rec-{len(actions) + 1}", step_number=len(actions) + 1,
                                         action_text=f"Review recent maintenance history of {top.machine_id}",
                                         button_label="View Maintenance", target_tab="machines", target_id=top.machine_id))
    else:
        actions = [RecommendedAction(id="rec-1", step_number=1, action_text="No corrective action required. Keep monitoring.",
                                     button_label="View Production", target_tab="production", target_id=None)]

    if_continues = IfContinuesData(
        current_daily_gap_kg=-round(daily_gap, 1), projected_7d_gap_kg=-round(daily_gap * 7, 1),
        projected_30d_gap_kg=-round(daily_gap * 30, 1), label="Estimated production impact",
        disclaimer_note="Projection assumes the current daily gap continues.")

    # ---- other issues
    issues: List[OtherIssueItem] = []
    mp = manpower_by_date(db)
    if mp:
        latest = mp[sorted(mp)[-1]]
        worst = min(latest.items(), key=lambda kv: kv[1][1] - kv[1][0])
        short = worst[1][0] - worst[1][1]
        if short > 0:
            issues.append(OtherIssueItem(id="issue-mp", status_icon="🟠", category="Manpower shortage",
                                         location_or_area=f"{worst[0]} Department",
                                         impact_detail=f"-{short} workers below sanctioned strength", target_tab="manpower"))
    if cur.energy_per_kg and prev and prev.energy_per_kg:
        chg = (cur.energy_per_kg - prev.energy_per_kg) / prev.energy_per_kg * 100
        if chg > 3:
            issues.append(OtherIssueItem(id="issue-energy", status_icon="🟠", category="Energy consumption",
                                         location_or_area="Factory Power Grid",
                                         impact_detail=f"Higher than the comparison period (+{chg:.0f}% kWh/kg)", target_tab="overview"))
    bad_quality = [q for q in quality_snapshot(db) if q.status == "OUT OF LIMIT"]
    if bad_quality:
        q = bad_quality[0]
        issues.append(OtherIssueItem(id="issue-quality", status_icon="🟡", category="Quality deviation",
                                     location_or_area="Yarn Quality Lab",
                                     impact_detail=f"{q.parameter} above limit ({q.value:g} vs {q.limit:g})", target_tab="manpower"))
    if has_business_data(db):
        money = revenue_from_template(db, "THIS_MONTH").money_position
        if money.outstanding_lakhs > money.collected_lakhs:
            issues.append(OtherIssueItem(id="issue-ar", status_icon="🟠", category="Accounts Receivable",
                                         location_or_area="Finance & Sales",
                                         impact_detail=f"₹{money.outstanding_lakhs:.1f} L outstanding vs ₹{money.collected_lakhs:.1f} L collected",
                                         target_tab="revenue"))

    tracker = [
        ActionTrackerItem(id=f"act-{i + 1}", issue=a.issue, action=a.action, owner=a.owner or "Unassigned",
                          status=a.status, status_badge=_STATUS_BADGE.get(a.status, a.status), created_date=a.report_date)
        for i, a in enumerate(db.query(ActionItemRecord).order_by(ActionItemRecord.report_date.desc()).limit(10).all())
    ]

    # ---- AI insight (deterministic)
    word = _PERIOD_WORD.get(p, "Today's")
    facts = [f"Actual production achieved: {actual:,.0f} kg vs {target:,.0f} kg target ({ach - 100:+.1f}%)."] if target > 0 else []
    if top:
        facts.append(f"Machine {top.machine_id} logged {top.downtime_min:.0f} minutes of downtime (-{top.loss:,.0f} kg loss).")
    if cur.power_events:
        facts.append(f"{cur.power_events} power event(s) were recorded in the selected period.")
    if top and loss > 0:
        summary = (f"{word} production is {loss:,.0f} kg below target. The largest observed contributor is "
                   f"{breakdown[0].category.lower()}, with {top.machine_id} showing the highest individual loss.")
        focus = f"Recommended focus: investigate {top.machine_id} ({top.main_issue})."
    else:
        summary = f"{word} production is on target." if target > 0 else "No production data is available for the selected period."
        focus = "Recommended focus: maintain current performance."
    ai_insight = AIInsightData(
        summary_paragraph=summary, recommended_focus=focus, evidence_confidence="HIGH", facts=facts,
        projections=[f"Unmitigated daily gap of {daily_gap:,.0f} kg leads to an estimated {daily_gap * 7:,.0f} kg gap over 7 days."]
        if loss > 0 else [])

    return DecisionCenterData(
        company_name="Ashok Textiles", selected_unit=unit, selected_period=period, user_role=user_role,
        permitted_section=section, top_priority=top_priority, why_contributors=why, where_location=where,
        recommended_actions=actions, if_continues=if_continues, other_issues=issues, action_tracker=tracker,
        ai_insight=ai_insight)
