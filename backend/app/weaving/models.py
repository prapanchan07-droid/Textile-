"""
Weaving intelligence schema.

Shape: a few master tables (looms, styles, beams, orders, operators, shifts), and four fact
tables the analytics read from: loom readings, stop events, inspections (+ defect observations)
and maintenance events. Fact rows carry the style, beam, shift and weaver that applied *when
they happened*, so questions like "did this style get worse after a beam change?" are plain
GROUP BYs and not interval joins.

Conventions
  * Table prefix ``wv_``. Business identifiers (loom_code, style_code, beam_no, order_no,
    roll_no, employee_code) are unique and are what seed data and imports key on.
  * Timestamps are timezone-aware (UTC in the database). ``shift_date`` is the mill's
    *production day* of the shift (a night shift that starts at 22:00 belongs to the day it
    started), so overnight shifts never split across days.
  * Enumerations are VARCHAR + CHECK, which migrate more easily than native enums.
  * ``data_origin`` marks whether a row is DEMO, IMPORTED or LIVE, so demonstration data can
    never be mistaken for the mill's own records.
"""
from __future__ import annotations

from datetime import date, datetime, time
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    JSON, BigInteger, Boolean, CheckConstraint, Date, DateTime, ForeignKey, Index, Integer, Numeric, String, Text, Time,
    UniqueConstraint, func, text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base

ORIGINS = ("DEMO", "IMPORTED", "LIVE")


def _in(column: str, values) -> str:
    return f"{column} IN ({', '.join(repr(v) for v in values)})"


def origin_col() -> Mapped[str]:
    return mapped_column(String(10), nullable=False, default="LIVE", server_default="LIVE")


def origin_check() -> CheckConstraint:
    return CheckConstraint(_in("data_origin", ORIGINS), name="data_origin")


TS = DateTime(timezone=True)

# --------------------------------------------------------------------------- reference / master data

SHIFT_CODES = ("I", "II", "III")


class WvShift(Base):
    __tablename__ = "wv_shifts"
    __table_args__ = (CheckConstraint("start_time <> end_time", name="distinct_times"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(10), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(40), nullable=False)
    start_time: Mapped[time] = mapped_column(Time, nullable=False)  # mill-local
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    crosses_midnight: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class WvLoom(Base):
    __tablename__ = "wv_looms"
    __table_args__ = (
        CheckConstraint("rated_rpm > 0", name="rated_rpm_positive"),
        CheckConstraint("reed_space_cm IS NULL OR reed_space_cm > 0", name="reed_space_positive"),
        origin_check(),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    loom_code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    loom_type: Mapped[str] = mapped_column(String(30), nullable=False)  # Airjet | Sulzer | ...
    make: Mapped[Optional[str]] = mapped_column(String(60))
    model: Mapped[Optional[str]] = mapped_column(String(60))
    reed_space_cm: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 1))
    rated_rpm: Mapped[int] = mapped_column(Integer, nullable=False)  # design speed, picks per minute
    installed_on: Mapped[Optional[date]] = mapped_column(Date)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    # machine details
    serial_no: Mapped[Optional[str]] = mapped_column(String(40))
    year_of_make: Mapped[Optional[int]] = mapped_column(Integer)
    shedding: Mapped[Optional[str]] = mapped_column(String(20))  # Cam | Dobby | Jacquard
    colours: Mapped[Optional[int]] = mapped_column(Integer)  # weft colours the loom can insert
    power_kw_rated: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 1))
    bay: Mapped[Optional[str]] = mapped_column(String(30))  # physical location, e.g. "Unit I · Bay A"
    last_overhaul_on: Mapped[Optional[date]] = mapped_column(Date)
    warranty_until: Mapped[Optional[date]] = mapped_column(Date)
    data_origin: Mapped[str] = origin_col()


class WvStyle(Base):
    __tablename__ = "wv_styles"
    __table_args__ = (
        CheckConstraint("ppi > 0", name="ppi_positive"),
        CheckConstraint("target_efficiency_pct > 0 AND target_efficiency_pct <= 100", name="target_eff_range"),
        CheckConstraint("rate_per_m >= 0 AND std_cost_per_m >= 0 AND variable_cost_per_m >= 0", name="money_non_negative"),
        origin_check(),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    style_code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    fabric_name: Mapped[str] = mapped_column(String(80), nullable=False)
    weave: Mapped[Optional[str]] = mapped_column(String(30))
    warp_count: Mapped[Optional[str]] = mapped_column(String(20))
    weft_count: Mapped[Optional[str]] = mapped_column(String(20))
    epi: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 1))  # ends per inch
    ppi: Mapped[Decimal] = mapped_column(Numeric(6, 1), nullable=False)  # picks per inch
    width_in: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 1))
    target_efficiency_pct: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False, default=Decimal("92.00"))
    # Planning parameters used only to put a rupee value on lost metres; not accounting data.
    rate_per_m: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=0)
    std_cost_per_m: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=0)
    variable_cost_per_m: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=0)
    # when set, only this loom type can weave the style (e.g. heavy canvas needs projectile looms)
    loom_type_required: Mapped[Optional[str]] = mapped_column(String(30))
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    data_origin: Mapped[str] = origin_col()


class WvYarnLot(Base):
    """A received lot of warp yarn with its incoming test results. Beams point at it by lot number (WvBeam.yarn_lot)."""

    __tablename__ = "wv_yarn_lots"
    __table_args__ = (origin_check(),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    lot_no: Mapped[str] = mapped_column(String(40), unique=True, nullable=False)
    yarn_count: Mapped[Optional[str]] = mapped_column(String(20))
    supplier: Mapped[Optional[str]] = mapped_column(String(80))
    received_on: Mapped[Optional[date]] = mapped_column(Date)
    strength_cn_tex: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))  # single-yarn tenacity
    elongation_pct: Mapped[Optional[Decimal]] = mapped_column(Numeric(4, 1))
    cv_pct: Mapped[Optional[Decimal]] = mapped_column(Numeric(4, 1))  # count variation
    data_origin: Mapped[str] = origin_col()


class WvBeam(Base):
    __tablename__ = "wv_beams"
    __table_args__ = (
        CheckConstraint("total_ends > 0", name="ends_positive"),
        CheckConstraint("length_m > 0", name="length_positive"),
        CheckConstraint(_in("status", ("READY", "MOUNTED", "FINISHED")), name="status"),
        origin_check(),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    beam_no: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    style_id: Mapped[int] = mapped_column(ForeignKey("wv_styles.id"), nullable=False, index=True)
    total_ends: Mapped[int] = mapped_column(Integer, nullable=False)
    length_m: Mapped[Decimal] = mapped_column(Numeric(10, 1), nullable=False)
    yarn_lot: Mapped[Optional[str]] = mapped_column(String(40), index=True)
    sized_on: Mapped[Optional[date]] = mapped_column(Date)
    size_pickup_pct: Mapped[Optional[Decimal]] = mapped_column(Numeric(4, 1))  # size add-on from the sizing machine
    status: Mapped[str] = mapped_column(String(12), nullable=False, default="READY")
    data_origin: Mapped[str] = origin_col()

    style = relationship("WvStyle")


class WvBeamMounting(Base):
    """A beam sitting on a loom. At most one open mounting per loom."""

    __tablename__ = "wv_beam_mountings"
    __table_args__ = (
        UniqueConstraint("loom_id", "mounted_at", name="uq_wv_beam_mountings_loom_mounted"),
        CheckConstraint("removed_at IS NULL OR removed_at > mounted_at", name="order"),
        Index("uq_wv_beam_mountings_open_loom", "loom_id", unique=True, postgresql_where=text("removed_at IS NULL"), sqlite_where=text("removed_at IS NULL")),
        Index("ix_wv_beam_mountings_loom_time", "loom_id", "mounted_at"),
        origin_check(),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    beam_id: Mapped[int] = mapped_column(ForeignKey("wv_beams.id"), nullable=False, index=True)
    loom_id: Mapped[int] = mapped_column(ForeignKey("wv_looms.id"), nullable=False)
    mounted_at: Mapped[datetime] = mapped_column(TS, nullable=False)
    removed_at: Mapped[Optional[datetime]] = mapped_column(TS)
    data_origin: Mapped[str] = origin_col()


class WvCustomer(Base):
    __tablename__ = "wv_customers"
    __table_args__ = (CheckConstraint(_in("tier", ("A", "B", "C")), name="tier"), origin_check())

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    segment: Mapped[Optional[str]] = mapped_column(String(30))  # Garment | Export | Trader | Uniform | Home textile
    city: Mapped[Optional[str]] = mapped_column(String(60))
    tier: Mapped[str] = mapped_column(String(1), nullable=False, default="B")  # A = strategic
    data_origin: Mapped[str] = origin_col()


class WvProductionOrder(Base):
    __tablename__ = "wv_production_orders"
    __table_args__ = (
        CheckConstraint("ordered_m > 0", name="qty_positive"),
        CheckConstraint(_in("priority", ("A", "B", "C")), name="priority"),
        CheckConstraint(_in("status", ("PLANNED", "RUNNING", "COMPLETED", "CANCELLED")), name="status"),
        origin_check(),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    order_no: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    style_id: Mapped[int] = mapped_column(ForeignKey("wv_styles.id"), nullable=False, index=True)
    customer: Mapped[Optional[str]] = mapped_column(String(120))
    customer_id: Mapped[Optional[int]] = mapped_column(ForeignKey("wv_customers.id"), index=True)
    priority: Mapped[str] = mapped_column(String(1), nullable=False, default="B", server_default="B")  # A = most urgent
    rate_per_m: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2))
    ordered_m: Mapped[Decimal] = mapped_column(Numeric(12, 1), nullable=False)
    start_date: Mapped[Optional[date]] = mapped_column(Date)
    due_date: Mapped[Optional[date]] = mapped_column(Date, index=True)
    status: Mapped[str] = mapped_column(String(12), nullable=False, default="PLANNED")
    data_origin: Mapped[str] = origin_col()


class WvOrderAssignment(Base):
    """A loom working on an order for a period. At most one open assignment per loom."""

    __tablename__ = "wv_order_assignments"
    __table_args__ = (
        UniqueConstraint("loom_id", "assigned_from", name="uq_wv_order_assignments_loom_from"),
        CheckConstraint("assigned_to IS NULL OR assigned_to > assigned_from", name="order"),
        Index("uq_wv_order_assignments_open_loom", "loom_id", unique=True, postgresql_where=text("assigned_to IS NULL"), sqlite_where=text("assigned_to IS NULL")),
        origin_check(),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("wv_production_orders.id"), nullable=False, index=True)
    loom_id: Mapped[int] = mapped_column(ForeignKey("wv_looms.id"), nullable=False, index=True)
    assigned_from: Mapped[datetime] = mapped_column(TS, nullable=False)
    assigned_to: Mapped[Optional[datetime]] = mapped_column(TS)
    data_origin: Mapped[str] = origin_col()


OPERATOR_ROLES = ("WEAVER", "FITTER", "INSPECTOR", "TECHNICIAN", "SUPERVISOR")


class WvOperator(Base):
    __tablename__ = "wv_operators"
    __table_args__ = (CheckConstraint(_in("operator_role", OPERATOR_ROLES), name="role"), origin_check())

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    employee_code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    full_name: Mapped[Optional[str]] = mapped_column(String(120))
    operator_role: Mapped[str] = mapped_column(String(12), nullable=False)
    grade: Mapped[Optional[str]] = mapped_column(String(6))
    home_shift_id: Mapped[Optional[int]] = mapped_column(ForeignKey("wv_shifts.id"))
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    # employee details (no pay data on purpose)
    designation: Mapped[Optional[str]] = mapped_column(String(40))
    department: Mapped[Optional[str]] = mapped_column(String(30))
    contract_type: Mapped[Optional[str]] = mapped_column(String(12))  # PERMANENT | CONTRACT
    joined_on: Mapped[Optional[date]] = mapped_column(Date)
    experience_years: Mapped[Optional[Decimal]] = mapped_column(Numeric(4, 1))
    skills: Mapped[Optional[str]] = mapped_column(String(80))  # comma separated loom types / skills
    phone: Mapped[Optional[str]] = mapped_column(String(20))
    data_origin: Mapped[str] = origin_col()


class WvShiftAssignment(Base):
    __tablename__ = "wv_shift_assignments"
    __table_args__ = (
        UniqueConstraint("shift_date", "shift_id", "loom_id", "assignment_role", name="uq_wv_shift_assignments_slot"),
        CheckConstraint(_in("assignment_role", ("WEAVER", "FITTER")), name="role"),
        origin_check(),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    shift_date: Mapped[date] = mapped_column(Date, nullable=False)
    shift_id: Mapped[int] = mapped_column(ForeignKey("wv_shifts.id"), nullable=False)
    loom_id: Mapped[int] = mapped_column(ForeignKey("wv_looms.id"), nullable=False)
    operator_id: Mapped[int] = mapped_column(ForeignKey("wv_operators.id"), nullable=False, index=True)
    assignment_role: Mapped[str] = mapped_column(String(10), nullable=False)
    data_origin: Mapped[str] = origin_col()


class WvAttendance(Base):
    __tablename__ = "wv_attendance"
    __table_args__ = (
        UniqueConstraint("shift_date", "shift_id", "operator_id", name="uq_wv_attendance_slot"),
        CheckConstraint(_in("status", ("PRESENT", "ABSENT", "LEAVE")), name="status"),
        origin_check(),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    shift_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    shift_id: Mapped[int] = mapped_column(ForeignKey("wv_shifts.id"), nullable=False)
    operator_id: Mapped[int] = mapped_column(ForeignKey("wv_operators.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(8), nullable=False)
    data_origin: Mapped[str] = origin_col()


# --------------------------------------------------------------------------- facts

QUALITY_FLAGS = ("OK", "PARTIAL", "NO_PICKS")


class WvLoomReading(Base):
    """One loom, one interval (normally an hour): how long it ran and how many picks it inserted."""

    __tablename__ = "wv_loom_readings"
    __table_args__ = (
        UniqueConstraint("loom_id", "reading_start", name="uq_wv_loom_readings_loom_start"),
        CheckConstraint("reading_end > reading_start", name="interval_order"),
        CheckConstraint("duration_seconds > 0", name="duration_positive"),
        CheckConstraint("running_seconds >= 0 AND running_seconds <= duration_seconds", name="running_within_interval"),
        CheckConstraint("picks IS NULL OR picks >= 0", name="picks_non_negative"),
        CheckConstraint(_in("quality_flag", QUALITY_FLAGS), name="quality_flag"),
        Index("ix_wv_loom_readings_date_loom", "shift_date", "loom_id"),
        Index("ix_wv_loom_readings_date_style", "shift_date", "style_id"),
        Index("ix_wv_loom_readings_date_shift", "shift_date", "shift_id"),
        Index("ix_wv_loom_readings_beam", "beam_id"),
        origin_check(),
    )

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    loom_id: Mapped[int] = mapped_column(ForeignKey("wv_looms.id"), nullable=False)
    reading_start: Mapped[datetime] = mapped_column(TS, nullable=False)
    reading_end: Mapped[datetime] = mapped_column(TS, nullable=False)
    duration_seconds: Mapped[int] = mapped_column(Integer, nullable=False)
    shift_id: Mapped[int] = mapped_column(ForeignKey("wv_shifts.id"), nullable=False)
    shift_date: Mapped[date] = mapped_column(Date, nullable=False)
    style_id: Mapped[Optional[int]] = mapped_column(ForeignKey("wv_styles.id"))
    beam_id: Mapped[Optional[int]] = mapped_column(ForeignKey("wv_beams.id"))
    order_id: Mapped[Optional[int]] = mapped_column(ForeignKey("wv_production_orders.id"))
    weaver_id: Mapped[Optional[int]] = mapped_column(ForeignKey("wv_operators.id"))
    running_seconds: Mapped[int] = mapped_column(Integer, nullable=False)
    picks: Mapped[Optional[int]] = mapped_column(BigInteger)  # NULL = counter missing; excluded, not counted as zero
    # optional machine sensors; NULL when the loom has none or the sensor was offline in the interval
    power_kw: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 2))  # average electrical draw
    vibration_mm_s: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))  # RMS velocity
    motor_temp_c: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 1))
    air_pressure_bar: Mapped[Optional[Decimal]] = mapped_column(Numeric(4, 2))  # main-nozzle pressure (airjet)
    quality_flag: Mapped[str] = mapped_column(String(10), nullable=False, default="OK", server_default="OK")
    data_origin: Mapped[str] = origin_col()


STOP_CATEGORIES = (
    "WARP", "WEFT", "MECHANICAL", "ELECTRICAL", "BEAM", "STYLE", "WAITING", "YARN", "PLANNED_MAINTENANCE", "OTHER",
)


class WvStopReason(Base):
    __tablename__ = "wv_stop_reasons"
    __table_args__ = (CheckConstraint(_in("category", STOP_CATEGORIES), name="category"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(60), nullable=False)
    category: Mapped[str] = mapped_column(String(20), nullable=False)
    is_planned: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    # Counted in "stops per 100,000 picks". Planned stops (beam change, style change, PM) are not.
    counts_toward_stop_rate: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    diagnostic_hint: Mapped[Optional[str]] = mapped_column(Text)


class WvStopEvent(Base):
    """A period when a loom was stopped. ``ended_at`` is NULL while the loom is still stopped."""

    __tablename__ = "wv_stop_events"
    __table_args__ = (
        UniqueConstraint("loom_id", "started_at", name="uq_wv_stop_events_loom_start"),
        CheckConstraint("ended_at IS NULL OR ended_at >= started_at", name="interval_order"),
        Index("ix_wv_stop_events_date_loom", "shift_date", "loom_id"),
        Index("ix_wv_stop_events_reason_date", "reason_id", "shift_date"),
        Index("ix_wv_stop_events_style_date", "style_id", "shift_date"),
        Index("ix_wv_stop_events_beam", "beam_id"),
        Index("ix_wv_stop_events_started_at", "started_at"),
        Index("ix_wv_stop_events_open", "loom_id", postgresql_where=text("ended_at IS NULL"), sqlite_where=text("ended_at IS NULL")),
        origin_check(),
    )

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    loom_id: Mapped[int] = mapped_column(ForeignKey("wv_looms.id"), nullable=False)
    started_at: Mapped[datetime] = mapped_column(TS, nullable=False)
    ended_at: Mapped[Optional[datetime]] = mapped_column(TS)
    reason_id: Mapped[int] = mapped_column(ForeignKey("wv_stop_reasons.id"), nullable=False)
    shift_id: Mapped[int] = mapped_column(ForeignKey("wv_shifts.id"), nullable=False)  # shift in which it started
    shift_date: Mapped[date] = mapped_column(Date, nullable=False)
    style_id: Mapped[Optional[int]] = mapped_column(ForeignKey("wv_styles.id"))
    beam_id: Mapped[Optional[int]] = mapped_column(ForeignKey("wv_beams.id"))
    weaver_id: Mapped[Optional[int]] = mapped_column(ForeignKey("wv_operators.id"))
    fitter_id: Mapped[Optional[int]] = mapped_column(ForeignKey("wv_operators.id"))
    note: Mapped[Optional[str]] = mapped_column(Text)
    data_origin: Mapped[str] = origin_col()

    reason = relationship("WvStopReason")


class WvDefectType(Base):
    __tablename__ = "wv_defect_types"
    __table_args__ = (CheckConstraint(_in("category", ("WEAVING", "YARN", "PROCESS", "OTHER")), name="category"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(60), nullable=False)
    category: Mapped[str] = mapped_column(String(10), nullable=False, default="WEAVING")


GRADES = ("A", "B", "C", "REJECT")


class WvInspection(Base):
    """One inspected roll (piece) of fabric."""

    __tablename__ = "wv_inspections"
    __table_args__ = (
        CheckConstraint("length_m > 0", name="length_positive"),
        CheckConstraint(_in("grade", GRADES), name="grade"),
        Index("ix_wv_inspections_date_loom", "shift_date", "loom_id"),
        Index("ix_wv_inspections_date_style", "shift_date", "style_id"),
        Index("ix_wv_inspections_date_shift", "shift_date", "shift_id"),
        Index("ix_wv_inspections_beam", "beam_id"),
        origin_check(),
    )

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    roll_no: Mapped[str] = mapped_column(String(40), unique=True, nullable=False)
    loom_id: Mapped[int] = mapped_column(ForeignKey("wv_looms.id"), nullable=False)
    style_id: Mapped[int] = mapped_column(ForeignKey("wv_styles.id"), nullable=False)
    beam_id: Mapped[Optional[int]] = mapped_column(ForeignKey("wv_beams.id"))
    shift_id: Mapped[int] = mapped_column(ForeignKey("wv_shifts.id"), nullable=False)  # shift the roll was doffed in
    shift_date: Mapped[date] = mapped_column(Date, nullable=False)
    inspected_at: Mapped[datetime] = mapped_column(TS, nullable=False)
    inspector_id: Mapped[Optional[int]] = mapped_column(ForeignKey("wv_operators.id"))
    length_m: Mapped[Decimal] = mapped_column(Numeric(8, 2), nullable=False)
    grade: Mapped[str] = mapped_column(String(8), nullable=False)
    data_origin: Mapped[str] = origin_col()

    defects = relationship("WvDefectObservation", back_populates="inspection", cascade="all, delete-orphan")


class WvDefectObservation(Base):
    __tablename__ = "wv_defect_observations"
    __table_args__ = (
        CheckConstraint(_in("severity", ("MINOR", "MAJOR", "CRITICAL")), name="severity"),
        CheckConstraint("points BETWEEN 1 AND 4", name="points_range"),  # 4-point inspection system
        CheckConstraint("defect_count > 0", name="count_positive"),
        Index("ix_wv_defect_observations_inspection", "inspection_id"),
        Index("ix_wv_defect_observations_type", "defect_type_id"),
    )

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    inspection_id: Mapped[int] = mapped_column(ForeignKey("wv_inspections.id", ondelete="CASCADE"), nullable=False)
    defect_type_id: Mapped[int] = mapped_column(ForeignKey("wv_defect_types.id"), nullable=False)
    severity: Mapped[str] = mapped_column(String(10), nullable=False)
    points: Mapped[int] = mapped_column(Integer, nullable=False)
    defect_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    position_m: Mapped[Optional[Decimal]] = mapped_column(Numeric(8, 2))

    inspection = relationship("WvInspection", back_populates="defects")


class WvMaintenanceEvent(Base):
    __tablename__ = "wv_maintenance_events"
    __table_args__ = (
        CheckConstraint(_in("event_type", ("PREVENTIVE", "BREAKDOWN", "INSPECTION")), name="event_type"),
        CheckConstraint(_in("status", ("PLANNED", "IN_PROGRESS", "COMPLETED", "CANCELLED")), name="status"),
        CheckConstraint("completed_at IS NULL OR started_at IS NULL OR completed_at >= started_at", name="interval_order"),
        Index("ix_wv_maintenance_events_loom_status", "loom_id", "status"),
        Index("ix_wv_maintenance_events_planned", "planned_for"),
        origin_check(),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    event_ref: Mapped[str] = mapped_column(String(60), unique=True, nullable=False)  # stable business id, e.g. PM-AJ-14-2026-10-12
    loom_id: Mapped[int] = mapped_column(ForeignKey("wv_looms.id"), nullable=False)
    event_type: Mapped[str] = mapped_column(String(12), nullable=False)
    task: Mapped[str] = mapped_column(String(120), nullable=False)
    planned_for: Mapped[Optional[date]] = mapped_column(Date)
    started_at: Mapped[Optional[datetime]] = mapped_column(TS)
    completed_at: Mapped[Optional[datetime]] = mapped_column(TS)
    status: Mapped[str] = mapped_column(String(12), nullable=False, default="PLANNED")
    technician_id: Mapped[Optional[int]] = mapped_column(ForeignKey("wv_operators.id"))
    stop_event_id: Mapped[Optional[int]] = mapped_column(ForeignKey("wv_stop_events.id"))  # the breakdown this repaired
    notes: Mapped[Optional[str]] = mapped_column(Text)
    data_origin: Mapped[str] = origin_col()


# --------------------------------------------------------------------------- follow-up (recommendation loop)

ACTION_STATUSES = ("OPEN", "IN_PROGRESS", "COMPLETED", "CANCELLED")


class WvAction(Base):
    """
    A corrective action a person has taken on. ``finding_key`` links it to the analytics finding
    that prompted it (see analytics/findings.py), and the outcome columns record what happened
    afterwards, which is what lets the platform measure whether a recommendation actually worked.
    """

    __tablename__ = "wv_actions"
    __table_args__ = (
        CheckConstraint(_in("status", ACTION_STATUSES), name="status"),
        Index("ix_wv_actions_status_due", "status", "due_date"),
        origin_check(),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    action_ref: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    finding_key: Mapped[Optional[str]] = mapped_column(String(160), index=True)
    issue: Mapped[str] = mapped_column(Text, nullable=False)
    action: Mapped[str] = mapped_column(Text, nullable=False)
    owner_role: Mapped[Optional[str]] = mapped_column(String(30))
    owner_name: Mapped[Optional[str]] = mapped_column(String(80))
    due_date: Mapped[Optional[date]] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(12), nullable=False, default="OPEN")
    expected_impact_lakhs: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=0)
    requires_approval: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    approved_by_user_id: Mapped[Optional[str]] = mapped_column(ForeignKey("users.id"))
    approved_at: Mapped[Optional[datetime]] = mapped_column(TS)
    created_by_user_id: Mapped[Optional[str]] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(TS, nullable=False, server_default=func.now())
    completed_at: Mapped[Optional[datetime]] = mapped_column(TS)
    outcome_note: Mapped[Optional[str]] = mapped_column(Text)
    # Set by a person when the outcome confirmed (or ruled out) a hypothesis. The only place a cause becomes "verified".
    verified_cause: Mapped[Optional[str]] = mapped_column(Text)
    outcome_measured_lakhs: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2))
    data_origin: Mapped[str] = origin_col()


class WvShiftNote(Base):
    """Shift hand-over notes and floor issues written by supervisors."""

    __tablename__ = "wv_shift_notes"
    __table_args__ = (
        CheckConstraint(_in("category", ("HANDOVER", "ISSUE", "MAINTENANCE_REQUEST", "QUALITY")), name="category"),
        CheckConstraint(_in("severity", ("INFO", "WARNING", "URGENT")), name="severity"),
        Index("ix_wv_shift_notes_date_shift", "shift_date", "shift_id"),
        origin_check(),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    note_ref: Mapped[str] = mapped_column(String(40), unique=True, nullable=False)
    shift_date: Mapped[date] = mapped_column(Date, nullable=False)
    shift_id: Mapped[int] = mapped_column(ForeignKey("wv_shifts.id"), nullable=False)
    loom_id: Mapped[Optional[int]] = mapped_column(ForeignKey("wv_looms.id"))
    category: Mapped[str] = mapped_column(String(20), nullable=False, default="HANDOVER")
    severity: Mapped[str] = mapped_column(String(8), nullable=False, default="INFO")
    body: Mapped[str] = mapped_column(Text, nullable=False)
    author_name: Mapped[Optional[str]] = mapped_column(String(80))
    created_by_user_id: Mapped[Optional[str]] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(TS, nullable=False, server_default=func.now())
    resolved_at: Mapped[Optional[datetime]] = mapped_column(TS)
    data_origin: Mapped[str] = origin_col()


class WvSchedulePlan(Base):
    """An AI-proposed loom schedule. It changes nothing until a manager approves it."""

    __tablename__ = "wv_schedule_plans"
    __table_args__ = (CheckConstraint(_in("status", ("PROPOSED", "APPROVED", "REJECTED")), name="status"), origin_check())

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    plan_ref: Mapped[str] = mapped_column(String(40), unique=True, nullable=False)
    status: Mapped[str] = mapped_column(String(10), nullable=False, default="PROPOSED")
    objective: Mapped[str] = mapped_column(String(200), nullable=False)
    horizon_days: Mapped[int] = mapped_column(Integer, nullable=False)
    summary: Mapped[dict] = mapped_column(JSON, nullable=False)  # the plan as proposed: assignments, predicted completion, trade-offs
    created_at: Mapped[datetime] = mapped_column(TS, nullable=False, server_default=func.now())
    created_by_user_id: Mapped[Optional[str]] = mapped_column(ForeignKey("users.id"))
    decided_at: Mapped[Optional[datetime]] = mapped_column(TS)
    decided_by_user_id: Mapped[Optional[str]] = mapped_column(ForeignKey("users.id"))
    decision_note: Mapped[Optional[str]] = mapped_column(Text)
    data_origin: Mapped[str] = origin_col()
