"""Report importers. `detect_and_parse` picks the parser from the workbook's structure, never from the file name."""
from typing import Dict, List, Tuple

from app.mill.importers import mill_workbook, toyota_export, tsudakoma_export
from app.mill.importers.base import ParseResult, Sheet

FORMATS = {
    mill_workbook.FORMAT: "Mill daily production workbook (TY / TS / SZ sheets)",
    tsudakoma_export.FORMAT: "Tsudakoma monitoring export, Report by shift (PICK or MTR)",
    toyota_export.FORMAT: "Toyota monitoring system Shift Report",
}


class UnknownFormat(ValueError):
    pass


def detect(sheets: List[Sheet]) -> str:
    names = [s.name for s in sheets]
    if toyota_export.is_toyota_export(names):
        return toyota_export.FORMAT
    if tsudakoma_export.is_tsudakoma_export(names):
        return tsudakoma_export.FORMAT
    if mill_workbook.is_mill_workbook(names):
        return mill_workbook.FORMAT
    raise UnknownFormat(
        "This workbook does not match a known layout (mill daily workbook, Tsudakoma 'Report by term' export or Toyota 'Shift Report'). "
        f"Sheets found: {', '.join(names[:10])}"
    )


def detect_and_parse(sheets: List[Sheet]) -> Tuple[str, ParseResult]:
    fmt = detect(sheets)
    parser = {mill_workbook.FORMAT: mill_workbook.parse, tsudakoma_export.FORMAT: tsudakoma_export.parse, toyota_export.FORMAT: toyota_export.parse}[fmt]
    res = parser(sheets)
    check_consistency(res)
    return fmt, res


def check_consistency(res: ParseResult) -> None:
    """Flag loom-shifts whose kilopicks do not fit their efficiency (e.g. 82.5% with 16.5 kpicks, a likely typing slip).

    For one loom at one RPM, kilopicks per efficiency point is nearly constant, so a record more than 3x off the
    loom's median in this file is implausible. Values are kept as reported; the issue makes them visible.
    """
    groups: Dict[tuple, List] = {}
    for r in res.records:
        kp, eff, rpm = r.values.get("kilopicks"), r.values.get("efficiency_pct"), r.values.get("rpm")
        if kp and eff and eff >= 10 and rpm:
            groups.setdefault((r.category, r.loom_no, r.source_kind, round(rpm, -1)), []).append((kp / eff, r))
    for items in groups.values():
        if len(items) < 5:
            continue
        ratios = sorted(x for x, _ in items)
        med = ratios[len(ratios) // 2]
        for ratio, r in items:
            if med and not (med / 3 <= ratio <= med * 3):
                res.issue("WARNING", "INCONSISTENT_VALUES",
                          f"{r.category}-{r.loom_no:02d} {r.prod_date} {r.shift}: {r.values['kilopicks']:g} kilopicks at "
                          f"{r.values['efficiency_pct']:g}% efficiency is {ratio / med:.2f}x this loom's usual kilopicks per efficiency point; check the source",
                          r.sheet, r.row, None, r.values["kilopicks"])
