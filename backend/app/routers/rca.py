"""Phase 5: Root Cause Analysis API."""
import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
import json

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, desc, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.models import Equipment, MaintenanceLog, FailureReport
from app.models.schemas.rca_schemas import (
    RCARequest, RCAResponse,
    SimilarCaseResponse, SimilarCasesResponse,
    FailurePatternResponse, FailurePatternsListResponse,
    RCAReportResponse, RCAReportsListResponse,
    RCAReportTextResponse, RCAReportHtmlResponse,
    RCADashboardResponse,
    RootCauseResponse, AlternativeCauseResponse, ConfidenceComponentResponse
)
from app.rca.pattern_engine import get_pattern_engine
from app.rca.similar_case_retriever import get_similar_case_retriever
from app.rca.root_cause_engine import get_root_cause_engine
from app.rca.report_generator import get_report_generator

router = APIRouter(prefix="/api/rca", tags=["Phase 5 - Root Cause Analysis"])


# ============ Root Cause Analysis ============

@router.post("/analyze", response_model=RCAResponse)
async def root_cause_analysis(
    request: RCARequest
):
    """
    Perform root cause analysis on equipment.
    
    Analyzes sensor readings, historical cases, and patterns
    to identify the most probable root cause of equipment issues.
    """
    engine = get_root_cause_engine()
    
    # Perform analysis
    result = engine.analyze(
        equipment_name=request.equipment,
        temperature=request.temperature,
        vibration=request.vibration,
        current=request.current,
        pressure=request.pressure,
        rpm=request.rpm,
        issue_description=request.issue,
        severity=request.severity,
        anomaly_score=request.anomaly_score,
        failure_probability=request.failure_probability
    )
    
    # Build response
    similar_cases = [
        SimilarCaseResponse(
            case_id=c.case_id,
            case_type=c.case_type,
            equipment_name=c.equipment_name,
            issue=c.issue,
            root_cause=c.root_cause,
            action_taken=c.action_taken,
            outcome=c.outcome,
            severity=c.severity,
            match_score=c.match_score,
            date=c.date
        )
        for c in result.similar_cases
    ]
    
    confidence_components = [
        ConfidenceComponentResponse(
            source=comp.source,
            weight=comp.weight,
            score=comp.score,
            evidence=comp.evidence,
            details=comp.details
        )
        for comp in result.confidence_result.components
    ]
    
    return RCAResponse(
        analysis_id=result.analysis_id,
        equipment_name=result.equipment_name,
        timestamp=result.timestamp,
        sensor_readings=result.sensor_readings,
        primary_cause=RootCauseResponse(
            cause=result.primary_cause.cause,
            confidence=result.primary_cause.confidence,
            confidence_level=result.primary_cause.confidence_level,
            evidence=result.primary_cause.evidence,
            recommended_actions=result.primary_cause.recommended_actions,
            explanation=result.primary_cause.explanation,
            pattern_matched=result.primary_cause.pattern_matched
        ),
        secondary_causes=[
            AlternativeCauseResponse(
                cause=alt.cause,
                confidence=alt.confidence,
                reasoning=alt.reasoning
            )
            for alt in result.secondary_causes
        ],
        contributing_factors=result.contributing_factors,
        similar_cases=similar_cases,
        confidence=result.confidence_result.overall_confidence,
        confidence_level=result.confidence_result.level,
        confidence_components=confidence_components,
        reasoning_path=result.reasoning_path,
        recommended_actions=result.recommended_actions,
        investigation_steps=result.investigation_steps
    )


# ============ Similar Cases ============

@router.get("/similar-cases", response_model=SimilarCasesResponse)
async def get_similar_cases(
    equipment: str = Query(..., min_length=1),
    issue: Optional[str] = Query(None),
    limit: int = Query(5, ge=1, le=20)
):
    """
    Retrieve similar historical cases.
    
    Searches maintenance logs and failure reports
    for cases similar to the current issue.
    """
    retriever = get_similar_case_retriever()
    
    cases = retriever.get_all_similar_cases(
        equipment_name=equipment,
        issue_description=issue or "",
        sensor_readings={},
        limit=limit
    )
    
    return SimilarCasesResponse(
        equipment=equipment,
        cases=[
            SimilarCaseResponse(
                case_id=c.case_id,
                case_type=c.case_type,
                equipment_name=c.equipment_name,
                issue=c.issue,
                root_cause=c.root_cause,
                action_taken=c.action_taken,
                outcome=c.outcome,
                severity=c.severity,
                match_score=c.match_score,
                date=c.date
            )
            for c in cases
        ],
        total=len(cases)
    )


# ============ Failure Patterns ============

@router.get("/patterns", response_model=FailurePatternsListResponse)
async def get_failure_patterns():
    """Get all registered failure patterns."""
    pattern_engine = get_pattern_engine()
    patterns = pattern_engine.get_all_patterns()
    
    return FailurePatternsListResponse(
        patterns=[
            FailurePatternResponse(
                pattern_id=p.pattern_id,
                name=p.name,
                symptoms=p.symptoms,
                probable_cause=p.probable_cause,
                confidence_weight=p.confidence_weight,
                description=p.description,
                recommended_actions=p.recommended_actions
            )
            for p in patterns
        ],
        total=len(patterns)
    )


@router.post("/patterns")
async def add_failure_pattern(
    pattern_id: str,
    name: str,
    symptoms: Dict[str, Any],
    probable_cause: str,
    confidence_weight: float = 0.8,
    description: str = "",
    recommended_actions: List[str] = None
):
    """Add a new failure pattern."""
    from app.rca.pattern_engine import FailurePattern
    
    pattern_engine = get_pattern_engine()
    
    pattern = FailurePattern(
        pattern_id=pattern_id,
        name=name,
        symptoms=symptoms,
        probable_cause=probable_cause,
        confidence_weight=confidence_weight,
        description=description,
        recommended_actions=recommended_actions or []
    )
    
    pattern_engine.add_pattern(pattern)
    
    return {"status": "success", "message": "Pattern added"}


# ============ RCA Reports ============

@router.post("/reports")
async def create_report(
    analysis_id: str,
    equipment: str,
    issue: str,
    severity: Optional[str] = None,
    temperature: Optional[float] = None,
    vibration: Optional[float] = None,
    current: Optional[float] = None,
    pressure: Optional[float] = None,
    rpm: Optional[float] = None,
    format: str = Query("json", pattern="^(json|text|html)$")
):
    """Create and save a full RCA report from analysis."""
    report_gen = get_report_generator()
    engine = get_root_cause_engine()

    # Run a full analysis
    rca_result = engine.analyze(
        equipment_name=equipment,
        temperature=temperature,
        vibration=vibration,
        current=current,
        pressure=pressure,
        rpm=rpm,
        issue_description=issue,
        severity=severity
    )
    # Use the provided analysis_id to keep traceability
    rca_result.analysis_id = analysis_id

    # Generate and save the full report
    report = report_gen.generate_report(rca_result, issue=issue, format=format)
    report_gen.save_report(report)

    return {"status": "success", "report_id": analysis_id}


@router.get("/reports", response_model=RCAReportsListResponse)
async def get_reports(
    limit: int = Query(20, ge=1, le=100)
):
    """Get all saved RCA reports."""
    report_gen = get_report_generator()
    reports = report_gen.get_all_reports()[:limit]
    
    return RCAReportsListResponse(
        reports=[
            RCAReportResponse(
                report_id=r.report_id,
                equipment=r.equipment,
                issue=r.issue,
                root_cause=r.root_cause,
                confidence=r.confidence,
                alternative_causes=r.alternative_causes,
                evidence=r.evidence,
                recommended_actions=r.recommended_actions,
                investigation_steps=r.investigation_steps,
                similar_cases=r.similar_cases,
                created_at=r.created_at,
                report_format=r.report_format
            )
            for r in reports
        ],
        total=len(reports)
    )


@router.get("/reports/{report_id}", response_model=RCAReportResponse)
async def get_report(report_id: str):
    """Get a specific RCA report."""
    report_gen = get_report_generator()
    report = report_gen.load_report(report_id)
    
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    return RCAReportResponse(
        report_id=report.report_id,
        equipment=report.equipment,
        issue=report.issue,
        root_cause=report.root_cause,
        confidence=report.confidence,
        alternative_causes=report.alternative_causes,
        evidence=report.evidence,
        recommended_actions=report.recommended_actions,
        investigation_steps=report.investigation_steps,
        similar_cases=report.similar_cases,
        created_at=report.created_at,
        report_format=report.report_format
    )


@router.get("/reports/{report_id}/text", response_model=RCAReportTextResponse)
async def get_report_text(report_id: str):
    """Get RCA report as text format."""
    report_gen = get_report_generator()
    report = report_gen.load_report(report_id)
    
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    text = report_gen.generate_text_report(report)
    
    return RCAReportTextResponse(
        report_id=report_id,
        content=text
    )


@router.get("/reports/{report_id}/html", response_model=RCAReportHtmlResponse)
async def get_report_html(report_id: str):
    """Get RCA report as HTML format."""
    report_gen = get_report_generator()
    report = report_gen.load_report(report_id)
    
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    html = report_gen.generate_html_report(report)
    
    return RCAReportHtmlResponse(
        report_id=report_id,
        content=html
    )


# ============ RCA Dashboard ============

@router.get("/dashboard", response_model=RCADashboardResponse)
async def get_rca_dashboard(
    db: AsyncSession = Depends(get_db)
):
    """Get RCA dashboard statistics."""
    # Get recent maintenance logs and failure reports
    log_result = await db.execute(
        select(MaintenanceLog).order_by(desc(MaintenanceLog.created_at)).limit(10)
    )
    logs = log_result.scalars().all()
    
    failure_result = await db.execute(
        select(FailureReport).order_by(desc(FailureReport.created_at)).limit(10)
    )
    failures = failure_result.scalars().all()
    
    # Count total
    total_logs = await db.execute(select(func.count()).select_from(MaintenanceLog))
    total_failures = await db.execute(select(func.count()).select_from(FailureReport))
    
    total_analyses = total_logs.scalar() + total_failures.scalar()
    
    # Common causes (mock data for demo)
    common_causes = [
        {"cause": "Bearing Wear", "count": 15, "percentage": 35},
        {"cause": "Cooling System Failure", "count": 10, "percentage": 23},
        {"cause": "Pump Blockage", "count": 8, "percentage": 19},
        {"cause": "Electrical Fault", "count": 5, "percentage": 12},
        {"cause": "Lubrication Failure", "count": 5, "percentage": 11}
    ]
    
    return RCADashboardResponse(
        total_analyses=total_analyses,
        recent_analyses=[],
        common_causes=common_causes,
        average_confidence=78.5
    )


# ============ RCA from Equipment ============

@router.post("/analyze-equipment/{equipment_name}")
async def analyze_equipment(
    equipment_name: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Perform RCA for equipment using latest sensor data.
    
    Retrieves the most recent sensor readings for the equipment
    and performs comprehensive root cause analysis.
    """
    from app.models.models import SensorData
    
    # Get latest sensor data
    result = await db.execute(
        select(SensorData)
        .where(SensorData.equipment_name == equipment_name)
        .order_by(desc(SensorData.timestamp))
        .limit(1)
    )
    sensor_data = result.scalar_one_or_none()
    
    if not sensor_data:
        raise HTTPException(
            status_code=404,
            detail=f"No sensor data found for equipment: {equipment_name}"
        )
    
    # Create RCA request from sensor data
    request = RCARequest(
        equipment=equipment_name,
        temperature=sensor_data.temperature,
        vibration=sensor_data.vibration,
        current=sensor_data.current,
        pressure=sensor_data.pressure,
        rpm=float(sensor_data.rpm) if sensor_data.rpm else None
    )
    
    # Perform analysis
    return await root_cause_analysis(request)