from datetime import datetime
from typing import Optional
from sqlalchemy import String, DateTime, Float, Integer, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.session import Base

class ReportRecord(Base):
    __tablename__ = "reports"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    file_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    report_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    confidence_score: Mapped[float] = mapped_column(Float, default=1.0)
    status: Mapped[str] = mapped_column(String(50), default="PROCESSED")  # PROCESSED, DUPLICATE, WARNING, FAILED
    report_date: Mapped[Optional[str]] = mapped_column(String(20), nullable=True, index=True)
    upload_timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    production_records = relationship("ProductionRecord", back_populates="source_report", cascade="all, delete-orphan")
    downtime_records = relationship("DowntimeRecord", back_populates="source_report", cascade="all, delete-orphan")


class ProductionRecord(Base):
    __tablename__ = "production_records"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    source_report_id: Mapped[str] = mapped_column(String(50), ForeignKey("reports.id"), nullable=False)
    report_date: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    shift: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)  # Shift I, Shift II, Shift III, or None for Daily
    department: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    unit: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    machine_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    machine_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    actual_kg: Mapped[float] = mapped_column(Float, default=0.0)
    target_kg: Mapped[float] = mapped_column(Float, default=0.0)
    gap_kg: Mapped[float] = mapped_column(Float, default=0.0)
    achievement_pct: Mapped[float] = mapped_column(Float, default=0.0)
    source_sheet: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    source_row: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    source_column: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    source_report = relationship("ReportRecord", back_populates="production_records")


class DowntimeRecord(Base):
    __tablename__ = "downtime_records"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    source_report_id: Mapped[str] = mapped_column(String(50), ForeignKey("reports.id"), nullable=False)
    report_date: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    shift: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)
    machine_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    machine_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    downtime_minutes: Mapped[Optional[float]] = mapped_column(Float, nullable=True, default=None)
    loss_kg: Mapped[float] = mapped_column(Float, default=0.0)
    reason_category: Mapped[str] = mapped_column(String(100), default="Machine Downtime")
    remarks: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    source_report = relationship("ReportRecord", back_populates="downtime_records")


class QualityRecord(Base):
    __tablename__ = "quality_records"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    source_report_id: Mapped[str] = mapped_column(String(50), ForeignKey("reports.id"), nullable=False)
    report_date: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    shift: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    yarn_count: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    quality_score: Mapped[float] = mapped_column(Float, default=100.0)
    defect_rate: Mapped[float] = mapped_column(Float, default=0.0)
    warp_breaks: Mapped[int] = mapped_column(Integer, default=0)
    weft_breaks: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class EnergyRecord(Base):
    __tablename__ = "energy_records"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    source_report_id: Mapped[str] = mapped_column(String(50), ForeignKey("reports.id"), nullable=False)
    report_date: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    shift: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    kwh_consumed: Mapped[float] = mapped_column(Float, default=0.0)
    energy_per_kg: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class ManpowerRecord(Base):
    __tablename__ = "manpower_records"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    source_report_id: Mapped[str] = mapped_column(String(50), ForeignKey("reports.id"), nullable=False)
    report_date: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    shift: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    department: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    planned_count: Mapped[int] = mapped_column(Integer, default=0)
    actual_count: Mapped[int] = mapped_column(Integer, default=0)
    gap_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
