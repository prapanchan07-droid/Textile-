"""
Payloads for the weaving pages. Every number comes from analytics/metrics.py over rows from analytics/records.py,
and every payload states its period, filters, sources and data freshness.
"""
from __future__ import annotations

from collections import Counter
from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.mill import constants as C
from app.mill.analytics import metrics as M
from app.mill.analytics.findings import explain_missing, find, loom_anomalies
from app.mill.analytics.records import Filters, by, cohort_key, dominant_style, group_of_looms, load
from app.mill.analytics.targets import Targets
from app.mill.models import (
    Alert, EnergyReading, Group, GroupLoomAssignment, ImportBatch, Loom, MachineConnection, ShiftProduction, Style, Task,
    TelemetrySample, WorkOrder,
)
from app.mill.telemetry.collector import live_state


def jsonable(v: Any) -> Any:
    if isinstance(v, dict):
        return {str(k): jsonable(x) for k, x in v.items()}
    if isinstance(v, (list, tuple)):
        return [jsonable(x) for x in v]
    if isinstance(v, (date, datetime)):
        return v.isoformat()
    if isinstance(v, float):
        return round(v, 4)
    return v


def _r(v: Optional[float], d: int = 2) -> Optional[float]:
    return None if v is None else round(v, d)


def freshness(db: Session) -> dict:
    """Latest data per category and source, and the last import. Imported data is never presented as live."""
    rows = db.execute(select(Loom.category, ShiftProduction.source_kind, func.max(ShiftProduction.prod_date))
                      .join(Loom, Loom.id == ShiftProduction.loom_id).group_by(Loom.category, ShiftProduction.source_kind)).all()
    last_import = db.scalar(select(func.max(ImportBatch.committed_at)).where(ImportBatch.status == "COMMITTED"))
    conns = Counter(live_state(c) for c in db.scalars(select(MachineConnection)))
    return {
        "latest_by_category": {cat: {src: d.isoformat() for c2, src, d in rows if c2 == cat} for cat in sorted({r[0] for r in rows})},
        "last_import_at": last_import.isoformat() if last_import else None,
        "live_connections": dict(conns),
        "live_feed": "SIMULATED" if db.scalar(select(func.count()).select_from(TelemetrySample).where(TelemetrySample.data_origin == C.ORIGIN_SIMULATED)) else
                     ("LIVE" if conns.get("CONNECTED") else "NONE"),
        "statement": "Production figures come from imported reports (historical / periodic). They are not a live machine feed.",
    }


def _period_meta(f: Filters, rows: List[dict]) -> dict:
    return {"filters": f.describe(), "date_from": f.date_from.isoformat() if f.date_from else None,
            "date_to": f.date_to.isoformat() if f.date_to else None,
            "days_with_data": len({r["prod_date"] for r in rows}),
            "sources": dict(Counter(r["source_kind"] for r in rows))}


def _kpi_block(rows: List[dict]) -> dict:
    a = M.aggregate(rows)
    return {k: (_r(v) if isinstance(v, float) else v) for k, v in a.items()}


def command_center(db: Session, f: Filters) -> dict:
    rows = load(db, f)
    looms = list(db.scalars(select(Loom).where(Loom.is_active.is_(True))))
    by_cat = {cat: _kpi_block(cr) for (cat,), cr in by(rows, "category").items()}
    by_shift = {s: _kpi_block(sr) for (s,), sr in by(rows, "shift").items()}
    daily = []
    for (d,), dr in sorted(by(rows, "prod_date").items()):
        item = {"date": d.isoformat(), "meters": _r(M.aggregate(dr)["meters"], 1), "efficiency_pct": _r(M.eff_weighted(dr)),
                "sources": sorted({r["source_kind"] for r in dr})}
        for (cat,), cr in by(dr, "category").items():
            item[f"eff_{cat}"] = _r(M.eff_weighted(cr))
            item[f"meters_{cat}"] = _r(M.aggregate(cr)["meters"], 1)
        daily.append(item)
    targets = Targets(db, "meters_per_shift", f.date_from, f.date_to)
    target_total = None
    if targets:
        groups = group_of_looms(db, f.date_to or date.today())
        vals = [targets.value(r["prod_date"], r["loom_code"], r["category"], groups.get(r["loom_id"]).id if groups.get(r["loom_id"]) else None)
                for r in rows if r["meters"] is not None]
        if any(v is not None for v in vals):
            target_total = sum(v for v in vals if v is not None)
    open_alerts = Counter(s for (s,) in db.execute(select(Alert.severity).where(Alert.status != "RESOLVED")))
    now = datetime.now(timezone.utc)
    open_tasks = list(db.scalars(select(Task).where(Task.status.in_(C.TASK_OPEN))))
    wo_open = db.scalar(select(func.count()).select_from(WorkOrder).where(WorkOrder.status.in_(("OPEN", "IN_PROGRESS", "ON_HOLD"))))
    findings = find(db, f, limit=8)
    groups = _group_rows(db, f, rows)
    order = {"CRITICAL": 0, "WARNING": 1, "INFO": 2}
    open_list = sorted(db.scalars(select(Alert).where(Alert.status != "RESOLVED")), key=lambda a: (order.get(a.severity, 3), -a.last_seen_at.timestamp()))
    top_alerts = [
        {"id": a.id, "title": a.title, "severity": a.severity, "status": a.status, "period": a.period_label, "loom_id": a.loom_id,
         "observed": a.observed, "threshold": a.threshold, "source": a.source, "escalation_level": a.escalation_level}
        for a in open_list[:8]
    ]
    reporting = {r["loom_id"] for r in rows}
    return jsonable({
        "period": _period_meta(f, rows), "freshness": freshness(db),
        "kpis": {**_kpi_block(rows), "registered_looms": len(looms), "reporting_looms": len(reporting),
                 "not_reporting_looms": sorted(l.code for l in looms if l.id not in reporting
                                               and (not f.categories or l.category in f.categories)),
                 "target_meters": _r(target_total, 1),
                 "open_alerts": dict(open_alerts), "open_tasks": len(open_tasks),
                 "overdue_tasks": sum(1 for t in open_tasks if t.due_at and t.due_at < now),
                 "open_work_orders": wo_open},
        "by_category": by_cat, "by_shift": by_shift, "daily": daily, "findings": findings, "groups": groups, "top_alerts": top_alerts,
        "comparability": "Categories differ in machine type, width and style; compare efficiency across them with care and meters not at all.",
    })


def _group_rows(db: Session, f: Filters, rows: List[dict]) -> List[dict]:
    groups = list(db.scalars(select(Group).where(Group.is_active.is_(True)).order_by(Group.code)))
    if not groups:
        return []
    out = []
    assignments = list(db.scalars(select(GroupLoomAssignment)))
    tasks = Counter((t.group_id, t.status) for t in db.scalars(select(Task)))
    alerts = Counter(a.group_id for a in db.scalars(select(Alert).where(Alert.status != "RESOLVED")))
    for g in groups:
        # A record counts for the group when the loom was assigned to it on that date.
        spans = [(a.loom_id, a.valid_from, a.valid_to) for a in assignments if a.group_id == g.id]
        gr = [r for r in rows if any(l == r["loom_id"] and vf <= r["prod_date"] and (vt is None or r["prod_date"] < vt) for l, vf, vt in spans)]
        current = {l for l, vf, vt in spans if vt is None}
        agg = M.aggregate(gr)
        out.append({"id": g.id, "code": g.code, "name": g.name, "leader": g.leader.name if g.leader else None, "looms": len(current),
                    "meters": _r(agg["meters"], 1), "efficiency_pct": _r(agg["efficiency_pct"]), "loom_shifts": agg["loom_shifts"],
                    "open_tasks": sum(n for (gid, s), n in tasks.items() if gid == g.id and s in C.TASK_OPEN),
                    "blocked_tasks": tasks.get((g.id, "BLOCKED"), 0), "completed_tasks": tasks.get((g.id, "COMPLETED"), 0),
                    "open_alerts": alerts.get(g.id, 0)})
    return out


def loom_grid(db: Session, f: Filters) -> dict:
    """Every loom with its latest known record, live state (only if a connection exists) and open work."""
    looms = list(db.scalars(select(Loom).where(Loom.is_active.is_(True)).order_by(Loom.category, Loom.loom_no)))
    rows = load(db, f)
    per = by(rows, "loom_id")
    conns = {c.loom_id: c for c in db.scalars(select(MachineConnection))}
    groups = group_of_looms(db, f.date_to or date.today())
    alerts = Counter(a.loom_id for a in db.scalars(select(Alert).where(Alert.status != "RESOLVED")))
    wos = Counter(w.loom_id for w in db.scalars(select(WorkOrder).where(WorkOrder.status.in_(("OPEN", "IN_PROGRESS", "ON_HOLD")))))
    last_tel = {}
    for s in db.scalars(select(TelemetrySample).where(TelemetrySample.id.in_(
            select(func.max(TelemetrySample.id)).group_by(TelemetrySample.loom_id)))):
        last_tel[s.loom_id] = s
    cohorts: Dict[tuple, List[float]] = {}
    stats = {}
    for loom in looms:
        lr = per.get((loom.id,), [])
        if lr:
            agg = M.aggregate(lr)
            key = cohort_key(lr)
            stats[loom.id] = (agg, key)
            if agg["efficiency_pct"] is not None:
                cohorts.setdefault(key, []).append(agg["efficiency_pct"])
    out = []
    for loom in looms:
        lr = per.get((loom.id,), [])
        last = lr[-1] if lr else None
        agg, key = stats.get(loom.id, (None, None))
        peers = cohorts.get(key) if key else None
        conn = conns.get(loom.id)
        tel = last_tel.get(loom.id)
        state = live_state(conn)
        g = groups.get(loom.id)
        out.append({
            "id": loom.id, "code": loom.code, "category": loom.category, "manufacturer": loom.manufacturer, "loom_no": loom.loom_no,
            "width_cm": loom.width_cm, "group": {"id": g.id, "code": g.code, "name": g.name} if g else None,
            "latest": None if last is None else {"date": last["prod_date"], "shift": last["shift"], "efficiency_pct": last["efficiency_pct"],
                                                  "meters": last["meters"], "rpm": last["rpm"], "style": last["style_code"], "source": last["source_kind"]},
            "period": None if agg is None else {"efficiency_pct": _r(agg["efficiency_pct"]), "meters": _r(agg["meters"], 1),
                                                "warp_stops_cmpx": _r(agg["warp_stops_cmpx"]), "weft_stops_cmpx": _r(agg["weft_stops_cmpx"]),
                                                "loom_shifts": agg["loom_shifts"], "style": key[2] if key else None,
                                                "peer_median_efficiency_pct": _r(M.median(peers)) if peers and len(peers) >= 3 else None,
                                                "trend": [_r(r["efficiency_pct"], 1) for r in lr[-21:]]},
            "live": {"state": state, "origin": tel.data_origin if tel and state in ("CONNECTED", "STALE") else None,
                     "machine_state": tel.state if tel and state == "CONNECTED" else None,
                     "rpm": tel.rpm if tel and state == "CONNECTED" else None,
                     "sampled_at": tel.sampled_at if tel else None},
            "open_alerts": alerts.get(loom.id, 0), "open_work_orders": wos.get(loom.id, 0),
        })
    return jsonable({"period": _period_meta(f, rows), "freshness": freshness(db), "looms": out})


def loom_detail(db: Session, loom: Loom, f: Filters) -> dict:
    rows = load(db, Filters(**{**f.__dict__, "loom_ids": [loom.id]}))
    agg = M.aggregate(rows)
    # Peers over the same period: same category, width and style, same source.
    peer_info = None
    if rows:
        key = cohort_key(rows)
        all_rows = load(db, Filters(**{**f.__dict__, "loom_ids": [], "categories": [loom.category], "group_id": None}))
        peers = []
        for (lid,), lr in by(all_rows, "loom_id").items():
            if cohort_key(lr) == key:
                a = M.aggregate(lr)
                peers.append({"loom_id": lid, "loom_code": lr[0]["loom_code"], "efficiency_pct": _r(a["efficiency_pct"]), "meters": _r(a["meters"], 1),
                              "warp_stops_cmpx": _r(a["warp_stops_cmpx"]), "weft_stops_cmpx": _r(a["weft_stops_cmpx"]), "loom_shifts": a["loom_shifts"]})
        effs = [p["efficiency_pct"] for p in peers if p["efficiency_pct"] is not None]
        peer_info = {"cohort": {"category": key[0], "width_cm": key[1], "style": key[2], "source": key[3]}, "size": len(peers),
                     "median_efficiency_pct": _r(M.median(effs)), "rank": 1 + sum(1 for e in effs if e > _r(agg["efficiency_pct"])) if agg["efficiency_pct"] is not None else None,
                     "peers": sorted(peers, key=lambda p: -(p["efficiency_pct"] or 0)),
                     "valid": len(peers) >= 3, "note": None if len(peers) >= 3 else "Fewer than 3 comparable looms: peer comparison not meaningful."}
    shifts = {s: _kpi_block(sr) for (s,), sr in by(rows, "shift").items()}
    daily = [{"date": d.isoformat(), "efficiency_pct": _r(M.eff_weighted(dr)), "meters": _r(M.aggregate(dr)["meters"], 1),
              "warp_stops": M.aggregate(dr)["warp_stops"], "weft_stops": M.aggregate(dr)["weft_stops"],
              "sources": sorted({r["source_kind"] for r in dr})} for (d,), dr in sorted(by(rows, "prod_date").items())]
    records = [{k: r[k] for k in ("id", "prod_date", "shift", "source_kind", "data_origin", "style_code", "rpm", "efficiency_pct", "loom_efficiency_pct",
                                  "kilopicks", "meters", "warp_stops", "weft_stops", "other_stops", "run_min", "stop_min", "batch_id")} for r in rows]
    stop_causes: Dict[str, float] = {}
    for sp in db.scalars(select(ShiftProduction).where(ShiftProduction.loom_id == loom.id, ShiftProduction.prod_date >= (f.date_from or date.min),
                                                       ShiftProduction.prod_date <= (f.date_to or date.max))):
        for k, v in ((sp.extras or {}).get("stop_counts_by_sensor") or {}).items():
            if v:
                stop_causes[k] = stop_causes.get(k, 0) + v
    conn = db.scalar(select(MachineConnection).where(MachineConnection.loom_id == loom.id))
    tel = list(db.scalars(select(TelemetrySample).where(TelemetrySample.loom_id == loom.id).order_by(TelemetrySample.sampled_at.desc()).limit(60)))
    alerts = list(db.scalars(select(Alert).where(Alert.loom_id == loom.id).order_by(Alert.last_seen_at.desc()).limit(30)))
    tasks = list(db.scalars(select(Task).where(Task.loom_id == loom.id).order_by(Task.created_at.desc()).limit(30)))
    wos = list(db.scalars(select(WorkOrder).where(WorkOrder.loom_id == loom.id).order_by(WorkOrder.reported_at.desc()).limit(30)))
    hist = list(db.execute(select(GroupLoomAssignment, Group).join(Group).where(GroupLoomAssignment.loom_id == loom.id)
                           .order_by(GroupLoomAssignment.valid_from.desc())))
    findings = [x for x in find(db, f, limit=200) if x.get("loom_id") == loom.id]
    style = dominant_style(rows) if rows else None
    return jsonable({
        "loom": {"id": loom.id, "code": loom.code, "category": loom.category, "manufacturer": loom.manufacturer, "model": loom.model,
                 "loom_no": loom.loom_no, "width_cm": loom.width_cm, "notes": loom.notes, "attributes": loom.attributes,
                 "style": style, "style_description": db.get(Style, style).description if style and db.get(Style, style) else None},
        "period": _period_meta(f, rows), "kpis": _kpi_block(rows), "by_shift": shifts, "daily": daily, "records": records,
        "peers": peer_info, "anomalies": loom_anomalies(rows), "findings": findings,
        "stop_causes": sorted(({"cause": k, "count": v} for k, v in stop_causes.items()), key=lambda x: -x["count"]),
        "stop_causes_note": None if stop_causes else "Per-sensor stop counts exist only in the Tsudakoma export; other sources give warp/weft totals only.",
        "missing_note": explain_missing(loom.category),
        "connection": None if conn is None else {"adapter": conn.adapter, "host": conn.host, "enabled": conn.enabled, "state": live_state(conn),
                                                 "last_success_at": conn.last_success_at, "last_error": conn.last_error},
        "live_state": live_state(conn),
        "telemetry": [{"sampled_at": t.sampled_at, "state": t.state, "rpm": t.rpm, "efficiency_pct": t.efficiency_pct, "origin": t.data_origin} for t in tel],
        "alerts": [{"id": a.id, "title": a.title, "severity": a.severity, "status": a.status, "period": a.period_label, "observed": a.observed,
                    "threshold": a.threshold, "first_seen_at": a.first_seen_at, "resolution_notes": a.resolution_notes} for a in alerts],
        "tasks": [{"id": t.id, "title": t.title, "status": t.status, "priority": t.priority, "due_at": t.due_at} for t in tasks],
        "work_orders": [{"id": w.id, "title": w.title, "kind": w.kind, "status": w.status, "reported_at": w.reported_at, "completed_at": w.completed_at,
                         "downtime_min": w.downtime_min, "cause": w.cause} for w in wos],
        "group_history": [{"group": g.name, "group_id": g.id, "valid_from": a.valid_from, "valid_to": a.valid_to} for a, g in hist],
        "recommendations": _recommend(loom, agg, peer_info, findings, rows),
    })


def _recommend(loom: Loom, agg: dict, peers: Optional[dict], findings: List[dict], rows: List[dict]) -> List[dict]:
    """Next actions derived from the evidence on the page. Suggestions for people to decide on; nothing is automated."""
    out = [{"action": x["next_step"], "why": x["title"], "basis": x["basis"]} for x in findings]
    if not rows:
        out.append({"action": "Import a report that covers this loom for the selected period.", "why": "No records in the period.", "basis": "DATA"})
    if loom.category == "SZ":
        out.append({"action": "Start recording warp/weft stop counts for Sulzer looms (the SZ report leaves them empty).",
                    "why": "Stop-based analysis is impossible without them.", "basis": "DATA"})
    if not any((r.get("run_min") is not None) for r in rows):
        out.append({"action": "Record stop reasons and durations (or connect the monitoring system) to identify causes of lost time.",
                    "why": "The mill report has stop counts only, no durations or reasons.", "basis": "DATA"})
    return out


def production(db: Session, f: Filters) -> dict:
    """Production and shift analytics: daily x shift, category x shift, style mix."""
    rows = load(db, f)
    grid = []
    for (d, s), dr in sorted(by(rows, "prod_date", "shift").items()):
        a = M.aggregate(dr)
        grid.append({"date": d, "shift": s, "meters": _r(a["meters"], 1), "kilopicks": _r(a["kilopicks"], 1), "efficiency_pct": _r(a["efficiency_pct"]),
                     "warp_stops_cmpx": _r(a["warp_stops_cmpx"]), "weft_stops_cmpx": _r(a["weft_stops_cmpx"]), "loom_shifts": a["loom_shifts"]})
    cat_shift = []
    for (cat, s), cr in sorted(by(rows, "category", "shift").items()):
        cat_shift.append({"category": cat, "shift": s, **_kpi_block(cr)})
    styles = []
    for (st,), sr in by(rows, "style_code").items():
        a = M.aggregate(sr)
        styles.append({"style": st, "looms": a["looms"], "loom_shifts": a["loom_shifts"], "meters": _r(a["meters"], 1),
                       "efficiency_pct": _r(a["efficiency_pct"]), "warp_stops_cmpx": _r(a["warp_stops_cmpx"]),
                       "weft_stops_cmpx": _r(a["weft_stops_cmpx"]), "categories": sorted({r["category"] for r in sr})})
    styles.sort(key=lambda x: -(x["meters"] or 0))
    descr = {s.code: s.description for s in db.scalars(select(Style))}
    for s in styles:
        s["description"] = descr.get(s["style"])
    return jsonable({"period": _period_meta(f, rows), "totals": _kpi_block(rows), "by_day_shift": grid, "by_category_shift": cat_shift,
                     "by_style": styles, "freshness": freshness(db)})


DIMENSIONS = {"loom": ("loom_id",), "shift": ("shift",), "style": ("style_code",), "category": ("category",), "date": ("prod_date",),
              "group": ("group",), "width": ("category", "width_cm")}


def compare(db: Session, f: Filters, dimension: str) -> dict:
    rows = load(db, f)
    if dimension == "group":
        groups = {}
        for r in rows:
            g = groups.setdefault(r["prod_date"], group_of_looms(db, r["prod_date"]))
            gg = g.get(r["loom_id"])
            r["group"] = gg.name if gg else "Unassigned"
    keys = DIMENSIONS[dimension]
    out = []
    for k, kr in by(rows, *keys).items():
        a = M.aggregate(kr)
        label = kr[0]["loom_code"] if dimension == "loom" else " / ".join(str(x) for x in k)
        out.append({"key": label, "loom_id": kr[0]["loom_id"] if dimension == "loom" else None,
                    "cohort": " / ".join(str(x) for x in cohort_key(kr)[:3]) if dimension == "loom" else None,
                    "sources": sorted({r["source_kind"] for r in kr}), **{x: (_r(v) if isinstance(v, float) else v) for x, v in a.items()}})
    # Peer standing for looms: efficiency against the median of the same cohort.
    if dimension == "loom":
        cohorts: Dict[str, List[float]] = {}
        for o in out:
            if o["efficiency_pct"] is not None:
                cohorts.setdefault(o["cohort"] + "|" + ",".join(o["sources"]), []).append(o["efficiency_pct"])
        for o in out:
            peers = cohorts.get(o["cohort"] + "|" + ",".join(o["sources"]), [])
            med = M.median(peers) if len(peers) >= 3 else None
            o["cohort_size"] = len(peers)
            o["vs_cohort_pts"] = _r(o["efficiency_pct"] - med) if med is not None and o["efficiency_pct"] is not None else None
    out.sort(key=lambda x: str(x["key"]))
    mixed = len({r["source_kind"] for r in rows}) > 1
    return jsonable({"period": _period_meta(f, rows), "dimension": dimension, "rows": out,
                     "warnings": (["Rows mix the mill report and machine exports. Compare stop rates and meters only within one source (filter by source)."] if mixed else [])
                     + (["Categories differ in machine type and width: compare efficiency, not meters."] if dimension == "category" else [])})


def energy(db: Session, f: Filters) -> dict:
    """Air and energy: only measured values. Says exactly what is missing when there are none."""
    rows = load(db, f)
    air_rows = [r for r in rows if r.get("air_nm3") is not None]
    q = select(EnergyReading)
    if f.date_from:
        q = q.where(EnergyReading.period_end >= datetime.combine(f.date_from, datetime.min.time(), tzinfo=timezone.utc))
    if f.date_to:
        q = q.where(EnergyReading.period_start <= datetime.combine(f.date_to + timedelta(days=1), datetime.min.time(), tzinfo=timezone.utc))
    readings = list(db.scalars(q))
    reported_zero = db.scalar(select(func.count()).select_from(ShiftProduction).where(
        ShiftProduction.extras["air_consumption_reported_nm3"].as_float() == 0)) if db.bind.dialect.name == "postgresql" else None
    per_loom = []
    for (lid,), lr in by(air_rows, "loom_id").items():
        air = sum(r["air_nm3"] for r in lr)
        m = sum(r["meters"] for r in lr if r["meters"])
        per_loom.append({"loom_code": lr[0]["loom_code"], "air_nm3": _r(air), "meters": _r(m, 1), "nm3_per_meter": _r(air / m, 4) if m else None})
    return jsonable({
        "period": _period_meta(f, rows),
        "air": {"records_with_measured_air": len(air_rows), "per_loom": per_loom,
                "reported_zero_records": reported_zero,
                "status": "MEASURED" if air_rows else "NOT_MEASURED"},
        "energy": {"readings": len(readings), "kwh": _r(sum(r.kwh for r in readings if r.kwh is not None)) if readings else None,
                   "basis": sorted({r.basis for r in readings}), "status": "AVAILABLE" if readings else "NO_READINGS"},
        "requirements": [
            "Compressed air: per-loom flow meters, or the OEM air-consumption value enabled in the monitoring system (the Tsudakoma "
            "export has the column but reports 0 for every loom, i.e. not measured). Toyota's report lists an 'Air flow' field that is not switched on in the export.",
            "Electricity: energy meters per loom, per group feeder or at least per shed, with readings at shift boundaries.",
            "Cost: the electricity tariff (Rs/kWh) and compressor specific power (kWh per Nm3) to turn measurements into money.",
            "RPM, efficiency, kilopicks and meters cannot reveal kWh or air volume; no estimate is shown without measured input.",
        ],
    })
