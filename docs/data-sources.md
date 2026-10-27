# Data sources: what each file contains and how it is imported

The four files supplied by the mill were inspected cell by cell. Parsers detect the layout from the workbook's
structure (sheet names, header rows), never from the file name, and never modify the original file. All four
files are **historical / periodic data**: nothing from them is presented as a live machine state.

| File | What it is | Parser (`source_format`) |
|---|---|---|
| `TY,TS,SZ-Production Report- Sepember - 2026.xlsx` | The mill's own daily production book: 90 sheets, one per day × machine category (`dd.mm.yy-TY/-TS/-SZ`), 1–30 Sept 2026 | `MILL_DAILY_WORKBOOK` (`app/mill/importers/mill_workbook.py`) |
| `13-10-2026-PICK.xls` | Tsudakoma monitoring export "Report by shift", cloth length in **x100 picks**, 13 Oct 2026 | `TSUDAKOMA_SHIFT_EXPORT` (`tsudakoma_export.py`) |
| `13-10-2026-MTR.xls` | The **same** Tsudakoma report saved with cloth length in **meters** | `TSUDAKOMA_SHIFT_EXPORT` |
| `11-10-2026-ty.xls` | Toyota monitoring system "Shift Report" (author "TOYOTA Monitoring System"), 11 Oct 2026 | `TOYOTA_SHIFT_REPORT` (`toyota_export.py`) |

Machine categories (from the sheet suffixes and sheet titles): **TY = Toyota** (42 looms, L01–L42),
**TS = Tsudakoma** (24 looms, 1–24 / L001–L024), **SZ = Sulzer** (12 looms, 1–12). A loom is identified as
`<category>-<number>` (TY-01), which is how `L01` (mill report), `001` (Toyota export) and `L001` (Tsudakoma
export) are matched.

## 1. Mill daily workbook (`MILL_DAILY_WORKBOOK`)

Layout, identical in all 90 sheets (three signatures, one per category):

* **Top table** (imported). Header row starting `L. NO` (TY, row 1) or `Loom No` (TS and SZ, row 3). Columns:
  `Loom | RPM | PICK (style code) | Shift A: Eff, Kilopick, Meter, Warp, Weft | Shift B: … | Shift C: … | Day Report: …`.
  The blocks are located by their header names, not fixed positions. The table ends at the first non-loom
  row; the summary row under it (`AVG =`, `TOTAL AVERAGE` or an unlabeled average) is used only to reconcile.
* **Lower section** (not imported as production): the same looms regrouped by reed width (`340 CM`, `190 CM`,
  `360 CM`) and fabric, with the fabric description above each group; TS sheets also carry three names under
  the Shift A/B/C headers (role not stated; kept in the raw rows, not attached to records). Used for loom width,
  style descriptions and a cross-check of RPM.
* Side panels (`PICK CHANGE`, `1st & 2nd Shift`, `ON DATE / UP TO DATE` totals, maintenance names) are not
  machine rows and are not imported.

Fields imported per loom-shift: `rpm`, `style_code`, `efficiency_pct`, `kilopicks`, `meters`, `warp_stops`,
`weft_stops`. Loom facts: `width_cm` (most frequent width group across days). Styles: code and the group's
fabric description.

**Unavailable vs zero.** SZ sheets leave Warp/Weft empty in the top table (they are 0 only in the lower
section): stored as unavailable (NULL), never as 0. 7 SZ loom-shifts have no efficiency. A value of 0 in the
source stays 0.

**Result of importing the September file**: 90 sheets, 7,020 loom-shift records (78 looms × 3 shifts × 30 days),
0 errors, 144 warnings, 1,200 reconciliation checks (1,074 match, 126 mismatch). The mismatches are genuine
properties of the workbook, all visible in the import page:

| Finding | Where | Effect |
|---|---|---|
| The Day Report meters of loom L02 (TY) are half the sum of its three shifts (e.g. 178.9 vs 357.8 on 1 Sept) | every TY sheet | The sheet's TY daily meter total is short by about half of L02's output (e.g. 28,589.3 vs 28,768.2) |
| The TS shift-average efficiency leaves out loom 1 (average of 23 of 24 looms) | 23 TS shift summaries | Sheet's TS shift efficiency differs from the true average by up to ~1 pt |
| SZ Day efficiency treats a missing shift as 0 (e.g. 15.24% = 45.72 / 3) | 3 SZ loom-days | Day efficiency understated for those looms |
| RPM in the width/fabric section differs from the main table (L06 577.6 vs 550, L41 837.5 vs 750, L26 779.8 vs 1197) | 84 rows | Main table used; warning recorded |
| Width-group counts in the footer differ from the grouped rows on 9 days | 18 checks | Width per loom = its most frequent group |
| Other shift-efficiency summary differences (SZ, some TS) that no single left-out loom explains | 23 checks | Flagged; per-loom values imported as given |
| **24.09.26-SZ shift B: kilopicks of all 11 running Sulzer looms are ~10× too small** for their efficiency (e.g. SZ-01 16.5 kpicks at 82.5%) | 10 rows (+1 on 08.09.26-SZ, SZ-06 shift B at 0.22×) | `INCONSISTENT_VALUES` warnings; values kept as reported. Likely a unit or formula slip on that sheet: correct the source and re-import |

## 2. Tsudakoma export (`TSUDAKOMA_SHIFT_EXPORT`)

Sheets: `Report by term` (data), `Counter by term`, `Stop cause graph by term`, `Efficiency graph by term`
(totals, used for reconciliation) and `Temp` (the export's working sheet, not imported). `Data date:2026/10/14 06:21`.

`Report by term` has one section per machine type: the header row's first cell is the section code: **ZA**
(air-jet; holds all rows) and **ZW** (water-jet; empty). Units are on the row under the header.

| Column | Unit | Stored as |
|---|---|---|
| Date, Shift No. (1/2/3 → A/B/C), Loom No. (L001), Style No. | | `prod_date`, `shift`, loom TS-01, `style_code` |
| rpm | rpm | `rpm` |
| Mill efficiency / Loom efficiency | % | `efficiency_pct` / `loom_efficiency_pct` |
| Cloth length | x100 picks (PICK file) or meter (MTR file) | `kilopicks` (= x100 picks / 10) or `meters` |
| Total stop / Filling stop / Warp stop | minutes, times, s/cmpx | `stop_min`, `total_stops`, `weft_stop_min`, `weft_stops`, `warp_stop_min`, `warp_stops`; `other_stops` = total − warp − weft |
| H1/H2 feeler (C1–C8), Dropper, Leno L/R, CC, Package sensor (C1–C8), Counter, Stop button | times | `extras.stop_counts_by_sensor` |
| Air consumption | Nm3 | `air_nm3` (see below) |

PICK and MTR are the same report: importing both fills kilopicks and meters of the same 61 loom-shift records
(the second import updates, never duplicates). The unit is read from the header row of the section that holds
data (the empty ZW section of the PICK file is labelled "meter").

* **Air consumption is 0 Nm3 for all 61 loom-shifts.** That is a sensor not fitted / not enabled, not zero air:
  stored as unavailable, with the reported 0 kept in `extras.air_consumption_reported_nm3` and a warning.
* Looms TS-04, TS-13 and TS-16 have no rows in this export (shift A: 21 looms; B and C: 20). Recorded as an
  import note and raised by the "No production recorded" alert, never treated as zero production.
* Reconciliation: cloth length per shift vs `Counter by term` (3/3 match in both files), stop frequency per cause
  vs `Stop cause graph by term` (all 20 causes match), mill efficiency per shift vs `Efficiency graph by term`
  (3/3 within 0.15 pt; the export weights by monitored time that per-loom rows do not carry).
* The sheet's `s/cmpx` rate checks out as stops per 100,000 picks.

## 3. Toyota shift report (`TOYOTA_SHIFT_REPORT`)

Sheets: `Field Name` (field dictionary), `Data` (raw; several computed cells left empty), `Stop Count and Time`,
`Stop Rate(Hour)`, `Stop Rate(Day)`, `Stop Rate(cmpx)`. `Stop Rate(Hour)` is read: fully computed, one header row,
126 rows (42 looms × shifts A–C of 11 Oct 2026) and a `Total` row.

| Column | Stored as |
|---|---|
| Shiftname (`2026/10/11.A`) | `prod_date`, `shift` |
| Loom (`001`) | TY-01 |
| Style (`40s40s132.84-63p`; free text, not the mill's `8448-84` code) | `style_code` |
| RPM, Effic.(%), Run(min), Stop(min) | `rpm`, `efficiency_pct` (= run / (run + stop)), `run_min`, `stop_min` |
| Product(1000pick), Product(meter) | `kilopicks`, `meters` |
| Warp / Weft (times, min) | `warp_stops`, `warp_stop_min`, `weft_stops`, `weft_stop_min` |
| UnSelect (times, min), Total (times, min) | `other_stops`, `extras.unselect_stop_min`, `total_stops` |

Reconciliation against the `Total` row: kilopicks 53,509.5, meters 22,793.6, warp 1,091, weft 3,211, total stops
4,560, run minutes 54,391.7 and time-weighted efficiency 89.97%: **all match exactly**.

**Panel factor.** In `Stop Count and Time`, an unlabeled column after Product is exactly **2×** the counted picks
and meters for looms 001–012 and equal for the others. The mill report's figures for its 340 cm TY looms match
the doubled values (e.g. L01: 500 RPM but 407 kilopicks per 8-hour shift at 85%, only possible at ~1,000 picks/min).
The counted values are imported; the factor is stored per loom (`attributes.toyota_panel_factor`) and shown on the
loom page. Consequences: compare meters/kilopicks and stop rates within one source; efficiency is unaffected.
**To confirm with the mill:** the reason (two fabric panels on 340 cm looms is the likely one).

Fields listed in `Field Name` but not present in the export: `Air flow` (RYUURYOU), `Tension`, `TAPO success rate`,
`Start miss`, `Operator`, `Top beam`, `Beam`, detailed stop causes (WarpTop, Leno, False, Doff, Manual, Off…). The
report parameters show them switched off (`ryuuryou=0`, `tension=0`, …); they could be enabled in the Toyota
system.

## 4. Unverified or unsupported

* Loom **models** (JAT/ZAX generation, Sulzer type) are not in any file; the Tsudakoma section code "ZA" suggests
  ZAX-series air-jets but is not taken as proof. Set models on the loom page once confirmed.
* Sulzer RPM × time does not reproduce the reported kilopicks (e.g. 260 RPM, 197.6 kpicks, 95%): the SZ RPM or
  pick count semantics need confirming. Values are imported as reported; derived checks are not applied to SZ.
* No file carries stop **reasons**, stop durations by cause (except the Tsudakoma per-sensor counts), operator per
  loom, beam, yarn lot, energy (kWh) or measured air.
* The three TS names under the shift headers may be shift supervisors or group leaders; confirm before linking
  them to groups.

## 5. Re-running the checks

```bash
cd backend
python -m app.mill.cli import "/path/TY,TS,SZ-Production Report- Sepember - 2026.xlsx" /path/13-10-2026-PICK.xls /path/13-10-2026-MTR.xls /path/11-10-2026-ty.xls
MILL_SAMPLE_DIR=/path/to/folder TEST_DATABASE_URL=postgresql+psycopg://…/textile_test pytest tests/test_platform_pg.py::test_real_files_reconcile
```
