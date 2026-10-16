# Weaving intelligence: pages by role, the AI features, data, metrics and limits

The weaving module is a **decision-support platform**, not an ERP: it turns loom data into things people can act on
(data → analytics → problem detection → root cause → recommendation → human-approved action → measured outcome).
This document says what each role sees, how each AI feature works, what it does **not** claim, and where the data comes from.

## Pages by role

The sidebar is the only navigation. Each role has pages of its own and shared ones (`backend/app/core/roles.py`, `ROLE_SECTIONS`,
the single table that drives both the menu and the API's authorization).

| Role | Lands on | Also sees |
|---|---|---|
| **Owner / MD** | **Owner Brief**: money, delivery promises, decisions waiting, free capacity to sell | Orders & Profit, AI Scheduler (can approve), AI Insights, Compare, Action Tracker |
| **Weaving Manager** (the weaving GM) | **Command Centre**: morning brief, live floor, plan vs actual, orders at risk, crew cover | Production, Stoppages, Machines, Workforce, Orders & Profit, AI Scheduler (can approve), AI Insights, Compare, Action Tracker |
| **Shift Supervisor** | **Shift Cockpit**: this shift live, floor map, who is stopped, crew, notes | Shift Handover, Stoppages, Machines, Workforce (own shift), Action Tracker |
| **Maintenance** | **Maintenance Desk**: ranked work, PM board, breakdowns, machine watch | Machines, Stoppages, Action Tracker |
| **Quality** | **Quality Desk**: defect patterns by shift/style/yarn lot, rolls below first grade | AI Insights, Compare, Action Tracker |

Removed on purpose: the separate "Fabric quality" and "Loom floor" pages and the duplicate tab bar.

## The AI features, and what each one does not claim

All of them are deterministic statistics or optimisation over the database. Nothing is a language-model guess, and nothing is
described as a *prediction* unless it has been checked against what happened.

**Machine abnormality watch** (`analytics/sensors.py`, Machines, Maintenance, Command Centre). Vibration, motor temperature,
main-nozzle air pressure and power are reduced to a daily value per loom. Each loom is compared with **its own normal** (the
"before" side of its best step change: median and spread), not a fixed number. It raises *critical / warning / watch* alerts,
a rough time to the alarm level from the 7-day trend, detects sensors dropping out, and finds a loom that draws more power in
one shift. *Not claimed:* that an alert means a failure will happen. These are early-warning signals, not validated against real
breakdowns (the demo data is synthetic); alarm levels are typical values to be set per machine make.

**Machine health score** (0–100, per loom). Starts at 100 and subtracts, each shown separately: sensor alerts (critical 30 /
warning 15 / watch 7, capped at 45), mechanical+electrical stop rate vs same-type looms (≥3× −20, ≥2× −10), overdue PM
(−5 per week, capped 15), efficiency below its own earlier level (−10), and more than 600 days since overhaul (−5). *Not claimed:*
a probability of failure. It orders attention.

**Findings** (`analytics/investigations.py`, AI Insights). Loom decline since a date; repeated stoppages (with shift concentration);
beams / yarn lots with excess warp breaks; shifts with unusual defects; maintenance priorities. Each keeps *facts*, *statistical
signals*, *hypotheses (always unverified, each with how to check)* and a *verified cause* that stays empty unless a person records it
on a completed action. Confidence is a rule (p-value, observations, days). *Not claimed:* causes.

**Delivery-risk forecast** (`analytics/orders.py`, Orders, Owner Brief). Each order's expected completion = remaining metres ÷
its own pace over the last 7 complete production days, with an 80% range from day-to-day variation. States: late, at risk
(< 2 days slack, or late if pace dips), on track, not on a loom, stalled, done. *Not claimed:* a promise. It assumes the order keeps its looms.

**Output forecast** (`analytics/forecast.py`). Simple or damped-trend smoothing, whichever did better on a hold-out of the last five
days; the past error (MAPE) is printed beside every forecast, and no forecast is made below ~10 days of history.

**AI Scheduler** (`analytics/scheduler.py`). Simulates the next 28 days twice: *as booked* (each loom finishes its order, then takes
the next booked order of the same style) and *proposed* (lookahead hill-climbing: a loom moves only if it reduces projected weighted
lateness by at least 0.25 day, net of a 3.6-hour style-change cost). Constraints: loom type and reed space vs the style; priority-A orders
avoid looms with health < 60. Output: per-order before/after, a loom timeline (Gantt), and each move with the projected finish dates of
**both** orders. *Not claimed:* optimality, or knowledge of beam/yarn/operator availability. **It changes nothing:** the owner or weaving
manager approves (the plan's signature must match what they reviewed), which records the plan and raises one action per move.

**Compare** (`analytics/compare.py`). Any 1–8 looms, styles, shifts, loom types, beams, yarn lots, suppliers (or weavers, owner and
manager only) side by side against the first as reference. A difference is called out only if it is unlikely to be chance (exact rate
test, p < 0.01) **and** large enough to matter (≥ 1.25× / ≤ 0.8×, or ≥ 1.0 efficiency point). Recommended comparisons are generated from today's findings.

**Workforce signal.** A weaver is flagged for support only if their stops are clearly above what *any* weaver gets **on the same looms**
(loom-adjusted, ≥ 1.3×, p < 0.001, ≥ 25 stops), so a faulty loom is never blamed on its weaver. No pay data is held.

## Data model (prefix `wv_`)

```
wv_shifts   wv_looms (make, model, serial, year, shedding, power, bay, overhaul, warranty)
wv_styles (loom_type_required)   wv_yarn_lots (supplier, strength, CV)   wv_beams (yarn_lot, size_pickup)   wv_beam_mountings
wv_customers   wv_production_orders (priority, due, rate)   wv_order_assignments
wv_operators (designation, grade, contract, experience, skills)   wv_shift_assignments   wv_attendance
wv_loom_readings   (fact, hourly: running time, picks, power, vibration, motor temperature, air pressure)
wv_stop_events + wv_stop_reasons   wv_inspections + wv_defect_observations + wv_defect_types
wv_maintenance_events   wv_shift_notes   wv_schedule_plans   wv_actions (finding_key, approval, outcome, verified_cause)
```

Facts carry the style, beam, shift and weaver that applied when they happened, so every comparison is a `GROUP BY`. Business keys are unique
(`loom_code`, `beam_no`, `order_no`, `roll_no`, `employee_code`...), which keeps imports and the seed idempotent. Sensor columns are nullable
(a loom may have none, or a sensor may be offline). `data_origin` marks DEMO / IMPORTED / LIVE.

**Time.** Timestamps are timezone-aware. The *production day* starts when Shift I starts (06:00 mill time); Shift III belongs to the day it
started. Windows (`TODAY`, `YESTERDAY`, `LAST_7_DAYS`, `THIS_MONTH`) are sets of production days; a window still running ends at "now" and is
compared with the previous window **at the same elapsed hours**, never with a full day.

## Metrics

Authoritative definitions are in `analytics/definitions.py`, published at `GET /api/v1/weaving/analytics/definitions`. Loom efficiency =
picks ÷ (rated rpm × scheduled minutes), excluding readings with no pick counter from both sides; not called OEE. Stops per 100,000 picks counts
unplanned stops that started in the window. Average stop length covers unplanned, finished stops only. Defects per 100 m divide by metres *inspected*.
Rupee figures are estimates (lost metres × contribution per metre) with their assumptions returned.

## Authorization (enforced on the server)

| Endpoint | Who |
|---|---|
| `GET /weaving/pages/{slug}` | roles whose menu includes that page (403 otherwise); money fields are `null` for roles without financial access |
| `/weaving/pages/machines/{loom}`, `/weaving/analytics/*`, `/weaving/events/stops`, `/weaving/inspections` | the matching section |
| `/weaving/compare/run`, `/weaving/compare/options` | roles with Compare; comparing individual weavers: owner and weaving manager only |
| `/weaving/investigations/*` | any signed-in role; **findings are filtered to those addressed to the role** |
| `POST /weaving/actions` | any weaving role. Created by a manager/owner → approved; by anyone else → awaits approval. A supervisor cannot set a money value |
| `POST /weaving/actions/{ref}/approve`, `POST /weaving/scheduler/decision` | owner and weaving manager only |
| `PATCH /weaving/actions/{ref}` | any weaving role for status/outcome; **`verified_cause` only by owner, weaving manager or quality, and only on a completed action** |
| `POST /weaving/notes` | any signed-in user (saved to the current shift) |
| Report ingestion and the pre-weaving factory modules | owner and weaving manager only |

`tests/test_pages_authorization.py` checks every page for every role.

## Closing the loop

`wv_actions` links an action to the finding that prompted it (`finding_key`), records who approved it, the outcome, and (only here) a verified
cause. A later phase can compare a finding's metric before and after an action to learn whether recommendations work. Automation must stay
human-approved: nothing here executes a consequential factory action; the scheduler's approval creates tasks for people.

## Known limitations

* The only data is demonstration data until a mill's own readings are loaded; loading real data (file import, machine feeds) is the next phase.
  Sensor values are only as good as the sensors; the machine watch has not been validated on real failures.
* Hypotheses can only be listed, not discriminated, without controller fault codes, humidity, sizing records or yarn test data per beam.
* The scheduler ignores beam, yarn and operator availability and assumes constant efficiency; it is a decision aid.
* Staffing norms (4 looms per weaver, 12 per fitter) are assumptions (`analytics/workforce.py`). No price-by-grade data, so quality findings carry no rupee estimate.
* A roll is attributed to the shift it was removed in; a stop to the shift it started in. The step-change test is approximate.
* Weaving analytics require PostgreSQL. The backend Docker image build and a full `docker compose up` have not been verified end to end.
