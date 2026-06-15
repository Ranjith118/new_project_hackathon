"""SQLAlchemy database models for Maintenance Wizard."""
import uuid
from datetime import datetime, date
from typing import Optional

from sqlalchemy import String, Text, Integer, Float, Date, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.database import Base


class Equipment(Base):
    """Equipment model for tracking industrial equipment."""
    __tablename__ = "equipment"

    equipment_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    equipment_name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    equipment_type: Mapped[str] = mapped_column(String(100), nullable=False)
    manufacturer: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    installation_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="operational")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())


class MaintenanceLog(Base):
    """Maintenance log model for tracking maintenance activities."""
    __tablename__ = "maintenance_logs"

    log_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    equipment_name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    issue: Mapped[str] = mapped_column(Text, nullable=False)
    action_taken: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    downtime_hours: Mapped[float] = mapped_column(Float, default=0.0)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)  # low, medium, high, critical
    technician: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    maintenance_date: Mapped[date] = mapped_column(Date, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class SensorData(Base):
    """Sensor data model for storing equipment sensor readings."""
    __tablename__ = "sensor_data"

    sensor_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    equipment_name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    # Core sensors
    temperature: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    vibration: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    current: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    pressure: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    rpm: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    # Extended sensors
    voltage: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    flow_rate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    humidity: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    power_consumption: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    lubrication_level: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    bearing_temperature: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class FailureReport(Base):
    """Failure report model for tracking equipment failures."""
    __tablename__ = "failure_reports"

    report_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    equipment_name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    failure_type: Mapped[str] = mapped_column(String(100), nullable=False)
    root_cause: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    downtime_hours: Mapped[float] = mapped_column(Float, default=0.0)
    report_date: Mapped[date] = mapped_column(Date, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class SparePart(Base):
    """Spare parts model for inventory management."""
    __tablename__ = "spare_parts"

    part_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    part_name: Mapped[str] = mapped_column(String(200), nullable=False)
    stock_quantity: Mapped[int] = mapped_column(Integer, default=0)
    lead_time_days: Mapped[int] = mapped_column(Integer, default=0)
    supplier: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class UploadedFile(Base):
    """Uploaded files metadata model."""
    __tablename__ = "uploaded_files"

    file_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    filename: Mapped[str] = mapped_column(String(500), nullable=False)
    file_type: Mapped[str] = mapped_column(String(50), nullable=False)
    file_category: Mapped[str] = mapped_column(String(50), nullable=False)  # manual, sop, log, report, sensor, spares, incident
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    file_path: Mapped[str] = mapped_column(String(1000), nullable=False)
    equipment_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    uploaded_by: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class IntelligentDocument(Base):
    """AI-analyzed document with full metadata."""
    __tablename__ = "intelligent_documents"

    doc_id: Mapped[str] = mapped_column(String(36), primary_key=True,
                                         default=lambda: str(uuid.uuid4()))
    file_name: Mapped[str]          = mapped_column(String(300), nullable=False)
    file_path: Mapped[str]          = mapped_column(String(500), nullable=False)
    file_type: Mapped[str]          = mapped_column(String(10), nullable=False)
    file_size: Mapped[int]          = mapped_column(Integer, default=0)

    # AI-classified fields
    document_type: Mapped[Optional[str]]   = mapped_column(String(100), nullable=True)
    type_confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    equipment_name: Mapped[Optional[str]]  = mapped_column(String(200), nullable=True)
    equipment_type: Mapped[Optional[str]]  = mapped_column(String(100), nullable=True)
    manufacturer: Mapped[Optional[str]]    = mapped_column(String(200), nullable=True)
    model_number: Mapped[Optional[str]]    = mapped_column(String(100), nullable=True)
    keywords: Mapped[Optional[str]]        = mapped_column(Text, nullable=True)  # JSON

    # AI summaries
    executive_summary: Mapped[Optional[str]]  = mapped_column(Text, nullable=True)
    technical_summary: Mapped[Optional[str]]  = mapped_column(Text, nullable=True)
    maintenance_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Processing
    processing_status: Mapped[str] = mapped_column(String(30), default="uploaded")
    processing_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    chunk_count: Mapped[int]        = mapped_column(Integer, default=0)
    page_count: Mapped[int]         = mapped_column(Integer, default=0)

    upload_date: Mapped[datetime]   = mapped_column(DateTime, server_default=func.now())
    processed_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)


class DocumentKnowledge(Base):
    """Structured knowledge extracted from a document by AI."""
    __tablename__ = "document_knowledge"

    knowledge_id: Mapped[str] = mapped_column(String(36), primary_key=True,
                                               default=lambda: str(uuid.uuid4()))
    doc_id: Mapped[str]        = mapped_column(String(36), nullable=False, index=True)
    equipment_name: Mapped[str] = mapped_column(String(200), nullable=False)

    # All stored as JSON strings
    operating_conditions: Mapped[Optional[str]]       = mapped_column(Text, nullable=True)
    fault_modes: Mapped[Optional[str]]                = mapped_column(Text, nullable=True)
    maintenance_tasks: Mapped[Optional[str]]          = mapped_column(Text, nullable=True)
    safety_instructions: Mapped[Optional[str]]        = mapped_column(Text, nullable=True)
    spare_parts: Mapped[Optional[str]]                = mapped_column(Text, nullable=True)
    sensor_thresholds: Mapped[Optional[str]]          = mapped_column(Text, nullable=True)
    maintenance_intervals: Mapped[Optional[str]]      = mapped_column(Text, nullable=True)
    critical_components: Mapped[Optional[str]]        = mapped_column(Text, nullable=True)
    inspection_checklist: Mapped[Optional[str]]       = mapped_column(Text, nullable=True)
    troubleshooting_procedures: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class DelayLog(Base):
    """Equipment delay/downtime log."""
    __tablename__ = "delay_logs"

    delay_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    delay_code: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    equipment_name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    delay_start: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    delay_end: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    delay_duration_min: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    delay_category: Mapped[str] = mapped_column(String(100), nullable=False)  # mechanical, electrical, process, planned, external
    production_impact: Mapped[str] = mapped_column(String(50), default="low")  # none, low, medium, high, critical
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    operator_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="open")  # open, resolved, under_review
    reported_by: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class FaultLog(Base):
    """Fault and error message log."""
    __tablename__ = "fault_logs"

    fault_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    fault_code: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    equipment_name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    error_message: Mapped[str] = mapped_column(Text, nullable=False)
    fault_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)  # low, medium, high, critical
    fault_timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="active")  # active, acknowledged, resolved
    acknowledged_by: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    resolution_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class IncidentRecord(Base):
    """Operational incident record."""
    __tablename__ = "incident_records"

    incident_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    incident_code: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    equipment_name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    incident_type: Mapped[str] = mapped_column(String(100), nullable=False)  # safety, process, equipment, environmental
    description: Mapped[str] = mapped_column(Text, nullable=False)
    incident_date: Mapped[date] = mapped_column(Date, nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    affected_area: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    reported_by: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    corrective_action: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    preventive_action: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="open")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class BreakdownRecord(Base):
    """Historical breakdown database."""
    __tablename__ = "breakdown_history"

    breakdown_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    breakdown_code: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    equipment_name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    failure_type: Mapped[str] = mapped_column(String(100), nullable=False)
    breakdown_date: Mapped[date] = mapped_column(Date, nullable=False)
    downtime_hours: Mapped[float] = mapped_column(Float, default=0.0)
    repair_time_hours: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    root_cause: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    failure_description: Mapped[str] = mapped_column(Text, nullable=False)
    corrective_action: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    preventive_action: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    repair_cost: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    technician: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    parts_replaced: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class AlertRecord(Base):
    """Persistent alert storage."""
    __tablename__ = "alert_records"

    alert_id:      Mapped[str]           = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    equipment_name:Mapped[str]           = mapped_column(String(200), nullable=False, index=True)
    alert_type:    Mapped[str]           = mapped_column(String(20),  nullable=False)  # low/medium/high/critical
    severity:      Mapped[int]           = mapped_column(Integer, default=1)
    message:       Mapped[str]           = mapped_column(Text, nullable=False)
    source:        Mapped[str]           = mapped_column(String(50), default="threshold")
    status:        Mapped[str]           = mapped_column(String(20), default="active")
    acknowledged_by: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    resolved_at:   Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at:    Mapped[datetime]      = mapped_column(DateTime, server_default=func.now())
