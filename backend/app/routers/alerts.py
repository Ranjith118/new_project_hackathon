"""Persistent alert storage and retrieval."""
import uuid
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.models import AlertRecord

router = APIRouter(prefix="/api/alerts", tags=["Alerts"])


def _fmt(r: AlertRecord) -> dict:
    """Serialize an AlertRecord to a dict the frontend expects."""
    ts = r.created_at.isoformat() if r.created_at else datetime.now().isoformat()
    return {
        "alert_id":        r.alert_id,
        "equipment_name":  r.equipment_name,
        "alert_type":      r.alert_type,
        "severity":        r.severity,
        "message":         r.message,
        "source":          r.source,
        "status":          r.status,
        "timestamp":       ts,   # frontend reads this field for display
        "created_at":      ts,
        "resolved_at":     r.resolved_at.isoformat() if r.resolved_at else None,
        "sensor_readings": {},   # enriched in list endpoint
    }


@router.get("")
async def get_alerts(
    status: Optional[str] = None,
    equipment_name: Optional[str] = None,
    limit: int = Query(100, le=500),
    db: AsyncSession = Depends(get_db),
):
    q = select(AlertRecord).order_by(desc(AlertRecord.created_at))
    if status:         q = q.where(AlertRecord.status == status)
    if equipment_name: q = q.where(AlertRecord.equipment_name.ilike(f"%{equipment_name}%"))
    q = q.limit(limit)
    rows = (await db.execute(q)).scalars().all()

    # Enrich with latest sensor readings per equipment
    from app.models.models import SensorData
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
    sensor_rows = (await db.execute(stmt)).scalars().all()
    sensor_map = {s.equipment_name: s for s in sensor_rows}

    alerts = []
    for r in rows:
        a = _fmt(r)
        s = sensor_map.get(r.equipment_name)
        if s:
            a["sensor_readings"] = {
                k: getattr(s, k) for k in ["temperature", "vibration", "current", "pressure", "rpm"]
                if getattr(s, k) is not None
            }
        alerts.append(a)

    active = [a for a in alerts if a["status"] == "active"]
    return {
        "alerts":         alerts,
        "total":          len(alerts),
        "active_count":   len(active),
        "critical_count": sum(1 for a in active if a["alert_type"] == "critical"),
    }


@router.post("")
async def create_alert(data: dict, db: AsyncSession = Depends(get_db)):
    now = datetime.now()
    row = AlertRecord(
        alert_id=       str(uuid.uuid4()),
        equipment_name= data.get("equipment_name", "Unknown"),
        alert_type=     data.get("alert_type", "medium"),
        severity=       data.get("severity", 2),
        message=        data.get("message", ""),
        source=         data.get("source", "threshold"),
        status=         "active",
        created_at=     now,
    )
    db.add(row)
    await db.flush()
    await db.refresh(row)
    return _fmt(row)


@router.patch("/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: str, db: AsyncSession = Depends(get_db)):
    row = (await db.execute(
        select(AlertRecord).where(AlertRecord.alert_id == alert_id)
    )).scalar_one_or_none()
    if not row:
        from fastapi import HTTPException
        raise HTTPException(404, "Alert not found")
    row.status = "acknowledged"
    await db.flush()
    await db.refresh(row)
    return _fmt(row)


@router.patch("/{alert_id}/resolve")
async def resolve_alert(alert_id: str, db: AsyncSession = Depends(get_db)):
    row = (await db.execute(
        select(AlertRecord).where(AlertRecord.alert_id == alert_id)
    )).scalar_one_or_none()
    if not row:
        from fastapi import HTTPException
        raise HTTPException(404, "Alert not found")
    row.status = "resolved"
    row.resolved_at = datetime.now()
    await db.flush()
    await db.refresh(row)
    return _fmt(row)


@router.get("/summary")
async def get_summary(db: AsyncSession = Depends(get_db)):
    total  = (await db.execute(select(func.count()).select_from(AlertRecord))).scalar() or 0
    active = (await db.execute(
        select(func.count()).select_from(AlertRecord)
        .where(AlertRecord.status == "active")
    )).scalar() or 0

    # Per-type counts for active alerts
    type_rows = (await db.execute(
        select(AlertRecord.alert_type, func.count().label("cnt"))
        .where(AlertRecord.status == "active")
        .group_by(AlertRecord.alert_type)
    )).all()
    by_type = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    for row in type_rows:
        if row.alert_type in by_type:
            by_type[row.alert_type] = row.cnt

    return {
        "total":          total,
        "active":         active,
        "critical_count": by_type["critical"],
        "by_type":        by_type,
    }
