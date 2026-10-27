"""
Shared pieces of the importers.

Every parser reads a workbook through `Sheet` (a name and a grid of cell values) so the same code handles .xls,
.xlsx and hand-built grids in tests. Parsers return a `ParseResult`: normalized records, issues, reconciliation
checks and the raw rows they used. Nothing is written to the database here.
"""
from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any, Dict, List, Optional, Sequence

PARSER_VERSION = "1.0.0"


@dataclass
class Sheet:
    name: str
    rows: List[List[Any]]

    def cell(self, r: int, c: int) -> Any:
        """0-based access that returns None outside the grid."""
        if r < 0 or r >= len(self.rows):
            return None
        row = self.rows[r]
        return row[c] if 0 <= c < len(row) else None


@dataclass
class Issue:
    severity: str  # ERROR / WARNING / INFO
    code: str
    message: str
    sheet: Optional[str] = None
    row: Optional[int] = None  # 1-based (as Excel shows it)
    column: Optional[str] = None
    raw_value: Optional[str] = None


@dataclass
class Record:
    """One loom-shift from one source, before it is matched to a loom row in the database."""
    category: str
    loom_no: int
    prod_date: date
    shift: str
    source_kind: str
    values: Dict[str, Any]
    extras: Dict[str, Any] = field(default_factory=dict)
    sheet: Optional[str] = None
    row: Optional[int] = None  # 1-based

    @property
    def key(self):
        return (self.category, self.loom_no, self.prod_date, self.shift, self.source_kind)


@dataclass
class Check:
    """A source total compared with the same total recomputed from the normalized records."""
    scope: str          # e.g. "01.09.26-TY Shift A"
    metric: str
    source_value: Optional[float]
    computed_value: Optional[float]
    tolerance: float
    note: str = ""

    @property
    def status(self) -> str:
        if self.source_value is None or self.computed_value is None:
            return "NOT_COMPARABLE"
        return "MATCH" if abs(self.source_value - self.computed_value) <= self.tolerance else "MISMATCH"

    def as_dict(self) -> dict:
        return {
            "scope": self.scope, "metric": self.metric, "source_value": self.source_value,
            "computed_value": None if self.computed_value is None else round(self.computed_value, 4),
            "tolerance": self.tolerance, "status": self.status, "note": self.note,
        }


@dataclass
class LoomFact:
    """Something a source says about a loom (width group, export section, operator...)."""
    category: str
    loom_no: int
    width_cm: Optional[int] = None
    attributes: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ParseResult:
    source_format: str
    records: List[Record] = field(default_factory=list)
    issues: List[Issue] = field(default_factory=list)
    checks: List[Check] = field(default_factory=list)
    loom_facts: List[LoomFact] = field(default_factory=list)
    styles: Dict[str, Optional[str]] = field(default_factory=dict)  # code -> description
    raw_rows: Dict[tuple, List[Any]] = field(default_factory=dict)  # (sheet, 1-based row) -> cells
    summary: Dict[str, Any] = field(default_factory=dict)

    def issue(self, severity: str, code: str, message: str, sheet=None, row=None, column=None, raw=None) -> None:
        self.issues.append(Issue(severity, code, message, sheet, row, column, None if raw is None else str(raw)))

    def keep_raw(self, sheet: Sheet, r: int) -> None:
        self.raw_rows[(sheet.name, r + 1)] = [jsonable(v) for v in sheet.rows[r]]


# --------------------------------------------------------------------------- cell helpers

ERROR_STRINGS = {"#REF!", "#DIV/0!", "#VALUE!", "#N/A", "#NAME?", "#NUM!", "#NULL!"}
UNAVAILABLE = {"", "-", "--", "—", "NA", "N/A", "NIL"}


class CellError(ValueError):
    pass


def jsonable(v: Any) -> Any:
    if isinstance(v, (datetime, date)):
        return v.isoformat()
    if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
        return None
    return v


def clean_text(v: Any) -> str:
    return re.sub(r"\s+", " ", str(v)).strip() if v is not None else ""


def norm_header(v: Any) -> str:
    """'Warp\\n(times)' -> 'warp(times)', 'EFF %' -> 'eff%'"""
    return re.sub(r"\s+", "", str(v or "")).lower()


def to_float(v: Any) -> Optional[float]:
    """Number, or None when the source shows the value as unavailable. Raises CellError for spreadsheet errors."""
    if v is None or isinstance(v, bool):
        return None
    if isinstance(v, (int, float)):
        if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
            return None
        return float(v)
    s = str(v).strip()
    if s.upper() in ERROR_STRINGS:
        raise CellError(f"spreadsheet error {s}")
    if s.upper() in UNAVAILABLE:
        return None
    try:
        return float(s.replace(",", ""))
    except ValueError:
        raise CellError(f"not a number: {s!r}")


def to_int(v: Any) -> Optional[int]:
    f = to_float(v)
    if f is None:
        return None
    if abs(f - round(f)) > 1e-6:
        raise CellError(f"expected a whole number, got {f}")
    return int(round(f))


def col_letter(c: int) -> str:
    s = ""
    c += 1
    while c:
        c, rem = divmod(c - 1, 26)
        s = chr(65 + rem) + s
    return s


def read_number(res: ParseResult, sheet: Sheet, r: int, c: int, label: str, integer: bool = False) -> Optional[float]:
    """Read one numeric cell, recording an issue instead of failing the import when the value is unusable."""
    raw = sheet.cell(r, c)
    try:
        return to_int(raw) if integer else to_float(raw)
    except CellError as e:
        res.issue("WARNING", "INVALID_VALUE", f"{label}: {e}; stored as unavailable", sheet.name, r + 1, f"{col_letter(c)} ({label})", raw)
        return None


def find_row(sheet: Sheet, predicate, start: int = 0, stop: Optional[int] = None) -> Optional[int]:
    for r in range(start, min(stop or len(sheet.rows), len(sheet.rows))):
        if predicate(sheet.rows[r]):
            return r
    return None


def row_text(row: Sequence[Any]) -> List[str]:
    return [norm_header(v) for v in row]
