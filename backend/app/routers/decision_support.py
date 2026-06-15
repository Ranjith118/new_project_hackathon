"""Phase 8: Plant-Level Prioritization & Decision Support API."""
import uuid
from datetime import datetime
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.schemas.decision_support_schemas import (
    CriticalityScoreResponse, CriticalitySummaryResponse,
    RiskScoreResponse, RiskSummaryResponse,
    MaintenancePriorityResponse, PrioritySummaryResponse,
    BottleneckResponse, BottleneckSummaryResponse,
    ScheduledMaintenanceResponse, MaintenanceScheduleResponse,
    ExecutiveSummaryResponse, ProductionImpactResponse,
    PlantHealthDashboardResponse, EquipmentRankingResponse,
    DecisionSummaryRequest
)
from app.decision_support.criticality_engine import get_criticality_engine
from app.decision_support.risk_engine import get_plant_risk_engine
from app.decision_support.prioritization_engine import get_prioritization_engine
from app.decision_support.bottleneck_engine import get_bottleneck_engine
from app.decision_support.scheduling_engine import get_scheduling_engine
from app.decision_support.executive_summary import get_executive_summary_engine

router = APIRouter(prefix="/api/decision-support", tags=["Phase 8 - Plant-Level Prioritization"])


# ── Shared helper: refresh risk engine from live sensor DB rows ──────────────
async def _refresh_risk_from_live_sensors(db: AsyncSession) -> None:
    """
    Read the latest sensor row per equipment from the DB, compute a health
    score, and feed those live values into the PlantRiskEngine singleton so
    that every downstream engine (prioritization, bottleneck, etc.) operates
    on current data rather than hardcoded defaults.
    """
    from app.models.models import SensorData
    from app.health.health_score import get_health_calculator
    import math, random

    risk_engine = get_plant_risk_engine()
    calc = get_health_calculator()

    # Equipment profiles kept in sync with sensor_data router
    EQUIPMENT_PROFILES = {
        "Rolling Mill Motor":    {"temperature": (65,115,90,"°C",95,110), "vibration":(0.5,5.0,1.8,"mm/s",2.8,4.0), "current":(18,32,22,"A",28,32),  "pressure":(70,95,80,"bar",90,95),   "rpm":(1400,2200,1500,"rpm",2000,2200)},
        "Blast Furnace Fan":     {"temperature": (50,95,72,"°C",85,93),   "vibration":(0.5,4.5,1.5,"mm/s",3.0,4.5), "current":(38,58,42,"A",52,58),   "pressure":(180,250,200,"mbar",230,248),"rpm":(940,1020,980,"rpm",1010,1020)},
        "Cooling Pump A":        {"temperature": (30,85,55,"°C",75,85),   "vibration":(0.3,3.5,1.0,"mm/s",2.5,3.5), "current":(20,35,27,"A",30,35),   "pressure":(30,55,42,"bar",50,54),   "rpm":(1400,1800,1600,"rpm",1750,1800)},
        "Main Compressor":       {"temperature": (60,100,78,"°C",90,100), "vibration":(0.5,4.0,1.6,"mm/s",2.8,4.0), "current":(30,60,45,"A",55,60),   "pressure":(5,12,8,"bar",11,12),     "rpm":(1450,1550,1500,"rpm",1530,1550)},
        "Conveyor Belt System":  {"temperature": (20,60,35,"°C",50,60),   "vibration":(0.2,2.5,0.8,"mm/s",2.0,2.5), "current":(10,25,16,"A",22,25),   "pressure":(2,8,4,"bar",7,8),        "rpm":(800,1200,1000,"rpm",1150,1200)},
    }
    DEFAULT_PROFILE = {
        "temperature":(40,100,70,"°C",90,100), "vibration":(0.5,4.0,1.5,"mm/s",3.0,4.0),
        "current":(15,35,22,"A",30,35),        "pressure":(2,10,6,"bar",9,10),
        "rpm":(900,1800,1200,"rpm",1700,1800),
    }

    # Name → canonical ID used by the criticality / risk engines
    NAME_TO_ID = {
        "Blast Furnace Fan":    "blast_furnace_fan",
        "Rolling Mill Motor":   "rolling_mill_motor",
        "Main Compressor":      "main_compressor",
        "Cooling Pump A":       "cooling_pump_a",
        "Conveyor Belt System": "conveyor_belt_system",
    }

    # Get latest row per equipment
    subq = (
        select(SensorData.equipment_name, func.max(SensorData.created_at).label("max_ca"))
        .group_by(SensorData.equipment_name)
        .subquery()
    )
    stmt = (
        select(SensorData)
        .join(subq, (SensorData.equipment_name == subq.c.equipment_name) &
                    (SensorData.created_at == subq.c.max_ca))
    )
    all_rows = (await db.execute(stmt)).scalars().all()

    if not all_rows:
        # No live data yet — fall back to defaults once
        if not risk_engine.risk_scores:
            risk_engine.calculate_all_from_defaults()
        return

    for row in all_rows:
        eq_name = row.equipment_name
        eq_id   = NAME_TO_ID.get(eq_name, eq_name.lower().replace(" ", "_"))

        # Build readings dict
        rdg = {}
        for k in ["temperature", "vibration", "current", "pressure", "rpm"]:
            v = getattr(row, k, None)
            if v is not None:
                rdg[k] = float(v)

        if not rdg:
            continue

        # Health score from live readings
        health = calc.calculate_score(rdg)
        health_score = health.score

        # Derive failure probability from health score + sensor thresholds
        profile = EQUIPMENT_PROFILES.get(eq_name, DEFAULT_PROFILE)
        penalty = 0
        for sensor_key, (lo, hi, normal, unit, warn, crit) in profile.items():
            val = rdg.get(sensor_key)
            if val is None:
                continue
            if val >= crit:
                penalty += 30
            elif val >= warn:
                penalty += 10
        failure_prob = min(0.99, max(0.01, (100 - health_score + penalty) / 100.0))

        # Derive RUL: healthier → more days remaining
        # Map health 0→100 to RUL ~3→120 days
        rul_days = max(3, int(health_score * 1.2))

        # Anomaly score: negative = anomalous
        anomaly_score = -1.0 * (failure_prob - 0.5) * 2  # range -1..1

        # Push into risk engine
        risk_engine.calculate_risk(
            equipment_id=eq_id,
            equipment_name=eq_name,
            equipment_type="motor",
            failure_probability=round(failure_prob, 4),
            rul_days=rul_days,
            health_score=health_score,
            anomaly_score=round(anomaly_score, 4),
        )

    # If some default equipment have no live sensor row, keep their last-known values
    # (calculate_all_from_defaults only fills equipment_ids not already present)
    for eq_id in get_criticality_engine().criticality_scores:
        if eq_id not in risk_engine.risk_scores:
            risk_engine.calculate_all_from_defaults()
            break


# ============ Criticality Endpoints ============

@router.get("/criticality", response_model=List[CriticalityScoreResponse])
async def get_all_criticality():
    """Get all equipment criticality scores."""
    engine = get_criticality_engine()
    scores = engine.get_all_criticality()
    
    return [
        CriticalityScoreResponse(
            equipment_id=c.equipment_id,
            equipment_name=c.equipment_name,
            equipment_type=c.equipment_type,
            criticality_score=c.criticality_score,
            criticality_level=c.criticality_level,
            factors=c.factors,
            production_dependency=c.production_dependency,
            safety_impact=c.safety_impact,
            environmental_impact=c.environmental_impact,
            downtime_cost=c.downtime_cost,
            replacement_difficulty=c.replacement_difficulty,
            last_updated=c.last_updated
        )
        for c in scores
    ]


@router.get("/criticality/summary", response_model=CriticalitySummaryResponse)
async def get_criticality_summary():
    """Get criticality summary statistics."""
    engine = get_criticality_engine()
    summary = engine.get_criticality_summary()
    
    return CriticalitySummaryResponse(**summary)


@router.get("/criticality/critical", response_model=List[CriticalityScoreResponse])
async def get_critical_equipment():
    """Get critical level equipment."""
    engine = get_criticality_engine()
    scores = engine.get_critical_equipment()
    
    return [
        CriticalityScoreResponse(
            equipment_id=c.equipment_id,
            equipment_name=c.equipment_name,
            equipment_type=c.equipment_type,
            criticality_score=c.criticality_score,
            criticality_level=c.criticality_level,
            factors=c.factors,
            production_dependency=c.production_dependency,
            safety_impact=c.safety_impact,
            environmental_impact=c.environmental_impact,
            downtime_cost=c.downtime_cost,
            replacement_difficulty=c.replacement_difficulty,
            last_updated=c.last_updated
        )
        for c in scores
    ]


# ============ Risk Endpoints ============

@router.get("/risk", response_model=List[RiskScoreResponse])
async def get_all_risks(db: AsyncSession = Depends(get_db)):
    """Get all equipment risk scores — refreshed from live sensor DB on every call."""
    engine = get_plant_risk_engine()
    await _refresh_risk_from_live_sensors(db)
    risks = engine.get_all_risks()
    
    return [
        RiskScoreResponse(
            equipment_id=r.equipment_id,
            equipment_name=r.equipment_name,
            equipment_type=r.equipment_type,
            risk_score=r.risk_score,
            risk_level=r.risk_level,
            failure_probability=r.failure_probability,
            rul_days=r.rul_days,
            health_score=r.health_score,
            anomaly_score=r.anomaly_score,
            criticality_score=r.criticality_score,
            components=r.components,
            reasons=r.reasons,
            last_updated=r.last_updated
        )
        for r in risks
    ]


@router.get("/risk/summary", response_model=RiskSummaryResponse)
async def get_risk_summary(db: AsyncSession = Depends(get_db)):
    """Get risk summary statistics."""
    engine = get_plant_risk_engine()
    await _refresh_risk_from_live_sensors(db)
    summary = engine.get_risk_summary()
    
    return RiskSummaryResponse(**summary)


@router.get("/risk/critical", response_model=List[RiskScoreResponse])
async def get_critical_risks(db: AsyncSession = Depends(get_db)):
    """Get critical risk equipment."""
    engine = get_plant_risk_engine()
    await _refresh_risk_from_live_sensors(db)
    risks = engine.get_critical_risks()
    
    return [
        RiskScoreResponse(
            equipment_id=r.equipment_id,
            equipment_name=r.equipment_name,
            equipment_type=r.equipment_type,
            risk_score=r.risk_score,
            risk_level=r.risk_level,
            failure_probability=r.failure_probability,
            rul_days=r.rul_days,
            health_score=r.health_score,
            anomaly_score=r.anomaly_score,
            criticality_score=r.criticality_score,
            components=r.components,
            reasons=r.reasons,
            last_updated=r.last_updated
        )
        for r in risks
    ]


# ============ Prioritization Endpoints ============

@router.get("/priorities", response_model=List[MaintenancePriorityResponse])
async def get_all_priorities(db: AsyncSession = Depends(get_db)):
    """Get all maintenance priorities."""
    risk_engine = get_plant_risk_engine()
    prio_engine = get_prioritization_engine()
    await _refresh_risk_from_live_sensors(db)
    risks = risk_engine.get_all_risks()
    priorities = prio_engine.prioritize(risks, {})
    
    return [
        MaintenancePriorityResponse(
            priority_id=p.priority_id,
            equipment_id=p.equipment_id,
            equipment_name=p.equipment_name,
            rank=p.rank,
            priority_score=p.priority_score,
            priority_level=p.priority_level,
            risk_score=p.risk_score,
            failure_probability=p.failure_probability,
            rul_days=p.rul_days,
            criticality=p.criticality,
            recommended_action=p.recommended_action,
            reason=p.reason,
            estimated_downtime=p.estimated_downtime,
            estimated_cost=p.estimated_cost,
            spare_available=p.spare_available,
            production_impact=p.production_impact,
            created_at=p.created_at
        )
        for p in priorities
    ]


@router.get("/priorities/summary", response_model=PrioritySummaryResponse)
async def get_priority_summary(db: AsyncSession = Depends(get_db)):
    """Get priority summary statistics."""
    risk_engine = get_plant_risk_engine()
    prio_engine = get_prioritization_engine()
    await _refresh_risk_from_live_sensors(db)
    risks = risk_engine.get_all_risks()
    prio_engine.prioritize(risks, {})
    
    summary = prio_engine.get_priority_summary()
    
    return PrioritySummaryResponse(**summary)


# ============ Bottleneck Endpoints ============

@router.get("/bottlenecks", response_model=List[BottleneckResponse])
async def get_all_bottlenecks():
    """Get all identified bottlenecks."""
    engine = get_bottleneck_engine()
    bottlenecks = engine.get_all_bottlenecks()
    
    return [
        BottleneckResponse(
            bottleneck_id=b.bottleneck_id,
            equipment_id=b.equipment_id,
            equipment_name=b.equipment_name,
            bottleneck_type=b.bottleneck_type,
            severity=b.severity,
            reason=b.reason,
            impact=b.impact,
            affected_systems=b.affected_systems,
            risk_score=b.risk_score,
            mitigation_options=b.mitigation_options,
            created_at=b.created_at
        )
        for b in bottlenecks
    ]


@router.get("/bottlenecks/summary", response_model=BottleneckSummaryResponse)
async def get_bottleneck_summary():
    """Get bottleneck summary statistics."""
    engine = get_bottleneck_engine()
    summary = engine.get_bottleneck_summary()
    
    return BottleneckSummaryResponse(**summary)


@router.get("/bottlenecks/critical", response_model=List[BottleneckResponse])
async def get_critical_bottlenecks():
    """Get critical severity bottlenecks."""
    engine = get_bottleneck_engine()
    bottlenecks = engine.get_critical_bottlenecks()
    
    return [
        BottleneckResponse(
            bottleneck_id=b.bottleneck_id,
            equipment_id=b.equipment_id,
            equipment_name=b.equipment_name,
            bottleneck_type=b.bottleneck_type,
            severity=b.severity,
            reason=b.reason,
            impact=b.impact,
            affected_systems=b.affected_systems,
            risk_score=b.risk_score,
            mitigation_options=b.mitigation_options,
            created_at=b.created_at
        )
        for b in bottlenecks
    ]


# ============ Schedule Endpoints ============

@router.post("/schedule", response_model=MaintenanceScheduleResponse)
async def generate_schedule(
    max_daily_downtime: float = Query(8.0),
    available_technicians: int = Query(5),
    db: AsyncSession = Depends(get_db)
):
    """Generate optimized maintenance schedule."""
    risk_engine = get_plant_risk_engine()
    prio_engine = get_prioritization_engine()
    sched_engine = get_scheduling_engine()
    await _refresh_risk_from_live_sensors(db)
    risks = risk_engine.get_all_risks()
    priorities = prio_engine.prioritize(risks, {})
    
    schedule = sched_engine.generate_schedule(
        priorities=priorities,
        max_daily_downtime=max_daily_downtime,
        available_technicians=available_technicians
    )
    
    return MaintenanceScheduleResponse(
        schedule_id=schedule.schedule_id,
        week_start=schedule.week_start,
        created_at=schedule.created_at,
        tasks=[
            ScheduledMaintenanceResponse(
                schedule_id=t.schedule_id,
                equipment_id=t.equipment_id,
                equipment_name=t.equipment_name,
                maintenance_type=t.maintenance_type,
                scheduled_date=t.scheduled_date,
                priority=t.priority,
                estimated_duration_hours=t.estimated_duration_hours,
                estimated_downtime=t.estimated_downtime,
                technicians_required=t.technicians_required,
                parts_needed=t.parts_needed,
                prerequisites=t.prerequisites,
                status=t.status,
                notes=t.notes
            )
            for t in schedule.tasks
        ],
        total_tasks=schedule.total_tasks,
        total_downtime_hours=schedule.total_downtime_hours,
        production_impact=schedule.production_impact,
        summary=schedule.summary
    )


@router.get("/schedule/latest", response_model=MaintenanceScheduleResponse)
async def get_latest_schedule():
    """Get the most recent maintenance schedule."""
    engine = get_scheduling_engine()
    schedule = engine.get_latest_schedule()
    
    if not schedule:
        raise HTTPException(status_code=404, detail="No schedule generated yet")
    
    return MaintenanceScheduleResponse(
        schedule_id=schedule.schedule_id,
        week_start=schedule.week_start,
        created_at=schedule.created_at,
        tasks=[
            ScheduledMaintenanceResponse(
                schedule_id=t.schedule_id,
                equipment_id=t.equipment_id,
                equipment_name=t.equipment_name,
                maintenance_type=t.maintenance_type,
                scheduled_date=t.scheduled_date,
                priority=t.priority,
                estimated_duration_hours=t.estimated_duration_hours,
                estimated_downtime=t.estimated_downtime,
                technicians_required=t.technicians_required,
                parts_needed=t.parts_needed,
                prerequisites=t.prerequisites,
                status=t.status,
                notes=t.notes
            )
            for t in schedule.tasks
        ],
        total_tasks=schedule.total_tasks,
        total_downtime_hours=schedule.total_downtime_hours,
        production_impact=schedule.production_impact,
        summary=schedule.summary
    )


# ============ Executive Summary Endpoints ============

@router.post("/summary", response_model=ExecutiveSummaryResponse)
async def generate_summary(request: DecisionSummaryRequest):
    """Generate executive summary."""
    engine = get_executive_summary_engine()
    
    summary = engine.generate_summary(
        plant_name=request.plant_name,
        include_detailed=request.include_detailed
    )
    
    return ExecutiveSummaryResponse(
        summary_id=summary.summary_id,
        generated_at=summary.generated_at,
        plant_name=summary.plant_name,
        plant_health_score=summary.plant_health_score,
        critical_equipment_count=summary.critical_equipment_count,
        immediate_actions=summary.immediate_actions,
        short_term_actions=summary.short_term_actions,
        medium_term_actions=summary.medium_term_actions,
        key_insights=summary.key_insights,
        risks=summary.risks,
        recommendations=summary.recommendations,
        summary_text=summary.summary_text,
        detailed_report=summary.detailed_report
    )


# ============ Plant Health Dashboard ============

@router.get("/plant-health", response_model=PlantHealthDashboardResponse)
async def get_plant_health_dashboard(db: AsyncSession = Depends(get_db)):
    """Get complete plant health dashboard data."""
    criticality = get_criticality_engine()
    risk_engine = get_plant_risk_engine()
    prio_engine = get_prioritization_engine()
    await _refresh_risk_from_live_sensors(db)
    
    risk_summary = risk_engine.get_risk_summary()
    criticality_summary = criticality.get_criticality_summary()
    
    risks = risk_engine.get_all_risks()
    prio_engine.prioritize(risks, {})
    priority_summary = prio_engine.get_priority_summary()
    
    return PlantHealthDashboardResponse(
        plant_health_score=100 - (risk_summary.get('average_risk', 50)),
        total_equipment=risk_summary.get('total_equipment', 0),
        critical_count=risk_summary.get('critical_count', 0),
        high_count=risk_summary.get('high_count', 0),
        active_alerts=risk_summary.get('critical_count', 0) + risk_summary.get('high_count', 0),
        maintenance_backlog=priority_summary.get('p1_count', 0) + priority_summary.get('p2_count', 0),
        criticality_summary=CriticalitySummaryResponse(**criticality_summary),
        risk_summary=RiskSummaryResponse(**risk_summary),
        priority_summary=PrioritySummaryResponse(**priority_summary)
    )


# ============ Equipment Ranking ============

@router.get("/equipment-ranking", response_model=EquipmentRankingResponse)
async def get_equipment_ranking(
    limit: int = Query(20, ge=1, le=50),
    db: AsyncSession = Depends(get_db)
):
    """Get equipment ranking by priority — live sensor data drives the scores."""
    risk_engine = get_plant_risk_engine()
    prio_engine = get_prioritization_engine()
    await _refresh_risk_from_live_sensors(db)
    risks = risk_engine.get_all_risks()
    priorities = prio_engine.prioritize(risks, {})
    
    return EquipmentRankingResponse(
        rankings=[
            MaintenancePriorityResponse(
                priority_id=p.priority_id,
                equipment_id=p.equipment_id,
                equipment_name=p.equipment_name,
                rank=p.rank,
                priority_score=p.priority_score,
                priority_level=p.priority_level,
                risk_score=p.risk_score,
                failure_probability=p.failure_probability,
                rul_days=p.rul_days,
                criticality=p.criticality,
                recommended_action=p.recommended_action,
                reason=p.reason,
                estimated_downtime=p.estimated_downtime,
                estimated_cost=p.estimated_cost,
                spare_available=p.spare_available,
                production_impact=p.production_impact,
                created_at=p.created_at
            )
            for p in priorities[:limit]
        ],
        total=len(priorities)
    )