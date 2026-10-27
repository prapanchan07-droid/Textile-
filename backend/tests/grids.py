"""
Small hand-built sheets with the exact layouts of the mill's files (see docs/data-sources.md), so parser tests
need neither the real files nor the network. Values are invented; positions and headers are the real ones.
"""
from __future__ import annotations

import io
from typing import List

from app.mill.importers.base import Sheet

SHIFT_HEADS_TY = ["EFF %", "KILO PICK", "MTR", "Warp\n(times)", "Weft\n(times)"]
SHIFT_HEADS = ["Effi", "Kilopick", "Meter ", "WARP", "WEFT"]


def ty_sheet(name: str = "01.09.26-TY", looms=None) -> Sheet:
    """TY: header on row 1, shift labels under it, loom rows, an 'AVG =' summary, then the width/fabric section."""
    looms = looms or [
        # loom, rpm, style, (eff, kp, m, warp, weft) x3
        ("L01", 500.0, "8448-84", [(84.0, 400.0, 120.0, 10, 5), (90.0, 430.0, 130.0, 6, 4), (86.0, 410.0, 125.0, 8, 6)]),
        ("L02", 1198.0, "4140-49", [(95.0, 550.0, 285.0, 5, 16), (92.0, 530.0, 275.0, 3, 30), (74.0, 420.0, 218.0, 5, 12)]),
        ("L03", 1196.0, "4140-49", [(87.0, 497.0, 257.0, 15, 17), (92.0, 529.0, 274.0, 4, 17), (75.0, 428.0, 222.0, 14, 4)]),
    ]
    rows: List[list] = [["L. NO", "RPM", "PICK"] + SHIFT_HEADS_TY * 4,
                        [None, None, None, "SHIFT-A", None, None, None, None, "SHIFT-B", None, None, None, None, "SHIFT-C", None, None, None, None, "DAY REPORT"]]
    for no, rpm, style, shifts in looms:
        day = (sum(s[0] for s in shifts) / 3, sum(s[1] for s in shifts), sum(s[2] for s in shifts), sum(s[3] for s in shifts), sum(s[4] for s in shifts))
        rows.append([no, rpm, style] + [v for s in shifts for v in s] + list(day))
    summ = [None, None, "AVG ="]
    for i in range(3):
        summ += [sum(l[3][i][0] for l in looms) / len(looms), sum(l[3][i][1] for l in looms), sum(l[3][i][2] for l in looms), 0.5, 1.5]
    summ += [0.0, sum(sum(s[1] for s in l[3]) for l in looms), sum(sum(s[2] for s in l[3]) for l in looms), 0.5, 1.5]
    rows.append(summ)
    rows += [[], [], [None, " ", None, None, "TOYOTA ", None, None, None, None, None, None, None, None, None, None, None, None, None, None, "DATE : 01/09/2026"],
             ["Loom Type", "Loom No", "RPM", "Ends & PICK"] + SHIFT_HEADS_TY * 4,
             ["340 CM", None, None, None, '40s Vortex X 40s Vortex 132X84-65"']]
    rows.append([None] + list(rows[2][:3]) + rows[2][3:])
    rows.append(["190 CM", None, None, None, '30s VSF  X 30s Vortex / 66X49-63"Plain '])
    for r in rows[3:5]:
        rows.append([None] + list(r))
    rows += [[], [None] * 19 + ["340 CM"], [None] * 19 + ["1 LOOMS"], [None] * 19 + ["190 CM"], [None] * 19 + ["2 LOOMS"]]
    return Sheet(name, rows)


def sz_sheet(name: str = "01.09.26-SZ") -> Sheet:
    """SZ: warp/weft left empty in the top table (unavailable), 0 in the lower section."""
    rows = [["SULZER"], [None, None, None, "Shift-A", None, None, None, None, "Shift-B", None, None, None, None, "Shift-C", None, None, None, None, "Day Report"],
            ["Loom No", "RPM", "PICK"] + SHIFT_HEADS * 4]
    data = [(1, 260, "3528-44", [(95.3, 197.6, 114.07), (94.4, 195.8, 113.03), (85.8, 178.0, 102.75)]),
            (2, 268, "11920-91", [(86.3, 164.0, 22.89), (84.2, 160.0, 22.33), (64.9, 123.4, 17.22)])]
    for no, rpm, style, s in data:
        day = (sum(x[0] for x in s) / 3, sum(x[1] for x in s), sum(x[2] for x in s))
        rows.append([no, rpm, style] + [v for x in s for v in (x[0], x[1], x[2], None, None)] + [day[0], day[1], day[2], 0, 0])
    rows.append([None, None, None, 80.0, None, 136.96])
    summ = ["TOTAL AVERAGE", None, None]
    for i in range(3):
        summ += [sum(d[3][i][0] for d in data) / 2, sum(d[3][i][1] for d in data), sum(d[3][i][2] for d in data), 0, 0]
    summ += [0, sum(sum(x[1] for x in d[3]) for d in data), sum(sum(x[2] for x in d[3]) for d in data), 0, 0]
    rows.append(summ)
    rows += [[], [None] * 17 + ["360 CM"], [None] * 17 + ["2 LOOMS"]]
    return Sheet(name, rows)


TS_HEAD = ["ZA", "Date", "Shift No.", "Loom No.", "Style No. ", "rpm", "Mill efficiency", "Loom efficiency", "Cloth length", "", "Total stop", "", "",
           "Filling stop", "", "", "Warp stop", "", "", "H1 feeler (C1)", "Dropper", "Air consumption"]


def tsudakoma_sheets(unit: str = "x100 picks") -> List[Sheet]:
    """Tsudakoma 'Report by term'. unit 'x100 picks' (PICK file, length in column I) or 'meter' (MTR file, column J)."""
    pick = unit != "meter"
    units = ["", "", "", "", "", "rpm", "%", "%", unit if pick else "", "" if pick else "meter", "minutes", "times", "s/cmpx", "minutes", "times",
             "s/cmpx", "minutes", "times", "s/cmpx", "times", "times", "Nm3"]
    head = list(TS_HEAD)
    if not pick:
        head[8], head[9] = "", "Cloth length"
    rows = [[], [], [], ["", "", "Report by shift"], ["", "Data date:2026/10/14 06:21"], head, units]
    data = [("L001", 1, 1253.0, 87.1, 88.3, 3401.0, 159.3, 35.7, 72, 25.0, 56, 6.6, 11, 41, 11),
            ("L002", 1, 1256.0, 97.4, 97.4, 5874.0, 270.7, 12.3, 17, 6.1, 9, 1.4, 2, 4, 2),
            ("L001", 2, 1250.0, 95.0, 95.0, 5700.0, 266.0, 20.0, 30, 10.0, 20, 5.0, 6, 10, 6)]
    for loom, shift, rpm, me, le, x100, m, tmin, tn, fmin, fn, wmin, wn, h1, drop in data:
        length = [x100, x100 / 10] if pick else [x100 / 10, m]
        rows.append(["", "2026/10/13", float(shift), loom, "30V30V665763", rpm, me, le] + length + [tmin, float(tn), 1.0, fmin, float(fn), 1.0, wmin, float(wn), 1.0,
                                                                                                 float(h1), float(drop), 0.0])
    rows += [[], ["", "", "", "", "", 1253.0, 93.0, 93.6, 14975.0 if pick else "", "", 22.7]]
    rows += [["ZW", "Date", "Shift No.", "Loom No.", "Style No. ", "rpm", "Mill efficiency", "Loom efficiency", "Cloth length"],
             ["", "", "", "", "", "rpm", "%", "%", "meter"], [], ["", "", "", "", "", "-", "-", "-", 0.0]]
    report = Sheet("Report by term", rows)
    total_a = (3401.0 + 5874.0) if pick else (159.3 + 270.7)
    total_b = 5700.0 if pick else 266.0
    counter = Sheet("Counter by term", [[]] * 24 + [["", "Shift No.", "Cloth length(x100 picks)" if pick else "Cloth length(meter)"], ["", 1.0, total_a], ["", 2.0, total_b]])
    causes = Sheet("Stop cause graph by term", [[]] * 20 + [["", "Stop cause", "Down time", "Stop frequency"], ["", "Filling", 41.1, 85.0], ["", "Warp", 13.0, 19.0],
                                                           ["", "Dropper", 1.0, 19.0], ["", "Others", 1.0, 2.0]])
    eff = Sheet("Efficiency graph by term", [[]] * 26 + [["", "Date & Shift No.", "Mill efficiency"], ["", "2026/10/13,1", 92.3], ["", "2026/10/13,2", 95.0]])
    return [report, counter, causes, eff, Sheet("Temp", [["L001"]])]


TOY_HEAD = ["Shiftname\n", "Loom\n", "Style\n", "RPM\n", "Effic.\n(%)", "Run\n(min)", "Stop\n(min)", "Product\n(1000pick)", "Product\n(meter)",
            "Warp\n(times)", "Warp\n(min)", "Warp\n(times/h)", "Warp\n(times/day)", "Warp\n(times/cmpx)", "Weft\n(times)", "Weft\n(min)", "Weft\n(times/h)",
            "Weft\n(times/day)", "Weft\n(times/cmpx)", "UnSelect\n(times)", "UnSelect\n(min)", "UnSelect2\n(times)", "UnSelect\n(times/h)",
            "UnSelect\n(times/day)", "UnSelect\n(times/cmpx)", "Total\n(times)", "Total\n(min)", "Total2\n(times)", "Total\n(times/h)", "Total\n(times/day)",
            "Total\n(times/cmpx)"]


def toyota_sheets() -> List[Sheet]:
    data = [("2026/10/11.A", "001", "40s40s132.84-63p", 509.3, 92.12, 442.167, 37.833, 225.2, 68.1, 2, 11.0, 18, 26.8, 0, 0.0, 20, 37.8),
            ("2026/10/11.A", "040", "30v30v6657-63P", 1196.98, 86.85, 416.883, 63.117, 499.0, 222.0, 13, 30.0, 10, 20.0, 1, 13.1, 24, 63.1)]
    rows = [["Shift Report ( 2026/10/12 10:08 )"], ["Period(Shift) : 2026/10/11.A -> 2026/10/11.A"], [], TOY_HEAD]
    for sh, loom, style, rpm, eff, run, stop, kp, m, w, wmin, f, fmin, u, umin, t, tmin in data:
        rows.append([sh, loom, style, rpm, eff, run, stop, kp, m, w, wmin, 0, 0, 0, f, fmin, 0, 0, 0, u, umin, 0, 0, 0, 0, t, tmin, t, 0, 0, 0])
    tot = ["Total", "", "", 850.0, 100 * (442.167 + 416.883) / 960, 442.167 + 416.883, 37.833 + 63.117, 724.2, 290.1, 15, 41.0, 0, 0, 0, 28, 46.8, 0, 0, 0, 1, 13.1,
           0, 0, 0, 0, 44, 100.9, 44, 0, 0, 0]
    rows.append(tot)
    hour = Sheet("Stop Rate(Hour)", rows)
    sc_head = TOY_HEAD[:8] + [""] + [TOY_HEAD[8], ""] + TOY_HEAD[9:]
    sc = [rows[0], rows[1], [], sc_head]
    for r in rows[4:6]:
        factor = 2 if r[1] == "001" else 1
        sc.append(r[:8] + [r[7] * factor] + [r[8], r[8] * factor] + r[9:])
    return [Sheet("Field Name", [["<Shift Report>"]]), Sheet("Data", rows), Sheet("Stop Count and Time", sc), hour, Sheet("Stop Rate(cmpx)", rows)]


def to_xlsx(sheets: List[Sheet]) -> bytes:
    from openpyxl import Workbook

    wb = Workbook()
    wb.remove(wb.active)
    for s in sheets:
        ws = wb.create_sheet(s.name[:31])
        for r in s.rows:
            ws.append(list(r) if r else [None])
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()
