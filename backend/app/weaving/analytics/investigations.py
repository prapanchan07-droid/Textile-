"""
Investigations: look for things worth a person's attention and return them with their evidence.

Each investigation is deterministic SQL + statistics over the weaving tables. None of them decides
what caused a problem. A finding separates what the data shows (facts), which differences are unlikely
to be chance (signals), plausible explanations (hypotheses, always UNVERIFIED, each with how to check
it) and suggested next steps. A cause is only ever recorded as verified through a completed action's
outcome (WvAction), never inferred here.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import date, timedelta
from typing import Dict, List, Optional, Tuple

from sqlalchemy import select

from app.schemas.weaving_intel import Evidence, Finding, Hypothesis, ImpactEstimate, Signal
from app.weaving import models as m
from app.weaving.analytics import calc, stats
from app.weaving.analytics.context import BASELINE_DAYS, AnalysisContext
from app.weaving.analytics.findings import confidence, data_limitations, lakhs, priority_score, sort_findings

# Thresholds (documented in docs/weaving-intelligence.md)
DECLINE_MIN_DROP_PTS = 3.0
DECLINE_MIN_T = 2.0
DECLINE_MIN_DAY_HOURS = 6.0  # a day needs this many measured hours to be a point in the series
STOP_RATE_RATIO = 1.8
STOP_MIN_EVENTS = 6
BEAM_RATE_RATIO = 1.6
BEAM_MIN_EVENTS = 10
BEAM_MIN_PICKS = 150_000
SHIFT_DEFECT_RATIO = 1.4
SHIFT_MIN_DEFECTS = 15
SHIFT_MIN_METRES = 300.0


def _d(d: date) -> str:
    return d.isoformat()


def _period(a: date, b: date) -> str:
    return f"{_d(a)} to {_d(b)}"


def _r(x: Optional[float], n: int = 1) -> Optional[float]:
    return None if x is None else round(x, n)


# ============================================================================ 1. loom below its own baseline

def loom_declines(ctx: AnalysisContext) -> List[Finding]:
    refs = ctx.refs
    hist_start, end = ctx.hist_start, ctx.window.end_date
    rows = ctx.prod_between(hist_start, end)
    params = calc.loom_impact_params(ctx.prod_between(ctx.lens_start, end), refs)
    by_loom_day = calc.roll_production(rows, lambda r: (r.loom_id, r.shift_date))
    by_loom: Dict[int, List[Tuple[date, calc.ProdAgg]]] = defaultdict(list)
    for (loom_id, d), agg in by_loom_day.items():
        if agg.measured_s >= DECLINE_MIN_DAY_HOURS * 3600 and agg.efficiency_pct is not None:
            by_loom[loom_id].append((d, agg))
    meters_by_loom_style = calc.roll_production(rows, lambda r: (r.loom_id, r.style_id))
    dominant_style: Dict[int, Optional[int]] = {}
    for (loom_id, style_id), agg in meters_by_loom_style.items():
        if loom_id not in dominant_style or agg.meters > meters_by_loom_style[(loom_id, dominant_style[loom_id])].meters:
            dominant_style[loom_id] = style_id

    findings: List[Finding] = []
    for loom_id, series in by_loom.items():
        series.sort(key=lambda x: x[0])
        effs = [a.efficiency_pct for _d_, a in series]
        shift = stats.level_shift(effs)
        if not shift:
            continue
        drop = shift["before_mean"] - shift["after_mean"]
        if drop < DECLINE_MIN_DROP_PTS or shift["t"] < DECLINE_MIN_T:
            continue
        i = shift["index"]
        started = series[i][0]
        before_days, after_days = [d for d, _ in series[:i]], [d for d, _ in series[i:]]
        before_set, after_set = set(before_days), set(after_days)
        before = calc.total_production([r for r in rows if r.loom_id == loom_id and r.shift_date in before_set])
        after = calc.total_production([r for r in rows if r.loom_id == loom_id and r.shift_date in after_set])
        loom = refs.looms[loom_id]
        code = loom.loom_code

        # utilization vs speed: is it stopping more, or running slower?
        def speed(agg: calc.ProdAgg) -> Optional[float]:
            run_min = agg.measured_running_s / 60.0
            return agg.picks / (loom.rated_rpm * run_min) * 100.0 if run_min > 0 else None

        # which stop causes went up (eligible stops per 100k picks), before vs after the change date
        stop_rows = [r for r in ctx.stops_between(hist_start, end) if r.loom_id == loom_id and r.counts_toward_rate]
        sb = calc.roll_stops([r for r in stop_rows if r.shift_date in before_set], lambda r: r.reason_id)
        sa = calc.roll_stops([r for r in stop_rows if r.shift_date in after_set], lambda r: r.reason_id)
        cause_facts, top_cause = [], None
        for rid in sorted(sa, key=lambda k: -sa[k].eligible_events):
            ra, rb = sa[rid], sb.get(rid, calc.StopAgg())
            ratio, p = stats.rate_ratio_test(ra.eligible_events, max(after.picks, 1.0), rb.eligible_events, max(before.picks, 1.0))
            if ratio is not None and ratio >= 1.5 and ra.eligible_events >= 8 and p is not None and p < 0.01:
                reason = refs.reasons[rid]
                cause_facts.append(
                    f"{reason.name} stops rose from {_r(rb.per_100k_picks(before.picks), 1)} to {_r(ra.per_100k_picks(after.picks), 1)} per 100,000 picks "
                    f"({rb.eligible_events} before, {ra.eligible_events} after; rate ratio {ratio:.1f}, p ≈ {p:.2g})"
                )
                if top_cause is None:
                    top_cause = (reason, ratio, p)

        # do comparable looms (same dominant style) show the same drop over the same dates?
        peers = [i for i, st in dominant_style.items() if st == dominant_style.get(loom_id) and i != loom_id]
        peer_change = []
        for pid in peers:
            pb = calc.total_production([r for r in rows if r.loom_id == pid and r.shift_date in before_set]).efficiency_pct
            pa = calc.total_production([r for r in rows if r.loom_id == pid and r.shift_date in after_set]).efficiency_pct
            if pb is not None and pa is not None:
                peer_change.append(pa - pb)
        peer_med = stats.median(peer_change) if peer_change else None

        win_agg = calc.total_production([r for r in ctx.prod_between(ctx.window.start_date, end) if r.loom_id == loom_id])
        pr = params.get(loom_id)
        impact = None
        if win_agg.capacity_picks > 0 and win_agg.picks > 0 and pr:
            lost_m = drop / 100.0 * win_agg.capacity_picks * (win_agg.meters / win_agg.picks)
            impact = ImpactEstimate(lost_m=round(lost_m, 1), lost_lakhs=round(lost_m * pr.contribution_per_m / 100_000.0, 3),
                                    assumptions=["Metres lost = efficiency drop x the loom's capacity in the report window x its metres per pick.", "Rupees = lost metres x style contribution per metre (rate - variable cost)."])

        facts = [
            f"{code} averaged {_r(shift['after_mean'])}% efficiency from {_d(started)} ({len(after_days)} days), against {_r(shift['before_mean'])}% in the {len(before_days)} days before: a drop of {_r(drop)} points.",
            f"Availability (running time) went from {_r(before.utilization_pct)}% to {_r(after.utilization_pct)}%; running speed went from {_r(speed(before))}% to {_r(speed(after))}% of rated.",
        ]
        facts += cause_facts
        if peer_med is not None:
            facts.append(f"{len(peer_change)} comparable looms (same style) changed by {peer_med:+.1f} points over the same dates (median).")

        style_before = {r.style_id for r in rows if r.loom_id == loom_id and r.shift_date in before_set and r.style_id is not None}
        style_after = {r.style_id for r in rows if r.loom_id == loom_id and r.shift_date in after_set and r.style_id is not None}
        hypotheses: List[Hypothesis] = []
        steps: List[str] = []
        if style_before != style_after and style_before and style_after:
            facts.append(f"The loom changed style: {', '.join(sorted(refs.style_code(i) for i in style_before))} before, {', '.join(sorted(refs.style_code(i) for i in style_after))} after. A different style can run at a different efficiency without any fault.")
            hypotheses.append(Hypothesis(statement="The change is the new style's normal efficiency, not a problem on the loom.", how_to_check="Compare with other looms already running the new style, and with this style's target efficiency."))
        if top_cause:
            reason = top_cause[0]
            hypotheses.append(Hypothesis(statement=f"The decline is driven by more {reason.name.lower()} stops.", how_to_check=reason.diagnostic_hint or "Inspect the loom for this stop category."))
            steps.append(f"Walk {code} with the fitter and check the {reason.name.lower()} points first. {reason.diagnostic_hint or ''}".strip())
        elif before.utilization_pct is not None and after.utilization_pct is not None and (before.utilization_pct - after.utilization_pct) < 1.0:
            steps.append(f"Availability barely changed, so look at running speed: check the loom's speed setting and the drive for {code}.")
        if peer_med is not None and peer_med > -1.5:
            hypotheses.append(Hypothesis(statement=f"The cause is specific to {code} rather than the style, since comparable looms did not decline.", how_to_check=f"Compare {code}'s settings and parts with a healthy loom on the same style."))
        elif peer_med is not None:
            hypotheses.append(Hypothesis(statement="The cause may be shared with the style (yarn, beam or sizing), since comparable looms also declined.", how_to_check="Review the yarn lot and beam preparation for this style over the same dates."))
        # context that is only a coincidence in time until someone checks it
        change_ts = ctx.cal.day_bounds(started)[0]
        beam_changes = ctx.db.execute(
            select(m.WvBeam.beam_no, m.WvBeam.yarn_lot, m.WvBeamMounting.mounted_at).join(m.WvBeamMounting, m.WvBeamMounting.beam_id == m.WvBeam.id)
            .where(m.WvBeamMounting.loom_id == loom_id, m.WvBeamMounting.mounted_at.between(change_ts - timedelta(days=1), change_ts + timedelta(days=2)))
        ).all()
        for beam_no, lot, mounted in beam_changes:
            facts.append(f"Beam {beam_no} (yarn lot {lot}) was mounted on {mounted.astimezone(ctx.cal.tz):%d %b %H:%M}, close to when the decline started. This is a coincidence in time, not a finding.")
            hypotheses.append(Hypothesis(statement=f"The new beam {beam_no} may be involved.", how_to_check="Compare warp-break rates on this beam with other beams of the same style (see the beam investigation)."))
        overdue = ctx.db.execute(select(m.WvMaintenanceEvent.task, m.WvMaintenanceEvent.planned_for).where(
            m.WvMaintenanceEvent.loom_id == loom_id, m.WvMaintenanceEvent.event_type == "PREVENTIVE", m.WvMaintenanceEvent.status == "PLANNED",
            m.WvMaintenanceEvent.planned_for < ctx.today)).all()
        for task, due in overdue:
            facts.append(f"Preventive maintenance '{task}' was due {_d(due)} and is not recorded as done ({(ctx.today - due).days} days overdue).")
            steps.append(f"Do the overdue preventive maintenance on {code} ('{task}').")
            hypotheses.append(Hypothesis(statement="Overdue maintenance may be contributing.", how_to_check="Do the maintenance, then compare the loom's efficiency over the next 3 production days."))
        if not steps:
            steps.append(f"Inspect {code} on the floor and compare it with a healthy loom on the same style.")

        n_obs = len(series)
        conf = confidence(shift["p_lower"], before.readings + after.readings, len(series),
                          missing=["Which parts or settings changed on this loom (no change log)."],
                          extra=[f"Step change found by best two-segment split; t ≈ {shift['t']:.1f} (approximate)"])
        # the step-change test is approximate: never claim more than MEDIUM from it alone
        if conf.level == "HIGH" and (len(after_days) < 5 or shift["t"] < 4.0):
            conf.level = "MEDIUM"
        severity = "HIGH" if drop >= 8 or (impact and (impact.lost_lakhs or 0) >= 1.0) else "MEDIUM" if drop >= 4 else "LOW"
        findings.append(Finding(
            key=f"loom_decline:{code}", kind="loom_decline", severity=severity,
            title=f"{code} has been {_r(drop)} points below its own earlier level since {started:%d %b}",
            facts=facts,
            evidence=Evidence(
                period=_period(series[0][0], series[-1][0]), scope={"loom": code, "style": refs.style_code(dominant_style.get(loom_id))},
                observed={"efficiency_after_pct": _r(shift["after_mean"]), "days_after": len(after_days), "decline_started_on": _d(started),
                          "utilization_after_pct": _r(after.utilization_pct), "speed_after_pct": _r(speed(after))},
                baseline={"efficiency_before_pct": _r(shift["before_mean"]), "days_before": len(before_days), "utilization_before_pct": _r(before.utilization_pct), "speed_before_pct": _r(speed(before)),
                          "peer_looms_median_change_pts": _r(peer_med)},
                n_observations=n_obs, estimated_impact=impact, limitations=data_limitations(after) + [f"Only days with at least {DECLINE_MIN_DAY_HOURS:.0f} measured hours are used.", "The start date is the best single step in the daily series; a gradual drift can look like a step."]),
            signals=[Signal(name="Step change in daily efficiency", method="best two-segment split of the daily series; Welch t, normal approximation", statistic=_r(shift["t"], 2), p_value=shift["p_lower"], note="Approximate. Treat effect size as the better guide.")],
            hypotheses=hypotheses, next_steps=steps, confidence=conf,
            priority_score=priority_score(severity, conf.level, impact.lost_lakhs if impact else None),
            audiences=["WEAVING_MANAGER", "SHIFT_SUPERVISOR", "MAINTENANCE"] + (["OWNER"] if severity == "HIGH" else []),
            link=f"/weaving/looms?loom={code}"))
    return sort_findings(findings)


# ============================================================================ 2. recurring stoppage patterns

def recurring_stops(ctx: AnalysisContext) -> List[Finding]:
    refs = ctx.refs
    ls, le = ctx.lens_start, ctx.lens_end
    prod = ctx.prod_between(ls, le)
    stops = [r for r in ctx.stops_between(ls, le) if not r.is_planned]
    base_stops = [r for r in ctx.stops_between(ctx.baseline_start, ctx.baseline_end) if not r.is_planned]
    base_prod = ctx.prod_between(ctx.baseline_start, ctx.baseline_end)
    picks_by_loom = {k: v.picks for k, v in calc.roll_production(prod, lambda r: r.loom_id).items()}
    picks_by_loom_shift = {k: v.picks for k, v in calc.roll_production(prod, lambda r: (r.loom_id, r.shift_id)).items()}
    base_picks = {k: v.picks for k, v in calc.roll_production(base_prod, lambda r: r.loom_id).items()}
    params = calc.loom_impact_params(prod, refs)
    loom_type = {i: l.loom_type for i, l in refs.looms.items()}
    type_picks: Dict[str, float] = defaultdict(float)
    for i, p in picks_by_loom.items():
        type_picks[loom_type[i]] += p
    pair = calc.roll_stops(stops, lambda r: (r.loom_id, r.reason_id))
    type_reason = calc.roll_stops(stops, lambda r: (loom_type[r.loom_id], r.reason_id))
    base_pair = calc.roll_stops(base_stops, lambda r: (r.loom_id, r.reason_id))
    days_of: Dict[Tuple[int, int], set] = defaultdict(set)
    for r in stops:
        if r.eligible_events:
            days_of[(r.loom_id, r.reason_id)].add(r.shift_date)

    findings: List[Finding] = []
    for (loom_id, reason_id), agg in pair.items():
        ev = agg.eligible_events
        n_days = len(days_of[(loom_id, reason_id)])
        if ev < STOP_MIN_EVENTS or n_days < 3:
            continue
        t = loom_type[loom_id]
        peer_events = type_reason[(t, reason_id)].eligible_events - ev
        peer_picks = type_picks[t] - picks_by_loom.get(loom_id, 0.0)
        ratio, p = stats.rate_ratio_test(ev, max(picks_by_loom.get(loom_id, 0.0), 1.0), peer_events, max(peer_picks, 1.0))
        if ratio is None or ratio < STOP_RATE_RATIO or p is None or p > 0.001:
            continue
        reason, code = refs.reasons[reason_id], refs.loom_code(loom_id)

        # same events by shift vs where the loom's picks were made
        by_shift = calc.roll_stops([r for r in stops if r.loom_id == loom_id and r.reason_id == reason_id], lambda r: r.shift_id)
        total_picks = picks_by_loom.get(loom_id, 0.0) or 1.0
        shift_facts, conc = [], None
        for sid, sa in sorted(by_shift.items(), key=lambda kv: -kv[1].eligible_events):
            share = sa.eligible_events / ev
            expected = picks_by_loom_shift.get((loom_id, sid), 0.0) / total_picks
            pc = stats.share_concentration_test(sa.eligible_events, ev, expected) if 0 < expected < 1 else None
            if share >= 0.6 and pc is not None and pc < 0.01:
                conc = (refs.shift_name(sid), share, expected, pc)
                shift_facts.append(f"{sa.eligible_events} of {ev} stops ({share * 100:.0f}%) happened in {refs.shift_name(sid)}, which ran {expected * 100:.0f}% of this loom's picks (p ≈ {pc:.2g}).")
            break

        prev = base_pair.get((loom_id, reason_id))
        base_ev = prev.eligible_events if prev else 0
        base_rate = base_ev / base_picks[loom_id] * 100_000 if base_picks.get(loom_id) else None
        now_rate = ev / picks_by_loom[loom_id] * 100_000
        trend = None
        if base_rate is not None and base_picks.get(loom_id, 0) > 100_000:
            r2, p2 = stats.rate_ratio_test(ev, picks_by_loom[loom_id], base_ev, base_picks[loom_id])
            trend = "worsening" if (r2 or 0) >= 1.5 and (p2 or 1) < 0.01 else "chronic" if base_ev >= 4 else "similar to before"

        loss = calc.downtime_impact([r for r in stops if r.loom_id == loom_id and r.reason_id == reason_id], params)
        impact = ImpactEstimate(lost_m=round(loss.lost_m, 1), lost_lakhs=round(loss.lost_lakhs, 3), assumptions=loss.assumptions) if loss.lost_m else None
        facts = [
            f"{code}: {ev} {reason.name.lower()} stops on {n_days} of the last {ctx.lens_days} production days, {_r(now_rate)} per 100,000 picks against {_r(peer_events / max(peer_picks, 1.0) * 100_000)} for other {t} looms (ratio {ratio:.1f}, p ≈ {p:.2g}).",
            f"They cost {_r(agg.downtime_min, 0):.0f} minutes of downtime ({_r(agg.avg_duration_min)} min per stop on average).",
        ] + shift_facts
        if base_rate is not None:
            facts.append(f"In the {BASELINE_DAYS} days before, the loom had {base_ev} such stops ({_r(base_rate)} per 100,000 picks)" + (f": the pattern is {trend}." if trend else "."))
        hyp = [Hypothesis(statement=f"A fault on {code} is producing repeated {reason.name.lower()} stops.", how_to_check=reason.diagnostic_hint or "Inspect the loom.")]
        steps = [f"Open a ticket on {code} for the repeated {reason.name.lower()} stops. {reason.diagnostic_hint or ''}".strip()]
        if conc:
            hyp.append(Hypothesis(statement=f"Something specific to {conc[0]} (supply, operating practice or environment) contributes.", how_to_check=f"Compare conditions and handling for {code} in {conc[0]} with the other shifts."))
            steps.append(f"Ask the {conc[0]} supervisor what differs for {code} in that shift.")
        conf = confidence(p, ev, n_days, missing=["Fault codes from the loom controller are not recorded, so the specific failing component is unknown."])
        severity = "HIGH" if (impact and (impact.lost_lakhs or 0) >= 0.5) or agg.downtime_min >= 600 else "MEDIUM"
        cat = reason.category
        aud = ["WEAVING_MANAGER", "SHIFT_SUPERVISOR"] + (["MAINTENANCE"] if cat in ("MECHANICAL", "ELECTRICAL") else []) + (["OWNER"] if severity == "HIGH" else [])
        findings.append(Finding(
            key=f"recurring_stop:{code}:{reason.code}", kind="recurring_stop", severity=severity,
            title=f"{code} keeps stopping for {reason.name.lower()}", facts=facts,
            evidence=Evidence(period=_period(ls, le), scope={"loom": code, "reason": reason.code},
                              observed={"stops": ev, "days_with_stops": n_days, "per_100k_picks": _r(now_rate), "downtime_min": _r(agg.downtime_min, 0), "avg_duration_min": _r(agg.avg_duration_min)},
                              baseline={"peer_looms_per_100k_picks": _r(peer_events / max(peer_picks, 1.0) * 100_000), "own_previous_per_100k_picks": _r(base_rate), "own_previous_stops": base_ev},
                              n_observations=ev, estimated_impact=impact,
                              limitations=["Downtime is attributed to the day each stop started.", "Peers are looms of the same type; they may run different styles."]),
            signals=[Signal(name="Stop rate above comparable looms", method="conditional exact test for two Poisson rates (one-sided)", statistic=_r(ratio, 2), p_value=p)]
                   + ([Signal(name=f"Stops concentrated in {conc[0]}", method="exact binomial vs the shift's share of picks", statistic=_r(conc[1], 3), p_value=conc[3])] if conc else []),
            hypotheses=hyp, next_steps=steps, confidence=conf, priority_score=priority_score(severity, conf.level, impact.lost_lakhs if impact else None),
            audiences=aud, link=f"/weaving/stoppages?loom={code}"))
    return sort_findings(findings)


# ============================================================================ 3. beams / yarn lots with excess warp breaks

def beam_warp_excess(ctx: AnalysisContext) -> List[Finding]:
    refs = ctx.refs
    ls, le = ctx.lens_start, ctx.lens_end
    prod = [r for r in ctx.prod_between(ls, le) if r.beam_id is not None and r.style_id is not None]
    warp_ids = {i for i, r in refs.reasons.items() if r.category == "WARP"}
    warp = [r for r in ctx.stops_between(ls, le) if r.reason_id in warp_ids and r.eligible_events and r.beam_id is not None]
    picks_beam = {k: v.picks for k, v in calc.roll_production(prod, lambda r: r.beam_id).items()}
    ev_beam: Dict[int, int] = defaultdict(int)
    for r in warp:
        ev_beam[r.beam_id] += r.eligible_events
    beam_style = {r.beam_id: r.style_id for r in prod}
    looms_of: Dict[int, set] = defaultdict(set)
    for r in prod:
        looms_of[r.beam_id].add(r.loom_id)
    by_style: Dict[int, List[int]] = defaultdict(list)
    for b, s in beam_style.items():
        by_style[s].append(b)

    findings: List[Finding] = []
    for style_id, beams in by_style.items():
        tot_ev = sum(ev_beam[b] for b in beams)
        tot_picks = sum(picks_beam.get(b, 0.0) for b in beams)
        flagged = []
        for b in beams:
            picks_b, ev_b = picks_beam.get(b, 0.0), ev_beam[b]
            if picks_b < BEAM_MIN_PICKS or ev_b < BEAM_MIN_EVENTS:
                continue
            ratio, p = stats.rate_ratio_test(ev_b, picks_b, tot_ev - ev_b, tot_picks - picks_b)
            if ratio is not None and ratio >= BEAM_RATE_RATIO and p is not None and p < 0.001:
                flagged.append((b, ev_b, picks_b, ratio, p))
        if not flagged:
            continue
        style_code = refs.style_code(style_id)
        fl_ids = {f[0] for f in flagged}
        fl_ev, fl_picks = sum(f[1] for f in flagged), sum(f[2] for f in flagged)
        ot_ev, ot_picks = tot_ev - fl_ev, tot_picks - fl_picks
        ratio, p = stats.rate_ratio_test(fl_ev, fl_picks, ot_ev, ot_picks)
        lots = defaultdict(list)
        for b in fl_ids:
            lots[refs.beams[b].yarn_lot or "unknown"].append(refs.beams[b].beam_no)
        n_looms = len(set().union(*[looms_of[b] for b in fl_ids]))
        facts = [
            f"Warp stops on {style_code}: {fl_ev} on {len(fl_ids)} beam(s) ({', '.join(sorted(refs.beams[b].beam_no for b in fl_ids))}) over {fl_picks / 1e6:.2f} M picks = {fl_ev / fl_picks * 1e5:.1f} per 100,000 picks, "
            f"against {ot_ev / max(ot_picks, 1) * 1e5:.1f} on the other {len(beams) - len(fl_ids)} beam(s) of the style ({ot_ev} stops over {ot_picks / 1e6:.2f} M picks); rate ratio {ratio:.1f}, p ≈ {p:.2g}.",
            f"The flagged beams ran on {n_looms} different loom(s).",
        ]
        hyp = []
        for lot, beam_nos in lots.items():
            all_in_lot = [b for b in beams if refs.beams[b].yarn_lot == lot]
            share = len([b for b in all_in_lot if b in fl_ids]) / len(all_in_lot) if all_in_lot else 0
            facts.append(f"Yarn lot {lot}: {len([b for b in all_in_lot if b in fl_ids])} of its {len(all_in_lot)} beam(s) in this style are flagged.")
            if len(beam_nos) >= 2 and share >= 0.6:
                hyp.append(Hypothesis(statement=f"Yarn lot {lot} (or its sizing) is weaker than the style's other lots.", how_to_check="Test retained yarn samples from this lot for strength and elongation, and compare the sizing recipe and add-on with other lots."))
        if n_looms >= 2:
            hyp.append(Hypothesis(statement="The cause travels with the beam (warp preparation or yarn), not with one loom.", how_to_check="Mount a flagged beam's remaining length on a loom with a good record, or compare the same looms on other beams."))
        else:
            hyp.append(Hypothesis(statement="The excess may be a loom effect, because only one loom ran these beams.", how_to_check="Compare this loom's warp-break rate on other beams."))
        hyp.append(Hypothesis(statement="Warp preparation (warping tension, sizing) may differ for these beams.", how_to_check="Check the warping and sizing batch records for these beams."))
        conf = confidence(p, fl_ev, ctx.lens_days, missing=["Sizing recipe, size add-on and yarn test results are not recorded in the system."],
                          extra=[f"Compared with the style's other beams in the same {ctx.lens_days}-day window"])
        excess_ev = max(0.0, fl_ev - fl_picks * ot_ev / max(ot_picks, 1))
        downtime_min = sum(r.downtime_s for r in warp if r.beam_id in fl_ids) / 60.0
        severity = "HIGH" if ratio >= 2.0 and fl_ev >= 30 else "MEDIUM"
        findings.append(Finding(
            key=f"beam_warp_excess:{style_code}", kind="beam_warp_excess", severity=severity,
            title=f"{style_code}: {len(fl_ids)} beam(s) break warp {ratio:.1f}x more than the style's other beams", facts=facts,
            evidence=Evidence(period=_period(ls, le), scope={"style": style_code, "beams": ", ".join(sorted(refs.beams[b].beam_no for b in fl_ids)), "yarn_lots": ", ".join(lots)},
                              observed={"warp_stops": fl_ev, "picks": round(fl_picks), "per_100k_picks": _r(fl_ev / fl_picks * 1e5), "downtime_min": _r(downtime_min, 0), "excess_stops_estimate": _r(excess_ev, 0)},
                              baseline={"other_beams_per_100k_picks": _r(ot_ev / max(ot_picks, 1) * 1e5), "other_beams": len(beams) - len(fl_ids), "other_beams_stops": ot_ev},
                              n_observations=fl_ev, estimated_impact=None,
                              limitations=["Beam is the beam mounted when each stop started.", "No rupee estimate: the downtime attributable to the excess has not been separated from normal warp stops.", "Many beams are compared at once; the p-value threshold is strict to allow for that."]),
            signals=[Signal(name="Warp-stop rate above the style's other beams", method="conditional exact test for two Poisson rates (one-sided), flagged beams pooled", statistic=_r(ratio, 2), p_value=p)],
            hypotheses=hyp, next_steps=[f"Hold the remaining beams from lot(s) {', '.join(lots)} for {style_code} until a yarn/size check is done.", "Take yarn samples from a flagged beam and a normal beam of the same style for a strength test."],
            confidence=conf, priority_score=priority_score(severity, conf.level, None),
            audiences=["WEAVING_MANAGER", "QUALITY"] + (["OWNER"] if severity == "HIGH" else []), link="/weaving/stoppages"))
    return sort_findings(findings)


def beam_change_effect(ctx: AnalysisContext, style_code: str) -> dict:
    """
    For one style: on each loom where a beam was replaced during the lens, warp-stop rate on the previous
    beam vs the new beam. Answers "did performance change after a beam change?" without claiming why.
    """
    refs = ctx.refs
    style_id = next((i for i, s in refs.styles.items() if s.style_code == style_code), None)
    if style_id is None:
        return {"style": style_code, "pairs": [], "note": "Unknown style"}
    ls, le = ctx.lens_start, ctx.lens_end
    prod = [r for r in ctx.prod_between(ls - timedelta(days=14), le) if r.style_id == style_id and r.beam_id is not None]
    warp_ids = {i for i, r in refs.reasons.items() if r.category == "WARP"}
    warp = [r for r in ctx.stops_between(ls - timedelta(days=14), le) if r.reason_id in warp_ids and r.beam_id is not None]
    picks = {k: v for k, v in calc.roll_production(prod, lambda r: (r.loom_id, r.beam_id)).items()}
    ev: Dict[Tuple[int, int], int] = defaultdict(int)
    for r in warp:
        ev[(r.loom_id, r.beam_id)] += r.eligible_events
    first_day: Dict[Tuple[int, int], date] = {}
    for r in prod:
        k = (r.loom_id, r.beam_id)
        first_day[k] = min(first_day.get(k, r.shift_date), r.shift_date)
    by_loom: Dict[int, List[Tuple[date, int]]] = defaultdict(list)
    for (loom_id, beam_id), d in first_day.items():
        by_loom[loom_id].append((d, beam_id))
    pairs, pooled = [], {"prev_ev": 0, "prev_picks": 0.0, "new_ev": 0, "new_picks": 0.0}
    for loom_id, lst in by_loom.items():
        lst.sort()
        for (d0, b0), (d1, b1) in zip(lst, lst[1:]):
            if d1 < ls:
                continue
            p0, p1 = picks[(loom_id, b0)], picks[(loom_id, b1)]
            if p0.picks < 50_000 or p1.picks < 50_000:
                continue
            e0, e1 = ev[(loom_id, b0)], ev[(loom_id, b1)]
            ratio, p = stats.rate_ratio_test(e1, p1.picks, e0, p0.picks)
            pairs.append({"loom": refs.loom_code(loom_id), "previous_beam": refs.beams[b0].beam_no, "new_beam": refs.beams[b1].beam_no, "changed_on": _d(d1),
                          "previous_warp_stops_per_100k": _r(e0 / p0.picks * 1e5), "new_warp_stops_per_100k": _r(e1 / p1.picks * 1e5),
                          "previous_efficiency_pct": _r(p0.efficiency_pct), "new_efficiency_pct": _r(p1.efficiency_pct),
                          "rate_ratio": _r(ratio, 2), "p_value": p, "previous_yarn_lot": refs.beams[b0].yarn_lot, "new_yarn_lot": refs.beams[b1].yarn_lot})
            pooled["prev_ev"] += e0; pooled["prev_picks"] += p0.picks; pooled["new_ev"] += e1; pooled["new_picks"] += p1.picks
    ratio, p = stats.rate_ratio_test(pooled["new_ev"], pooled["new_picks"], pooled["prev_ev"], pooled["prev_picks"])
    return {"style": style_code, "period": _period(ls, le), "pairs": sorted(pairs, key=lambda x: x["changed_on"]),
            "pooled": {"new_beams_per_100k": _r(pooled["new_ev"] / pooled["new_picks"] * 1e5) if pooled["new_picks"] else None,
                       "previous_beams_per_100k": _r(pooled["prev_ev"] / pooled["prev_picks"] * 1e5) if pooled["prev_picks"] else None,
                       "rate_ratio": _r(ratio, 2), "p_value": p, "beam_changes": len(pairs)},
            "note": "Association only: a higher rate after a beam change does not show the beam is the cause. See the beam and yarn-lot finding for contributing factors."}


# ============================================================================ 4. defect rate by shift

def shift_defect_shifts(ctx: AnalysisContext) -> List[Finding]:
    refs = ctx.refs
    insp, defs = ctx.insp_between(ctx.lens_start, ctx.lens_end)
    binsp, bdefs = ctx.insp_between(ctx.baseline_start, ctx.baseline_end)
    by_shift_style = calc.roll_quality(insp, defs, lambda r: (r.shift_id, r.style_id))
    by_style = calc.roll_quality(insp, defs, lambda r: r.style_id)
    base_ss = calc.roll_quality(binsp, bdefs, lambda r: (r.shift_id, r.style_id))
    prod_ss = calc.roll_production(ctx.prod_between(ctx.lens_start, ctx.lens_end), lambda r: (r.shift_id, r.style_id))

    findings: List[Finding] = []
    for (sid, style_id), q in by_shift_style.items():
        rest_def = by_style[style_id].defects - q.defects
        rest_m = by_style[style_id].length_m - q.length_m
        if q.defects < SHIFT_MIN_DEFECTS or q.length_m < SHIFT_MIN_METRES or rest_m < SHIFT_MIN_METRES:
            continue
        ratio, p = stats.rate_ratio_test(q.defects, q.length_m, rest_def, rest_m)
        if ratio is None or ratio < SHIFT_DEFECT_RATIO or p is None or p > 0.001:
            continue
        shift_name, style_code = refs.shift_name(sid), refs.style_code(style_id)
        # what kind of defect explains the excess, and where
        type_rows = defaultdict(lambda: [0, 0])
        for d in defs:
            if d.style_id == style_id:
                type_rows[(d.defect_type_id, d.shift_id == sid)][0] += d.defects
        by_type = []
        for t in {k[0] for k in type_rows}:
            a, b = type_rows[(t, True)][0], type_rows[(t, False)][0]
            r_t, p_t = stats.rate_ratio_test(a, q.length_m, b, rest_m)
            by_type.append((t, a, b, r_t, p_t))
        by_type.sort(key=lambda x: -(x[1] - x[2] * q.length_m / rest_m))
        type_facts = [f"{refs.defect_types[t].name}: {a} in {shift_name} ({a / q.length_m * 100:.2f} per 100 m) vs {b} in other shifts ({b / rest_m * 100:.2f} per 100 m)" for t, a, b, r_t, p_t in by_type[:2] if a]
        loom_def = calc.roll_quality([r for r in insp if r.shift_id == sid and r.style_id == style_id], [d for d in defs if d.shift_id == sid and d.style_id == style_id], lambda r: r.loom_id)
        top_loom = max(loom_def.items(), key=lambda kv: kv[1].defects) if loom_def else None
        base = base_ss.get((sid, style_id))
        base_rate = base.defects_per_100m if base and base.length_m >= SHIFT_MIN_METRES else None
        ctx_prod = prod_ss.get((sid, style_id))
        facts = [
            f"{style_code} in {shift_name}: {q.defects} defects over {q.length_m:.0f} m inspected = {q.defects_per_100m:.2f} per 100 m, against {rest_def / rest_m * 100:.2f} per 100 m for {style_code} in the other shifts ({rest_def} over {rest_m:.0f} m); rate ratio {ratio:.1f}, p ≈ {p:.2g}.",
            f"First-grade share: {_r(q.grade_a_pct)}% in {shift_name} vs {_r(by_style[style_id].grade_a_pct)}% for the style overall.",
        ] + type_facts
        if top_loom:
            facts.append(f"{top_loom[1].defects} of those defects ({top_loom[1].defects / q.defects * 100:.0f}%) came from {refs.loom_code(top_loom[0])}.")
        if base_rate is not None:
            facts.append(f"The same shift and style had {base_rate:.2f} defects per 100 m in the {BASELINE_DAYS} days before.")
        if ctx_prod:
            facts.append(f"Context: that shift's looms on this style ran at {_r(ctx_prod.efficiency_pct)}% efficiency and {_r(ctx_prod.utilization_pct)}% availability.")
        hyp = [
            Hypothesis(statement="A set-up or tension difference on this shift's looms (shedding, reed, take-up) is producing the defects.", how_to_check="Compare loom settings and a fabric sample from this shift against the same style in another shift."),
            Hypothesis(statement="Operating or handling practice differs between shifts.", how_to_check="Observe a changeover and a doffing in this shift against another shift; review the checklist."),
        ]
        if base_rate is not None and ratio >= 1.4:
            hyp.append(Hypothesis(statement="Something changed recently, since this shift did not have the problem before.", how_to_check="Ask what changed on this style in this shift (yarn lot, beam, settings, people) around the start of the rise."))
        conf = confidence(p, q.defects, ctx.lens_days, missing=["Defects are not tied to the beam/yarn lot at roll level beyond the beam recorded on the roll.", "No ambient (humidity/temperature) data."],
                          extra=[f"Inspection covers rolls inspected within the {ctx.lens_days}-day window; uninspected rolls are not assumed clean"])
        severity = "HIGH" if ratio >= 2.0 and q.defects >= 40 else "MEDIUM"
        findings.append(Finding(
            key=f"shift_defect_shift:{refs.shifts[sid].code}:{style_code}", kind="shift_defect_shift", severity=severity,
            title=f"{style_code} defects are {ratio:.1f}x higher in {shift_name}", facts=facts,
            evidence=Evidence(period=_period(ctx.lens_start, ctx.lens_end), scope={"style": style_code, "shift": shift_name},
                              observed={"defects": q.defects, "metres_inspected": _r(q.length_m, 0), "defects_per_100m": _r(q.defects_per_100m, 2), "points_per_100m": _r(q.points_per_100m, 2), "grade_a_pct": _r(q.grade_a_pct)},
                              baseline={"other_shifts_defects_per_100m": _r(rest_def / rest_m * 100, 2), "other_shifts_metres": _r(rest_m, 0), "same_shift_previous_defects_per_100m": _r(base_rate, 2)},
                              n_observations=q.defects, estimated_impact=None,
                              limitations=["No rupee estimate: the price difference between grades is not recorded.", "A roll is attributed to the shift in which it was removed from the loom; it may have been woven across shifts.", "Only inspected fabric counts."]),
            signals=[Signal(name="Defect rate above other shifts", method="conditional exact test for two Poisson rates (one-sided)", statistic=_r(ratio, 2), p_value=p)],
            hypotheses=hyp, next_steps=[f"Quality to inspect {style_code} rolls from {shift_name} against another shift's, focusing on {by_type[0] and refs.defect_types[by_type[0][0]].name.lower() or 'the top defect'}.", f"Supervisor to review set-up and handling of {style_code} looms in {shift_name}."],
            confidence=conf, priority_score=priority_score(severity, conf.level, None),
            audiences=["WEAVING_MANAGER", "QUALITY", "SHIFT_SUPERVISOR"] + (["OWNER"] if severity == "HIGH" else []), link="/weaving/quality"))
    return sort_findings(findings)


# ============================================================================ 5. maintenance priorities

def maintenance_priorities(ctx: AnalysisContext, recurring: Optional[List[Finding]] = None, alerts: Optional[list] = None) -> List[Finding]:
    """
    Rank looms for the maintenance team. Score = urgency (a breakdown open now, overdue PM, and machine-watch alerts:
    critical 2, warning 1) + recurrence (mechanical/electrical stop pattern) + estimated production impact, weighted by
    evidence strength. Machine-watch alerts are early-warning signals that have not been validated against real failures.
    """
    refs = ctx.refs
    recurring = recurring if recurring is not None else recurring_stops(ctx)
    mech_cats = {"MECHANICAL", "ELECTRICAL"}
    by_loom: Dict[str, dict] = defaultdict(lambda: {"urgency": 0.0, "facts": [], "steps": [], "impact": 0.0, "events": 0, "conf": "LOW", "patterns": [], "alert_levels": set()})
    # open stoppages for mechanical / electrical reasons
    for r in ctx.stops_window:
        reason = refs.reasons[r.reason_id]
        if r.open_events and reason.category in mech_cats:
            code = refs.loom_code(r.loom_id)
            e = by_loom[code]
            e["urgency"] += 3.0
            e["facts"].append(f"{code} is stopped now for {reason.name.lower()} (stop still open).")
            e["steps"].append(f"Attend {code} now: stopped for {reason.name.lower()}.")
    for f in recurring:
        if f.evidence.scope.get("reason") in {"MECHANICAL", "ELECTRICAL"}:
            code = f.evidence.scope["loom"]
            e = by_loom[code]
            e["events"] += int(f.evidence.observed["stops"] or 0)
            e["impact"] += f.evidence.estimated_impact.lost_lakhs if f.evidence.estimated_impact and f.evidence.estimated_impact.lost_lakhs else 0.0
            e["facts"].append(f.title + f" ({f.evidence.observed['stops']} stops, {f.evidence.observed['downtime_min']} min).")
            e["steps"] += f.next_steps[:1]
            e["conf"] = f.confidence.level if f.confidence.level == "HIGH" else e["conf"]
            e["patterns"].append(f.key)
    for a in alerts or []:
        if a.level not in ("CRITICAL", "WARNING") or a.kind == "SENSOR_OFFLINE":
            continue
        e = by_loom[a.loom]
        e["urgency"] += 2.0 if a.level == "CRITICAL" else 1.0
        e["facts"].append(f"Machine watch: {a.title} ({a.level.lower()}). {a.facts[0]}")
        e["steps"].append(f"Inspect {a.loom}: {a.hypothesis}")
        e["alert_levels"].add(a.level)
    overdue = ctx.db.execute(select(m.WvMaintenanceEvent.loom_id, m.WvMaintenanceEvent.task, m.WvMaintenanceEvent.planned_for).where(
        m.WvMaintenanceEvent.event_type == "PREVENTIVE", m.WvMaintenanceEvent.status == "PLANNED", m.WvMaintenanceEvent.planned_for < ctx.today)).all()
    for loom_id, task, due in overdue:
        code = refs.loom_code(loom_id)
        days = (ctx.today - due).days
        if code in by_loom:  # only matters for the ranking when the loom also has current trouble
            by_loom[code]["urgency"] += min(2.0, days / 7.0)
            by_loom[code]["facts"].append(f"Preventive maintenance '{task}' is {days} days overdue.")
            by_loom[code]["steps"].append(f"Do the overdue '{task}' on {code}.")
    findings: List[Finding] = []
    for code, e in by_loom.items():
        score = e["urgency"] + e["events"] / 10.0 + e["impact"] * 2.0
        if score <= 0:
            continue
        sev = "HIGH" if e["urgency"] >= 3 or e["impact"] >= 0.5 or "CRITICAL" in e["alert_levels"] else "MEDIUM"
        conf = confidence(None, e["events"], ctx.lens_days, extra=["Ranking combines recorded stops and maintenance records; it is not a failure prediction"],
                          missing=["Controller fault codes and vibration/temperature readings are not available."])
        conf.level = "HIGH" if e["conf"] == "HIGH" and e["urgency"] > 0 else ("MEDIUM" if e["events"] >= 10 or e["urgency"] >= 2 else "LOW")
        findings.append(Finding(
            key=f"maintenance_priority:{code}", kind="maintenance_priority", severity=sev, title=f"Maintenance priority: {code}",
            facts=e["facts"], evidence=Evidence(period=_period(ctx.lens_start, ctx.lens_end), scope={"loom": code},
                                                observed={"urgency_points": round(e["urgency"], 2), "mech_elec_stops": e["events"], "ranking_score": round(score, 2)},
                                                n_observations=e["events"], estimated_impact=ImpactEstimate(lost_m=0.0, lost_lakhs=round(e["impact"], 3)) if e["impact"] else None,
                                                limitations=["Score = urgency (open breakdown, overdue PM) + recurrence/10 + 2 x estimated lakh impact. A heuristic for ordering work."]),
            hypotheses=[], next_steps=list(dict.fromkeys(e["steps"])), confidence=conf,
            priority_score=round(score * {"HIGH": 1.0, "MEDIUM": 0.6, "LOW": 0.3}[conf.level], 4), audiences=["MAINTENANCE", "WEAVING_MANAGER"], link=f"/weaving/stoppages?loom={code}"))
    return sort_findings(findings)


# ============================================================================ all together

def all_findings(ctx: AnalysisContext, include_maintenance: bool = False) -> List[Finding]:
    """
    Every finding, highest priority first. Maintenance rankings use their own scale (urgency points) and
    mostly restate the recurring-stop findings, so they are left out of the cross-kind list unless asked for.
    """
    recurring = recurring_stops(ctx)
    out = loom_declines(ctx) + recurring + beam_warp_excess(ctx) + shift_defect_shifts(ctx)
    if include_maintenance:
        out += maintenance_priorities(ctx, recurring)
    return sort_findings(out)


def priorities_for(role: Optional[str], findings: List[Finding], limit: int = 5) -> List[Finding]:
    """The answer to "what should we focus on today?": findings for this role, highest priority first."""
    keep = [f for f in findings if role is None or role in f.audiences]
    return sort_findings(keep)[:limit]
