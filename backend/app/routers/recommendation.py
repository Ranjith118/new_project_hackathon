"""Phase 6: Maintenance Recommendation Engine API."""
import uuid
from datetime import datetime
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.schemas.recommendation_schemas import (
    RecommendationRequest, RecommendationResponse, RecommendationItem,
    RepairGuideResponse, RepairStepResponse,
    MaintenanceScheduleResponse, MaintenanceTaskResponse,
    SparePartSetResponse, SpareRecommendationItem,
    MaintenancePlanRequest, CompleteMaintenancePlanResponse,
    RecommendationDashboardResponse, RecommendationSummary,
    MaintenanceReportRequest, MaintenanceReportResponse
)
from app.recommendation.recommendation_engine import get_recommendation_engine
from app.recommendation.repair_guide import get_repair_guide_generator
from app.recommendation.maintenance_planner import get_maintenance_planner
from app.recommendation.spare_recommender import get_spare_recommender

router = APIRouter(prefix="/api/recommendation", tags=["Phase 6 - Maintenance Recommendation"])


# ============ Recommendations ============

@router.post("", response_model=RecommendationResponse)
async def generate_recommendation(
    request: RecommendationRequest
):
    """
    Generate maintenance recommendations.
    
    Combines root cause, failure prediction, RUL, and health data
    to produce actionable maintenance recommendations.
    """
    engine = get_recommendation_engine()
    
    sensor_readings = {}
    if request.temperature is not None:
        sensor_readings['temperature'] = request.temperature
    if request.vibration is not None:
        sensor_readings['vibration'] = request.vibration
    if request.current is not None:
        sensor_readings['current'] = request.current
    if request.pressure is not None:
        sensor_readings['pressure'] = request.pressure
    if request.rpm is not None:
        sensor_readings['rpm'] = request.rpm
    
    result = engine.generate_recommendations(
        equipment_name=request.equipment,
        root_cause=request.root_cause,
        failure_probability=request.failure_probability,
        rul_days=request.rul_days,
        health_score=request.health_score,
        risk_level=request.risk_level,
        anomaly_detected=request.anomaly_detected,
        sensor_readings=sensor_readings if sensor_readings else None
    )
    
    # Convert to response format
    def to_recommendation_item(rec):
        return RecommendationItem(
            recommendation_id=rec.recommendation_id,
            equipment_name=rec.equipment_name,
            priority=rec.priority,
            category=rec.category,
            action=rec.action,
            reason=rec.reason,
            evidence=rec.evidence,
            references=rec.references,
            estimated_downtime_hours=rec.estimated_downtime_hours,
            estimated_cost=rec.estimated_cost
        )
    
    return RecommendationResponse(
        recommendation_id=result.recommendation_id,
        equipment_name=result.equipment_name,
        timestamp=result.timestamp,
        priority=result.priority,
        immediate_actions=[to_recommendation_item(r) for r in result.immediate_actions],
        repair_actions=[to_recommendation_item(r) for r in result.repair_actions],
        monitoring_actions=[to_recommendation_item(r) for r in result.monitoring_actions],
        preventive_actions=[to_recommendation_item(r) for r in result.preventive_actions],
        safety_actions=[to_recommendation_item(r) for r in result.safety_actions],
        overall_reason=result.overall_reason,
        confidence=result.confidence,
        estimated_total_downtime=result.estimated_total_downtime
    )


# ============ Repair Guides ============

@router.get("/repair-guide/{equipment_name}", response_model=RepairGuideResponse)
async def get_repair_guide(
    equipment_name: str,
    repair_type: str = Query("bearing_replacement")
):
    """
    Get step-by-step repair guide for equipment.
    
    Args:
        equipment_name: Name of equipment
        repair_type: Type of repair (bearing_replacement, cleaning, alignment, lubrication)
    """
    generator = get_repair_guide_generator()
    
    guide = generator.generate_repair_guide(
        equipment_name=equipment_name,
        repair_type=repair_type
    )
    
    return RepairGuideResponse(
        guide_id=guide.guide_id,
        equipment_name=guide.equipment_name,
        repair_type=guide.repair_type,
        estimated_total_time_minutes=guide.estimated_total_time_minutes,
        steps=[
            RepairStepResponse(
                step_number=s.step_number,
                action=s.action,
                description=s.description,
                estimated_time_minutes=s.estimated_time_minutes,
                safety_requirements=s.safety_requirements,
                tools_required=s.tools_required,
                source=s.source
            )
            for s in guide.steps
        ],
        required_parts=guide.required_parts,
        required_tools=guide.required_tools,
        safety_warnings=guide.safety_warnings,
        post_repair_checks=guide.post_repair_checks
    )


@router.get("/repair-types")
async def get_repair_types():
    """Get available repair types."""
    generator = get_repair_guide_generator()
    return {"types": generator.get_available_repair_types()}


# ============ Maintenance Schedule ============

@router.post("/schedule", response_model=MaintenanceScheduleResponse)
async def generate_maintenance_schedule(
    request: MaintenancePlanRequest
):
    """
    Generate preventive maintenance schedule.
    
    Creates optimized maintenance schedule based on
    equipment type and criticality.
    """
    planner = get_maintenance_planner()
    
    schedule = planner.generate_schedule(
        equipment_name=request.equipment,
        equipment_type=request.equipment_type or 'default',
        criticality=request.criticality,
        condition=request.condition
    )
    
    return MaintenanceScheduleResponse(
        schedule_id=schedule.schedule_id,
        equipment_name=schedule.equipment_name,
        created_at=schedule.created_at,
        tasks=[
            MaintenanceTaskResponse(
                task_id=t.task_id,
                task_name=t.task_name,
                description=t.description,
                frequency=t.frequency,
                estimated_duration_hours=t.estimated_duration_hours,
                priority=t.priority,
                skills_required=t.skills_required,
                parts_needed=t.parts_needed,
                estimated_cost=t.estimated_cost
            )
            for t in schedule.tasks
        ],
        total_weekly_hours=schedule.total_weekly_hours,
        total_monthly_hours=schedule.total_monthly_hours,
        estimated_annual_cost=schedule.estimated_annual_cost
    )


# ============ Spare Parts ============

@router.post("/spares", response_model=SparePartSetResponse)
async def recommend_spare_parts(
    equipment: str,
    equipment_type: str = Query("motor"),
    root_cause: Optional[str] = Query(None),
    failure_probability: Optional[float] = Query(None)
):
    """
    Generate spare parts recommendations.
    
    Args:
        equipment: Equipment name
        equipment_type: Type of equipment
        root_cause: Identified root cause
        failure_probability: Failure probability (0-1)
    """
    recommender = get_spare_recommender()
    
    result = recommender.recommend(
        equipment_name=equipment,
        equipment_type=equipment_type,
        root_cause=root_cause,
        failure_probability=failure_probability
    )
    
    return SparePartSetResponse(
        recommendation_id=result.recommendation_id,
        equipment_name=result.equipment_name,
        root_cause=result.root_cause,
        timestamp=result.timestamp,
        parts=[
            SpareRecommendationItem(
                part_id=p.part_id,
                part_name=p.part_name,
                part_number=p.part_number,
                quantity=p.quantity,
                urgency=p.urgency,
                lead_time_days=p.lead_time_days,
                estimated_cost=p.estimated_cost,
                supplier=p.supplier,
                reason=p.reason,
                source=p.source
            )
            for p in result.parts
        ],
        total_estimated_cost=result.total_estimated_cost,
        critical_parts=result.critical_parts
    )


# ============ Complete Maintenance Plan ============

@router.post("/complete-plan", response_model=CompleteMaintenancePlanResponse)
async def generate_complete_plan(
    request: RecommendationRequest
):
    """
    Generate complete maintenance plan including:
    - Recommendations
    - Repair guide
    - Maintenance schedule
    - Spare parts
    """
    rec_engine = get_recommendation_engine()
    repair_gen = get_repair_guide_generator()
    planner = get_maintenance_planner()
    spare_rec = get_spare_recommender()
    
    # Get recommendations
    sensor_readings = {}
    if request.temperature is not None:
        sensor_readings['temperature'] = request.temperature
    if request.vibration is not None:
        sensor_readings['vibration'] = request.vibration
    if request.current is not None:
        sensor_readings['current'] = request.current
    if request.pressure is not None:
        sensor_readings['pressure'] = request.pressure
    if request.rpm is not None:
        sensor_readings['rpm'] = request.rpm
    
    rec_result = rec_engine.generate_recommendations(
        equipment_name=request.equipment,
        root_cause=request.root_cause,
        failure_probability=request.failure_probability,
        rul_days=request.rul_days,
        health_score=request.health_score,
        risk_level=request.risk_level,
        anomaly_detected=request.anomaly_detected,
        sensor_readings=sensor_readings if sensor_readings else None
    )
    
    # Get repair guide
    repair_type = 'bearing_replacement'
    if request.root_cause:
        if 'bearing' in request.root_cause.lower():
            repair_type = 'bearing_replacement'
        elif 'pump' in request.root_cause.lower() or 'blockage' in request.root_cause.lower():
            repair_type = 'pump_cleaning'
        elif 'alignment' in request.root_cause.lower():
            repair_type = 'motor_alignment'
        elif 'lubrication' in request.root_cause.lower():
            repair_type = 'lubrication'
    
    repair_guide = repair_gen.generate_repair_guide(
        equipment_name=request.equipment,
        repair_type=repair_type,
        root_cause=request.root_cause
    )
    
    # Get maintenance schedule
    schedule = planner.generate_schedule(
        equipment_name=request.equipment,
        equipment_type=request.equipment_type or 'default',
        criticality='high' if request.risk_level == 'critical' else 'medium',
        condition='poor' if (request.health_score and request.health_score < 50) else 'fair'
    )
    
    # Get spare parts
    spares = spare_rec.recommend(
        equipment_name=request.equipment,
        equipment_type=request.equipment_type or 'default',
        root_cause=request.root_cause,
        failure_probability=request.failure_probability
    )
    
    # Calculate totals
    immediate_actions = [r.action for r in rec_result.immediate_actions]
    total_downtime = rec_result.estimated_total_downtime + (repair_guide.estimated_total_time_minutes / 60)
    total_cost = spares.total_estimated_cost
    
    return CompleteMaintenancePlanResponse(
        plan_id=str(uuid.uuid4()),
        equipment_name=request.equipment,
        timestamp=datetime.now(),
        priority=rec_result.priority,
        root_cause=request.root_cause,
        immediate_actions=immediate_actions,
        repair_guide=RepairGuideResponse(
            guide_id=repair_guide.guide_id,
            equipment_name=repair_guide.equipment_name,
            repair_type=repair_guide.repair_type,
            estimated_total_time_minutes=repair_guide.estimated_total_time_minutes,
            steps=[
                RepairStepResponse(
                    step_number=s.step_number,
                    action=s.action,
                    description=s.description,
                    estimated_time_minutes=s.estimated_time_minutes,
                    safety_requirements=s.safety_requirements,
                    tools_required=s.tools_required,
                    source=s.source
                )
                for s in repair_guide.steps
            ],
            required_parts=repair_guide.required_parts,
            required_tools=repair_guide.required_tools,
            safety_warnings=repair_guide.safety_warnings,
            post_repair_checks=repair_guide.post_repair_checks
        ),
        maintenance_schedule=MaintenanceScheduleResponse(
            schedule_id=schedule.schedule_id,
            equipment_name=schedule.equipment_name,
            created_at=schedule.created_at,
            tasks=[
                MaintenanceTaskResponse(
                    task_id=t.task_id,
                    task_name=t.task_name,
                    description=t.description,
                    frequency=t.frequency,
                    estimated_duration_hours=t.estimated_duration_hours,
                    priority=t.priority,
                    skills_required=t.skills_required,
                    parts_needed=t.parts_needed,
                    estimated_cost=t.estimated_cost
                )
                for t in schedule.tasks
            ],
            total_weekly_hours=schedule.total_weekly_hours,
            total_monthly_hours=schedule.total_monthly_hours,
            estimated_annual_cost=schedule.estimated_annual_cost
        ),
        spare_parts=SparePartSetResponse(
            recommendation_id=spares.recommendation_id,
            equipment_name=spares.equipment_name,
            root_cause=spares.root_cause,
            timestamp=spares.timestamp,
            parts=[
                SpareRecommendationItem(
                    part_id=p.part_id,
                    part_name=p.part_name,
                    part_number=p.part_number,
                    quantity=p.quantity,
                    urgency=p.urgency,
                    lead_time_days=p.lead_time_days,
                    estimated_cost=p.estimated_cost,
                    supplier=p.supplier,
                    reason=p.reason,
                    source=p.source
                )
                for p in spares.parts
            ],
            total_estimated_cost=spares.total_estimated_cost,
            critical_parts=spares.critical_parts
        ),
        estimated_total_downtime=round(total_downtime, 1),
        estimated_total_cost=total_cost,
        next_steps=[
            "Review immediate actions",
            "Schedule repair window",
            "Order spare parts",
            "Prepare work permits"
        ]
    )


# ============ Dashboard ============

@router.get("/dashboard", response_model=RecommendationDashboardResponse)
async def get_recommendation_dashboard():
    """
    Get recommendation dashboard summary.
    
    Returns counts by priority and list of recommendations.
    """
    # For demo, return mock data
    # In production, would query database for recent recommendations
    
    return RecommendationDashboardResponse(
        total_recommendations=12,
        p1_count=2,
        p2_count=4,
        p3_count=4,
        p4_count=2,
        recommendations=[
            RecommendationSummary(
                equipment_name="Rolling Mill Motor",
                priority="P1",
                root_cause="Bearing Wear",
                action_count=5,
                estimated_downtime=6.0
            ),
            RecommendationSummary(
                equipment_name="Cooling Pump A",
                priority="P2",
                root_cause="Pump Blockage",
                action_count=4,
                estimated_downtime=4.0
            )
        ],
        critical_equipment=["Rolling Mill Motor", "Main Compressor"]
    )


# ============ History ============

@router.get("/history")
async def get_recommendation_history(
    limit: int = Query(20, ge=1, le=100)
):
    """Get recommendation history."""
    # For demo, return empty list
    # In production, would query database
    return {"recommendations": [], "total": 0}