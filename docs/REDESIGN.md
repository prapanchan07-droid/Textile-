# Frontend redesign: evaluation and decisions

Branch: `redesign/erp-platform`. Context: a composite textile mill (spinning to weaving) with 1,000+ workers and about ₹3,000 Cr turnover. People who use it every day: MD/CXOs, plant heads, maintenance, the QA lab, HR, and sales/finance.

## 1. Problems in the previous build

**Platform**
- No router. Pages were a `useState` tab: no URLs, no deep links, the browser Back button left the app, and nothing could be shared or bookmarked.
- The period filter in the header only affected Factory Overview. Every other page had its own period (or none), and each used a different spelling (`THIS_WEEK`, `SEVEN_DAYS`, `LAST_7_DAYS`). Production never sent a period.
- `decisionCenterService` and `machineComparisonService` **returned hard-coded fake data whenever the API failed**, with no indication on screen. Leadership could make a decision based on invented numbers.
- User role (`SUPER_ADMIN`) and section access were set by the browser and sent as request headers. That is not access control.
- Controls that did nothing: Export, notification bell, ⌘K search, unit switcher, Access Control, Settings, Support. There was also an `alert()` where "View details" should have been.
- Internal build labels were shown to users ("Phase 2", "Phase 7", "Foundation Specs", a Module 01 checklist). The Foundation page used dark-theme classes on a light page.
- 16 components were never used. There were two `Header.tsx` files and three different ways of calling the API (axios, raw `fetch` with hard-coded `/api/v1`, and fallbacks).
- The Action Tracker let users change status, but only in local state. Every change was lost on refresh.

**Data integrity (found by comparing pages against each other)**

| Finding | Where |
|---|---|
| The same power events are reported at **15:42 / 18:10** on Overview and **14:15 / 16:40** on Decision Center | `/overview` vs `/decision-center` |
| Production shows **0 kg** while Overview shows **34,620 kg** for the same day | Production reads only ingested reports; Overview reads synthetic data |
| "Last 7 days" and "Month to date" return the **same totals as Today** | `/overview` synthetic path ignores `period` |
| SMX-03 is labelled "Airjet Spinning" in one place and "Simplex" everywhere else | `/decision-center` |
| Loss share is 47.1% on one page and 47.0% on another | Each page calculates it separately |
| Head-to-head energy shows `0 kWh/kg` for 0.22 | `/machine-comparison` formatter rounds to an integer |
| Revenue is ₹28.5 L/month. A ₹3,000 Cr company does about ₹250 Cr/month | Sample data is about 1,000× too small, and money fields are hard-wired to lakhs |

## 2. Block-by-block verdicts

✅ keep · 🔁 merge/move · ✂️ remove · 🛠 rebuild

**Factory Overview → Control Tower**
- ✅ Production today. 🛠 Rebuilt as KPI tiles: output, achievement, efficiency, downtime, energy/kg, and defect rate, each with a delta against the comparison period.
- ✅ Why is production low. 🛠 Rebuilt as ranked bars with evidence text under each cause.
- ✂️ Compared with yesterday, as a separate section. Its deltas now sit on the KPI tiles.
- ✅ Machines needing attention. 🛠 Now a sortable table; clicking a row opens the machine drawer.
- 🔁 AI recommendation and If this continues. These are merged into one "Analyst brief" card, and the projection is a single line (it is just the daily gap × 7 and × 30).
- ➕ Added an Output by shift chart. The data was already returned by the API but was never shown.

**Decision Center → Action Center**
- ✅ Top priority, now with the evidence beside it. ✅ Why and ✅ Where, side by side. ✅ Recommended actions, which now link to the right page and machine.
- ✂️ If nothing is done, as a section. It repeated the Overview and is now one fact on the priority card.
- ✂️ AI insight, as a separate section. Its facts became the "Evidence" panel.
- 🛠 Action tracker. It is read-only until a write API exists, with filter tabs and CSV export.

**Production**
- ✅ Output, shifts, loss reasons, machine type, and factors.
- 🛠 A report-date picker replaces the period control, because the endpoint reports one date.
- 🛠 An honest empty state replaces a page full of zeros.
- 🛠 A reconciliation warning shows when shift totals don't add up.

**Machines & Downtime + Machine Comparison → one module, two tabs**
- 🛠 Fleet: a searchable, sortable machine register with CSV export, plus a downtime analysis showing planned vs unplanned time and causes.
- 🔁 Machine detail and machine trend. These moved into a machine drawer (`/assets?machine=V-09`) that can be opened from any page.
- 🔁 Machine Comparison. It is now the Benchmark tab, with the selection, metric, and reference stored in the URL. Head-to-head appears automatically when two machines are selected.

**Manpower & Quality → split into two pages**
- They have different owners (HR vs the QA lab) and different questions, so they are now separate pages.
- Quality: parameters with a meter against the spec limit, a trend with a limit line for the selected parameter, and issues by machine.
- Workforce: departments sorted by largest gap, an availability trend, and people alerts.

**Revenue & Loss → Sales & Finance**
- ✅ Revenue, trend, dispatch, and cash position. 🛠 Stock is now shown as utilisation against its limit.
- ✂️ Business performance. It repeated the same six numbers shown above it.
- 🛠 Currency switches from ₹ L to ₹ Cr automatically.

**Upload modal → Data Imports page.** It now includes the template guide ("what each sheet updates") and a searchable import history.

**Foundation Specs → System Status.** API and database health plus data freshness. The developer checklist has been removed.

## 3. New platform features

- Routed URLs for every page and view. The period, tab, machine, date, and comparison selection are all in the URL, so any view can be shared.
- One period vocabulary, mapped to each endpoint in `src/lib/period.ts`. Pages that don't support a period don't show the control.
- React Query. Data is cached across pages, the previous data stays visible (dimmed) while a new period loads, and all dashboards refresh after an import.
- **No fabricated fallbacks.** API failures show an error with a Retry button.
- Command palette (Ctrl/⌘ K) for pages, every machine, and common actions.
- Light and dark themes built on CSS tokens, following the system setting or a manual choice.
- Collapsible sidebar and a mobile drawer.
- Every chart has a table view, and every table can be exported to CSV.
- Chart palette validated for colour-blind separation.
- Indian number grouping. Weights switch to tonnes, currency to ₹ L / ₹ Cr, and durations to h/min.

## 4. What an ERP at this scale still needs (mostly backend)

Listed in priority order. None of these are shown in the UI yet, because showing modules without data behind them would repeat the old "Phase 2" problem.

1. **Authentication and RBAC** (SSO, and roles checked on the server: CXO, plant head, section in-charge, QA, HR, finance), plus an **audit log**.
2. **Master data API**: units, departments, machines, counts/qualities, shifts, and customers. This is needed before any unit filter works.
3. **Actions API** (create, assign, update status, comment, due date, SLA) so the Action Center can be written to.
4. **Real period handling** in every service, with one shared date-window helper, and a single source for each KPI so pages cannot disagree.
5. **Maintenance (CMMS)**: preventive maintenance schedules, breakdown work orders, spares, and MTBF/MTTR.
6. **Energy**: UKG (kWh per kg of yarn) by department, and power-quality events. Power is the second-largest cost in spinning.
7. **Inventory and procurement**: cotton bale lots and mixing, yarn and fabric stock by count and lot, and purchase orders.
8. **Order management and PPC**: sales order book, count-wise production plan, and dispatch schedule.
9. **Quality lab integration** (Uster/HVI files), and lot-wise quality certificates.
10. **HR and payroll integration**: biometric attendance, contract labour, and piece-rate.
11. **Notifications**: thresholds for achievement, spec limits, and downtime, delivered in-app, by email, or on WhatsApp.
12. Scheduled PDF reports for the daily MD brief, and background jobs for ingestion.

## 5. Cleanup

The old UI is no longer referenced by `main.tsx`. Once the new version has been reviewed, delete these files and folders:

```
frontend/src/App.tsx
frontend/src/components/
frontend/src/pages/
frontend/src/services/
```

`frontend/src/types/` is still used; it mirrors the backend schemas.
