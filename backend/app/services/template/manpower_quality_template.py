"""Manpower & Quality page built from uploaded template data."""
from typing import Dict, List, Optional, Tuple

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.ingestion import ManpowerRecord
from app.models.template_data import QualityParameterRecord, MachineDailyRecord
from app.schemas.manpower_quality import (
    ManpowerQualityModuleResponse, ManpowerSummary, DepartmentManpowerItem, ManpowerTrendPoint,
    QualityStatusData, QualityParameterItem, QualityMachineItem, AttentionItem,
)
from app.services.template.factory_data import date_label


def param_status(value: float, limit: float) -> str:
    if limit > 0 and value > limit:
        return "OUT OF LIMIT"
    if limit > 0 and value >= 0.9 * limit:
        return "ATTENTION"
    return "NORMAL"


def manpower_by_date(db: Session) -> Dict[str, Dict[str, Tuple[int, int]]]:
    """{date: {department: (required, available)}} summed over shifts."""
    out: Dict[str, Dict[str, Tuple[int, int]]] = {}
    for r in db.query(ManpowerRecord).all():
        dept = r.department or "Unassigned"
        req, avail = out.setdefault(r.report_date, {}).get(dept, (0, 0))
        out[r.report_date][dept] = (req + r.planned_count, avail + r.actual_count)
    return out


def latest_quality_date(db: Session) -> Optional[str]:
    return db.query(func.max(QualityParameterRecord.report_date)).scalar()


def quality_snapshot(db: Session) -> List[QualityParameterItem]:
    """Latest-date average per parameter."""
    d = latest_quality_date(db)
    if not d:
        return []
    grouped: Dict[str, List[QualityParameterRecord]] = {}
    for r in db.query(QualityParameterRecord).filter(QualityParameterRecord.report_date == d).all():
        grouped.setdefault(r.parameter, []).append(r)
    items = []
    for name, recs in grouped.items():
        value = round(sum(r.value for r in recs) / len(recs), 2)
        limit = round(sum(r.limit_value for r in recs) / len(recs), 2)
        items.append(QualityParameterItem(parameter=name, label=name, value=value, limit=limit,
                                          unit=recs[0].unit, status=param_status(value, limit)))
    order = {"OUT OF LIMIT": 0, "ATTENTION": 1, "NORMAL": 2}
    return sorted(items, key=lambda i: (order[i.status], -(i.value / i.limit if i.limit else 0)))


def manpower_quality_from_template(db: Session, period: str) -> ManpowerQualityModuleResponse:
    # ---------------- manpower
    mp = manpower_by_date(db)
    dates = sorted(mp)
    if dates:
        latest = mp[dates[-1]]
        required = sum(v[0] for v in latest.values())
        available = sum(v[1] for v in latest.values())
        summary = ManpowerSummary(required=required, available=available, shortage=max(0, required - available),
                                  attendance_pct=round(available / required * 100, 1) if required else 0.0)
        gaps = [
            DepartmentManpowerItem(department=d, required=r, available=a, gap=a - r if a < r else 0,
                                   attendance_pct=round(a / r * 100, 1) if r else 0.0)
            for d, (r, a) in latest.items()
        ]
        gaps.sort(key=lambda g: g.gap)
        trend = []
        for d in dates[-7:]:
            r = sum(v[0] for v in mp[d].values())
            a = sum(v[1] for v in mp[d].values())
            trend.append(ManpowerTrendPoint(date_label=date_label(d), required=r, available=a,
                                            shortage=max(0, r - a), attendance_pct=round(a / r * 100, 1) if r else 0.0))
    else:
        summary = ManpowerSummary(required=0, available=0, shortage=0, attendance_pct=0.0)
        gaps, trend = [], []

    # ---------------- quality
    params = quality_snapshot(db)
    qdate = latest_quality_date(db)
    readings = db.query(QualityParameterRecord).filter(QualityParameterRecord.report_date == qdate).all() if qdate else []
    passed = sum(1 for r in readings if r.value <= r.limit_value)
    pass_rate = round(passed / len(readings) * 100, 1) if readings else 0.0
    out_of_limit = [p for p in params if p.status == "OUT OF LIMIT"]
    if not readings:
        q_status = QualityStatusData(status="NORMAL", samples_tested=0, pass_rate_pct=0.0, defect_rate_pct=0.0,
                                     main_issue="Data unavailable")
    else:
        q_status = QualityStatusData(
            status="CRITICAL" if pass_rate < 80 else ("ATTENTION" if out_of_limit or pass_rate < 95 else "NORMAL"),
            samples_tested=len(readings), pass_rate_pct=pass_rate, defect_rate_pct=round(100 - pass_rate, 1),
            main_issue=out_of_limit[0].parameter if out_of_limit else "None")

    trends: Dict[str, List[dict]] = {}
    if params:
        q_dates = [r[0] for r in db.query(QualityParameterRecord.report_date).distinct()
                   .order_by(QualityParameterRecord.report_date).all()][-7:]
        for d in q_dates:
            by_param: Dict[str, List[QualityParameterRecord]] = {}
            for r in db.query(QualityParameterRecord).filter(QualityParameterRecord.report_date == d).all():
                by_param.setdefault(r.parameter, []).append(r)
            for name, recs in by_param.items():
                trends.setdefault(name, []).append({
                    "date_label": date_label(d), "value": round(sum(r.value for r in recs) / len(recs), 2),
                    "limit": round(sum(r.limit_value for r in recs) / len(recs), 2)})

    # worst reading per machine on the latest date
    types = {mid: mtype for mid, mtype in db.query(MachineDailyRecord.machine_id, MachineDailyRecord.machine_type).distinct().all()}
    worst: Dict[str, QualityParameterRecord] = {}
    for r in readings:
        key = r.machine_id or "Factory"
        ratio = r.value / r.limit_value if r.limit_value else 0
        if key not in worst or ratio > worst[key].value / (worst[key].limit_value or 1):
            worst[key] = r
    by_machine = sorted(worst.values(), key=lambda r: r.value / (r.limit_value or 1), reverse=True)[:6]
    machine_items = [
        QualityMachineItem(
            machine_process=f"{types[r.machine_id]} {r.machine_id}" if r.machine_id in types else (r.machine_id or "Factory"),
            quality_issue=r.parameter, current_value=r.value, limit=r.limit_value, unit=r.unit,
            status=param_status(r.value, r.limit_value))
        for r in by_machine
    ]

    # ---------------- attention list
    attention: List[AttentionItem] = []
    for g in gaps:
        if g.gap < 0 and (g.attendance_pct < 93 or -g.gap >= 20):
            attention.append(AttentionItem(severity="HIGH", title=f"{g.department} manpower shortage",
                                           detail=f"{-g.gap} workers short ({g.attendance_pct}% attendance)"))
        elif g.gap < 0 and g.attendance_pct < 96:
            attention.append(AttentionItem(severity="MEDIUM", title=f"{g.department} attendance below target",
                                           detail=f"Attendance at {g.attendance_pct}% ({-g.gap} workers short)"))
    for r in by_machine:
        st = param_status(r.value, r.limit_value)
        if st == "OUT OF LIMIT":
            attention.append(AttentionItem(severity="HIGH", title=f"{r.parameter} above specification limit",
                                           detail=f"Observed on {r.machine_id or 'factory'} ({r.value:g} vs {r.limit_value:g} limit)"))
        elif st == "ATTENTION":
            attention.append(AttentionItem(severity="MEDIUM", title=f"{r.parameter} close to limit",
                                           detail=f"{r.machine_id or 'Factory'} at {r.value:g} vs {r.limit_value:g} limit"))
    attention.sort(key=lambda a: {"HIGH": 0, "MEDIUM": 1, "LOW": 2}[a.severity])

    return ManpowerQualityModuleResponse(
        company_name="Ashok Textiles", period=period, manpower_summary=summary, department_gaps=gaps,
        manpower_trend=trend, quality_status=q_status, quality_parameters=params, quality_trends_by_param=trends,
        quality_issues_by_machine=machine_items, needs_attention=attention[:6])
