"""Pydantic schemas for Phase 4: Failure Prediction and RUL."""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


# ============ Prediction Request Schemas ============

class FailurePredictionRequest(BaseModel):
    """Schema for failure prediction request."""
    equipment_name: Optional[str] = Field(default="Unknown Equipment")
    temperature: float = Field(..., ge=-50, le=200)
    vibration: float = Field(..., ge=0, le=20)
    current: float = Field(..., ge=0, le=100)
    pressure: float = Field(..., ge=0, le=150)
    rpm: float = Field(..., ge=0, le=5000)


class RULPredictionRequest(BaseModel):
    """Schema for RUL prediction request."""
    equipment_name: Optional[str] = Field(default="Unknown Equipment")
    temperature: float = Field(..., ge=-50, le=200)
    vibration: float = Field(..., ge=0, le=20)
    current: float = Field(..., ge=0, le=100)
    pressure: float = Field(..., ge=0, le=150)
    rpm: float = Field(..., ge=0, le=5000)


# ============ Prediction Response Schemas ============

class FeatureAnalysis(BaseModel):
    """Schema for feature analysis."""
    feature: str
    value: float
    importance: float
    status: str
    impact: Optional[str] = None


class FailurePredictionResponse(BaseModel):
    """Schema for failure prediction response."""
    equipment_name: str
    timestamp: datetime
    failure_probability: float
    risk_level: str
    confidence: float
    prediction: int
    reason: str
    contributing_factors: List[str]
    feature_analysis: List[Dict[str, Any]]


class RULPredictionResponse(BaseModel):
    """Schema for RUL prediction response."""
    equipment_name: str
    timestamp: datetime
    remaining_useful_life: int
    confidence_interval: Optional[Dict[str, Any]] = None
    explanation: str
    critical_factors: List[str]
    warning_factors: List[str]
    feature_analysis: List[FeatureAnalysis]


# ============ Degradation Schemas ============

class DegradationResponse(BaseModel):
    """Schema for degradation state response."""
    equipment_name: str
    timestamp: datetime
    level: str
    score: int
    factors: Dict[str, float]
    explanation: str


# ============ Risk Assessment Schemas ============

class RiskAssessmentResponse(BaseModel):
    """Schema for risk assessment response."""
    equipment_name: str
    timestamp: datetime
    overall_risk: str
    risk_score: int
    health_score: int
    failure_probability: float
    rul_days: int
    explanation: str
    contributing_factors: List[str]
    confidence: float


# ============ Warning Schemas ============

class EarlyWarningResponse(BaseModel):
    """Schema for early warning response."""
    warning_id: str
    equipment_name: str
    level: str
    reason: str
    failure_probability: Optional[float] = None
    rul_days: Optional[int] = None
    timestamp: datetime


class WarningListResponse(BaseModel):
    """Schema for warning list response."""
    warnings: List[EarlyWarningResponse]
    total: int
    critical_count: int
    high_count: int


# ============ Recommendation Schemas ============

class MaintenanceRecommendationResponse(BaseModel):
    """Schema for maintenance recommendation."""
    recommendation_id: str
    equipment_name: str
    priority: str
    category: str
    action: str
    reason: str
    triggered_by: str
    created_at: datetime


# ============ Equipment Prediction Schemas ============

class EquipmentPrediction(BaseModel):
    """Schema for single equipment prediction."""
    equipment_name: str
    health_score: int
    failure_probability: float
    rul_days: int
    risk_level: str
    degradation_level: str
    anomaly_detected: bool
    last_updated: datetime


class EquipmentPredictionListResponse(BaseModel):
    """Schema for equipment predictions list."""
    predictions: List[EquipmentPrediction]
    total: int
    critical_count: int
    high_risk_count: int


# ============ Dashboard Schemas ============

class FailureAlertResponse(BaseModel):
    """Schema for failure alert."""
    alert_id: str
    equipment_name: str
    alert_type: str
    level: str
    reason: str
    failure_probability: Optional[float] = None
    rul_days: Optional[int] = None
    timestamp: datetime


class FailureAlertListResponse(BaseModel):
    """Schema for failure alert list."""
    alerts: List[FailureAlertResponse]
    total: int


class PredictiveDashboardResponse(BaseModel):
    """Schema for predictive maintenance dashboard."""
    total_equipment: int
    critical_risk_count: int
    high_risk_count: int
    medium_risk_count: int
    low_risk_count: int
    critical_alerts: List[EarlyWarningResponse]
    equipment_predictions: List[EquipmentPrediction]
    average_failure_probability: float
    average_rul_days: float


# ============ Model Registry Schemas ============

class ModelInfo(BaseModel):
    """Schema for model information."""
    model_id: str
    model_name: str
    model_type: str
    training_date: datetime
    accuracy: Optional[float] = None
    metrics: Optional[Dict[str, Any]] = None
    version: str
    is_active: bool = True


class ModelRegistryResponse(BaseModel):
    """Schema for model registry."""
    models: List[ModelInfo]
    total: int


# ============ Training Schemas ============

class TrainModelRequest(BaseModel):
    """Schema for model training request."""
    model_type: str = Field(..., pattern="^(failure|rul)$")
    model_name: str = Field(..., min_length=1)
    test_size: float = Field(default=0.2, ge=0.1, le=0.4)
    params: Optional[Dict[str, Any]] = None


class TrainModelResponse(BaseModel):
    """Schema for model training response."""
    status: str
    model_name: str
    model_type: str
    metrics: Dict[str, Any]
    trained_at: datetime