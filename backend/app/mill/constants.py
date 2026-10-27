"""Fixed vocabularies shared by the importers, analytics and API."""
from datetime import time
from typing import Dict, Tuple

# Machine categories as the mill names them in its reports (sheet suffixes -TY, -TS, -SZ).
CATEGORIES: Dict[str, str] = {
    "TY": "Toyota",
    "TS": "Tsudakoma",
    "SZ": "Sulzer",
}

SHIFTS = ("A", "B", "C")

# Shift clock times. Evidence: the Tsudakoma export's Temp sheet stamps shift 1 records at 14:00 and shift 2 at
# 22:00 (end of shift), i.e. A 06:00-14:00, B 14:00-22:00, C 22:00-06:00 (C ends the next calendar day).
SHIFT_TIMES: Dict[str, Tuple[time, time]] = {
    "A": (time(6, 0), time(14, 0)),
    "B": (time(14, 0), time(22, 0)),
    "C": (time(22, 0), time(6, 0)),
}
SHIFT_MINUTES = 480  # Toyota export: run + stop minutes = 480 for a fully monitored shift

# Where a production record came from. Analytics never mix these silently (see analytics/records.py).
SOURCE_MILL_REPORT = "MILL_REPORT"        # the mill's own daily production workbook
SOURCE_MACHINE_EXPORT = "MACHINE_EXPORT"  # an OEM monitoring-system export (Toyota / Tsudakoma)
SOURCE_KINDS = (SOURCE_MILL_REPORT, SOURCE_MACHINE_EXPORT)

ORIGIN_IMPORTED = "IMPORTED"    # historical / periodic file data, never "live"
ORIGIN_LIVE = "LIVE"            # read from a machine through an approved adapter
ORIGIN_SIMULATED = "SIMULATED"  # simulator adapter; always labelled as such
ORIGINS = (ORIGIN_IMPORTED, ORIGIN_LIVE, ORIGIN_SIMULATED)

TASK_STATUSES = ("PENDING", "IN_PROGRESS", "BLOCKED", "COMPLETED", "REOPENED")
TASK_OPEN = ("PENDING", "IN_PROGRESS", "BLOCKED", "REOPENED")
PRIORITIES = ("LOW", "MEDIUM", "HIGH", "CRITICAL")

ALERT_STATUSES = ("OPEN", "ACKNOWLEDGED", "RESOLVED")
SEVERITIES = ("INFO", "WARNING", "CRITICAL")

WORK_ORDER_TYPES = ("BREAKDOWN", "PREVENTIVE", "INSPECTION", "ADJUSTMENT")
WORK_ORDER_STATUSES = ("OPEN", "IN_PROGRESS", "ON_HOLD", "COMPLETED", "CANCELLED")

PERSON_ROLES = ("OPERATOR", "GROUP_LEADER", "SUPERVISOR", "MAINTENANCE", "FITTER", "OTHER")

REPORT_STATUSES = ("DRAFT", "PUBLISHED", "ACKNOWLEDGED")

# Connection readiness, from "nothing configured" to "reading".
CONNECTION_STATES = ("NOT_CONFIGURED", "AWAITING_VENDOR_INFO", "CONFIGURED", "CONNECTED", "STALE", "OFFLINE", "ERROR")
ADAPTERS = ("NONE", "SIMULATOR", "TOYOTA_TMS", "TSUDAKOMA_TISS")


def loom_code(category: str, number: int) -> str:
    """Canonical loom id across every source: TY 'L01', Toyota export '001' and number 1 are all TY-01."""
    return f"{category}-{number:02d}"


def shift_from_number(n) -> str:
    return SHIFTS[int(n) - 1]
