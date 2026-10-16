"""AI Insights, Compare, the Quality Desk and the Action Tracker."""
from __future__ import annotations

from collections import defaultdict
from datetime import date, timedelta
from typing import Dict, List, Optional

from sqlalchemy import select

from app.core.roles import Role
from app.weaving import models as m
from app.weaving.analytics import calc, compare as cmp
from app.weaving.pages.shared import Mill, kpi, r1


def _actions_by_finding(mill: Mill) -> Dict[str, List[dict]]:
    out: Dict[str, List[dict]] = defaultdict(list)
    for a in mill.db.scalars(select(m.WvAction).where(m.WvAction.finding_key.isnot(None), m.WvAction.status != "CANCELLED")):
        out[a.finding_key].append({"ref": a.action_ref, "action": a.action, "owner": a.owner_name, "status": a.status, "due": a.due_date.isoformat() if a.due_date else None,
                                   "outcome_note": a.outcome_note, "verified_cause": a.verified_cause})
    return out


def insights(mill: Mill) -> dict:
    findings = list(mill.findings)
    if mill.role == Role.MAINTENANCE:
        findings += mill.maintenance_findings
    mine = mill.for_me(findings)
    linked = _actions_by_finding(mill)
    dicts = mill.finding_dicts(mine)
    for d in dicts:
        d["actions"] = linked.get(d["key"], [])
        verified = [a["verified_cause"] for a in d["actions"] if a.get("verified_cause")]
        d["verified_cause"] = verified[0] if verified else None
    alerts = [a.as_dict() for a in mill.alerts] if mill.role in (Role.WEAVING_MANAGER, Role.OWNER, Role.MAINTENANCE) else []
    kinds = defaultdict(int)
    for f in mine:
        kinds[f.kind] += 1
    return {"as_of": mill.now.isoformat(), "role": mill.role.value, "money_visible": mill.money, "lens_days": mill.ctx.lens_days, "findings": dicts, "alerts": alerts,
            "summary": {"total": len(mine), "high": sum(1 for f in mine if f.severity == "HIGH"), "by_kind": dict(kinds), "with_actions": sum(1 for d in dicts if d["actions"])},
            "method": ["Every finding shows the facts first, then statistical signals, then hypotheses. Hypotheses are always UNVERIFIED.", "A cause becomes verified only when a person records it on the outcome of a completed action.",
                       "Confidence is a rule (p-value, number of observations, days of data), not a feeling. Details sit under each finding."]}


def compare_page(mill: Mill) -> dict:
    ctx = mill.ctx
    types = [t for t in cmp.TYPES if t != "weaver" or mill.money]
    opts = {t: cmp.options(ctx, t) for t in ("loom", "style", "shift", "loom_type", "yarn_lot", "supplier")}
    if mill.money:
        opts["weaver"] = cmp.options(ctx, "weaver")
    recs = cmp.recommended(ctx, mill.for_me(mill.findings) if mill.role != Role.QUALITY else mill.findings)
    recs = [r for r in recs if r["type"] in types]
    return {"as_of": mill.now.isoformat(), "types": [{"key": t, "label": {"loom": "Looms", "style": "Styles", "shift": "Shifts", "loom_type": "Loom types", "beam": "Beams", "yarn_lot": "Yarn lots", "supplier": "Yarn suppliers", "weaver": "Weavers"}[t]} for t in types],
            "metrics": [{"key": k, "label": l, "unit": u, "better": b} for k, l, u, b in cmp.METRICS], "default_metrics": cmp.DEFAULT_METRICS, "options": opts, "recommended": recs}


def quality(mill: Mill) -> dict:
    ctx, refs = mill.ctx, mill.refs
    w, pw = ctx.window, ctx.previous
    insp, defs = ctx.insp_between(w.start_date, w.end_date)
    pinsp, pdefs = ctx.insp_between(pw.start_date, pw.end_date)
    q, pq = calc.total_quality(insp, defs), calc.total_quality(pinsp, pdefs)
    prod = calc.total_production(ctx.prod_between(w.start_date, w.end_date))
    end = w.end_date
    i14, d14 = ctx.insp_between(end - timedelta(days=13), end)
    D = calc.roll_quality(i14, d14, lambda r: r.shift_date)
    trend = [{"label": f"{d:%d %b}", "defects_per_100m": r1(a.defects_per_100m, 2), "grade_a_pct": r1(a.grade_a_pct), "inspected_m": round(a.length_m)} for d, a in sorted(D.items())]
    # defect types by shift, per 100 m inspected
    shift_len = calc.roll_quality(insp, defs, lambda r: r.shift_id)
    types = sorted({refs.defect_types[d.defect_type_id].name for d in defs})
    cnt: Dict[tuple, int] = defaultdict(int)
    for d in defs:
        cnt[(d.shift_id, refs.defect_types[d.defect_type_id].name)] += d.defects
    by_shift = []
    for sid in sorted(refs.shifts, key=lambda i: refs.shifts[i].sort_order):
        L = shift_len.get(sid)
        if not L or not L.length_m:
            continue
        row = {"shift": refs.shift_name(sid), "total": r1(L.defects_per_100m, 2), "inspected_m": round(L.length_m)}
        for t in types:
            row[t] = r1(cnt[(sid, t)] / L.length_m * 100, 2)
        by_shift.append(row)
    # style x shift heat
    SS = calc.roll_quality(insp, defs, lambda r: (r.style_id, r.shift_id))
    heat = []
    for sid in sorted({k[0] for k in SS}, key=lambda i: refs.style_code(i)):
        row = {"style": refs.style_code(sid), "cells": {}}
        for shid in sorted(refs.shifts, key=lambda i: refs.shifts[i].sort_order):
            a = SS.get((sid, shid))
            row["cells"][refs.shift_name(shid)] = r1(a.defects_per_100m, 2) if a and a.length_m >= 150 else None
        heat.append(row)
    # yarn lots: incoming tests against what happened on the loom
    lots = {l.lot_no: l for l in mill.db.scalars(select(m.WvYarnLot))}
    prod_rows = [r for r in ctx.prod_between(ctx.lens_start, ctx.lens_end) if r.beam_id]
    warp_ids = {i for i, r in refs.reasons.items() if r.category == "WARP"}
    stop_rows = [r for r in ctx.stops_between(ctx.lens_start, ctx.lens_end) if r.beam_id and r.reason_id in warp_ids]
    lot_of = lambda r: refs.beams[r.beam_id].yarn_lot if r.beam_id in refs.beams else None
    LP = calc.roll_production(prod_rows, lot_of)
    LS = calc.roll_stops(stop_rows, lot_of)
    beams_of: Dict[str, set] = defaultdict(set)
    for r in prod_rows:
        beams_of[lot_of(r)].add(r.beam_id)
    sizep = defaultdict(list)
    for b in refs.beams.values():
        if b.yarn_lot and b.size_pickup_pct is not None:
            sizep[b.yarn_lot].append(float(b.size_pickup_pct))
    flagged = {s.strip() for f in mill.findings if f.kind == "beam_warp_excess" for s in f.evidence.scope.get("yarn_lots", "").split(",")}
    lot_rows = []
    for lot, p in LP.items():
        L = lots.get(lot)
        lot_rows.append({"lot": lot, "supplier": L.supplier if L else None, "style": next((refs.style_code(refs.beams[r.beam_id].style_id) for r in prod_rows if lot_of(r) == lot), None),
                         "strength_cn_tex": float(L.strength_cn_tex) if L and L.strength_cn_tex is not None else None, "elongation_pct": float(L.elongation_pct) if L and L.elongation_pct is not None else None,
                         "cv_pct": float(L.cv_pct) if L and L.cv_pct is not None else None, "size_pickup_pct": r1(sum(sizep[lot]) / len(sizep[lot])) if sizep.get(lot) else None, "beams": len(beams_of[lot]),
                         "warp_stops_per_100k": r1(LS[lot].per_100k_picks(p.picks), 2) if lot in LS and p.picks > 0 else 0.0, "efficiency_pct": r1(p.efficiency_pct), "flagged": lot in flagged})
    lot_rows.sort(key=lambda r: (not r["flagged"], -(r["warp_stops_per_100k"] or 0)))
    lots_total = len(lot_rows)
    lot_rows = lot_rows[:12]
    rolls = mill.db.execute(select(m.WvInspection, m.WvLoom.loom_code, m.WvStyle.style_code, m.WvShift.name).join(m.WvLoom, m.WvLoom.id == m.WvInspection.loom_id).join(m.WvStyle, m.WvStyle.id == m.WvInspection.style_id)
                            .join(m.WvShift, m.WvShift.id == m.WvInspection.shift_id).where(m.WvInspection.grade != "A", m.WvInspection.shift_date >= end - timedelta(days=3)).order_by(m.WvInspection.inspected_at.desc()).limit(14)).all()
    recent = []
    for i, lc, sc, sh in rolls:
        obs = mill.db.scalars(select(m.WvDefectObservation).where(m.WvDefectObservation.inspection_id == i.id)).all()
        recent.append({"roll_no": i.roll_no, "loom": lc, "style": sc, "shift": sh, "grade": i.grade, "length_m": float(i.length_m), "defects": sum(o.defect_count for o in obs), "points": sum(o.points * o.defect_count for o in obs)})
    loom_q = calc.roll_quality(insp, defs, lambda r: r.loom_id)
    worst = sorted([(refs.loom_code(l), a) for l, a in loom_q.items() if a.length_m >= 150], key=lambda x: -(x[1].defects_per_100m or 0))[:8]
    qual_findings = [f for f in mill.findings if f.kind in ("beam_warp_excess", "shift_defect_shift")]
    return {"as_of": mill.now.isoformat(), "period": w.label,
            "kpis": [kpi("First grade", q.grade_a_pct, "%", pq.grade_a_pct, "up", [t["grade_a_pct"] for t in trend if t["grade_a_pct"] is not None]),
                     kpi("Defects per 100 m", q.defects_per_100m, "", pq.defects_per_100m, "down", [t["defects_per_100m"] for t in trend if t["defects_per_100m"] is not None], decimals=2),
                     kpi("Points per 100 m", q.points_per_100m, "", pq.points_per_100m, "down", [], "4-point system", decimals=1),
                     kpi("Third grade / reject", q.grade_c_pct, "%", pq.grade_c_pct, "down", []),
                     kpi("Inspected", q.length_m, "m", None, "up", [], f"{q.length_m / prod.meters * 100:.0f}% of fabric woven" if prod.meters else "", decimals=0)],
            "trend": trend, "defect_types": types, "by_shift": by_shift, "style_shift": {"shifts": [refs.shift_name(i) for i in sorted(refs.shifts, key=lambda i: refs.shifts[i].sort_order)], "rows": heat},
            "yarn_lots": lot_rows, "yarn_lots_total": lots_total, "recent_rolls": recent, "worst_looms": [{"loom": c, "defects_per_100m": r1(a.defects_per_100m, 2), "grade_a_pct": r1(a.grade_a_pct), "inspected_m": round(a.length_m)} for c, a in worst],
            "findings": mill.finding_dicts(qual_findings[:4]),
            "notes": ["Only inspected fabric counts: rolls not yet inspected are not assumed clean.", "Yarn-lot figures cover the last 14 production days. A weaker lot is evidence worth testing, not proof of cause."]}


def actions_page(mill: Mill) -> dict:
    A = m.WvAction
    rows = mill.db.scalars(select(A).where(A.status != "CANCELLED")).all()
    order = {"OPEN": 0, "IN_PROGRESS": 1, "COMPLETED": 2}
    rows.sort(key=lambda a: (order.get(a.status, 3), a.due_date or date.max))
    today = mill.ctx.today
    items = [{"ref": a.action_ref, "issue": a.issue, "action": a.action, "owner_role": a.owner_role, "owner": a.owner_name, "due": a.due_date.isoformat() if a.due_date else None,
              "overdue": bool(a.due_date and a.status in ("OPEN", "IN_PROGRESS") and a.due_date < today), "status": a.status, "finding_key": a.finding_key, "requires_approval": a.requires_approval, "approved": a.approved_at is not None,
              "expected_impact_lakhs": mill.lakhs(float(a.expected_impact_lakhs or 0)), "outcome_note": a.outcome_note, "verified_cause": a.verified_cause, "completed_at": a.completed_at.isoformat() if a.completed_at else None,
              "created_at": a.created_at.isoformat() if a.created_at else None} for a in rows]
    open_items = [i for i in items if i["status"] in ("OPEN", "IN_PROGRESS")]
    return {"as_of": mill.now.isoformat(), "money_visible": mill.money, "can_approve": mill.money,
            "summary": {"open": sum(1 for i in items if i["status"] == "OPEN"), "in_progress": sum(1 for i in items if i["status"] == "IN_PROGRESS"), "completed": sum(1 for i in items if i["status"] == "COMPLETED"),
                        "overdue": sum(1 for i in open_items if i["overdue"]), "value_open_lakhs": mill.lakhs(sum(float(a.expected_impact_lakhs or 0) for a in rows if a.status in ("OPEN", "IN_PROGRESS")))},
            "actions": items, "owner_roles": ["OWNER", "WEAVING_MANAGER", "SHIFT_SUPERVISOR", "MAINTENANCE", "QUALITY"]}
