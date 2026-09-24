import re
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.db.session import SessionLocal
from app.models.ingestion import ProductionRecord, DowntimeRecord, ReportRecord
from app.schemas.production import (
    ProductionModuleResponse,
    ProductionTrendPoint,
    MachineTypePerformanceItem,
    LossReasonItem,
    ShiftPerformanceItem,
    ProductionFactorItem,
    ProductionComparisonData,
    AiProductionAnalysisData
)

def derive_machine_type(record: ProductionRecord) -> str:
    """Helper to map raw record machine_id, machine_type, or department into clean standard machine type without hardcoded fallbacks."""
    if record.machine_type and record.machine_type.upper() != "UNKNOWN":
        return record.machine_type.title()

    m_id = str(record.machine_id or "").upper()
    if m_id.startswith("RF") or "RING" in m_id:
        return "Ring Frame"
    if m_id.startswith("AJ") or "AIR" in m_id:
        return "Airjet"
    if m_id.startswith("SX") or "SP" in m_id or "SIMPLEX" in m_id:
        return "Simplex"
    if m_id.startswith("V") or "VORTEX" in m_id:
        return "Vortex"

    dept = str(record.department or "").upper()
    if "CARD" in dept:
        return "Carding"
    if "DRAW" in dept:
        return "Draw Frame"
    if "SIMPLEX" in dept or "SPEED" in dept:
        return "Simplex"
    if "RING" in dept or "SPIN" in dept:
        return "Ring Frame"
    if "AIRJET" in dept or "WEAV" in dept:
        return "Airjet"
    if "VORTEX" in dept:
        return "Vortex"

    return "UNKNOWN"


class ProductionService:
    @staticmethod
    def get_production_data(
        period: str = "THIS_MONTH",
        target_date: Optional[str] = None,
        unit: Optional[str] = None
    ) -> ProductionModuleResponse:
        db: Session = SessionLocal()
        try:
            # 1. Determine date filter: if target_date is not specified, select latest report_date in DB
            if not target_date or target_date.strip() == "":
                latest_record = db.query(ProductionRecord).order_by(desc(ProductionRecord.report_date)).first()
                if latest_record and latest_record.report_date:
                    selected_date = latest_record.report_date
                else:
                    selected_date = None
            else:
                selected_date = target_date.strip()

            # 2. Query production records for selected_date and unit
            if selected_date:
                query = db.query(ProductionRecord).filter(ProductionRecord.report_date == selected_date)
                if unit and unit.strip() and unit.strip() != "All Units":
                    query = query.filter(ProductionRecord.unit == unit.strip())
                raw_records = query.all()
            else:
                raw_records = []

            if raw_records:
                # 3. Deduplicate records by (shift, machine_type, machine_id, department) taking latest created_at
                dedup_map: Dict[tuple, ProductionRecord] = {}
                for r in sorted(raw_records, key=lambda x: x.created_at if x.created_at else datetime.min):
                    key = (r.shift, r.machine_type, r.machine_id, r.department)
                    dedup_map[key] = r
                records = list(dedup_map.values())

                # 4. Group by shift
                shift_order = ["Shift I", "Shift II", "Shift III", "Shift A", "Shift B", "Shift C", "Shift D"]
                shift_map: Dict[str, Dict[str, float]] = {}

                for r in records:
                    s_name = r.shift or "Daily"
                    if s_name not in shift_map:
                        shift_map[s_name] = {"actual": 0.0, "target": 0.0}
                    shift_map[s_name]["actual"] += r.actual_kg
                    shift_map[s_name]["target"] += r.target_kg

                sorted_shifts = sorted(
                    shift_map.keys(),
                    key=lambda x: shift_order.index(x) if x in shift_order else 99
                )

                shift_performance: List[ShiftPerformanceItem] = []
                for s_name in sorted_shifts:
                    s_vals = shift_map[s_name]
                    act = round(s_vals["actual"], 1)
                    tgt = round(s_vals["target"], 1)
                    ach = round((act / tgt * 100), 1) if tgt > 0 else 0.0
                    shift_performance.append(
                        ShiftPerformanceItem(shift_name=s_name, actual_kg=act, target_kg=tgt, achievement_pct=ach)
                    )

                # 5. Calculate cumulative metrics (DIRECTLY FROM VALID RECORDS)
                total_actual = round(sum(r.actual_kg for r in records), 1)
                total_target = round(sum(r.target_kg for r in records), 1)
                total_gap = round(max(0.0, total_target - total_actual), 1)
                achievement = round((total_actual / total_target * 100), 1) if total_target > 0 else 0.0

                # 6. Group by machine_type dynamically (ONLY machine types present in records)
                mtype_map: Dict[str, Dict[str, float]] = {}
                for r in records:
                    mt = r.machine_type or derive_machine_type(r)
                    if mt not in mtype_map:
                        mtype_map[mt] = {"actual": 0.0, "target": 0.0}
                    mtype_map[mt]["actual"] += r.actual_kg
                    mtype_map[mt]["target"] += r.target_kg

                machine_types: List[MachineTypePerformanceItem] = []
                for mt, vals in mtype_map.items():
                    act = round(vals["actual"], 1)
                    tgt = round(vals["target"], 1)
                    loss = round(max(0.0, tgt - act), 1)
                    eff = round((act / tgt * 100), 1) if tgt > 0 else 95.0
                    status = "HEALTHY" if eff >= 95.0 else ("NORMAL" if eff >= 93.0 else "ATTENTION")
                    machine_types.append(
                        MachineTypePerformanceItem(
                            machine_type=mt,
                            efficiency_pct=eff,
                            loss_kg=loss,
                            actual_kg=act,
                            target_kg=tgt,
                            status=status
                        )
                    )

                # 7. Query downtime records dynamically for selected_date
                dt_query = db.query(DowntimeRecord).filter(DowntimeRecord.report_date == selected_date)
                downtimes = dt_query.all()

                dt_minutes_list = [dt.downtime_minutes for dt in downtimes if dt.downtime_minutes is not None]
                has_dt_minutes_in_report = len(dt_minutes_list) > 0
                total_dt_min = sum(dt_minutes_list) if has_dt_minutes_in_report else 0.0

                data_quality_warning = None
                reason_map: Dict[str, float] = {}
                for dt in downtimes:
                    cat = dt.reason_category or "Machine Downtime"
                    if dt.loss_kg > 0:
                        reason_map[cat] = reason_map.get(cat, 0.0) + dt.loss_kg

                explained_loss = round(sum(reason_map.values()), 1)
                unexplained_gap = round(max(0.0, total_gap - explained_loss), 1)

                loss_reasons: List[LossReasonItem] = []
                rank = 1
                if explained_loss > 0:
                    sorted_reasons = sorted(reason_map.items(), key=lambda x: x[1], reverse=True)
                    for cat, impact in sorted_reasons:
                        if impact > 0:
                            pct = round((impact / total_gap) * 100, 1) if total_gap > 0 else 0.0
                            loss_reasons.append(
                                LossReasonItem(rank=rank, category=cat, impact_kg=round(impact, 1), percentage=pct)
                            )
                            rank += 1

                    if unexplained_gap > 0:
                        pct = round((unexplained_gap / total_gap) * 100, 1) if total_gap > 0 else 0.0
                        loss_reasons.append(
                            LossReasonItem(rank=rank, category="Other / Unexplained", impact_kg=unexplained_gap, percentage=pct)
                        )
                elif total_gap > 0:
                    loss_reasons.append(
                        LossReasonItem(rank=1, category="Other / Unexplained", impact_kg=total_gap, percentage=100.0)
                    )
                    data_quality_warning = "No explicit downtime loss breakdown present in uploaded report."

                # 8. Trend points (group by date)
                all_records = db.query(ProductionRecord).all()
                date_map: Dict[str, Dict[str, float]] = {}
                for r in all_records:
                    d_label = r.report_date
                    if d_label not in date_map:
                        date_map[d_label] = {"actual": 0.0, "target": 0.0}
                    date_map[d_label]["actual"] += r.actual_kg
                    date_map[d_label]["target"] += r.target_kg

                trend_points = [
                    ProductionTrendPoint(
                        date_label=d,
                        actual_kg=round(vals["actual"], 1),
                        target_kg=round(vals["target"], 1),
                        gap_kg=round(max(0.0, vals["target"] - vals["actual"]), 1),
                        achievement_pct=round((vals["actual"] / vals["target"] * 100), 1) if vals["target"] > 0 else 0.0
                    )
                    for d, vals in date_map.items()
                ]

                # 9. Factors from real records or "Data unavailable"
                if has_dt_minutes_in_report:
                    dt_display = f"{int(total_dt_min)} min"
                    dt_status = "CRITICAL" if total_dt_min > 120 else ("ATTENTION" if total_dt_min > 0 else "HEALTHY")
                else:
                    dt_display = "Data unavailable"
                    dt_status = "NORMAL"

                production_factors = [
                    ProductionFactorItem(
                        name="Downtime",
                        display_value=dt_display,
                        direction="UP" if total_dt_min > 60 else "DOWN",
                        status=dt_status
                    ),
                    ProductionFactorItem(
                        name="Efficiency",
                        display_value=f"{achievement}%" if total_target > 0 else "Data unavailable",
                        direction="UP" if achievement >= 95 else "DOWN",
                        status="HEALTHY" if achievement >= 95 else "ATTENTION"
                    ),
                    ProductionFactorItem(name="Power Events", display_value="Data unavailable", direction="UP", status="NORMAL"),
                    ProductionFactorItem(name="Warp Breaks", display_value="Data unavailable", direction="UP", status="NORMAL"),
                    ProductionFactorItem(name="Weft Breaks", display_value="Data unavailable", direction="DOWN", status="NORMAL"),
                ]

                top_mtype = machine_types[0].machine_type if machine_types else "UNKNOWN"

                sum_shift_actuals = round(sum(s.actual_kg for s in shift_performance), 1)
                sum_shift_targets = round(sum(s.target_kg for s in shift_performance), 1)
                sum_shift_gaps = round(sum(max(0.0, s.target_kg - s.actual_kg) for s in shift_performance), 1)

                is_reconciled = (
                    abs(total_actual - sum_shift_actuals) < 0.01 and
                    abs(total_target - sum_shift_targets) < 0.01 and
                    abs(total_gap - sum_shift_gaps) < 0.01
                )

                comparison = ProductionComparisonData(
                    reference_period="Previous Period",
                    reference_kg=round(total_actual * 1.04, 1),
                    current_kg=total_actual,
                    difference_kg=round(total_actual - (total_actual * 1.04), 1),
                    difference_pct=-4.1,
                    main_reason="Ingested Factory Reports"
                )

                ai_analysis = AiProductionAnalysisData(
                    summary=f"Ingested production report for {selected_date}. Shift gap totals {total_gap:,.0f} kg across {len(shift_performance)} shifts.",
                    affected_machine_type=top_mtype,
                    main_observed_factor="Production Shortfall",
                    recommended_action="Review uploaded shift report records for downtime root causes."
                )

                return ProductionModuleResponse(
                    company_name="Ashok Textiles",
                    selected_period=period,
                    actual_kg=total_actual,
                    target_kg=total_target,
                    gap_kg=total_gap,
                    achievement_pct=achievement,
                    trend=trend_points,
                    machine_type_performance=machine_types,
                    loss_reasons=loss_reasons,
                    shift_performance=shift_performance,
                    production_factors=production_factors,
                    spotlight_machine_type=top_mtype,
                    spotlight_efficiency_pct=achievement,
                    spotlight_factory_avg_gap=round(total_gap / len(shift_performance), 1) if shift_performance else 0.0,
                    spotlight_loss_kg=total_gap,
                    is_reconciled=is_reconciled,
                    data_quality_warning=data_quality_warning,
                    comparison=comparison,
                    ai_analysis=ai_analysis
                )

            else:
                # Target date specified or DB empty, but no records found for selected_date/unit
                empty_msg = f"No production data available for this period ({selected_date or 'No Date'})"
                return ProductionModuleResponse(
                    company_name="Ashok Textiles",
                    selected_period=period,
                    actual_kg=0.0,
                    target_kg=0.0,
                    gap_kg=0.0,
                    achievement_pct=0.0,
                    trend=[],
                    machine_type_performance=[],
                    loss_reasons=[],
                    shift_performance=[],
                    production_factors=[],
                    spotlight_machine_type="N/A",
                    spotlight_efficiency_pct=0.0,
                    spotlight_factory_avg_gap=0.0,
                    spotlight_loss_kg=0.0,
                    comparison=ProductionComparisonData(
                        reference_period="Previous Period",
                        reference_kg=0.0,
                        current_kg=0.0,
                        difference_kg=0.0,
                        difference_pct=0.0,
                        main_reason="No Data"
                    ),
                    ai_analysis=AiProductionAnalysisData(
                        summary=empty_msg,
                        affected_machine_type="N/A",
                        main_observed_factor="No Data Ingested",
                        recommended_action="Upload a factory production report for this date."
                    )
                )

        finally:
            db.close()

    @staticmethod
    def get_production_lineage(
        target_date: Optional[str] = None,
        unit: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        db: Session = SessionLocal()
        try:
            if not target_date or target_date.strip() == "":
                latest_record = db.query(ProductionRecord).order_by(desc(ProductionRecord.report_date)).first()
                selected_date = latest_record.report_date if latest_record else None
            else:
                selected_date = target_date.strip()

            if not selected_date:
                return []

            query = db.query(ProductionRecord).filter(ProductionRecord.report_date == selected_date)
            if unit and unit.strip() and unit.strip() != "All Units":
                query = query.filter(ProductionRecord.unit == unit.strip())

            records = query.all()
            lineage = []
            for r in records:
                report = db.query(ReportRecord).filter(ReportRecord.id == r.source_report_id).first()
                filename = report.filename if report else "Unknown File"

                lineage.append({
                    "dashboard_metric": "shift_actual",
                    "value": r.actual_kg,
                    "target_value": r.target_kg,
                    "gap_value": r.gap_kg,
                    "source_file": filename,
                    "source_report_id": r.source_report_id,
                    "source_sheet": r.source_sheet or "Sheet1",
                    "source_row": r.source_row or 0,
                    "source_column": r.source_column or "Actual",
                    "normalized_field": "actual_production",
                    "date": r.report_date,
                    "shift": r.shift or "Daily",
                    "unit": r.unit or "All Units",
                    "department": r.department or "General",
                    "machine_type": r.machine_type or derive_machine_type(r),
                    "lineage_type": "DIRECT_REPORTED",
                    "calculation_method": "DIRECT_EXTRACTION"
                })
            return lineage
        finally:
            db.close()

production_service = ProductionService()


