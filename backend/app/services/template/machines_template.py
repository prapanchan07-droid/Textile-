"""Machines & Downtime page built from uploaded template data."""
from typing import Dict, List

from sqlalchemy.orm import Session

from app.schemas.machines import (
    MachinesModuleResponse, MachinePerformanceItem, SpotlightMachine, DowntimeKpi, DowntimeReasonItem,
    MachineTrendPoint, MachineDetailData,
)
from app.services.template.factory_data import (
    aggregate_window, current_window, daily_series, date_label, status_for_efficiency, MachineAgg,
)


def _machine_item(m: MachineAgg) -> MachinePerformanceItem:
    return MachinePerformanceItem(
        machine_id=m.machine_id, machine_type=m.machine_type, actual_kg=round(m.actual, 1), target_kg=round(m.target, 1),
        efficiency_pct=m.efficiency, loss_kg=round(m.loss, 1), downtime_min=int(round(m.downtime_min)),
        status=status_for_efficiency(m.efficiency), main_issue=m.main_issue)


def machines_from_template(db: Session, period: str, machine_type: str, machine_id: str) -> MachinesModuleResponse:
    agg = aggregate_window(db, current_window(db, period))
    machines = sorted(agg.machines.values(), key=lambda m: (m.loss, -m.efficiency), reverse=True) if agg else []

    types = ["All"] + sorted({m.machine_type for m in machines})
    filtered = [m for m in machines if not machine_type or machine_type.upper() == "ALL"
                or m.machine_type.lower() == machine_type.lower()]

    selected = filtered[0] if filtered else (machines[0] if machines else None)
    if machine_id and machine_id.upper() != "ALL":
        selected = next((m for m in machines if m.machine_id.lower() == machine_id.lower()), selected)
    if selected is None:
        raise ValueError("No machine data available.")

    # Downtime KPIs & reasons over the filtered machines
    total_dt = sum(m.downtime_min for m in filtered)
    planned_dt = sum(m.planned_downtime_min for m in filtered)
    reason_min: Dict[str, float] = {}
    for m in filtered:
        for reason, minutes in m.reasons.items():
            reason_min[reason] = reason_min.get(reason, 0.0) + minutes
    reasons_total = sum(reason_min.values())
    downtime_reasons: List[DowntimeReasonItem] = [
        DowntimeReasonItem(category=name, downtime_min=int(round(minutes)),
                           percentage=round(minutes / reasons_total * 100, 1) if reasons_total > 0 else 0.0)
        for name, minutes in sorted(reason_min.items(), key=lambda kv: kv[1], reverse=True)
    ]

    # 7-day trend per machine
    trends: Dict[str, List[dict]] = {}
    for d, day_agg in daily_series(db, 7):
        for mid, m in day_agg.machines.items():
            trends.setdefault(mid, []).append(
                {"date_label": date_label(d), "efficiency_pct": m.efficiency, "loss_kg": round(m.loss, 1)})

    power_dt = sum(v for k, v in selected.reasons.items() if "power" in k.lower() or "electric" in k.lower())
    if selected.quality is None:
        quality_status = "Data unavailable"
    else:
        quality_status = f"{'NORMAL' if selected.quality >= 95 else 'ATTENTION'} - {selected.quality}% quality rating"

    return MachinesModuleResponse(
        company_name="Ashok Textiles", period=period, selected_machine_type=machine_type, selected_machine_id=machine_id,
        machine_types=types,
        all_machines=[_machine_item(m) for m in filtered],
        spotlight_machine=SpotlightMachine(
            machine_id=selected.machine_id, machine_type=selected.machine_type, loss_kg=round(selected.loss, 1),
            efficiency_pct=selected.efficiency, downtime_min=int(round(selected.downtime_min)), main_issue=selected.main_issue),
        downtime_kpis=DowntimeKpi(
            total_downtime_min=int(round(total_dt)), unplanned_downtime_min=int(round(total_dt - planned_dt)),
            planned_downtime_min=int(round(planned_dt)), stoppage_count=sum(m.stoppages for m in filtered)),
        downtime_reasons=downtime_reasons,
        machine_trend=[MachineTrendPoint(**pt) for pt in trends.get(selected.machine_id, [])],
        machine_trends_by_id=trends,
        machine_detail=MachineDetailData(
            machine_id=selected.machine_id, machine_type=selected.machine_type, actual_kg=round(selected.actual, 1),
            target_kg=round(selected.target, 1), efficiency_pct=selected.efficiency, loss_kg=round(selected.loss, 1),
            total_downtime_min=int(round(selected.downtime_min)), stoppage_count=selected.stoppages,
            main_reason=selected.main_reason or "N/A", last_maintenance=selected.last_maintenance or "Not recorded",
            next_maintenance=selected.next_maintenance or "Not recorded",
            recent_event=selected.issue or "No recent event recorded", power_events=selected.power_events,
            power_downtime_min=int(round(power_dt)), quality_status=quality_status),
    )
