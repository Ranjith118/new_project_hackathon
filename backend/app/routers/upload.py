"""File upload API endpoints."""
import os
import uuid
import csv
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from fastapi.responses import FileResponse
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.config import settings
from app.models.models import UploadedFile, MaintenanceLog, SensorData, SparePart, FailureReport
from app.schemas.schemas import UploadedFileResponse

router = APIRouter(prefix="/api/upload", tags=["File Upload"])

# Category to folder mapping
CATEGORY_FOLDERS = {
    "manual": "manuals",
    "sop": "sop",
    "maintenance_log": "maintenance_logs",
    "failure_report": "failure_reports",
    "sensor_data": "sensor_data",
    "spares": "spares",
    "incident": "incidents",
}

# Allowed file extensions
ALLOWED_EXTENSIONS = {
    "manual": [".pdf"],
    "sop": [".pdf"],
    "maintenance_log": [".csv"],
    "failure_report": [".csv"],
    "sensor_data": [".csv"],
    "spares": [".csv"],
    "incident": [".csv"],
}


def validate_file(file: UploadFile, category: str) -> str:
    """Validate uploaded file type and extension."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")
    
    ext = Path(file.filename).suffix.lower()
    allowed = ALLOWED_EXTENSIONS.get(category, [])
    
    if ext not in allowed:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type for {category}. Allowed: {', '.join(allowed)}"
        )
    
    return ext


def generate_unique_filename(original_filename: str, category: str) -> str:
    """Generate unique filename with timestamp."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = str(uuid.uuid4())[:8]
    name = Path(original_filename).stem
    ext = Path(original_filename).suffix
    return f"{name}_{timestamp}_{unique_id}{ext}"


async def save_upload_file(file: UploadFile, category: str) -> tuple[str, int]:
    """Save uploaded file to disk and return path and size."""
    folder = CATEGORY_FOLDERS.get(category, "uploads")
    upload_dir = settings.UPLOAD_DIR / folder
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    unique_filename = generate_unique_filename(file.filename, category)
    file_path = upload_dir / unique_filename
    
    content = await file.read()
    file_size = len(content)
    
    if file_size > settings.MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail=f"File too large. Max size: {settings.MAX_FILE_SIZE // (1024*1024)}MB")
    
    with open(file_path, "wb") as f:
        f.write(content)
    
    return str(file_path), file_size


async def parse_csv_and_import(filepath: str, category: str, db: AsyncSession) -> dict:
    """Parse CSV file and import data to database."""
    imported = 0
    errors = []
    
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        for row_idx, row in enumerate(reader, start=2):
            try:
                if category == "maintenance_log":
                    # Parse maintenance log CSV
                    log_data = {
                        "equipment_name": row.get("equipment_name", ""),
                        "issue": row.get("issue", ""),
                        "action_taken": row.get("action_taken", ""),
                        "downtime_hours": float(row.get("downtime_hours", 0) or 0),
                        "severity": row.get("severity", "medium"),
                        "technician": row.get("technician", ""),
                        "maintenance_date": datetime.strptime(row.get("maintenance_date", ""), "%Y-%m-%d").date()
                    }
                    db_log = MaintenanceLog(**log_data)
                    db.add(db_log)
                    imported += 1
                    
                elif category == "failure_report":
                    # Parse failure report CSV
                    report_data = {
                        "equipment_name": row.get("equipment_name", ""),
                        "failure_type": row.get("failure_type", ""),
                        "root_cause": row.get("root_cause", ""),
                        "downtime_hours": float(row.get("downtime_hours", 0) or 0),
                        "report_date": datetime.strptime(row.get("report_date", ""), "%Y-%m-%d").date()
                    }
                    db_report = FailureReport(**report_data)
                    db.add(db_report)
                    imported += 1
                    
                elif category == "sensor_data":
                    # Parse sensor data CSV
                    sensor_data = {
                        "equipment_name": row.get("equipment_name", ""),
                        "temperature": float(row.get("temperature")) if row.get("temperature") else None,
                        "vibration": float(row.get("vibration")) if row.get("vibration") else None,
                        "current": float(row.get("current")) if row.get("current") else None,
                        "pressure": float(row.get("pressure")) if row.get("pressure") else None,
                        "rpm": int(row.get("rpm")) if row.get("rpm") else None,
                        "timestamp": datetime.strptime(row.get("timestamp", ""), "%Y-%m-%d %H:%M:%S")
                    }
                    db_sensor = SensorData(**sensor_data)
                    db.add(db_sensor)
                    imported += 1
                    
                elif category == "spares":
                    # Parse spare parts CSV
                    part_data = {
                        "part_name": row.get("part_name", ""),
                        "stock_quantity": int(row.get("stock_quantity", 0) or 0),
                        "lead_time_days": int(row.get("lead_time_days", 0) or 0),
                        "supplier": row.get("supplier", "")
                    }
                    db_part = SparePart(**part_data)
                    db.add(db_part)
                    imported += 1
                    
            except Exception as e:
                errors.append({"row": row_idx, "error": str(e)})
    
    await db.flush()
    return {"imported": imported, "errors": errors if errors else None}


@router.post("/manual", response_model=UploadedFileResponse)
async def upload_manual(
    file: UploadFile = File(...),
    equipment_name: Optional[str] = Form(None),
    uploaded_by: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db)
):
    """Upload equipment manual (PDF)."""
    validate_file(file, "manual")
    file_path, file_size = await save_upload_file(file, "manual")
    
    # Save metadata
    file_meta = UploadedFile(
        filename=file.filename,
        file_type="application/pdf",
        file_category="manual",
        file_size=file_size,
        file_path=file_path,
        equipment_name=equipment_name,
        uploaded_by=uploaded_by
    )
    db.add(file_meta)
    await db.flush()
    await db.refresh(file_meta)
    
    return file_meta


@router.post("/sop", response_model=UploadedFileResponse)
async def upload_sop(
    file: UploadFile = File(...),
    equipment_name: Optional[str] = Form(None),
    uploaded_by: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db)
):
    """Upload SOP document (PDF)."""
    validate_file(file, "sop")
    file_path, file_size = await save_upload_file(file, "sop")
    
    # Save metadata
    file_meta = UploadedFile(
        filename=file.filename,
        file_type="application/pdf",
        file_category="sop",
        file_size=file_size,
        file_path=file_path,
        equipment_name=equipment_name,
        uploaded_by=uploaded_by
    )
    db.add(file_meta)
    await db.flush()
    await db.refresh(file_meta)
    
    return file_meta


@router.post("/maintenance-log", response_model=UploadedFileResponse)
async def upload_maintenance_log(
    file: UploadFile = File(...),
    uploaded_by: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db)
):
    """Upload maintenance log CSV and import to database."""
    validate_file(file, "maintenance_log")
    file_path, file_size = await save_upload_file(file, "maintenance_log")
    
    # Parse and import CSV
    result = await parse_csv_and_import(file_path, "maintenance_log", db)
    
    # Save metadata
    file_meta = UploadedFile(
        filename=file.filename,
        file_type="text/csv",
        file_category="maintenance_log",
        file_size=file_size,
        file_path=file_path,
        uploaded_by=uploaded_by
    )
    db.add(file_meta)
    await db.flush()
    await db.refresh(file_meta)
    
    return {"file": file_meta, "import_result": result}


@router.post("/failure-report", response_model=UploadedFileResponse)
async def upload_failure_report(
    file: UploadFile = File(...),
    uploaded_by: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db)
):
    """Upload failure report CSV and import to database."""
    validate_file(file, "failure_report")
    file_path, file_size = await save_upload_file(file, "failure_report")
    
    # Parse and import CSV
    result = await parse_csv_and_import(file_path, "failure_report", db)
    
    # Save metadata
    file_meta = UploadedFile(
        filename=file.filename,
        file_type="text/csv",
        file_category="failure_report",
        file_size=file_size,
        file_path=file_path,
        uploaded_by=uploaded_by
    )
    db.add(file_meta)
    await db.flush()
    await db.refresh(file_meta)
    
    return {"file": file_meta, "import_result": result}


@router.post("/sensor-data", response_model=UploadedFileResponse)
async def upload_sensor_data(
    file: UploadFile = File(...),
    uploaded_by: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db)
):
    """Upload sensor data CSV and import to database."""
    validate_file(file, "sensor_data")
    file_path, file_size = await save_upload_file(file, "sensor_data")
    
    # Parse and import CSV
    result = await parse_csv_and_import(file_path, "sensor_data", db)
    
    # Save metadata
    file_meta = UploadedFile(
        filename=file.filename,
        file_type="text/csv",
        file_category="sensor_data",
        file_size=file_size,
        file_path=file_path,
        uploaded_by=uploaded_by
    )
    db.add(file_meta)
    await db.flush()
    await db.refresh(file_meta)
    
    return {"file": file_meta, "import_result": result}


@router.post("/spares", response_model=UploadedFileResponse)
async def upload_spares(
    file: UploadFile = File(...),
    uploaded_by: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db)
):
    """Upload spare parts CSV and import to database."""
    validate_file(file, "spares")
    file_path, file_size = await save_upload_file(file, "spares")
    
    # Parse and import CSV
    result = await parse_csv_and_import(file_path, "spares", db)
    
    # Save metadata
    file_meta = UploadedFile(
        filename=file.filename,
        file_type="text/csv",
        file_category="spares",
        file_size=file_size,
        file_path=file_path,
        uploaded_by=uploaded_by
    )
    db.add(file_meta)
    await db.flush()
    await db.refresh(file_meta)
    
    return {"file": file_meta, "import_result": result}


@router.get("/files", response_model=list[UploadedFileResponse])
async def list_uploaded_files(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    category: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """List all uploaded files."""
    query = select(UploadedFile)
    
    if category:
        query = query.where(UploadedFile.file_category == category)
    
    query = query.offset(skip).limit(limit).order_by(UploadedFile.created_at.desc())
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{file_id}/download")
async def download_file(
    file_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Download an uploaded file."""
    query = select(UploadedFile).where(UploadedFile.file_id == file_id)
    result = await db.execute(query)
    file_meta = result.scalar_one_or_none()
    
    if not file_meta:
        raise HTTPException(status_code=404, detail="File not found")
    
    file_path = Path(file_meta.file_path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found on disk")
    
    return FileResponse(
        path=file_path,
        filename=file_meta.filename,
        media_type=file_meta.file_type
    )


@router.delete("/{file_id}", status_code=204)
async def delete_uploaded_file(
    file_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Delete an uploaded file."""
    query = select(UploadedFile).where(UploadedFile.file_id == file_id)
    result = await db.execute(query)
    file_meta = result.scalar_one_or_none()
    
    if not file_meta:
        raise HTTPException(status_code=404, detail="File not found")
    
    # Delete file from disk
    file_path = Path(file_meta.file_path)
    if file_path.exists():
        file_path.unlink()
    
    await db.delete(file_meta)
    return None