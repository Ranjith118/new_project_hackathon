"""
Procurement Intelligence Engine.

This module generates procurement plans, analyzes risks,
and prioritizes procurement needs.
"""
import uuid
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from app.procurement.inventory_engine import get_inventory_engine, SparePart
from app.procurement.mapping_engine import get_mapping_engine, PartMapping


@dataclass
class ProcurementRequest:
    """Procurement request for a part."""
    request_id: str
    part_id: str
    part_name: str
    part_number: str
    quantity: int
    priority: str  # P1, P2, P3, P4
    urgency: str  # immediate, high, medium, low
    reason: str
    supplier: str
    lead_time_days: int
    estimated_cost: float
    request_date: datetime = field(default_factory=datetime.now)
    required_by: Optional[datetime] = None
    status: str = "pending"  # pending, approved, ordered, received


@dataclass
class ProcurementPlan:
    """Complete procurement plan."""
    plan_id: str
    equipment_name: str
    root_cause: str
    created_at: datetime
    requests: List[ProcurementRequest]
    total_estimated_cost: float
    critical_requests: int
    lead_time_risk: bool
    availability_risk: bool


@dataclass
class ProcurementRisk:
    """Procurement risk assessment."""
    risk_id: str
    part_id: str
    part_name: str
    risk_type: str  # lead_time, availability, cost
    severity: str  # critical, high, medium, low
    description: str
    mitigation: str


class ProcurementEngine:
    """
    Generate procurement plans and analyze procurement risks.
    """
    
    def __init__(self):
        self.inventory = get_inventory_engine()
        self.mapping = get_mapping_engine()
        self.requests: Dict[str, ProcurementRequest] = {}
    
    def generate_procurement_plan(
        self,
        equipment_name: str,
        equipment_type: str,
        root_cause: str,
        failure_probability: Optional[float] = None,
        rul_days: Optional[int] = None
    ) -> ProcurementPlan:
        """
        Generate procurement plan based on equipment and root cause.
        
        Args:
            equipment_name: Name of equipment
            equipment_type: Type of equipment
            root_cause: Identified root cause
            failure_probability: Failure probability (0-1)
            rul_days: Remaining useful life in days
            
        Returns:
            ProcurementPlan with all required procurement requests
        """
        plan_id = str(uuid.uuid4())
        
        # Get required spare parts
        required_parts = self.mapping.get_spare_parts(
            equipment_type=equipment_type,
            root_cause=root_cause,
            failure_probability=failure_probability
        )
        
        requests = []
        total_cost = 0.0
        critical_count = 0
        lead_time_risk = False
        availability_risk = False
        
        for part_mapping in required_parts:
            # Check inventory availability
            part = self.inventory.get_part(part_mapping.part_id)
            
            if not part:
                continue
            
            # Calculate required quantity
            available_stock = part.stock_quantity
            required_qty = part_mapping.quantity_required
            shortage = max(0, required_qty - available_stock)
            
            if shortage > 0:
                # Determine priority
                priority = self._determine_priority(
                    failure_probability, rul_days, part_mapping.urgency, shortage
                )
                
                # Check lead time risk
                lead_time_risk_flag = False
                if rul_days and part.lead_time_days > rul_days:
                    lead_time_risk_flag = True
                    lead_time_risk = True
                
                # Create procurement request
                request = ProcurementRequest(
                    request_id=str(uuid.uuid4()),
                    part_id=part.part_id,
                    part_name=part.part_name,
                    part_number=part.part_number,
                    quantity=shortage,
                    priority=priority,
                    urgency=part_mapping.urgency,
                    reason=f"Required for {root_cause}",
                    supplier=part.supplier,
                    lead_time_days=part.lead_time_days,
                    estimated_cost=shortage * part.unit_cost,
                    required_by=datetime.now() + timedelta(days=part.lead_time_days)
                )
                
                requests.append(request)
                total_cost += request.estimated_cost
                
                if priority == 'P1':
                    critical_count += 1
                
                if available_stock == 0:
                    availability_risk = True
        
        return ProcurementPlan(
            plan_id=plan_id,
            equipment_name=equipment_name,
            root_cause=root_cause,
            created_at=datetime.now(),
            requests=requests,
            total_estimated_cost=total_cost,
            critical_requests=critical_count,
            lead_time_risk=lead_time_risk,
            availability_risk=availability_risk
        )
    
    def _determine_priority(
        self,
        failure_probability: Optional[float],
        rul_days: Optional[int],
        part_urgency: str,
        shortage: int
    ) -> str:
        """Determine procurement priority."""
        # Check failure probability
        if failure_probability and failure_probability >= 0.85:
            return 'P1'
        
        # Check RUL vs lead time
        if rul_days and rul_days <= 15:
            return 'P1'
        
        # Check part urgency
        if part_urgency == 'critical':
            return 'P1'
        
        # Check failure probability
        if failure_probability and failure_probability >= 0.70:
            return 'P2'
        
        # Check RUL
        if rul_days and rul_days <= 30:
            return 'P2'
        
        # Check part urgency
        if part_urgency == 'high':
            return 'P2'
        
        # Default to P3
        return 'P3'
    
    def analyze_procurement_risks(
        self,
        equipment_name: str,
        equipment_type: str,
        root_cause: str,
        failure_probability: Optional[float] = None,
        rul_days: Optional[int] = None
    ) -> List[ProcurementRisk]:
        """Analyze procurement risks."""
        risks = []
        
        # Get required parts
        required_parts = self.mapping.get_spare_parts(
            equipment_type=equipment_type,
            root_cause=root_cause,
            failure_probability=failure_probability
        )
        
        for part_mapping in required_parts:
            part = self.inventory.get_part(part_mapping.part_id)
            if not part:
                continue
            
            # Check stock availability
            if part.stock_quantity < part_mapping.quantity_required:
                # Out of stock or insufficient
                if part.stock_quantity == 0:
                    risk = ProcurementRisk(
                        risk_id=str(uuid.uuid4()),
                        part_id=part.part_id,
                        part_name=part.part_name,
                        risk_type='availability',
                        severity='critical',
                        description=f"Part {part.part_name} is out of stock. {part_mapping.quantity_required} required.",
                        mitigation=f"Order {part_mapping.quantity_required * 2} units from {part.supplier}"
                    )
                    risks.append(risk)
                elif part.stock_quantity < part_mapping.quantity_required:
                    risk = ProcurementRisk(
                        risk_id=str(uuid.uuid4()),
                        part_id=part.part_id,
                        part_name=part.part_name,
                        risk_type='availability',
                        severity='high',
                        description=f"Insufficient stock: {part.stock_quantity} available, {part_mapping.quantity_required} required.",
                        mitigation=f"Order {part_mapping.quantity_required - part.stock_quantity} units"
                    )
                    risks.append(risk)
            
            # Check lead time risk
            if rul_days and part.lead_time_days > rul_days:
                days_short = part.lead_time_days - rul_days
                risk = ProcurementRisk(
                    risk_id=str(uuid.uuid4()),
                    part_id=part.part_id,
                    part_name=part.part_name,
                    risk_type='lead_time',
                    severity='high',
                    description=f"Lead time ({part.lead_time_days} days) exceeds RUL ({rul_days} days) by {days_short} days.",
                    mitigation="Expedite order or arrange temporary workaround"
                )
                risks.append(risk)
            
            # Check failure probability risk
            if failure_probability and failure_probability >= 0.8:
                if part.stock_quantity < part_mapping.quantity_required:
                    risk = ProcurementRisk(
                        risk_id=str(uuid.uuid4()),
                        part_id=part.part_id,
                        part_name=part.part_name,
                        risk_type='cost',
                        severity='high',
                        description=f"High failure probability ({failure_probability*100:.0f}%) with insufficient stock.",
                        mitigation="Stock up immediately to avoid downtime"
                    )
                    risks.append(risk)
        
        return risks
    
    def create_purchase_request(
        self,
        part_id: str,
        quantity: int,
        priority: str,
        reason: str
    ) -> ProcurementRequest:
        """Create a purchase request."""
        part = self.inventory.get_part(part_id)
        if not part:
            raise ValueError(f"Part {part_id} not found")
        
        request = ProcurementRequest(
            request_id=str(uuid.uuid4()),
            part_id=part_id,
            part_name=part.part_name,
            part_number=part.part_number,
            quantity=quantity,
            priority=priority,
            urgency='high' if priority in ['P1', 'P2'] else 'medium',
            reason=reason,
            supplier=part.supplier,
            lead_time_days=part.lead_time_days,
            estimated_cost=quantity * part.unit_cost
        )
        
        self.requests[request.request_id] = request
        return request
    
    def get_pending_requests(self) -> List[ProcurementRequest]:
        """Get all pending procurement requests."""
        return [r for r in self.requests.values() if r.status == 'pending']
    
    def get_requests_by_priority(self, priority: str) -> List[ProcurementRequest]:
        """Get requests by priority."""
        return [r for r in self.requests.values() if r.priority == priority and r.status == 'pending']
    
    def approve_request(self, request_id: str) -> bool:
        """Approve a procurement request."""
        if request_id in self.requests:
            self.requests[request_id].status = 'approved'
            return True
        return False
    
    def order_request(self, request_id: str) -> bool:
        """Mark request as ordered."""
        if request_id in self.requests:
            self.requests[request_id].status = 'ordered'
            return True
        return False
    
    def receive_request(self, request_id: str) -> bool:
        """Mark request as received and update inventory."""
        if request_id not in self.requests:
            return False
        
        request = self.requests[request_id]
        request.status = 'received'
        
        # Update inventory
        self.inventory.adjust_stock(
            request.part_id,
            self.inventory.get_part(request.part_id).stock_quantity + request.quantity,
            f"Purchase order {request.request_id} received"
        )
        
        return True


# Singleton instance
_procurement_engine: Optional[ProcurementEngine] = None


def get_procurement_engine() -> ProcurementEngine:
    """Get global procurement engine instance."""
    global _procurement_engine
    if _procurement_engine is None:
        _procurement_engine = ProcurementEngine()
    return _procurement_engine