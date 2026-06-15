"""Pydantic schemas for Phase 6: Maintenance Recommendation Engine."""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


# ============ Recommendation Schemas ============

class RecommendationItem(BaseModel):
    """Single recommendation item."""
    recommendation_id: str
    equipment_name: str
    priority: str  # P1, P2, P3, P4
    category: str  # immediate, repair, monitoring, preventive, safety
    action: str
    reason: str
    evidence: List[str]
    references: List[str]
    estimated_downtime_hours: float
    estimated_cost: Optional[float] = None


class RecommendationRequest(BaseModel):
    """Schema for recommendation request."""
    equipment: str = Field(..., min_length=1, max_length=200)
    equipment_type: Optional[str] = Field(default=None, max_length=100)
    root_cause: Optional[str] = Field(default=None, max_length=200)
    failure_probability: Optional[float] = Field(default=None, ge=0, le=1)
    rul_days: Optional[int] = Field(default=None, ge=0)
    health_score: Optional[int] = Field(default=None, ge=0, le=100)
    risk_level: Optional[str] = Field(default=None, pattern="^(low|medium|high|critical)$")
    anomaly_detected: Optional[bool] = False
    temperature: Optional[float] = None
    vibration: Optional[float] = None
    current: Optional[float] = None
    pressure: Optional[float] = None
    rpm: Optional[float] = None


class RecommendationResponse(BaseModel):
    """Schema for recommendation response."""
    recommendation_id: str
    equipment_name: str
    timestamp: datetime
    priority: str
    immediate_actions: List[RecommendationItem]
    repair_actions: List[RecommendationItem]
    monitoring_actions: List[RecommendationItem]
    preventive_actions: List[RecommendationItem]
    safety_actions: List[RecommendationItem]
    overall_reason: str
    confidence: float
    estimated_total_downtime: float


# ============ Repair Guide Schemas ============

class RepairStepResponse(BaseModel):
    """Schema for repair step."""
    step_number: int
    action: str
    description: str
    estimated_time_minutes: int
    safety_requirements: List[str]
    tools_required: List[str]
    source: str


class RepairGuideResponse(BaseModel):
    """Schema for repair guide."""
    guide_id: str
    equipment_name: str
    repair_type: str
    estimated_total_time_minutes: int
    steps: List[RepairStepResponse]
    required_parts: List[str]
    required_tools: List[str]
    safety_warnings: List[str]
    post_repair_checks: List[str]


# ============ Maintenance Plan Schemas ============

class MaintenanceTaskResponse(BaseModel):
    """Schema for maintenance task."""
    task_id: str
    task_name: str
    description: str
    frequency: str
    estimated_duration_hours: float
    priority: str
    skills_required: List[str]
    parts_needed: List[str]
    estimated_cost: float


class MaintenanceScheduleResponse(BaseModel):
    """Schema for maintenance schedule."""
    schedule_id: str
    equipment_name: str
    created_at: datetime
    tasks: List[MaintenanceTaskResponse]
    total_weekly_hours: float
    total_monthly_hours: float
    estimated_annual_cost: float


# ============ Spare Parts Schemas ============

class SpareRecommendationItem(BaseModel):
    """Schema for spare part recommendation."""
    part_id: str
    part_name: str
    part_number: str
    quantity: int
    urgency: str
    lead_time_days: int
    estimated_cost: float
    supplier: Optional[str] = None
    reason: str
    source: str


class SparePartSetResponse(BaseModel):
    """Schema for spare parts set."""
    recommendation_id: str
    equipment_name: str
    root_cause: str
    timestamp: datetime
    parts: List[SpareRecommendationItem]
    total_estimated_cost: float
    critical_parts: List[str]


# ============ Maintenance Plan Request ============

class MaintenancePlanRequest(BaseModel):
    """Schema for maintenance plan request."""
    equipment: str = Field(..., min_length=1, max_length=200)
    equipment_type: Optional[str] = Field(default=None, max_length=100)
    criticality: Optional[str] = Field(default="medium", pattern="^(low|medium|high|critical)$")
    condition: Optional[str] = Field(default="good", pattern="^(good|fair|poor)$")


# ============ Complete Maintenance Plan ============

class CompleteMaintenancePlanResponse(BaseModel):
    """Schema for complete maintenance plan."""
    plan_id: str
    equipment_name: str
    timestamp: datetime
    priority: str
    root_cause: Optional[str] = None
    immediate_actions: List[str]
    repair_guide: Optional[RepairGuideResponse] = None
    maintenance_schedule: MaintenanceScheduleResponse
    spare_parts: SparePartSetResponse
    estimated_total_downtime: float
    estimated_total_cost: float
    next_steps: List[str]


# ============ Dashboard Schemas ============

class RecommendationSummary(BaseModel):
    """Schema for recommendation summary."""
    equipment_name: str
    priority: str
    root_cause: Optional[str] = None
    action_count: int
    estimated_downtime: float


class RecommendationDashboardResponse(BaseModel):
    """Schema for recommendation dashboard."""
    total_recommendations: int
    p1_count: int
    p2_count: int
    p3_count: int
    p4_count: int
    recommendations: List[RecommendationSummary]
    critical_equipment: List[str]


# ============ Report Schemas ============

class MaintenanceReportRequest(BaseModel):
    """Schema for maintenance report request."""
    equipment: str
    include_rca: bool = True
    include_predictions: bool = True
    include_recommendations: bool = True
    include_spare_parts: bool = True


class MaintenanceReportResponse(BaseModel):
    """Schema for maintenance report."""
    report_id: str
    equipment_name: str
    generated_at: datetime
    report_type: str
    content: Dict[str, Any]