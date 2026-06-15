"""Failure reports API endpoints."""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.models import FailureReport
from app.schemas.schemas import (
    FailureReportCreate, FailureReportUpdate, FailureReportResponse
)

router = APIRouter(prefix="/api/failure-reports", tags=["Failure Reports"])


@router.post("/", response_model=FailureReportResponse, status_code=201)
async def create_failure_report(
    report: FailureReportCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new failure report."""
    db_report = FailureReport(**report.model_dump())
    db.add(db_report)
    await db.flush()
    await db.refresh(db_report)
    return db_report


@router.get("/", response_model=list[FailureReportResponse])
async def list_failure_reports(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    equipment_name: Optional[str] = None,
    failure_type: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """List failure reports with optional filters."""
    query = select(FailureReport)
    
    if equipment_name:
        query = query.where(FailureReport.equipment_name.ilike(f"%{equipment_name}%"))
    if failure_type:
        query = query.where(FailureReport.failure_type == failure_type)
    
    query = query.offset(skip).limit(limit).order_by(FailureReport.report_date.desc())
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{report_id}", response_model=FailureReportResponse)
async def get_failure_report(
    report_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get failure report by ID."""
    query = select(FailureReport).where(FailureReport.report_id == report_id)
    result = await db.execute(query)
    report = result.scalar_one_or_none()
    
    if not report:
        raise HTTPException(status_code=404, detail="Failure report not found")
    
    return report


@router.put("/{report_id}", response_model=FailureReportResponse)
async def update_failure_report(
    report_id: str,
    report_update: FailureReportUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update failure report by ID."""
    query = select(FailureReport).where(FailureReport.report_id == report_id)
    result = await db.execute(query)
    report = result.scalar_one_or_none()
    
    if not report:
        raise HTTPException(status_code=404, detail="Failure report not found")
    
    update_data = report_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(report, field, value)
    
    await db.flush()
    await db.refresh(report)
    return report


@router.delete("/{report_id}", status_code=204)
async def delete_failure_report(
    report_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Delete failure report by ID."""
    query = select(FailureReport).where(FailureReport.report_id == report_id)
    result = await db.execute(query)
    report = result.scalar_one_or_none()
    
    if not report:
        raise HTTPException(status_code=404, detail="Failure report not found")
    
    await db.delete(report)
    return None


@router.get("/count/total")
async def count_failure_reports(db: AsyncSession = Depends(get_db)):
    """Get total failure reports count."""
    query = select(func.count()).select_from(FailureReport)
    result = await db.execute(query)
    return {"count": result.scalar()}