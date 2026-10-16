"""
Deterministic DEMONSTRATION data for the weaving analytics.

  python -m app.weaving.seed demo [--days 21] [--end-date YYYY-MM-DD]

Properties
  * Everything it writes is marked data_origin = 'DEMO'. It refuses to run when ENVIRONMENT=production.
  * Deterministic: every number comes from a random generator seeded per (loom, day) / (roll), and the
    timeline is anchored to a stored epoch (system_info 'weaving_demo_epoch'), so the same days always
    produce the same rows no matter when the command is run.
  * Idempotent and non-destructive: rows are INSERTed with ON CONFLICT DO NOTHING on their business keys
    (loom_code, style_code, beam_no, order_no, roll_no, loom+start time ...). Existing rows are never
    modified or deleted. Re-running extends the history up to the current hour. The one exception is
    closing demo stoppages that were still open at the last run once their (deterministic) end has passed.

Planted situations (so the investigations have something to find). Day numbers count from the epoch.
  * AJ-14   weft stops rise ~3x and speed drops from day 9: an efficiency decline with a known start. Main-nozzle air
            pressure also drops ~0.9 bar from day 9 (a sensor signal that fits, but is not proof).
  * SZ-05   chronic mechanical stops (~6x), overdue preventive maintenance, and vibration/temperature creeping up from day 8.
  * SZ-07   electrical stops and ~20% higher power draw in Shift III.
  * AJ-09   no stops yet, but motor temperature and vibration drift upward from day 10 (an early warning).
  * AJ-22   its sensors drop out about a third of the time from day 12 (a data-quality alert).
  * S-415   beams carrying yarn lot YL-415-07 (mounted days 8-11) break warp ~2.4x more often; the lot has weaker incoming
            yarn tests and the beams a lower size pick-up.
  * S-204   float / warp-streak defects ~2.4x in Shift III from day 9.
  * AJ-18   defect rate ~2.2x all the time.
  * W-II-07 (a junior weaver) has ~1.7x the weft stops on whatever loom they run: a person-level coaching signal.
  * Shift III has fewer fitters (more waiting) and more absenteeism.
  * Order book: some orders are on track, some at risk (S-415, S-204), one is late (S-310): fodder for the AI scheduler.
"""
from __future__ import annotations

import math
import random
import zlib
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Dict, List, Optional, Tuple

from sqlalchemy import func, select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging import logger
from app.models.system import SystemInfo
from app.weaving import models as m
from app.weaving.analytics.calendar import MillCalendar, ShiftDef
from app.weaving.analytics.definitions import PICKS_PER_METRE_PER_PPI
from app.weaving.seed import content as C
from app.weaving.seed.reference import ensure_reference_data

DEMO = "DEMO"
EPOCH_KEY = "weaving_demo_epoch"
SEED_SALT = "ashok-demo-v1"
CHUNK = 5000

# code, fabric, weave, warp, weft, epi, ppi, width_in, target eff %, rate/m, std cost/m, variable cost/m, required loom type
STYLES = [
    ("S-101", "Poplin 60x60", "Plain", "60s", "60s", 144, 76, 58, 91, 118, 96, 58, None),
    ("S-204", "Twill 20x16", "Twill 3/1", "20s", "16s", 88, 58, 58, 90, 142, 118, 71, None),
    ("S-310", "Canvas 10x10", "Plain", "10s", "10s", 52, 42, 63, 86, 175, 168, 100, "Sulzer"),
    ("S-415", "Shirting 40x40", "Plain", "40s", "40s", 120, 68, 58, 91, 132, 101, 61, None),
    ("S-522", "Sheeting 30x30", "Plain", "30s", "30s", 96, 56, 90, 90, 109, 95, 57, None),
    ("S-630", "Drill 16x12", "Twill 3/1", "16s", "12s", 76, 52, 58, 87, 156, 139, 83, "Sulzer"),
]
N_AIRJET, N_SULZER = 24, 8
AIRJET_RPM, SULZER_RPM = 850, 420
CHANGE_LOOMS = {"AJ-05": "S-522", "AJ-06": "S-522", "AJ-19": "S-415", "SZ-03": "S-204"}  # switch style at day 10
STYLE_CHANGE_DAY = 10
DECLINE_DAY = 9
BAD_LOT = ("S-415", 7)
WEAK_WEAVER = "W-II-07"

# events per 100,000 picks, by loom type: warp, weft, mechanical, electrical, yarn, waiting
RATES = {
    "Airjet": {"WARP_BREAK": 1.5, "WEFT_BREAK": 1.3, "MECHANICAL": 0.12, "ELECTRICAL": 0.04, "YARN_QUALITY": 0.10, "WAITING_FITTER": 0.15},
    "Sulzer": {"WARP_BREAK": 1.3, "WEFT_BREAK": 0.7, "MECHANICAL": 0.20, "ELECTRICAL": 0.05, "YARN_QUALITY": 0.10, "WAITING_FITTER": 0.20},
}
# mean duration in minutes
DURATION = {"WARP_BREAK": 2.2, "WEFT_BREAK": 1.6, "MECHANICAL": 14.0, "ELECTRICAL": 9.0, "YARN_QUALITY": 3.5, "WAITING_FITTER": 4.5}

DEFECT_WEIGHTS = {"FLOAT": 0.24, "SLUB": 0.20, "MISSING_PICK": 0.18, "OIL_STAIN": 0.08, "WARP_STREAK": 0.15, "HOLE": 0.07, "REED_MARK": 0.08}
GRADE_THRESHOLDS = (8.0, 12.0, 18.0)  # points per 100 m: A <= 8, B <= 12, C <= 18, else REJECT (demo grading rule)


def _rng(*parts) -> random.Random:
    return random.Random(zlib.crc32("|".join(str(p) for p in (SEED_SALT, *parts)).encode()))


def _poisson(rng: random.Random, lam: float) -> int:
    if lam <= 0:
        return 0
    if lam > 30:
        return max(0, round(rng.gauss(lam, math.sqrt(lam))))
    L, k, p = math.exp(-lam), 0, 1.0
    while True:
        p *= rng.random()
        if p <= L:
            return k
        k += 1


def _lognormal(rng: random.Random, mean: float, sigma: float = 0.6) -> float:
    mu = math.log(mean) - sigma ** 2 / 2
    return rng.lognormvariate(mu, sigma)


@dataclass
class SeedReport:
    epoch: date
    end_date: date
    added: Dict[str, int] = field(default_factory=dict)
    closed_open_stops: int = 0

    def __str__(self) -> str:
        rows = "\n".join(f"  {k:<26}{v:>8}" for k, v in self.added.items())
        return f"Demo data {self.epoch} .. {self.end_date}  (rows newly inserted)\n{rows}\n  open stops closed          {self.closed_open_stops:>8}"


# ---------------------------------------------------------------------------- helpers

def _insert(db: Session, table, rows: List[dict]) -> None:
    for i in range(0, len(rows), CHUNK):
        db.execute(pg_insert(table).on_conflict_do_nothing(), rows[i:i + CHUNK])


def _count(db: Session, model, **where) -> int:
    q = select(func.count()).select_from(model)
    for k, v in where.items():
        q = q.where(getattr(model, k) == v)
    return db.scalar(q) or 0


def _loom_defs() -> List[dict]:
    looms = []
    for i in range(N_AIRJET):
        make, model, shed, colours, kw, reed = C.AIRJET_MODEL
        year = 2017 + (i * 5) % 5
        looms.append({"code": f"AJ-{i + 1:02d}", "type": "Airjet", "idx": i, "rpm": AIRJET_RPM, "make": make, "model": model, "reed": reed, "shedding": shed, "colours": colours,
                      "kw": kw, "year": year, "bay": f"Unit I · Bay {'ABCD'[i // 6]}", "serial": f"PIC-O8-{year}-{3100 + i * 7:04d}",
                      "overhaul": date(2025, 1 + (i * 3) % 11, 5 + i % 20), "warranty": date(2026, 12, 31) if year >= 2021 else None})
    for i in range(N_SULZER):
        make, model, shed, colours, kw, reed = C.SULZER_MODEL
        year = 2007 + (i * 3) % 5
        looms.append({"code": f"SZ-{i + 1:02d}", "type": "Sulzer", "idx": i, "rpm": SULZER_RPM, "make": make, "model": model, "reed": reed, "shedding": shed, "colours": colours,
                      "kw": kw, "year": year, "bay": "Unit II · Bay E", "serial": f"SUL-P7-{year}-{1180 + i * 11:04d}",
                      "overhaul": date(2024, 3 + i % 8, 10 + i), "warranty": None})
    styles_by_code = {s[0]: s for s in STYLES}
    for n, lm in enumerate(looms):
        if lm["type"] == "Sulzer":
            lm["style"] = "S-310" if lm["idx"] < 3 else ("S-630" if lm["idx"] < 6 else "S-204")
        else:
            lm["style"] = "S-101" if lm["idx"] < 8 else ("S-415" if lm["idx"] < 16 else "S-522")
        lm["alt_style"] = CHANGE_LOOMS.get(lm["code"])
        lm["n"] = n
        rr = _rng("loom", lm["code"])
        lm["speed"] = 0.972 + rr.uniform(-0.008, 0.008)
        lm["base_defects"] = rr.uniform(2.0, 3.2)
        # sensor baselines (a healthy loom's normal level)
        sr = _rng("sensorbase", lm["code"])
        lm["vib_base"] = (2.1 if lm["type"] == "Airjet" else 2.7) + sr.uniform(-0.2, 0.2)
        lm["temp_base"] = 57.0 + sr.uniform(-2.0, 2.0)
    assert all(l["style"] in styles_by_code for l in looms)
    return looms


# ---------------------------------------------------------------------------- the generator

def seed_demo(db: Session, *, now: Optional[datetime] = None, days: int = 21, end_date: Optional[date] = None) -> SeedReport:
    if settings.ENVIRONMENT.lower() == "production":
        raise RuntimeError("Demo data must never be loaded into a production environment (ENVIRONMENT=production).")
    if db.bind is not None and db.bind.dialect.name != "postgresql":
        raise RuntimeError("The weaving demo data needs PostgreSQL.")
    now = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    ensure_reference_data(db)

    shifts = [ShiftDef(s.id, s.code, s.name, s.start_time, s.end_time, s.sort_order) for s in db.scalars(select(m.WvShift).order_by(m.WvShift.sort_order))]
    cal = MillCalendar(settings.MILL_TIMEZONE, shifts)
    last_day = end_date or cal.production_day(now)
    epoch_row = db.scalar(select(SystemInfo).where(SystemInfo.key == EPOCH_KEY))
    if epoch_row is None:
        epoch = last_day - timedelta(days=days - 1)
        db.add(SystemInfo(id=f"sys-{EPOCH_KEY}", key=EPOCH_KEY, value=epoch.isoformat(), description="First production day of the weaving DEMO data"))
        db.flush()
    else:
        epoch = date.fromisoformat(epoch_row.value)
    if last_day < epoch:
        raise ValueError("end_date is before the demo epoch")

    before = {name: _count(db, model) for name, model in _TABLES.items()}
    loom_defs = _loom_defs()
    ids = _upsert_masters(db, loom_defs, epoch, cal)
    gen = _Generator(db, cal, loom_defs, ids, epoch, last_day, now)
    gen.run()
    report = SeedReport(epoch, last_day)
    db.flush()
    report.closed_open_stops = gen.converge_open_stops()
    db.flush()
    report.added = {name: _count(db, model) - before[name] for name, model in _TABLES.items()}
    logger.info(f"Weaving demo seed finished: {report.added}")
    return report


_TABLES = {
    "looms": m.WvLoom, "styles": m.WvStyle, "beams": m.WvBeam, "beam_mountings": m.WvBeamMounting,
    "production_orders": m.WvProductionOrder, "order_assignments": m.WvOrderAssignment, "operators": m.WvOperator,
    "shift_assignments": m.WvShiftAssignment, "attendance": m.WvAttendance, "loom_readings": m.WvLoomReading,
    "stop_events": m.WvStopEvent, "inspections": m.WvInspection, "defect_observations": m.WvDefectObservation,
    "maintenance_events": m.WvMaintenanceEvent, "actions": m.WvAction, "customers": m.WvCustomer, "yarn_lots": m.WvYarnLot, "shift_notes": m.WvShiftNote,
}


def _person(code: str) -> str:
    """A deterministic, unique, synthetic employee name for a business code."""
    r = _rng("person", code)
    return f"{r.choice(C.FIRST_NAMES)} {r.choice(C.INITIALS)}"


def _upsert_masters(db: Session, loom_defs: List[dict], epoch: date, cal: MillCalendar) -> dict:
    """Insert missing masters by business key, then return {business key: id} maps."""
    _insert(db, m.WvLoom.__table__, [
        dict(loom_code=l["code"], loom_type=l["type"], make=l["make"], model=l["model"], reed_space_cm=l["reed"], rated_rpm=l["rpm"],
             installed_on=date(l["year"], 6, 1) + timedelta(days=l["n"] * 3), is_active=True, serial_no=l["serial"], year_of_make=l["year"], shedding=l["shedding"],
             colours=l["colours"], power_kw_rated=l["kw"], bay=l["bay"], last_overhaul_on=l["overhaul"], warranty_until=l["warranty"], data_origin=DEMO) for l in loom_defs])
    _insert(db, m.WvStyle.__table__, [
        dict(style_code=s[0], fabric_name=s[1], weave=s[2], warp_count=s[3], weft_count=s[4], epi=s[5], ppi=s[6], width_in=s[7],
             target_efficiency_pct=s[8], rate_per_m=s[9], std_cost_per_m=s[10], variable_cost_per_m=s[11], loom_type_required=s[12], is_active=True, data_origin=DEMO)
        for s in STYLES])
    _insert(db, m.WvCustomer.__table__, [dict(code=c[0], name=c[1], segment=c[2], city=c[3], tier=c[4], data_origin=DEMO) for c in C.CUSTOMERS])
    db.flush()
    style_id = {r.style_code: r.id for r in db.scalars(select(m.WvStyle))}
    cust_id = {r.code: r.id for r in db.scalars(select(m.WvCustomer))}
    std_rate = {s[0]: s[9] for s in STYLES}
    orders = []
    for style, seq in C.RUNNING_ORDERS.items():
        for suffix, cust, qty, start, due, prio, adj in seq:
            orders.append(dict(order_no=f"SO-{suffix}", style_id=style_id[style], customer_id=cust_id[cust], customer=next(c[1] for c in C.CUSTOMERS if c[0] == cust),
                               priority=prio, rate_per_m=round(std_rate[style] * adj, 2), ordered_m=qty, start_date=epoch + timedelta(days=start), due_date=epoch + timedelta(days=due),
                               status="RUNNING", data_origin=DEMO))
    for suffix, style, cust, qty, due, prio in C.QUEUED_ORDERS:
        orders.append(dict(order_no=f"SO-{suffix}", style_id=style_id[style], customer_id=cust_id[cust], customer=next(c[1] for c in C.CUSTOMERS if c[0] == cust),
                           priority=prio, rate_per_m=round(std_rate[style] * 1.01, 2), ordered_m=qty, start_date=None, due_date=epoch + timedelta(days=due), status="PLANNED", data_origin=DEMO))
    _insert(db, m.WvProductionOrder.__table__, orders)
    # people: 9 weavers per shift (the 9th is the shift's floater), 3 fitters per shift, 1 supervisor per shift, 4 inspectors, 3 technicians
    shift_id = {s.code: s.id for s in db.scalars(select(m.WvShift))}
    ops = []

    def person(code, role, grade, shift_code, i):
        r = _rng("emp", code)
        senior = grade in ("G1+", "G1")
        years = round(r.uniform(6, 22) if senior else r.uniform(1, 7), 1)
        skills = "Airjet,Sulzer" if (senior and r.random() < 0.55) else ("Sulzer" if r.random() < 0.15 else "Airjet")
        design = C.DESIGNATIONS[role][1 if (senior and len(C.DESIGNATIONS[role]) > 1) else 0]
        ops.append(dict(employee_code=code, full_name=_person(code), operator_role=role, grade=grade, home_shift_id=shift_id[shift_code], is_active=True,
                        designation=design, department=C.DEPARTMENTS[role], contract_type="PERMANENT" if r.random() < 0.72 else "CONTRACT",
                        joined_on=epoch - timedelta(days=int(years * 365)), experience_years=years, skills=skills if role in ("WEAVER", "FITTER") else role.title(),
                        phone=f"+91 90000 {10000 + len(ops) * 7:05d}", data_origin=DEMO))

    for code, sid in shift_id.items():
        for w in range(1, 10):
            person(f"W-{code}-{w:02d}", "WEAVER", ("G1+", "G1", "G2", "G2+")[w % 4], code, w)
        for f in range(1, 4):
            person(f"F-{code}-{f:02d}", "FITTER", ("G1", "G2")[f % 2], code, f)
    for sc, shift_code in C.SUPERVISORS:
        person(sc, "SUPERVISOR", "G1+", shift_code, 1)
    for i in range(1, 5):
        person(f"I-{i:02d}", "INSPECTOR", "G2", "I" if i < 3 else "II", i)
    for i in range(1, 4):
        person(f"T-{i:02d}", "TECHNICIAN", "G1", "I", i)
    _insert(db, m.WvOperator.__table__, ops)
    db.flush()
    return {
        "style": style_id,
        "customer": cust_id,
        "order": {r.order_no: r.id for r in db.scalars(select(m.WvProductionOrder))},
        "loom": {r.loom_code: r.id for r in db.scalars(select(m.WvLoom))},
        "op": {r.employee_code: r.id for r in db.scalars(select(m.WvOperator))},
        "shift": shift_id,
        "reason": {r.code: r.id for r in db.scalars(select(m.WvStopReason))},
        "defect": {r.code: r.id for r in db.scalars(select(m.WvDefectType))},
        "beam": {},
    }


@dataclass
class _BeamPlan:
    k: int
    start: datetime
    end: datetime
    style: str
    beam_no: str
    lot: str
    style_change: bool


class _Generator:
    def __init__(self, db, cal: MillCalendar, loom_defs, ids, epoch: date, last_day: date, now: datetime):
        self.db, self.cal, self.looms, self.ids, self.epoch, self.last_day, self.now = db, cal, loom_defs, ids, epoch, last_day, now
        self.shifts = {s.id: s for s in cal.shifts}
        self.shift_by_code = {s.code: s for s in cal.shifts}
        self.epoch_start = cal.day_bounds(epoch)[0]
        self.horizon = cal.day_bounds(last_day)[1]
        self.style_ppi = {s[0]: float(s[6]) for s in STYLES}
        self.rows: Dict[str, List[dict]] = {k: [] for k in (
            "beams", "mountings", "assign", "shift_assign", "attendance", "readings", "stops", "inspections", "maintenance")}
        self.defects_by_roll: Dict[str, List[dict]] = {}
        self.lots: Dict[str, dict] = {}
        # per style: [(order_no, start, end)] in time order; the last order is open-ended
        self.order_seq: Dict[str, List[Tuple[str, datetime, Optional[datetime]]]] = {}
        for style, seq in C.RUNNING_ORDERS.items():
            seq = sorted(seq, key=lambda o: o[3])
            self.order_seq[style] = [(f"SO-{o[0]}", self.epoch_start + timedelta(days=o[3]), self.epoch_start + timedelta(days=seq[i + 1][3]) if i + 1 < len(seq) else None) for i, o in enumerate(seq)]
        self.stop_end: Dict[Tuple[int, datetime], Optional[datetime]] = {}
        self.breakdown_keys: List[Tuple[str, int, datetime, str]] = []

    # --- plans -----------------------------------------------------------------

    def order_for(self, style: str, t: datetime) -> str:
        seq = self.order_seq[style]
        for no, st, en in seq:
            if t >= st and (en is None or t < en):
                return no
        return seq[0][0]

    def day_offset(self, d: date) -> int:
        return (d - self.epoch).days

    def beam_plans(self, lm) -> List[_BeamPlan]:
        """Beams on a loom, back to back. A loom with an alternate style switches at the first beam boundary after STYLE_CHANGE_DAY."""
        cycle_h = round(24 * (3.4 + (lm["idx"] % 5) * 0.3))
        t0 = self.epoch_start - timedelta(hours=(lm["n"] * 7) % cycle_h + 1)
        switch_at = self.epoch_start + timedelta(days=STYLE_CHANGE_DAY)
        k_switch = math.ceil((switch_at - t0).total_seconds() / 3600 / cycle_h) if lm["alt_style"] else None
        plans, k, t = [], 0, t0
        while t < self.horizon:
            style = lm["alt_style"] if k_switch is not None and k >= k_switch else lm["style"]
            off_days = math.floor((t - self.epoch_start).total_seconds() / 86400)
            bucket = (off_days + 20) // 4
            plans.append(_BeamPlan(k, t, t + timedelta(hours=cycle_h), style, f"B-{style[2:]}-{lm['code']}-{k:03d}", f"YL-{style[2:]}-{bucket:02d}", k == k_switch))
            k += 1
            t += timedelta(hours=cycle_h)
        return plans

    def run(self) -> None:
        ids, db = self.ids, self.db
        days = [self.epoch + timedelta(days=i) for i in range((self.last_day - self.epoch).days + 1)]
        self._attendance_and_assignments(days)
        for lm in self.looms:
            self._simulate_loom(lm, days)
        self._flush_rows()

    # --- people ----------------------------------------------------------------

    def _attendance_and_assignments(self, days: List[date]) -> None:
        ids = self.ids
        self.op_code = {v: k for k, v in ids["op"].items()}
        self.weaver_of: Dict[Tuple[date, int, str], int] = {}
        self.fitter_of: Dict[Tuple[date, int, str], int] = {}
        self.absent_cover: Dict[Tuple[date, int, str], bool] = {}
        loom_codes = [l["code"] for l in self.looms]
        for d in days:
            for s in self.cal.shifts:
                code = s.code
                rng = _rng("roster", d.isoformat(), code)
                p_absent = 0.12 if code == "III" else 0.05
                weavers = [f"W-{code}-{i:02d}" for i in range(1, 10)]
                present = {w: rng.random() > p_absent for w in weavers}
                floater = weavers[-1]
                groups = [loom_codes[i:i + 4] for i in range(0, len(loom_codes), 4)]
                floater_used = False
                for gi, group in enumerate(groups):
                    owner = weavers[gi]
                    cover = owner
                    covered_by_other = False
                    if not present[owner]:
                        covered_by_other = True
                        if present[floater] and not floater_used:
                            cover, floater_used = floater, True
                        else:
                            cover = weavers[(gi + 1) % len(groups)] if present[weavers[(gi + 1) % len(groups)]] else floater
                    for lc in group:
                        self.weaver_of[(d, s.id, lc)] = ids["op"][cover]
                        self.absent_cover[(d, s.id, lc)] = covered_by_other
                        self.rows["shift_assign"].append(dict(shift_date=d, shift_id=s.id, loom_id=ids["loom"][lc], operator_id=ids["op"][cover], assignment_role="WEAVER", data_origin=DEMO))
                for w in weavers:
                    self.rows["attendance"].append(dict(shift_date=d, shift_id=s.id, operator_id=ids["op"][w], status="PRESENT" if present[w] else ("LEAVE" if rng.random() < 0.4 else "ABSENT"), data_origin=DEMO))
                for fi in range(1, 4):
                    fcode = f"F-{code}-{fi:02d}"
                    f_present = rng.random() > (0.10 if code == "III" else 0.04)
                    self.rows["attendance"].append(dict(shift_date=d, shift_id=s.id, operator_id=ids["op"][fcode], status="PRESENT" if f_present else "ABSENT", data_origin=DEMO))
                for li, lc in enumerate(loom_codes):
                    fcode = f"F-{code}-{li // 11 + 1:02d}"
                    self.fitter_of[(d, s.id, lc)] = ids["op"][fcode]
                    self.rows["shift_assign"].append(dict(shift_date=d, shift_id=s.id, loom_id=ids["loom"][lc], operator_id=ids["op"][fcode], assignment_role="FITTER", data_origin=DEMO))

    # --- one loom --------------------------------------------------------------

    def _simulate_loom(self, lm, days: List[date]) -> None:
        ids, cal = self.ids, self.cal
        loom_id = ids["loom"][lm["code"]]
        plans = self.beam_plans(lm)
        mounted = [p for p in plans if p.end > self.epoch_start and p.start < self.now]
        # beams, mountings and order assignments
        for p in mounted:
            sid = ids["style"][p.style]
            self.rows["beams"].append(dict(beam_no=p.beam_no, style_id=sid, total_ends=int(next(s[5] for s in STYLES if s[0] == p.style) * next(s[7] for s in STYLES if s[0] == p.style)),
                                          length_m=1200 + (lm["n"] * 37 + p.k * 53) % 400, yarn_lot=p.lot, sized_on=(p.start - timedelta(days=2)).date(),
                                          size_pickup_pct=round((6.2 if (p.style, int(p.lot.rsplit("-", 1)[1])) == BAD_LOT else 9.5) + _rng("size", p.beam_no).uniform(-0.5, 0.5), 1),
                                          status="MOUNTED" if p.start <= self.now < p.end else ("FINISHED" if p.end <= self.now else "READY"), data_origin=DEMO))
        for p in mounted:
            lot = self.lots.setdefault(p.lot, {"style": p.style, "first": p.start})
            lot["first"] = min(lot["first"], p.start)
        # order assignments: one row per stretch of time the loom works on the same order
        marks = sorted({p.start for p in mounted} | {t for no, st, en in self.order_seq.get(mounted[0].style, []) for t in (st, en) if t} | {t for sty in {p.style for p in mounted} for no, st, en in self.order_seq[sty] for t in (st, en) if t})
        marks = [t for t in marks if mounted[0].start <= t < mounted[-1].end]
        if mounted[0].start not in marks:
            marks.insert(0, mounted[0].start)
        segs: List[Tuple[datetime, str]] = []
        for t in marks:
            pl = next((p for p in mounted if p.start <= t < p.end), None)
            if pl is None:
                continue
            no = self.order_for(pl.style, t)
            if not segs or segs[-1][1] != no:
                segs.append((t, no))
        for i, (t0, no) in enumerate(segs):
            t1 = segs[i + 1][0] if i + 1 < len(segs) else None
            self.rows["assign"].append(dict(order_no=no, loom_id=loom_id, assigned_from=t0, assigned_to=t1, data_origin=DEMO))
        carry_until: Optional[datetime] = None
        ppi_m = lambda style: self.style_ppi[style] * PICKS_PER_METRE_PER_PPI
        meter_counter = 0.0
        roll_seq = 0
        next_roll_len = 100.0

        for d in days:
            day_start, day_end = cal.day_bounds(d)
            off = self.day_offset(d)
            rng = _rng("day", lm["code"], d.isoformat())
            # --- build stop intervals for the day
            intervals: List[Tuple[datetime, datetime, str, str]] = []  # start, end, reason, note
            for p in mounted:
                if day_start <= p.start < day_end and p.start > self.epoch_start:
                    dur = 90.0 if p.style_change else rng.uniform(32, 58)
                    intervals.append((p.start, p.start + timedelta(minutes=dur), "STYLE_CHANGE" if p.style_change else "BEAM_CHANGE", ""))
            pm_stop = self._pm_stop_for_day(lm, d)
            if pm_stop:
                intervals.append(pm_stop)
            s_rng = _rng("stops", lm["code"], d.isoformat())
            for h in range(24):
                hs = day_start + timedelta(hours=h)
                sday, shift = cal.shift_at(hs)
                plan = next(p for p in plans if p.start <= hs < p.end)
                mult = self._multipliers(lm, off, shift.code, plan)
                if self.op_code.get(self.weaver_of.get((sday, shift.id, lm["code"]))) == WEAK_WEAVER:
                    mult["WEFT_BREAK"] = mult.get("WEFT_BREAK", 1.0) * 1.7  # a junior weaver who needs coaching on weft handling
                picks_per_hour = lm["rpm"] * 60 * lm["speed"]
                for reason, rate in RATES[lm["type"]].items():
                    lam = rate * mult.get(reason, 1.0) * picks_per_hour / 100_000.0
                    for _ in range(_poisson(s_rng, lam)):
                        st = hs + timedelta(seconds=s_rng.uniform(0, 3599))
                        dur = _lognormal(s_rng, DURATION[reason] * mult.get("dur_" + reason, 1.0) * mult.get("dur", 1.0))
                        intervals.append((st, st + timedelta(minutes=min(max(dur, 0.25), 240)), reason, ""))
            intervals.sort(key=lambda x: x[0])
            resolved: List[Tuple[datetime, datetime, str]] = []
            cursor = carry_until
            for st, en, reason, _note in intervals:
                if cursor and st < cursor:
                    shift_by = cursor - st
                    st, en = cursor, en + shift_by
                resolved.append((st, en, reason))
                cursor = en
            carry_until = cursor if cursor and cursor > day_end else None
            # --- stop events (only those that began before `now`)
            for st, en, reason in resolved:
                if st >= self.now or st >= day_end:
                    continue
                sday2, shift = cal.shift_at(st)
                plan = next(p for p in plans if p.start <= st < p.end)
                key = (loom_id, st)
                self.stop_end[key] = en
                ended = en if en <= self.now else None
                self.rows["stops"].append(dict(
                    loom_id=loom_id, started_at=st, ended_at=ended, reason_id=ids["reason"][reason], shift_id=shift.id, shift_date=sday2,
                    style_id=ids["style"][plan.style], beam_id=None, weaver_id=self.weaver_of.get((sday2, shift.id, lm["code"])),
                    fitter_id=self.fitter_of.get((sday2, shift.id, lm["code"])), note=None, data_origin=DEMO, _beam_no=plan.beam_no))
                if reason in ("MECHANICAL", "ELECTRICAL") and (en - st).total_seconds() >= 1800:
                    self.breakdown_keys.append((lm["code"], loom_id, st, reason))
            # --- hourly readings
            for h in range(24):
                hs, he = day_start + timedelta(hours=h), day_start + timedelta(hours=h + 1)
                if he > self.now:
                    break
                sday, shift = cal.shift_at(hs)
                plan = next(p for p in plans if p.start <= hs < p.end)
                stopped = sum(max(0.0, (min(en, he) - max(st, hs)).total_seconds()) for st, en, _r in resolved if st < he and en > hs)
                running = int(round(max(0.0, 3600 - stopped)))
                speed = lm["speed"] * (1 + rng.gauss(0, 0.004))
                if lm["code"] == "AJ-14" and off >= DECLINE_DAY:
                    speed *= 0.965
                picks = int(round(lm["rpm"] * running / 60.0 * speed))
                r = rng.random()
                flag, picks_v = "OK", picks
                if r < 0.005:
                    flag, picks_v = "NO_PICKS", None
                elif r < 0.010:
                    flag, picks_v = "PARTIAL", int(picks * 0.9)
                sensors = self._sensors(lm, d, h, off, shift.code, running / 3600.0)
                self.rows["readings"].append(dict(
                    loom_id=loom_id, reading_start=hs, reading_end=he, duration_seconds=3600, shift_id=shift.id, shift_date=sday,
                    style_id=ids["style"][plan.style], beam_id=None, order_id=ids["order"][self.order_for(plan.style, hs)],
                    weaver_id=self.weaver_of.get((sday, shift.id, lm["code"])), running_seconds=running, picks=picks_v, quality_flag=flag,
                    data_origin=DEMO, _beam_no=plan.beam_no, **sensors))
                # --- rolls doffed from woven metres
                if picks_v is not None:
                    meter_counter += picks_v / ppi_m(plan.style)
                    while meter_counter >= next_roll_len:
                        meter_counter -= next_roll_len
                        roll_seq += 1
                        self._make_roll(lm, roll_seq, next_roll_len, he, sday, shift, plan, off)
                        next_roll_len = 90 + _rng("rolllen", lm["code"], roll_seq).uniform(0, 30)
        self._maintenance_plan(lm, days)

    def _sensors(self, lm, d: date, hour: int, off: int, shift_code: str, run_frac: float) -> dict:
        """Hourly machine sensors on their own random stream, so adding them never changes the stops or output."""
        r = _rng("sensor", lm["code"], d.isoformat(), hour)
        if lm["code"] == "AJ-22" and off >= 12 and r.random() < 0.35:
            return dict(power_kw=None, vibration_mm_s=None, motor_temp_c=None, air_pressure_bar=None)  # sensor dropout
        if r.random() < 0.003:
            return dict(power_kw=None, vibration_mm_s=None, motor_temp_c=None, air_pressure_bar=None)
        power = lm["kw"] * (0.20 + 0.55 * run_frac) * (1 + r.gauss(0, 0.02))
        vib = lm["vib_base"] * (0.25 + 0.75 * run_frac) + r.gauss(0, 0.07)
        ambient = 31 + 3 * math.sin((hour - 9) / 24 * 2 * math.pi)
        temp = ambient + (lm["temp_base"] - 33) * (0.45 + 0.55 * run_frac) + r.gauss(0, 0.5)
        press = 6.0 + r.gauss(0, 0.05) if lm["type"] == "Airjet" else None
        code = lm["code"]
        if code == "SZ-05" and off >= 8:
            ramp = off - 7 + hour / 24
            vib += 0.18 * ramp * run_frac
            temp += 1.3 * ramp * run_frac
        if code == "AJ-09" and off >= 10:
            ramp = off - 9 + hour / 24
            temp += 0.9 * ramp * run_frac
            vib += 0.05 * ramp * run_frac
        if code == "AJ-14" and off >= DECLINE_DAY and press is not None:
            press -= 0.9
        if code == "SZ-07" and shift_code == "III":
            power *= 1.2
        return dict(power_kw=round(power, 2), vibration_mm_s=round(max(vib, 0.05), 2), motor_temp_c=round(temp, 1), air_pressure_bar=round(press, 2) if press is not None else None)

    def _multipliers(self, lm, off: int, shift_code: str, plan: _BeamPlan) -> dict:
        mult: dict = {}
        if shift_code == "III":
            mult["WAITING_FITTER"] = 2.2
        if lm["code"] == "AJ-14" and off >= DECLINE_DAY:
            mult["WEFT_BREAK"] = 3.0
        if lm["code"] == "SZ-05":
            mult["MECHANICAL"] = 6.0
            mult["dur_MECHANICAL"] = 1.4
        if lm["code"] == "SZ-07" and shift_code == "III":
            mult["ELECTRICAL"] = 10.0
        if (plan.style, int(plan.lot.rsplit("-", 1)[1])) == BAD_LOT:
            mult["WARP_BREAK"] = 2.4
        return mult

    def _pm_stop_for_day(self, lm, d: date):
        pm = self._pm_dates(lm)
        for pd_ in pm:
            if pd_ == d and not self._pm_overdue(lm, pd_):
                st = self.cal.day_bounds(d)[0] + timedelta(hours=3 + lm["n"] % 5)
                if st < self.now:
                    return (st, st + timedelta(minutes=75), "PLANNED_MAINT", "")
        return None

    def _pm_dates(self, lm) -> List[date]:
        out, k = [], 0
        while True:
            dd = self.epoch - timedelta(days=21) + timedelta(days=(lm["n"] * 5) % 21 + 21 * k)
            if dd > self.last_day + timedelta(days=21):
                return out
            out.append(dd)
            k += 1

    def _pm_overdue(self, lm, d: date) -> bool:
        today = self.cal.production_day(self.now)
        return lm["code"] in ("AJ-14", "SZ-05") and today - timedelta(days=14) <= d < today

    def _maintenance_plan(self, lm, days: List[date]) -> None:
        loom_id = self.ids["loom"][lm["code"]]
        today = self.cal.production_day(self.now)
        task = "Nozzle + cutter service" if lm["type"] == "Airjet" else "Gripper + timing check"
        for d in self._pm_dates(lm):
            if d > self.last_day + timedelta(days=14):
                continue
            done = d <= today and not self._pm_overdue(lm, d) and d >= self.epoch - timedelta(days=21)
            started = self.cal.day_bounds(d)[0] + timedelta(hours=3 + lm["n"] % 5)
            if done and started >= self.now:
                done = False
            self.rows["maintenance"].append(dict(
                event_ref=f"PM-{lm['code']}-{d.isoformat()}", loom_id=loom_id, event_type="PREVENTIVE", task=task, planned_for=d,
                started_at=started if done else None, completed_at=(started + timedelta(minutes=75)) if done else None,
                status="COMPLETED" if done else "PLANNED", technician_id=self.ids["op"][f"T-{lm['n'] % 3 + 1:02d}"], stop_event_id=None, notes=None, data_origin=DEMO))

    # --- rolls and defects -----------------------------------------------------

    def _make_roll(self, lm, seq: int, length: float, doffed_at: datetime, sday: date, shift: ShiftDef, plan: _BeamPlan, off: int) -> None:
        rng = _rng("roll", lm["code"], seq)
        inspected_at = doffed_at + timedelta(hours=rng.uniform(1.5, 6))
        if rng.random() > 0.88 or inspected_at > self.now:
            return  # not inspected (yet): uninspected fabric is not assumed clean
        roll_no = f"R-{lm['code']}-{seq:05d}"
        rate = lm["base_defects"]
        weights = dict(DEFECT_WEIGHTS)
        if shift.code == "III" and plan.style == "S-204" and off >= DECLINE_DAY:
            rate *= 2.4
            weights["FLOAT"] *= 3.0
            weights["WARP_STREAK"] *= 3.0
        if lm["code"] == "AJ-18":
            rate *= 2.2
        n = _poisson(rng, rate * length / 100.0)
        obs, points = [], 0
        types, w = list(weights), list(weights.values())
        for _ in range(n):
            t = rng.choices(types, w)[0]
            sev = rng.choices(["MINOR", "MAJOR", "CRITICAL"], [0.70, 0.25, 0.05])[0]
            pts = 1 if sev == "MINOR" else (rng.choice([2, 3]) if sev == "MAJOR" else 4)
            points += pts
            obs.append(dict(defect_type_id=self.ids["defect"][t], severity=sev, points=pts, defect_count=1, position_m=round(rng.uniform(0, length), 2)))
        p100 = points / length * 100
        grade = "A" if p100 <= GRADE_THRESHOLDS[0] else "B" if p100 <= GRADE_THRESHOLDS[1] else "C" if p100 <= GRADE_THRESHOLDS[2] else "REJECT"
        self.rows["inspections"].append(dict(
            roll_no=roll_no, loom_id=self.ids["loom"][lm["code"]], style_id=self.ids["style"][plan.style], shift_id=shift.id, shift_date=sday,
            inspected_at=inspected_at, inspector_id=self.ids["op"][f"I-{seq % 4 + 1:02d}"], length_m=round(length, 2), grade=grade, data_origin=DEMO, _beam_no=plan.beam_no))
        self.defects_by_roll[roll_no] = obs

    # --- persistence -----------------------------------------------------------

    def _flush_rows(self) -> None:
        db, ids, R = self.db, self.ids, self.rows
        _insert(db, m.WvYarnLot.__table__, self._yarn_lots())
        _insert(db, m.WvBeam.__table__, R["beams"])
        db.flush()
        beam_id = {b.beam_no: b.id for b in db.scalars(select(m.WvBeam).where(m.WvBeam.data_origin == DEMO))}
        order_id = ids["order"]
        # mountings: one per beam on its loom
        for lm in self.looms:
            for p in self.beam_plans(lm):
                if p.end <= self.epoch_start or p.start >= self.now:
                    continue
                R["mountings"].append(dict(beam_id=beam_id[p.beam_no], loom_id=ids["loom"][lm["code"]], mounted_at=p.start,
                                           removed_at=p.end if p.end <= self.now else None, data_origin=DEMO))
        _insert(db, m.WvBeamMounting.__table__, R["mountings"])
        for r in R["assign"]:
            r["order_id"] = order_id[r.pop("order_no")]
        _insert(db, m.WvOrderAssignment.__table__, R["assign"])
        _insert(db, m.WvShiftAssignment.__table__, R["shift_assign"])
        _insert(db, m.WvAttendance.__table__, R["attendance"])
        for key in ("readings", "stops", "inspections"):
            for r in R[key]:
                r["beam_id"] = beam_id.get(r.pop("_beam_no"))
        _insert(db, m.WvLoomReading.__table__, R["readings"])
        _insert(db, m.WvStopEvent.__table__, R["stops"])
        _insert(db, m.WvInspection.__table__, R["inspections"])
        db.flush()
        # defect observations for inspections that are new this run
        rolls, have = {}, set()
        names = list(self.defects_by_roll)
        for i in range(0, len(names), CHUNK):
            rolls.update({r.roll_no: r.id for r in db.scalars(select(m.WvInspection).where(m.WvInspection.roll_no.in_(names[i:i + CHUNK])))})
        rid = list(rolls.values())
        for i in range(0, len(rid), CHUNK):
            have.update(db.scalars(select(m.WvDefectObservation.inspection_id).where(m.WvDefectObservation.inspection_id.in_(rid[i:i + CHUNK]))))
        obs_rows = [dict(inspection_id=rid, **o) for rn, rid in rolls.items() if rid not in have for o in self.defects_by_roll[rn]]
        for i in range(0, len(obs_rows), CHUNK):
            db.execute(pg_insert(m.WvDefectObservation.__table__), obs_rows[i:i + CHUNK])
        # breakdown maintenance events, linked to their stop
        stop_ids = {(r.loom_id, r.started_at): r.id for r in db.execute(select(m.WvStopEvent.loom_id, m.WvStopEvent.started_at, m.WvStopEvent.id).where(m.WvStopEvent.data_origin == DEMO, m.WvStopEvent.reason_id.in_([ids["reason"]["MECHANICAL"], ids["reason"]["ELECTRICAL"]])))}
        for code, loom_id, st, reason in self.breakdown_keys:
            sid = stop_ids.get((loom_id, st))
            if sid is None:
                continue
            en = self.stop_end[(loom_id, st)]
            done = en <= self.now
            R["maintenance"].append(dict(event_ref=f"BD-{code}-{st.strftime('%Y%m%d%H%M')}", loom_id=loom_id, event_type="BREAKDOWN",
                                         task=f"{'Mechanical' if reason == 'MECHANICAL' else 'Electrical'} breakdown", planned_for=None, started_at=st,
                                         completed_at=en if done else None, status="COMPLETED" if done else "IN_PROGRESS",
                                         technician_id=ids["op"][f"T-{loom_id % 3 + 1:02d}"], stop_event_id=sid, notes=None, data_origin=DEMO))
        _insert(db, m.WvMaintenanceEvent.__table__, R["maintenance"])
        self._actions()
        self._notes()

    def _yarn_lots(self) -> List[dict]:
        """Incoming test results per yarn lot. The lot behind the S-415 warp-break excess tests weaker, which is evidence, not proof."""
        out = []
        for lot_no, info in sorted(self.lots.items()):
            r = _rng("lot", lot_no)
            style = info["style"]
            warp = next(x[3] for x in STYLES if x[0] == style)
            bad = (style, int(lot_no.rsplit("-", 1)[1])) == BAD_LOT
            out.append(dict(lot_no=lot_no, yarn_count=warp, supplier=C.SUPPLIERS[(int(lot_no.rsplit("-", 1)[1]) + len(style)) % len(C.SUPPLIERS)],
                            received_on=(info["first"] - timedelta(days=9)).date(), strength_cn_tex=round((12.9 if bad else 15.6) + r.uniform(-0.4, 0.4), 2),
                            elongation_pct=round((4.1 if bad else 5.6) + r.uniform(-0.2, 0.2), 1), cv_pct=round((15.2 if bad else 11.5) + r.uniform(-0.7, 0.7), 1), data_origin=DEMO))
        return out

    def _notes(self) -> None:
        """Hand-over notes written by the shift supervisors for the last three production days."""
        ids, today = self.ids, self.last_day
        rows = []
        for k, (back, shift_code, loom, sev, cat, text) in enumerate(C.NOTES):
            day = today - timedelta(days=back)
            if day < self.epoch:
                continue
            shift = self.shift_by_code[shift_code]
            start, _end = self.cal.shift_bounds(day, shift)
            created = start + timedelta(hours=5)
            if created > self.now:
                continue
            rows.append(dict(note_ref=f"N-{day.isoformat()}-{shift_code}-{k}", shift_date=day, shift_id=shift.id, loom_id=ids["loom"][loom] if loom else None, category=cat, severity=sev,
                             body=text, author_name=_person(f"S-{shift_code}-01"), created_at=created, resolved_at=(created + timedelta(hours=6)) if back >= 1 and sev == "INFO" else None, data_origin=DEMO))
        _insert(self.db, m.WvShiftNote.__table__, rows)

    def _actions(self) -> None:
        today = self.cal.production_day(self.now)
        d = lambda n: today + timedelta(days=n)
        who = lambda code: _person(code)
        rows = [
            ("A-DEMO-101", "loom_decline:AJ-14", "AJ-14 weft breaks rising", "Check weft feeder and main-nozzle air pressure; replace worn nozzle", "MAINTENANCE", who("F-III-02"), d(1), "IN_PROGRESS", 0.9),
            ("A-DEMO-102", "recurring_stop:SZ-05:MECHANICAL", "SZ-05 repeated mechanical stops", "Full gripper and timing overhaul; check bearing noise", "MAINTENANCE", who("T-01"), d(0), "OPEN", 0.7),
            ("A-DEMO-103", "beam_warp_excess:S-415", "S-415 warp breaks on one yarn lot", "Hold the lot, test retained yarn samples, review size pick-up", "QUALITY", who("I-01"), d(2), "OPEN", 0.6),
            ("A-DEMO-104", "shift_defect_shift:III:S-204", "Shift III float defects on S-204", "Inspect reed and shedding on S-204 looms in Shift III", "QUALITY", who("I-02"), d(1), "OPEN", None),
            ("A-DEMO-105", None, "Beam change delays", "Pre-stage next beams before run-out", "WEAVING_MANAGER", who("S-I-01"), d(-2), "COMPLETED", 0.3),
            ("A-DEMO-106", None, "Shift III fitter coverage", "Add a floater fitter to Shift III until absenteeism recovers", "WEAVING_MANAGER", who("S-III-01"), d(3), "IN_PROGRESS", 0.5),
            ("A-DEMO-107", None, "SO-2422 (canvas) will miss its date", "Review loom allocation for the Sulzer looms with the planner", "WEAVING_MANAGER", who("S-I-01"), d(1), "OPEN", 1.2),
        ]
        _insert(self.db, m.WvAction.__table__, [dict(action_ref=r[0], finding_key=r[1], issue=r[2], action=r[3], owner_role=r[4], owner_name=r[5], due_date=r[6], status=r[7],
                                                     expected_impact_lakhs=r[8] or 0, requires_approval=True, data_origin=DEMO,
                                                     completed_at=self.now if r[7] == "COMPLETED" else None) for r in rows])

    def converge_open_stops(self) -> int:
        """Close demo stops left open by an earlier run whose deterministic end has now passed."""
        db = self.db
        open_rows = db.execute(select(m.WvStopEvent.loom_id, m.WvStopEvent.started_at).where(m.WvStopEvent.ended_at.is_(None), m.WvStopEvent.data_origin == DEMO)).all()
        closed = 0
        for loom_id, started in open_rows:
            end = self.stop_end.get((loom_id, started))
            if end is not None and end <= self.now:
                db.execute(update(m.WvStopEvent).where(m.WvStopEvent.loom_id == loom_id, m.WvStopEvent.started_at == started, m.WvStopEvent.ended_at.is_(None), m.WvStopEvent.data_origin == DEMO).values(ended_at=end))
                db.execute(update(m.WvMaintenanceEvent).where(m.WvMaintenanceEvent.event_type == "BREAKDOWN", m.WvMaintenanceEvent.started_at == started, m.WvMaintenanceEvent.loom_id == loom_id, m.WvMaintenanceEvent.completed_at.is_(None), m.WvMaintenanceEvent.data_origin == DEMO).values(completed_at=end, status="COMPLETED"))
                closed += 1
        return closed


def reset_demo(db: Session) -> dict:
    """
    Delete ONLY rows marked data_origin = 'DEMO' (and the stored epoch), in foreign-key order, inside the caller's
    transaction. If any real (non-DEMO) row still points at a demo row the database refuses and everything rolls back.
    """
    if settings.ENVIRONMENT.lower() == "production":
        raise RuntimeError("Refusing to touch data in a production environment.")
    order = [m.WvDefectObservation, m.WvInspection, m.WvMaintenanceEvent, m.WvStopEvent, m.WvLoomReading, m.WvShiftNote, m.WvSchedulePlan, m.WvAction,
             m.WvShiftAssignment, m.WvAttendance, m.WvOrderAssignment, m.WvBeamMounting, m.WvProductionOrder, m.WvBeam, m.WvYarnLot, m.WvOperator, m.WvCustomer, m.WvStyle, m.WvLoom]
    deleted = {}
    for model in order:
        if model is m.WvDefectObservation:
            ids = select(m.WvInspection.id).where(m.WvInspection.data_origin == DEMO)
            res = db.execute(m.WvDefectObservation.__table__.delete().where(m.WvDefectObservation.inspection_id.in_(ids)))
        else:
            res = db.execute(model.__table__.delete().where(model.data_origin == DEMO))
        deleted[model.__tablename__] = res.rowcount
    db.execute(SystemInfo.__table__.delete().where(SystemInfo.key == EPOCH_KEY))
    return deleted
