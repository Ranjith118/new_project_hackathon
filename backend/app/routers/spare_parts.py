"""Spare parts API endpoints."""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.models import SparePart
from app.schemas.schemas import (
    SparePartCreate, SparePartUpdate, SparePartResponse
)

router = APIRouter(prefix="/api/spare-parts", tags=["Spare Parts"])


@router.post("/", response_model=SparePartResponse, status_code=201)
async def create_spare_part(
    part: SparePartCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new spare part entry."""
    db_part = SparePart(**part.model_dump())
    db.add(db_part)
    await db.flush()
    await db.refresh(db_part)
    return db_part


@router.get("/", response_model=list[SparePartResponse])
async def list_spare_parts(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    search: Optional[str] = None,
    low_stock: Optional[bool] = None,
    db: AsyncSession = Depends(get_db)
):
    """List spare parts with optional filters."""
    query = select(SparePart)
    
    if search:
        query = query.where(SparePart.part_name.ilike(f"%{search}%"))
    if low_stock:
        query = query.where(SparePart.stock_quantity <= 5)
    
    query = query.offset(skip).limit(limit).order_by(SparePart.part_name)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{part_id}", response_model=SparePartResponse)
async def get_spare_part(
    part_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get spare part by ID."""
    query = select(SparePart).where(SparePart.part_id == part_id)
    result = await db.execute(query)
    part = result.scalar_one_or_none()
    
    if not part:
        raise HTTPException(status_code=404, detail="Spare part not found")
    
    return part


@router.put("/{part_id}", response_model=SparePartResponse)
async def update_spare_part(
    part_id: str,
    part_update: SparePartUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update spare part by ID."""
    query = select(SparePart).where(SparePart.part_id == part_id)
    result = await db.execute(query)
    part = result.scalar_one_or_none()
    
    if not part:
        raise HTTPException(status_code=404, detail="Spare part not found")
    
    update_data = part_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(part, field, value)
    
    await db.flush()
    await db.refresh(part)
    return part


@router.delete("/{part_id}", status_code=204)
async def delete_spare_part(
    part_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Delete spare part by ID."""
    query = select(SparePart).where(SparePart.part_id == part_id)
    result = await db.execute(query)
    part = result.scalar_one_or_none()
    
    if not part:
        raise HTTPException(status_code=404, detail="Spare part not found")
    
    await db.delete(part)
    return None


@router.get("/count/total")
async def count_spare_parts(db: AsyncSession = Depends(get_db)):
    """Get total spare parts count."""
    query = select(func.count()).select_from(SparePart)
    result = await db.execute(query)
    return {"count": result.scalar()}