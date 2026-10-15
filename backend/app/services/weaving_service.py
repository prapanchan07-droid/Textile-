"""
Weaving module (MOCK DATA).

Everything here is generated deterministically from a fixed seed so the
numbers stay identical between requests and across pages. The response is
flagged ``data_source = "MOCK"`` and the UI shows a banner saying so.
Replace ``_build_dataset`` with a DB-backed loader later; the aggregation and
decision logic below does not change.
"""
import random
from datetime import date, timedelta
from functools import lru_cache
from typing import Dict, List

from app.schemas.weaving import (
    WeavingAction, WeavingDecision, WeavingDefect, WeavingDeptStaff, WeavingGradeCount,
    WeavingGroupRow, WeavingKpis, WeavingLoom, WeavingMaintenance, WeavingModuleResponse,
    WeavingPeople, WeavingPmItem, WeavingQuality, WeavingShiftRow, WeavingShiftStaff,
    WeavingStopCause, WeavingStyle, WeavingTrendPoint,
)

HISTORY_DAYS = 60
TARGET_EFF = 92.0  # owner-set efficiency target (% of loom capacity)
SHIFTS = ["Shift I", "Shift II", "Shift III"]
SHIFT_OUTPUT_SHARE = [0.345, 0.335, 0.32]

# cause -> (weight, advice)
CAUSES: Dict[str, tuple] = {
    "Warp break": (0.26, "Check warp yarn strength and sizing pick-up. Review the beam lot with the sizing team."),
    "Weft break": (0.22, "Check weft yarn count variation, nozzle pressure and the feeder setting."),
    "Mechanical": (0.14, "Move these looms to the next preventive-maintenance slot. Check wear parts."),
    "Electrical / Power": (0.08, "Inspect the sub-station feeder and the loom drives. Log voltage dips."),
    "Beam change / no beam": (0.12, "Pre-stage the next beam. Plan the knotting and gaiting ahead of the run-out."),
    "Style change": (0.06, "Batch similar styles together to cut changeover time."),
    "Waiting for fitter": (0.07, "Re-balance fitters across the floor. Add a floater in the shift with the most waiting."),
    "Yarn quality": (0.05, "Hold the yarn lot and raise it with spinning QA."),
}
CAUSE_NAMES = list(CAUSES)

# style -> (fabric, rate/m, cost/m)
STYLES: Dict[str, tuple] = {
    "S-101": ("Poplin 60x60", 118.0, 96.0),
    "S-204": ("Twill 20x16", 142.0, 118.0),
    "S-310": ("Canvas 10x10", 175.0, 168.0),
    "S-415": ("Shirting 40x40", 132.0, 101.0),
    "S-522": ("Sheeting 30x30", 109.0, 95.0),
    "S-630": ("Drill 16x12", 156.0, 139.0),
}
VAR_COST_SHARE = 0.60  # share of cost that is variable; the rest is fixed

DEFECTS = ["Float", "Slub", "Missing pick", "Oil stain", "Warp streak", "Hole"]

# Current stoppages ("right now" snapshot): loom -> (reason, minutes stopped)
LIVE_STOPS = {
    "AJ-14": ("Weft break", 187),
    "SZ-05": ("Mechanical", 95),
    "AJ-33": ("Electrical / Power", 42),
    "SZ-09": ("Waiting for fitter", 64),
    "AJ-08": ("Warp break", 12),
    "AJ-21": ("Beam change / no beam", 38),
}
LIVE_IDLE = {"SZ-12", "AJ-36"}

PERIOD_LABELS = {"TODAY": "Today", "YESTERDAY": "Yesterday", "LAST_7_DAYS": "Last 7 days", "THIS_MONTH": "This month"}


def _clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def _style_for(loom_id: str, idx: int) -> str:
    if loom_id.startswith("SZ"):
        return "S-310" if idx < 4 else ("S-630" if idx < 8 else "S-204")
    if idx < 10:
        return "S-101"
    if idx < 18:
        return "S-415"
    if idx < 26:
        return "S-522"
    return "S-415" if idx < 30 else "S-101"


@lru_cache(maxsize=1)
def _build_dataset() -> dict:
    rng = random.Random(20261014)
    today = date.today()
    days = [today - timedelta(days=HISTORY_DAYS - 1 - i) for i in range(HISTORY_DAYS)]

    looms = []
    for i in range(36):
        looms.append({"id": f"AJ-{i + 1:02d}", "type": "Airjet", "idx": i, "cap": 565.0, "rpm": 850, "base_eff": 90.0})
    for i in range(12):
        looms.append({"id": f"SZ-{i + 1:02d}", "type": "Sulzer", "idx": i, "cap": 360.0, "rpm": 420, "base_eff": 85.5})

    for n, lm in enumerate(looms):
        lm["style"] = _style_for(lm["id"], lm["idx"])
        lm["base_eff"] += rng.uniform(-1.5, 1.5)
        lm["base_defects"] = rng.uniform(1.6, 2.6)
        w = {c: CAUSES[c][0] * rng.uniform(0.7, 1.3) for c in CAUSE_NAMES}
        lm["weights"] = w
        lm["weaver"] = f"W-{n // 4 + 1:03d}"
        lm["fitter"] = f"F-{n // 12 + 1:02d}"

    by_id = {lm["id"]: lm for lm in looms}
    # Planted problems so the analytics have something real to find.
    by_id["AJ-14"]["weights"]["Weft break"] *= 4.0
    by_id["AJ-27"]["base_defects"] = 4.8
    by_id["SZ-05"]["base_eff"] = 80.0
    by_id["SZ-05"]["weights"]["Mechanical"] *= 4.5
    by_id["AJ-33"]["weights"]["Electrical / Power"] *= 5.0
    by_id["SZ-09"]["weights"]["Waiting for fitter"] *= 5.0
    by_id["SZ-01"]["base_eff"] = 85.0

    records: List[dict] = []  # one per loom per day
    for di, d in enumerate(days):
        day_wave = 1.0 + (0.6 if d.weekday() == 0 else 0.0)  # Monday restart losses
        for lm in looms:
            eff = lm["base_eff"] + rng.gauss(0, 1.6) - (day_wave - 1.0) * 1.5
            if lm["id"] == "AJ-14" and di >= HISTORY_DAYS - 6:
                eff -= 4.0 + (di - (HISTORY_DAYS - 6)) * 2.2  # worsening over the last six days
            if lm["id"] == "SZ-05":
                eff -= rng.uniform(0, 3)
            eff = _clamp(eff, 50.0, 98.5)
            cap = lm["cap"]
            actual = cap * eff / 100.0
            target = cap * TARGET_EFF / 100.0
            lost_min = (100.0 - eff) / 100.0 * 1440.0
            wsum = sum(lm["weights"].values())
            causes = {c: lost_min * 0.92 * (lm["weights"][c] / wsum) * rng.uniform(0.85, 1.15) for c in CAUSE_NAMES}
            defects = max(0.6, lm["base_defects"] + rng.gauss(0, 0.35))
            grade_a = _clamp(97.5 - defects * 1.9 + rng.gauss(0, 0.4), 70, 99)
            records.append({
                "day": di, "date": d, "loom": lm["id"], "eff": eff, "actual": actual, "target": target,
                "causes": causes, "defects": defects, "grade_a": grade_a,
            })
    return {"days": days, "looms": looms, "records": records, "today": today}


def _window(period: str, today: date) -> int:
    if period == "TODAY":
        return 1
    if period == "YESTERDAY":
        return 1
    if period == "LAST_7_DAYS":
        return 7
    return max(1, today.day)  # month to date


def _contribution_per_m(style: str) -> float:
    _, rate, cost = STYLES[style]
    return rate - cost * VAR_COST_SHARE


def _agg(records: List[dict], looms_by_id: dict) -> dict:
    """Totals over a set of per-loom-day records."""
    out = {"actual": 0.0, "target": 0.0, "cap": 0.0, "loss_m": 0.0, "loss_lakhs": 0.0, "revenue": 0.0,
           "grade_a_m": 0.0, "defect_w": 0.0, "causes": {c: 0.0 for c in CAUSE_NAMES},
           "cause_loss": {c: 0.0 for c in CAUSE_NAMES}, "per_loom": {}}
    for r in records:
        lm = looms_by_id[r["loom"]]
        style = lm["style"]
        short = max(0.0, r["target"] - r["actual"])
        contrib = _contribution_per_m(style)
        out["actual"] += r["actual"]
        out["target"] += r["target"]
        out["cap"] += lm["cap"]
        out["loss_m"] += short
        out["loss_lakhs"] += short * contrib / 100000.0
        out["revenue"] += r["actual"] * STYLES[style][1] / 100000.0
        out["grade_a_m"] += r["actual"] * r["grade_a"] / 100.0
        out["defect_w"] += r["defects"] * r["actual"]
        tot_c = sum(r["causes"].values()) or 1.0
        for c, m in r["causes"].items():
            out["causes"][c] += m
            out["cause_loss"][c] += short * contrib / 100000.0 * (m / tot_c)
        pl = out["per_loom"].setdefault(r["loom"], {"actual": 0.0, "target": 0.0, "cap": 0.0, "loss_m": 0.0, "loss_lakhs": 0.0,
                                                    "grade_a_m": 0.0, "defect_w": 0.0, "causes": {c: 0.0 for c in CAUSE_NAMES}})
        pl["actual"] += r["actual"]
        pl["target"] += r["target"]
        pl["cap"] += lm["cap"]
        pl["loss_m"] += short
        pl["loss_lakhs"] += short * contrib / 100000.0
        pl["grade_a_m"] += r["actual"] * r["grade_a"] / 100.0
        pl["defect_w"] += r["defects"] * r["actual"]
        for c, m in r["causes"].items():
            pl["causes"][c] += m
    return out


def _pct(a: float, b: float) -> float:
    return round(a / b * 100.0, 1) if b else 0.0


def _chg_pct(cur: float, prev: float) -> float:
    return round((cur - prev) / prev * 100.0, 1) if prev else 0.0


class WeavingService:
    @staticmethod
    def get_weaving_data(period: str = "TODAY") -> WeavingModuleResponse:
        period = period if period in PERIOD_LABELS else "TODAY"
        ds = _build_dataset()
        today: date = ds["today"]
        looms = ds["looms"]
        looms_by_id = {lm["id"]: lm for lm in looms}
        recs = ds["records"]
        last = HISTORY_DAYS - 1

        n = _window(period, today)
        end = last - (1 if period == "YESTERDAY" else 0)
        cur_days = range(end - n + 1, end + 1)
        prev_days = range(end - 2 * n + 1, end - n + 1)
        cur = [r for r in recs if r["day"] in cur_days]
        prev = [r for r in recs if r["day"] in prev_days]
        a, p = _agg(cur, looms_by_id), _agg(prev, looms_by_id)

        eff = _pct(a["actual"], a["cap"])
        eff_prev = _pct(p["actual"], p["cap"])
        ga = _pct(a["grade_a_m"], a["actual"])
        ga_prev = _pct(p["grade_a_m"], p["actual"])

        # ---- live snapshot ----
        statuses = {}
        for lm in looms:
            if lm["id"] in LIVE_STOPS:
                statuses[lm["id"]] = "STOPPED"
            elif lm["id"] in LIVE_IDLE:
                statuses[lm["id"]] = "IDLE"
            else:
                statuses[lm["id"]] = "RUNNING"
        running = sum(1 for s in statuses.values() if s == "RUNNING")
        stopped = sum(1 for s in statuses.values() if s == "STOPPED")
        idle = sum(1 for s in statuses.values() if s == "IDLE")

        kpis = WeavingKpis(
            fabric_m=round(a["actual"]), target_m=round(a["target"]), achievement_pct=_pct(a["actual"], a["target"]),
            efficiency_pct=eff, grade_a_pct=ga, loss_lakhs=round(a["loss_lakhs"], 2), loss_m=round(a["loss_m"]),
            revenue_lakhs=round(a["revenue"], 2),
            fabric_change_pct=_chg_pct(a["actual"], p["actual"]), efficiency_change_pts=round(eff - eff_prev, 1),
            grade_a_change_pts=round(ga - ga_prev, 1), loss_change_pct=_chg_pct(a["loss_lakhs"], p["loss_lakhs"]),
            looms_total=len(looms), looms_running=running, looms_stopped=stopped, looms_idle=idle,
        )

        # ---- looms ----
        loom_rows: List[WeavingLoom] = []
        for lm in looms:
            pl = a["per_loom"][lm["id"]]
            l_eff = _pct(pl["actual"], pl["cap"])
            defects = round(pl["defect_w"] / pl["actual"], 2) if pl["actual"] else 0.0
            top_cause = max(pl["causes"], key=pl["causes"].get)
            health = "NORMAL"
            crit_eff, warn_eff = (80, 86) if lm["type"] == "Airjet" else (77, 82)
            if l_eff < crit_eff or defects > 4.0:
                health = "CRITICAL"
            elif l_eff < warn_eff or defects > 3.2:
                health = "ATTENTION"
            issue = "High fabric defects" if defects > 3.2 else (top_cause if health != "NORMAL" else "None")
            hist = [round(r["eff"], 1) for r in recs if r["loom"] == lm["id"] and r["day"] > last - 14]
            reason, since = LIVE_STOPS.get(lm["id"], (None, 0))
            stops_n = int(sum(pl["causes"].values()) / 6.5)  # average stop is about 6.5 minutes
            loom_rows.append(WeavingLoom(
                loom_id=lm["id"], loom_type=lm["type"], style=lm["style"], status=statuses[lm["id"]], health=health,
                rpm=0 if statuses[lm["id"]] != "RUNNING" else int(lm["rpm"] * _clamp(0.97 + (l_eff - 90) / 400.0, 0.9, 1.0)),
                efficiency_pct=l_eff, actual_m=round(pl["actual"]), target_m=round(pl["target"]),
                loss_m=round(pl["loss_m"]), loss_lakhs=round(pl["loss_lakhs"], 2),
                grade_a_pct=_pct(pl["grade_a_m"], pl["actual"]), defects_per_100m=defects, stops=stops_n,
                stop_reason=reason, stopped_since_min=since, weaver=lm["weaver"], fitter=lm["fitter"],
                main_issue=issue, trend=hist,
            ))

        # ---- stoppage causes ----
        tot_min = sum(a["causes"].values()) or 1.0
        stop_causes = [
            WeavingStopCause(
                cause=c, minutes=round(m), stops=max(1, round(m / 6.5)), loss_lakhs=round(a["cause_loss"][c], 2),
                share_pct=round(m / tot_min * 100, 1), advice=CAUSES[c][1],
            )
            for c, m in sorted(a["causes"].items(), key=lambda kv: kv[1], reverse=True)
        ]
        top_cause = stop_causes[0]

        # ---- trend (always at least a week for context) ----
        tn = max(n, 7) if period != "YESTERDAY" else 7
        t_days = range(end - tn + 1, end + 1)
        trend = []
        for di in t_days:
            dr = [r for r in recs if r["day"] == di]
            da = _agg(dr, looms_by_id)
            trend.append(WeavingTrendPoint(
                date_label=ds["days"][di].strftime("%d %b"), actual_m=round(da["actual"]), target_m=round(da["target"]),
                efficiency_pct=_pct(da["actual"], da["cap"]), grade_a_pct=_pct(da["grade_a_m"], da["actual"]),
                loss_lakhs=round(da["loss_lakhs"], 2),
            ))

        # ---- shifts ----
        shift_factor = [1.012, 1.0, 0.972]
        shift_cause_bias = [
            {"Warp break": 1.0, "Weft break": 1.0},
            {"Weft break": 1.35, "Warp break": 0.95},
            {"Waiting for fitter": 2.2, "Electrical / Power": 1.4, "Mechanical": 1.2},
        ]
        shifts = []
        for si, sname in enumerate(SHIFTS):
            s_act = a["actual"] * SHIFT_OUTPUT_SHARE[si] * shift_factor[si] / (sum(x * f for x, f in zip(SHIFT_OUTPUT_SHARE, shift_factor)))
            s_tar = a["target"] * SHIFT_OUTPUT_SHARE[si]
            s_cap = a["cap"] * SHIFT_OUTPUT_SHARE[si]
            biased = {c: a["causes"][c] * shift_cause_bias[si].get(c, 1.0) for c in CAUSE_NAMES}
            shifts.append(WeavingShiftRow(
                shift=sname, actual_m=round(s_act), target_m=round(s_tar), efficiency_pct=_pct(s_act, s_cap),
                grade_a_pct=round(ga + [0.6, 0.0, -1.1][si], 1), top_stop_reason=max(biased, key=biased.get),
            ))

        # ---- groups ----
        groups = []
        for typ in ["Airjet", "Sulzer"]:
            ids = [lm["id"] for lm in looms if lm["type"] == typ]
            g = [a["per_loom"][i] for i in ids]
            g_act, g_cap, g_tar = sum(x["actual"] for x in g), sum(x["cap"] for x in g), sum(x["target"] for x in g)
            groups.append(WeavingGroupRow(
                loom_type=typ, looms=len(ids), actual_m=round(g_act), target_m=round(g_tar), efficiency_pct=_pct(g_act, g_cap),
                grade_a_pct=_pct(sum(x["grade_a_m"] for x in g), g_act), loss_lakhs=round(sum(x["loss_lakhs"] for x in g), 2),
            ))

        # ---- quality ----
        def_total = max(1, round(a["defect_w"] / 100.0))
        weights = [0.24, 0.20, 0.18, 0.14, 0.15, 0.09]
        defect_types = [
            WeavingDefect(defect=d, count=round(def_total * w), share_pct=round(w * 100, 1)) for d, w in zip(DEFECTS, weights)
        ]
        grade_b = round((100 - ga) * 0.72, 1)
        grade_c = round(100 - ga - grade_b, 1)
        rejected_m = round(a["actual"] * grade_c / 100.0)
        # revenue given up when a metre sells as B (-18%) or C (-45%)
        avg_rate = a["revenue"] * 100000.0 / a["actual"] if a["actual"] else 0
        downgrade = (a["actual"] * grade_b / 100 * avg_rate * 0.18 + a["actual"] * grade_c / 100 * avg_rate * 0.45) / 100000.0
        worst = sorted(loom_rows, key=lambda r: r.defects_per_100m, reverse=True)[:8]
        quality = WeavingQuality(
            grade_a_pct=ga, grade_b_pct=grade_b, grade_c_pct=grade_c,
            defects_per_100m=round(a["defect_w"] / a["actual"], 2) if a["actual"] else 0.0,
            rejected_m=rejected_m, downgrade_loss_lakhs=round(downgrade, 2), defect_types=defect_types,
            worst_looms=[{"loom_id": w.loom_id, "style": w.style, "defects_per_100m": w.defects_per_100m,
                          "grade_a_pct": w.grade_a_pct, "weaver": w.weaver} for w in worst],
        )

        # ---- styles ----
        style_rows: List[WeavingStyle] = []
        for sid, (fabric, rate, cost) in STYLES.items():
            ids = [lm["id"] for lm in looms if lm["style"] == sid]
            g = [a["per_loom"][i] for i in ids]
            m = sum(x["actual"] for x in g)
            cap = sum(x["cap"] for x in g)
            s_eff = _pct(m, cap)
            s_ga = _pct(sum(x["grade_a_m"] for x in g), m)
            # effective cost rises when efficiency is low (fixed cost spread over fewer metres)
            eff_cost = cost * VAR_COST_SHARE + cost * (1 - VAR_COST_SHARE) * (TARGET_EFF / max(s_eff, 1))
            real_rate = rate * (1 - (100 - s_ga) / 100 * 0.3)
            margin = (real_rate - eff_cost) / real_rate * 100
            profit = (real_rate - eff_cost) * m / 100000.0
            if margin < 3:
                rec, why = "STOP", "Margin is close to zero. Every extra metre adds little profit and ties up looms."
            elif margin < 10:
                rec, why = "REPRICE", "Margin is thin. Ask for a higher rate on the next order or shift looms to better styles."
            elif margin >= 22 and s_eff >= 90:
                rec, why = "PUSH", "Healthy margin and the looms run well. Take more orders for this style."
            else:
                rec, why = "HOLD", "Acceptable margin. Keep the current loom allocation."
            style_rows.append(WeavingStyle(
                style=sid, fabric=fabric, meters=round(m), rate_per_m=rate, cost_per_m=round(eff_cost, 1),
                margin_pct=round(margin, 1), profit_lakhs=round(profit, 2), grade_a_pct=s_ga, efficiency_pct=s_eff,
                recommendation=rec, reason=why,
            ))
        style_rows.sort(key=lambda s: s.margin_pct, reverse=True)

        # ---- people (aggregate only, no named employees) ----
        dept_def = [
            ("Airjet weaving", 60, 57, "G1+"), ("Sulzer weaving", 16, 15, "G1"), ("Fabric checking", 20, 18, "G1"),
            ("Maintenance M/C", 12, 11, "G2"), ("Knotting", 4, 4, "G1"), ("Gaiting", 3, 3, "G1"),
            ("Electrical", 3, 3, "G2+"), ("Loading & unloading", 6, 5, "G2"),
        ]
        absence_today = {"Airjet weaving": 7, "Sulzer weaving": 2, "Fabric checking": 3, "Maintenance M/C": 2}
        depts = []
        for name, req, have, grade in dept_def:
            avail = have - absence_today.get(name, 0)
            gap = req - avail
            depts.append(WeavingDeptStaff(
                department=name, required=req, available=avail, gap=gap, avg_grade=grade,
                status="CRITICAL" if gap >= 8 else ("ATTENTION" if gap >= 3 else "NORMAL"),
            ))
        headcount = sum(d[2] for d in dept_def)
        avail_total = sum(d.available for d in depts)
        grades = [WeavingGradeCount(grade=g, count=c) for g, c in
                  [("G1+", 49), ("G1", 27), ("G2", 24), ("G2+", 9), ("G3", 7), ("G4", 5), ("G5", 2), ("G6", 3)]]
        shift_staff = []
        for si, sname in enumerate(SHIFTS):
            absent = [3, 4, 6][si]
            weavers = 22 - absent
            looms_pw = round(len(looms) / max(weavers, 1), 1)
            sh_out = a["actual"] / max(n, 1) * SHIFT_OUTPUT_SHARE[si]
            shift_staff.append(WeavingShiftStaff(
                shift=sname, looms_per_weaver=looms_pw, output_per_weaver_m=round(sh_out / max(weavers, 1)), absent=absent,
                status="CRITICAL" if looms_pw > 2.6 else ("ATTENTION" if looms_pw > 2.4 else "NORMAL"),
            ))
        people = WeavingPeople(
            headcount=headcount, available_today=avail_total,
            absenteeism_pct=round((headcount - avail_total) / headcount * 100, 1), departments=depts, grades=grades,
            shifts=shift_staff, promotion_ready=9, needs_training=6,
        )

        # ---- maintenance ----
        prng = random.Random(77)
        pm_items: List[WeavingPmItem] = []
        tasks = {"Airjet": ["Nozzle + cutter service", "Full cleaning & lubrication"], "Sulzer": ["Gripper + timing check", "Full cleaning & lubrication"]}
        for lm in looms:
            for t in tasks[lm["type"]]:
                off = prng.randint(-2, 40)
                if lm["id"] in ("AJ-14", "SZ-05") and "service" in t or lm["id"] == "SZ-05" and "check" in t:
                    off = -prng.randint(6, 12)
                due = today + timedelta(days=off)
                od = max(0, -off)
                pm_items.append(WeavingPmItem(
                    loom_id=lm["id"], task=t, due_date=due.isoformat(), days_overdue=od,
                    status="OVERDUE" if od > 0 else ("DUE_SOON" if off <= 5 else "OK"),
                ))
        overdue = [i for i in pm_items if i.status == "OVERDUE"]
        soon = [i for i in pm_items if i.status == "DUE_SOON"]
        mech_stops = (a["causes"]["Mechanical"] + a["causes"]["Electrical / Power"]) / 28.0
        run_hours = a["actual"] / max(a["cap"], 1) * len(looms) * 24 * n
        listed = sorted([i for i in pm_items if i.status != "OK"], key=lambda i: -i.days_overdue)[:24]
        maintenance = WeavingMaintenance(
            mtbf_hours=round(run_hours / max(mech_stops, 1), 1),
            mttr_min=round((a["causes"]["Mechanical"] + a["causes"]["Electrical / Power"]) / max(mech_stops, 1), 0),
            breakdowns=int(mech_stops), pm_overdue=len(overdue), pm_due_soon=len(soon),
            pm_compliance_pct=round((1 - len(overdue) / len(pm_items)) * 100, 1), items=listed,
        )

        # ---- decisions (rules first, so each one can be explained) ----
        decisions: List[WeavingDecision] = []
        worst_loom = max(loom_rows, key=lambda r: r.loss_lakhs)
        if worst_loom.health != "NORMAL":
            decisions.append(WeavingDecision(
                id="loom-loss", severity="HIGH" if worst_loom.efficiency_pct < 80 else "MEDIUM",
                title=f"Inspect loom {worst_loom.loom_id} now",
                why=f"Running at {worst_loom.efficiency_pct}% against a {TARGET_EFF:.0f}% target. Main issue: {worst_loom.main_issue}. "
                    f"It is the biggest single loss on the floor.",
                action=f"Send the senior fitter to {worst_loom.loom_id}. Check the main cause, then re-test for one shift.",
                owner="Weaving Manager", impact_lakhs=round(worst_loom.loss_lakhs, 2), link=f"/weaving/looms?loom={worst_loom.loom_id}",
            ))
        if top_cause.share_pct >= 20:
            decisions.append(WeavingDecision(
                id="top-stop", severity="HIGH" if top_cause.loss_lakhs > 1.0 else "MEDIUM",
                title=f"{top_cause.cause} is the biggest loss",
                why=f"{top_cause.share_pct}% of all stop time ({top_cause.minutes:,} min) and about ₹{top_cause.loss_lakhs} L of lost margin.",
                action=top_cause.advice, owner="Production Head", impact_lakhs=top_cause.loss_lakhs, link="/weaving/stoppages",
            ))
        bad_style = [s for s in style_rows if s.recommendation in ("STOP", "REPRICE")]
        if bad_style:
            s = bad_style[-1]
            decisions.append(WeavingDecision(
                id="style-margin", severity="HIGH" if s.recommendation == "STOP" else "MEDIUM",
                title=f"{s.style} {s.fabric}: {s.recommendation.lower()} the next order",
                why=f"Margin is only {s.margin_pct}% at {s.efficiency_pct}% loom efficiency. {s.reason}",
                action="Ask Sales to reprice, or move these looms to a higher-margin style.",
                owner="MD / Sales Head", impact_lakhs=round(max(0.0, 12 - s.margin_pct) / 100 * s.meters * s.rate_per_m / 100000.0, 2),
                link="/weaving/styles",
            ))
        hi_def = [r for r in loom_rows if r.defects_per_100m > 3.5]
        if hi_def:
            d = hi_def[0]
            decisions.append(WeavingDecision(
                id="quality-hold", severity="MEDIUM",
                title=f"Hold fabric from loom {d.loom_id} for inspection",
                why=f"{d.defects_per_100m} defects per 100 m and only {d.grade_a_pct}% first grade, against {quality.grade_a_pct}% for the floor.",
                action="Stop shipping its rolls until the cause (yarn lot, beam or loom settings) is confirmed.",
                owner="QA Head",
                impact_lakhs=round(max(0.0, d.actual_m * (ga - d.grade_a_pct) / 100 * avg_rate * 0.3 / 100000.0), 2), link="/weaving/quality",
            ))
        if maintenance.pm_overdue >= 3:
            decisions.append(WeavingDecision(
                id="pm-overdue", severity="MEDIUM",
                title=f"{maintenance.pm_overdue} preventive-maintenance jobs are overdue",
                why="Overdue service on the same looms that show the lowest efficiency raises the risk of a long breakdown.",
                action="Approve a planned stop slot this week for the overdue looms.",
                owner="Maintenance Head", impact_lakhs=round(maintenance.pm_overdue * 0.18, 2), link="/weaving/people",
            ))
        worst_shift = max(shift_staff, key=lambda s: s.looms_per_weaver)
        if worst_shift.status != "NORMAL":
            decisions.append(WeavingDecision(
                id="staffing", severity="MEDIUM",
                title=f"{worst_shift.shift} is short of weavers",
                why=f"{worst_shift.absent} absent, so each weaver covers {worst_shift.looms_per_weaver} looms against a safe limit of about 2.4.",
                action="Pull a pool weaver or a trained operator into this shift.",
                owner="HR & Manpower Head", impact_lakhs=round(a["loss_lakhs"] * 0.08, 2), link="/weaving/people",
            ))
        decisions.sort(key=lambda d: ({"HIGH": 0, "MEDIUM": 1, "LOW": 2}[d.severity], -d.impact_lakhs))

        verdict = (
            f"{PERIOD_LABELS[period]}: {round(a['actual']):,} m of fabric, {kpis.achievement_pct}% of target. "
            f"Weaving lost about ₹{kpis.loss_lakhs} L of margin, mostly from {top_cause.cause.lower()} ({top_cause.share_pct}% of stop time). "
            f"{len([d for d in decisions if d.severity == 'HIGH'])} urgent and {len([d for d in decisions if d.severity != 'HIGH'])} other decisions are waiting."
        )

        actions = [
            WeavingAction(id="A-101", issue="AJ-14 weft breaks rising", action="Check weft feeder and nozzle pressure; replace worn nozzle",
                          owner="Shift Fitter F-02", due=(today + timedelta(days=1)).isoformat(), status="IN_PROGRESS", impact_lakhs=0.9),
            WeavingAction(id="A-102", issue="SZ-05 mechanical stops", action="Full gripper and timing overhaul",
                          owner="Maintenance Manager", due=today.isoformat(), status="OPEN", impact_lakhs=0.7),
            WeavingAction(id="A-103", issue="Canvas S-310 margin below 3%", action="Re-quote the next canvas order at +₹12/m",
                          owner="Sales Head", due=(today + timedelta(days=4)).isoformat(), status="OPEN", impact_lakhs=1.1),
            WeavingAction(id="A-104", issue="Shift III short of weavers", action="Deploy 3 pool weavers to Shift III",
                          owner="HR & Manpower Head", due=(today + timedelta(days=2)).isoformat(), status="IN_PROGRESS", impact_lakhs=0.5),
            WeavingAction(id="A-105", issue="AJ-27 high defect rate", action="Hold rolls, check beam lot and reed",
                          owner="QA Head", due=(today + timedelta(days=1)).isoformat(), status="OPEN", impact_lakhs=0.4),
            WeavingAction(id="A-106", issue="Beam change delays", action="Pre-stage next beams before run-out",
                          owner="Preparatory Head", due=(today - timedelta(days=2)).isoformat(), status="COMPLETED", impact_lakhs=0.3),
        ]

        return WeavingModuleResponse(
            period=period, period_label=PERIOD_LABELS[period], days=n, verdict=verdict, kpis=kpis, decisions=decisions,
            trend=trend, shifts=shifts, groups=groups, looms=loom_rows, stop_causes=stop_causes, quality=quality,
            styles=style_rows, people=people, maintenance=maintenance, actions=actions,
        )
