"""
Database schema for the weaving platform.

Conventions
  * Timestamps are timezone-aware and stored in UTC; production dates (`prod_date`) are mill-local calendar days.
  * Imported file data is kept in three layers: the original file on disk (never modified), `raw_source_rows`
    (each source row as read, for investigation and re-processing) and `shift_production` (normalized,
    analytics-ready). Nothing is silently dropped: anything not imported is recorded in `import_issues`.
  * NULL means "not available in the source"; 0 means the source reported zero. The two are never conflated.
  * `data_origin` (IMPORTED / LIVE / SIMULATED) travels with every production and telemetry row.
"""
from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Optional

from sqlalchemy import (
    JSON, BigInteger, Boolean, CheckConstraint, Date, DateTime, Float, ForeignKey, Index, Integer, String, Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.mill import constants as C
import app.models.user  # noqa: F401  (several tables reference users.id)

Json = JSON().with_variant(JSONB(), "postgresql")


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _in(col: str, values) -> str:
    return f"{col} IN ({', '.join(repr(v) for v in values)})"


TS = DateTime(timezone=True)


# --------------------------------------------------------------------------- machines


class Loom(Base):
    __tablename__ = "looms"
    __table_args__ = (
        UniqueConstraint("category", "loom_no", name="category_loom_no"),
        CheckConstraint(_in("category", C.CATEGORIES), name="category"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(20), unique=True, index=True)  # TY-01
    category: Mapped[str] = mapped_column(String(4))
    loom_no: Mapped[int] = mapped_column(Integer)
    manufacturer: Mapped[str] = mapped_column(String(40))
    model: Mapped[Optional[str]] = mapped_column(String(80))       # unknown until confirmed by the mill
    width_cm: Mapped[Optional[int]] = mapped_column(Integer)       # reed width group from the mill report (190/340/360)
    notes: Mapped[Optional[str]] = mapped_column(Text)
    attributes: Mapped[dict] = mapped_column(Json, default=dict)   # source-observed facts, e.g. export section, panel factor
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(TS, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(TS, default=utcnow, onupdate=utcnow)


class Style(Base):
    """Fabric / pick configuration code as written in the reports (e.g. 4140-49), with the description when known."""
    __tablename__ = "styles"

    code: Mapped[str] = mapped_column(String(80), primary_key=True)
    description: Mapped[Optional[str]] = mapped_column(Text)
    first_seen: Mapped[Optional[date]] = mapped_column(Date)
    last_seen: Mapped[Optional[date]] = mapped_column(Date)


# --------------------------------------------------------------------------- imports


class ImportBatch(Base):
    __tablename__ = "import_batches"
    __table_args__ = (CheckConstraint(_in("status", ("PREVIEWED", "PROCESSING", "COMMITTED", "FAILED", "DUPLICATE", "DISCARDED")), name="status"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    filename: Mapped[str] = mapped_column(String(255))
    sha256: Mapped[str] = mapped_column(String(64), index=True)
    size_bytes: Mapped[int] = mapped_column(Integer)
    stored_path: Mapped[Optional[str]] = mapped_column(String(500))  # original file, kept unmodified
    source_format: Mapped[Optional[str]] = mapped_column(String(40))  # MILL_DAILY_WORKBOOK / TSUDAKOMA_SHIFT_EXPORT / TOYOTA_SHIFT_REPORT
    parser_version: Mapped[str] = mapped_column(String(20))
    status: Mapped[str] = mapped_column(String(12))
    period_start: Mapped[Optional[date]] = mapped_column(Date)
    period_end: Mapped[Optional[date]] = mapped_column(Date)
    records_parsed: Mapped[int] = mapped_column(Integer, default=0)
    records_inserted: Mapped[int] = mapped_column(Integer, default=0)
    records_updated: Mapped[int] = mapped_column(Integer, default=0)
    records_unchanged: Mapped[int] = mapped_column(Integer, default=0)
    error_count: Mapped[int] = mapped_column(Integer, default=0)
    warning_count: Mapped[int] = mapped_column(Integer, default=0)
    summary: Mapped[dict] = mapped_column(Json, default=dict)          # sheets, looms, categories, data-quality summary
    reconciliation: Mapped[list] = mapped_column(Json, default=list)  # source totals vs normalized totals
    error: Mapped[Optional[str]] = mapped_column(Text)
    uploaded_by: Mapped[Optional[str]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    created_at: Mapped[datetime] = mapped_column(TS, default=utcnow)
    committed_at: Mapped[Optional[datetime]] = mapped_column(TS)


class ImportIssue(Base):
    __tablename__ = "import_issues"
    __table_args__ = (CheckConstraint(_in("severity", ("ERROR", "WARNING", "INFO")), name="severity"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    batch_id: Mapped[int] = mapped_column(ForeignKey("import_batches.id", ondelete="CASCADE"), index=True)
    severity: Mapped[str] = mapped_column(String(8))
    code: Mapped[str] = mapped_column(String(40))
    message: Mapped[str] = mapped_column(Text)
    sheet: Mapped[Optional[str]] = mapped_column(String(80))
    row: Mapped[Optional[int]] = mapped_column(Integer)      # 1-based, as Excel shows it
    column: Mapped[Optional[str]] = mapped_column(String(80))
    raw_value: Mapped[Optional[str]] = mapped_column(Text)


class RawSourceRow(Base):
    """One source row exactly as read (cell values), so discrepancies can be investigated and data re-processed."""
    __tablename__ = "raw_source_rows"
    __table_args__ = (UniqueConstraint("batch_id", "sheet", "row", name="batch_sheet_row"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    batch_id: Mapped[int] = mapped_column(ForeignKey("import_batches.id", ondelete="CASCADE"), index=True)
    sheet: Mapped[str] = mapped_column(String(80))
    row: Mapped[int] = mapped_column(Integer)
    cells: Mapped[list] = mapped_column(Json)


# --------------------------------------------------------------------------- production


class ShiftProduction(Base):
    """One loom, one shift, one source. Analytics pick one source per loom-shift (see analytics/records.py)."""
    __tablename__ = "shift_production"
    __table_args__ = (
        UniqueConstraint("loom_id", "prod_date", "shift", "source_kind", name="loom_date_shift_source"),
        CheckConstraint(_in("shift", C.SHIFTS), name="shift"),
        CheckConstraint(_in("source_kind", C.SOURCE_KINDS), name="source_kind"),
        CheckConstraint(_in("data_origin", C.ORIGINS), name="data_origin"),
        CheckConstraint("efficiency_pct IS NULL OR (efficiency_pct >= 0 AND efficiency_pct <= 100)", name="efficiency_range"),
        Index("ix_shift_production_date", "prod_date", "shift"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    loom_id: Mapped[int] = mapped_column(ForeignKey("looms.id", ondelete="CASCADE"), index=True)
    prod_date: Mapped[date] = mapped_column(Date)
    shift: Mapped[str] = mapped_column(String(1))
    source_kind: Mapped[str] = mapped_column(String(16))
    data_origin: Mapped[str] = mapped_column(String(10), default=C.ORIGIN_IMPORTED)
    style_code: Mapped[Optional[str]] = mapped_column(String(80))
    rpm: Mapped[Optional[float]] = mapped_column(Float)
    efficiency_pct: Mapped[Optional[float]] = mapped_column(Float)       # as reported by the source
    loom_efficiency_pct: Mapped[Optional[float]] = mapped_column(Float)  # Tsudakoma reports a second, "loom" efficiency
    kilopicks: Mapped[Optional[float]] = mapped_column(Float)
    meters: Mapped[Optional[float]] = mapped_column(Float)
    warp_stops: Mapped[Optional[int]] = mapped_column(Integer)
    weft_stops: Mapped[Optional[int]] = mapped_column(Integer)
    other_stops: Mapped[Optional[int]] = mapped_column(Integer)
    total_stops: Mapped[Optional[int]] = mapped_column(Integer)
    run_min: Mapped[Optional[float]] = mapped_column(Float)
    stop_min: Mapped[Optional[float]] = mapped_column(Float)
    warp_stop_min: Mapped[Optional[float]] = mapped_column(Float)
    weft_stop_min: Mapped[Optional[float]] = mapped_column(Float)
    air_nm3: Mapped[Optional[float]] = mapped_column(Float)
    operator_name: Mapped[Optional[str]] = mapped_column(String(80))
    extras: Mapped[dict] = mapped_column(Json, default=dict)  # source-specific fields (stop causes, sensor counts...)
    batch_id: Mapped[Optional[int]] = mapped_column(ForeignKey("import_batches.id", ondelete="SET NULL"), index=True)
    raw_row_id: Mapped[Optional[int]] = mapped_column(ForeignKey("raw_source_rows.id", ondelete="SET NULL"))
    created_at: Mapped[datetime] = mapped_column(TS, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(TS, default=utcnow, onupdate=utcnow)

    loom: Mapped[Loom] = relationship()


class ProductionTarget(Base):
    """A configured target. Scope is the whole mill, a category, a group or one loom; the most specific one applies."""
    __tablename__ = "production_targets"
    __table_args__ = (
        CheckConstraint(_in("scope", ("MILL", "CATEGORY", "GROUP", "LOOM")), name="scope"),
        CheckConstraint(_in("metric", ("efficiency_pct", "meters_per_shift", "kilopicks_per_shift")), name="metric"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    scope: Mapped[str] = mapped_column(String(10))
    scope_ref: Mapped[Optional[str]] = mapped_column(String(40))  # category code, group id or loom code
    metric: Mapped[str] = mapped_column(String(24))
    value: Mapped[float] = mapped_column(Float)
    effective_from: Mapped[date] = mapped_column(Date)
    effective_to: Mapped[Optional[date]] = mapped_column(Date)
    created_by: Mapped[Optional[str]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    created_at: Mapped[datetime] = mapped_column(TS, default=utcnow)


class EnergyReading(Base):
    """Electricity / compressed-air readings. Only measured or explicitly estimated values; estimates are flagged."""
    __tablename__ = "energy_readings"
    __table_args__ = (
        CheckConstraint(_in("basis", ("MEASURED", "OEM_REPORTED", "ESTIMATED")), name="basis"),
        Index("ix_energy_readings_period", "period_start"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    loom_id: Mapped[Optional[int]] = mapped_column(ForeignKey("looms.id", ondelete="CASCADE"), index=True)
    meter_ref: Mapped[Optional[str]] = mapped_column(String(80))  # e.g. a feeder or compressor meter
    period_start: Mapped[datetime] = mapped_column(TS)
    period_end: Mapped[datetime] = mapped_column(TS)
    kwh: Mapped[Optional[float]] = mapped_column(Float)
    air_nm3: Mapped[Optional[float]] = mapped_column(Float)
    pressure_bar: Mapped[Optional[float]] = mapped_column(Float)
    basis: Mapped[str] = mapped_column(String(14))
    source: Mapped[str] = mapped_column(String(120))
    assumptions: Mapped[Optional[str]] = mapped_column(Text)
    batch_id: Mapped[Optional[int]] = mapped_column(ForeignKey("import_batches.id", ondelete="SET NULL"))
    created_at: Mapped[datetime] = mapped_column(TS, default=utcnow)


# --------------------------------------------------------------------------- people and groups


class Person(Base):
    __tablename__ = "people"
    __table_args__ = (CheckConstraint(_in("role", C.PERSON_ROLES), name="role"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    role: Mapped[str] = mapped_column(String(16))
    employee_code: Mapped[Optional[str]] = mapped_column(String(40), unique=True)
    phone: Mapped[Optional[str]] = mapped_column(String(30))
    user_id: Mapped[Optional[str]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(TS, default=utcnow)


class Group(Base):
    """An operational group of looms and people led by a group leader. The mill runs 11 today; the count is not fixed."""
    __tablename__ = "groups"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(20), unique=True)
    name: Mapped[str] = mapped_column(String(120))
    leader_id: Mapped[Optional[int]] = mapped_column(ForeignKey("people.id", ondelete="SET NULL"))
    responsibilities: Mapped[Optional[str]] = mapped_column(Text)
    shift_coverage: Mapped[Optional[str]] = mapped_column(String(20))  # e.g. "A,B,C"
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(TS, default=utcnow)

    leader: Mapped[Optional[Person]] = relationship()


class GroupLoomAssignment(Base):
    """A loom belongs to a group from `valid_from` until `valid_to` (exclusive, NULL = still assigned)."""
    __tablename__ = "group_loom_assignments"
    __table_args__ = (Index("ix_group_loom_current", "loom_id", "valid_to"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id", ondelete="CASCADE"), index=True)
    loom_id: Mapped[int] = mapped_column(ForeignKey("looms.id", ondelete="CASCADE"))
    valid_from: Mapped[date] = mapped_column(Date)
    valid_to: Mapped[Optional[date]] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(TS, default=utcnow)


class GroupMemberAssignment(Base):
    __tablename__ = "group_member_assignments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id", ondelete="CASCADE"), index=True)
    person_id: Mapped[int] = mapped_column(ForeignKey("people.id", ondelete="CASCADE"), index=True)
    shift: Mapped[Optional[str]] = mapped_column(String(1))
    valid_from: Mapped[date] = mapped_column(Date)
    valid_to: Mapped[Optional[date]] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(TS, default=utcnow)


# --------------------------------------------------------------------------- alerts and notifications


class AlertRule(Base):
    __tablename__ = "alert_rules"
    __table_args__ = (
        CheckConstraint(_in("severity", C.SEVERITIES), name="severity"),
        CheckConstraint(_in("comparator", ("lt", "gt")), name="comparator"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(40), unique=True)
    name: Mapped[str] = mapped_column(String(120))
    description: Mapped[Optional[str]] = mapped_column(Text)
    metric: Mapped[str] = mapped_column(String(40))          # see alerts/rules.py METRICS
    comparator: Mapped[str] = mapped_column(String(2))
    threshold: Mapped[Optional[float]] = mapped_column(Float)  # absolute limit (or deviation for *_vs_baseline metrics)
    baseline_days: Mapped[int] = mapped_column(Integer, default=14)  # history window for *_vs_baseline / robust-z metrics
    min_baseline_points: Mapped[int] = mapped_column(Integer, default=6)
    categories: Mapped[Optional[str]] = mapped_column(String(20))  # comma list, NULL = all
    consecutive: Mapped[int] = mapped_column(Integer, default=1)  # breaches in a row before an alert opens
    cooldown_hours: Mapped[int] = mapped_column(Integer, default=24)  # no re-open within this after resolution
    escalate_after_hours: Mapped[Optional[int]] = mapped_column(Integer)
    severity: Mapped[str] = mapped_column(String(8))
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    updated_at: Mapped[datetime] = mapped_column(TS, default=utcnow, onupdate=utcnow)


class Alert(Base):
    __tablename__ = "alerts"
    __table_args__ = (
        CheckConstraint(_in("status", C.ALERT_STATUSES), name="status"),
        CheckConstraint(_in("severity", C.SEVERITIES), name="severity"),
        Index("ix_alerts_dedup_open", "dedup_key", "status"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    rule_id: Mapped[Optional[int]] = mapped_column(ForeignKey("alert_rules.id", ondelete="SET NULL"))
    rule_code: Mapped[str] = mapped_column(String(40))
    dedup_key: Mapped[str] = mapped_column(String(120))
    loom_id: Mapped[Optional[int]] = mapped_column(ForeignKey("looms.id", ondelete="CASCADE"), index=True)
    group_id: Mapped[Optional[int]] = mapped_column(ForeignKey("groups.id", ondelete="SET NULL"))
    title: Mapped[str] = mapped_column(String(200))
    metric: Mapped[str] = mapped_column(String(40))
    observed: Mapped[Optional[float]] = mapped_column(Float)
    threshold: Mapped[Optional[float]] = mapped_column(Float)
    baseline: Mapped[Optional[float]] = mapped_column(Float)
    period_label: Mapped[Optional[str]] = mapped_column(String(40))  # e.g. 2026-09-14 B
    source: Mapped[str] = mapped_column(String(40))  # MILL_REPORT / MACHINE_EXPORT / TELEMETRY / SYSTEM
    data_origin: Mapped[str] = mapped_column(String(10), default=C.ORIGIN_IMPORTED)
    evidence: Mapped[dict] = mapped_column(Json, default=dict)
    severity: Mapped[str] = mapped_column(String(8))
    status: Mapped[str] = mapped_column(String(12), default="OPEN")
    occurrences: Mapped[int] = mapped_column(Integer, default=1)
    first_seen_at: Mapped[datetime] = mapped_column(TS, default=utcnow)
    last_seen_at: Mapped[datetime] = mapped_column(TS, default=utcnow)
    condition_cleared_at: Mapped[Optional[datetime]] = mapped_column(TS)
    escalation_level: Mapped[int] = mapped_column(Integer, default=0)
    assigned_group_id: Mapped[Optional[int]] = mapped_column(ForeignKey("groups.id", ondelete="SET NULL"))
    assigned_person_id: Mapped[Optional[int]] = mapped_column(ForeignKey("people.id", ondelete="SET NULL"))
    acknowledged_by: Mapped[Optional[str]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    acknowledged_at: Mapped[Optional[datetime]] = mapped_column(TS)
    resolved_by: Mapped[Optional[str]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    resolved_at: Mapped[Optional[datetime]] = mapped_column(TS)
    resolution_notes: Mapped[Optional[str]] = mapped_column(Text)

    loom: Mapped[Optional[Loom]] = relationship()


class AlertEvent(Base):
    __tablename__ = "alert_events"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    alert_id: Mapped[int] = mapped_column(ForeignKey("alerts.id", ondelete="CASCADE"), index=True)
    kind: Mapped[str] = mapped_column(String(20))  # OPENED / REPEATED / ACKNOWLEDGED / ESCALATED / CLEARED / RESOLVED / ASSIGNED / REOPENED
    note: Mapped[Optional[str]] = mapped_column(Text)
    actor_id: Mapped[Optional[str]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    at: Mapped[datetime] = mapped_column(TS, default=utcnow)


class Notification(Base):
    """One message to one user on one channel, with its delivery state. In-app is the only configured channel."""
    __tablename__ = "notifications"
    __table_args__ = (
        CheckConstraint(_in("delivery_status", ("DELIVERED", "PENDING", "FAILED", "NOT_CONFIGURED")), name="delivery_status"),
        Index("ix_notifications_user_unread", "user_id", "read_at"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    channel: Mapped[str] = mapped_column(String(12), default="IN_APP")
    title: Mapped[str] = mapped_column(String(200))
    body: Mapped[Optional[str]] = mapped_column(Text)
    severity: Mapped[str] = mapped_column(String(8), default="INFO")
    alert_id: Mapped[Optional[int]] = mapped_column(ForeignKey("alerts.id", ondelete="CASCADE"))
    task_id: Mapped[Optional[int]] = mapped_column(ForeignKey("tasks.id", ondelete="CASCADE"))
    link: Mapped[Optional[str]] = mapped_column(String(200))
    delivery_status: Mapped[str] = mapped_column(String(16), default="DELIVERED")
    attempts: Mapped[int] = mapped_column(Integer, default=1)
    last_error: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(TS, default=utcnow)
    read_at: Mapped[Optional[datetime]] = mapped_column(TS)


# --------------------------------------------------------------------------- work


class Task(Base):
    __tablename__ = "tasks"
    __table_args__ = (
        CheckConstraint(_in("status", C.TASK_STATUSES), name="status"),
        CheckConstraint(_in("priority", C.PRIORITIES), name="priority"),
        Index("ix_tasks_group_status", "group_id", "status"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[Optional[str]] = mapped_column(Text)
    expected_outcome: Mapped[Optional[str]] = mapped_column(Text)
    group_id: Mapped[Optional[int]] = mapped_column(ForeignKey("groups.id", ondelete="SET NULL"))
    assignee_id: Mapped[Optional[int]] = mapped_column(ForeignKey("people.id", ondelete="SET NULL"))
    loom_id: Mapped[Optional[int]] = mapped_column(ForeignKey("looms.id", ondelete="SET NULL"))
    alert_id: Mapped[Optional[int]] = mapped_column(ForeignKey("alerts.id", ondelete="SET NULL"))
    priority: Mapped[str] = mapped_column(String(8), default="MEDIUM")
    status: Mapped[str] = mapped_column(String(12), default="PENDING")
    due_at: Mapped[Optional[datetime]] = mapped_column(TS)
    completion_notes: Mapped[Optional[str]] = mapped_column(Text)
    escalated_to_owner: Mapped[bool] = mapped_column(Boolean, default=False)
    created_by: Mapped[Optional[str]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    created_at: Mapped[datetime] = mapped_column(TS, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(TS, default=utcnow, onupdate=utcnow)
    completed_at: Mapped[Optional[datetime]] = mapped_column(TS)


class TaskEvent(Base):
    __tablename__ = "task_events"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id", ondelete="CASCADE"), index=True)
    kind: Mapped[str] = mapped_column(String(20))  # CREATED / STATUS / COMMENT / ASSIGNED / ESCALATED
    from_status: Mapped[Optional[str]] = mapped_column(String(12))
    to_status: Mapped[Optional[str]] = mapped_column(String(12))
    note: Mapped[Optional[str]] = mapped_column(Text)
    actor_id: Mapped[Optional[str]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    at: Mapped[datetime] = mapped_column(TS, default=utcnow)


class WorkOrder(Base):
    __tablename__ = "work_orders"
    __table_args__ = (
        CheckConstraint(_in("kind", C.WORK_ORDER_TYPES), name="kind"),
        CheckConstraint(_in("status", C.WORK_ORDER_STATUSES), name="status"),
        CheckConstraint(_in("priority", C.PRIORITIES), name="priority"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    loom_id: Mapped[int] = mapped_column(ForeignKey("looms.id", ondelete="CASCADE"), index=True)
    kind: Mapped[str] = mapped_column(String(12))
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[Optional[str]] = mapped_column(Text)
    priority: Mapped[str] = mapped_column(String(8), default="MEDIUM")
    status: Mapped[str] = mapped_column(String(12), default="OPEN")
    assignee_id: Mapped[Optional[int]] = mapped_column(ForeignKey("people.id", ondelete="SET NULL"))
    alert_id: Mapped[Optional[int]] = mapped_column(ForeignKey("alerts.id", ondelete="SET NULL"))
    due_date: Mapped[Optional[date]] = mapped_column(Date)  # planned date for preventive work
    reported_at: Mapped[datetime] = mapped_column(TS, default=utcnow)
    started_at: Mapped[Optional[datetime]] = mapped_column(TS)
    completed_at: Mapped[Optional[datetime]] = mapped_column(TS)
    downtime_min: Mapped[Optional[float]] = mapped_column(Float)  # entered by maintenance; never inferred
    cause: Mapped[Optional[str]] = mapped_column(Text)            # confirmed cause, entered after the work
    resolution: Mapped[Optional[str]] = mapped_column(Text)
    created_by: Mapped[Optional[str]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    created_at: Mapped[datetime] = mapped_column(TS, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(TS, default=utcnow, onupdate=utcnow)


class OwnerReport(Base):
    """GM-to-owner report. Numbers are frozen in `snapshot` at publication and never recomputed afterwards."""
    __tablename__ = "owner_reports"
    __table_args__ = (CheckConstraint(_in("status", C.REPORT_STATUSES), name="status"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    period_start: Mapped[date] = mapped_column(Date)
    period_end: Mapped[date] = mapped_column(Date)
    shift: Mapped[Optional[str]] = mapped_column(String(1))  # a shift-level report, or NULL for the whole day(s)
    status: Mapped[str] = mapped_column(String(12), default="DRAFT")
    snapshot: Mapped[dict] = mapped_column(Json, default=dict)
    commentary: Mapped[Optional[str]] = mapped_column(Text)
    decisions_needed: Mapped[Optional[str]] = mapped_column(Text)
    risks: Mapped[Optional[str]] = mapped_column(Text)
    generated_at: Mapped[datetime] = mapped_column(TS, default=utcnow)
    created_by: Mapped[Optional[str]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    published_at: Mapped[Optional[datetime]] = mapped_column(TS)
    published_by: Mapped[Optional[str]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    acknowledged_at: Mapped[Optional[datetime]] = mapped_column(TS)
    acknowledged_by: Mapped[Optional[str]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    owner_comment: Mapped[Optional[str]] = mapped_column(Text)


# --------------------------------------------------------------------------- connectivity


class MachineConnection(Base):
    """How (and whether) a loom's live data can be read. Credentials are never stored here, only the name of the
    environment variable that holds them."""
    __tablename__ = "machine_connections"
    __table_args__ = (
        CheckConstraint(_in("adapter", C.ADAPTERS), name="adapter"),
        CheckConstraint(_in("state", C.CONNECTION_STATES), name="state"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    loom_id: Mapped[int] = mapped_column(ForeignKey("looms.id", ondelete="CASCADE"), unique=True)
    adapter: Mapped[str] = mapped_column(String(16), default="NONE")
    host: Mapped[Optional[str]] = mapped_column(String(120))
    port: Mapped[Optional[int]] = mapped_column(Integer)
    credentials_env: Mapped[Optional[str]] = mapped_column(String(80))
    poll_seconds: Mapped[int] = mapped_column(Integer, default=60)
    enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    state: Mapped[str] = mapped_column(String(22), default="NOT_CONFIGURED")
    last_attempt_at: Mapped[Optional[datetime]] = mapped_column(TS)
    last_success_at: Mapped[Optional[datetime]] = mapped_column(TS)
    consecutive_failures: Mapped[int] = mapped_column(Integer, default=0)
    next_attempt_at: Mapped[Optional[datetime]] = mapped_column(TS)
    last_error: Mapped[Optional[str]] = mapped_column(Text)
    notes: Mapped[Optional[str]] = mapped_column(Text)
    updated_at: Mapped[datetime] = mapped_column(TS, default=utcnow, onupdate=utcnow)


class TelemetrySample(Base):
    """A reading from an adapter. High volume: keep a retention window (TELEMETRY_RETENTION_DAYS)."""
    __tablename__ = "telemetry_samples"
    __table_args__ = (
        CheckConstraint(_in("data_origin", (C.ORIGIN_LIVE, C.ORIGIN_SIMULATED)), name="data_origin"),
        CheckConstraint(_in("state", ("RUNNING", "STOPPED", "UNKNOWN")), name="state"),
        Index("ix_telemetry_loom_ts", "loom_id", "sampled_at"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    loom_id: Mapped[int] = mapped_column(ForeignKey("looms.id", ondelete="CASCADE"))
    sampled_at: Mapped[datetime] = mapped_column(TS)    # machine/adapter timestamp
    received_at: Mapped[datetime] = mapped_column(TS, default=utcnow)
    data_origin: Mapped[str] = mapped_column(String(10))
    state: Mapped[str] = mapped_column(String(8))
    rpm: Mapped[Optional[float]] = mapped_column(Float)
    efficiency_pct: Mapped[Optional[float]] = mapped_column(Float)
    picks_counter: Mapped[Optional[float]] = mapped_column(Float)
    stop_code: Mapped[Optional[str]] = mapped_column(String(40))
    warp_stops: Mapped[Optional[int]] = mapped_column(Integer)
    weft_stops: Mapped[Optional[int]] = mapped_column(Integer)
    air_nm3: Mapped[Optional[float]] = mapped_column(Float)
    values: Mapped[dict] = mapped_column(Json, default=dict)


# --------------------------------------------------------------------------- audit


class AuditLog(Base):
    __tablename__ = "audit_log"
    __table_args__ = (Index("ix_audit_entity", "entity", "entity_id"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    actor_id: Mapped[Optional[str]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    action: Mapped[str] = mapped_column(String(40))
    entity: Mapped[str] = mapped_column(String(40))
    entity_id: Mapped[Optional[str]] = mapped_column(String(40))
    before: Mapped[Optional[dict]] = mapped_column(Json)
    after: Mapped[Optional[dict]] = mapped_column(Json)
    at: Mapped[datetime] = mapped_column(TS, default=utcnow, index=True)
