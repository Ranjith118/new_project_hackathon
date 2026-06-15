"""Pydantic schemas for Phase 7: Spare Parts & Procurement Intelligence."""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


# ============ Spare Part Schemas ============

class SparePartCreate(BaseModel):
    """Schema for creating a spare part."""
    part_name: str = Field(..., min_length=1, max_length=200)
    part_number: str = Field(..., min_length=1, max_length=50)
    category: str = Field(..., min_length=1, max_length=100)
    stock_quantity: int = Field(default=0, ge=0)
    minimum_stock: int = Field(default=5, ge=0)
    reorder_level: int = Field(default=3, ge=0)
    supplier: str = Field(..., min_length=1, max_length=200)
    lead_time_days: int = Field(default=7, ge=1)
    unit_cost: float = Field(default=0.0, ge=0)
    location: Optional[str] = None
    equipment_type: Optional[str] = None
    description: Optional[str] = None


class SparePartUpdate(BaseModel):
    """Schema for updating a spare part."""
    part_name: Optional[str] = Field(default=None, max_length=200)
    part_number: Optional[str] = Field(default=None, max_length=50)
    category: Optional[str] = Field(default=None, max_length=100)
    stock_quantity: Optional[int] = Field(default=None, ge=0)
    minimum_stock: Optional[int] = Field(default=None, ge=0)
    reorder_level: Optional[int] = Field(default=None, ge=0)
    supplier: Optional[str] = Field(default=None, max_length=200)
    lead_time_days: Optional[int] = Field(default=None, ge=1)
    unit_cost: Optional[float] = Field(default=None, ge=0)
    location: Optional[str] = None
    equipment_type: Optional[str] = None
    description: Optional[str] = None


class SparePartResponse(BaseModel):
    """Schema for spare part response."""
    part_id: str
    part_name: str
    part_number: str
    category: str
    stock_quantity: int
    minimum_stock: int
    reorder_level: int
    supplier: str
    lead_time_days: int
    unit_cost: float
    location: Optional[str] = None
    last_updated: datetime
    equipment_type: Optional[str] = None
    description: Optional[str] = None
    status: str  # in_stock, low_stock, out_of_stock, reorder_required


class SparePartListResponse(BaseModel):
    """Schema for spare parts list."""
    parts: List[SparePartResponse]
    total: int


# ============ Inventory Schemas ============

class InventoryAlertResponse(BaseModel):
    """Schema for inventory alert."""
    alert_id: str
    part_id: str
    part_name: str
    alert_type: str
    severity: str
    message: str
    current_stock: int
    minimum_stock: int
    recommended_order: int
    created_at: datetime


class InventoryStatusResponse(BaseModel):
    """Schema for inventory status."""
    part_id: str
    part_name: str
    part_number: str
    status: str
    available_quantity: int
    required_quantity: int
    shortage: int
    safety_stock_ok: bool
    reorder_needed: bool


class InventorySummaryResponse(BaseModel):
    """Schema for inventory summary."""
    total_parts: int
    in_stock: int
    low_stock: int
    out_of_stock: int
    total_inventory_value: float
    critical_count: int


# ============ Supplier Schemas ============

class SupplierCreate(BaseModel):
    """Schema for creating a supplier."""
    supplier_name: str = Field(..., min_length=1, max_length=200)
    contact_person: str = Field(..., min_length=1, max_length=100)
    email: str = Field(..., min_length=1, max_length=100)
    phone: str = Field(..., min_length=1, max_length=50)
    address: str = Field(..., min_length=1, max_length=300)
    lead_time_days: int = Field(default=7, ge=1)
    reliability_score: float = Field(default=85.0, ge=0, le=100)
    preferred_supplier: bool = False
    categories: List[str] = Field(default_factory=list)


class SupplierResponse(BaseModel):
    """Schema for supplier response."""
    supplier_id: str
    supplier_name: str
    contact_person: str
    email: str
    phone: str
    address: str
    lead_time_days: int
    reliability_score: float
    on_time_delivery_rate: float
    quality_score: float
    preferred_supplier: bool
    categories: List[str]
    last_order_date: Optional[datetime] = None
    total_orders: int


class SupplierListResponse(BaseModel):
    """Schema for suppliers list."""
    suppliers: List[SupplierResponse]
    total: int


class SupplierPerformanceResponse(BaseModel):
    """Schema for supplier performance."""
    supplier_id: str
    supplier_name: str
    total_orders: int
    on_time_deliveries: int
    late_deliveries: int
    on_time_rate: float
    average_lead_time: float
    quality_issues: int
    total_spend: float
    reliability_score: float


# ============ Procurement Schemas ============

class ProcurementRequestResponse(BaseModel):
    """Schema for procurement request."""
    request_id: str
    part_id: str
    part_name: str
    part_number: str
    quantity: int
    priority: str
    urgency: str
    reason: str
    supplier: str
    lead_time_days: int
    estimated_cost: float
    request_date: datetime
    required_by: Optional[datetime] = None
    status: str


class ProcurementPlanResponse(BaseModel):
    """Schema for procurement plan."""
    plan_id: str
    equipment_name: str
    root_cause: str
    created_at: datetime
    requests: List[ProcurementRequestResponse]
    total_estimated_cost: float
    critical_requests: int
    lead_time_risk: bool
    availability_risk: bool


class ProcurementRiskResponse(BaseModel):
    """Schema for procurement risk."""
    risk_id: str
    part_id: str
    part_name: str
    risk_type: str
    severity: str
    description: str
    mitigation: str


class ReorderRecommendationResponse(BaseModel):
    """Schema for reorder recommendation."""
    recommendation_id: str
    part_id: str
    part_name: str
    part_number: str
    current_stock: int
    minimum_stock: int
    reorder_level: int
    recommended_quantity: int
    urgency: str
    reason: str
    estimated_cost: float
    supplier: str
    lead_time_days: int
    created_at: datetime


class ReorderSummaryResponse(BaseModel):
    """Schema for reorder summary."""
    total_recommendations: int
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    total_estimated_cost: float
    by_supplier: Dict[str, Dict[str, Any]]


# ============ Procurement Plan Request ============

class ProcurementPlanRequest(BaseModel):
    """Schema for procurement plan request."""
    equipment_name: str
    equipment_type: str
    root_cause: str
    failure_probability: Optional[float] = None
    rul_days: Optional[int] = None


# ============ Dashboard Schemas ============

class ProcurementDashboardResponse(BaseModel):
    """Schema for procurement dashboard."""
    inventory_summary: InventorySummaryResponse
    pending_requests: List[ProcurementRequestResponse]
    critical_alerts: List[InventoryAlertResponse]
    reorder_recommendations: List[ReorderRecommendationResponse]
    supplier_summary: Dict[str, Any]


# ============ Part Mapping Schemas ============

class PartMappingResponse(BaseModel):
    """Schema for part mapping."""
    mapping_id: str
    equipment_type: str
    root_cause: str
    part_id: str
    part_name: str
    part_number: str
    quantity_required: int
    urgency: str
    description: str


class PartMappingRequest(BaseModel):
    """Schema for part mapping request."""
    equipment_type: str
    root_cause: str
    failure_probability: Optional[float] = None