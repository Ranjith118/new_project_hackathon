"""Phase 9: Feedback Learning & Continuous Improvement API."""
import uuid
from datetime import datetime
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.schemas.learning_schemas import (
    FeedbackCreate, FeedbackResponse, FeedbackListResponse,
    OutcomeCreate, OutcomeResponse, OutcomeListResponse, OutcomeSummaryResponse,
    PerformanceTrendResponse, ModelPerformanceResponse, RecommendationScoreResponse,
    PerformanceDashboardResponse, RetrainingJobResponse, RetrainingSummaryResponse,
    LearningSummaryResponse, ModuleFeedbackSummaryResponse
)
from app.learning.feedback_engine import get_feedback_engine, FeedbackType, OutcomeType
from app.learning.recommendation_scoring import get_scoring_engine
from app.learning.performance_monitor import get_performance_monitor
from app.learning.retraining_engine import get_retraining_engine
from app.learning.learning_summary import get_learning_summary_engine

router = APIRouter(prefix="/api/learning", tags=["Phase 9 - Feedback Learning"])


# ============ Feedback Endpoints ============

@router.post("/feedback", response_model=FeedbackResponse)
async def add_feedback(feedback: FeedbackCreate):
    """Add engineer feedback on recommendations."""
    engine = get_feedback_engine()
    
    result = engine.add_feedback(
        equipment_id=feedback.equipment_id,
        equipment_name=feedback.equipment_name,
        module_name=feedback.module_name,
        recommendation=feedback.recommendation,
        feedback_type=feedback.feedback_type,
        rating=feedback.rating,
        comments=feedback.comments or "",
        engineer_name=feedback.engineer_name
    )
    
    return FeedbackResponse(
        feedback_id=result.feedback_id,
        equipment_id=result.equipment_id,
        equipment_name=result.equipment_name,
        module_name=result.module_name,
        recommendation=result.recommendation,
        feedback_type=result.feedback_type.value,
        rating=result.rating,
        comments=result.comments,
        engineer_name=result.engineer_name,
        timestamp=result.timestamp,
        resolved=result.resolved
    )


@router.get("/feedback", response_model=FeedbackListResponse)
async def get_feedback(
    module: Optional[str] = None,
    days: int = Query(30, ge=1, le=365)
):
    """Get feedback history."""
    engine = get_feedback_engine()
    
    if module:
        feedback = engine.get_feedback_by_module(module)
    else:
        feedback = engine.get_recent_feedback(days)
    
    return FeedbackListResponse(
        feedback=[
            FeedbackResponse(
                feedback_id=f.feedback_id,
                equipment_id=f.equipment_id,
                equipment_name=f.equipment_name,
                module_name=f.module_name,
                recommendation=f.recommendation,
                feedback_type=f.feedback_type.value,
                rating=f.rating,
                comments=f.comments,
                engineer_name=f.engineer_name,
                timestamp=f.timestamp,
                resolved=f.resolved
            )
            for f in feedback
        ],
        total=len(feedback)
    )


@router.get("/feedback/module/{module_name}", response_model=List[FeedbackResponse])
async def get_feedback_by_module(module_name: str):
    """Get feedback for a specific module."""
    engine = get_feedback_engine()
    feedback = engine.get_feedback_by_module(module_name)
    
    return [
        FeedbackResponse(
            feedback_id=f.feedback_id,
            equipment_id=f.equipment_id,
            equipment_name=f.equipment_name,
            module_name=f.module_name,
            recommendation=f.recommendation,
            feedback_type=f.feedback_type.value,
            rating=f.rating,
            comments=f.comments,
            engineer_name=f.engineer_name,
            timestamp=f.timestamp,
            resolved=f.resolved
        )
        for f in feedback
    ]


@router.get("/feedback/summary/{module_name}", response_model=ModuleFeedbackSummaryResponse)
async def get_module_feedback_summary(module_name: str):
    """Get feedback summary for a module."""
    engine = get_feedback_engine()
    summary = engine.get_module_summary(module_name)
    
    return ModuleFeedbackSummaryResponse(
        module_name=summary.module_name,
        total_feedback=summary.total_feedback,
        positive_count=summary.positive_count,
        negative_count=summary.negative_count,
        acceptance_rate=summary.acceptance_rate,
        average_rating=summary.average_rating,
        top_positive=summary.top_positive,
        top_negative=summary.top_negative
    )


# ============ Outcome Endpoints ============

@router.post("/outcome", response_model=OutcomeResponse)
async def add_outcome(outcome: OutcomeCreate):
    """Add maintenance outcome."""
    engine = get_feedback_engine()
    
    result = engine.add_outcome(
        equipment_id=outcome.equipment_id,
        equipment_name=outcome.equipment_name,
        predicted_cause=outcome.predicted_cause,
        actual_cause=outcome.actual_cause,
        predicted_action=outcome.predicted_action,
        actual_action=outcome.actual_action,
        outcome=outcome.outcome,
        predicted_downtime=outcome.predicted_downtime_hours,
        actual_downtime=outcome.actual_downtime_hours,
        predicted_cost=outcome.predicted_cost,
        actual_cost=outcome.actual_cost,
        spare_parts=outcome.spare_parts_used,
        success=outcome.success,
        notes=outcome.notes or "",
        engineer_name=outcome.engineer_name,
        completed_at=outcome.completed_at
    )
    
    return OutcomeResponse(
        outcome_id=result.outcome_id,
        equipment_id=result.equipment_id,
        equipment_name=result.equipment_name,
        predicted_cause=result.predicted_cause,
        actual_cause=result.actual_cause,
        predicted_action=result.predicted_action,
        actual_action=result.actual_action,
        outcome=result.outcome.value,
        predicted_downtime_hours=result.predicted_downtime_hours,
        actual_downtime_hours=result.actual_downtime_hours,
        predicted_cost=result.predicted_cost,
        actual_cost=result.actual_cost,
        spare_parts_used=result.spare_parts_used,
        success=result.success,
        notes=result.notes,
        engineer_name=result.engineer_name,
        completed_at=result.completed_at,
        created_at=result.created_at
    )


@router.get("/outcomes", response_model=OutcomeListResponse)
async def get_outcomes(days: int = Query(30, ge=1, le=365)):
    """Get maintenance outcomes."""
    engine = get_feedback_engine()
    outcomes = engine.get_recent_outcomes(days)
    
    return OutcomeListResponse(
        outcomes=[
            OutcomeResponse(
                outcome_id=o.outcome_id,
                equipment_id=o.equipment_id,
                equipment_name=o.equipment_name,
                predicted_cause=o.predicted_cause,
                actual_cause=o.actual_cause,
                predicted_action=o.predicted_action,
                actual_action=o.actual_action,
                outcome=o.outcome.value,
                predicted_downtime_hours=o.predicted_downtime_hours,
                actual_downtime_hours=o.actual_downtime_hours,
                predicted_cost=o.predicted_cost,
                actual_cost=o.actual_cost,
                spare_parts_used=o.spare_parts_used,
                success=o.success,
                notes=o.notes,
                engineer_name=o.engineer_name,
                completed_at=o.completed_at,
                created_at=o.created_at
            )
            for o in outcomes
        ],
        total=len(outcomes)
    )


@router.get("/outcomes/summary", response_model=OutcomeSummaryResponse)
async def get_outcome_summary():
    """Get outcome summary statistics."""
    engine = get_feedback_engine()
    summary = engine.get_outcome_summary()
    
    return OutcomeSummaryResponse(**summary)


# ============ Performance Endpoints ============

@router.get("/performance/dashboard")
async def get_performance_dashboard():
    """Get performance dashboard data."""
    monitor = get_performance_monitor()
    dashboard = monitor.get_dashboard_summary()
    return dashboard


@router.get("/performance/trends", response_model=List[PerformanceTrendResponse])
async def get_performance_trends(days: int = Query(30, ge=1, le=365)):
    """Get performance trends."""
    monitor = get_performance_monitor()
    trends = monitor.get_all_trends(days)
    
    return [
        PerformanceTrendResponse(
            metric_name=t.metric_name,
            current_value=t.current_value,
            previous_value=t.previous_value,
            change=t.change,
            trend=t.trend,
            data_points=[
                {'timestamp': m.timestamp.isoformat(), 'value': m.value}
                for m in t.data_points
            ]
        )
        for t in trends
    ]


@router.get("/performance/models", response_model=List[ModelPerformanceResponse])
async def get_model_performance():
    """Get performance for all models."""
    scoring = get_scoring_engine()
    performance = scoring.get_all_performance()
    
    return [
        ModelPerformanceResponse(
            model_name=p.model_name,
            accuracy=p.accuracy,
            precision=p.precision,
            recall=p.recall,
            f1_score=p.f1_score,
            mae=p.mae,
            rmse=p.rmse,
            sample_count=p.sample_count,
            last_updated=p.last_updated
        )
        for p in performance
    ]


@router.get("/performance/recommendation-scores", response_model=List[RecommendationScoreResponse])
async def get_recommendation_scores():
    """Get recommendation scores."""
    scoring = get_scoring_engine()
    scores = scoring.get_all_scores()
    
    return [
        RecommendationScoreResponse(
            recommendation_type=s.recommendation_type,
            module_name=s.module_name,
            total_count=s.total_count,
            acceptance_count=s.acceptance_count,
            success_count=s.success_count,
            avg_effectiveness=s.avg_effectiveness,
            confidence_adjustment=s.confidence_adjustment,
            last_updated=s.last_updated
        )
        for s in scores
    ]


# ============ Retraining Endpoints ============

@router.get("/retraining/summary", response_model=RetrainingSummaryResponse)
async def get_retraining_summary():
    """Get retraining summary."""
    engine = get_retraining_engine()
    summary = engine.get_retraining_summary()
    
    return RetrainingSummaryResponse(**summary)


@router.get("/retraining/jobs", response_model=List[RetrainingJobResponse])
async def get_retraining_jobs(limit: int = Query(10, ge=1, le=50)):
    """Get recent retraining jobs."""
    engine = get_retraining_engine()
    jobs = engine.get_recent_jobs(limit)
    
    return [
        RetrainingJobResponse(
            job_id=j.job_id,
            model_name=j.model_name,
            status=j.status,
            trigger=j.trigger,
            started_at=j.started_at,
            completed_at=j.completed_at,
            old_version=j.old_version,
            new_version=j.new_version,
            old_accuracy=j.old_accuracy,
            new_accuracy=j.new_accuracy,
            improvement=j.improvement,
            samples_used=j.samples_used,
            error_message=j.error_message
        )
        for j in jobs
    ]


@router.post("/retraining/trigger")
async def trigger_retraining(model_name: str):
    """Trigger manual model retraining."""
    engine = get_retraining_engine()
    job = engine.create_retraining_job(model_name, trigger='manual')
    
    # In production, this would start an async job
    # For now, just return the job
    
    return {
        "status": "pending",
        "job_id": job.job_id,
        "model_name": job.model_name,
        "message": "Retraining job created and queued"
    }


# ============ Learning Summary Endpoints ============

@router.get("/summary", response_model=LearningSummaryResponse)
async def get_learning_summary(
    period: str = Query('monthly', pattern='^(weekly|monthly|quarterly)$'),
    days: int = Query(30, ge=7, le=365)
):
    """Generate learning summary."""
    engine = get_learning_summary_engine()
    summary = engine.generate_summary(period=period, days=days)
    
    return LearningSummaryResponse(
        summary_id=summary.summary_id,
        generated_at=summary.generated_at,
        period=summary.period,
        period_start=summary.period_start,
        period_end=summary.period_end,
        total_feedback=summary.total_feedback,
        positive_feedback=summary.positive_feedback,
        negative_feedback=summary.negative_feedback,
        acceptance_rate=summary.acceptance_rate,
        total_outcomes=summary.total_outcomes,
        success_rate=summary.success_rate,
        prediction_accuracy=summary.prediction_accuracy,
        average_accuracy=summary.average_accuracy,
        accuracy_change=summary.accuracy_change,
        models_improved=summary.models_improved,
        retraining_jobs=summary.retraining_jobs,
        models_retrained=summary.models_retrained,
        average_improvement=summary.average_improvement,
        top_improvements=summary.top_improvements,
        areas_of_concern=summary.areas_of_concern,
        recommendations=summary.recommendations,
        summary_text=summary.summary_text,
        detailed_report=summary.detailed_report
    )


@router.get("/summary/quick")
async def get_quick_summary():
    """Get quick summary for dashboard."""
    engine = get_learning_summary_engine()
    return engine.get_quick_summary()