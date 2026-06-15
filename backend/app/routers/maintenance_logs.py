"""Maintenance logs API endpoints."""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.models import MaintenanceLog
from app.schemas.schemas import (
    MaintenanceLogCreate, MaintenanceLogUpdate, MaintenanceLogResponse, PaginatedResponse
)

router = APIRouter(prefix="/api/maintenance-logs", tags=["Maintenance Logs"])


@router.post("/", response_model=MaintenanceLogResponse, status_code=201)
async def create_maintenance_log(
    log: MaintenanceLogCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new maintenance log entry."""
    db_log = MaintenanceLog(**log.model_dump())
    db.add(db_log)
    await db.flush()
    await db.refresh(db_log)
    return db_log


@router.get("/", response_model=list[MaintenanceLogResponse])
async def list_maintenance_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    equipment_name: Optional[str] = None,
    severity: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """List maintenance logs with optional filters."""
    query = select(MaintenanceLog)
    
    if equipment_name:
        query = query.where(MaintenanceLog.equipment_name.ilike(f"%{equipment_name}%"))
    if severity:
        query = query.where(MaintenanceLog.severity == severity)
    
    query = query.offset(skip).limit(limit).order_by(MaintenanceLog.maintenance_date.desc())
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{log_id}", response_model=MaintenanceLogResponse)
async def get_maintenance_log(
    log_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get maintenance log by ID."""
    query = select(MaintenanceLog).where(MaintenanceLog.log_id == log_id)
    result = await db.execute(query)
    log = result.scalar_one_or_none()
    
    if not log:
        raise HTTPException(status_code=404, detail="Maintenance log not found")
    
    return log


@router.put("/{log_id}", response_model=MaintenanceLogResponse)
async def update_maintenance_log(
    log_id: str,
    log_update: MaintenanceLogUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update maintenance log by ID."""
    query = select(MaintenanceLog).where(MaintenanceLog.log_id == log_id)
    result = await db.execute(query)
    log = result.scalar_one_or_none()
    
    if not log:
        raise HTTPException(status_code=404, detail="Maintenance log not found")
    
    update_data = log_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(log, field, value)
    
    await db.flush()
    await db.refresh(log)
    return log


@router.delete("/{log_id}", status_code=204)
async def delete_maintenance_log(
    log_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Delete maintenance log by ID."""
    query = select(MaintenanceLog).where(MaintenanceLog.log_id == log_id)
    result = await db.execute(query)
    log = result.scalar_one_or_none()
    
    if not log:
        raise HTTPException(status_code=404, detail="Maintenance log not found")
    
    await db.delete(log)
    return None


@router.get("/count/total")
async def count_maintenance_logs(db: AsyncSession = Depends(get_db)):
    """Get total maintenance logs count."""
    query = select(func.count()).select_from(MaintenanceLog)
    result = await db.execute(query)
    return {"count": result.scalar()}