"""
Input Intelligence Hub API.
Provides unified KPIs, data quality scores, processing status,
and pipeline health for the central hub page.
"""
from datetime import datetime, date, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy import select, func, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.models import (
    Equipment, SensorData, MaintenanceLog, FailureReport,
    SparePart, IntelligentDocument, DelayLog, FaultLog,
    IncidentRecord, BreakdownRecord, UploadedFile
)

router = APIRouter(prefix="/api/hub", tags=["Intelligence Hub"])


@router.get("/kpis")
async def get_hub_kpis(db: AsyncSession = Depends(get_db)):
    """Master KPI card data for the Input Intelligence Center."""

    async def count(model):
        r = await db.execute(select(func.count()).select_from(model))
        return r.scalar() or 0

    eq_count   = await count(Equipment)
    sensor_count = await count(SensorData)
    maint_count  = await count(MaintenanceLog)
    fail_count   = await count(FailureReport)
    parts_count  = await count(SparePart)
    doc_count    = await count(IntelligentDocument)
    delay_count  = await count(DelayLog)
    fault_count  = await count(FaultLog)
    incident_count = await count(IncidentRecord)
    breakdown_count = await count(BreakdownRecord)

    # Active alerts (from anomaly engine in memory)
    active_alerts = 0
    try:
        from app.health.alert_engine import get_alert_engine
        ae = get_alert_engine()
        summary = ae.get_alert_summary()
        active_alerts = summary.get("active", 0)
    except Exception:
        pass

    # AI-ready docs (processed)
    ai_ready = (await db.execute(
        select(func.count()).select_from(IntelligentDocument)
        .where(IntelligentDocument.processing_status == "completed")
    )).scalar() or 0

    total_operational = delay_count + fault_count + incident_count + breakdown_count

    return {
        "equipment":        eq_count,
        "sensor_records":   sensor_count,
        "maintenance_logs": maint_count,
        "failure_reports":  fail_count,
        "spare_parts":      parts_count,
        "documents":        doc_count,
        "active_alerts":    active_alerts,
        "ai_ready_docs":    ai_ready,
        "operational_records": total_operational,
        "delay_logs":       delay_count,
        "fault_logs":       fault_count,
        "incidents":        incident_count,
        "breakdowns":       breakdown_count,
    }


@router.get("/data-quality")
async def get_data_quality(db: AsyncSession = Depends(get_db)):
    """Calculate data quality scores across all modules."""

    # ── Equipment quality ──────────────────────────────────
    eq_rows = (await db.execute(select(Equipment))).scalars().all()
    eq_total = len(eq_rows)
    eq_complete = sum(1 for e in eq_rows if e.manufacturer and e.installation_date)
    eq_score = round((eq_complete / eq_total * 100) if eq_total else 0)

    # ── Maintenance log quality ────────────────────────────
    ml_rows = (await db.execute(select(MaintenanceLog))).scalars().all()
    ml_total = len(ml_rows)
    ml_complete = sum(1 for m in ml_rows if m.action_taken and m.technician)
    ml_score = round((ml_complete / ml_total * 100) if ml_total else 0)

    # ── Sensor data quality ────────────────────────────────
    sd_total = (await db.execute(select(func.count()).select_from(SensorData))).scalar() or 0
    sd_complete = (await db.execute(
        select(func.count()).select_from(SensorData)
        .where(SensorData.temperature.isnot(None))
        .where(SensorData.vibration.isnot(None))
    )).scalar() or 0
    sd_score = round((sd_complete / sd_total * 100) if sd_total else 0)

    # ── Document quality ───────────────────────────────────
    doc_rows = (await db.execute(select(IntelligentDocument))).scalars().all()
    doc_total = len(doc_rows)
    doc_processed = sum(1 for d in doc_rows if d.processing_status == "completed")
    doc_score = round((doc_processed / doc_total * 100) if doc_total else 0)

    # ── Failure report quality ─────────────────────────────
    fr_rows = (await db.execute(select(FailureReport))).scalars().all()
    fr_total = len(fr_rows)
    fr_complete = sum(1 for f in fr_rows if f.root_cause)
    fr_score = round((fr_complete / fr_total * 100) if fr_total else 0)

    # ── Spare parts quality ────────────────────────────────
    sp_rows = (await db.execute(select(SparePart))).scalars().all()
    sp_total = len(sp_rows)
    sp_complete = sum(1 for s in sp_rows if s.supplier and s.lead_time_days)
    sp_score = round((sp_complete / sp_total * 100) if sp_total else 0)

    # ── Overall AI readiness ───────────────────────────────
    scores = [eq_score, ml_score, sd_score, doc_score, fr_score, sp_score]
    overall = round(sum(scores) / len([s for s in scores if s > 0])) if any(s > 0 for s in scores) else 0

    # ── Missing data indicators ────────────────────────────
    missing_eq  = eq_total - eq_complete
    missing_ml  = ml_total - ml_complete
    missing_doc = doc_total - doc_processed

    return {
        "overall_ai_readiness": overall,
        "modules": {
            "equipment":       {"score": eq_score,  "total": eq_total,  "complete": eq_complete},
            "maintenance_logs":{"score": ml_score,  "total": ml_total,  "complete": ml_complete},
            "sensor_data":     {"score": sd_score,  "total": sd_total,  "complete": sd_complete},
            "documents":       {"score": doc_score, "total": doc_total, "complete": doc_processed},
            "failure_reports": {"score": fr_score,  "total": fr_total,  "complete": fr_complete},
            "spare_parts":     {"score": sp_score,  "total": sp_total,  "complete": sp_complete},
        },
        "issues": {
            "missing_equipment_info": missing_eq,
            "incomplete_maintenance_logs": missing_ml,
            "unprocessed_documents": missing_doc,
        }
    }


@router.get("/processing-status")
async def get_processing_status(db: AsyncSession = Depends(get_db)):
    """Document processing pipeline status."""
    rows = (await db.execute(
        select(IntelligentDocument).order_by(IntelligentDocument.upload_date.desc()).limit(20)
    )).scalars().all()

    # Count by status
    status_counts = {}
    for r in rows:
        status_counts[r.processing_status] = status_counts.get(r.processing_status, 0) + 1

    pipeline = []
    for r in rows[:10]:
        pipeline.append({
            "doc_id":   r.doc_id,
            "file_name": r.file_name,
            "file_type": r.file_type,
            "status":   r.processing_status,
            "equipment_name": r.equipment_name,
            "document_type": r.document_type,
            "chunk_count": r.chunk_count,
            "upload_date": r.upload_date.isoformat() if r.upload_date else None,
            "processed_date": r.processed_date.isoformat() if r.processed_date else None,
            "error": r.processing_error,
        })

    # Sensor data growth (last 7 days)
    sensor_trend = []
    for i in range(6, -1, -1):
        d = date.today() - timedelta(days=i)
        cnt = (await db.execute(
            select(func.count()).select_from(SensorData)
            .where(func.date(SensorData.created_at) == d)
        )).scalar() or 0
        sensor_trend.append({"date": d.isoformat(), "count": cnt})

    # Maintenance log trend
    maint_trend = []
    for i in range(6, -1, -1):
        d = date.today() - timedelta(days=i)
        cnt = (await db.execute(
            select(func.count()).select_from(MaintenanceLog)
            .where(MaintenanceLog.maintenance_date == d)
        )).scalar() or 0
        maint_trend.append({"date": d.isoformat(), "count": cnt})

    return {
        "document_pipeline": pipeline,
        "status_counts": status_counts,
        "sensor_data_trend": sensor_trend,
        "maintenance_trend": maint_trend,
    }


@router.get("/module-summary")
async def get_module_summary(db: AsyncSession = Depends(get_db)):
    """Summary of all data modules for the hub overview."""
    # Recent activity across all modules
    recent = []

    ml = (await db.execute(select(MaintenanceLog).order_by(MaintenanceLog.created_at.desc()).limit(5))).scalars().all()
    for r in ml:
        recent.append({"module": "Maintenance Log", "text": f"{r.equipment_name} — {r.issue[:50]}", "time": r.created_at.isoformat(), "color": "text-yellow-400"})

    fr = (await db.execute(select(FailureReport).order_by(FailureReport.created_at.desc()).limit(5))).scalars().all()
    for r in fr:
        recent.append({"module": "Failure Report", "text": f"{r.equipment_name} — {r.failure_type}", "time": r.created_at.isoformat(), "color": "text-red-400"})

    fl = (await db.execute(select(FaultLog).order_by(FaultLog.created_at.desc()).limit(5))).scalars().all()
    for r in fl:
        recent.append({"module": "Fault Log", "text": f"{r.equipment_name} — {r.error_message[:50]}", "time": r.created_at.isoformat(), "color": "text-orange-400"})

    docs = (await db.execute(select(IntelligentDocument).order_by(IntelligentDocument.upload_date.desc()).limit(5))).scalars().all()
    for r in docs:
        recent.append({"module": "Document", "text": f"{r.file_name} [{r.processing_status}]", "time": r.upload_date.isoformat(), "color": "text-purple-400"})

    # Sort by time desc
    recent.sort(key=lambda x: x["time"], reverse=True)

    return {"recent_activity": recent[:15]}


@router.get("/live-summary")
async def get_live_summary(db: AsyncSession = Depends(get_db)):
    """Real-time summary of the entire plant — polled by AI assistant every 3s."""
    from app.models.models import AlertRecord, FailureReport, SensorData
    from sqlalchemy import select, func, desc
    from app.health.alert_engine import get_alert_engine

    # Active alerts from DB
    active_alerts = (await db.execute(
        select(AlertRecord).where(AlertRecord.status == "active")
        .order_by(desc(AlertRecord.created_at)).limit(10)
    )).scalars().all()

    # Latest failure reports
    recent_failures = (await db.execute(
        select(FailureReport).order_by(desc(FailureReport.created_at)).limit(5)
    )).scalars().all()

    # Latest sensor data per equipment
    latest_sensors = (await db.execute(
        select(SensorData).order_by(desc(SensorData.created_at)).limit(20)
    )).scalars().all()
    seen = set(); sensor_latest = []
    for s in latest_sensors:
        if s.equipment_name not in seen:
            seen.add(s.equipment_name)
            sensor_latest.append({
                "equipment": s.equipment_name,
                "temperature": s.temperature, "vibration": s.vibration,
                "current": s.current, "pressure": s.pressure, "rpm": s.rpm,
                "updated": s.created_at.isoformat() if s.created_at else None,
            })

    return {
        "timestamp": __import__("datetime").datetime.now().isoformat(),
        "active_alerts": [{"equipment": a.equipment_name, "type": a.alert_type, "message": a.message[:60]} for a in active_alerts],
        "active_alert_count": len(active_alerts),
        "critical_count": sum(1 for a in active_alerts if a.alert_type == "critical"),
        "recent_failures": [{"equipment": f.equipment_name, "type": f.failure_type, "date": str(f.report_date)} for f in recent_failures],
        "latest_sensor_readings": sensor_latest,
    }
