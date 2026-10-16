import uuid
from datetime import date, datetime, timezone
from typing import List, Literal, Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_any_section, require_section
from app.core.exceptions import ForbiddenException, NotFoundException, ValidationException
from app.core.roles import FINANCIAL_ROLES, Role
from app.db.session import get_db
from app.models.user import User
from app.schemas.common import StandardResponse
from app.schemas.weaving_intel import Finding, InspectionOut, InspectionPage, StopEventOut, StopEventPage
from app.weaving import models as m
from app.weaving.analytics import breakdowns, compare as cmp, investigations
from app.weaving.analytics.calendar import PERIODS
from app.weaving.analytics.context import AnalysisContext
from app.weaving.analytics.definitions import DEFINITIONS
from app.weaving.pages import commercial, intel, machines, ops, overview, people
from app.weaving.pages.shared import Mill

# Every weaving route needs a signed-in user; each route narrows it to the roles whose menu includes that page.
router = APIRouter(prefix="/weaving", tags=["Weaving intelligence"])

PeriodQ = Query("TODAY", description="TODAY, YESTERDAY, LAST_7_DAYS or THIS_MONTH (production days, mill time)")


def _need_postgres(db: Session) -> None:
    if db.bind is not None and db.bind.dialect.name != "postgresql":
        raise ValidationException("Weaving analytics need PostgreSQL. Set DATABASE_URL to a PostgreSQL database (see docs/database.md).")


def _period(p: str) -> str:
    if p not in PERIODS:
        raise ValidationException(f"period must be one of {', '.join(PERIODS)}")
    return p


def _mill(db: Session, user: User, period: str, lens_days: int = 14) -> Mill:
    _need_postgres(db)
    return Mill(db, Role(user.role), _period(period), lens_days=lens_days)


def _ok(data):
    return StandardResponse(success=True, data=data)


# ============================================================================ pages (one per sidebar item)

@router.get("/pages/command", summary="Command Centre: the weaving GM's live picture")
def page_command(period: str = PeriodQ, user: User = Depends(require_section("command")), db: Session = Depends(get_db)):
    return _ok(overview.command(_mill(db, user, period)))


@router.get("/pages/owner", summary="Owner Brief: money, delivery promises, decisions")
def page_owner(period: str = Query("LAST_7_DAYS"), user: User = Depends(require_section("owner")), db: Session = Depends(get_db)):
    return _ok(overview.owner(_mill(db, user, period)))


@router.get("/pages/production")
def page_production(period: str = PeriodQ, user: User = Depends(require_section("production")), db: Session = Depends(get_db)):
    return _ok(ops.production(_mill(db, user, period)))


@router.get("/pages/stoppages")
def page_stoppages(period: str = PeriodQ, user: User = Depends(require_section("stoppages")), db: Session = Depends(get_db)):
    return _ok(ops.stoppages(_mill(db, user, period)))


@router.get("/pages/machines")
def page_machines(user: User = Depends(require_section("machines")), db: Session = Depends(get_db)):
    return _ok(machines.fleet(_mill(db, user, "TODAY")))


@router.get("/pages/machines/{loom}")
def page_machine_detail(loom: str, user: User = Depends(require_section("machines")), db: Session = Depends(get_db)):
    return _ok(machines.detail(_mill(db, user, "TODAY"), loom))


@router.get("/pages/maintenance")
def page_maintenance(user: User = Depends(require_section("maintenance")), db: Session = Depends(get_db)):
    return _ok(machines.maintenance(_mill(db, user, "TODAY")))


@router.get("/pages/workforce")
def page_workforce(user: User = Depends(require_section("workforce")), db: Session = Depends(get_db)):
    return _ok(people.workforce_page(_mill(db, user, "TODAY")))


@router.get("/pages/cockpit")
def page_cockpit(user: User = Depends(require_section("cockpit")), db: Session = Depends(get_db)):
    return _ok(people.cockpit(_mill(db, user, "TODAY")))


@router.get("/pages/handover")
def page_handover(which: Literal["current", "previous"] = "current", user: User = Depends(require_section("handover")), db: Session = Depends(get_db)):
    return _ok(people.handover(_mill(db, user, "TODAY"), which))


@router.get("/pages/orders")
def page_orders(user: User = Depends(require_section("orders")), db: Session = Depends(get_db)):
    return _ok(commercial.orders_page(_mill(db, user, "LAST_7_DAYS")))


@router.get("/pages/scheduler")
def page_scheduler(user: User = Depends(require_section("scheduler")), db: Session = Depends(get_db)):
    return _ok(commercial.scheduler_page(_mill(db, user, "TODAY")))


@router.get("/pages/insights")
def page_insights(period: str = PeriodQ, lens_days: int = Query(14, ge=3, le=60), user: User = Depends(require_section("insights")), db: Session = Depends(get_db)):
    return _ok(intel.insights(_mill(db, user, period, lens_days)))


@router.get("/pages/quality")
def page_quality(period: str = Query("LAST_7_DAYS"), user: User = Depends(require_section("quality")), db: Session = Depends(get_db)):
    return _ok(intel.quality(_mill(db, user, period)))


@router.get("/pages/actions")
def page_actions(user: User = Depends(require_section("actions")), db: Session = Depends(get_db)):
    return _ok(intel.actions_page(_mill(db, user, "TODAY")))


@router.get("/pages/compare")
def page_compare(user: User = Depends(require_section("compare")), db: Session = Depends(get_db)):
    return _ok(intel.compare_page(_mill(db, user, "LAST_7_DAYS")))


@router.get("/compare/options")
def compare_options(type: str, user: User = Depends(require_section("compare")), db: Session = Depends(get_db)):
    if type not in cmp.TYPES or (type == "weaver" and Role(user.role) not in FINANCIAL_ROLES):
        raise ValidationException("Unknown or restricted comparison type")
    return _ok(cmp.options(_mill(db, user, "LAST_7_DAYS").ctx, type))


@router.get("/compare/run", summary="Compare entities side by side; the first is the reference")
def compare_run(type: str, keys: List[str] = Query(...), metrics: Optional[List[str]] = Query(None), days: int = Query(14, ge=3, le=28), style: Optional[str] = None,
                user: User = Depends(require_section("compare")), db: Session = Depends(get_db)):
    if type not in cmp.TYPES:
        raise ValidationException("Unknown comparison type")
    if type == "weaver" and Role(user.role) not in FINANCIAL_ROLES:
        raise ForbiddenException("Comparing individual employees is limited to the owner and the weaving manager")
    if not 1 <= len(keys) <= 8:
        raise ValidationException("Pick between 1 and 8 to compare")
    return _ok(cmp.compare(_mill(db, user, "LAST_7_DAYS").ctx, type, keys, metrics, days, style))


# ============================================================================ definitions, findings, event lists

@router.get("/analytics/definitions", summary="What every metric means: formula, units, exclusions, missing-data handling")
def metric_definitions(user: User = Depends(get_current_user)):
    return _ok([d.__dict__ for d in DEFINITIONS])


@router.get("/analytics/production", summary="Production, efficiency and utilization grouped by loom, style, beam, shift, day or loom type")
def production_analytics(period: str = PeriodQ, group_by: Literal["loom", "style", "beam", "shift", "day", "loom_type"] = "loom",
                         user: User = Depends(require_section("production")), db: Session = Depends(get_db)):
    _need_postgres(db)
    ctx = AnalysisContext(db, period=_period(period))
    return _ok({"period": f"{ctx.window.start_date} to {ctx.window.end_date}", "complete": ctx.window.complete, "group_by": group_by, "rows": breakdowns.production_breakdown(ctx, group_by)})


@router.get("/analytics/stoppages", summary="Stop counts, rate per 100,000 picks, duration and downtime grouped by loom, style, beam, shift, day, cause or category")
def stoppage_analytics(period: str = PeriodQ, group_by: Literal["loom", "style", "beam", "shift", "day", "cause", "category"] = "cause",
                       user: User = Depends(require_section("stoppages")), db: Session = Depends(get_db)):
    _need_postgres(db)
    ctx = AnalysisContext(db, period=_period(period))
    return _ok({"period": f"{ctx.window.start_date} to {ctx.window.end_date}", "complete": ctx.window.complete, "group_by": group_by, "rows": breakdowns.stoppage_breakdown(ctx, group_by)})


@router.get("/analytics/quality", summary="Defect rates and grades grouped by loom, style, beam, shift, day or defect type")
def quality_analytics(period: str = PeriodQ, group_by: Literal["loom", "style", "beam", "shift", "day", "defect_type"] = "style",
                      user: User = Depends(require_any_section("quality", "insights")), db: Session = Depends(get_db)):
    _need_postgres(db)
    ctx = AnalysisContext(db, period=_period(period))
    return _ok({"period": f"{ctx.window.start_date} to {ctx.window.end_date}", "complete": ctx.window.complete, "group_by": group_by, "rows": breakdowns.quality_breakdown(ctx, group_by)})


@router.get("/events/stops", response_model=StandardResponse[StopEventPage], summary="Stop events, newest first (paginated)")
def list_stop_events(
    page: int = Query(1, ge=1), page_size: int = Query(50, ge=1, le=200), loom: Optional[str] = None, category: Optional[str] = None,
    open_only: bool = False, date_from: Optional[date] = None, date_to: Optional[date] = None,
    user: User = Depends(require_section("stoppages")), db: Session = Depends(get_db),
):
    E, L, R, S, ST, B = m.WvStopEvent, m.WvLoom, m.WvStopReason, m.WvShift, m.WvStyle, m.WvBeam
    where = []
    if loom:
        where.append(L.loom_code == loom)
    if category:
        where.append(R.category == category.upper())
    if open_only:
        where.append(E.ended_at.is_(None))
    if date_from:
        where.append(E.shift_date >= date_from)
    if date_to:
        where.append(E.shift_date <= date_to)
    base = select(E.id).join(L, L.id == E.loom_id).join(R, R.id == E.reason_id)
    total = db.scalar(select(func.count()).select_from(base.where(*where).subquery())) or 0
    q = (select(E, L.loom_code, R.name, R.category, R.is_planned, S.name, ST.style_code, B.beam_no)
         .join(L, L.id == E.loom_id).join(R, R.id == E.reason_id).join(S, S.id == E.shift_id).outerjoin(ST, ST.id == E.style_id).outerjoin(B, B.id == E.beam_id)
         .where(*where).order_by(E.started_at.desc()).limit(page_size).offset((page - 1) * page_size))
    items = [StopEventOut(id=e.id, loom=lc, started_at=e.started_at.isoformat(), ended_at=e.ended_at.isoformat() if e.ended_at else None,
                          duration_min=round((e.ended_at - e.started_at).total_seconds() / 60, 2) if e.ended_at else None, open=e.ended_at is None,
                          reason=rn, category=cat, planned=pl, shift=sn, style=sc, beam=bn) for e, lc, rn, cat, pl, sn, sc, bn in db.execute(q)]
    return _ok(StopEventPage(page=page, page_size=page_size, total=total, items=items))


@router.get("/inspections", response_model=StandardResponse[InspectionPage], summary="Inspected rolls, newest first (paginated)")
def list_inspections(
    page: int = Query(1, ge=1), page_size: int = Query(50, ge=1, le=200), loom: Optional[str] = None, style: Optional[str] = None, grade: Optional[str] = None,
    date_from: Optional[date] = None, date_to: Optional[date] = None,
    user: User = Depends(require_any_section("quality", "insights")), db: Session = Depends(get_db),
):
    I, L, ST, B, S, D = m.WvInspection, m.WvLoom, m.WvStyle, m.WvBeam, m.WvShift, m.WvDefectObservation
    where = []
    if loom:
        where.append(L.loom_code == loom)
    if style:
        where.append(ST.style_code == style)
    if grade:
        where.append(I.grade == grade.upper())
    if date_from:
        where.append(I.shift_date >= date_from)
    if date_to:
        where.append(I.shift_date <= date_to)
    base = select(I.id).join(L, L.id == I.loom_id).join(ST, ST.id == I.style_id)
    total = db.scalar(select(func.count()).select_from(base.where(*where).subquery())) or 0
    defects = (select(D.inspection_id, func.sum(D.defect_count).label("n"), func.sum(D.points * D.defect_count).label("pts")).group_by(D.inspection_id).subquery())
    q = (select(I, L.loom_code, ST.style_code, B.beam_no, S.name, func.coalesce(defects.c.n, 0), func.coalesce(defects.c.pts, 0))
         .join(L, L.id == I.loom_id).join(ST, ST.id == I.style_id).join(S, S.id == I.shift_id).outerjoin(B, B.id == I.beam_id).outerjoin(defects, defects.c.inspection_id == I.id)
         .where(*where).order_by(I.inspected_at.desc()).limit(page_size).offset((page - 1) * page_size))
    items = [InspectionOut(id=i.id, roll_no=i.roll_no, loom=lc, style=sc, beam=bn, shift=sn, shift_date=i.shift_date.isoformat(), inspected_at=i.inspected_at.isoformat(),
                           length_m=float(i.length_m), grade=i.grade, defects=int(n), points=int(pts)) for i, lc, sc, bn, sn, n, pts in db.execute(q)]
    return _ok(InspectionPage(page=page, page_size=page_size, total=total, items=items))


def _visible(findings: List[Finding], role: Role) -> List[Finding]:
    return [f for f in findings if role.value in f.audiences]


@router.get("/investigations/findings", response_model=StandardResponse[List[Finding]], summary="Evidence-backed findings for your role")
def findings(period: str = PeriodQ, lens_days: int = Query(14, ge=3, le=60), kind: Optional[str] = None, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _need_postgres(db)
    role = Role(user.role)
    ctx = AnalysisContext(db, period=_period(period), lens_days=lens_days)
    out = _visible(investigations.all_findings(ctx, include_maintenance=True), role)
    if kind:
        out = [f for f in out if f.kind == kind]
    return _ok(out)


@router.get("/investigations/priorities", response_model=StandardResponse[List[Finding]], summary="What should we focus on today? Ranked findings for your role")
def priorities(period: str = PeriodQ, limit: int = Query(5, ge=1, le=20), user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _need_postgres(db)
    role = Role(user.role)
    ctx = AnalysisContext(db, period=_period(period))
    return _ok(investigations.priorities_for(role.value, investigations.all_findings(ctx, include_maintenance=role == Role.MAINTENANCE), limit))


@router.get("/investigations/style/{style_code}/beam-change", summary="Did this style's warp-stop rate change after beam changes?")
def beam_change(style_code: str, period: str = PeriodQ, user: User = Depends(require_section("stoppages")), db: Session = Depends(get_db)):
    _need_postgres(db)
    ctx = AnalysisContext(db, period=_period(period))
    result = investigations.beam_change_effect(ctx, style_code)
    if result.get("note") == "Unknown style":
        raise NotFoundException(f"No style {style_code}")
    return _ok(result)


# ============================================================================ writes (people decide; the system records)

class ActionIn(BaseModel):
    issue: str = Field(min_length=3, max_length=300)
    action: str = Field(min_length=3, max_length=1000)
    owner_role: Optional[str] = None
    owner_name: Optional[str] = Field(None, max_length=80)
    due_date: Optional[date] = None
    finding_key: Optional[str] = Field(None, max_length=160)
    expected_impact_lakhs: float = Field(0, ge=0, le=100000)


class ActionPatch(BaseModel):
    status: Optional[Literal["OPEN", "IN_PROGRESS", "COMPLETED", "CANCELLED"]] = None
    outcome_note: Optional[str] = Field(None, max_length=1000)
    verified_cause: Optional[str] = Field(None, max_length=500)
    owner_name: Optional[str] = Field(None, max_length=80)
    due_date: Optional[date] = None


def _action(db: Session, ref: str) -> m.WvAction:
    a = db.scalar(select(m.WvAction).where(m.WvAction.action_ref == ref))
    if a is None:
        raise NotFoundException(f"No action {ref}")
    return a


@router.post("/actions", summary="Record an action. Anyone can raise one; the manager or owner approves those that need approval.")
def create_action(body: ActionIn, user: User = Depends(require_section("actions")), db: Session = Depends(get_db)):
    role = Role(user.role)
    if body.owner_role and body.owner_role not in {r.value for r in Role}:
        raise ValidationException("Unknown owner role")
    now = datetime.now(timezone.utc)
    a = m.WvAction(action_ref=f"A-{uuid.uuid4().hex[:6].upper()}", finding_key=body.finding_key, issue=body.issue.strip(), action=body.action.strip(), owner_role=body.owner_role, owner_name=body.owner_name,
                   due_date=body.due_date, status="OPEN", expected_impact_lakhs=body.expected_impact_lakhs if role in FINANCIAL_ROLES else 0, created_by_user_id=user.id,
                   requires_approval=role not in FINANCIAL_ROLES, approved_by_user_id=user.id if role in FINANCIAL_ROLES else None, approved_at=now if role in FINANCIAL_ROLES else None, data_origin="LIVE")
    db.add(a)
    db.commit()
    return _ok({"ref": a.action_ref, "status": a.status, "requires_approval": a.requires_approval})


@router.patch("/actions/{ref}", summary="Update an action's status or record its outcome")
def update_action(ref: str, body: ActionPatch, user: User = Depends(require_section("actions")), db: Session = Depends(get_db)):
    role = Role(user.role)
    a = _action(db, ref)
    if body.verified_cause is not None and role not in (*FINANCIAL_ROLES, Role.QUALITY):
        raise ForbiddenException("Only the owner, weaving manager or quality controller can record a verified cause")
    if body.status is not None:
        a.status = body.status
        a.completed_at = datetime.now(timezone.utc) if body.status == "COMPLETED" else None
    if body.outcome_note is not None:
        a.outcome_note = body.outcome_note
    if body.verified_cause is not None:
        if a.status != "COMPLETED":
            raise ValidationException("A cause can be marked verified only on a completed action")
        a.verified_cause = body.verified_cause.strip() or None
    if body.owner_name is not None:
        a.owner_name = body.owner_name
    if body.due_date is not None:
        a.due_date = body.due_date
    db.commit()
    return _ok({"ref": a.action_ref, "status": a.status})


@router.post("/actions/{ref}/approve", summary="Approve an action that needs approval (owner or weaving manager)")
def approve_action(ref: str, user: User = Depends(require_section("actions")), db: Session = Depends(get_db)):
    if Role(user.role) not in FINANCIAL_ROLES:
        raise ForbiddenException("Only the owner or weaving manager can approve")
    a = _action(db, ref)
    a.approved_by_user_id, a.approved_at = user.id, datetime.now(timezone.utc)
    db.commit()
    return _ok({"ref": a.action_ref, "approved": True})


class NoteIn(BaseModel):
    body: str = Field(min_length=3, max_length=1000)
    loom: Optional[str] = None
    category: Literal["HANDOVER", "ISSUE", "MAINTENANCE_REQUEST", "QUALITY"] = "HANDOVER"
    severity: Literal["INFO", "WARNING", "URGENT"] = "INFO"


@router.post("/notes", summary="Write a shift note (hand-over, issue, maintenance request)")
def create_note(body: NoteIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _need_postgres(db)
    ctx = AnalysisContext(db)
    day, shift = ctx.cal.shift_at(ctx.now)
    loom_id = None
    if body.loom:
        loom_id = db.scalar(select(m.WvLoom.id).where(m.WvLoom.loom_code == body.loom))
        if loom_id is None:
            raise ValidationException(f"Unknown loom {body.loom}")
    n = m.WvShiftNote(note_ref=f"N-{uuid.uuid4().hex[:10]}", shift_date=day, shift_id=shift.id, loom_id=loom_id, category=body.category, severity=body.severity, body=body.body.strip(),
                      author_name=user.full_name, created_by_user_id=user.id, data_origin="LIVE")
    db.add(n)
    db.commit()
    return _ok({"id": n.id, "shift": shift.name})


@router.post("/notes/{note_id}/resolve", summary="Mark a note as resolved")
def resolve_note(note_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    n = db.get(m.WvShiftNote, note_id)
    if n is None:
        raise NotFoundException("No such note")
    n.resolved_at = datetime.now(timezone.utc)
    db.commit()
    return _ok({"id": n.id, "resolved": True})


class DecisionIn(BaseModel):
    decision: Literal["APPROVE", "REJECT"]
    signature: str = Field(min_length=8, max_length=64, description="the signature of the plan you reviewed; refused if the plan has since changed")
    note: Optional[str] = Field(None, max_length=500)


@router.post("/scheduler/decision", summary="Approve or reject the proposed schedule (owner or weaving manager). Approval records the plan and raises actions; it moves no loom by itself.")
def scheduler_decision(body: DecisionIn, user: User = Depends(require_section("scheduler")), db: Session = Depends(get_db)):
    if Role(user.role) not in FINANCIAL_ROLES:
        raise ForbiddenException("Only the owner or weaving manager can approve or reject a schedule")
    from fastapi.encoders import jsonable_encoder
    mill = _mill(db, user, "TODAY")
    plan = commercial.scheduler_page(mill)
    if plan["signature"] != body.signature:
        raise ValidationException("The plan has changed since you reviewed it. Reload the page and review it again.")
    now = datetime.now(timezone.utc)
    ref = f"PLAN-{now:%Y%m%d-%H%M}-{uuid.uuid4().hex[:4].upper()}"
    stored = {k: plan[k] for k in ("signature", "generated_at", "horizon_days", "objective", "assumptions", "baseline", "proposed", "orders", "moves", "summary")}
    p = m.WvSchedulePlan(plan_ref=ref, status="APPROVED" if body.decision == "APPROVE" else "REJECTED", objective=plan["objective"][:200], horizon_days=plan["horizon_days"], summary=jsonable_encoder(stored),
                         created_by_user_id=user.id, decided_at=now, decided_by_user_id=user.id, decision_note=body.note, data_origin="LIVE")
    db.add(p)
    created = 0
    if body.decision == "APPROVE":
        seen = set()
        for mv in plan["moves"]:
            key = (mv["loom"], mv["to_order"])
            if key in seen:
                continue
            seen.add(key)
            db.add(m.WvAction(action_ref=f"A-{uuid.uuid4().hex[:6].upper()}", finding_key=f"schedule:{ref}", issue=f"Move {mv['loom']} to {mv['to_order']}", action=mv["reason"], owner_role="SHIFT_SUPERVISOR",
                              due_date=date.fromisoformat(mv["date"]), status="OPEN", requires_approval=False, approved_by_user_id=user.id, approved_at=now, created_by_user_id=user.id, data_origin="LIVE"))
            created += 1
    db.commit()
    return _ok({"plan_ref": ref, "status": p.status, "actions_created": created})
