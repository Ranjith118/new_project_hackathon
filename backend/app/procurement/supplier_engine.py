"""
Supplier Management Engine.

This module manages supplier information, tracks supplier performance,
and recommends preferred suppliers.
"""
import uuid
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Supplier:
    """Supplier information."""
    supplier_id: str
    supplier_name: str
    contact_person: str
    email: str
    phone: str
    address: str
    lead_time_days: int
    reliability_score: float  # 0-100
    on_time_delivery_rate: float  # 0-100
    quality_score: float  # 0-100
    preferred_supplier: bool
    categories: List[str]
    last_order_date: Optional[datetime] = None
    total_orders: int = 0
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class SupplierPerformance:
    """Supplier performance metrics."""
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


class SupplierEngine:
    """
    Manage supplier information and performance.
    """
    
    DEFAULT_SUPPLIERS = [
        {
            'supplier_id': 'SUP001',
            'supplier_name': 'SKF Bearings',
            'contact_person': 'John Smith',
            'email': 'john.smith@skfbearings.com',
            'phone': '+1-555-0101',
            'address': '123 Industrial Way, Chicago, IL',
            'lead_time_days': 7,
            'reliability_score': 95.0,
            'on_time_delivery_rate': 98.0,
            'quality_score': 97.0,
            'preferred_supplier': True,
            'categories': ['Bearings', 'Seals', 'Lubricants']
        },
        {
            'supplier_id': 'SUP002',
            'supplier_name': 'Seal Pro Inc',
            'contact_person': 'Sarah Johnson',
            'email': 'sarah@sealproinc.com',
            'phone': '+1-555-0102',
            'address': '456 Seal Lane, Houston, TX',
            'lead_time_days': 10,
            'reliability_score': 88.0,
            'on_time_delivery_rate': 85.0,
            'quality_score': 92.0,
            'preferred_supplier': False,
            'categories': ['Seals', 'Gaskets']
        },
        {
            'supplier_id': 'SUP003',
            'supplier_name': 'Lubricant Inc',
            'contact_person': 'Mike Brown',
            'email': 'mike.brown@lubricantinc.com',
            'phone': '+1-555-0103',
            'address': '789 Oil Street, Detroit, MI',
            'lead_time_days': 3,
            'reliability_score': 92.0,
            'on_time_delivery_rate': 95.0,
            'quality_score': 90.0,
            'preferred_supplier': True,
            'categories': ['Consumables', 'Lubricants', 'Filters']
        },
        {
            'supplier_id': 'SUP004',
            'supplier_name': 'Coupling Co',
            'contact_person': 'Lisa Davis',
            'email': 'lisa@couplingco.com',
            'phone': '+1-555-0104',
            'address': '321 Power Road, Cleveland, OH',
            'lead_time_days': 5,
            'reliability_score': 90.0,
            'on_time_delivery_rate': 92.0,
            'quality_score': 95.0,
            'preferred_supplier': True,
            'categories': ['Couplings', 'Motors']
        },
        {
            'supplier_id': 'SUP005',
            'supplier_name': 'ABB Distributors',
            'contact_person': 'Tom Wilson',
            'email': 'tom.wilson@abb.com',
            'phone': '+1-555-0105',
            'address': '555 Electric Ave, Pittsburgh, PA',
            'lead_time_days': 7,
            'reliability_score': 94.0,
            'on_time_delivery_rate': 96.0,
            'quality_score': 98.0,
            'preferred_supplier': True,
            'categories': ['Electrical', 'Motors', 'Drives']
        },
        {
            'supplier_id': 'SUP006',
            'supplier_name': 'Filter Co',
            'contact_person': 'Emma Martinez',
            'email': 'emma@filterco.com',
            'phone': '+1-555-0106',
            'address': '888 Air Boulevard, Atlanta, GA',
            'lead_time_days': 5,
            'reliability_score': 85.0,
            'on_time_delivery_rate': 88.0,
            'quality_score': 88.0,
            'preferred_supplier': False,
            'categories': ['Filters', 'Consumables']
        },
        {
            'supplier_id': 'SUP007',
            'supplier_name': 'Fan Pro',
            'contact_person': 'Chris Lee',
            'email': 'chris.lee@fanpro.com',
            'phone': '+1-555-0107',
            'address': '999 Cool Street, Denver, CO',
            'lead_time_days': 7,
            'reliability_score': 91.0,
            'on_time_delivery_rate': 93.0,
            'quality_score': 94.0,
            'preferred_supplier': False,
            'categories': ['Cooling', 'Fans']
        },
        {
            'supplier_id': 'SUP008',
            'supplier_name': 'Industrial Supply',
            'contact_person': 'Anna Taylor',
            'email': 'anna@industrialsupply.com',
            'phone': '+1-555-0108',
            'address': '111 Supply Chain Dr, St. Louis, MO',
            'lead_time_days': 3,
            'reliability_score': 89.0,
            'on_time_delivery_rate': 91.0,
            'quality_score': 86.0,
            'preferred_supplier': False,
            'categories': ['Seals', 'Gaskets', 'Hardware']
        },
        {
            'supplier_id': 'SUP009',
            'supplier_name': 'Temperature Co',
            'contact_person': 'David Anderson',
            'email': 'david@tempco.com',
            'phone': '+1-555-0109',
            'address': '222 Heat Way, Phoenix, AZ',
            'lead_time_days': 5,
            'reliability_score': 87.0,
            'on_time_delivery_rate': 90.0,
            'quality_score': 91.0,
            'preferred_supplier': False,
            'categories': ['Temperature', 'Electrical']
        },
        {
            'supplier_id': 'SUP010',
            'supplier_name': 'Metal Works',
            'contact_person': 'Rachel White',
            'email': 'rachel@metalworks.com',
            'phone': '+1-555-0110',
            'address': '333 Steel Ave, Birmingham, AL',
            'lead_time_days': 14,
            'reliability_score': 82.0,
            'on_time_delivery_rate': 78.0,
            'quality_score': 89.0,
            'preferred_supplier': False,
            'categories': ['Hardware', 'Custom Parts']
        }
    ]
    
    def __init__(self):
        self.suppliers: Dict[str, Supplier] = {}
        self._load_default_suppliers()
    
    def _load_default_suppliers(self):
        """Load default suppliers."""
        for supplier_data in self.DEFAULT_SUPPLIERS:
            supplier = Supplier(**supplier_data)
            self.suppliers[supplier.supplier_id] = supplier
    
    def add_supplier(self, supplier: Supplier) -> bool:
        """Add a new supplier."""
        if supplier.supplier_id in self.suppliers:
            return False
        self.suppliers[supplier.supplier_id] = supplier
        return True
    
    def update_supplier(self, supplier_id: str, updates: Dict[str, Any]) -> bool:
        """Update supplier information."""
        if supplier_id not in self.suppliers:
            return False
        
        supplier = self.suppliers[supplier_id]
        for key, value in updates.items():
            if hasattr(supplier, key):
                setattr(supplier, key, value)
        return True
    
    def get_supplier(self, supplier_id: str) -> Optional[Supplier]:
        """Get supplier by ID."""
        return self.suppliers.get(supplier_id)
    
    def get_supplier_by_name(self, name: str) -> Optional[Supplier]:
        """Get supplier by name."""
        for supplier in self.suppliers.values():
            if supplier.supplier_name.lower() == name.lower():
                return supplier
        return None
    
    def get_all_suppliers(self) -> List[Supplier]:
        """Get all suppliers."""
        return list(self.suppliers.values())
    
    def get_preferred_suppliers(self) -> List[Supplier]:
        """Get preferred suppliers."""
        return [s for s in self.suppliers.values() if s.preferred_supplier]
    
    def get_suppliers_by_category(self, category: str) -> List[Supplier]:
        """Get suppliers by category."""
        return [s for s in self.suppliers.values() if category in s.categories]
    
    def get_best_supplier(
        self,
        category: str,
        min_lead_time: bool = False
    ) -> Optional[Supplier]:
        """Get best supplier for a category."""
        suppliers = self.get_suppliers_by_category(category)
        
        if not suppliers:
            return None
        
        # Score suppliers
        def score(s):
            score_value = s.reliability_score * 0.4
            score_value += s.on_time_delivery_rate * 0.3
            score_value += s.quality_score * 0.2
            score_value += (100 - min(s.lead_time_days, 20)) * 0.1  # Prefer faster
            
            if min_lead_time:
                score_value += (100 - min(s.lead_time_days, 20)) * 0.1
            
            return score_value
        
        return max(suppliers, key=score)
    
    def get_supplier_performance(self, supplier_id: str) -> Optional[SupplierPerformance]:
        """Get supplier performance metrics."""
        supplier = self.get_supplier(supplier_id)
        if not supplier:
            return None
        
        # Calculate metrics (simplified - in production would query order history)
        total_orders = max(supplier.total_orders, 1)
        on_time = int(total_orders * supplier.on_time_delivery_rate / 100)
        
        return SupplierPerformance(
            supplier_id=supplier.supplier_id,
            supplier_name=supplier.supplier_name,
            total_orders=total_orders,
            on_time_deliveries=on_time,
            late_deliveries=total_orders - on_time,
            on_time_rate=supplier.on_time_delivery_rate,
            average_lead_time=supplier.lead_time_days,
            quality_issues=max(1, int(total_orders * (100 - supplier.quality_score) / 100)),
            total_spend=total_orders * 1000,  # Placeholder
            reliability_score=supplier.reliability_score
        )
    
    def record_order(self, supplier_id: str):
        """Record an order from a supplier."""
        supplier = self.get_supplier(supplier_id)
        if supplier:
            supplier.total_orders += 1
            supplier.last_order_date = datetime.now()
    
    def get_all_performances(self) -> List[SupplierPerformance]:
        """Get performance for all suppliers."""
        return [
            self.get_supplier_performance(sid)
            for sid in self.suppliers
            if self.get_supplier_performance(sid)
        ]
    
    def get_supplier_summary(self) -> Dict[str, Any]:
        """Get supplier summary statistics."""
        suppliers = list(self.suppliers.values())
        
        return {
            'total_suppliers': len(suppliers),
            'preferred_suppliers': sum(1 for s in suppliers if s.preferred_supplier),
            'average_reliability': sum(s.reliability_score for s in suppliers) / len(suppliers),
            'average_lead_time': sum(s.lead_time_days for s in suppliers) / len(suppliers),
            'high_performers': sum(1 for s in suppliers if s.reliability_score >= 90)
        }


# Singleton instance
_supplier_engine: Optional[SupplierEngine] = None


def get_supplier_engine() -> SupplierEngine:
    """Get global supplier engine instance."""
    global _supplier_engine
    if _supplier_engine is None:
        _supplier_engine = SupplierEngine()
    return _supplier_engine