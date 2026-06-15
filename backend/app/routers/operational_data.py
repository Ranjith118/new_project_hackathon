"""
Operational & Failure Data Management — unified router.
Covers: Delay Logs, Fault Logs, Incident Records, Breakdown History, Analytics.
"""
import uuid
from collections import defaultdict
from datetime import datetime, date, timedelta
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select, func, desc, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.models import DelayLog, FaultLog, IncidentRecord, BreakdownRecord

router = APIRouter(prefix="/api/operational", tags=["Operational Data"])


# ─────────────────────────────────────────────────────────────
# SCHEMAS
# ─────────────────────────────────────────────────────────────

class DelayLogCreate(BaseModel):
    equipment_name: str
    delay_start: datetime
    delay_end: Optional[datetime] = None
    delay_duration_min: Optional[float] = None
    delay_category: str
    production_impact: str = "low"
    reason: str
    operator_notes: Optional[str] = None
    status: str = "open"
    reported_by: Optional[str] = None

class FaultLogCreate(BaseModel):
    equipment_name: str
    fault_code: Optional[str] = None
    error_message: str
    fault_description: Optional[str] = None
    severity: str
    fault_timestamp: datetime
    status: str = "active"
    acknowledged_by: Optional[str] = None
    resolution_notes: Optional[str] = None

class IncidentCreate(BaseModel):
    equipment_name: str
    incident_type: str
    description: str
    incident_date: date
    severity: str
    affected_area: Optional[str] = None
    reported_by: Optional[str] = None
    corrective_action: Optional[str] = None
    preventive_action: Optional[str] = None
    status: str = "open"

class BreakdownCreate(BaseModel):
    equipment_name: str
    failure_type: str
    breakdown_date: date
    downtime_hours: float = 0.0
    repair_time_hours: Optional[float] = None
    root_cause: Optional[str] = None
    failure_description: str
    corrective_action: Optional[str] = None
    preventive_action: Optional[str] = None
    repair_cost: Optional[float] = None
    technician: Optional[str] = None
    parts_replaced: Optional[str] = None


# ─────────────────────────────────────────────────────────────
# DELAY LOGS
# ─────────────────────────────────────────────────────────────

@router.post("/delays", status_code=201)
async def create_delay(data: DelayLogCreate, db: AsyncSession = Depends(get_db)):
    # Auto-calc duration if both times given
    dur = data.delay_duration_min
    if dur is None and data.delay_end:
        dur = (data.delay_end - data.delay_start).total_seconds() / 60

    idx = await db.execute(select(func.count()).select_from(DelayLog))
    n = (idx.scalar() or 0) + 1
    code = f"DL{n:04d}"

    row = DelayLog(
        delay_code=code,
        equipment_name=data.equipment_name,
        delay_start=data.delay_start,
        delay_end=data.delay_end,
        delay_duration_min=dur,
        delay_category=data.delay_category,
        production_impact=data.production_impact,
        reason=data.reason,
        operator_notes=data.operator_notes,
        status=data.status,
        reported_by=data.reported_by,
    )
    db.add(row); await db.flush(); await db.refresh(row)
    return _delay_dict(row)

@router.get("/delays")
async def list_delays(
    equipment_name: Optional[str] = None,
    status: Optional[str] = None,
    category: Optional[str] = None,
    limit: int = Query(100, le=500),
    db: AsyncSession = Depends(get_db)
):
    q = select(DelayLog).order_by(desc(DelayLog.delay_start))
    if equipment_name: q = q.where(DelayLog.equipment_name.ilike(f"%{equipment_name}%"))
    if status:         q = q.where(DelayLog.status == status)
    if category:       q = q.where(DelayLog.delay_category == category)
    q = q.limit(limit)
    rows = (await db.execute(q)).scalars().all()
    return [_delay_dict(r) for r in rows]

@router.patch("/delays/{delay_id}")
async def update_delay(delay_id: str, data: dict, db: AsyncSession = Depends(get_db)):
    row = (await db.execute(select(DelayLog).where(DelayLog.delay_id == delay_id))).scalar_one_or_none()
    if not row: raise HTTPException(404, "Delay log not found")
    for k, v in data.items():
        if hasattr(row, k): setattr(row, k, v)
    await db.flush(); await db.refresh(row)
    return _delay_dict(row)

@router.delete("/delays/{delay_id}", status_code=204)
async def delete_delay(delay_id: str, db: AsyncSession = Depends(get_db)):
    row = (await db.execute(select(DelayLog).where(DelayLog.delay_id == delay_id))).scalar_one_or_none()
    if not row: raise HTTPException(404, "Not found")
    await db.delete(row)

def _delay_dict(r: DelayLog):
    return {
        "delay_id": r.delay_id, "delay_code": r.delay_code,
        "equipment_name": r.equipment_name,
        "delay_start": r.delay_start.isoformat() if r.delay_start else None,
        "delay_end": r.delay_end.isoformat() if r.delay_end else None,
        "delay_duration_min": r.delay_duration_min,
        "delay_category": r.delay_category, "production_impact": r.production_impact,
        "reason": r.reason, "operator_notes": r.operator_notes,
        "status": r.status, "reported_by": r.reported_by,
        "created_at": r.created_at.isoformat() if r.created_at else None,
    }


# ─────────────────────────────────────────────────────────────
# FAULT LOGS
# ─────────────────────────────────────────────────────────────

@router.post("/faults", status_code=201)
async def create_fault(data: FaultLogCreate, db: AsyncSession = Depends(get_db)):
    idx = await db.execute(select(func.count()).select_from(FaultLog))
    n = (idx.scalar() or 0) + 1
    auto_code = data.fault_code or f"FLT{n:04d}"
    row = FaultLog(
        fault_code=auto_code,
        equipment_name=data.equipment_name,
        error_message=data.error_message,
        fault_description=data.fault_description,
        severity=data.severity,
        fault_timestamp=data.fault_timestamp,
        status=data.status,
        acknowledged_by=data.acknowledged_by,
        resolution_notes=data.resolution_notes,
    )
    db.add(row); await db.flush(); await db.refresh(row)
    return _fault_dict(row)

@router.get("/faults")
async def list_faults(
    equipment_name: Optional[str] = None,
    severity: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = Query(100, le=500),
    db: AsyncSession = Depends(get_db)
):
    q = select(FaultLog).order_by(desc(FaultLog.fault_timestamp))
    if equipment_name: q = q.where(FaultLog.equipment_name.ilike(f"%{equipment_name}%"))
    if severity:       q = q.where(FaultLog.severity == severity)
    if status:         q = q.where(FaultLog.status == status)
    q = q.limit(limit)
    rows = (await db.execute(q)).scalars().all()
    return [_fault_dict(r) for r in rows]

@router.patch("/faults/{fault_id}")
async def update_fault(fault_id: str, data: dict, db: AsyncSession = Depends(get_db)):
    row = (await db.execute(select(FaultLog).where(FaultLog.fault_id == fault_id))).scalar_one_or_none()
    if not row: raise HTTPException(404, "Fault log not found")
    for k, v in data.items():
        if hasattr(row, k): setattr(row, k, v)
    await db.flush(); await db.refresh(row)
    return _fault_dict(row)

@router.delete("/faults/{fault_id}", status_code=204)
async def delete_fault(fault_id: str, db: AsyncSession = Depends(get_db)):
    row = (await db.execute(select(FaultLog).where(FaultLog.fault_id == fault_id))).scalar_one_or_none()
    if not row: raise HTTPException(404, "Not found")
    await db.delete(row)

def _fault_dict(r: FaultLog):
    return {
        "fault_id": r.fault_id, "fault_code": r.fault_code,
        "equipment_name": r.equipment_name, "error_message": r.error_message,
        "fault_description": r.fault_description, "severity": r.severity,
        "fault_timestamp": r.fault_timestamp.isoformat() if r.fault_timestamp else None,
        "status": r.status, "acknowledged_by": r.acknowledged_by,
        "resolution_notes": r.resolution_notes,
        "created_at": r.created_at.isoformat() if r.created_at else None,
    }


# ─────────────────────────────────────────────────────────────
# INCIDENT RECORDS
# ─────────────────────────────────────────────────────────────

@router.post("/incidents", status_code=201)
async def create_incident(data: IncidentCreate, db: AsyncSession = Depends(get_db)):
    idx = await db.execute(select(func.count()).select_from(IncidentRecord))
    n = (idx.scalar() or 0) + 1
    row = IncidentRecord(
        incident_code=f"INC{n:04d}",
        equipment_name=data.equipment_name,
        incident_type=data.incident_type,
        description=data.description,
        incident_date=data.incident_date,
        severity=data.severity,
        affected_area=data.affected_area,
        reported_by=data.reported_by,
        corrective_action=data.corrective_action,
        preventive_action=data.preventive_action,
        status=data.status,
    )
    db.add(row); await db.flush(); await db.refresh(row)
    return _incident_dict(row)

@router.get("/incidents")
async def list_incidents(
    equipment_name: Optional[str] = None,
    severity: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = Query(100, le=500),
    db: AsyncSession = Depends(get_db)
):
    q = select(IncidentRecord).order_by(desc(IncidentRecord.incident_date))
    if equipment_name: q = q.where(IncidentRecord.equipment_name.ilike(f"%{equipment_name}%"))
    if severity:       q = q.where(IncidentRecord.severity == severity)
    if status:         q = q.where(IncidentRecord.status == status)
    q = q.limit(limit)
    rows = (await db.execute(q)).scalars().all()
    return [_incident_dict(r) for r in rows]

@router.patch("/incidents/{incident_id}")
async def update_incident(incident_id: str, data: dict, db: AsyncSession = Depends(get_db)):
    row = (await db.execute(select(IncidentRecord).where(IncidentRecord.incident_id == incident_id))).scalar_one_or_none()
    if not row: raise HTTPException(404, "Incident not found")
    for k, v in data.items():
        if hasattr(row, k): setattr(row, k, v)
    await db.flush(); await db.refresh(row)
    return _incident_dict(row)

@router.delete("/incidents/{incident_id}", status_code=204)
async def delete_incident(incident_id: str, db: AsyncSession = Depends(get_db)):
    row = (await db.execute(select(IncidentRecord).where(IncidentRecord.incident_id == incident_id))).scalar_one_or_none()
    if not row: raise HTTPException(404, "Not found")
    await db.delete(row)

def _incident_dict(r: IncidentRecord):
    return {
        "incident_id": r.incident_id, "incident_code": r.incident_code,
        "equipment_name": r.equipment_name, "incident_type": r.incident_type,
        "description": r.description,
        "incident_date": r.incident_date.isoformat() if r.incident_date else None,
        "severity": r.severity, "affected_area": r.affected_area,
        "reported_by": r.reported_by, "corrective_action": r.corrective_action,
        "preventive_action": r.preventive_action, "status": r.status,
        "created_at": r.created_at.isoformat() if r.created_at else None,
    }


# ─────────────────────────────────────────────────────────────
# BREAKDOWN HISTORY
# ─────────────────────────────────────────────────────────────

@router.post("/breakdowns", status_code=201)
async def create_breakdown(data: BreakdownCreate, db: AsyncSession = Depends(get_db)):
    idx = await db.execute(select(func.count()).select_from(BreakdownRecord))
    n = (idx.scalar() or 0) + 1
    row = BreakdownRecord(
        breakdown_code=f"BD{n:04d}",
        equipment_name=data.equipment_name,
        failure_type=data.failure_type,
        breakdown_date=data.breakdown_date,
        downtime_hours=data.downtime_hours,
        repair_time_hours=data.repair_time_hours,
        root_cause=data.root_cause,
        failure_description=data.failure_description,
        corrective_action=data.corrective_action,
        preventive_action=data.preventive_action,
        repair_cost=data.repair_cost,
        technician=data.technician,
        parts_replaced=data.parts_replaced,
    )
    db.add(row); await db.flush(); await db.refresh(row)
    return _breakdown_dict(row)

@router.get("/breakdowns")
async def list_breakdowns(
    equipment_name: Optional[str] = None,
    failure_type: Optional[str] = None,
    limit: int = Query(100, le=500),
    db: AsyncSession = Depends(get_db)
):
    q = select(BreakdownRecord).order_by(desc(BreakdownRecord.breakdown_date))
    if equipment_name: q = q.where(BreakdownRecord.equipment_name.ilike(f"%{equipment_name}%"))
    if failure_type:   q = q.where(BreakdownRecord.failure_type.ilike(f"%{failure_type}%"))
    q = q.limit(limit)
    rows = (await db.execute(q)).scalars().all()
    return [_breakdown_dict(r) for r in rows]

@router.patch("/breakdowns/{breakdown_id}")
async def update_breakdown(breakdown_id: str, data: dict, db: AsyncSession = Depends(get_db)):
    row = (await db.execute(select(BreakdownRecord).where(BreakdownRecord.breakdown_id == breakdown_id))).scalar_one_or_none()
    if not row: raise HTTPException(404, "Breakdown not found")
    for k, v in data.items():
        if hasattr(row, k): setattr(row, k, v)
    await db.flush(); await db.refresh(row)
    return _breakdown_dict(row)

@router.delete("/breakdowns/{breakdown_id}", status_code=204)
async def delete_breakdown(breakdown_id: str, db: AsyncSession = Depends(get_db)):
    row = (await db.execute(select(BreakdownRecord).where(BreakdownRecord.breakdown_id == breakdown_id))).scalar_one_or_none()
    if not row: raise HTTPException(404, "Not found")
    await db.delete(row)

def _breakdown_dict(r: BreakdownRecord):
    return {
        "breakdown_id": r.breakdown_id, "breakdown_code": r.breakdown_code,
        "equipment_name": r.equipment_name, "failure_type": r.failure_type,
        "breakdown_date": r.breakdown_date.isoformat() if r.breakdown_date else None,
        "downtime_hours": r.downtime_hours, "repair_time_hours": r.repair_time_hours,
        "root_cause": r.root_cause, "failure_description": r.failure_description,
        "corrective_action": r.corrective_action, "preventive_action": r.preventive_action,
        "repair_cost": r.repair_cost, "technician": r.technician,
        "parts_replaced": r.parts_replaced,
        "created_at": r.created_at.isoformat() if r.created_at else None,
    }


# ─────────────────────────────────────────────────────────────
# ANALYTICS DASHBOARD
# ─────────────────────────────────────────────────────────────

@router.get("/analytics")
async def get_analytics(db: AsyncSession = Depends(get_db)):
    """Aggregated analytics across all operational data."""

    # Counts
    delay_count    = (await db.execute(select(func.count()).select_from(DelayLog))).scalar() or 0
    fault_count    = (await db.execute(select(func.count()).select_from(FaultLog))).scalar() or 0
    incident_count = (await db.execute(select(func.count()).select_from(IncidentRecord))).scalar() or 0
    breakdown_count= (await db.execute(select(func.count()).select_from(BreakdownRecord))).scalar() or 0

    # Total downtime from breakdowns
    total_downtime = (await db.execute(select(func.sum(BreakdownRecord.downtime_hours)).select_from(BreakdownRecord))).scalar() or 0

    # Total delay minutes
    total_delay_min = (await db.execute(select(func.sum(DelayLog.delay_duration_min)).select_from(DelayLog))).scalar() or 0

    # Top equipment by breakdown count
    bd_by_eq = (await db.execute(
        select(BreakdownRecord.equipment_name, func.count().label("cnt"))
        .group_by(BreakdownRecord.equipment_name).order_by(desc("cnt")).limit(8)
    )).all()

    # Top equipment by total downtime
    dt_by_eq = (await db.execute(
        select(BreakdownRecord.equipment_name, func.sum(BreakdownRecord.downtime_hours).label("total_dt"))
        .group_by(BreakdownRecord.equipment_name).order_by(desc("total_dt")).limit(8)
    )).all()

    # Failure type frequency
    ft_freq = (await db.execute(
        select(BreakdownRecord.failure_type, func.count().label("cnt"))
        .group_by(BreakdownRecord.failure_type).order_by(desc("cnt")).limit(10)
    )).all()

    # Fault severity breakdown
    sev_counts = (await db.execute(
        select(FaultLog.severity, func.count().label("cnt"))
        .group_by(FaultLog.severity)
    )).all()

    # Delay category breakdown
    cat_counts = (await db.execute(
        select(DelayLog.delay_category, func.count().label("cnt"))
        .group_by(DelayLog.delay_category)
    )).all()

    # Most delayed equipment
    delay_by_eq = (await db.execute(
        select(DelayLog.equipment_name, func.sum(DelayLog.delay_duration_min).label("total_min"))
        .group_by(DelayLog.equipment_name).order_by(desc("total_min")).limit(8)
    )).all()

    # Monthly breakdown trend (last 6 months)
    six_months_ago = date.today() - timedelta(days=180)
    monthly_rows = (await db.execute(
        select(BreakdownRecord.breakdown_date, func.count().label("cnt"))
        .where(BreakdownRecord.breakdown_date >= six_months_ago)
        .group_by(BreakdownRecord.breakdown_date)
        .order_by(BreakdownRecord.breakdown_date)
    )).all()
    monthly: dict = defaultdict(int)
    for row in monthly_rows:
        month = row.breakdown_date.strftime("%Y-%m")
        monthly[month] += row.cnt
    monthly_trend = [{"month": k, "count": v} for k, v in sorted(monthly.items())]

    return {
        "summary": {
            "total_delays": delay_count,
            "total_faults": fault_count,
            "total_incidents": incident_count,
            "total_breakdowns": breakdown_count,
            "total_downtime_hours": round(total_downtime, 1),
            "total_delay_minutes": round(total_delay_min, 1),
        },
        "top_breakdown_equipment": [{"equipment": r.equipment_name, "count": r.cnt} for r in bd_by_eq],
        "top_downtime_equipment":  [{"equipment": r.equipment_name, "downtime_hours": round(r.total_dt, 1)} for r in dt_by_eq],
        "failure_type_frequency":  [{"type": r.failure_type, "count": r.cnt} for r in ft_freq],
        "fault_severity_counts":   [{"severity": r.severity, "count": r.cnt} for r in sev_counts],
        "delay_category_counts":   [{"category": r.delay_category, "count": r.cnt} for r in cat_counts],
        "most_delayed_equipment":  [{"equipment": r.equipment_name, "total_minutes": round(r.total_min, 1)} for r in delay_by_eq],
        "monthly_breakdown_trend": monthly_trend,
    }


# ─────────────────────────────────────────────────────────────
# AI INSIGHTS
# ─────────────────────────────────────────────────────────────

@router.get("/ai-insights")
async def get_ai_insights(db: AsyncSession = Depends(get_db)):
    """Generate AI-powered insights from operational history."""
    from app.config import settings
    try:
        from groq import Groq
    except ImportError:
        return {"insights": ["Groq not installed. Run: pip install groq"]}

    # Gather summary stats for the prompt
    bd_rows = (await db.execute(
        select(BreakdownRecord).order_by(desc(BreakdownRecord.breakdown_date)).limit(50)
    )).scalars().all()

    fault_rows = (await db.execute(
        select(FaultLog).order_by(desc(FaultLog.fault_timestamp)).limit(30)
    )).scalars().all()

    delay_rows = (await db.execute(
        select(DelayLog).order_by(desc(DelayLog.delay_start)).limit(30)
    )).scalars().all()

    # Build compact context
    lines = ["=== RECENT BREAKDOWNS ==="]
    for r in bd_rows[:20]:
        lines.append(f"- {r.equipment_name} | {r.failure_type} | {r.breakdown_date} | Downtime: {r.downtime_hours}h | Cause: {r.root_cause or 'Unknown'}")

    lines.append("\n=== RECENT FAULTS ===")
    for r in fault_rows[:15]:
        lines.append(f"- {r.equipment_name} | {r.fault_code} | {r.severity} | {r.error_message}")

    lines.append("\n=== RECENT DELAYS ===")
    for r in delay_rows[:10]:
        lines.append(f"- {r.equipment_name} | {r.delay_category} | {r.delay_duration_min}min | {r.reason}")

    context = "\n".join(lines)

    prompt = f"""You are a Senior Reliability Engineer analyzing operational data from a steel manufacturing plant.
Based on the following historical data, generate 5-7 specific, actionable AI insights about:
- Recurring failures and patterns
- Equipment with highest failure frequency
- Downtime trends
- Common root causes
- Recommendations

Data:
{context}

Return ONLY a JSON array of insight strings. Example:
["insight 1", "insight 2", ...]
Keep each insight under 120 characters. Be specific with equipment names and numbers."""

    try:
        client = Groq(api_key=settings.GROQ_API_KEY)
        resp = client.chat.completions.create(
            model=settings.LLM_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3, max_tokens=600,
        )
        raw = resp.choices[0].message.content.strip()
        if "```" in raw:
            raw = raw.split("```")[1].replace("json", "").strip()
        import json
        insights = json.loads(raw)
        return {"insights": insights}
    except Exception as e:
        return {"insights": [f"Could not generate insights: {str(e)}"]}
