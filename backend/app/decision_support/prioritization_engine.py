"""
Maintenance Prioritization Engine.

This module prioritizes maintenance actions based on risk scores,
failure probability, RUL, equipment criticality, and other factors.
"""
import uuid
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from app.decision_support.risk_engine import get_plant_risk_engine, RiskScore


@dataclass
class MaintenancePriority:
    """Maintenance priority for equipment."""
    priority_id: str
    equipment_id: str
    equipment_name: str
    rank: int
    priority_score: float
    priority_level: str  # P1, P2, P3, P4
    risk_score: float
    failure_probability: float
    rul_days: int
    criticality: float
    recommended_action: str
    reason: List[str]
    estimated_downtime: float
    estimated_cost: float
    spare_available: bool
    procurement_lead_time: Optional[int] = None
    production_impact: str = "high"
    created_at: datetime = field(default_factory=datetime.now)


class PrioritizationEngine:
    """
    Prioritize maintenance actions across all equipment.
    
    Factors:
    - Risk score
    - Failure probability
    - Remaining useful life
    - Equipment criticality
    - Spare availability
    - Production impact
    """
    
    def __init__(self):
        self.risk_engine = get_plant_risk_engine()
        self.priorities: List[MaintenancePriority] = []
    
    def prioritize(
        self,
        risk_scores: List[RiskScore],
        spare_availability: Optional[Dict[str, bool]] = None
    ) -> List[MaintenancePriority]:
        """
        Prioritize equipment based on risk scores.
        
        Args:
            risk_scores: List of risk scores
            spare_availability: Dict mapping equipment_id to availability
            
        Returns:
            List of MaintenancePriority sorted by priority
        """
        priorities = []
        
        for risk in risk_scores:
            # Calculate priority score
            priority_score = self._calculate_priority_score(risk)
            
            # Determine priority level
            priority_level = self._get_priority_level(priority_score)
            
            # Determine recommended action
            action = self._get_recommended_action(risk, priority_level)
            
            # Determine production impact
            production_impact = self._get_production_impact(risk.criticality_score)
            
            # Check spare availability
            spare_avail = spare_availability.get(risk.equipment_id, True) if spare_availability else True
            
            priority = MaintenancePriority(
                priority_id=str(uuid.uuid4()),
                equipment_id=risk.equipment_id,
                equipment_name=risk.equipment_name,
                rank=0,  # Will be set after sorting
                priority_score=priority_score,
                priority_level=priority_level,
                risk_score=risk.risk_score,
                failure_probability=risk.failure_probability,
                rul_days=risk.rul_days,
                criticality=risk.criticality_score,
                recommended_action=action,
                reason=risk.reasons,
                estimated_downtime=self._estimate_downtime(priority_level),
                estimated_cost=self._estimate_cost(priority_level),
                spare_available=spare_avail,
                production_impact=production_impact
            )
            
            priorities.append(priority)
        
        # Sort by priority score (descending)
        priorities.sort(key=lambda p: p.priority_score, reverse=True)
        
        # Assign ranks
        for i, priority in enumerate(priorities, 1):
            priority.rank = i
        
        self.priorities = priorities
        return priorities
    
    def _calculate_priority_score(self, risk: RiskScore) -> float:
        """Calculate overall priority score."""
        # Weighted combination
        score = risk.risk_score * 0.4
        score += risk.failure_probability * 100 * 0.25
        
        # RUL factor (shorter = higher priority)
        if risk.rul_days <= 7:
            score += 20
        elif risk.rul_days <= 14:
            score += 15
        elif risk.rul_days <= 30:
            score += 10
        elif risk.rul_days <= 60:
            score += 5
        
        # Criticality factor
        score += risk.criticality_score * 0.15
        
        return min(100, score)
    
    def _get_priority_level(self, score: float) -> str:
        """Get priority level from score."""
        if score >= 80:
            return 'P1'
        elif score >= 65:
            return 'P2'
        elif score >= 50:
            return 'P3'
        else:
            return 'P4'
    
    def _get_recommended_action(self, risk: RiskScore, priority: str) -> str:
        """Get recommended action based on risk and priority."""
        if priority == 'P1':
            if risk.rul_days <= 7:
                return "Schedule immediate maintenance (within 24 hours)"
            elif risk.rul_days <= 14:
                return "Schedule urgent maintenance (within 3 days)"
            else:
                return "Schedule maintenance this week"
        elif priority == 'P2':
            return "Schedule maintenance within 2 weeks"
        elif priority == 'P3':
            return "Schedule maintenance within 1 month"
        else:
            return "Include in preventive maintenance schedule"
    
    def _get_production_impact(self, criticality: float) -> str:
        """Get production impact level."""
        if criticality >= 80:
            return 'critical'
        elif criticality >= 60:
            return 'high'
        elif criticality >= 40:
            return 'medium'
        else:
            return 'low'
    
    def _estimate_downtime(self, priority: str) -> float:
        """Estimate downtime hours based on priority."""
        estimates = {
            'P1': 8.0,
            'P2': 4.0,
            'P3': 2.0,
            'P4': 1.0
        }
        return estimates.get(priority, 2.0)
    
    def _estimate_cost(self, priority: str) -> float:
        """Estimate maintenance cost based on priority."""
        estimates = {
            'P1': 5000,
            'P2': 3000,
            'P3': 1500,
            'P4': 500
        }
        return estimates.get(priority, 1000)
    
    def get_top_priorities(self, count: int = 10) -> List[MaintenancePriority]:
        """Get top N priorities."""
        return self.priorities[:count]
    
    def get_p1_priorities(self) -> List[MaintenancePriority]:
        """Get all P1 priorities."""
        return [p for p in self.priorities if p.priority_level == 'P1']
    
    def get_p1_and_p2(self) -> List[MaintenancePriority]:
        """Get all P1 and P2 priorities."""
        return [p for p in self.priorities if p.priority_level in ['P1', 'P2']]
    
    def get_priority_summary(self) -> Dict[str, Any]:
        """Get summary of priorities."""
        return {
            'total_equipment': len(self.priorities),
            'p1_count': sum(1 for p in self.priorities if p.priority_level == 'P1'),
            'p2_count': sum(1 for p in self.priorities if p.priority_level == 'P2'),
            'p3_count': sum(1 for p in self.priorities if p.priority_level == 'P3'),
            'p4_count': sum(1 for p in self.priorities if p.priority_level == 'P4'),
            'total_estimated_downtime': sum(p.estimated_downtime for p in self.priorities),
            'total_estimated_cost': sum(p.estimated_cost for p in self.priorities),
            'critical_production_impact': sum(1 for p in self.priorities if p.production_impact == 'critical')
        }


# Singleton instance
_prioritization_engine: Optional[PrioritizationEngine] = None


def get_prioritization_engine() -> PrioritizationEngine:
    """Get global prioritization engine instance."""
    global _prioritization_engine
    if _prioritization_engine is None:
        _prioritization_engine = PrioritizationEngine()
    return _prioritization_engine