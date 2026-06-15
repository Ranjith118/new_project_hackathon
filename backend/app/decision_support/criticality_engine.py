"""
Equipment Criticality Engine.

This module calculates equipment criticality scores based on
multiple factors including production dependency, safety impact,
environmental impact, downtime cost, and replacement difficulty.
"""
import uuid
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class CriticalityScore:
    """Equipment criticality score with breakdown."""
    equipment_id: str
    equipment_name: str
    equipment_type: str
    criticality_score: float  # 0-100
    criticality_level: str  # critical, high, medium, low
    factors: Dict[str, float]
    production_dependency: float
    safety_impact: float
    environmental_impact: float
    downtime_cost: float
    replacement_difficulty: float
    last_updated: datetime = field(default_factory=datetime.now)


class CriticalityEngine:
    """
    Calculate and manage equipment criticality scores.
    
    Criticality considers:
    - Production dependency (how critical to production flow)
    - Safety impact (potential safety hazards)
    - Environmental impact (environmental compliance)
    - Downtime cost (cost per hour of downtime)
    - Replacement difficulty (time/resources to replace)
    """
    
    # Default criticality scores for steel plant equipment
    DEFAULT_CRITICALITY = {
        'blast_furnace_fan': {
            'equipment_name': 'Blast Furnace Fan',
            'equipment_type': 'compressor',
            'production_dependency': 95,
            'safety_impact': 90,
            'environmental_impact': 85,
            'downtime_cost': 950000,    # ₹9,50,000/hr (was $10,000 × 95)
            'replacement_difficulty': 85,
            'level': 'critical'
        },
        'rolling_mill_motor': {
            'equipment_name': 'Rolling Mill Motor',
            'equipment_type': 'motor',
            'production_dependency': 90,
            'safety_impact': 80,
            'environmental_impact': 70,
            'downtime_cost': 807500,    # ₹8,07,500/hr (was $8,500 × 95)
            'replacement_difficulty': 80,
            'level': 'critical'
        },
        'main_compressor': {
            'equipment_name': 'Main Compressor',
            'equipment_type': 'compressor',
            'production_dependency': 92,
            'safety_impact': 85,
            'environmental_impact': 75,
            'downtime_cost': 855000,    # ₹8,55,000/hr (was $9,000 × 95)
            'replacement_difficulty': 75,
            'level': 'critical'
        },
        'cooling_pump_a': {
            'equipment_name': 'Cooling Pump A',
            'equipment_type': 'pump',
            'production_dependency': 75,
            'safety_impact': 65,
            'environmental_impact': 60,
            'downtime_cost': 475000,    # ₹4,75,000/hr (was $5,000 × 95)
            'replacement_difficulty': 50,
            'level': 'high'
        },
        'conveyor_belt_system': {
            'equipment_name': 'Conveyor Belt System',
            'equipment_type': 'conveyor',
            'production_dependency': 80,
            'safety_impact': 70,
            'environmental_impact': 50,
            'downtime_cost': 427500,    # ₹4,27,500/hr (was $4,500 × 95)
            'replacement_difficulty': 40,
            'level': 'high'
        },
        'slab_reheating_furnace': {
            'equipment_name': 'Slab Reheating Furnace',
            'equipment_type': 'furnace',
            'production_dependency': 88,
            'safety_impact': 95,
            'environmental_impact': 90,
            'downtime_cost': 712500,    # ₹7,12,500/hr (was $7,500 × 95)
            'replacement_difficulty': 70,
            'level': 'critical'
        },
        'hot_rolling_mill': {
            'equipment_name': 'Hot Rolling Mill',
            'equipment_type': 'mill',
            'production_dependency': 92,
            'safety_impact': 85,
            'environmental_impact': 80,
            'downtime_cost': 902500,    # ₹9,02,500/hr (was $9,500 × 95)
            'replacement_difficulty': 85,
            'level': 'critical'
        },
        'cold_rolling_mill': {
            'equipment_name': 'Cold Rolling Mill',
            'equipment_type': 'mill',
            'production_dependency': 85,
            'safety_impact': 75,
            'environmental_impact': 70,
            'downtime_cost': 760000,    # ₹7,60,000/hr (was $8,000 × 95)
            'replacement_difficulty': 80,
            'level': 'critical'
        },
        'crane_motor_1': {
            'equipment_name': 'Crane Motor 1',
            'equipment_type': 'crane',
            'production_dependency': 70,
            'safety_impact': 90,
            'environmental_impact': 40,
            'downtime_cost': 380000,    # ₹3,80,000/hr (was $4,000 × 95)
            'replacement_difficulty': 45,
            'level': 'high'
        },
        'cooling_pump_b': {
            'equipment_name': 'Cooling Pump B',
            'equipment_type': 'pump',
            'production_dependency': 60,
            'safety_impact': 55,
            'environmental_impact': 50,
            'downtime_cost': 332500,    # ₹3,32,500/hr (was $3,500 × 95)
            'replacement_difficulty': 40,
            'level': 'medium'
        },
        'lubrication_system': {
            'equipment_name': 'Central Lubrication System',
            'equipment_type': 'system',
            'production_dependency': 55,
            'safety_impact': 50,
            'environmental_impact': 60,
            'downtime_cost': 285000,    # ₹2,85,000/hr (was $3,000 × 95)
            'replacement_difficulty': 35,
            'level': 'medium'
        },
        'hydraulic_power_unit': {
            'equipment_name': 'Hydraulic Power Unit',
            'equipment_type': 'hydraulic',
            'production_dependency': 65,
            'safety_impact': 75,
            'environmental_impact': 70,
            'downtime_cost': 427500,    # ₹4,27,500/hr (was $4,500 × 95)
            'replacement_difficulty': 55,
            'level': 'high'
        }
    }
    
    # Weight factors for criticality calculation
    WEIGHTS = {
        'production_dependency': 0.35,
        'safety_impact': 0.25,
        'downtime_cost': 0.20,
        'replacement_difficulty': 0.10,
        'environmental_impact': 0.10
    }
    
    def __init__(self):
        self.criticality_scores: Dict[str, CriticalityScore] = {}
        self._load_default_criticality()
    
    def _load_default_criticality(self):
        """Load default criticality scores."""
        for equip_id, data in self.DEFAULT_CRITICALITY.items():
            factors = {
                'production_dependency': data['production_dependency'],
                'safety_impact': data['safety_impact'],
                'environmental_impact': data['environmental_impact'],
                'downtime_cost': data['downtime_cost'] / 100,  # Normalize
                'replacement_difficulty': data['replacement_difficulty']
            }
            
            score = self._calculate_criticality_score(factors)
            
            self.criticality_scores[equip_id] = CriticalityScore(
                equipment_id=equip_id,
                equipment_name=data['equipment_name'],
                equipment_type=data['equipment_type'],
                criticality_score=score,
                criticality_level=data['level'],
                factors=factors,
                production_dependency=data['production_dependency'],
                safety_impact=data['safety_impact'],
                environmental_impact=data['environmental_impact'],
                downtime_cost=data['downtime_cost'],
                replacement_difficulty=data['replacement_difficulty']
            )
    
    def _calculate_criticality_score(self, factors: Dict[str, float]) -> float:
        """Calculate overall criticality score from factors."""
        score = 0.0
        
        for factor_name, weight in self.WEIGHTS.items():
            if factor_name in factors:
                score += factors[factor_name] * weight
        
        return min(100, max(0, score))
    
    def get_criticality(self, equipment_id: str) -> Optional[CriticalityScore]:
        """Get criticality score for equipment."""
        return self.criticality_scores.get(equipment_id)
    
    def get_all_criticality(self) -> List[CriticalityScore]:
        """Get all criticality scores."""
        return list(self.criticality_scores.values())
    
    def get_critical_equipment(self) -> List[CriticalityScore]:
        """Get all critical level equipment."""
        return [c for c in self.criticality_scores.values() 
                if c.criticality_level == 'critical']
    
    def get_high_equipment(self) -> List[CriticalityScore]:
        """Get all high criticality equipment."""
        return [c for c in self.criticality_scores.values() 
                if c.criticality_level == 'high']
    
    def update_criticality(
        self,
        equipment_id: str,
        factors: Dict[str, float]
    ) -> bool:
        """Update criticality score for equipment."""
        if equipment_id not in self.criticality_scores:
            return False
        
        cs = self.criticality_scores[equipment_id]
        
        # Update factors
        for key, value in factors.items():
            if key in cs.factors:
                cs.factors[key] = value
        
        # Recalculate score
        cs.criticality_score = self._calculate_criticality_score(cs.factors)
        cs.criticality_level = self._get_level(cs.criticality_score)
        cs.last_updated = datetime.now()
        
        return True
    
    def _get_level(self, score: float) -> str:
        """Get criticality level from score."""
        if score >= 80:
            return 'critical'
        elif score >= 60:
            return 'high'
        elif score >= 40:
            return 'medium'
        else:
            return 'low'
    
    def get_criticality_summary(self) -> Dict[str, Any]:
        """Get summary of criticality scores."""
        scores = list(self.criticality_scores.values())
        
        return {
            'total_equipment': len(scores),
            'critical_count': sum(1 for s in scores if s.criticality_level == 'critical'),
            'high_count': sum(1 for s in scores if s.criticality_level == 'high'),
            'medium_count': sum(1 for s in scores if s.criticality_level == 'medium'),
            'low_count': sum(1 for s in scores if s.criticality_level == 'low'),
            'average_criticality': sum(s.criticality_score for s in scores) / len(scores) if scores else 0,
            'total_downtime_cost_per_hour': sum(s.downtime_cost for s in scores)
        }


# Singleton instance
_criticality_engine: Optional[CriticalityEngine] = None


def get_criticality_engine() -> CriticalityEngine:
    """Get global criticality engine instance."""
    global _criticality_engine
    if _criticality_engine is None:
        _criticality_engine = CriticalityEngine()
    return _criticality_engine