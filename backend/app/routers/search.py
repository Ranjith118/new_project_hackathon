"""Global Search API — searches across all modules."""
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.models import (
    Equipment, SensorData, MaintenanceLog, FailureReport,
    SparePart, IntelligentDocument, DelayLog, FaultLog,
    IncidentRecord, BreakdownRecord
)

router = APIRouter(prefix="/api/search", tags=["Global Search"])


@router.get("")
async def global_search(
    q: str = Query(..., min_length=1),
    db: AsyncSession = Depends(get_db)
):
    """Search across all modules."""
    term = f"%{q}%"
    results = []

    # Equipment
    rows = (await db.execute(
        select(Equipment).where(
            or_(Equipment.equipment_name.ilike(term),
                Equipment.equipment_type.ilike(term),
                Equipment.manufacturer.ilike(term))
        ).limit(10)
    )).scalars().all()
    for r in rows:
        results.append({"type": "Equipment", "id": r.equipment_id,
                        "title": r.equipment_name, "subtitle": f"{r.equipment_type} · {r.status}",
                        "href": "/equipment", "color": "text-blue-400"})

    # Maintenance Logs
    rows = (await db.execute(
        select(MaintenanceLog).where(
            or_(MaintenanceLog.equipment_name.ilike(term),
                MaintenanceLog.issue.ilike(term),
                MaintenanceLog.action_taken.ilike(term))
        ).limit(8)
    )).scalars().all()
    for r in rows:
        results.append({"type": "Maintenance Log", "id": r.log_id,
                        "title": r.equipment_name, "subtitle": r.issue[:80],
                        "href": "/maintenance-logs", "color": "text-yellow-400"})

    # Failure Reports
    rows = (await db.execute(
        select(FailureReport).where(
            or_(FailureReport.equipment_name.ilike(term),
                FailureReport.failure_type.ilike(term),
                FailureReport.root_cause.ilike(term))
        ).limit(8)
    )).scalars().all()
    for r in rows:
        results.append({"type": "Failure Report", "id": r.report_id,
                        "title": r.equipment_name, "subtitle": r.failure_type,
                        "href": "/failure-reports", "color": "text-red-400"})

    # Spare Parts
    rows = (await db.execute(
        select(SparePart).where(
            or_(SparePart.part_name.ilike(term),
                SparePart.supplier.ilike(term))
        ).limit(8)
    )).scalars().all()
    for r in rows:
        results.append({"type": "Spare Part", "id": r.part_id,
                        "title": r.part_name, "subtitle": f"Stock: {r.stock_quantity} · Supplier: {r.supplier or 'N/A'}",
                        "href": "/spare-parts", "color": "text-green-400"})

    # Documents
    rows = (await db.execute(
        select(IntelligentDocument).where(
            or_(IntelligentDocument.file_name.ilike(term),
                IntelligentDocument.equipment_name.ilike(term),
                IntelligentDocument.document_type.ilike(term),
                IntelligentDocument.executive_summary.ilike(term))
        ).limit(8)
    )).scalars().all()
    for r in rows:
        results.append({"type": "Document", "id": r.doc_id,
                        "title": r.file_name, "subtitle": f"{r.document_type or 'Document'} · {r.equipment_name or 'General'}",
                        "href": "/doc-intelligence", "color": "text-purple-400"})

    # Fault Logs
    rows = (await db.execute(
        select(FaultLog).where(
            or_(FaultLog.equipment_name.ilike(term),
                FaultLog.error_message.ilike(term),
                FaultLog.fault_code.ilike(term))
        ).limit(6)
    )).scalars().all()
    for r in rows:
        results.append({"type": "Fault Log", "id": r.fault_id,
                        "title": r.equipment_name, "subtitle": f"{r.fault_code or ''} · {r.error_message[:60]}",
                        "href": "/operational", "color": "text-orange-400"})

    # Incidents
    rows = (await db.execute(
        select(IncidentRecord).where(
            or_(IncidentRecord.equipment_name.ilike(term),
                IncidentRecord.description.ilike(term),
                IncidentRecord.incident_type.ilike(term))
        ).limit(6)
    )).scalars().all()
    for r in rows:
        results.append({"type": "Incident", "id": r.incident_id,
                        "title": r.equipment_name, "subtitle": r.description[:80],
                        "href": "/operational", "color": "text-pink-400"})

    # Breakdowns
    rows = (await db.execute(
        select(BreakdownRecord).where(
            or_(BreakdownRecord.equipment_name.ilike(term),
                BreakdownRecord.failure_type.ilike(term),
                BreakdownRecord.root_cause.ilike(term))
        ).limit(6)
    )).scalars().all()
    for r in rows:
        results.append({"type": "Breakdown", "id": r.breakdown_id,
                        "title": r.equipment_name, "subtitle": f"{r.failure_type} · Downtime: {r.downtime_hours}h",
                        "href": "/operational", "color": "text-red-300"})

    return {"query": q, "total": len(results), "results": results}
