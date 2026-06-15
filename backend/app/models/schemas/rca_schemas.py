"""Pydantic schemas for Phase 5: Root Cause Analysis."""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


# ============ RCA Request Schemas ============

class RCARequest(BaseModel):
    """Schema for root cause analysis request."""
    equipment: str = Field(..., min_length=1, max_length=200)
    issue: Optional[str] = Field(default=None, max_length=500)
    severity: Optional[str] = Field(default=None, pattern="^(low|medium|high|critical)$")
    temperature: Optional[float] = Field(default=None, ge=-50, le=200)
    vibration: Optional[float] = Field(default=None, ge=0, le=20)
    current: Optional[float] = Field(default=None, ge=0, le=100)
    pressure: Optional[float] = Field(default=None, ge=0, le=150)
    rpm: Optional[float] = Field(default=None, ge=0, le=5000)
    anomaly_score: Optional[float] = Field(default=None)
    failure_probability: Optional[float] = Field(default=None, ge=0, le=1)


# ============ RCA Response Schemas ============

class SimilarCaseResponse(BaseModel):
    """Schema for similar case."""
    case_id: str
    case_type: str
    equipment_name: str
    issue: str
    root_cause: Optional[str] = None
    action_taken: Optional[str] = None
    outcome: Optional[str] = None
    severity: str
    match_score: float
    date: datetime


class RootCauseResponse(BaseModel):
    """Schema for root cause."""
    cause: str
    confidence: float
    confidence_level: str
    evidence: List[str]
    recommended_actions: List[str]
    explanation: str
    pattern_matched: Optional[str] = None


class AlternativeCauseResponse(BaseModel):
    """Schema for alternative cause."""
    cause: str
    confidence: float
    reasoning: str


class ConfidenceComponentResponse(BaseModel):
    """Schema for confidence component."""
    source: str
    weight: float
    score: float
    evidence: List[str]
    details: str


class RCAResponse(BaseModel):
    """Schema for root cause analysis response."""
    analysis_id: str
    equipment_name: str
    timestamp: datetime
    sensor_readings: Dict[str, Optional[float]]
    primary_cause: RootCauseResponse
    secondary_causes: List[AlternativeCauseResponse]
    contributing_factors: List[str]
    similar_cases: List[SimilarCaseResponse]
    confidence: float
    confidence_level: str
    confidence_components: List[ConfidenceComponentResponse]
    reasoning_path: List[str]
    recommended_actions: List[str]
    investigation_steps: List[str]


# ============ Similar Cases Schemas ============

class SimilarCasesResponse(BaseModel):
    """Schema for similar cases response."""
    equipment: str
    cases: List[SimilarCaseResponse]
    total: int


# ============ Failure Patterns Schemas ============

class FailurePatternResponse(BaseModel):
    """Schema for failure pattern."""
    pattern_id: str
    name: str
    symptoms: Dict[str, Any]
    probable_cause: str
    confidence_weight: float
    description: str
    recommended_actions: List[str]


class FailurePatternsListResponse(BaseModel):
    """Schema for failure patterns list."""
    patterns: List[FailurePatternResponse]
    total: int


# ============ RCA Reports Schemas ============

class RCAReportResponse(BaseModel):
    """Schema for RCA report."""
    report_id: str
    equipment: str
    issue: str
    root_cause: str
    confidence: float
    alternative_causes: List[Dict[str, Any]]
    evidence: List[str]
    recommended_actions: List[str]
    investigation_steps: List[str]
    similar_cases: List[Dict[str, Any]]
    created_at: datetime
    report_format: str


class RCAReportsListResponse(BaseModel):
    """Schema for RCA reports list."""
    reports: List[RCAReportResponse]
    total: int


class RCAReportTextResponse(BaseModel):
    """Schema for text report."""
    report_id: str
    content: str


class RCAReportHtmlResponse(BaseModel):
    """Schema for HTML report."""
    report_id: str
    content: str


# ============ Dashboard Schemas ============

class RCADashboardResponse(BaseModel):
    """Schema for RCA dashboard."""
    total_analyses: int
    recent_analyses: List[RCAResponse]
    common_causes: List[Dict[str, Any]]
    average_confidence: float