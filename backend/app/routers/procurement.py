"""Phase 7: Spare Parts & Procurement Intelligence API."""
import uuid
from datetime import datetime
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.schemas.procurement_schemas import (
    SparePartCreate, SparePartUpdate, SparePartResponse, SparePartListResponse,
    InventoryAlertResponse, InventoryStatusResponse, InventorySummaryResponse,
    SupplierCreate, SupplierResponse, SupplierListResponse, SupplierPerformanceResponse,
    ProcurementRequestResponse, ProcurementPlanResponse, ProcurementRiskResponse,
    ReorderRecommendationResponse, ReorderSummaryResponse,
    ProcurementPlanRequest, ProcurementDashboardResponse,
    PartMappingResponse, PartMappingRequest
)
from app.procurement.inventory_engine import get_inventory_engine, StockStatus
from app.procurement.mapping_engine import get_mapping_engine
from app.procurement.procurement_engine import get_procurement_engine
from app.procurement.supplier_engine import get_supplier_engine
from app.procurement.reorder_engine import get_reorder_engine

router = APIRouter(prefix="/api/procurement", tags=["Phase 7 - Spare Parts & Procurement"])


# ============ Spare Parts CRUD ============

@router.get("/spares", response_model=SparePartListResponse)
async def get_all_spares(
    category: Optional[str] = None,
    equipment_type: Optional[str] = None
):
    """Get all spare parts with optional filtering."""
    inventory = get_inventory_engine()
    
    parts = inventory.get_all_parts()
    
    if category:
        parts = [p for p in parts if p.category == category]
    
    if equipment_type:
        parts = [p for p in parts if p.equipment_type == equipment_type]
    
    return SparePartListResponse(
        parts=[
            SparePartResponse(
                part_id=p.part_id,
                part_name=p.part_name,
                part_number=p.part_number,
                category=p.category,
                stock_quantity=p.stock_quantity,
                minimum_stock=p.minimum_stock,
                reorder_level=p.reorder_level,
                supplier=p.supplier,
                lead_time_days=p.lead_time_days,
                unit_cost=p.unit_cost,
                location=p.location,
                last_updated=p.last_updated,
                equipment_type=p.equipment_type,
                description=p.description,
                status=inventory._get_stock_status(p).value
            )
            for p in parts
        ],
        total=len(parts)
    )


@router.get("/spares/{part_id}", response_model=SparePartResponse)
async def get_spare(part_id: str):
    """Get a specific spare part."""
    inventory = get_inventory_engine()
    part = inventory.get_part(part_id)
    
    if not part:
        raise HTTPException(status_code=404, detail="Spare part not found")
    
    return SparePartResponse(
        part_id=part.part_id,
        part_name=part.part_name,
        part_number=part.part_number,
        category=part.category,
        stock_quantity=part.stock_quantity,
        minimum_stock=part.minimum_stock,
        reorder_level=part.reorder_level,
        supplier=part.supplier,
        lead_time_days=part.lead_time_days,
        unit_cost=part.unit_cost,
        location=part.location,
        last_updated=part.last_updated,
        equipment_type=part.equipment_type,
        description=part.description,
        status=inventory._get_stock_status(part).value
    )


@router.post("/spares", response_model=SparePartResponse)
async def create_spare(part: SparePartCreate):
    """Create a new spare part."""
    from app.procurement.inventory_engine import SparePart
    
    inventory = get_inventory_engine()
    
    new_part = SparePart(
        part_id=f"SP{str(uuid.uuid4())[:4]}",
        part_name=part.part_name,
        part_number=part.part_number,
        category=part.category,
        stock_quantity=part.stock_quantity,
        minimum_stock=part.minimum_stock,
        reorder_level=part.reorder_level,
        supplier=part.supplier,
        lead_time_days=part.lead_time_days,
        unit_cost=part.unit_cost,
        location=part.location,
        equipment_type=part.equipment_type,
        description=part.description
    )
    
    inventory.add_part(new_part)
    
    return SparePartResponse(
        part_id=new_part.part_id,
        part_name=new_part.part_name,
        part_number=new_part.part_number,
        category=new_part.category,
        stock_quantity=new_part.stock_quantity,
        minimum_stock=new_part.minimum_stock,
        reorder_level=new_part.reorder_level,
        supplier=new_part.supplier,
        lead_time_days=new_part.lead_time_days,
        unit_cost=new_part.unit_cost,
        location=new_part.location,
        last_updated=new_part.last_updated,
        equipment_type=new_part.equipment_type,
        description=new_part.description,
        status=inventory._get_stock_status(new_part).value
    )


@router.put("/spares/{part_id}", response_model=SparePartResponse)
async def update_spare(part_id: str, updates: SparePartUpdate):
    """Update a spare part."""
    inventory = get_inventory_engine()
    
    update_dict = updates.model_dump(exclude_unset=True)
    if not inventory.update_part(part_id, update_dict):
        raise HTTPException(status_code=404, detail="Spare part not found")
    
    part = inventory.get_part(part_id)
    
    return SparePartResponse(
        part_id=part.part_id,
        part_name=part.part_name,
        part_number=part.part_number,
        category=part.category,
        stock_quantity=part.stock_quantity,
        minimum_stock=part.minimum_stock,
        reorder_level=part.reorder_level,
        supplier=part.supplier,
        lead_time_days=part.lead_time_days,
        unit_cost=part.unit_cost,
        location=part.location,
        last_updated=part.last_updated,
        equipment_type=part.equipment_type,
        description=part.description,
        status=inventory._get_stock_status(part).value
    )


@router.delete("/spares/{part_id}")
async def delete_spare(part_id: str):
    """Delete a spare part."""
    inventory = get_inventory_engine()
    
    if part_id not in inventory.parts:
        raise HTTPException(status_code=404, detail="Spare part not found")
    
    del inventory.parts[part_id]
    
    return {"status": "success", "message": "Spare part deleted"}


# ============ Inventory Status ============

@router.get("/inventory-status")
async def get_inventory_status():
    """Get inventory status for all parts."""
    inventory = get_inventory_engine()
    
    statuses = []
    for part in inventory.get_all_parts():
        status = inventory.get_inventory_status(part.part_id)
        if status:
            statuses.append(InventoryStatusResponse(
                part_id=status.part.part_id,
                part_name=status.part.part_name,
                part_number=status.part.part_number,
                status=status.status.value,
                available_quantity=status.available_quantity,
                required_quantity=status.required_quantity,
                shortage=status.shortage,
                safety_stock_ok=status.safety_stock_ok,
                reorder_needed=status.reorder_needed
            ))
    
    return {"statuses": statuses, "total": len(statuses)}


@router.get("/inventory-summary", response_model=InventorySummaryResponse)
async def get_inventory_summary():
    """Get inventory summary statistics."""
    inventory = get_inventory_engine()
    summary = inventory.get_inventory_summary()
    
    return InventorySummaryResponse(**summary)


# ============ Inventory Alerts ============

@router.get("/alerts")
async def get_inventory_alerts():
    """Get all inventory alerts."""
    inventory = get_inventory_engine()
    alerts = inventory.get_all_alerts()
    
    return {
        "alerts": [
            InventoryAlertResponse(
                alert_id=a.alert_id,
                part_id=a.part_id,
                part_name=a.part_name,
                alert_type=a.alert_type,
                severity=a.severity,
                message=a.message,
                current_stock=a.current_stock,
                minimum_stock=a.minimum_stock,
                recommended_order=a.recommended_order,
                created_at=a.created_at
            )
            for a in alerts
        ],
        "total": len(alerts)
    }


@router.get("/alerts/critical")
async def get_critical_alerts():
    """Get critical inventory alerts."""
    inventory = get_inventory_engine()
    alerts = inventory.get_critical_alerts()
    
    return {
        "alerts": [
            InventoryAlertResponse(
                alert_id=a.alert_id,
                part_id=a.part_id,
                part_name=a.part_name,
                alert_type=a.alert_type,
                severity=a.severity,
                message=a.message,
                current_stock=a.current_stock,
                minimum_stock=a.minimum_stock,
                recommended_order=a.recommended_order,
                created_at=a.created_at
            )
            for a in alerts
        ],
        "total": len(alerts)
    }


# ============ Reorder Recommendations ============

@router.get("/reorder")
async def get_reorder_recommendations():
    """Get all reorder recommendations."""
    reorder_engine = get_reorder_engine()
    recommendations = reorder_engine.generate_all_recommendations()
    
    return {
        "recommendations": [
            ReorderRecommendationResponse(
                recommendation_id=r.recommendation_id,
                part_id=r.part_id,
                part_name=r.part_name,
                part_number=r.part_number,
                current_stock=r.current_stock,
                minimum_stock=r.minimum_stock,
                reorder_level=r.reorder_level,
                recommended_quantity=r.recommended_quantity,
                urgency=r.urgency,
                reason=r.reason,
                estimated_cost=r.estimated_cost,
                supplier=r.supplier,
                lead_time_days=r.lead_time_days,
                created_at=r.created_at
            )
            for r in recommendations
        ],
        "total": len(recommendations)
    }


@router.get("/reorder-summary", response_model=ReorderSummaryResponse)
async def get_reorder_summary():
    """Get reorder summary."""
    reorder_engine = get_reorder_engine()
    summary = reorder_engine.get_reorder_summary()
    
    return ReorderSummaryResponse(**summary)


# ============ Suppliers ============

@router.get("/suppliers", response_model=SupplierListResponse)
async def get_suppliers():
    """Get all suppliers."""
    supplier_engine = get_supplier_engine()
    suppliers = supplier_engine.get_all_suppliers()
    
    return SupplierListResponse(
        suppliers=[
            SupplierResponse(
                supplier_id=s.supplier_id,
                supplier_name=s.supplier_name,
                contact_person=s.contact_person,
                email=s.email,
                phone=s.phone,
                address=s.address,
                lead_time_days=s.lead_time_days,
                reliability_score=s.reliability_score,
                on_time_delivery_rate=s.on_time_delivery_rate,
                quality_score=s.quality_score,
                preferred_supplier=s.preferred_supplier,
                categories=s.categories,
                last_order_date=s.last_order_date,
                total_orders=s.total_orders
            )
            for s in suppliers
        ],
        total=len(suppliers)
    )


@router.get("/suppliers/{supplier_id}", response_model=SupplierResponse)
async def get_supplier(supplier_id: str):
    """Get a specific supplier."""
    supplier_engine = get_supplier_engine()
    supplier = supplier_engine.get_supplier(supplier_id)
    
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    
    return SupplierResponse(
        supplier_id=supplier.supplier_id,
        supplier_name=supplier.supplier_name,
        contact_person=supplier.contact_person,
        email=supplier.email,
        phone=supplier.phone,
        address=supplier.address,
        lead_time_days=supplier.lead_time_days,
        reliability_score=supplier.reliability_score,
        on_time_delivery_rate=supplier.on_time_delivery_rate,
        quality_score=supplier.quality_score,
        preferred_supplier=supplier.preferred_supplier,
        categories=supplier.categories,
        last_order_date=supplier.last_order_date,
        total_orders=supplier.total_orders
    )


@router.get("/suppliers/{supplier_id}/performance", response_model=SupplierPerformanceResponse)
async def get_supplier_performance(supplier_id: str):
    """Get supplier performance metrics."""
    supplier_engine = get_supplier_engine()
    performance = supplier_engine.get_supplier_performance(supplier_id)
    
    if not performance:
        raise HTTPException(status_code=404, detail="Supplier not found")
    
    return SupplierPerformanceResponse(
        supplier_id=performance.supplier_id,
        supplier_name=performance.supplier_name,
        total_orders=performance.total_orders,
        on_time_deliveries=performance.on_time_deliveries,
        late_deliveries=performance.late_deliveries,
        on_time_rate=performance.on_time_rate,
        average_lead_time=performance.average_lead_time,
        quality_issues=performance.quality_issues,
        total_spend=performance.total_spend,
        reliability_score=performance.reliability_score
    )


# ============ Part Mappings ============

@router.post("/mappings", response_model=List[PartMappingResponse])
async def get_part_mappings(request: PartMappingRequest):
    """Get spare part mappings for equipment and root cause."""
    mapping_engine = get_mapping_engine()
    
    mappings = mapping_engine.get_spare_parts(
        equipment_type=request.equipment_type,
        root_cause=request.root_cause,
        failure_probability=request.failure_probability
    )
    
    return [
        PartMappingResponse(
            mapping_id=m.mapping_id,
            equipment_type=m.equipment_type,
            root_cause=m.root_cause,
            part_id=m.part_id,
            part_name=m.part_name,
            part_number=m.part_number,
            quantity_required=m.quantity_required,
            urgency=m.urgency,
            description=m.description
        )
        for m in mappings
    ]


# ============ Procurement Plan ============

@router.post("/plan", response_model=ProcurementPlanResponse)
async def generate_procurement_plan(request: ProcurementPlanRequest):
    """Generate procurement plan for equipment and root cause."""
    procurement = get_procurement_engine()
    
    plan = procurement.generate_procurement_plan(
        equipment_name=request.equipment_name,
        equipment_type=request.equipment_type,
        root_cause=request.root_cause,
        failure_probability=request.failure_probability,
        rul_days=request.rul_days
    )
    
    return ProcurementPlanResponse(
        plan_id=plan.plan_id,
        equipment_name=plan.equipment_name,
        root_cause=plan.root_cause,
        created_at=plan.created_at,
        requests=[
            ProcurementRequestResponse(
                request_id=r.request_id,
                part_id=r.part_id,
                part_name=r.part_name,
                part_number=r.part_number,
                quantity=r.quantity,
                priority=r.priority,
                urgency=r.urgency,
                reason=r.reason,
                supplier=r.supplier,
                lead_time_days=r.lead_time_days,
                estimated_cost=r.estimated_cost,
                request_date=r.request_date,
                required_by=r.required_by,
                status=r.status
            )
            for r in plan.requests
        ],
        total_estimated_cost=plan.total_estimated_cost,
        critical_requests=plan.critical_requests,
        lead_time_risk=plan.lead_time_risk,
        availability_risk=plan.availability_risk
    )


@router.get("/risks", response_model=List[ProcurementRiskResponse])
async def get_procurement_risks(
    equipment_name: str,
    equipment_type: str,
    root_cause: str,
    failure_probability: Optional[float] = None,
    rul_days: Optional[int] = None
):
    """Analyze procurement risks."""
    procurement = get_procurement_engine()
    
    risks = procurement.analyze_procurement_risks(
        equipment_name=equipment_name,
        equipment_type=equipment_type,
        root_cause=root_cause,
        failure_probability=failure_probability,
        rul_days=rul_days
    )
    
    return [
        ProcurementRiskResponse(
            risk_id=r.risk_id,
            part_id=r.part_id,
            part_name=r.part_name,
            risk_type=r.risk_type,
            severity=r.severity,
            description=r.description,
            mitigation=r.mitigation
        )
        for r in risks
    ]


# ============ Dashboard ============

@router.get("/dashboard", response_model=ProcurementDashboardResponse)
async def get_procurement_dashboard():
    """Get procurement dashboard data."""
    inventory = get_inventory_engine()
    reorder_engine = get_reorder_engine()
    supplier_engine = get_supplier_engine()
    
    # Get inventory summary
    inv_summary = inventory.get_inventory_summary()
    
    # Get critical alerts
    alerts = inventory.get_critical_alerts()
    
    # Get reorder recommendations
    reorders = reorder_engine.generate_all_recommendations()[:10]
    
    # Get supplier summary
    supplier_summary = supplier_engine.get_supplier_summary()
    
    return ProcurementDashboardResponse(
        inventory_summary=InventorySummaryResponse(**inv_summary),
        pending_requests=[],
        critical_alerts=[
            InventoryAlertResponse(
                alert_id=a.alert_id,
                part_id=a.part_id,
                part_name=a.part_name,
                alert_type=a.alert_type,
                severity=a.severity,
                message=a.message,
                current_stock=a.current_stock,
                minimum_stock=a.minimum_stock,
                recommended_order=a.recommended_order,
                created_at=a.created_at
            )
            for a in alerts
        ],
        reorder_recommendations=[
            ReorderRecommendationResponse(
                recommendation_id=r.recommendation_id,
                part_id=r.part_id,
                part_name=r.part_name,
                part_number=r.part_number,
                current_stock=r.current_stock,
                minimum_stock=r.minimum_stock,
                reorder_level=r.reorder_level,
                recommended_quantity=r.recommended_quantity,
                urgency=r.urgency,
                reason=r.reason,
                estimated_cost=r.estimated_cost,
                supplier=r.supplier,
                lead_time_days=r.lead_time_days,
                created_at=r.created_at
            )
            for r in reorders
        ],
        supplier_summary=supplier_summary
    )