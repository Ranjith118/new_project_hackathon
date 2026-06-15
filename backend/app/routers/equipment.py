"""Equipment API endpoints."""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.models import Equipment
from app.schemas.schemas import (
    EquipmentCreate, EquipmentUpdate, EquipmentResponse, PaginatedResponse
)

router = APIRouter(prefix="/api/equipment", tags=["Equipment"])


@router.post("/", response_model=EquipmentResponse, status_code=201)
async def create_equipment(
    equipment: EquipmentCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new equipment entry."""
    db_equipment = Equipment(**equipment.model_dump())
    db.add(db_equipment)
    await db.flush()
    await db.refresh(db_equipment)
    return db_equipment


@router.get("/", response_model=list[EquipmentResponse])
async def list_equipment(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = None,
    status: Optional[str] = None,
    equipment_type: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """List all equipment with optional filters."""
    query = select(Equipment)
    
    if search:
        query = query.where(Equipment.equipment_name.ilike(f"%{search}%"))
    if status:
        query = query.where(Equipment.status == status)
    if equipment_type:
        query = query.where(Equipment.equipment_type == equipment_type)
    
    query = query.offset(skip).limit(limit).order_by(Equipment.created_at.desc())
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{equipment_id}", response_model=EquipmentResponse)
async def get_equipment(
    equipment_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get equipment by ID."""
    query = select(Equipment).where(Equipment.equipment_id == equipment_id)
    result = await db.execute(query)
    equipment = result.scalar_one_or_none()
    
    if not equipment:
        raise HTTPException(status_code=404, detail="Equipment not found")
    
    return equipment


@router.put("/{equipment_id}", response_model=EquipmentResponse)
async def update_equipment(
    equipment_id: str,
    equipment_update: EquipmentUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update equipment by ID."""
    query = select(Equipment).where(Equipment.equipment_id == equipment_id)
    result = await db.execute(query)
    equipment = result.scalar_one_or_none()
    
    if not equipment:
        raise HTTPException(status_code=404, detail="Equipment not found")
    
    update_data = equipment_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(equipment, field, value)
    
    await db.flush()
    await db.refresh(equipment)
    return equipment


@router.delete("/{equipment_id}", status_code=204)
async def delete_equipment(
    equipment_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Delete equipment by ID."""
    query = select(Equipment).where(Equipment.equipment_id == equipment_id)
    result = await db.execute(query)
    equipment = result.scalar_one_or_none()
    
    if not equipment:
        raise HTTPException(status_code=404, detail="Equipment not found")
    
    await db.delete(equipment)
    return None


@router.get("/count/total")
async def count_equipment(db: AsyncSession = Depends(get_db)):
    """Get total equipment count."""
    query = select(func.count()).select_from(Equipment)
    result = await db.execute(query)
    return {"count": result.scalar()}