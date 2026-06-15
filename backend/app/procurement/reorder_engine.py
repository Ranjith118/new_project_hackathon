"""
Reorder Recommendation Engine.

This module generates automatic reorder recommendations
based on stock levels and usage patterns.
"""
import uuid
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from app.procurement.inventory_engine import get_inventory_engine, SparePart


@dataclass
class ReorderRecommendation:
    """Reorder recommendation."""
    recommendation_id: str
    part_id: str
    part_name: str
    part_number: str
    current_stock: int
    minimum_stock: int
    reorder_level: int
    recommended_quantity: int
    urgency: str  # critical, high, medium, low
    reason: str
    estimated_cost: float
    supplier: str
    lead_time_days: int
    created_at: datetime = field(default_factory=datetime.now)


class ReorderEngine:
    """
    Generate automatic reorder recommendations.
    """
    
    def __init__(self):
        self.inventory = get_inventory_engine()
    
    def generate_all_recommendations(self) -> List[ReorderRecommendation]:
        """Generate reorder recommendations for all parts below reorder level."""
        recommendations = []
        
        for part in self.inventory.get_all_parts():
            if part.stock_quantity <= part.reorder_level:
                rec = self._create_recommendation(part)
                if rec:
                    recommendations.append(rec)
        
        # Sort by urgency
        urgency_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
        recommendations.sort(key=lambda r: urgency_order.get(r.urgency, 4))
        
        return recommendations
    
    def generate_for_part(self, part_id: str) -> Optional[ReorderRecommendation]:
        """Generate reorder recommendation for a specific part."""
        part = self.inventory.get_part(part_id)
        if not part:
            return None
        
        if part.stock_quantity > part.reorder_level:
            return None
        
        return self._create_recommendation(part)
    
    def _create_recommendation(self, part: SparePart) -> Optional[ReorderRecommendation]:
        """Create reorder recommendation for a part."""
        # Determine urgency based on stock level
        if part.stock_quantity == 0:
            urgency = 'critical'
        elif part.stock_quantity <= part.minimum_stock / 2:
            urgency = 'high'
        elif part.stock_quantity <= part.minimum_stock:
            urgency = 'medium'
        else:
            urgency = 'low'
        
        # Calculate recommended quantity
        # Order enough to bring stock to minimum + safety buffer
        safety_factor = 2.0 if urgency in ['critical', 'high'] else 1.5
        recommended_qty = int((part.minimum_stock - part.stock_quantity + part.reorder_level) * safety_factor)
        
        # Ensure minimum order quantity
        recommended_qty = max(recommended_qty, part.minimum_stock)
        
        # Generate reason
        if part.stock_quantity == 0:
            reason = f"OUT OF STOCK - Order immediately to avoid equipment downtime"
        elif part.stock_quantity <= part.reorder_level:
            reason = f"Stock ({part.stock_quantity}) at or below reorder level ({part.reorder_level})"
        else:
            reason = f"Stock ({part.stock_quantity}) below minimum ({part.minimum_stock})"
        
        # Add urgency reason
        if part.stock_quantity == 0:
            reason += f". Critical spare required for maintenance."
        elif urgency in ['critical', 'high']:
            reason += f". High equipment criticality requires buffer stock."
        
        return ReorderRecommendation(
            recommendation_id=str(uuid.uuid4()),
            part_id=part.part_id,
            part_name=part.part_name,
            part_number=part.part_number,
            current_stock=part.stock_quantity,
            minimum_stock=part.minimum_stock,
            reorder_level=part.reorder_level,
            recommended_quantity=recommended_qty,
            urgency=urgency,
            reason=reason,
            estimated_cost=recommended_qty * part.unit_cost,
            supplier=part.supplier,
            lead_time_days=part.lead_time_days
        )
    
    def get_critical_reorders(self) -> List[ReorderRecommendation]:
        """Get critical reorder recommendations."""
        all_recs = self.generate_all_recommendations()
        return [r for r in all_recs if r.urgency in ['critical', 'high']]
    
    def get_urgent_reorders(self) -> List[ReorderRecommendation]:
        """Get urgent reorder recommendations (out of stock only)."""
        all_recs = self.generate_all_recommendations()
        return [r for r in all_recs if r.urgency == 'critical']
    
    def get_reorder_summary(self) -> Dict[str, Any]:
        """Get summary of reorder recommendations."""
        recommendations = self.generate_all_recommendations()
        
        total_cost = sum(r.estimated_cost for r in recommendations)
        critical_count = sum(1 for r in recommendations if r.urgency == 'critical')
        high_count = sum(1 for r in recommendations if r.urgency == 'high')
        medium_count = sum(1 for r in recommendations if r.urgency == 'medium')
        low_count = sum(1 for r in recommendations if r.urgency == 'low')
        
        # Group by supplier
        by_supplier = {}
        for rec in recommendations:
            if rec.supplier not in by_supplier:
                by_supplier[rec.supplier] = {'count': 0, 'cost': 0}
            by_supplier[rec.supplier]['count'] += 1
            by_supplier[rec.supplier]['cost'] += rec.estimated_cost
        
        return {
            'total_recommendations': len(recommendations),
            'critical_count': critical_count,
            'high_count': high_count,
            'medium_count': medium_count,
            'low_count': low_count,
            'total_estimated_cost': total_cost,
            'by_supplier': by_supplier
        }


# Singleton instance
_reorder_engine: Optional[ReorderEngine] = None


def get_reorder_engine() -> ReorderEngine:
    """Get global reorder engine instance."""
    global _reorder_engine
    if _reorder_engine is None:
        _reorder_engine = ReorderEngine()
    return _reorder_engine