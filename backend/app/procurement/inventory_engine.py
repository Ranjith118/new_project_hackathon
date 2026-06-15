"""
Spare Parts Inventory Management Engine.

This module manages spare parts inventory, tracks stock levels,
and monitors inventory status.
"""
import uuid
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum


class StockStatus(Enum):
    """Inventory stock status."""
    IN_STOCK = "in_stock"
    LOW_STOCK = "low_stock"
    OUT_OF_STOCK = "out_of_stock"
    REORDER_REQUIRED = "reorder_required"


@dataclass
class SparePart:
    """Spare part with inventory information."""
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
    last_updated: datetime = field(default_factory=datetime.now)
    equipment_type: Optional[str] = None
    description: Optional[str] = None


@dataclass
class InventoryStatus:
    """Inventory status for a part."""
    part: SparePart
    status: StockStatus
    available_quantity: int
    required_quantity: int
    shortage: int
    safety_stock_ok: bool
    reorder_needed: bool


@dataclass
class InventoryAlert:
    """Inventory alert."""
    alert_id: str
    part_id: str
    part_name: str
    alert_type: str  # out_of_stock, low_stock, reorder_required
    severity: str  # critical, high, medium, low
    message: str
    current_stock: int
    minimum_stock: int
    recommended_order: int
    created_at: datetime


class InventoryEngine:
    """
    Manage spare parts inventory.
    
    Features:
    - Stock tracking
    - Status monitoring
    - Alert generation
    - Inventory reports
    """
    
    # Default spare parts for steel plant
    DEFAULT_PARTS = [
        {
            'part_id': 'SP001',
            'part_name': 'Deep Groove Ball Bearing',
            'part_number': 'B6205',
            'category': 'Bearings',
            'stock_quantity': 5,
            'minimum_stock': 10,
            'reorder_level': 7,
            'supplier': 'SKF Bearings',
            'lead_time_days': 7,
            'unit_cost': 4275.00,       # ₹4,275 (was $45 × 95)
            'location': 'Warehouse A, Shelf 3',
            'equipment_type': 'motor'
        },
        {
            'part_id': 'SP002',
            'part_name': 'Mechanical Seal',
            'part_number': 'MS-100',
            'category': 'Seals',
            'stock_quantity': 3,
            'minimum_stock': 5,
            'reorder_level': 4,
            'supplier': 'Seal Pro Inc',
            'lead_time_days': 10,
            'unit_cost': 11400.00,      # ₹11,400 (was $120 × 95)
            'location': 'Warehouse A, Shelf 5',
            'equipment_type': 'pump'
        },
        {
            'part_id': 'SP003',
            'part_name': 'Bearing Lubricant',
            'part_number': 'BL-001',
            'category': 'Consumables',
            'stock_quantity': 20,
            'minimum_stock': 10,
            'reorder_level': 8,
            'supplier': 'Lubricant Inc',
            'lead_time_days': 3,
            'unit_cost': 2375.00,       # ₹2,375 (was $25 × 95)
            'location': 'Warehouse B, Shelf 1',
            'equipment_type': 'general'
        },
        {
            'part_id': 'SP004',
            'part_name': 'Coupling Spider',
            'part_number': 'CS-150',
            'category': 'Couplings',
            'stock_quantity': 8,
            'minimum_stock': 5,
            'reorder_level': 4,
            'supplier': 'Coupling Co',
            'lead_time_days': 5,
            'unit_cost': 3325.00,       # ₹3,325 (was $35 × 95)
            'location': 'Warehouse A, Shelf 7',
            'equipment_type': 'motor'
        },
        {
            'part_id': 'SP005',
            'part_name': 'Air Filter Element',
            'part_number': 'AF-STD',
            'category': 'Filters',
            'stock_quantity': 0,
            'minimum_stock': 15,
            'reorder_level': 10,
            'supplier': 'Filter Co',
            'lead_time_days': 5,
            'unit_cost': 4275.00,       # ₹4,275 (was $45 × 95)
            'location': 'Warehouse B, Shelf 2',
            'equipment_type': 'compressor'
        },
        {
            'part_id': 'SP006',
            'part_name': 'Electrical Contactor',
            'part_number': 'CT-25A',
            'category': 'Electrical',
            'stock_quantity': 4,
            'minimum_stock': 6,
            'reorder_level': 4,
            'supplier': 'ABB Distributors',
            'lead_time_days': 7,
            'unit_cost': 8075.00,       # ₹8,075 (was $85 × 95)
            'location': 'Warehouse C, Shelf 3',
            'equipment_type': 'motor'
        },
        {
            'part_id': 'SP007',
            'part_name': 'Oil Filter',
            'part_number': 'OF-STD',
            'category': 'Filters',
            'stock_quantity': 12,
            'minimum_stock': 20,
            'reorder_level': 15,
            'supplier': 'Filter Co',
            'lead_time_days': 5,
            'unit_cost': 3325.00,       # ₹3,325 (was $35 × 95)
            'location': 'Warehouse B, Shelf 2',
            'equipment_type': 'compressor'
        },
        {
            'part_id': 'SP008',
            'part_name': 'Gasket Sheet',
            'part_number': 'GS-500',
            'category': 'Seals',
            'stock_quantity': 15,
            'minimum_stock': 10,
            'reorder_level': 8,
            'supplier': 'Industrial Supply',
            'lead_time_days': 3,
            'unit_cost': 2850.00,       # ₹2,850 (was $30 × 95)
            'location': 'Warehouse A, Shelf 4',
            'equipment_type': 'general'
        },
        {
            'part_id': 'SP009',
            'part_name': 'Thermal Protector',
            'part_number': 'TP-25',
            'category': 'Electrical',
            'stock_quantity': 2,
            'minimum_stock': 4,
            'reorder_level': 3,
            'supplier': 'Temperature Co',
            'lead_time_days': 5,
            'unit_cost': 3800.00,       # ₹3,800 (was $40 × 95)
            'location': 'Warehouse C, Shelf 2',
            'equipment_type': 'motor'
        },
        {
            'part_id': 'SP010',
            'part_name': 'Cooling Fan Blade',
            'part_number': 'CFB-150',
            'category': 'Cooling',
            'stock_quantity': 1,
            'minimum_stock': 3,
            'reorder_level': 2,
            'supplier': 'Fan Pro',
            'lead_time_days': 7,
            'unit_cost': 9025.00,       # ₹9,025 (was $95 × 95)
            'location': 'Warehouse A, Shelf 6',
            'equipment_type': 'motor'
        }
    ]
    
    def __init__(self):
        self.parts: Dict[str, SparePart] = {}
        self.alerts: List[InventoryAlert] = []
        self._load_default_parts()
    
    def _load_default_parts(self):
        """Load default parts."""
        for part_data in self.DEFAULT_PARTS:
            part = SparePart(**part_data)
            self.parts[part.part_id] = part
    
    def add_part(self, part: SparePart) -> bool:
        """Add a new spare part."""
        if part.part_id in self.parts:
            return False
        self.parts[part.part_id] = part
        self._check_and_alert(part.part_id)
        return True
    
    def update_part(self, part_id: str, updates: Dict[str, Any]) -> bool:
        """Update spare part information."""
        if part_id not in self.parts:
            return False
        
        part = self.parts[part_id]
        for key, value in updates.items():
            if hasattr(part, key):
                setattr(part, key, value)
        part.last_updated = datetime.now()
        
        self._check_and_alert(part_id)
        return True
    
    def adjust_stock(self, part_id: str, quantity: int, reason: str = "") -> bool:
        """Adjust stock quantity."""
        if part_id not in self.parts:
            return False
        
        part = self.parts[part_id]
        part.stock_quantity = max(0, quantity)
        part.last_updated = datetime.now()
        
        self._check_and_alert(part_id)
        return True
    
    def get_part(self, part_id: str) -> Optional[SparePart]:
        """Get spare part by ID."""
        return self.parts.get(part_id)
    
    def get_part_by_number(self, part_number: str) -> Optional[SparePart]:
        """Get spare part by part number."""
        for part in self.parts.values():
            if part.part_number == part_number:
                return part
        return None
    
    def get_all_parts(self) -> List[SparePart]:
        """Get all spare parts."""
        return list(self.parts.values())
    
    def get_parts_by_category(self, category: str) -> List[SparePart]:
        """Get parts by category."""
        return [p for p in self.parts.values() if p.category == category]
    
    def get_parts_by_equipment_type(self, equipment_type: str) -> List[SparePart]:
        """Get parts by equipment type."""
        return [p for p in self.parts.values() if p.equipment_type == equipment_type]
    
    def check_availability(self, part_id: str, required_quantity: int = 1) -> Dict[str, Any]:
        """Check part availability."""
        part = self.parts.get(part_id)
        if not part:
            return {'available': False, 'error': 'Part not found'}
        
        available = part.stock_quantity >= required_quantity
        status = self._get_stock_status(part)
        
        return {
            'available': available,
            'part_id': part_id,
            'part_name': part.part_name,
            'current_stock': part.stock_quantity,
            'required_quantity': required_quantity,
            'status': status.value,
            'shortage': max(0, required_quantity - part.stock_quantity)
        }
    
    def get_inventory_status(self, part_id: str) -> Optional[InventoryStatus]:
        """Get detailed inventory status."""
        part = self.parts.get(part_id)
        if not part:
            return None
        
        status = self._get_stock_status(part)
        safety_ok = part.stock_quantity >= part.minimum_stock
        reorder_needed = part.stock_quantity <= part.reorder_level
        
        return InventoryStatus(
            part=part,
            status=status,
            available_quantity=part.stock_quantity,
            required_quantity=part.minimum_stock,
            shortage=max(0, part.minimum_stock - part.stock_quantity),
            safety_stock_ok=safety_ok,
            reorder_needed=reorder_needed
        )
    
    def get_all_alerts(self) -> List[InventoryAlert]:
        """Get all inventory alerts."""
        self._generate_alerts()
        return self.alerts
    
    def get_critical_alerts(self) -> List[InventoryAlert]:
        """Get critical alerts only."""
        self._generate_alerts()
        return [a for a in self.alerts if a.severity in ['critical', 'high']]
    
    def _get_stock_status(self, part: SparePart) -> StockStatus:
        """Determine stock status."""
        if part.stock_quantity == 0:
            return StockStatus.OUT_OF_STOCK
        elif part.stock_quantity <= part.reorder_level:
            return StockStatus.REORDER_REQUIRED
        elif part.stock_quantity <= part.minimum_stock:
            return StockStatus.LOW_STOCK
        else:
            return StockStatus.IN_STOCK
    
    def _check_and_alert(self, part_id: str):
        """Check stock and generate alert if needed."""
        part = self.parts.get(part_id)
        if not part:
            return
        
        # Remove existing alerts for this part
        self.alerts = [a for a in self.alerts if a.part_id != part_id]
        
        # Check stock levels
        if part.stock_quantity == 0:
            self.alerts.append(InventoryAlert(
                alert_id=str(uuid.uuid4()),
                part_id=part.part_id,
                part_name=part.part_name,
                alert_type='out_of_stock',
                severity='critical',
                message=f"OUT OF STOCK: {part.part_name} (P/N: {part.part_number})",
                current_stock=0,
                minimum_stock=part.minimum_stock,
                recommended_order=part.minimum_stock * 2,
                created_at=datetime.now()
            ))
        elif part.stock_quantity <= part.reorder_level:
            self.alerts.append(InventoryAlert(
                alert_id=str(uuid.uuid4()),
                part_id=part.part_id,
                part_name=part.part_name,
                alert_type='reorder_required',
                severity='high',
                message=f"REORDER REQUIRED: {part.part_name} (Stock: {part.stock_quantity})",
                current_stock=part.stock_quantity,
                minimum_stock=part.minimum_stock,
                recommended_order=part.minimum_stock - part.stock_quantity + part.reorder_level,
                created_at=datetime.now()
            ))
        elif part.stock_quantity <= part.minimum_stock:
            self.alerts.append(InventoryAlert(
                alert_id=str(uuid.uuid4()),
                part_id=part.part_id,
                part_name=part.part_name,
                alert_type='low_stock',
                severity='medium',
                message=f"LOW STOCK: {part.part_name} (Stock: {part.stock_quantity})",
                current_stock=part.stock_quantity,
                minimum_stock=part.minimum_stock,
                recommended_order=part.minimum_stock - part.stock_quantity,
                created_at=datetime.now()
            ))
    
    def _generate_alerts(self):
        """Generate alerts for all parts."""
        self.alerts = []
        for part_id in self.parts:
            self._check_and_alert(part_id)
    
    def get_inventory_summary(self) -> Dict[str, Any]:
        """Get inventory summary statistics."""
        total_parts = len(self.parts)
        in_stock = sum(1 for p in self.parts.values() if p.stock_quantity >= p.minimum_stock)
        low_stock = sum(1 for p in self.parts.values() if p.stock_quantity <= p.minimum_stock and p.stock_quantity > 0)
        out_of_stock = sum(1 for p in self.parts.values() if p.stock_quantity == 0)
        
        total_value = sum(p.stock_quantity * p.unit_cost for p in self.parts.values())
        
        return {
            'total_parts': total_parts,
            'in_stock': in_stock,
            'low_stock': low_stock,
            'out_of_stock': out_of_stock,
            'total_inventory_value': total_value,
            'critical_count': out_of_stock
        }


# Singleton instance
_inventory_engine: Optional[InventoryEngine] = None


def get_inventory_engine() -> InventoryEngine:
    """Get global inventory engine instance."""
    global _inventory_engine
    if _inventory_engine is None:
        _inventory_engine = InventoryEngine()
    return _inventory_engine