"""Pydantic schemas for Phase 8: Plant-Level Prioritization & Decision Support."""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


# ============ Criticality Schemas ============

class CriticalityScoreResponse(BaseModel):
    """Schema for criticality score."""
    equipment_id: str
    equipment_name: str
    equipment_type: str
    criticality_score: float
    criticality_level: str
    factors: Dict[str, float]
    production_dependency: float
    safety_impact: float
    environmental_impact: float
    downtime_cost: float
    replacement_difficulty: float
    last_updated: datetime


class CriticalitySummaryResponse(BaseModel):
    """Schema for criticality summary."""
    total_equipment: int
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    average_criticality: float
    total_downtime_cost_per_hour: float


# ============ Risk Schemas ============

class RiskScoreResponse(BaseModel):
    """Schema for risk score."""
    equipment_id: str
    equipment_name: str
    equipment_type: str
    risk_score: float
    risk_level: str
    failure_probability: float
    rul_days: int
    health_score: int
    anomaly_score: float
    criticality_score: float
    components: Dict[str, float]
    reasons: List[str]
    last_updated: datetime


class RiskSummaryResponse(BaseModel):
    """Schema for risk summary."""
    total_equipment: int
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    average_risk: float
    plant_health_score: float
    critical_equipment_cost: float


# ============ Priority Schemas ============

class MaintenancePriorityResponse(BaseModel):
    """Schema for maintenance priority."""
    priority_id: str
    equipment_id: str
    equipment_name: str
    rank: int
    priority_score: float
    priority_level: str
    risk_score: float
    failure_probability: float
    rul_days: int
    criticality: float
    recommended_action: str
    reason: List[str]
    estimated_downtime: float
    estimated_cost: float
    spare_available: bool
    production_impact: str
    created_at: datetime


class PrioritySummaryResponse(BaseModel):
    """Schema for priority summary."""
    total_equipment: int
    p1_count: int
    p2_count: int
    p3_count: int
    p4_count: int
    total_estimated_downtime: float
    total_estimated_cost: float
    critical_production_impact: int


# ============ Bottleneck Schemas ============

class BottleneckResponse(BaseModel):
    """Schema for bottleneck."""
    bottleneck_id: str
    equipment_id: str
    equipment_name: str
    bottleneck_type: str
    severity: str
    reason: str
    impact: str
    affected_systems: List[str]
    risk_score: float
    mitigation_options: List[str]
    created_at: datetime


class BottleneckSummaryResponse(BaseModel):
    """Schema for bottleneck summary."""
    total_bottlenecks: int
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    single_point_failure_count: int
    series_critical_count: int
    capacity_limiter_count: int


# ============ Schedule Schemas ============

class ScheduledMaintenanceResponse(BaseModel):
    """Schema for scheduled maintenance."""
    schedule_id: str
    equipment_id: str
    equipment_name: str
    maintenance_type: str
    scheduled_date: datetime
    priority: str
    estimated_duration_hours: float
    estimated_downtime: float
    technicians_required: int
    parts_needed: List[str]
    prerequisites: List[str]
    status: str
    notes: str


class MaintenanceScheduleResponse(BaseModel):
    """Schema for maintenance schedule."""
    schedule_id: str
    week_start: datetime
    created_at: datetime
    tasks: List[ScheduledMaintenanceResponse]
    total_tasks: int
    total_downtime_hours: float
    production_impact: str
    summary: Dict[str, Any]


# ============ Executive Summary Schemas ============

class ExecutiveSummaryResponse(BaseModel):
    """Schema for executive summary."""
    summary_id: str
    generated_at: datetime
    plant_name: str
    plant_health_score: float
    critical_equipment_count: int
    immediate_actions: List[str]
    short_term_actions: List[str]
    medium_term_actions: List[str]
    key_insights: List[str]
    risks: List[str]
    recommendations: List[str]
    summary_text: str
    detailed_report: str


class ProductionImpactResponse(BaseModel):
    """Schema for production impact."""
    equipment: str
    expected_downtime_hours: float
    production_loss_per_hour: float
    total_production_impact: float
    impact_level: str
    recovery_actions: List[str]


# ============ Plant Health Dashboard ============

class PlantHealthDashboardResponse(BaseModel):
    """Schema for plant health dashboard."""
    plant_health_score: float
    total_equipment: int
    critical_count: int
    high_count: int
    active_alerts: int
    maintenance_backlog: int
    criticality_summary: CriticalitySummaryResponse
    risk_summary: RiskSummaryResponse
    priority_summary: PrioritySummaryResponse


# ============ Equipment Ranking ============

class EquipmentRankingResponse(BaseModel):
    """Schema for equipment ranking."""
    rankings: List[MaintenancePriorityResponse]
    total: int


# ============ Decision Summary Request ============

class DecisionSummaryRequest(BaseModel):
    """Schema for decision summary request."""
    plant_name: Optional[str] = Field(default="Steel Manufacturing Plant")
    include_detailed: bool = True