"""Parsers and metric formulas (no database)."""
from datetime import date

import pytest

from app.mill.analytics import metrics as M
from app.mill.importers import UnknownFormat, detect, detect_and_parse, mill_workbook, toyota_export, tsudakoma_export
from app.mill.importers.base import Sheet
from tests import grids


# ------------------------------------------------------------------ mill daily workbook


def test_ty_layout_maps_shift_blocks_and_skips_summary_rows():
    res = mill_workbook.parse([grids.ty_sheet()])
    assert len(res.records) == 9  # 3 looms x 3 shifts; the AVG row and the regrouped section are not machines
    r = {(x.loom_no, x.shift): x for x in res.records}
    assert r[(1, "B")].values == {"rpm": 500.0, "style_code": "8448-84", "efficiency_pct": 90.0, "kilopicks": 430.0, "meters": 130.0,
                                  "warp_stops": 6, "weft_stops": 4}
    assert r[(2, "C")].values["efficiency_pct"] == 74.0
    assert {x.prod_date for x in res.records} == {date(2026, 9, 1)}
    assert {x.category for x in res.records} == {"TY"}
    assert all(c.status == "MATCH" for c in res.checks), [c.as_dict() for c in res.checks if c.status != "MATCH"]
    assert not [i for i in res.issues if i.severity == "ERROR"]


def test_ty_widths_and_fabric_descriptions_come_from_the_lower_section():
    res = mill_workbook.parse([grids.ty_sheet()])
    widths = {f.loom_no: f.width_cm for f in res.loom_facts}
    assert widths == {1: 340, 2: 190, 3: 190}
    assert res.styles["8448-84"].startswith("40s Vortex")


def test_unavailable_is_not_zero():
    """SZ sheets leave warp/weft empty: stored as None (unavailable). A reported 0 stays 0."""
    res = mill_workbook.parse([grids.sz_sheet()])
    assert len(res.records) == 6
    assert all(x.values["warp_stops"] is None and x.values["weft_stops"] is None for x in res.records)
    sheet = grids.ty_sheet()
    sheet.rows[2][6] = 0  # L01 shift A warp = 0
    rec = next(x for x in mill_workbook.parse([sheet]).records if x.loom_no == 1 and x.shift == "A")
    assert rec.values["warp_stops"] == 0


def test_spreadsheet_errors_become_row_level_issues():
    sheet = grids.ty_sheet()
    sheet.rows[3][4] = "#REF!"  # L02 shift A kilopicks
    res = mill_workbook.parse([sheet])
    rec = next(x for x in res.records if x.loom_no == 2 and x.shift == "A")
    assert rec.values["kilopicks"] is None
    issue = next(i for i in res.issues if i.code == "INVALID_VALUE")
    assert (issue.sheet, issue.row, issue.raw_value) == ("01.09.26-TY", 4, "#REF!")


def test_day_report_disagreement_is_flagged_not_hidden():
    sheet = grids.ty_sheet()
    sheet.rows[3][20] = sheet.rows[3][20] / 2  # L02 day meters halved, as in the real September file
    res = mill_workbook.parse([sheet])
    assert any(i.code == "DAY_TOTAL_MISMATCH" and i.row == 4 for i in res.issues)


def test_duplicate_loom_rows_are_reported():
    sheet = grids.ty_sheet()
    sheet.rows.insert(4, list(sheet.rows[3]))
    res = mill_workbook.parse([sheet])
    assert any(i.code == "DUPLICATE_LOOM_ROW" for i in res.issues)
    assert len(res.records) == 9


def test_efficiency_out_of_range_is_rejected():
    sheet = grids.ty_sheet()
    sheet.rows[2][3] = 184.0
    res = mill_workbook.parse([sheet])
    rec = next(x for x in res.records if x.loom_no == 1 and x.shift == "A")
    assert rec.values["efficiency_pct"] is None
    assert any(i.code == "IMPLAUSIBLE_VALUE" for i in res.issues)


def test_kilopicks_inconsistent_with_efficiency_are_flagged():
    from app.mill.importers import check_consistency

    sheets = [grids.ty_sheet(f"{d:02d}.09.26-TY") for d in range(1, 4)]
    sheets[1].rows[3][9] = 53.0  # L02 shift B: 92% efficiency but a tenth of the usual kilopicks
    res = mill_workbook.parse(sheets)
    check_consistency(res)
    flagged = [i for i in res.issues if i.code == "INCONSISTENT_VALUES"]
    assert [(i.sheet, i.row) for i in flagged] == [("02.09.26-TY", 4)]
    assert next(r for r in res.records if r.sheet == "02.09.26-TY" and r.loom_no == 2 and r.shift == "B").values["kilopicks"] == 53.0  # kept as reported


# ------------------------------------------------------------------ machine exports


def test_tsudakoma_pick_and_mtr_units():
    pick = tsudakoma_export.parse(grids.tsudakoma_sheets("x100 picks"))
    mtr = tsudakoma_export.parse(grids.tsudakoma_sheets("meter"))
    assert pick.summary["cloth_length_unit"] == "x100picks" and mtr.summary["cloth_length_unit"] == "meter"
    p = {(r.loom_no, r.shift): r for r in pick.records}
    m = {(r.loom_no, r.shift): r for r in mtr.records}
    assert set(p) == set(m) == {(1, "A"), (2, "A"), (1, "B")}
    assert p[(1, "A")].values["kilopicks"] == 340.1 and "meters" not in p[(1, "A")].values
    assert m[(1, "A")].values["meters"] == 159.3 and "kilopicks" not in m[(1, "A")].values
    assert p[(1, "A")].values["warp_stops"] == 11 and p[(1, "A")].values["weft_stops"] == 56 and p[(1, "A")].values["other_stops"] == 5
    assert p[(1, "A")].extras["stop_counts_by_sensor"]["Dropper"] == 11.0
    for res in (pick, mtr):
        assert all(c.status == "MATCH" for c in res.checks), [c.as_dict() for c in res.checks if c.status != "MATCH"]


def test_all_zero_air_means_not_measured():
    res = tsudakoma_export.parse(grids.tsudakoma_sheets())
    assert all(r.values["air_nm3"] is None and r.extras["air_consumption_reported_nm3"] == 0 for r in res.records)
    assert any(i.code == "AIR_NOT_MEASURED" for i in res.issues)


def test_toyota_export_totals_and_panel_factor():
    res = toyota_export.parse(grids.toyota_sheets())
    assert len(res.records) == 2
    r = {x.loom_no: x for x in res.records}
    assert r[1].values["run_min"] == 442.167 and r[40].values["kilopicks"] == 499.0
    assert all(c.status == "MATCH" for c in res.checks), [c.as_dict() for c in res.checks if c.status != "MATCH"]
    factors = {f.loom_no: f.attributes["toyota_panel_factor"] for f in res.loom_facts}
    assert factors == {1: 2.0, 40: 1.0}


def test_detection_is_by_structure():
    assert detect([grids.ty_sheet(), grids.sz_sheet()]) == mill_workbook.FORMAT
    assert detect(grids.tsudakoma_sheets()) == tsudakoma_export.FORMAT
    assert detect(grids.toyota_sheets()) == toyota_export.FORMAT
    with pytest.raises(UnknownFormat):
        detect([Sheet("Sheet1", [["a", "b"]])])
    fmt, res = detect_and_parse(grids.toyota_sheets())
    assert fmt == toyota_export.FORMAT and res.records


# ------------------------------------------------------------------ metric formulas


def test_efficiency_is_time_weighted():
    rows = [{"efficiency_pct": 90.0, "run_min": 432.0, "stop_min": 48.0}, {"efficiency_pct": 50.0, "run_min": 120.0, "stop_min": 120.0}]
    assert M.eff_weighted(rows) == pytest.approx((90 * 480 + 50 * 240) / 720)
    # Without monitored minutes every record is a full 480-minute shift: the plain mean.
    assert M.eff_weighted([{"efficiency_pct": 90.0}, {"efficiency_pct": 80.0}]) == pytest.approx(85.0)


def test_stop_rate_uses_records_with_both_fields_only():
    rows = [{"warp_stops": 10, "kilopicks": 500.0}, {"warp_stops": None, "kilopicks": 400.0}, {"warp_stops": 5, "kilopicks": None}]
    assert M.rate_cmpx(rows, "warp_stops") == pytest.approx(10 / 500 * 100)


def test_aggregate_keeps_missing_out_of_sums():
    rows = [{"loom_id": 1, "meters": 100.0, "kilopicks": None, "efficiency_pct": None, "warp_stops": None, "weft_stops": None},
            {"loom_id": 2, "meters": None, "kilopicks": None, "efficiency_pct": 80.0, "warp_stops": None, "weft_stops": None}]
    a = M.aggregate(rows)
    assert a["meters"] == 100.0 and a["kilopicks"] is None and a["warp_stops"] is None
    assert a["coverage"]["meters"] == 1 and a["coverage"]["efficiency_pct"] == 1


def test_robust_z():
    hist = [90.0, 91.0, 89.0, 90.5, 89.5, 90.0, 91.5]
    assert M.robust_z(70.0, hist) < -3.5
    assert M.robust_z(90.0, [90.0] * 7) is None  # no spread: no score rather than a division by zero
