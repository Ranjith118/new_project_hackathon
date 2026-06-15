"""
Plant Risk Scoring Engine.

This module calculates comprehensive risk scores for all plant equipment
by combining failure probability, RUL, health scores, anomaly detection,
and criticality data.
"""
import uuid
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime

from app.decision_support.criticality_engine import get_criticality_engine


@dataclass
class RiskScore:
    """Comprehensive risk score for equipment."""
    equipment_id: str
    equipment_name: str
    equipment_type: str
    risk_score: float  # 0-100
    risk_level: str  # critical, high, medium, low
    failure_probability: float
    rul_days: int
    health_score: int
    anomaly_score: float
    criticality_score: float
    components: Dict[str, float]
    reasons: List[str]
    last_updated: datetime = field(default_factory=datetime.now)


class PlantRiskEngine:
    """
    Calculate plant-wide risk scores.
    
    Combines:
    - Failure probability from prediction engine
    - Remaining useful life
    - Health score from monitoring
    - Anomaly scores from detection
    - Equipment criticality
    """
    
    # Weight factors for risk calculation
    WEIGHTS = {
        'failure_probability': 0.30,
        'rul': 0.20,
        'health_score': 0.15,
        'anomaly_score': 0.15,
        'criticality': 0.20
    }
    
    def __init__(self):
        self.criticality = get_criticality_engine()
        self.risk_scores: Dict[str, RiskScore] = {}
    
    def calculate_risk(
        self,
        equipment_id: str,
        equipment_name: str,
        equipment_type: str,
        failure_probability: Optional[float] = None,
        rul_days: Optional[int] = None,
        health_score: Optional[int] = None,
        anomaly_score: Optional[float] = None
    ) -> RiskScore:
        """
        Calculate risk score for equipment.
        
        Args:
            equipment_id: Equipment identifier
            equipment_name: Equipment name
            equipment_type: Type of equipment
            failure_probability: Failure probability (0-1)
            rul_days: Remaining useful life in days
            health_score: Health score (0-100)
            anomaly_score: Anomaly score from detection
            
        Returns:
            RiskScore with all components
        """
        # Get criticality
        criticality = self.criticality.get_criticality(equipment_id)
        criticality_score = criticality.criticality_score if criticality else 50
        
        # Normalize inputs
        failure_prob_norm = self._normalize_failure_prob(failure_probability)
        rul_norm = self._normalize_rul(rul_days)
        health_norm = self._normalize_health(health_score)
        anomaly_norm = self._normalize_anomaly(anomaly_score)
        
        # Calculate components
        components = {
            'failure_probability': failure_prob_norm,
            'rul': rul_norm,
            'health_score': health_norm,
            'anomaly_score': anomaly_norm,
            'criticality': criticality_score
        }
        
        # Calculate overall risk score
        risk_score = 0.0
        for component, weight in self.WEIGHTS.items():
            risk_score += components.get(component, 50) * weight
        
        risk_score = min(100, max(0, risk_score))
        
        # Determine risk level
        risk_level = self._get_risk_level(risk_score)
        
        # Generate reasons
        reasons = self._generate_reasons(
            failure_probability, rul_days, health_score, 
            anomaly_score, criticality_score
        )
        
        risk = RiskScore(
            equipment_id=equipment_id,
            equipment_name=equipment_name,
            equipment_type=equipment_type,
            risk_score=risk_score,
            risk_level=risk_level,
            failure_probability=failure_probability or 0,
            rul_days=rul_days or 999,
            health_score=health_score or 100,
            anomaly_score=anomaly_score or 0,
            criticality_score=criticality_score,
            components=components,
            reasons=reasons
        )
        
        self.risk_scores[equipment_id] = risk
        return risk
    
    def _normalize_failure_prob(self, prob: Optional[float]) -> float:
        """Normalize failure probability to 0-100."""
        if prob is None:
            return 50
        return prob * 100
    
    def _normalize_rul(self, rul_days: Optional[int]) -> float:
        """Normalize RUL (shorter = higher risk)."""
        if rul_days is None:
            return 50
        if rul_days <= 7:
            return 100
        elif rul_days <= 14:
            return 90
        elif rul_days <= 30:
            return 70
        elif rul_days <= 60:
            return 50
        elif rul_days <= 90:
            return 30
        else:
            return 10
    
    def _normalize_health(self, health: Optional[int]) -> float:
        """Normalize health score (lower = higher risk)."""
        if health is None:
            return 50
        return 100 - health
    
    def _normalize_anomaly(self, anomaly: Optional[float]) -> float:
        """Normalize anomaly score."""
        if anomaly is None:
            return 50
        # Negative anomaly means more anomalous
        return max(0, min(100, (anomaly + 1) * 50))
    
    def _get_risk_level(self, score: float) -> str:
        """Get risk level from score."""
        if score >= 80:
            return 'critical'
        elif score >= 60:
            return 'high'
        elif score >= 40:
            return 'medium'
        else:
            return 'low'
    
    def _generate_reasons(
        self,
        failure_prob: Optional[float],
        rul_days: Optional[int],
        health_score: Optional[int],
        anomaly_score: Optional[float],
        criticality_score: float
    ) -> List[str]:
        """Generate human-readable reasons for risk score."""
        reasons = []
        
        if failure_prob and failure_prob >= 0.8:
            reasons.append(f"Very high failure probability ({failure_prob*100:.0f}%)")
        elif failure_prob and failure_prob >= 0.6:
            reasons.append(f"High failure probability ({failure_prob*100:.0f}%)")
        
        if rul_days and rul_days <= 7:
            reasons.append(f"Very short RUL ({rul_days} days)")
        elif rul_days and rul_days <= 14:
            reasons.append(f"Short RUL ({rul_days} days)")
        
        if health_score and health_score <= 40:
            reasons.append(f"Poor health condition ({health_score})")
        
        if anomaly_score and anomaly_score < -0.5:
            reasons.append("Significant anomalies detected")
        
        if criticality_score >= 80:
            reasons.append("Critical production equipment")
        elif criticality_score >= 60:
            reasons.append("High production dependency")
        
        if not reasons:
            reasons.append("General monitoring recommended")
        
        return reasons
    
    def get_risk(self, equipment_id: str) -> Optional[RiskScore]:
        """Get risk score for equipment."""
        return self.risk_scores.get(equipment_id)
    
    def get_all_risks(self) -> List[RiskScore]:
        """Get all risk scores."""
        return list(self.risk_scores.values())
    
    def get_critical_risks(self) -> List[RiskScore]:
        """Get all critical risk equipment."""
        return [r for r in self.risk_scores.values() if r.risk_level == 'critical']
    
    def get_high_risks(self) -> List[RiskScore]:
        """Get all high risk equipment."""
        return [r for r in self.risk_scores.values() if r.risk_level == 'high']
    
    def get_risk_summary(self) -> Dict[str, Any]:
        """Get plant-wide risk summary."""
        risks = list(self.risk_scores.values())
        
        if not risks:
            return {
                'total_equipment': 0,
                'critical_count': 0,
                'high_count': 0,
                'medium_count': 0,
                'low_count': 0,
                'average_risk': 0,
                'total_downtime_cost_at_risk': 0
            }
        
        criticality = self.criticality.get_criticality_summary()
        
        return {
            'total_equipment': len(risks),
            'critical_count': sum(1 for r in risks if r.risk_level == 'critical'),
            'high_count': sum(1 for r in risks if r.risk_level == 'high'),
            'medium_count': sum(1 for r in risks if r.risk_level == 'medium'),
            'low_count': sum(1 for r in risks if r.risk_level == 'low'),
            'average_risk': sum(r.risk_score for r in risks) / len(risks),
            'plant_health_score': 100 - (sum(r.risk_score for r in risks) / len(risks)),
            'critical_equipment_cost': criticality.get('total_downtime_cost_per_hour', 0)
        }
    
    def calculate_all_from_defaults(self) -> List[RiskScore]:
        """Calculate risk scores for all default equipment."""
        # Simulated data for demo
        equipment_data = [
            {'id': 'blast_furnace_fan', 'name': 'Blast Furnace Fan', 'type': 'compressor',
             'failure_prob': 0.92, 'rul': 7, 'health': 35, 'anomaly': -0.8},
            {'id': 'rolling_mill_motor', 'name': 'Rolling Mill Motor', 'type': 'motor',
             'failure_prob': 0.88, 'rul': 10, 'health': 42, 'anomaly': -0.6},
            {'id': 'main_compressor', 'name': 'Main Compressor', 'type': 'compressor',
             'failure_prob': 0.85, 'rul': 12, 'health': 48, 'anomaly': -0.5},
            {'id': 'cooling_pump_a', 'name': 'Cooling Pump A', 'type': 'pump',
             'failure_prob': 0.65, 'rul': 20, 'health': 60, 'anomaly': -0.3},
            {'id': 'conveyor_belt_system', 'name': 'Conveyor Belt System', 'type': 'conveyor',
             'failure_prob': 0.55, 'rul': 35, 'health': 70, 'anomaly': -0.2},
            {'id': 'slab_reheating_furnace', 'name': 'Slab Reheating Furnace', 'type': 'furnace',
             'failure_prob': 0.78, 'rul': 15, 'health': 52, 'anomaly': -0.4},
            {'id': 'hot_rolling_mill', 'name': 'Hot Rolling Mill', 'type': 'mill',
             'failure_prob': 0.82, 'rul': 14, 'health': 50, 'anomaly': -0.45},
            {'id': 'cold_rolling_mill', 'name': 'Cold Rolling Mill', 'type': 'mill',
             'failure_prob': 0.72, 'rul': 18, 'health': 58, 'anomaly': -0.35},
            {'id': 'crane_motor_1', 'name': 'Crane Motor 1', 'type': 'crane',
             'failure_prob': 0.45, 'rul': 45, 'health': 75, 'anomaly': -0.1},
            {'id': 'cooling_pump_b', 'name': 'Cooling Pump B', 'type': 'pump',
             'failure_prob': 0.35, 'rul': 60, 'health': 82, 'anomaly': 0.0},
            {'id': 'lubrication_system', 'name': 'Central Lubrication System', 'type': 'system',
             'failure_prob': 0.30, 'rul': 75, 'health': 85, 'anomaly': 0.1},
            {'id': 'hydraulic_power_unit', 'name': 'Hydraulic Power Unit', 'type': 'hydraulic',
             'failure_prob': 0.50, 'rul': 40, 'health': 68, 'anomaly': -0.25}
        ]
        
        results = []
        for eq in equipment_data:
            risk = self.calculate_risk(
                equipment_id=eq['id'],
                equipment_name=eq['name'],
                equipment_type=eq['type'],
                failure_probability=eq['failure_prob'],
                rul_days=eq['rul'],
                health_score=eq['health'],
                anomaly_score=eq['anomaly']
            )
            results.append(risk)
        
        return results


# Singleton instance
_plant_risk_engine: Optional[PlantRiskEngine] = None


def get_plant_risk_engine() -> PlantRiskEngine:
    """Get global plant risk engine instance."""
    global _plant_risk_engine
    if _plant_risk_engine is None:
        _plant_risk_engine = PlantRiskEngine()
    return _plant_risk_engine