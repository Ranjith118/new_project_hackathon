"""Dashboard API endpoints for statistics and overview."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func, case
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.models import Equipment, MaintenanceLog, FailureReport, SparePart, UploadedFile
from app.schemas.schemas import DashboardResponse, DashboardStats, RecentUpload, EquipmentStatusSummary

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


@router.get("/stats", response_model=DashboardStats)
async def get_dashboard_stats(db: AsyncSession = Depends(get_db)):
    """Get dashboard statistics."""
    # Count equipment
    equipment_count = await db.scalar(select(func.count()).select_from(Equipment))
    
    # Count maintenance logs
    maintenance_count = await db.scalar(select(func.count()).select_from(MaintenanceLog))
    
    # Count failure reports
    failure_count = await db.scalar(select(func.count()).select_from(FailureReport))
    
    # Count manuals (file category = 'manual')
    manuals_count = await db.scalar(
        select(func.count()).select_from(UploadedFile).where(UploadedFile.file_category == "manual")
    )
    
    # Count SOPs (file category = 'sop')
    sops_count = await db.scalar(
        select(func.count()).select_from(UploadedFile).where(UploadedFile.file_category == "sop")
    )
    
    # Count spare parts
    spares_count = await db.scalar(select(func.count()).select_from(SparePart))
    
    # Count equipment by status
    status_counts_result = await db.execute(
        select(
            Equipment.status,
            func.count().label("count")
        ).group_by(Equipment.status)
    )
    status_results = {row.status: row.count for row in status_counts_result.all()}
    
    operational = status_results.get("operational", 0)
    maintenance = status_results.get("maintenance", 0)
    failed = status_results.get("failed", 0)
    
    return DashboardStats(
        total_equipment=equipment_count or 0,
        total_maintenance_logs=maintenance_count or 0,
        total_failure_reports=failure_count or 0,
        total_manuals=manuals_count or 0,
        total_sops=sops_count or 0,
        total_spare_parts=spares_count or 0,
        operational_equipment=operational,
        maintenance_equipment=maintenance,
        failed_equipment=failed
    )


@router.get("/recent-uploads", response_model=list[RecentUpload])
async def get_recent_uploads(
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db)
):
    """Get recent file uploads."""
    query = select(UploadedFile).order_by(UploadedFile.created_at.desc()).limit(limit)
    result = await db.execute(query)
    files = result.scalars().all()
    
    return [
        RecentUpload(
            file_id=f.file_id,
            filename=f.filename,
            file_category=f.file_category,
            file_size=f.file_size,
            created_at=f.created_at
        )
        for f in files
    ]


@router.get("/equipment-status", response_model=list[EquipmentStatusSummary])
async def get_equipment_status(db: AsyncSession = Depends(get_db)):
    """Get equipment status summary."""
    query = select(
        Equipment.status,
        func.count().label("count")
    ).group_by(Equipment.status)
    
    result = await db.execute(query)
    
    return [
        EquipmentStatusSummary(status=row.status, count=row.count)
        for row in result.all()
    ]


@router.get("/", response_model=DashboardResponse)
async def get_dashboard(db: AsyncSession = Depends(get_db)):
    """Get complete dashboard data."""
    stats = await get_dashboard_stats(db)
    recent_uploads = await get_recent_uploads(db)
    equipment_status = await get_equipment_status(db)
    
    return DashboardResponse(
        stats=stats,
        recent_uploads=recent_uploads,
        equipment_status=equipment_status
    )