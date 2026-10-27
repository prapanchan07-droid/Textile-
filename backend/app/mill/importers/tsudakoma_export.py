"""
Tsudakoma monitoring export, "Report by shift" (files like 13-10-2026-PICK.xls and 13-10-2026-MTR.xls).

PICK and MTR are the same report saved with a different cloth-length unit: `x100 picks` or `meter` (row 2 of
the header). Both carry the same loom-shift rows, so importing both fills kilopicks and meters of the same
records. The unit is read from the header, never from the file name.

Sheet 'Report by term':
  * a section per loom type: the header row's first cell is the section code (ZA = air-jet section, which holds
    the data; ZW = water-jet section, empty in these files). Units on the next row.
  * columns: Date | Shift No. | Loom No. | Style No. | rpm | Mill efficiency | Loom efficiency | Cloth length |
    Total stop (minutes, times, s/cmpx) | Filling stop (...) | Warp stop (...) | per-sensor stop counts | Air consumption (Nm3)
  * a summary row (no date) under each section.
Other sheets give totals used for reconciliation: 'Counter by term' (cloth length per shift),
'Stop cause graph by term' (down time and frequency per cause), 'Efficiency graph by term' (mill efficiency per shift).
'Temp' is the export's working sheet and is not imported.
"""
from __future__ import annotations

import re
from datetime import date, datetime
from typing import Dict, List, Optional

from app.mill.constants import SOURCE_MACHINE_EXPORT, shift_from_number
from app.mill.importers.base import (
    Check, LoomFact, ParseResult, Sheet, Record, clean_text, col_letter, find_row, norm_header, read_number, to_float,
)

FORMAT = "TSUDAKOMA_SHIFT_EXPORT"
REPORT = "Report by term"
DATE_RE = re.compile(r"^(\d{4})/(\d{1,2})/(\d{1,2})$")

# Per-cause stop counts. 'Total stop', 'Filling stop', 'Warp stop' carry three columns each (minutes, times, rate).
TRIPLES = {"totalstop": "total", "fillingstop": "weft", "warpstop": "warp"}


def is_tsudakoma_export(sheet_names: List[str]) -> bool:
    return REPORT in sheet_names and "Counter by term" in sheet_names


def _date(v) -> Optional[date]:
    if isinstance(v, datetime):
        return v.date()
    m = DATE_RE.match(str(v or "").strip())
    return date(int(m.group(1)), int(m.group(2)), int(m.group(3))) if m else None


def _loom_no(v) -> Optional[int]:
    m = re.fullmatch(r"L?0*(\d{1,3})", str(v or "").strip(), re.I)
    return int(m.group(1)) if m else None


def _columns(sheet: Sheet, hdr: int) -> Dict[str, object]:
    heads = [clean_text(v) for v in sheet.rows[hdr]]
    units = [clean_text(v) for v in sheet.rows[hdr + 1]] if hdr + 1 < len(sheet.rows) else []
    cols: Dict[str, object] = {"causes": {}}
    for c, h in enumerate(heads):
        n = norm_header(h)
        if n == "date":
            cols["date"] = c
        elif n == "shiftno.":
            cols["shift"] = c
        elif n == "loomno.":
            cols["loom"] = c
        elif n.startswith("styleno"):
            cols["style"] = c
        elif n == "rpm":
            cols["rpm"] = c
        elif n == "millefficiency":
            cols["mill_eff"] = c
        elif n == "loomefficiency":
            cols["loom_eff"] = c
        elif n == "clothlength":
            cols["cloth"] = c
        elif n == "airconsumption":
            cols["air"] = c
        elif n in TRIPLES:
            cols[TRIPLES[n]] = c  # minutes; times at +1, rate at +2
        elif h and c > 18:
            cols["causes"][h] = c
    # The cloth-length unit sits under the 'Cloth length' header, or in the column next to it (MTR layout).
    cloth = cols.get("cloth")
    if cloth is not None:
        for c in (cloth, cloth + 1):
            u = units[c].lower() if c < len(units) else ""
            if "pick" in u or "meter" in u:
                cols["cloth"], cols["cloth_unit"] = c, ("x100picks" if "pick" in u else "meter")
                break
    return cols


def parse(sheets: List[Sheet]) -> ParseResult:
    res = ParseResult(FORMAT)
    by_name = {s.name: s for s in sheets}
    sheet = by_name[REPORT]
    data_date = None
    for row in sheet.rows[:6]:
        for v in row:
            m = re.search(r"Data date:\s*(\d{4}/\d{2}/\d{2} \d{2}:\d{2})", str(v or ""))
            if m:
                data_date = m.group(1)
    unit = None
    r = 0
    sections = []
    while True:
        hdr = find_row(sheet, lambda row: any(norm_header(v) == "loomno." for v in row), r)
        if hdr is None:
            break
        cols = _columns(sheet, hdr)
        section = clean_text(sheet.cell(hdr, 0)) or "?"
        n_rows = _section(sheet, res, cols, section, hdr)
        sections.append({"section": section, "rows": n_rows, "header_row": hdr + 1, "cloth_length_unit": cols.get("cloth_unit")})
        if n_rows == 0:
            res.issue("INFO", "EMPTY_SECTION", f"Section {section} has no loom rows", sheet.name, hdr + 1)
        elif "cloth_unit" not in cols:
            res.issue("ERROR", "UNIT_UNKNOWN", f"Section {section}: cloth-length unit not found under the header; cloth length not imported",
                      sheet.name, hdr + 2)
        r = hdr + 2

    # Only sections that hold rows decide the unit (an empty section can carry a different default unit).
    units = {s["cloth_length_unit"] for s in sections if s["rows"] and s["cloth_length_unit"]}
    if len(units) > 1:
        res.issue("ERROR", "MIXED_UNITS", "Sections with data use different cloth-length units; totals not reconciled", sheet.name)
    unit = next(iter(units)) if len(units) == 1 else None
    if not sections:
        res.issue("ERROR", "LAYOUT_NOT_RECOGNISED", "No 'Loom No.' header found", sheet.name)
    _reconcile(by_name, res, unit)
    dates = sorted({x.prod_date for x in res.records})
    res.summary = {
        "data_date": data_date, "cloth_length_unit": unit, "sections": sections,
        "period": [dates[0].isoformat(), dates[-1].isoformat()] if dates else None,
        "looms": len({x.loom_no for x in res.records}),
        "note": "Same report as its PICK/MTR twin; import both to get kilopicks and meters for the same loom-shifts.",
    }
    return res


def _section(sheet: Sheet, res: ParseResult, cols: dict, section: str, hdr: int) -> int:
    n = 0
    seen = set()
    air_values = []
    for r in range(hdr + 2, len(sheet.rows)):
        loom_raw = sheet.cell(r, cols.get("loom", 3))
        if norm_header(loom_raw) == "loomno." or any(norm_header(v) == "loomno." for v in sheet.rows[r]):
            break  # next section
        day = _date(sheet.cell(r, cols.get("date", 1)))
        no = _loom_no(loom_raw)
        if day is None or no is None:
            continue  # blank spacer, summary row ('-' row) or the next section's title
        res.keep_raw(sheet, r)
        try:
            shift = shift_from_number(to_float(sheet.cell(r, cols["shift"])))
        except (ValueError, TypeError, IndexError):
            res.issue("ERROR", "INVALID_SHIFT", "Shift number is not 1, 2 or 3; row not imported", sheet.name, r + 1,
                      col_letter(cols["shift"]), sheet.cell(r, cols["shift"]))
            continue
        if (no, day, shift) in seen:
            res.issue("ERROR", "DUPLICATE_LOOM_ROW", f"Loom L{no:03d} shift {shift} appears twice; second row not imported", sheet.name, r + 1)
            continue
        seen.add((no, day, shift))
        v = {
            "style_code": clean_text(sheet.cell(r, cols["style"])) or None if "style" in cols else None,
            "rpm": read_number(res, sheet, r, cols["rpm"], "rpm") if "rpm" in cols else None,
            "efficiency_pct": read_number(res, sheet, r, cols["mill_eff"], "Mill efficiency") if "mill_eff" in cols else None,
            "loom_efficiency_pct": read_number(res, sheet, r, cols["loom_eff"], "Loom efficiency") if "loom_eff" in cols else None,
        }
        if cols.get("cloth_unit"):
            length = read_number(res, sheet, r, cols["cloth"], "Cloth length")
            if cols["cloth_unit"] == "x100picks":
                v["kilopicks"] = None if length is None else round(length / 10, 4)  # x100 picks -> x1000 picks
            else:
                v["meters"] = length
        for key, pref in (("total", "total"), ("weft", "weft"), ("warp", "warp")):
            if key in cols:
                c = cols[key]
                mins = read_number(res, sheet, r, c, f"{key} stop minutes")
                times = read_number(res, sheet, r, c + 1, f"{key} stop times", integer=True)
                if pref == "total":
                    v["stop_min"], v["total_stops"] = mins, times
                else:
                    v[f"{pref}_stop_min"], v[f"{pref}_stops"] = mins, times
        if v.get("total_stops") is not None and v.get("warp_stops") is not None and v.get("weft_stops") is not None:
            v["other_stops"] = v["total_stops"] - v["warp_stops"] - v["weft_stops"]
        causes = {}
        for name, c in cols["causes"].items():
            val = read_number(res, sheet, r, c, name)
            if val is not None:
                causes[name] = val
        extras = {"export_section": section, "stop_counts_by_sensor": causes}
        if "air" in cols:
            air = read_number(res, sheet, r, cols["air"], "Air consumption")
            air_values.append(air)
            extras["air_consumption_reported_nm3"] = air
            v["air_nm3"] = air
        for k in ("eff", "loom_eff"):
            key = "efficiency_pct" if k == "eff" else "loom_efficiency_pct"
            if v.get(key) is not None and not 0 <= v[key] <= 100:
                res.issue("WARNING", "IMPLAUSIBLE_VALUE", f"{key} {v[key]} outside 0-100%; stored as unavailable", sheet.name, r + 1)
                v[key] = None
        res.records.append(Record("TS", no, day, shift, SOURCE_MACHINE_EXPORT, v, extras, sheet.name, r + 1))
        res.loom_facts.append(LoomFact("TS", no, None, {"tsudakoma_export_section": section}))
        n += 1
    # A column of zeros for every loom is a sensor that is not fitted or not enabled, not zero air use.
    reported = [a for a in air_values if a is not None]
    if reported and all(a == 0 for a in reported):
        res.issue("WARNING", "AIR_NOT_MEASURED",
                  f"Section {section}: 'Air consumption' is 0 Nm3 for all {len(reported)} loom-shifts, which means it is not being measured. "
                  "Stored as unavailable (the reported 0 is kept in the record's extras).", sheet.name, hdr + 1, "Air consumption")
        for rec in res.records:
            if rec.extras.get("export_section") == section:
                rec.values["air_nm3"] = None
    return n


def _reconcile(by_name: Dict[str, Sheet], res: ParseResult, unit: Optional[str]) -> None:
    recs = res.records
    counter = by_name.get("Counter by term")
    if counter and unit:
        r = find_row(counter, lambda row: any(norm_header(v) == "shiftno." for v in row))
        if r is not None:
            for rr in range(r + 1, len(counter.rows)):
                n = to_float_safe(counter.cell(rr, 1))
                total = to_float_safe(counter.cell(rr, 2))
                if n is None or total is None:
                    continue
                shift = shift_from_number(n)
                if unit == "x100picks":
                    computed = sum(x.values.get("kilopicks") or 0 for x in recs if x.shift == shift) * 10
                    metric = "cloth length (x100 picks)"
                else:
                    computed = sum(x.values.get("meters") or 0 for x in recs if x.shift == shift)
                    metric = "cloth length (meters)"
                res.checks.append(Check(f"Shift {shift}", metric, total, computed, 0.5, "Sheet 'Counter by term'"))
    causes = by_name.get("Stop cause graph by term")
    if causes:
        r = find_row(causes, lambda row: any(norm_header(v) == "stopcause" for v in row))
        if r is not None:
            for rr in range(r + 1, len(causes.rows)):
                name = clean_text(causes.cell(rr, 1))
                freq = to_float_safe(causes.cell(rr, 3))
                if not name or freq is None:
                    continue
                if name == "Filling":
                    computed = sum(x.values.get("weft_stops") or 0 for x in recs)
                elif name == "Warp":
                    computed = sum(x.values.get("warp_stops") or 0 for x in recs)
                elif name == "Others":
                    continue  # not reported per loom
                else:
                    computed = sum(x.extras["stop_counts_by_sensor"].get(name, 0) for x in recs)
                res.checks.append(Check("All shifts", f"stop frequency: {name}", freq, computed, 0.5, "Sheet 'Stop cause graph by term'"))
    eff = by_name.get("Efficiency graph by term")
    if eff:
        r = find_row(eff, lambda row: any(norm_header(v) == "date&shiftno." for v in row))
        if r is not None:
            for rr in range(r + 1, len(eff.rows)):
                key = clean_text(eff.cell(rr, 1))
                m = re.match(r"^(\d{4}/\d{2}/\d{2}),(\d)$", key)
                reported = to_float_safe(eff.cell(rr, 2))
                if not m or reported is None:
                    continue
                shift = shift_from_number(int(m.group(2)))
                vals = [x.values["efficiency_pct"] for x in recs if x.shift == shift and x.values.get("efficiency_pct") is not None]
                res.checks.append(Check(
                    f"Shift {shift}", "mill efficiency (simple mean of looms)", reported, sum(vals) / len(vals) if vals else None, 0.15,
                    "The export weights by monitored time, which the per-loom rows do not carry; small differences are expected",
                ))


def to_float_safe(v) -> Optional[float]:
    try:
        return to_float(v)
    except ValueError:
        return None
