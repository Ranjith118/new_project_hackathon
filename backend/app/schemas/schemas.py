"""Pydantic schemas for request/response validation."""
from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


# ============ Equipment Schemas ============

class EquipmentBase(BaseModel):
    """Base equipment schema."""
    equipment_name: str = Field(..., min_length=1, max_length=200)
    equipment_type: str = Field(..., min_length=1, max_length=100)
    manufacturer: Optional[str] = Field(None, max_length=200)
    installation_date: Optional[date] = None
    status: str = Field(default="operational", max_length=50)


class EquipmentCreate(EquipmentBase):
    """Schema for creating equipment."""
    pass


class EquipmentUpdate(BaseModel):
    """Schema for updating equipment."""
    equipment_name: Optional[str] = Field(None, min_length=1, max_length=200)
    equipment_type: Optional[str] = Field(None, min_length=1, max_length=100)
    manufacturer: Optional[str] = Field(None, max_length=200)
    installation_date: Optional[date] = None
    status: Optional[str] = Field(None, max_length=50)


class EquipmentResponse(EquipmentBase):
    """Schema for equipment response."""
    equipment_id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============ Maintenance Log Schemas ============

class MaintenanceLogBase(BaseModel):
    """Base maintenance log schema."""
    equipment_name: str = Field(..., min_length=1, max_length=200)
    issue: str = Field(..., min_length=1)
    action_taken: Optional[str] = None
    downtime_hours: float = Field(default=0.0, ge=0)
    severity: str = Field(..., pattern="^(low|medium|high|critical)$")
    technician: Optional[str] = Field(None, max_length=200)
    maintenance_date: date


class MaintenanceLogCreate(MaintenanceLogBase):
    """Schema for creating maintenance log."""
    pass


class MaintenanceLogUpdate(BaseModel):
    """Schema for updating maintenance log."""
    equipment_name: Optional[str] = Field(None, min_length=1, max_length=200)
    issue: Optional[str] = Field(None, min_length=1)
    action_taken: Optional[str] = None
    downtime_hours: Optional[float] = Field(None, ge=0)
    severity: Optional[str] = Field(None, pattern="^(low|medium|high|critical)$")
    technician: Optional[str] = Field(None, max_length=200)
    maintenance_date: Optional[date] = None


class MaintenanceLogResponse(MaintenanceLogBase):
    """Schema for maintenance log response."""
    log_id: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============ Sensor Data Schemas ============

class SensorDataBase(BaseModel):
    """Base sensor data schema."""
    equipment_name: str = Field(..., min_length=1, max_length=200)
    temperature: Optional[float] = None
    vibration: Optional[float] = None
    current: Optional[float] = None
    pressure: Optional[float] = None
    rpm: Optional[int] = None
    # Extended sensors
    voltage: Optional[float] = None
    flow_rate: Optional[float] = None
    humidity: Optional[float] = None
    power_consumption: Optional[float] = None
    lubrication_level: Optional[float] = None
    bearing_temperature: Optional[float] = None
    timestamp: datetime
    """Base sensor data schema."""
    equipment_name: str = Field(..., min_length=1, max_length=200)
    temperature: Optional[float] = None
    vibration: Optional[float] = None
    current: Optional[float] = None
    pressure: Optional[float] = None
    rpm: Optional[int] = None
    timestamp: datetime


class SensorDataCreate(SensorDataBase):
    """Schema for creating sensor data."""
    pass


class SensorDataBulk(BaseModel):
    """Schema for bulk sensor data import."""
    readings: List[SensorDataBase]


class SensorDataResponse(SensorDataBase):
    """Schema for sensor data response."""
    sensor_id: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============ Failure Report Schemas ============

class FailureReportBase(BaseModel):
    """Base failure report schema."""
    equipment_name: str = Field(..., min_length=1, max_length=200)
    failure_type: str = Field(..., min_length=1, max_length=100)
    root_cause: Optional[str] = None
    downtime_hours: float = Field(default=0.0, ge=0)
    report_date: date


class FailureReportCreate(FailureReportBase):
    """Schema for creating failure report."""
    pass


class FailureReportUpdate(BaseModel):
    """Schema for updating failure report."""
    equipment_name: Optional[str] = Field(None, min_length=1, max_length=200)
    failure_type: Optional[str] = Field(None, min_length=1, max_length=100)
    root_cause: Optional[str] = None
    downtime_hours: Optional[float] = Field(None, ge=0)
    report_date: Optional[date] = None


class FailureReportResponse(FailureReportBase):
    """Schema for failure report response."""
    report_id: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============ Spare Part Schemas ============

class SparePartBase(BaseModel):
    """Base spare part schema."""
    part_name: str = Field(..., min_length=1, max_length=200)
    stock_quantity: int = Field(default=0, ge=0)
    lead_time_days: int = Field(default=0, ge=0)
    supplier: Optional[str] = Field(None, max_length=200)


class SparePartCreate(SparePartBase):
    """Schema for creating spare part."""
    pass


class SparePartUpdate(BaseModel):
    """Schema for updating spare part."""
    part_name: Optional[str] = Field(None, min_length=1, max_length=200)
    stock_quantity: Optional[int] = Field(None, ge=0)
    lead_time_days: Optional[int] = Field(None, ge=0)
    supplier: Optional[str] = Field(None, max_length=200)


class SparePartResponse(SparePartBase):
    """Schema for spare part response."""
    part_id: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============ Uploaded File Schemas ============

class UploadedFileResponse(BaseModel):
    """Schema for uploaded file response."""
    file_id: str
    filename: str
    file_type: str
    file_category: str
    file_size: int
    file_path: str
    equipment_name: Optional[str] = None
    uploaded_by: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============ Dashboard Schemas ============

class DashboardStats(BaseModel):
    """Dashboard statistics schema."""
    total_equipment: int = 0
    total_maintenance_logs: int = 0
    total_failure_reports: int = 0
    total_manuals: int = 0
    total_sops: int = 0
    total_spare_parts: int = 0
    operational_equipment: int = 0
    maintenance_equipment: int = 0
    failed_equipment: int = 0


class RecentUpload(BaseModel):
    """Recent upload schema."""
    file_id: str
    filename: str
    file_category: str
    file_size: int
    created_at: datetime


class EquipmentStatusSummary(BaseModel):
    """Equipment status summary schema."""
    status: str
    count: int


class DashboardResponse(BaseModel):
    """Full dashboard response schema."""
    stats: DashboardStats
    recent_uploads: List[RecentUpload]
    equipment_status: List[EquipmentStatusSummary]


# ============ Pagination Schemas ============

class PaginatedResponse(BaseModel):
    """Generic paginated response."""
    items: List
    total: int
    page: int
    page_size: int
    total_pages: int