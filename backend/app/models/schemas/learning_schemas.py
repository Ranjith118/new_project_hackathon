"""Pydantic schemas for Phase 9: Feedback Learning & Continuous Improvement."""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


# ============ Feedback Schemas ============

class FeedbackCreate(BaseModel):
    """Schema for creating feedback."""
    equipment_id: str
    equipment_name: str
    module_name: str
    recommendation: str
    feedback_type: str
    rating: int = Field(ge=1, le=5)
    comments: Optional[str] = ""
    engineer_name: str


class FeedbackResponse(BaseModel):
    """Schema for feedback response."""
    feedback_id: str
    equipment_id: str
    equipment_name: str
    module_name: str
    recommendation: str
    feedback_type: str
    rating: int
    comments: str
    engineer_name: str
    timestamp: datetime
    resolved: bool


class FeedbackListResponse(BaseModel):
    """Schema for feedback list."""
    feedback: List[FeedbackResponse]
    total: int


# ============ Outcome Schemas ============

class OutcomeCreate(BaseModel):
    """Schema for creating maintenance outcome."""
    equipment_id: str
    equipment_name: str
    predicted_cause: str
    actual_cause: str
    predicted_action: str
    actual_action: str
    outcome: str  # success, partial_success, failure
    predicted_downtime_hours: float
    actual_downtime_hours: float
    predicted_cost: float
    actual_cost: float
    spare_parts_used: List[str]
    success: bool
    notes: Optional[str] = ""
    engineer_name: str
    completed_at: datetime


class OutcomeResponse(BaseModel):
    """Schema for outcome response."""
    outcome_id: str
    equipment_id: str
    equipment_name: str
    predicted_cause: str
    actual_cause: str
    predicted_action: str
    actual_action: str
    outcome: str
    predicted_downtime_hours: float
    actual_downtime_hours: float
    predicted_cost: float
    actual_cost: float
    spare_parts_used: List[str]
    success: bool
    notes: str
    engineer_name: str
    completed_at: datetime
    created_at: datetime


class OutcomeListResponse(BaseModel):
    """Schema for outcome list."""
    outcomes: List[OutcomeResponse]
    total: int


class OutcomeSummaryResponse(BaseModel):
    """Schema for outcome summary."""
    total_outcomes: int
    success_count: int
    partial_success_count: int
    failure_count: int
    success_rate: float
    prediction_accuracy: float
    avg_predicted_downtime: float
    avg_actual_downtime: float
    avg_predicted_cost: float
    avg_actual_cost: float
    downtime_variance: float
    cost_variance: float


# ============ Performance Schemas ============

class PerformanceTrendResponse(BaseModel):
    """Schema for performance trend."""
    metric_name: str
    current_value: float
    previous_value: float
    change: float
    trend: str
    data_points: List[Dict[str, Any]]


class ModelPerformanceResponse(BaseModel):
    """Schema for model performance."""
    model_name: str
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    mae: float
    rmse: float
    sample_count: int
    last_updated: datetime


class RecommendationScoreResponse(BaseModel):
    """Schema for recommendation score."""
    recommendation_type: str
    module_name: str
    total_count: int
    acceptance_count: int
    success_count: int
    avg_effectiveness: float
    confidence_adjustment: float
    last_updated: datetime


class PerformanceDashboardResponse(BaseModel):
    """Schema for performance dashboard."""
    prediction_accuracy: float
    recommendation_acceptance: float
    outcome_success_rate: float
    total_feedback_count: int
    total_outcomes_count: int
    model_count: int
    trends: List[Dict[str, Any]]
    models: List[ModelPerformanceResponse]


# ============ Retraining Schemas ============

class RetrainingJobResponse(BaseModel):
    """Schema for retraining job."""
    job_id: str
    model_name: str
    status: str
    trigger: str
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    old_version: str
    new_version: str
    old_accuracy: float
    new_accuracy: float
    improvement: float
    samples_used: int
    error_message: Optional[str] = None


class RetrainingSummaryResponse(BaseModel):
    """Schema for retraining summary."""
    total_jobs: int
    completed: int
    failed: int
    pending: int
    running: int
    average_improvement: float
    models_needing_retraining: List[str]
    last_retraining: Optional[datetime] = None


# ============ Learning Summary Schemas ============

class LearningSummaryResponse(BaseModel):
    """Schema for learning summary."""
    summary_id: str
    generated_at: datetime
    period: str
    period_start: datetime
    period_end: datetime
    total_feedback: int
    positive_feedback: int
    negative_feedback: int
    acceptance_rate: float
    total_outcomes: int
    success_rate: float
    prediction_accuracy: float
    average_accuracy: float
    accuracy_change: float
    models_improved: List[str]
    retraining_jobs: int
    models_retrained: int
    average_improvement: float
    top_improvements: List[str]
    areas_of_concern: List[str]
    recommendations: List[str]
    summary_text: str
    detailed_report: str


# ============ Module Summary Schema ============

class ModuleFeedbackSummaryResponse(BaseModel):
    """Schema for module feedback summary."""
    module_name: str
    total_feedback: int
    positive_count: int
    negative_count: int
    acceptance_rate: float
    average_rating: float
    top_positive: List[str]
    top_negative: List[str]