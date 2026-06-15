"""
Bottleneck Detection Engine.

This module identifies plant bottlenecks and single points of failure
that could halt production if they fail.
"""
import uuid
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime

from app.decision_support.risk_engine import get_plant_risk_engine, RiskScore
from app.decision_support.criticality_engine import get_criticality_engine


@dataclass
class Bottleneck:
    """Equipment identified as a bottleneck."""
    bottleneck_id: str
    equipment_id: str
    equipment_name: str
    bottleneck_type: str  # single_point_failure, series_critical, capacity_limiter
    severity: str  # critical, high, medium, low
    reason: str
    impact: str
    affected_systems: List[str]
    risk_score: float
    mitigation_options: List[str]
    created_at: datetime = field(default_factory=datetime.now)


class BottleneckEngine:
    """
    Detect plant bottlenecks and single points of failure.
    
    Identifies:
    - Single points of failure
    - Series-critical equipment
    - Capacity limiters
    - Equipment with no backup
    """
    
    # Default bottleneck definitions for steel plant
    DEFAULT_BOTTLENECKS = [
        {
            'equipment_id': 'blast_furnace_fan',
            'equipment_name': 'Blast Furnace Fan',
            'bottleneck_type': 'single_point_failure',
            'severity': 'critical',
            'reason': 'Only blast furnace fan in service - failure stops entire furnace',
            'impact': 'Entire steel production line halt',
            'affected_systems': ['Blast Furnace', 'Steel Making', 'Casting'],
            'mitigation': [
                'Maintain preventive maintenance schedule',
                'Keep critical spares in inventory',
                'Consider backup fan installation',
                'Implement real-time monitoring'
            ]
        },
        {
            'equipment_id': 'main_compressor',
            'equipment_name': 'Main Compressor',
            'bottleneck_type': 'single_point_failure',
            'severity': 'critical',
            'reason': 'Single compressor serving entire plant air requirements',
            'impact': 'All pneumatic systems and tools stop',
            'affected_systems': ['All Production Lines', 'Instrumentation', 'Control Systems'],
            'mitigation': [
                'Regular compressor maintenance',
                'Backup compressor on standby',
                'Air storage tanks for buffer',
                'Leak detection program'
            ]
        },
        {
            'equipment_id': 'rolling_mill_motor',
            'equipment_name': 'Rolling Mill Motor',
            'bottleneck_type': 'series_critical',
            'severity': 'critical',
            'reason': 'Primary rolling motor - no immediate backup',
            'impact': 'Hot rolling line production halt',
            'affected_systems': ['Hot Rolling Line', 'Slab Processing'],
            'mitigation': [
                'Motor winding temperature monitoring',
                'Vibration analysis program',
                'Spare motor on standby',
                'Reduced load operation procedure'
            ]
        },
        {
            'equipment_id': 'slab_reheating_furnace',
            'equipment_name': 'Slab Reheating Furnace',
            'bottleneck_type': 'capacity_limiter',
            'severity': 'high',
            'reason': 'Furnace capacity limits overall production throughput',
            'impact': 'Reduced production rate across all products',
            'affected_systems': ['Hot Rolling Line', 'Production Planning'],
            'mitigation': [
                'Optimal furnace loading strategies',
                'Preheat efficiency improvement',
                'Regular burner maintenance',
                'Energy consumption monitoring'
            ]
        },
        {
            'equipment_id': 'cooling_pump_a',
            'equipment_name': 'Cooling Pump A',
            'bottleneck_type': 'single_point_failure',
            'severity': 'high',
            'reason': 'Primary cooling pump - cooling system failure affects many units',
            'impact': 'Multiple equipment overheating risk',
            'affected_systems': ['Rolling Mills', 'Furnaces', 'Compressors'],
            'mitigation': [
                'Cooling Pump B as backup',
                'Temperature monitoring',
                'Emergency cooling procedures',
                'Regular pump maintenance'
            ]
        },
        {
            'equipment_id': 'conveyor_belt_system',
            'equipment_name': 'Conveyor Belt System',
            'bottleneck_type': 'series_critical',
            'severity': 'high',
            'reason': 'Main material transport system - belt failure stops material flow',
            'impact': 'Production line feeding disruption',
            'affected_systems': ['Slab Storage', 'Rolling Line', 'Product Storage'],
            'mitigation': [
                'Belt inspection program',
                'Spare belt sections',
                'Conveyor belt monitoring',
                'Material diversion procedures'
            ]
        }
    ]
    
    def __init__(self):
        self.risk_engine = get_plant_risk_engine()
        self.criticality = get_criticality_engine()
        self.bottlenecks: List[Bottleneck] = []
        self._load_default_bottlenecks()
    
    def _load_default_bottlenecks(self):
        """Load default bottleneck definitions."""
        for data in self.DEFAULT_BOTTLENECKS:
            risk = self.risk_engine.get_risk(data['equipment_id'])
            risk_score = risk.risk_score if risk else 50
            
            bottleneck = Bottleneck(
                bottleneck_id=str(uuid.uuid4()),
                equipment_id=data['equipment_id'],
                equipment_name=data['equipment_name'],
                bottleneck_type=data['bottleneck_type'],
                severity=data['severity'],
                reason=data['reason'],
                impact=data['impact'],
                affected_systems=data['affected_systems'],
                risk_score=risk_score,
                mitigation_options=data['mitigation']
            )
            
            self.bottlenecks.append(bottleneck)
    
    def get_all_bottlenecks(self) -> List[Bottleneck]:
        """Get all identified bottlenecks."""
        # Update risk scores
        for bottleneck in self.bottlenecks:
            risk = self.risk_engine.get_risk(bottleneck.equipment_id)
            if risk:
                bottleneck.risk_score = risk.risk_score
        
        return self.bottlenecks
    
    def get_critical_bottlenecks(self) -> List[Bottleneck]:
        """Get critical severity bottlenecks."""
        return [b for b in self.bottlenecks if b.severity == 'critical']
    
    def get_high_bottlenecks(self) -> List[Bottleneck]:
        """Get high severity bottlenecks."""
        return [b for b in self.bottlenecks if b.severity == 'high']
    
    def get_bottleneck_by_equipment(self, equipment_id: str) -> Optional[Bottleneck]:
        """Get bottleneck for specific equipment."""
        for b in self.bottlenecks:
            if b.equipment_id == equipment_id:
                return b
        return None
    
    def add_bottleneck(
        self,
        equipment_id: str,
        equipment_name: str,
        bottleneck_type: str,
        severity: str,
        reason: str,
        impact: str,
        affected_systems: List[str],
        mitigation_options: List[str]
    ) -> Bottleneck:
        """Add a new bottleneck."""
        risk = self.risk_engine.get_risk(equipment_id)
        risk_score = risk.risk_score if risk else 50
        
        bottleneck = Bottleneck(
            bottleneck_id=str(uuid.uuid4()),
            equipment_id=equipment_id,
            equipment_name=equipment_name,
            bottleneck_type=bottleneck_type,
            severity=severity,
            reason=reason,
            impact=impact,
            affected_systems=affected_systems,
            risk_score=risk_score,
            mitigation_options=mitigation_options
        )
        
        self.bottlenecks.append(bottleneck)
        return bottleneck
    
    def get_bottleneck_summary(self) -> Dict[str, Any]:
        """Get summary of bottlenecks."""
        return {
            'total_bottlenecks': len(self.bottlenecks),
            'critical_count': sum(1 for b in self.bottlenecks if b.severity == 'critical'),
            'high_count': sum(1 for b in self.bottlenecks if b.severity == 'high'),
            'medium_count': sum(1 for b in self.bottlenecks if b.severity == 'medium'),
            'low_count': sum(1 for b in self.bottlenecks if b.severity == 'low'),
            'single_point_failure_count': sum(1 for b in self.bottlenecks if b.bottleneck_type == 'single_point_failure'),
            'series_critical_count': sum(1 for b in self.bottlenecks if b.bottleneck_type == 'series_critical'),
            'capacity_limiter_count': sum(1 for b in self.bottlenecks if b.bottleneck_type == 'capacity_limiter')
        }


# Singleton instance
_bottleneck_engine: Optional[BottleneckEngine] = None


def get_bottleneck_engine() -> BottleneckEngine:
    """Get global bottleneck engine instance."""
    global _bottleneck_engine
    if _bottleneck_engine is None:
        _bottleneck_engine = BottleneckEngine()
    return _bottleneck_engine