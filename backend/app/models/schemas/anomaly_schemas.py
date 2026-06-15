"""Pydantic schemas for Phase 3: Anomaly Detection and Health Monitoring."""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


# ============ Sensor Data Schemas ============

class SensorDataBase(BaseModel):
    """Base sensor data schema."""
    equipment_name: str = Field(..., min_length=1, max_length=200)
    temperature: Optional[float] = Field(None, ge=-50, le=500)
    vibration: Optional[float] = Field(None, ge=0, le=100)
    current: Optional[float] = Field(None, ge=0, le=500)
    pressure: Optional[float] = Field(None, ge=0, le=1000)
    rpm: Optional[int] = Field(None, ge=0, le=50000)


class SensorDataCreate(SensorDataBase):
    """Schema for creating sensor data."""
    timestamp: Optional[datetime] = None


class SensorDataResponse(SensorDataBase):
    """Schema for sensor data response."""
    sensor_id: str
    timestamp: datetime
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SensorDataListResponse(BaseModel):
    """Schema for paginated sensor data list."""
    data: List[SensorDataResponse]
    total: int
    page: int
    page_size: int


# ============ Prediction Schemas ============

class PredictionRequest(BaseModel):
    """Schema for anomaly prediction request."""
    temperature: float = Field(..., ge=-50, le=500)
    vibration: float = Field(..., ge=0, le=100)
    current: float = Field(..., ge=0, le=500)
    pressure: float = Field(..., ge=0, le=1000)
    rpm: float = Field(..., ge=0, le=50000)
    equipment_name: Optional[str] = Field(default="Unknown Equipment")


class PredictionResponse(BaseModel):
    """Schema for prediction response."""
    equipment_name: str
    timestamp: datetime
    anomaly: bool
    anomaly_score: float
    health_score: int
    health_status: str
    risk_level: str
    message: str
    recommendations: List[str]
    alerts: List[Dict[str, Any]]
    explanation: Dict[str, Any]
    sensor_readings: Dict[str, float]


# ============ Health Status Schemas ============

class EquipmentHealthResponse(BaseModel):
    """Schema for equipment health response."""
    equipment_name: str
    health_score: int
    health_status: str
    risk_level: str
    status: str
    trend: str
    anomaly_count: int
    total_readings: int
    last_updated: datetime


class HealthStatusResponse(BaseModel):
    """Schema for overall health status."""
    total_equipment: int
    healthy_count: int
    fair_count: int
    poor_count: int
    critical_count: int
    equipment: List[EquipmentHealthResponse]
    overall_health_percentage: float


# ============ Alert Schemas ============

class AlertResponse(BaseModel):
    """Schema for alert response."""
    alert_id: str
    equipment_name: str
    alert_type: str
    severity: int
    message: str
    timestamp: datetime
    status: str
    source: str
    sensor_readings: Optional[Dict[str, float]] = None
    health_score: Optional[int] = None


class AlertListResponse(BaseModel):
    """Schema for paginated alert list."""
    alerts: List[AlertResponse]
    total: int
    active_count: int
    critical_count: int


class AlertAcknowledgeRequest(BaseModel):
    """Schema for acknowledging an alert."""
    alert_id: str
    acknowledged_by: Optional[str] = "system"


class AlertSummaryResponse(BaseModel):
    """Schema for alert summary."""
    total: int
    active: int
    acknowledged: int
    resolved: int
    by_type: Dict[str, int]
    critical_count: int


# ============ Health Score Schemas ============

class HealthFactorResponse(BaseModel):
    """Schema for individual health factor."""
    value: float
    optimal: float
    min: float
    max: float
    status: str
    deviation: float


class HealthScoreDetailResponse(BaseModel):
    """Schema for detailed health score."""
    score: int
    status: str
    risk_level: str
    factors: Dict[str, HealthFactorResponse]
    explanation: str
    recommendations: List[str]


# ============ Anomaly Explanation Schemas ============

class TriggeringFeatureResponse(BaseModel):
    """Schema for triggering feature."""
    name: str
    value: float
    threshold: float
    deviation: float
    importance: float


class AnomalyExplanationResponse(BaseModel):
    """Schema for anomaly explanation."""
    is_anomaly: bool
    anomaly_score: float
    triggering_features: List[TriggeringFeatureResponse]
    risk_explanation: str
    confidence: float


# ============ Dashboard Schemas ============

class DashboardHealthSummary(BaseModel):
    """Schema for dashboard health summary."""
    total_equipment: int
    healthy_percentage: float
    average_health_score: float
    active_alerts: int
    critical_alerts: int
    anomalies_detected: int


class DashboardSensorTrend(BaseModel):
    """Schema for sensor trend data."""
    equipment_name: str
    timestamp: datetime
    temperature: Optional[float] = None
    vibration: Optional[float] = None
    current: Optional[float] = None
    pressure: Optional[float] = None
    rpm: Optional[int] = None
    health_score: Optional[int] = None


class DashboardResponse(BaseModel):
    """Schema for dashboard data."""
    health_summary: DashboardHealthSummary
    recent_alerts: List[AlertResponse]
    equipment_health: List[EquipmentHealthResponse]
    sensor_trends: List[DashboardSensorTrend]