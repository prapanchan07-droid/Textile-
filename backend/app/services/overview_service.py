from typing import Optional
from app.db.session import SessionLocal
from app.services.template.factory_data import has_template_data
from app.services.template.overview_template import overview_from_template
from app.schemas.overview import (
    FactoryOverviewResponse,
    TimePeriod,
    ComparisonPeriod,
    PerformanceStatus,
    ExecutiveSummaryData,
    ProductionSummary,
    ProductionVariance,
    ProductionTrendItem,
    LossContributor,
    PeriodComparisonMetric,
    MachineAttentionItem,
    LowEfficiencyMachine,
    AIInsightData,
    ImpactProjectionData,
    RecommendedInvestigationData
)

class OverviewService:
    @staticmethod
    def get_factory_overview(
        period: TimePeriod = TimePeriod.TODAY,
        comparison: ComparisonPeriod = ComparisonPeriod.PREVIOUS_DAY,
        unit_id: Optional[str] = None,
        user_role: str = "SUPER_ADMIN",
        section_access: Optional[str] = None
    ) -> FactoryOverviewResponse:
        """Uses uploaded template data when present, otherwise the built-in synthetic data."""
        db = SessionLocal()
        try:
            if has_template_data(db):
                return overview_from_template(db, period, comparison, unit_id, user_role, section_access)
        finally:
            db.close()
        return OverviewService._synthetic_overview(period, comparison, unit_id, user_role, section_access)

    @staticmethod
    def _synthetic_overview(
        period: TimePeriod = TimePeriod.TODAY,
        comparison: ComparisonPeriod = ComparisonPeriod.PREVIOUS_DAY,
        unit_id: Optional[str] = None,
        user_role: str = "SUPER_ADMIN",
        section_access: Optional[str] = None
    ) -> FactoryOverviewResponse:
        
        # All Machines Dataset
        all_machines = [
            MachineAttentionItem(
                machine_id="V-09",
                machine_type="Vortex Spinning",
                section_id="Section B",
                efficiency_pct=84.2,
                loss_kg=680.0,
                downtime_minutes=240,
                change_pct=-8.4,
                status=PerformanceStatus.CRITICAL,
                primary_issue="Repeated motor trip & power fluctuation"
            ),
            MachineAttentionItem(
                machine_id="V-05",
                machine_type="Vortex Spinning",
                section_id="Section B",
                efficiency_pct=88.1,
                loss_kg=420.0,
                downtime_minutes=135,
                change_pct=-3.2,
                status=PerformanceStatus.ATTENTION,
                primary_issue="Drafting roller slippage"
            ),
            MachineAttentionItem(
                machine_id="SMX-03",
                machine_type="Simplex",
                section_id="Section A",
                efficiency_pct=90.5,
                loss_kg=290.0,
                downtime_minutes=90,
                change_pct=-1.5,
                status=PerformanceStatus.ATTENTION,
                primary_issue="Bobbin exchange delay"
            ),
            MachineAttentionItem(
                machine_id="V-12",
                machine_type="Vortex Spinning",
                section_id="Section A",
                efficiency_pct=92.4,
                loss_kg=180.0,
                downtime_minutes=45,
                change_pct=0.5,
                status=PerformanceStatus.NORMAL,
                primary_issue="Scheduled cleaning"
            ),
        ]

        # Apply RBAC Section-Level Access Filtering
        if section_access and section_access != "ALL":
            filtered_machines = [m for m in all_machines if m.section_id.lower() == section_access.lower()]
        else:
            filtered_machines = all_machines

        # Executive Summary
        executive_summary = ExecutiveSummaryData(
            factory_status="Production Below Target (-6.4%)",
            main_issue="Machine Downtime & Power Fluctuation Events",
            affected_entity="Vortex Spinning (Machine V-09 & V-05)",
            impact_kg=2380.0,
            recommended_action="Investigate repeated V-09 electrical tripping and maintenance log."
        )

        # Production Summary
        production_summary = ProductionSummary(
            target_kg=37000.0,
            actual_kg=34620.0,
            loss_kg=2380.0,
            achievement_pct=93.57,
            efficiency_pct=89.4,
            unit="kg"
        )

        # Variance
        variance = ProductionVariance(
            target_kg=37000.0,
            actual_kg=34620.0,
            variance_kg=-2380.0,
            variance_pct=-6.43,
            is_statistically_significant=True,
            display_note="Variance exceeds 5% operational alert threshold."
        )

        # Production Trend (Shift / Daily items)
        trend = [
            ProductionTrendItem(label="Shift A (06:00 - 14:00)", target_kg=12333.0, actual_kg=11950.0, loss_kg=383.0, efficiency_pct=92.1),
            ProductionTrendItem(label="Shift B (14:00 - 22:00)", target_kg=12333.0, actual_kg=11020.0, loss_kg=1313.0, efficiency_pct=84.8),
            ProductionTrendItem(label="Shift C (22:00 - 06:00)", target_kg=12334.0, actual_kg=11650.0, loss_kg=684.0, efficiency_pct=90.2),
        ]

        # Loss Contributors
        loss_contributors = [
            LossContributor(category="Machine Downtime", impact_kg=1120.0, percentage=47.1, evidence="Recorded 510 total downtime minutes across Vortex & Simplex lines."),
            LossContributor(category="Efficiency Loss", impact_kg=720.0, percentage=30.3, evidence="V-09 operated at 84.2% efficiency vs 91.6% factory baseline."),
            LossContributor(category="Power Events", impact_kg=280.0, percentage=11.8, evidence="2 voltage drop events logged at 15:42 and 18:10."),
            LossContributor(category="Maintenance", impact_kg=160.0, percentage=6.7, evidence="Scheduled drafting gear replacement extended by 40 minutes."),
            LossContributor(category="Other / Minor", impact_kg=100.0, percentage=4.1, evidence="Material changeover delays."),
        ]

        # Period Comparison Metrics
        period_comparison = [
            PeriodComparisonMetric(metric="Production Volume", current="34,620 kg", previous="36,100 kg", change_text="-1,480 kg", change_pct=-4.1, trend="down_bad"),
            PeriodComparisonMetric(metric="Factory Efficiency", current="89.4%", previous="92.6%", change_text="-3.2 % pts", change_pct=-3.45, trend="down_bad"),
            PeriodComparisonMetric(metric="Total Downtime", current="510 min", previous="398 min", change_text="+112 min", change_pct=28.1, trend="up_bad"),
            PeriodComparisonMetric(metric="Energy Consumption / kg", current="1.42 kWh/kg", previous="1.34 kWh/kg", change_text="+0.08 kWh/kg", change_pct=6.0, trend="up_bad"),
            PeriodComparisonMetric(metric="Quality Defect Rate", current="1.2%", previous="1.1%", change_text="+0.1 % pts", change_pct=9.1, trend="neutral"),
        ]

        # Low Efficiency Spotlight
        low_efficiency_spotlight = LowEfficiencyMachine(
            machine_id="V-09",
            efficiency_pct=84.2,
            factory_avg_pct=91.6,
            gap_points=-7.4,
            historical_status="Lowest 7-day rolling efficiency in Vortex section"
        )

        # AI Insight (Evidence-based, deterministic, non-speculative)
        ai_insight = AIInsightData(
            summary="Production is 4.1% below yesterday and 6.4% below daily target.",
            observations=[
                "The largest observed contributor is increased machine downtime (1,120 kg loss).",
                "Machine V-09 recorded the highest individual downtime (240 min) and lowest efficiency (84.2%).",
                "Two power fluctuation events coincided with the peak stoppage window on Shift B."
            ],
            contributors=[
                "Machine Downtime (47.1% of total loss)",
                "Sub-baseline Machine Efficiency (30.3% of total loss)",
                "Power Event Tripping (11.8% of total loss)"
            ],
            recommended_investigation=[
                "1. Review repeated electrical motor trip logs on V-09 during Shift B.",
                "2. Audit maintenance history and roller alignment on V-09 & V-05.",
                "3. Cross-reference power quality logs from the sub-station meter at 15:42 and 18:10."
            ],
            evidence_found=[
                "Downtime logs show 240 min stoppage on V-09.",
                "Power meter recorded 15% voltage sag at 15:42."
            ],
            confidence="HIGH (DETERMINISTIC EVIDENCE)"
        )

        # Impact Projection
        impact_projection = ImpactProjectionData(
            is_sufficient_data=True,
            daily_gap_kg=2380.0,
            projected_7d_gap_kg=16660.0,
            projected_30d_gap_kg=71400.0,
            assumptions_note="Linear projection based on current daily gap continuing unmitigated over 7-day and 30-day operational horizons."
        )

        # Recommended Investigation
        recommended_investigation = RecommendedInvestigationData(
            priority="HIGH",
            area="Vortex Spinning - Section B",
            machine_id="V-09",
            observed_issue="High downtime (240 min) & below-average efficiency (84.2%)",
            recommended_next_step="Review repeated downtime events and maintenance history for V-09."
        )

        return FactoryOverviewResponse(
            company_name="Ashok Textiles",
            selected_unit=unit_id or "All Units",
            selected_period=period,
            selected_comparison=comparison,
            data_frequency="DAILY",
            user_role=user_role,
            permitted_section=section_access,
            executive_summary=executive_summary,
            production_summary=production_summary,
            variance=variance,
            trend=trend,
            loss_contributors=loss_contributors,
            period_comparison=period_comparison,
            machines_requiring_attention=filtered_machines,
            low_efficiency_spotlight=low_efficiency_spotlight,
            ai_insight=ai_insight,
            impact_projection=impact_projection,
            recommended_investigation=recommended_investigation
        )
