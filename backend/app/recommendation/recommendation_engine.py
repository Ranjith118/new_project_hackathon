"""
Intelligent Maintenance Recommendation Engine.

This module generates actionable maintenance recommendations based on:
- Root Cause Analysis results
- Failure predictions
- RUL predictions
- Health scores
- Anomaly detection
- Equipment criticality
"""
import uuid
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from app.rca.pattern_engine import get_pattern_engine


@dataclass
class Recommendation:
    """Single maintenance recommendation."""
    recommendation_id: str
    equipment_name: str
    priority: str  # P1, P2, P3, P4
    category: str  # immediate, repair, monitoring, preventive, safety
    action: str
    reason: str
    evidence: List[str]
    references: List[str]
    estimated_downtime_hours: float
    estimated_cost: Optional[float] = None
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class MaintenanceRecommendationSet:
    """Complete set of recommendations for equipment."""
    recommendation_id: str
    equipment_name: str
    timestamp: datetime
    priority: str
    immediate_actions: List[Recommendation]
    repair_actions: List[Recommendation]
    monitoring_actions: List[Recommendation]
    preventive_actions: List[Recommendation]
    safety_actions: List[Recommendation]
    overall_reason: str
    confidence: float
    estimated_total_downtime: float


class RecommendationEngine:
    """
    Generate intelligent maintenance recommendations.
    
    Combines inputs from:
    - Root Cause Analysis
    - Failure Prediction
    - RUL Prediction
    - Health Monitoring
    - Anomaly Detection
    """
    
    # Priority thresholds
    PRIORITY_THRESHOLDS = {
        'P1': {'failure_prob': 0.85, 'rul': 15, 'risk_score': 80},
        'P2': {'failure_prob': 0.70, 'rul': 30, 'risk_score': 60},
        'P3': {'failure_prob': 0.50, 'rul': 60, 'risk_score': 40},
        'P4': {'failure_prob': 0.30, 'rul': 90, 'risk_score': 20}
    }
    
    # Recommendation templates by root cause
    RECOMMENDATION_TEMPLATES = {
        'bearing wear': {
            'immediate': [
                "Reduce equipment load immediately",
                "Monitor bearing temperature every 30 minutes",
                "Inspect bearing housing for visible damage"
            ],
            'repair': [
                "Schedule bearing replacement within 7 days",
                "Replace bearing with OEM part B6205",
                "Check and replace bearing seals",
                "Verify shaft alignment after replacement"
            ],
            'monitoring': [
                "Track vibration amplitude daily",
                "Monitor bearing temperature trend",
                "Check lubrication quality weekly"
            ],
            'safety': [
                "Allow equipment to cool before inspection",
                "Use thermal imaging camera for inspection",
                "Follow lockout-tagout procedures"
            ]
        },
        'bearing failure': {
            'immediate': [
                "Shut down equipment immediately",
                "Isolate power supply",
                "Implement lockout-tagout"
            ],
            'repair': [
                "Replace bearing immediately",
                "Inspect shaft for damage",
                "Check housing for wear",
                "Replace mounting hardware"
            ],
            'monitoring': [
                "Monitor new bearing temperature for 24 hours",
                "Track vibration baseline after replacement",
                "Schedule follow-up inspection in 1 week"
            ],
            'safety': [
                "Wear cut-resistant gloves",
                "Use bearing puller tool",
                "Follow crane operations for heavy components"
            ]
        },
        'pump blockage': {
            'immediate': [
                "Stop pump operation",
                "Close inlet and outlet valves",
                "Release pressure"
            ],
            'repair': [
                "Clear debris from pump inlet",
                "Replace or clean strainer",
                "Inspect impeller for damage",
                "Check for corrosion"
            ],
            'monitoring': [
                "Monitor flow rate",
                "Track pressure differential",
                "Inspect strainer daily"
            ],
            'safety': [
                "Wear chemical-resistant gloves",
                "Ensure proper ventilation",
                "Check for hazardous atmosphere"
            ]
        },
        'motor overheating': {
            'immediate': [
                "Reduce motor load by 50%",
                "Increase ventilation",
                "Monitor winding temperature"
            ],
            'repair': [
                "Clean motor windings",
                "Check and replace cooling fans",
                "Inspect ventilation passages",
                "Test insulation resistance"
            ],
            'monitoring': [
                "Track motor temperature trend",
                "Monitor current draw",
                "Check ambient temperature"
            ],
            'safety': [
                "Allow motor to cool before inspection",
                "Use infrared thermometer",
                "Test for voltage before working"
            ]
        },
        'cooling system failure': {
            'immediate': [
                "Reduce equipment load",
                "Activate backup cooling if available",
                "Monitor temperature continuously"
            ],
            'repair': [
                "Replace cooling fan motor",
                "Clean heat exchanger",
                "Check coolant level and quality",
                "Inspect coolant pump"
            ],
            'monitoring': [
                "Track temperature hourly",
                "Monitor coolant flow rate",
                "Check coolant condition weekly"
            ],
            'safety': [
                "Allow system to cool before maintenance",
                "Wear heat-resistant gloves",
                "Check for coolant leaks"
            ]
        },
        'electrical fault': {
            'immediate': [
                "Isolate electrical supply",
                "Test for live voltage",
                "Document fault symptoms"
            ],
            'repair': [
                "Replace damaged wiring",
                "Repair motor windings",
                "Replace contactors",
                "Test insulation"
            ],
            'monitoring': [
                "Monitor current waveform",
                "Track power factor",
                "Check for voltage fluctuations"
            ],
            'safety': [
                "Always de-energize before working",
                "Use proper PPE for electrical work",
                "Follow arc flash safety procedures",
                "Use voltage tester"
            ]
        },
        'shaft misalignment': {
            'immediate': [
                "Reduce speed to 50%",
                "Monitor vibration levels",
                "Inspect coupling condition"
            ],
            'repair': [
                "Realign shaft using laser alignment",
                "Replace coupling if damaged",
                "Check foundation bolts",
                "Adjust mounting plates"
            ],
            'monitoring': [
                "Track vibration spectrum daily",
                "Monitor coupling temperature",
                "Check alignment monthly"
            ],
            'safety': [
                "Lock out before alignment work",
                "Use appropriate lifting equipment",
                "Follow precision alignment procedures"
            ]
        },
        'lubrication failure': {
            'immediate': [
                "Stop equipment immediately",
                "Inspect lubrication system",
                "Check for oil leaks"
            ],
            'repair': [
                "Drain contaminated lubricant",
                "Flush lubrication system",
                "Replace filters",
                "Fill with correct lubricant grade"
            ],
            'monitoring': [
                "Check oil level daily",
                "Monitor oil temperature",
                "Perform oil analysis monthly"
            ],
            'safety': [
                "Wear chemical-resistant gloves",
                "Avoid contact with hot oil",
                "Dispose of contaminated oil properly"
            ]
        }
    }
    
    def __init__(self):
        self.pattern_engine = get_pattern_engine()
    
    def generate_recommendations(
        self,
        equipment_name: str,
        root_cause: Optional[str] = None,
        failure_probability: Optional[float] = None,
        rul_days: Optional[int] = None,
        health_score: Optional[int] = None,
        risk_level: Optional[str] = None,
        anomaly_detected: bool = False,
        sensor_readings: Optional[Dict[str, float]] = None
    ) -> MaintenanceRecommendationSet:
        """
        Generate comprehensive maintenance recommendations.
        
        Args:
            equipment_name: Name of equipment
            root_cause: Identified root cause from RCA
            failure_probability: Failure prediction probability (0-1)
            rul_days: Remaining useful life in days
            health_score: Health score (0-100)
            risk_level: Risk level (low, medium, high, critical)
            anomaly_detected: Whether anomaly was detected
            sensor_readings: Current sensor readings
            
        Returns:
            MaintenanceRecommendationSet with all recommendations
        """
        recommendation_id = str(uuid.uuid4())
        timestamp = datetime.now()
        
        # Determine priority
        priority = self._determine_priority(
            failure_probability, rul_days, health_score, risk_level
        )
        
        # Get template recommendations
        templates = self._get_templates(root_cause, anomaly_detected)
        
        # Generate recommendations by category
        immediate = self._generate_immediate_actions(
            equipment_name, priority, root_cause, sensor_readings, templates.get('immediate', [])
        )
        
        repair = self._generate_repair_actions(
            equipment_name, priority, root_cause, templates.get('repair', [])
        )
        
        monitoring = self._generate_monitoring_actions(
            equipment_name, priority, root_cause, sensor_readings, templates.get('monitoring', [])
        )
        
        preventive = self._generate_preventive_actions(
            equipment_name, root_cause, templates.get('monitoring', [])
        )
        
        safety = self._generate_safety_actions(
            equipment_name, priority, templates.get('safety', [])
        )
        
        # Calculate overall reason
        overall_reason = self._generate_overall_reason(
            root_cause, failure_probability, rul_days, health_score
        )
        
        # Calculate confidence
        confidence = self._calculate_confidence(
            failure_probability, rul_days, root_cause
        )
        
        # Calculate total downtime
        total_downtime = sum(a.estimated_downtime_hours for a in repair)
        
        return MaintenanceRecommendationSet(
            recommendation_id=recommendation_id,
            equipment_name=equipment_name,
            timestamp=timestamp,
            priority=priority,
            immediate_actions=immediate,
            repair_actions=repair,
            monitoring_actions=monitoring,
            preventive_actions=preventive,
            safety_actions=safety,
            overall_reason=overall_reason,
            confidence=confidence,
            estimated_total_downtime=total_downtime
        )
    
    def _determine_priority(
        self,
        failure_probability: Optional[float],
        rul_days: Optional[int],
        health_score: Optional[int],
        risk_level: Optional[str]
    ) -> str:
        """Determine recommendation priority."""
        # Check risk level first
        if risk_level:
            risk_priority_map = {
                'critical': 'P1',
                'high': 'P2',
                'medium': 'P3',
                'low': 'P4'
            }
            if risk_level in risk_priority_map:
                return risk_priority_map[risk_level]
        
        # Check failure probability
        if failure_probability is not None:
            if failure_probability >= 0.85:
                return 'P1'
            elif failure_probability >= 0.70:
                return 'P2'
            elif failure_probability >= 0.50:
                return 'P3'
        
        # Check RUL
        if rul_days is not None:
            if rul_days <= 15:
                return 'P1'
            elif rul_days <= 30:
                return 'P2'
            elif rul_days <= 60:
                return 'P3'
        
        # Check health score
        if health_score is not None:
            if health_score <= 40:
                return 'P1'
            elif health_score <= 60:
                return 'P2'
            elif health_score <= 80:
                return 'P3'
        
        return 'P4'
    
    def _get_templates(
        self,
        root_cause: Optional[str],
        anomaly_detected: bool
    ) -> Dict[str, List[str]]:
        """Get recommendation templates based on root cause."""
        if not root_cause:
            return self._get_generic_templates()
        
        root_cause_lower = root_cause.lower()
        
        for cause_key, templates in self.RECOMMENDATION_TEMPLATES.items():
            if cause_key in root_cause_lower:
                return templates
        
        return self._get_generic_templates()
    
    def _get_generic_templates(self) -> Dict[str, List[str]]:
        """Get generic recommendation templates."""
        return {
            'immediate': [
                "Inspect equipment for visible damage",
                "Check for abnormal sounds or vibrations",
                "Monitor critical parameters"
            ],
            'repair': [
                "Schedule comprehensive equipment inspection",
                "Replace worn components",
                "Clean and lubricate moving parts"
            ],
            'monitoring': [
                "Track equipment performance daily",
                "Record all anomalies",
                "Compare with historical data"
            ],
            'safety': [
                "Follow standard safety procedures",
                "Wear appropriate PPE",
                "Implement lockout-tagout"
            ]
        }
    
    def _generate_immediate_actions(
        self,
        equipment_name: str,
        priority: str,
        root_cause: Optional[str],
        sensor_readings: Optional[Dict[str, float]],
        template_actions: List[str]
    ) -> List[Recommendation]:
        """Generate immediate action recommendations."""
        actions = []
        
        # Add template actions
        for i, action in enumerate(template_actions[:3]):
            actions.append(Recommendation(
                recommendation_id=str(uuid.uuid4()),
                equipment_name=equipment_name,
                priority=priority,
                category='immediate',
                action=action,
                reason=f"Immediate action required for {root_cause or 'equipment issue'}",
                evidence=self._build_evidence(sensor_readings),
                references=["General Safety SOP", "Equipment Manual"],
                estimated_downtime_hours=0.5 if priority == 'P1' else 1.0
            ))
        
        # Add sensor-based actions if applicable
        if sensor_readings:
            if sensor_readings.get('temperature', 0) > 100:
                actions.append(Recommendation(
                    recommendation_id=str(uuid.uuid4()),
                    equipment_name=equipment_name,
                    priority='P1',
                    category='immediate',
                    action="CRITICAL: Temperature exceeds safe limit - reduce load immediately",
                    reason="Temperature above critical threshold",
                    evidence=[f"Temperature: {sensor_readings['temperature']}°C"],
                    references=["Temperature Safety Limit"],
                    estimated_downtime_hours=0
                ))
            
            if sensor_readings.get('vibration', 0) > 4.0:
                actions.append(Recommendation(
                    recommendation_id=str(uuid.uuid4()),
                    equipment_name=equipment_name,
                    priority='P1',
                    category='immediate',
                    action="CRITICAL: High vibration - inspect for mechanical failure",
                    reason="Vibration indicates imminent failure",
                    evidence=[f"Vibration: {sensor_readings['vibration']} mm/s"],
                    references=["Vibration Analysis Manual"],
                    estimated_downtime_hours=0.5
                ))
        
        return actions
    
    def _generate_repair_actions(
        self,
        equipment_name: str,
        priority: str,
        root_cause: Optional[str],
        template_actions: List[str]
    ) -> List[Recommendation]:
        """Generate repair action recommendations."""
        actions = []
        
        for action in template_actions[:5]:
            actions.append(Recommendation(
                recommendation_id=str(uuid.uuid4()),
                equipment_name=equipment_name,
                priority=priority,
                category='repair',
                action=action,
                reason=f"Repair required to address {root_cause or 'equipment degradation'}",
                evidence=["Equipment inspection required"],
                references=["Equipment Manual", "Repair SOP"],
                estimated_downtime_hours=2.0 if priority == 'P1' else 4.0
            ))
        
        return actions
    
    def _generate_monitoring_actions(
        self,
        equipment_name: str,
        priority: str,
        root_cause: Optional[str],
        sensor_readings: Optional[Dict[str, float]],
        template_actions: List[str]
    ) -> List[Recommendation]:
        """Generate monitoring action recommendations."""
        actions = []
        
        # Add template actions
        for action in template_actions[:4]:
            actions.append(Recommendation(
                recommendation_id=str(uuid.uuid4()),
                equipment_name=equipment_name,
                priority='P3' if priority in ['P1', 'P2'] else 'P4',
                category='monitoring',
                action=action,
                reason=f"Monitor to track {root_cause or 'equipment'} condition",
                evidence=self._build_evidence(sensor_readings),
                references=["Monitoring Protocol"],
                estimated_downtime_hours=0
            ))
        
        # Add sensor-specific monitoring
        if sensor_readings:
            if sensor_readings.get('temperature'):
                actions.append(Recommendation(
                    recommendation_id=str(uuid.uuid4()),
                    equipment_name=equipment_name,
                    priority='P3',
                    category='monitoring',
                    action=f"Track temperature every 2 hours (current: {sensor_readings['temperature']}°C)",
                    reason="Temperature monitoring for early warning",
                    evidence=[f"Current: {sensor_readings['temperature']}°C"],
                    references=["Temperature Monitoring SOP"],
                    estimated_downtime_hours=0
                ))
        
        return actions
    
    def _generate_preventive_actions(
        self,
        equipment_name: str,
        root_cause: Optional[str],
        template_actions: List[str]
    ) -> List[Recommendation]:
        """Generate preventive maintenance recommendations."""
        return [
            Recommendation(
                recommendation_id=str(uuid.uuid4()),
                equipment_name=equipment_name,
                priority='P4',
                category='preventive',
                action="Schedule weekly lubrication check",
                reason="Preventive maintenance for equipment longevity",
                evidence=["General maintenance schedule"],
                references=["Preventive Maintenance Schedule"],
                estimated_downtime_hours=1.0
            ),
            Recommendation(
                recommendation_id=str(uuid.uuid4()),
                equipment_name=equipment_name,
                priority='P3',
                category='preventive',
                action="Perform monthly vibration analysis",
                reason="Detect issues before failure",
                evidence=["Predictive maintenance protocol"],
                references=["Vibration Analysis Guide"],
                estimated_downtime_hours=2.0
            ),
            Recommendation(
                recommendation_id=str(uuid.uuid4()),
                equipment_name=equipment_name,
                priority='P3',
                category='preventive',
                action="Quarterly comprehensive inspection",
                reason="Ensure equipment reliability",
                evidence=["Maintenance schedule"],
                references=["Inspection Checklist"],
                estimated_downtime_hours=4.0
            )
        ]
    
    def _generate_safety_actions(
        self,
        equipment_name: str,
        priority: str,
        template_actions: List[str]
    ) -> List[Recommendation]:
        """Generate safety recommendations."""
        base_actions = [
            "Review and follow lockout-tagout procedures",
            "Wear appropriate PPE (gloves, safety glasses, hard hat)",
            "Ensure proper ventilation before entry",
            "Have fire extinguisher available"
        ]
        
        actions = []
        for action in base_actions + template_actions[:2]:
            actions.append(Recommendation(
                recommendation_id=str(uuid.uuid4()),
                equipment_name=equipment_name,
                priority='P1',
                category='safety',
                action=action,
                reason="Safety requirement for all maintenance activities",
                evidence=["Safety Regulations"],
                references=["Safety SOP", "OSHA Guidelines"],
                estimated_downtime_hours=0
            ))
        
        return actions
    
    def _build_evidence(self, sensor_readings: Optional[Dict[str, float]]) -> List[str]:
        """Build evidence list from sensor readings."""
        if not sensor_readings:
            return ["Equipment inspection required"]
        
        evidence = []
        for key, value in sensor_readings.items():
            if value is not None:
                unit = self._get_unit(key)
                evidence.append(f"{key}: {value}{unit}")
        
        return evidence if evidence else ["No sensor data available"]
    
    def _get_unit(self, sensor: str) -> str:
        """Get unit for sensor reading."""
        units = {
            'temperature': '°C',
            'vibration': ' mm/s',
            'current': 'A',
            'pressure': ' bar',
            'rpm': ' rpm'
        }
        return units.get(sensor, '')
    
    def _generate_overall_reason(
        self,
        root_cause: Optional[str],
        failure_probability: Optional[float],
        rul_days: Optional[int],
        health_score: Optional[int]
    ) -> str:
        """Generate overall reason for recommendations."""
        reasons = []
        
        if root_cause:
            reasons.append(f"Root cause: {root_cause}")
        
        if failure_probability is not None:
            reasons.append(f"Failure probability: {failure_probability * 100:.0f}%")
        
        if rul_days is not None:
            reasons.append(f"Remaining useful life: {rul_days} days")
        
        if health_score is not None:
            reasons.append(f"Health score: {health_score}")
        
        return ". ".join(reasons) if reasons else "General maintenance recommendation"
    
    def _calculate_confidence(
        self,
        failure_probability: Optional[float],
        rul_days: Optional[int],
        root_cause: Optional[str]
    ) -> float:
        """Calculate confidence score for recommendations."""
        confidence = 0.5
        
        if root_cause:
            confidence += 0.2
        
        if failure_probability is not None:
            confidence += 0.15
        
        if rul_days is not None:
            confidence += 0.15
        
        return min(1.0, confidence)


# Singleton instance
_recommendation_engine: Optional[RecommendationEngine] = None


def get_recommendation_engine() -> RecommendationEngine:
    """Get global recommendation engine instance."""
    global _recommendation_engine
    if _recommendation_engine is None:
        _recommendation_engine = RecommendationEngine()
    return _recommendation_engine