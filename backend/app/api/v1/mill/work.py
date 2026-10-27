"""Groups, people, loom and member assignments (dated), tasks and maintenance work orders."""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.api.v1.mill.common import Page, PageSize, ok, paginate
from app.core.exceptions import NotFoundException, ValidationException
from app.db.session import get_db
from app.mill import audit
from app.mill import constants as C
from app.mill.alerts.notify import notify_users
from app.mill.models import Alert, AlertEvent, Group, GroupLoomAssignment, GroupMemberAssignment, Loom, Person, Task, TaskEvent, WorkOrder
from app.mill.seed import bootstrap_groups
from app.models.user import User

router = APIRouter(tags=["Groups, tasks and maintenance"])


def utcnow():
    return datetime.now(timezone.utc)


# ------------------------------------------------------------------ people


class PersonIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    role: str
    employee_code: Optional[str] = Field(None, max_length=40)
    phone: Optional[str] = Field(None, max_length=30)
    is_active: bool = True


def _person(p: Person) -> dict:
    return {k: getattr(p, k) for k in ("id", "name", "role", "employee_code", "phone", "is_active")}


@router.get("/people")
def people(db: Session = Depends(get_db)):
    return ok([_person(p) for p in db.scalars(select(Person).order_by(Person.name))])


@router.post("/people")
def add_person(body: PersonIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if body.role not in C.PERSON_ROLES:
        raise ValidationException("Unknown role")
    p = Person(**body.model_dump())
    db.add(p)
    db.flush()
    audit.record(db, user.id, "PERSON_CREATE", "person", p.id, after=_person(p))
    db.commit()
    return ok(_person(p))


@router.put("/people/{person_id}")
def edit_person(person_id: int, body: PersonIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    p = db.get(Person, person_id)
    if p is None:
        raise NotFoundException("Person not found")
    if body.role not in C.PERSON_ROLES:
        raise ValidationException("Unknown role")
    before = _person(p)
    for k, v in body.model_dump().items():
        setattr(p, k, v)
    audit.record(db, user.id, "PERSON_UPDATE", "person", p.id, before, _person(p))
    db.commit()
    return ok(_person(p))


# ------------------------------------------------------------------ groups


class GroupIn(BaseModel):
    code: str = Field(min_length=1, max_length=20)
    name: str = Field(min_length=1, max_length=120)
    leader_id: Optional[int] = None
    responsibilities: Optional[str] = None
    shift_coverage: Optional[str] = Field(None, max_length=20)
    is_active: bool = True


def _current(on: Optional[date] = None):
    on = on or date.today()
    return and_(GroupLoomAssignment.valid_from <= on, or_(GroupLoomAssignment.valid_to.is_(None), GroupLoomAssignment.valid_to > on))


def _group(db: Session, g: Group, full: bool = False) -> dict:
    looms = list(db.execute(select(Loom).join(GroupLoomAssignment, GroupLoomAssignment.loom_id == Loom.id)
                            .where(GroupLoomAssignment.group_id == g.id, _current()).order_by(Loom.category, Loom.loom_no)).scalars())
    today = date.today()
    members = list(db.execute(select(GroupMemberAssignment, Person).join(Person).where(
        GroupMemberAssignment.group_id == g.id, GroupMemberAssignment.valid_from <= today,
        or_(GroupMemberAssignment.valid_to.is_(None), GroupMemberAssignment.valid_to > today))))
    out = {"id": g.id, "code": g.code, "name": g.name, "leader": _person(g.leader) if g.leader else None, "leader_id": g.leader_id,
           "responsibilities": g.responsibilities, "shift_coverage": g.shift_coverage, "is_active": g.is_active,
           "looms": [{"id": l.id, "code": l.code, "category": l.category} for l in looms],
           "members": [{**_person(p), "shift": m.shift, "assignment_id": m.id, "valid_from": m.valid_from} for m, p in members]}
    if full:
        out["loom_history"] = [{"loom": l.code, "valid_from": a.valid_from, "valid_to": a.valid_to} for a, l in db.execute(
            select(GroupLoomAssignment, Loom).join(Loom).where(GroupLoomAssignment.group_id == g.id).order_by(GroupLoomAssignment.valid_from.desc()))]
    return out


@router.get("/groups")
def groups(db: Session = Depends(get_db)):
    return ok([_group(db, g) for g in db.scalars(select(Group).order_by(Group.code))])


@router.get("/groups/{group_id}")
def group(group_id: int, db: Session = Depends(get_db)):
    g = db.get(Group, group_id)
    if g is None:
        raise NotFoundException("Group not found")
    data = _group(db, g, full=True)
    tasks = list(db.scalars(select(Task).where(Task.group_id == g.id).order_by(Task.created_at.desc()).limit(200)))
    data["tasks"] = [_task(t, db) for t in tasks]
    data["alerts"] = [{"id": a.id, "title": a.title, "severity": a.severity, "status": a.status, "period": a.period_label}
                      for a in db.scalars(select(Alert).where(or_(Alert.group_id == g.id, Alert.assigned_group_id == g.id), Alert.status != "RESOLVED"))]
    return ok(data)


@router.post("/groups/bootstrap")
def bootstrap(count: int = Query(11, ge=1, le=50), db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    made = bootstrap_groups(db, count)
    if not made:
        raise ValidationException("Groups already exist")
    audit.record(db, user.id, "GROUPS_BOOTSTRAP", "group", None, after={"count": len(made)})
    db.commit()
    return ok([_group(db, g) for g in made])


@router.post("/groups")
def add_group(body: GroupIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if db.scalar(select(Group.id).where(Group.code == body.code)):
        raise ValidationException("A group with this code exists")
    g = Group(**body.model_dump())
    db.add(g)
    db.flush()
    audit.record(db, user.id, "GROUP_CREATE", "group", g.id, after=body.model_dump())
    db.commit()
    return ok(_group(db, g))


@router.put("/groups/{group_id}")
def edit_group(group_id: int, body: GroupIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    g = db.get(Group, group_id)
    if g is None:
        raise NotFoundException("Group not found")
    if body.leader_id and db.get(Person, body.leader_id) is None:
        raise ValidationException("Unknown leader")
    fields = tuple(body.model_dump())
    before = audit.snapshot(g, fields)
    for k, v in body.model_dump().items():
        setattr(g, k, v)
    audit.record(db, user.id, "GROUP_UPDATE", "group", g.id, before, audit.snapshot(g, fields))
    db.commit()
    return ok(_group(db, g))


class LoomAssignIn(BaseModel):
    loom_ids: List[int] = Field(min_length=1)
    effective_from: date


@router.post("/groups/{group_id}/looms")
def assign_looms(group_id: int, body: LoomAssignIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """Move looms into this group from `effective_from`. Their previous assignment ends that day, so history stays right."""
    g = db.get(Group, group_id)
    if g is None:
        raise NotFoundException("Group not found")
    for lid in body.loom_ids:
        loom = db.get(Loom, lid)
        if loom is None:
            raise ValidationException(f"Unknown loom {lid}")
        open_ = db.scalar(select(GroupLoomAssignment).where(GroupLoomAssignment.loom_id == lid, GroupLoomAssignment.valid_to.is_(None)))
        if open_ is not None:
            if open_.group_id == group_id:
                continue
            if open_.valid_from >= body.effective_from:
                raise ValidationException(f"{loom.code} was assigned on {open_.valid_from}; the new date must be later")
            open_.valid_to = body.effective_from
        db.add(GroupLoomAssignment(group_id=group_id, loom_id=lid, valid_from=body.effective_from))
        audit.record(db, user.id, "LOOM_ASSIGN", "loom", loom.code, {"group_id": open_.group_id if open_ else None},
                     {"group_id": group_id, "effective_from": body.effective_from.isoformat()})
    db.commit()
    return ok(_group(db, g))


@router.post("/groups/{group_id}/looms/{loom_id}/release")
def release_loom(group_id: int, loom_id: int, effective_from: date, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    a = db.scalar(select(GroupLoomAssignment).where(GroupLoomAssignment.loom_id == loom_id, GroupLoomAssignment.group_id == group_id,
                                                    GroupLoomAssignment.valid_to.is_(None)))
    if a is None:
        raise NotFoundException("The loom is not currently in this group")
    if effective_from <= a.valid_from:
        raise ValidationException("The release date must be after the assignment date")
    a.valid_to = effective_from
    audit.record(db, user.id, "LOOM_RELEASE", "loom", loom_id, {"group_id": group_id}, {"group_id": None, "effective_from": effective_from.isoformat()})
    db.commit()
    return ok(True)


class MemberIn(BaseModel):
    person_id: int
    shift: Optional[str] = None
    effective_from: date


@router.post("/groups/{group_id}/members")
def add_member(group_id: int, body: MemberIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if db.get(Group, group_id) is None or db.get(Person, body.person_id) is None:
        raise NotFoundException("Group or person not found")
    if body.shift and body.shift not in C.SHIFTS:
        raise ValidationException("Shift must be A, B or C")
    for m in db.scalars(select(GroupMemberAssignment).where(GroupMemberAssignment.person_id == body.person_id, GroupMemberAssignment.valid_to.is_(None))):
        if m.valid_from >= body.effective_from:
            raise ValidationException("The person has a later assignment already")
        m.valid_to = body.effective_from
    db.add(GroupMemberAssignment(group_id=group_id, person_id=body.person_id, shift=body.shift, valid_from=body.effective_from))
    audit.record(db, user.id, "MEMBER_ASSIGN", "person", body.person_id, after={"group_id": group_id, "shift": body.shift,
                                                                                 "effective_from": body.effective_from.isoformat()})
    db.commit()
    return ok(_group(db, db.get(Group, group_id)))


@router.post("/groups/{group_id}/members/{assignment_id}/end")
def end_member(group_id: int, assignment_id: int, effective_from: date, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    m = db.get(GroupMemberAssignment, assignment_id)
    if m is None or m.group_id != group_id or m.valid_to is not None:
        raise NotFoundException("Active membership not found")
    if effective_from <= m.valid_from:
        raise ValidationException("The end date must be after the start date")
    m.valid_to = effective_from
    audit.record(db, user.id, "MEMBER_END", "person", m.person_id, {"group_id": group_id}, {"group_id": None})
    db.commit()
    return ok(True)


# ------------------------------------------------------------------ tasks


class TaskIn(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: Optional[str] = None
    expected_outcome: Optional[str] = None
    group_id: Optional[int] = None
    assignee_id: Optional[int] = None
    loom_id: Optional[int] = None
    alert_id: Optional[int] = None
    priority: str = "MEDIUM"
    due_at: Optional[datetime] = None


class TaskPatch(BaseModel):
    status: Optional[str] = None
    note: Optional[str] = None
    completion_notes: Optional[str] = None
    priority: Optional[str] = None
    due_at: Optional[datetime] = None
    group_id: Optional[int] = None
    assignee_id: Optional[int] = None
    escalated_to_owner: Optional[bool] = None


def _task(t: Task, db: Session, events: bool = False) -> dict:
    loom = db.get(Loom, t.loom_id) if t.loom_id else None
    g = db.get(Group, t.group_id) if t.group_id else None
    p = db.get(Person, t.assignee_id) if t.assignee_id else None
    out = {"id": t.id, "title": t.title, "description": t.description, "expected_outcome": t.expected_outcome, "status": t.status,
           "priority": t.priority, "due_at": t.due_at, "overdue": bool(t.due_at and t.status in C.TASK_OPEN and t.due_at < utcnow()),
           "group": {"id": g.id, "name": g.name} if g else None, "assignee": {"id": p.id, "name": p.name} if p else None,
           "loom": {"id": loom.id, "code": loom.code} if loom else None, "alert_id": t.alert_id, "completion_notes": t.completion_notes,
           "escalated_to_owner": t.escalated_to_owner, "created_at": t.created_at, "updated_at": t.updated_at, "completed_at": t.completed_at}
    if events:
        out["events"] = [{"kind": e.kind, "from": e.from_status, "to": e.to_status, "note": e.note, "at": e.at}
                         for e in db.scalars(select(TaskEvent).where(TaskEvent.task_id == t.id).order_by(TaskEvent.at))]
    return out


def _validate_refs(db: Session, group_id, assignee_id, loom_id, alert_id=None):
    for model, v, name in ((Group, group_id, "group"), (Person, assignee_id, "person"), (Loom, loom_id, "loom"), (Alert, alert_id, "alert")):
        if v is not None and db.get(model, v) is None:
            raise ValidationException(f"Unknown {name}")


@router.get("/tasks")
def tasks(status: Optional[str] = None, group_id: Optional[int] = None, loom_id: Optional[int] = None, overdue: bool = False,
          page: int = Page, page_size: int = PageSize, db: Session = Depends(get_db)):
    q = select(Task)
    if status == "OPEN":
        q = q.where(Task.status.in_(C.TASK_OPEN))
    elif status:
        q = q.where(Task.status == status)
    if group_id:
        q = q.where(Task.group_id == group_id)
    if loom_id:
        q = q.where(Task.loom_id == loom_id)
    if overdue:
        q = q.where(Task.status.in_(C.TASK_OPEN), Task.due_at < utcnow())
    q = q.order_by(Task.due_at.is_(None), Task.due_at, Task.id.desc())
    return ok(paginate(db, q, page, page_size, lambda t: _task(t, db)))


@router.get("/tasks/{task_id}")
def get_task(task_id: int, db: Session = Depends(get_db)):
    t = db.get(Task, task_id)
    if t is None:
        raise NotFoundException("Task not found")
    return ok(_task(t, db, events=True))


@router.post("/tasks")
def add_task(body: TaskIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if body.priority not in C.PRIORITIES:
        raise ValidationException("Unknown priority")
    _validate_refs(db, body.group_id, body.assignee_id, body.loom_id, body.alert_id)
    data = body.model_dump()
    if body.alert_id and not body.loom_id:
        data["loom_id"] = db.get(Alert, body.alert_id).loom_id
    t = Task(**data, created_by=user.id)
    db.add(t)
    db.flush()
    db.add(TaskEvent(task_id=t.id, kind="CREATED", to_status=t.status, actor_id=user.id))
    if body.alert_id:
        db.add(AlertEvent(alert_id=body.alert_id, kind="COMMENT", note=f"Task #{t.id} created: {t.title}", actor_id=user.id))
    audit.record(db, user.id, "TASK_CREATE", "task", t.id, after=body.model_dump(mode="json"))
    if t.priority in ("HIGH", "CRITICAL"):
        notify_users(db, title=f"New {t.priority.lower()} task: {t.title}", severity="WARNING", task_id=t.id, link=f"/tasks?id={t.id}")
    db.commit()
    return ok(_task(t, db, events=True))


ALLOWED = {
    "PENDING": {"IN_PROGRESS", "BLOCKED", "COMPLETED"},
    "IN_PROGRESS": {"BLOCKED", "COMPLETED", "PENDING"},
    "BLOCKED": {"IN_PROGRESS", "PENDING", "COMPLETED"},
    "COMPLETED": {"REOPENED"},
    "REOPENED": {"IN_PROGRESS", "BLOCKED", "COMPLETED"},
}


@router.patch("/tasks/{task_id}")
def patch_task(task_id: int, body: TaskPatch, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    t = db.get(Task, task_id)
    if t is None:
        raise NotFoundException("Task not found")
    data = body.model_dump(exclude_unset=True)
    fields = ("status", "priority", "due_at", "group_id", "assignee_id", "completion_notes", "escalated_to_owner")
    before = audit.snapshot(t, fields)
    if "status" in data and data["status"] != t.status:
        new = data["status"]
        if new not in ALLOWED.get(t.status, set()):
            raise ValidationException(f"A {t.status.lower()} task cannot move to {new.lower()}")
        if new == "COMPLETED" and not (data.get("completion_notes") or t.completion_notes):
            raise ValidationException("Record what was done (completion notes) to complete a task")
        if new == "BLOCKED" and not data.get("note"):
            raise ValidationException("Say what is blocking the task")
        db.add(TaskEvent(task_id=t.id, kind="STATUS", from_status=t.status, to_status=new, note=data.get("note"), actor_id=user.id))
        t.status = new
        t.completed_at = utcnow() if new == "COMPLETED" else (None if new == "REOPENED" else t.completed_at)
    elif data.get("note"):
        db.add(TaskEvent(task_id=t.id, kind="COMMENT", note=data["note"], actor_id=user.id))
    if "priority" in data and data["priority"] not in C.PRIORITIES:
        raise ValidationException("Unknown priority")
    _validate_refs(db, data.get("group_id"), data.get("assignee_id"), None)
    for k in ("priority", "due_at", "group_id", "assignee_id", "completion_notes", "escalated_to_owner"):
        if k in data:
            setattr(t, k, data[k])
    if data.get("escalated_to_owner") and not before["escalated_to_owner"]:
        db.add(TaskEvent(task_id=t.id, kind="ESCALATED", note="Escalated to the owner", actor_id=user.id))
    audit.record(db, user.id, "TASK_UPDATE", "task", t.id, before, audit.snapshot(t, fields))
    db.commit()
    return ok(_task(t, db, events=True))


@router.get("/daily-board")
def daily_board(db: Session = Depends(get_db)):
    """Per group: open, blocked, overdue and recently completed work, open alerts and owner escalations."""
    now = utcnow()
    since = now - timedelta(days=1)
    out = []
    for g in list(db.scalars(select(Group).where(Group.is_active.is_(True)).order_by(Group.code))) + [None]:
        q = select(Task).where(Task.group_id.is_(None) if g is None else Task.group_id == g.id)
        ts = list(db.scalars(q))
        if g is None and not ts:
            continue
        alerts = list(db.scalars(select(Alert).where(Alert.status != "RESOLVED",
                                                     or_(Alert.group_id == g.id, Alert.assigned_group_id == g.id) if g else Alert.group_id.is_(None))))
        out.append({
            "group": {"id": g.id, "code": g.code, "name": g.name, "leader": g.leader.name if g and g.leader else None} if g else {"id": None, "name": "No group"},
            "open": [_task(t, db) for t in ts if t.status in C.TASK_OPEN],
            "completed_last_24h": [_task(t, db) for t in ts if t.status == "COMPLETED" and t.completed_at and t.completed_at >= since],
            "blocked": sum(1 for t in ts if t.status == "BLOCKED"),
            "overdue": sum(1 for t in ts if t.status in C.TASK_OPEN and t.due_at and t.due_at < now),
            "high_priority_open": sum(1 for t in ts if t.status in C.TASK_OPEN and t.priority in ("HIGH", "CRITICAL")),
            "escalated_to_owner": sum(1 for t in ts if t.escalated_to_owner and t.status in C.TASK_OPEN),
            "open_alerts": [{"id": a.id, "title": a.title, "severity": a.severity, "status": a.status} for a in alerts][:20],
        })
    return ok(out)


# ------------------------------------------------------------------ maintenance


class WorkOrderIn(BaseModel):
    loom_id: int
    kind: str
    title: str = Field(min_length=1, max_length=200)
    description: Optional[str] = None
    priority: str = "MEDIUM"
    assignee_id: Optional[int] = None
    alert_id: Optional[int] = None
    due_date: Optional[date] = None


class WorkOrderPatch(BaseModel):
    status: Optional[str] = None
    assignee_id: Optional[int] = None
    priority: Optional[str] = None
    due_date: Optional[date] = None
    downtime_min: Optional[float] = Field(None, ge=0, le=100000)
    cause: Optional[str] = None
    resolution: Optional[str] = None


def _wo(w: WorkOrder, db: Session) -> dict:
    loom = db.get(Loom, w.loom_id)
    p = db.get(Person, w.assignee_id) if w.assignee_id else None
    return {"id": w.id, "loom": {"id": loom.id, "code": loom.code}, "kind": w.kind, "title": w.title, "description": w.description,
            "priority": w.priority, "status": w.status, "assignee": {"id": p.id, "name": p.name} if p else None, "alert_id": w.alert_id,
            "due_date": w.due_date, "overdue": bool(w.due_date and w.status in ("OPEN", "IN_PROGRESS", "ON_HOLD") and w.due_date < date.today()),
            "reported_at": w.reported_at, "started_at": w.started_at, "completed_at": w.completed_at, "downtime_min": w.downtime_min,
            "cause": w.cause, "resolution": w.resolution}


@router.get("/work-orders")
def work_orders(status: Optional[str] = None, loom_id: Optional[int] = None, kind: Optional[str] = None,
                page: int = Page, page_size: int = PageSize, db: Session = Depends(get_db)):
    q = select(WorkOrder)
    if status == "OPEN":
        q = q.where(WorkOrder.status.in_(("OPEN", "IN_PROGRESS", "ON_HOLD")))
    elif status:
        q = q.where(WorkOrder.status == status)
    if loom_id:
        q = q.where(WorkOrder.loom_id == loom_id)
    if kind:
        q = q.where(WorkOrder.kind == kind)
    q = q.order_by(WorkOrder.reported_at.desc())
    return ok(paginate(db, q, page, page_size, lambda w: _wo(w, db)))


@router.post("/work-orders")
def add_work_order(body: WorkOrderIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if body.kind not in C.WORK_ORDER_TYPES or body.priority not in C.PRIORITIES:
        raise ValidationException("Unknown type or priority")
    _validate_refs(db, None, body.assignee_id, body.loom_id, body.alert_id)
    w = WorkOrder(**body.model_dump(), created_by=user.id)
    db.add(w)
    db.flush()
    if body.alert_id:
        db.add(AlertEvent(alert_id=body.alert_id, kind="COMMENT", note=f"Work order #{w.id} raised: {w.title}", actor_id=user.id))
    audit.record(db, user.id, "WORK_ORDER_CREATE", "work_order", w.id, after=body.model_dump(mode="json"))
    db.commit()
    return ok(_wo(w, db))


@router.patch("/work-orders/{wo_id}")
def patch_work_order(wo_id: int, body: WorkOrderPatch, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    w = db.get(WorkOrder, wo_id)
    if w is None:
        raise NotFoundException("Work order not found")
    data = body.model_dump(exclude_unset=True)
    fields = ("status", "assignee_id", "priority", "due_date", "downtime_min", "cause", "resolution")
    before = audit.snapshot(w, fields)
    if "status" in data:
        if data["status"] not in C.WORK_ORDER_STATUSES:
            raise ValidationException("Unknown status")
        if data["status"] == "COMPLETED" and not (data.get("resolution") or w.resolution):
            raise ValidationException("Record the work done (resolution) to complete a work order")
        if data["status"] == "IN_PROGRESS" and w.started_at is None:
            w.started_at = utcnow()
        if data["status"] == "COMPLETED":
            w.completed_at = utcnow()
    if "priority" in data and data["priority"] not in C.PRIORITIES:
        raise ValidationException("Unknown priority")
    _validate_refs(db, None, data.get("assignee_id"), None)
    for k, v in data.items():
        setattr(w, k, v)
    audit.record(db, user.id, "WORK_ORDER_UPDATE", "work_order", w.id, before, audit.snapshot(w, fields))
    db.commit()
    return ok(_wo(w, db))
