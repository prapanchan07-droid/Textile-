"""
The mill's daily production workbook ("TY,TS,SZ-Production Report"): one sheet per day and machine category,
named `dd.mm.yy-TY`, `-TS` or `-SZ`.

Layout (identical in all 90 September sheets; checked by `docs/data-sources.md`):

  * Top table: a header row starting `L. NO` (TY) or `Loom No` (TS, SZ), then one row per loom with
    RPM, PICK (style code) and four five-column blocks: Shift A, Shift B, Shift C and Day Report, each
    `Eff | Kilopick | Meter | Warp | Weft`. The table ends at the first row that is not a loom; the next rows
    are a summary (`AVG =`, `TOTAL AVERAGE` or an unlabeled average row). That table is the data we import.
  * Lower section: the same looms regrouped by reed width (`340 CM`, `190 CM`, `360 CM`) and fabric, with
    the fabric description above each group. Used for loom width, style descriptions and cross-checks only.
  * SZ (Sulzer) sheets leave Warp/Weft empty in the top table: imported as unavailable, not zero.
"""
from __future__ import annotations

import re
from datetime import date, datetime
from statistics import mean
from typing import Dict, List, Optional, Tuple

from app.mill.constants import SOURCE_MILL_REPORT
from app.mill.importers.base import (
    Check, LoomFact, ParseResult, Record, Sheet, clean_text, col_letter, find_row, norm_header, read_number, to_float,
)

FORMAT = "MILL_DAILY_WORKBOOK"
SHEET_NAME = re.compile(r"^\s*(\d{1,2})\.(\d{1,2})\.(\d{2,4})\s*-\s*(TY|TS|SZ)\s*$", re.I)
WIDTH = re.compile(r"^\s*(\d{3})\s*CM\s*$", re.I)
LOOMS_COUNT = re.compile(r"^\s*(\d+)\s*LOOMS\s*$", re.I)

# Header spellings per field, as they occur across the three layouts.
FIELD_HEADERS = {
    "eff": {"eff%", "effi", "eff"},
    "kp": {"kilopick", "kilopicks"},
    "m": {"mtr", "meter", "meters", "mtrs"},
    "warp": {"warp(times)", "warp"},
    "weft": {"weft(times)", "weft"},
}
BLOCK_NAMES = ("A", "B", "C", "DAY")


def is_mill_workbook(sheet_names: List[str]) -> bool:
    matched = [n for n in sheet_names if SHEET_NAME.match(n)]
    return len(matched) > 0 and len(matched) >= len(sheet_names) * 0.8


def sheet_date_and_category(name: str) -> Optional[Tuple[date, str]]:
    m = SHEET_NAME.match(name)
    if not m:
        return None
    d, mo, y, cat = m.groups()
    year = int(y) + 2000 if len(y) == 2 else int(y)
    return date(year, int(mo), int(d)), cat.upper()


def _field_of(header: str) -> Optional[str]:
    for f, names in FIELD_HEADERS.items():
        if header in names:
            return f
    return None


def _header_row(sheet: Sheet, start: int = 0) -> Optional[int]:
    return find_row(sheet, lambda r: norm_header(r[0] if r else "") in ("l.no", "loomno"), start)


def _blocks(sheet: Sheet, hdr: int, first_col: int) -> Optional[Dict[str, Dict[str, int]]]:
    """Find the four Eff/Kilopick/Meter/Warp/Weft blocks from the header names (not from fixed positions)."""
    heads = [norm_header(v) for v in sheet.rows[hdr]]
    starts = [c for c in range(first_col, len(heads)) if _field_of(heads[c]) == "eff"]
    if len(starts) < 4:
        return None
    blocks = {}
    for name, s in zip(BLOCK_NAMES, starts[:4]):
        cols = {}
        for c in range(s, min(s + 5, len(heads))):
            f = _field_of(heads[c])
            if f and f not in cols:
                cols[f] = c
        if set(cols) != set(FIELD_HEADERS):
            return None
        blocks[name] = cols
    return blocks


def _loom_no(v, category: str) -> Optional[int]:
    if v is None:
        return None
    if isinstance(v, (int, float)) and not isinstance(v, bool):
        return int(v) if float(v).is_integer() and v > 0 else None
    m = re.fullmatch(r"L?\s*0*(\d{1,3})", str(v).strip(), re.I)
    return int(m.group(1)) if m else None


def _sheet_print_date(sheet: Sheet) -> Optional[date]:
    """The 'DATE : 01/09/2026' cell some sheets carry; the value may sit in the same cell or the next ones."""
    for r, row in enumerate(sheet.rows):
        for c, v in enumerate(row):
            if isinstance(v, str) and v.strip().upper().startswith("DATE"):
                for cand in [v.split(":", 1)[-1]] + [sheet.cell(r, c + k) for k in (1, 2)]:
                    if isinstance(cand, datetime):
                        return cand.date()
                    if isinstance(cand, date):
                        return cand
                    m = re.search(r"(\d{1,2})/(\d{1,2})/(\d{4})", str(cand or ""))
                    if m:
                        return date(int(m.group(3)), int(m.group(2)), int(m.group(1)))
    return None


def parse_sheet(sheet: Sheet, res: ParseResult) -> None:
    meta = sheet_date_and_category(sheet.name)
    if not meta:
        res.issue("WARNING", "SHEET_SKIPPED", "Sheet name is not dd.mm.yy-TY/TS/SZ; not imported", sheet.name)
        return
    day, cat = meta
    hdr = _header_row(sheet)
    blocks = _blocks(sheet, hdr, 3) if hdr is not None else None
    if hdr is None or blocks is None:
        res.issue("ERROR", "LAYOUT_NOT_RECOGNISED", "No 'Loom No' header with Shift A/B/C/Day blocks found; sheet not imported", sheet.name)
        return

    printed = _sheet_print_date(sheet)
    if printed and printed != day:
        res.issue("WARNING", "DATE_MISMATCH", f"Sheet name says {day}, the sheet's DATE cell says {printed}; using the sheet name",
                  sheet.name, raw=printed.isoformat())

    # ---- top table
    seen: Dict[int, int] = {}
    day_rows: Dict[int, dict] = {}
    r = hdr + 1
    end = None
    while r < len(sheet.rows):
        first = sheet.cell(r, 0)
        no = _loom_no(first, cat)
        if no is None:
            if seen and clean_text(first) == "" and all(v in (None, "") for v in sheet.rows[r][:3]):
                end = r  # blank or summary row right after the data
                break
            if seen:
                end = r
                break
            r += 1  # e.g. the "Shift-A / Shift-B" label row under the TY header
            continue
        res.keep_raw(sheet, r)
        if no in seen:
            res.issue("ERROR", "DUPLICATE_LOOM_ROW", f"Loom {no} appears twice in the table (rows {seen[no] + 1} and {r + 1}); second row not imported",
                      sheet.name, r + 1, "A", first)
            r += 1
            continue
        seen[no] = r
        rpm = read_number(res, sheet, r, 1, "RPM")
        style = clean_text(sheet.cell(r, 2)) or None
        if style:
            res.styles.setdefault(style, None)
        for shift in ("A", "B", "C"):
            b = blocks[shift]
            vals = {
                "rpm": rpm,
                "style_code": style,
                "efficiency_pct": read_number(res, sheet, r, b["eff"], f"Shift {shift} efficiency"),
                "kilopicks": read_number(res, sheet, r, b["kp"], f"Shift {shift} kilopicks"),
                "meters": read_number(res, sheet, r, b["m"], f"Shift {shift} meters"),
                "warp_stops": read_number(res, sheet, r, b["warp"], f"Shift {shift} warp stops", integer=True),
                "weft_stops": read_number(res, sheet, r, b["weft"], f"Shift {shift} weft stops", integer=True),
            }
            eff = vals["efficiency_pct"]
            if eff is not None and not (0 <= eff <= 100):
                res.issue("WARNING", "IMPLAUSIBLE_VALUE", f"Shift {shift} efficiency {eff} is outside 0-100%; stored as unavailable",
                          sheet.name, r + 1, col_letter(b["eff"]), eff)
                vals["efficiency_pct"] = None
            if all(vals[k] is None for k in ("efficiency_pct", "kilopicks", "meters")):
                res.issue("INFO", "NO_SHIFT_DATA", f"Loom {no} shift {shift}: no production values; no record created", sheet.name, r + 1)
                continue
            res.records.append(Record(cat, no, day, shift, SOURCE_MILL_REPORT, vals, {}, sheet.name, r + 1))
        d = blocks["DAY"]
        day_rows[no] = {f: to_float_safe(sheet.cell(r, c)) for f, c in d.items()}
        r += 1
    if not seen:
        res.issue("ERROR", "NO_LOOM_ROWS", "Header found but no loom rows under it", sheet.name, hdr + 1)
        return

    _reconcile(sheet, res, cat, day, blocks, seen, day_rows, end)
    _lower_section(sheet, res, cat, day, seen, end if end is not None else len(sheet.rows))


def to_float_safe(v) -> Optional[float]:
    try:
        return to_float(v)
    except ValueError:
        return None


def _reconcile(sheet, res, cat, day, blocks, seen, day_rows, end) -> None:
    """Per-loom Day Report columns and the sheet's summary row, against what was imported."""
    mine = [rec for rec in res.records if rec.sheet == sheet.name]
    tag = sheet.name.strip()

    # Day Report columns are the sheet's own per-loom totals: kilopicks/meters/stops = sum of shifts, Eff = mean of shifts.
    bad = 0
    for no, d in day_rows.items():
        shifts = [rec.values for rec in mine if rec.loom_no == no]
        for f, key, how in (("kp", "kilopicks", "sum"), ("m", "meters", "sum"), ("warp", "warp_stops", "sum"),
                            ("weft", "weft_stops", "sum"), ("eff", "efficiency_pct", "mean")):
            vals = [s[key] for s in shifts if s[key] is not None]
            if d.get(f) is None or not vals:
                continue
            computed = sum(vals) if how == "sum" else mean(vals)
            tol = 0.15 if f in ("kp", "m", "eff") else 0.01
            if abs(computed - d[f]) > tol:
                bad += 1
                res.issue("WARNING", "DAY_TOTAL_MISMATCH", f"Loom {no}: Day Report {key} {d[f]:g} but shifts give {computed:g}",
                          sheet.name, seen[no] + 1, col_letter(blocks["DAY"][f]), d[f])
    res.checks.append(Check(f"{tag} per-loom Day Report", "loom-day rows disagreeing with their shifts", 0, bad, 0,
                            f"{len(day_rows)} looms x 5 fields checked"))

    # Summary row right under the table: shift efficiency (simple mean of looms), kilopick and meter totals.
    if end is None:
        return
    a_kp, day_kp = blocks["A"]["kp"], blocks["DAY"]["kp"]
    srow = find_row(sheet, lambda row: all(c < len(row) and isinstance(row[c], (int, float)) for c in (a_kp, day_kp)), end, end + 3)
    if srow is None:
        res.issue("INFO", "NO_SUMMARY_ROW", "No summary row under the loom table; sheet totals not reconciled", sheet.name)
        return
    for blk in ("A", "B", "C", "DAY"):
        cols = blocks[blk]
        if blk == "DAY":
            recs_kp = [v for rec in mine for v in [rec.values["kilopicks"]] if v is not None]
            recs_m = [v for rec in mine for v in [rec.values["meters"]] if v is not None]
        else:
            recs_kp = [rec.values["kilopicks"] for rec in mine if rec.shift == blk and rec.values["kilopicks"] is not None]
            recs_m = [rec.values["meters"] for rec in mine if rec.shift == blk and rec.values["meters"] is not None]
        label = f"{tag} {'Day' if blk == 'DAY' else 'Shift ' + blk}"
        res.checks.append(Check(label, "kilopicks (sum)", to_float_safe(sheet.cell(srow, cols["kp"])), sum(recs_kp) if recs_kp else None, 0.5))
        res.checks.append(Check(label, "meters (sum)", to_float_safe(sheet.cell(srow, cols["m"])), sum(recs_m) if recs_m else None, 0.5))
        if blk != "DAY":
            pairs = [(rec.loom_no, rec.values["efficiency_pct"]) for rec in mine if rec.shift == blk and rec.values["efficiency_pct"] is not None]
            reported = to_float_safe(sheet.cell(srow, cols["eff"]))
            check = Check(label, "efficiency (simple mean of looms, as the sheet computes it)", reported,
                          mean(v for _, v in pairs) if pairs else None, 0.05,
                          "Equal to the time-weighted efficiency when every loom ran a full 480-minute shift")
            if check.status == "MISMATCH" and len(pairs) > 2:
                # A spreadsheet range that misses one row is the usual cause: name the loom if exactly one explains it.
                total = sum(v for _, v in pairs)
                left_out = [no for no, v in pairs if abs((total - v) / (len(pairs) - 1) - reported) <= 0.005]
                if len(left_out) == 1:
                    check.note = f"The sheet's average leaves out loom {left_out[0]} ({len(pairs) - 1} of {len(pairs)} looms)"
            res.checks.append(check)


def _lower_section(sheet: Sheet, res: ParseResult, cat: str, day: date, seen: Dict[int, int], start: int) -> None:
    """Width groups, fabric descriptions and a cross-check of the regrouped rows against the top table."""
    hdr = _header_row(sheet, start)
    if hdr is None:  # TY: the lower header starts with 'Loom Type'
        hdr = find_row(sheet, lambda r: norm_header(r[0] if r else "") == "loomtype", start)
    if hdr is None:
        return
    loom_col = 1 if norm_header(sheet.cell(hdr, 0)) == "loomtype" else 0
    first_block = _blocks(sheet, hdr, loom_col + 2)
    eff_col = first_block["A"]["eff"] if first_block else loom_col + 3
    widths: Dict[int, int] = {}
    width = None
    descr = None
    footer_width = None
    for r in range(hdr + 1, len(sheet.rows)):
        c0 = clean_text(sheet.cell(r, 0))
        if WIDTH.match(c0):  # a width marker applies from its row until the next marker
            width = int(WIDTH.match(c0).group(1))
        text = sheet.cell(r, eff_col)
        no = _loom_no(sheet.cell(r, loom_col), cat)
        if no is None and isinstance(text, str) and len(text.strip()) > 12 and re.search(r"\d", text):
            descr = clean_text(text)
            continue
        if no is not None and no in seen:
            if width:
                widths[no] = width
            style = clean_text(sheet.cell(r, loom_col + 2))
            if style and descr:
                prev = res.styles.get(style)
                if prev is None:
                    res.styles[style] = descr
            top_rpm = to_float_safe(sheet.cell(seen[no], 1))
            low_rpm = to_float_safe(sheet.cell(r, loom_col + 1))
            if top_rpm is not None and low_rpm is not None and abs(top_rpm - low_rpm) > 0.5:
                res.issue("WARNING", "SECTION_MISMATCH",
                          f"Loom {no}: RPM {top_rpm:g} in the main table but {low_rpm:g} in the width/fabric section; main table used",
                          sheet.name, r + 1, col_letter(loom_col + 1), low_rpm)
    # Footer like  '190 CM' | ... ; '24 LOOMS'  (TS, SZ have a single width group)
    for r, row in enumerate(sheet.rows):
        for c, v in enumerate(row):
            if isinstance(v, str) and WIDTH.match(v) and isinstance(sheet.cell(r + 1, c), str) and LOOMS_COUNT.match(sheet.cell(r + 1, c)):
                footer_width = footer_width or {}
                footer_width[int(WIDTH.match(v).group(1))] = int(LOOMS_COUNT.match(sheet.cell(r + 1, c)).group(1))
    if footer_width and len(footer_width) == 1 and not widths:
        (w, n), = footer_width.items()
        if n == len(seen):
            widths = {no: w for no in seen}
    for no in seen:
        res.loom_facts.append(LoomFact(cat, no, widths.get(no)))
    if footer_width:
        counts = {}
        for w in widths.values():
            counts[w] = counts.get(w, 0) + 1
        for w, n in footer_width.items():
            res.checks.append(Check(f"{sheet.name.strip()} width groups", f"looms at {w} cm", n, counts.get(w, 0), 0))


def parse(sheets: List[Sheet]) -> ParseResult:
    res = ParseResult(FORMAT)
    for sh in sheets:
        parse_sheet(sh, res)
    dates = sorted({r.prod_date for r in res.records})
    res.summary = {
        "sheets": len(sheets),
        "categories": sorted({r.category for r in res.records}),
        "looms": {cat: len({r.loom_no for r in res.records if r.category == cat}) for cat in sorted({r.category for r in res.records})},
        "period": [dates[0].isoformat(), dates[-1].isoformat()] if dates else None,
        "unavailable_fields": _unavailable(res.records),
    }
    return res


def _unavailable(records: List[Record]) -> Dict[str, Dict[str, int]]:
    """How many records per category have each field missing: the honest picture of what each layout carries."""
    out: Dict[str, Dict[str, int]] = {}
    for rec in records:
        for k, v in rec.values.items():
            if v is None:
                out.setdefault(rec.category, {}).setdefault(k, 0)
                out[rec.category][k] += 1
    return out
