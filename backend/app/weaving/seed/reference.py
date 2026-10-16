"""
Reference data every environment needs (shifts, stop reasons, defect types). This is configuration,
not factory records, so it is safe to load anywhere. Insert-if-missing only: existing rows, including
ones a mill has edited, are never changed.
"""
from datetime import time

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.weaving import models as m

SHIFTS = [
    ("I", "Shift I", time(6, 0), time(14, 0), False, 1),
    ("II", "Shift II", time(14, 0), time(22, 0), False, 2),
    ("III", "Shift III", time(22, 0), time(6, 0), True, 3),
]

# code, name, category, planned, counts toward stop rate, diagnostic hint
STOP_REASONS = [
    ("WARP_BREAK", "Warp break", "WARP", False, True, "Check warp yarn strength and size pick-up, drop wires, heald and reed condition, and the beam's yarn lot."),
    ("WEFT_BREAK", "Weft break", "WEFT", False, True, "Check weft yarn count variation, nozzle/gripper and feeder settings, and cone or package quality."),
    ("MECHANICAL", "Mechanical", "MECHANICAL", False, True, "Inspect wear parts (gripper, timing, brakes, bearings) and the last preventive-maintenance record."),
    ("ELECTRICAL", "Electrical / power", "ELECTRICAL", False, True, "Check the drive, sensors and feeder supply; log voltage dips against the stop times."),
    ("YARN_QUALITY", "Yarn quality", "YARN", False, True, "Hold the yarn lot and raise it with spinning QA."),
    ("WAITING_FITTER", "Waiting for fitter", "WAITING", False, True, "Review fitter coverage by shift and bank size."),
    ("BEAM_CHANGE", "Beam change", "BEAM", True, False, "Pre-stage the next beam and the knotting/gaiting crew before run-out."),
    ("STYLE_CHANGE", "Style change", "STYLE", True, False, "Batch similar styles to reduce changeovers."),
    ("PLANNED_MAINT", "Planned maintenance", "PLANNED_MAINTENANCE", True, False, "Preventive maintenance per plan."),
]

DEFECT_TYPES = [
    ("FLOAT", "Float", "WEAVING"), ("SLUB", "Slub", "YARN"), ("MISSING_PICK", "Missing pick", "WEAVING"),
    ("OIL_STAIN", "Oil stain", "PROCESS"), ("WARP_STREAK", "Warp streak", "WEAVING"), ("HOLE", "Hole", "WEAVING"),
    ("REED_MARK", "Reed mark", "WEAVING"),
]


def ensure_reference_data(db: Session) -> dict:
    """Insert any missing shifts, stop reasons and defect types. Returns how many were added."""
    added = {"shifts": 0, "stop_reasons": 0, "defect_types": 0}
    have = set(db.scalars(select(m.WvShift.code)))
    for code, name, start, end, crosses, order in SHIFTS:
        if code not in have:
            db.add(m.WvShift(code=code, name=name, start_time=start, end_time=end, crosses_midnight=crosses, sort_order=order))
            added["shifts"] += 1
    have = set(db.scalars(select(m.WvStopReason.code)))
    for code, name, cat, planned, counts, hint in STOP_REASONS:
        if code not in have:
            db.add(m.WvStopReason(code=code, name=name, category=cat, is_planned=planned, counts_toward_stop_rate=counts, diagnostic_hint=hint))
            added["stop_reasons"] += 1
    have = set(db.scalars(select(m.WvDefectType.code)))
    for code, name, cat in DEFECT_TYPES:
        if code not in have:
            db.add(m.WvDefectType(code=code, name=name, category=cat))
            added["defect_types"] += 1
    db.flush()
    return added
