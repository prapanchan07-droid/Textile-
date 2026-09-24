from typing import Optional
from app.db.session import SessionLocal
from app.services.template.factory_data import has_template_data
from app.services.template.decision_template import decision_center_from_template
from app.schemas.decision_center import (
    DecisionCenterData,
    TopPriorityData,
    WhyContributor,
    WhereLocationData,
    SecondaryMachineContributor,
    RecommendedAction,
    IfContinuesData,
    OtherIssueItem,
    ActionTrackerItem,
    AIInsightData,
)

class DecisionCenterService:
    @staticmethod
    def get_decision_center(
        period: str = "TODAY",
        comparison: str = "PREVIOUS_DAY",
        unit: str = "All Units",
        user_role: str = "SUPER_ADMIN",
        section_access: str = "ALL"
    ) -> DecisionCenterData:
        """Uses uploaded template data when present, otherwise the built-in synthetic data."""
        db = SessionLocal()
        try:
            if has_template_data(db):
                return decision_center_from_template(db, period, comparison, unit, user_role, section_access)
        finally:
            db.close()
        return DecisionCenterService._synthetic_decision_center(period, comparison, unit, user_role, section_access)

    @staticmethod
    def _synthetic_decision_center(
        period: str = "TODAY",
        comparison: str = "PREVIOUS_DAY",
        unit: str = "All Units",
        user_role: str = "SUPER_ADMIN",
        section_access: str = "ALL"
    ) -> DecisionCenterData:
        
        # Scaling multiplier based on selected period
        period_upper = period.upper()
        if period_upper in ["THIS_WEEK", "WEEK"]:
            multiplier = 7.0
            daily_gap = 2380.0
            target_kg = 259000.0
            actual_kg = 242340.0
            gap_kg = -16660.0
            sub_text = "Short by 16,660 kg (Week)"
        elif period_upper in ["THIS_MONTH", "MONTH"]:
            multiplier = 30.0
            daily_gap = 2380.0
            target_kg = 1110000.0
            actual_kg = 1038600.0
            gap_kg = -71400.0
            sub_text = "Short by 71,400 kg (Month)"
        elif period_upper == "SHIFT":
            multiplier = 0.33
            daily_gap = 2380.0
            target_kg = 12333.0
            actual_kg = 11540.0
            gap_kg = -793.0
            sub_text = "Short by 793 kg (Shift)"
        else:
            # TODAY / YESTERDAY
            multiplier = 1.0
            daily_gap = 2380.0
            target_kg = 37000.0
            actual_kg = 34620.0
            gap_kg = -2380.0
            sub_text = "Short by 2,380 kg"

        top_priority = TopPriorityData(
            priority_level="HIGH",
            badge_label="🔴 HIGH PRIORITY",
            title="Production is below target",
            sub_highlight=sub_text,
            main_contributor="Machine downtime",
            most_affected_machine_type="Vortex",
            most_affected_machine_id="V-09",
            actual_kg=actual_kg,
            target_kg=target_kg,
            gap_kg=gap_kg,
            target_tab="production"
        )

        why_contributors = [
            WhyContributor(
                category="Machine Downtime",
                percentage=47.0,
                status_color="RED",
                detail_text="47% of total production gap attributable to unscheduled stops"
            ),
            WhyContributor(
                category="Efficiency Loss",
                percentage=30.0,
                status_color="ORANGE",
                detail_text="30% due to speed drops and yarn breakage delays"
            ),
            WhyContributor(
                category="Power Events",
                percentage=12.0,
                status_color="YELLOW",
                detail_text="12% linked to brief voltage fluctuations during shift 2"
            )
        ]

        where_location = WhereLocationData(
            primary_machine_id="V-09",
            primary_machine_type="Vortex Spinning",
            primary_section="Spinning Unit 1",
            production_loss_kg=-680.0 * (multiplier if multiplier < 5 else 1.0),
            efficiency_pct=84.2,
            downtime_minutes=240,
            status="🔴 Critical",
            secondary_machines=[
                SecondaryMachineContributor(
                    machine_id="V-05",
                    machine_type="Vortex",
                    loss_kg=-420.0 * (multiplier if multiplier < 5 else 1.0),
                    status_color="ORANGE"
                ),
                SecondaryMachineContributor(
                    machine_id="SMX-03",
                    machine_type="Airjet Spinning",
                    loss_kg=-290.0 * (multiplier if multiplier < 5 else 1.0),
                    status_color="ORANGE"
                )
            ]
        )

        recommended_actions = [
            RecommendedAction(
                id="rec-1",
                step_number=1,
                action_text="Investigate repeated downtime on V-09",
                button_label="View Machine",
                target_tab="machines",
                target_id="V-09"
            ),
            RecommendedAction(
                id="rec-2",
                step_number=2,
                action_text="Check power fluctuation events during affected shifts",
                button_label="View Power",
                target_tab="overview",
                target_id="power-events"
            ),
            RecommendedAction(
                id="rec-3",
                step_number=3,
                action_text="Review recent maintenance history of V-09",
                button_label="View Maintenance",
                target_tab="machines",
                target_id="maintenance-v09"
            )
        ]

        if_continues = IfContinuesData(
            current_daily_gap_kg=-daily_gap,
            projected_7d_gap_kg=-(daily_gap * 7.0),
            projected_30d_gap_kg=-(daily_gap * 30.0),
            label="Estimated production impact",
            disclaimer_note="Projection assumes the current daily gap continues."
        )

        other_issues = [
            OtherIssueItem(
                id="issue-1",
                status_icon="🟠",
                category="Manpower shortage",
                location_or_area="Spinning Department",
                impact_detail="-30 workers below sanctioned strength",
                target_tab="manpower"
            ),
            OtherIssueItem(
                id="issue-2",
                status_icon="🟠",
                category="Energy consumption",
                location_or_area="Factory Power Grid",
                impact_detail="Higher than normal (+8% kWh/kg)",
                target_tab="overview"
            ),
            OtherIssueItem(
                id="issue-3",
                status_icon="🟡",
                category="Quality deviation",
                location_or_area="Yarn Quality Lab",
                impact_detail="Thick places increasing on 40s Combed",
                target_tab="manpower"
            ),
            OtherIssueItem(
                id="issue-4",
                status_icon="🟠",
                category="Accounts Receivable",
                location_or_area="Finance & Sales",
                impact_detail="2 Accounts Overdue >60 days (₹14.5 Lakh)",
                target_tab="revenue"
            )
        ]

        action_tracker = [
            ActionTrackerItem(
                id="act-101",
                issue="V-09 downtime",
                action="Check motor alignment + power fluctuation events",
                owner="Maintenance Manager",
                status="OPEN",
                status_badge="🔴 OPEN",
                created_date="2026-09-23"
            ),
            ActionTrackerItem(
                id="act-102",
                issue="Power fluctuation",
                action="Inspect transformer sub-station & main breaker",
                owner="Electrical Team",
                status="IN_PROGRESS",
                status_badge="🟠 IN PROGRESS",
                created_date="2026-09-22"
            ),
            ActionTrackerItem(
                id="act-103",
                issue="Spinning shift 2 absenteeism",
                action="Deploy pool contract workers to Spinning Unit 1",
                owner="HR & Manpower Head",
                status="COMPLETED",
                status_badge="🟢 COMPLETED",
                created_date="2026-09-21"
            )
        ]

        ai_insight = AIInsightData(
            summary_paragraph="Today's production is 2,380 kg below target. The largest observed contributor is machine downtime, with V-09 showing the highest individual loss and downtime. Repeated power events coincided with the affected operational period.",
            recommended_focus="Recommended focus: investigate V-09 downtime and related power events.",
            evidence_confidence="HIGH",
            facts=[
                "Actual production achieved: 34,620 kg vs 37,000 kg target (-6.4%).",
                "Machine V-09 logged 240 minutes of unscheduled downtime (-680 kg loss).",
                "Voltage trip events registered at 14:15 and 16:40 during Shift 2."
            ],
            projections=[
                "Unmitigated daily gap of 2,380 kg leads to an estimated 16,660 kg gap over 7 days."
            ]
        )

        return DecisionCenterData(
            company_name="Ashok Textiles",
            selected_unit=unit,
            selected_period=period,
            user_role=user_role,
            permitted_section=section_access if section_access != "ALL" else None,
            top_priority=top_priority,
            why_contributors=why_contributors,
            where_location=where_location,
            recommended_actions=recommended_actions,
            if_continues=if_continues,
            other_issues=other_issues,
            action_tracker=action_tracker,
            ai_insight=ai_insight
        )

decision_center_service = DecisionCenterService()
