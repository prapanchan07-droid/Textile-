"""
Toyota monitoring-system "Shift Report" export (e.g. 11-10-2026-ty.xls; workbook author "TOYOTA Monitoring System").

Sheets: 'Field Name' (field dictionary), 'Data' (raw rows, several computed cells left empty), 'Stop Count and Time',
'Stop Rate(Hour)', 'Stop Rate(Day)', 'Stop Rate(cmpx)'. We read 'Stop Rate(Hour)' (falling back to 'Stop Rate(cmpx)'):
fully computed, one header row, one row per loom-shift and a 'Total' row used for reconciliation.

Columns: Shiftname (2026/10/11.A) | Loom (001) | Style | RPM | Effic.(%) | Run(min) | Stop(min) | Product(1000pick) |
Product(meter) | Warp (times, min, rates) | Weft (...) | UnSelect (...) | Total (...).

'Stop Count and Time' has two extra, unlabeled production columns. For some looms they are exactly 2x the counted
picks and meters; the mill's own daily report uses those doubled figures for the 340 cm looms. We record the factor
per loom (`panel_factor`) and keep the counted values, so the difference is visible instead of silently "fixed".
"""
from __future__ import annotations

import re
from datetime import date
from typing import Dict, List, Optional

from app.mill.constants import SOURCE_MACHINE_EXPORT
from app.mill.importers.base import Check, LoomFact, ParseResult, Record, Sheet, clean_text, find_row, norm_header, read_number, to_float

FORMAT = "TOYOTA_SHIFT_REPORT"
SHIFT_RE = re.compile(r"^(\d{4})/(\d{1,2})/(\d{1,2})\.([ABC])$")

FIELDS = {
    "rpm": "rpm", "effic.(%)": "efficiency_pct", "run(min)": "run_min", "stop(min)": "stop_min",
    "product(1000pick)": "kilopicks", "product(meter)": "meters",
    "warp(times)": "warp_stops", "warp(min)": "warp_stop_min", "weft(times)": "weft_stops", "weft(min)": "weft_stop_min",
    "unselect(times)": "unselect_stops", "unselect(min)": "unselect_stop_min", "total(times)": "total_stops", "total(min)": "total_stop_min",
}
INTEGER = {"warp_stops", "weft_stops", "unselect_stops", "total_stops"}


def is_toyota_export(sheet_names: List[str]) -> bool:
    return "Field Name" in sheet_names and ("Stop Rate(Hour)" in sheet_names or "Stop Rate(cmpx)" in sheet_names)


def parse(sheets: List[Sheet]) -> ParseResult:
    res = ParseResult(FORMAT)
    by_name = {s.name: s for s in sheets}
    sheet = by_name.get("Stop Rate(Hour)") or by_name["Stop Rate(cmpx)"]
    title = clean_text(sheet.cell(0, 0))
    period = clean_text(sheet.cell(1, 0))
    hdr = find_row(sheet, lambda row: norm_header(row[0] if row else "") == "shiftname")
    if hdr is None:
        res.issue("ERROR", "LAYOUT_NOT_RECOGNISED", "No 'Shiftname' header found", sheet.name)
        return res
    heads = [norm_header(v) for v in sheet.rows[hdr]]
    cols = {FIELDS[h]: c for c, h in enumerate(heads) if h in FIELDS}
    col_loom, col_style = heads.index("loom"), heads.index("style")
    missing = sorted(set(FIELDS.values()) - set(cols))
    if missing:
        res.issue("WARNING", "COLUMNS_MISSING", f"Columns not in this export: {', '.join(missing)}", sheet.name, hdr + 1)

    total_row = None
    seen = set()
    for r in range(hdr + 1, len(sheet.rows)):
        key = clean_text(sheet.cell(r, 0))
        if key.lower() == "total":
            total_row = r
            continue
        m = SHIFT_RE.match(key)
        if not m:
            continue
        day, shift = date(int(m.group(1)), int(m.group(2)), int(m.group(3))), m.group(4)
        try:
            no = int(str(sheet.cell(r, col_loom)).strip())
        except ValueError:
            res.issue("ERROR", "INVALID_LOOM", "Loom number is not numeric; row not imported", sheet.name, r + 1, "B", sheet.cell(r, col_loom))
            continue
        if (no, day, shift) in seen:
            res.issue("ERROR", "DUPLICATE_LOOM_ROW", f"Loom {no:03d} shift {shift} appears twice; second row not imported", sheet.name, r + 1)
            continue
        seen.add((no, day, shift))
        res.keep_raw(sheet, r)
        vals: Dict[str, Optional[float]] = {k: read_number(res, sheet, r, c, k, integer=k in INTEGER) for k, c in cols.items()}
        style = clean_text(sheet.cell(r, col_style)) or None
        values = {
            "style_code": style,
            "rpm": vals.get("rpm"),
            "efficiency_pct": vals.get("efficiency_pct"),
            "kilopicks": vals.get("kilopicks"),
            "meters": vals.get("meters"),
            "run_min": vals.get("run_min"),
            "stop_min": vals.get("stop_min"),
            "warp_stops": vals.get("warp_stops"),
            "weft_stops": vals.get("weft_stops"),
            "warp_stop_min": vals.get("warp_stop_min"),
            "weft_stop_min": vals.get("weft_stop_min"),
            "other_stops": vals.get("unselect_stops"),
            "total_stops": vals.get("total_stops"),
        }
        if values["efficiency_pct"] is not None and not 0 <= values["efficiency_pct"] <= 100:
            res.issue("WARNING", "IMPLAUSIBLE_VALUE", f"Efficiency {values['efficiency_pct']} outside 0-100%; stored as unavailable", sheet.name, r + 1)
            values["efficiency_pct"] = None
        extras = {"unselect_stop_min": vals.get("unselect_stop_min"), "toyota_style_text": style,
                  "other_stops_meaning": "Toyota 'UnSelect' stops (stops not classified as warp or weft)"}
        res.records.append(Record("TY", no, day, shift, SOURCE_MACHINE_EXPORT, values, extras, sheet.name, r + 1))
        if style:
            res.styles.setdefault(style, None)

    _panel_factors(by_name.get("Stop Count and Time"), res)
    if total_row is not None:
        for key, label, how in (("kilopicks", "kilopicks", "sum"), ("meters", "meters", "sum"), ("warp_stops", "warp stops", "sum"),
                                ("weft_stops", "weft stops", "sum"), ("total_stops", "total stops", "sum"), ("run_min", "run minutes", "sum")):
            c = cols.get(key)
            if c is None:
                continue
            reported = _f(sheet.cell(total_row, c))
            computed = sum(x.values[key] or 0 for x in res.records)
            res.checks.append(Check("Report total", label, reported, computed, 0.5, "'Total' row of the export"))
        c = cols.get("efficiency_pct")
        if c is not None:
            runs = [x.values for x in res.records if x.values["run_min"] is not None and x.values["stop_min"] is not None]
            weighted = 100 * sum(v["run_min"] for v in runs) / sum(v["run_min"] + v["stop_min"] for v in runs) if runs else None
            res.checks.append(Check("Report total", "efficiency (run time / monitored time)", _f(sheet.cell(total_row, c)), weighted, 0.05,
                                    "Time-weighted: sum(run) / sum(run + stop)"))
    dates = sorted({x.prod_date for x in res.records})
    res.summary = {"title": title, "period_text": period, "looms": len({x.loom_no for x in res.records}),
                   "period": [dates[0].isoformat(), dates[-1].isoformat()] if dates else None,
                   "sheet_used": sheet.name}
    return res


def _panel_factors(sheet: Optional[Sheet], res: ParseResult) -> None:
    """In 'Stop Count and Time', the column after Product(1000pick) is either equal to it or exactly double."""
    if sheet is None:
        return
    hdr = find_row(sheet, lambda row: norm_header(row[0] if row else "") == "shiftname")
    if hdr is None:
        return
    heads = [norm_header(v) for v in sheet.rows[hdr]]
    try:
        kp = heads.index("product(1000pick)")
    except ValueError:
        return
    factors: Dict[int, set] = {}
    for r in range(hdr + 1, len(sheet.rows)):
        if not SHIFT_RE.match(clean_text(sheet.cell(r, 0))):
            continue
        a, b = _f(sheet.cell(r, kp)), _f(sheet.cell(r, kp + 1))
        try:
            no = int(str(sheet.cell(r, 1)).strip())
        except ValueError:
            continue
        if a and b:
            factors.setdefault(no, set()).add(round(b / a, 3))
    for no, fs in sorted(factors.items()):
        if len(fs) == 1:
            res.loom_facts.append(LoomFact("TY", no, None, {"toyota_panel_factor": next(iter(fs))}))
    doubled = sorted(no for no, fs in factors.items() if fs == {2.0})
    if doubled:
        res.issue("INFO", "PANEL_FACTOR",
                  f"'Stop Count and Time' shows production x2 for looms {', '.join(f'{n:03d}' for n in doubled)}. Counted picks/meters are imported; "
                  "the mill's daily report uses the doubled figures for these looms. Confirm the reason (e.g. two fabric panels) with the mill.",
                  sheet.name)


def _f(v) -> Optional[float]:
    try:
        return to_float(v)
    except ValueError:
        return None
