from datetime import datetime
from typing import Optional
from sqlalchemy import String, DateTime, Float, Integer, Text, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from app.db.session import Base


class MachineDailyRecord(Base):
    """One row per machine per shift (or per day) imported from the data template."""
    __tablename__ = "machine_daily_records"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    source_report_id: Mapped[str] = mapped_column(String(50), ForeignKey("reports.id"), nullable=False, index=True)
    report_date: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    unit: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    section: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    shift: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    machine_type: Mapped[str] = mapped_column(String(100), nullable=False)
    machine_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    target_kg: Mapped[float] = mapped_column(Float, default=0.0)
    actual_kg: Mapped[float] = mapped_column(Float, default=0.0)
    downtime_min: Mapped[float] = mapped_column(Float, default=0.0)
    downtime_reason: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    is_planned_downtime: Mapped[bool] = mapped_column(Boolean, default=False)
    stoppage_count: Mapped[int] = mapped_column(Integer, default=0)
    power_events: Mapped[int] = mapped_column(Integer, default=0)
    energy_kwh: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    quality_rating_pct: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    main_issue: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    last_maintenance: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    next_maintenance: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class QualityParameterRecord(Base):
    __tablename__ = "quality_parameter_records"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    source_report_id: Mapped[str] = mapped_column(String(50), ForeignKey("reports.id"), nullable=False, index=True)
    report_date: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    machine_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    parameter: Mapped[str] = mapped_column(String(100), nullable=False)
    value: Mapped[float] = mapped_column(Float, nullable=False)
    limit_value: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str] = mapped_column(String(30), default="")


class BusinessDailyRecord(Base):
    __tablename__ = "business_daily_records"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    source_report_id: Mapped[str] = mapped_column(String(50), ForeignKey("reports.id"), nullable=False, index=True)
    report_date: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    revenue_lakhs: Mapped[float] = mapped_column(Float, default=0.0)
    orders_meters: Mapped[float] = mapped_column(Float, default=0.0)
    dispatched_meters: Mapped[float] = mapped_column(Float, default=0.0)
    collected_lakhs: Mapped[float] = mapped_column(Float, default=0.0)
    outstanding_lakhs: Mapped[float] = mapped_column(Float, default=0.0)


class StockRecord(Base):
    __tablename__ = "stock_records"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    source_report_id: Mapped[str] = mapped_column(String(50), ForeignKey("reports.id"), nullable=False, index=True)
    report_date: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    current_value_lakhs: Mapped[float] = mapped_column(Float, default=0.0)
    limit_value_lakhs: Mapped[float] = mapped_column(Float, default=0.0)


class ActionItemRecord(Base):
    __tablename__ = "action_item_records"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    source_report_id: Mapped[str] = mapped_column(String(50), ForeignKey("reports.id"), nullable=False, index=True)
    report_date: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    issue: Mapped[str] = mapped_column(String(255), nullable=False)
    action: Mapped[str] = mapped_column(Text, nullable=False)
    owner: Mapped[str] = mapped_column(String(100), default="")
    status: Mapped[str] = mapped_column(String(30), default="OPEN")  # OPEN | IN_PROGRESS | COMPLETED
