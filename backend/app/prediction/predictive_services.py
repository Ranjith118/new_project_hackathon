"""
Predictive Maintenance Services.

This module provides:
- Degradation Engine
- Early Warning Engine
- Risk Assessment Engine
- Maintenance Recommendation Trigger
"""
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass, asdict
import uuid

from app.prediction.failure_model import get_failure_predictor, FailurePredictor
from app.prediction.rul_model import get_rul_predictor, RULPredictor


@dataclass
class DegradationState:
    """Equipment degradation state."""
    level: str  # healthy, slightly_degraded, moderately_degraded, severely_degraded
    score: int  # 0-100
    factors: Dict[str, float]
    explanation: str


@dataclass
class EarlyWarning:
    """Early warning alert."""
    warning_id: str
    equipment_name: str
    level: str  # low, medium, high, critical
    reason: str
    failure_probability: Optional[float] = None
    rul_days: Optional[int] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass
class RiskAssessment:
    """Combined risk assessment."""
    overall_risk: str  # low, medium, high, critical
    risk_score: int  # 0-100
    health_score: int
    failure_probability: float
    rul_days: int
    explanation: str
    contributing_factors: List[str]
    confidence: float


@dataclass
class MaintenanceRecommendation:
    """Maintenance recommendation triggered by prediction."""
    recommendation_id: str
    equipment_name: str
    priority: str  # immediate, urgent, scheduled
    category: str  # replacement, inspection, lubrication, calibration
    action: str
    reason: str
    triggered_by: str  # failure_probability, rul, anomaly
    created_at: datetime


class DegradationEngine:
    """
    Calculate equipment degradation level.
    
    Categories:
    - Healthy (80-100): Normal operation
    - Slightly Degraded (60-79): Minor issues
    - Moderately Degraded (40-59): Maintenance needed
    - Severely Degraded (0-39): Immediate action required
    """
    
    THRESHOLDS = {
        'healthy': (80, 100),
        'slightly_degraded': (60, 79),
        'moderately_degraded': (40, 59),
        'severely_degraded': (0, 39)
    }
    
    def __init__(self):
        self.failure_predictor = get_failure_predictor()
        self.rul_predictor = get_rul_predictor()
    
    def calculate_degradation(
        self,
        health_score: int,
        failure_probability: Optional[float] = None,
        rul_days: Optional[int] = None
    ) -> DegradationState:
        """
        Calculate degradation state.
        
        Args:
            health_score: Current health score (0-100)
            failure_probability: Failure probability (0-1)
            rul_days: Remaining useful life in days
            
        Returns:
            DegradationState with degradation level and factors
        """
        factors = {}
        
        # Health score contribution
        factors['health_score'] = health_score
        
        # Failure probability contribution (invert: high failure = low degradation)
        if failure_probability is not None:
            factors['failure_probability'] = failure_probability * 100
        else:
            factors['failure_probability'] = 50
        
        # RUL contribution (invert: low RUL = low degradation)
        if rul_days is not None:
            rul_score = min(100, rul_days)  # Max at 100 days
            factors['rul_score'] = rul_score
        else:
            factors['rul_score'] = 80
        
        # Calculate weighted degradation score
        degradation_score = (
            health_score * 0.5 +
            (100 - factors['failure_probability']) * 0.3 +
            factors['rul_score'] * 0.2
        )
        
        # Determine degradation level
        level = self._get_degradation_level(degradation_score)
        
        # Generate explanation
        explanation = self._generate_explanation(level, factors)
        
        return DegradationState(
            level=level,
            score=int(degradation_score),
            factors=factors,
            explanation=explanation
        )
    
    def _get_degradation_level(self, score: int) -> str:
        """Get degradation level from score."""
        for level, (min_score, max_score) in self.THRESHOLDS.items():
            if min_score <= score <= max_score:
                return level
        return 'severely_degraded'
    
    def _generate_explanation(
        self,
        level: str,
        factors: Dict[str, float]
    ) -> str:
        """Generate explanation for degradation level."""
        if level == 'healthy':
            return "Equipment operating optimally. No degradation detected."
        
        explanations = []
        
        if factors['health_score'] < 80:
            explanations.append(f"Health score: {factors['health_score']}")
        
        if factors['failure_probability'] > 30:
            explanations.append(f"Failure probability: {factors['failure_probability']:.1f}%")
        
        if factors.get('rul_score', 100) < 50:
            explanations.append(f"Low remaining useful life: {factors['rul_score']:.0f} days")
        
        if level == 'slightly_degraded':
            return f"Slight degradation detected. {'. '.join(explanations)}"
        elif level == 'moderately_degraded':
            return f"Moderate degradation. {'. '.join(explanations)}. Schedule maintenance soon."
        else:
            return f"SEVERE degradation. {' '.join(explanations)}. Immediate action required."


class EarlyWarningEngine:
    """
    Generate early warning alerts based on predictions.
    
    Triggers warnings when:
    - Failure Probability > 70%
    - RUL < 30 days
    """
    
    def __init__(self):
        self.warnings: List[EarlyWarning] = []
    
    def check_and_generate_warnings(
        self,
        equipment_name: str,
        failure_probability: Optional[float] = None,
        rul_days: Optional[int] = None
    ) -> List[EarlyWarning]:
        """
        Check conditions and generate warnings.
        
        Args:
            equipment_name: Name of equipment
            failure_probability: Failure probability (0-1)
            rul_days: Remaining useful life in days
            
        Returns:
            List of generated warnings
        """
        warnings = []
        
        # Check failure probability
        if failure_probability is not None:
            if failure_probability >= 0.9:
                warnings.append(EarlyWarning(
                    warning_id=str(uuid.uuid4()),
                    equipment_name=equipment_name,
                    level='critical',
                    reason=f"Failure probability exceeds 90%",
                    failure_probability=failure_probability,
                    rul_days=rul_days
                ))
            elif failure_probability >= 0.8:
                warnings.append(EarlyWarning(
                    warning_id=str(uuid.uuid4()),
                    equipment_name=equipment_name,
                    level='critical',
                    reason=f"Failure probability exceeds 80%",
                    failure_probability=failure_probability,
                    rul_days=rul_days
                ))
            elif failure_probability >= 0.7:
                warnings.append(EarlyWarning(
                    warning_id=str(uuid.uuid4()),
                    equipment_name=equipment_name,
                    level='high',
                    reason=f"Failure probability exceeds 70%",
                    failure_probability=failure_probability,
                    rul_days=rul_days
                ))
            elif failure_probability >= 0.5:
                warnings.append(EarlyWarning(
                    warning_id=str(uuid.uuid4()),
                    equipment_name=equipment_name,
                    level='medium',
                    reason=f"Failure probability exceeds 50%",
                    failure_probability=failure_probability,
                    rul_days=rul_days
                ))
        
        # Check RUL
        if rul_days is not None:
            if rul_days <= 7:
                warnings.append(EarlyWarning(
                    warning_id=str(uuid.uuid4()),
                    equipment_name=equipment_name,
                    level='critical',
                    reason=f"RUL less than 7 days - imminent failure",
                    failure_probability=failure_probability,
                    rul_days=rul_days
                ))
            elif rul_days <= 15:
                warnings.append(EarlyWarning(
                    warning_id=str(uuid.uuid4()),
                    equipment_name=equipment_name,
                    level='critical',
                    reason=f"RUL less than 15 days - urgent action required",
                    failure_probability=failure_probability,
                    rul_days=rul_days
                ))
            elif rul_days <= 30:
                warnings.append(EarlyWarning(
                    warning_id=str(uuid.uuid4()),
                    equipment_name=equipment_name,
                    level='high',
                    reason=f"RUL less than 30 days - schedule maintenance",
                    failure_probability=failure_probability,
                    rul_days=rul_days
                ))
            elif rul_days <= 60:
                warnings.append(EarlyWarning(
                    warning_id=str(uuid.uuid4()),
                    equipment_name=equipment_name,
                    level='medium',
                    reason=f"RUL less than 60 days - plan maintenance",
                    failure_probability=failure_probability,
                    rul_days=rul_days
                ))
        
        # Store warnings
        for warning in warnings:
            self.warnings.append(warning)
        
        # Deduplicate
        return self._deduplicate_warnings(warnings)
    
    def _deduplicate_warnings(
        self,
        warnings: List[EarlyWarning]
    ) -> List[EarlyWarning]:
        """Remove duplicate warnings for same equipment."""
        seen = set()
        unique = []
        
        for warning in warnings:
            key = (warning.equipment_name, warning.level, warning.reason[:50])
            if key not in seen:
                seen.add(key)
                unique.append(warning)
        
        return unique
    
    def get_active_warnings(
        self,
        equipment_name: Optional[str] = None,
        level: Optional[str] = None
    ) -> List[EarlyWarning]:
        """Get active warnings."""
        warnings = self.warnings
        
        if equipment_name:
            warnings = [w for w in warnings if w.equipment_name == equipment_name]
        
        if level:
            warnings = [w for w in warnings if w.level == level]
        
        # Sort by level and timestamp
        level_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
        warnings.sort(key=lambda w: (level_order.get(w.level, 4), -w.timestamp.timestamp()))
        
        return warnings
    
    def clear_warnings(self, equipment_name: Optional[str] = None):
        """Clear warnings."""
        if equipment_name:
            self.warnings = [
                w for w in self.warnings 
                if w.equipment_name != equipment_name
            ]
        else:
            self.warnings = []


class RiskAssessmentEngine:
    """
    Combine multiple signals into unified risk assessment.
    """
    
    def __init__(self):
        self.failure_predictor = get_failure_predictor()
        self.rul_predictor = get_rul_predictor()
    
    def assess_risk(
        self,
        equipment_name: str,
        health_score: int,
        failure_probability: Optional[float] = None,
        rul_days: Optional[int] = None,
        anomaly_score: Optional[float] = None
    ) -> RiskAssessment:
        """
        Generate comprehensive risk assessment.
        
        Args:
            equipment_name: Name of equipment
            health_score: Current health score
            failure_probability: Failure probability
            rul_days: Remaining useful life
            anomaly_score: Anomaly score from Isolation Forest
            
        Returns:
            RiskAssessment with overall risk evaluation
        """
        # Calculate risk score components
        health_risk = (100 - health_score) * 0.25
        failure_risk = (failure_probability or 0) * 100 * 0.30
        rul_risk = max(0, (60 - (rul_days or 60))) / 60 * 100 * 0.25 if rul_days else 0
        anomaly_risk = abs(min(anomaly_score or 0, 0)) * 100 * 0.20
        
        # Calculate overall risk score
        total_risk = health_risk + failure_risk + rul_risk + anomaly_risk
        risk_score = min(100, max(0, int(total_risk)))
        
        # Determine risk level
        if risk_score >= 80:
            overall_risk = 'critical'
        elif risk_score >= 60:
            overall_risk = 'high'
        elif risk_score >= 40:
            overall_risk = 'medium'
        else:
            overall_risk = 'low'
        
        # Identify contributing factors
        factors = []
        if health_score < 60:
            factors.append(f"Low health score ({health_score})")
        if (failure_probability or 0) > 0.5:
            factors.append(f"High failure probability ({(failure_probability or 0) * 100:.0f}%)")
        if (rul_days or 100) < 30:
            factors.append(f"Low RUL ({rul_days or 0} days)")
        if (anomaly_score or 0) < -0.3:
            factors.append("Anomaly detected in sensor patterns")
        
        # Generate explanation
        explanation = self._generate_explanation(overall_risk, risk_score, factors)
        
        # Calculate confidence
        confidence = 0.7
        if failure_probability is not None:
            confidence += 0.1
        if rul_days is not None:
            confidence += 0.1
        if anomaly_score is not None:
            confidence += 0.1
        confidence = min(1.0, confidence)
        
        return RiskAssessment(
            overall_risk=overall_risk,
            risk_score=risk_score,
            health_score=health_score,
            failure_probability=failure_probability or 0,
            rul_days=rul_days or 0,
            explanation=explanation,
            contributing_factors=factors,
            confidence=confidence
        )
    
    def _generate_explanation(
        self,
        risk_level: str,
        score: int,
        factors: List[str]
    ) -> str:
        """Generate explanation for risk level."""
        if risk_level == 'critical':
            return f"CRITICAL RISK ({score}/100). {' '.join(factors)}. Immediate action required."
        elif risk_level == 'high':
            return f"HIGH RISK ({score}/100). {' '.join(factors)}. Schedule maintenance soon."
        elif risk_level == 'medium':
            return f"MEDIUM RISK ({score}/100). {' '.join(factors) if factors else 'Minor concerns identified'}. Monitor closely."
        else:
            return f"LOW RISK ({score}/100). Equipment operating within acceptable parameters."


class MaintenanceRecommendationEngine:
    """
    Generate maintenance recommendations based on predictions.
    
    Triggers when:
    - Failure Probability > 80%
    - RUL < 15 days
    - Anomaly detected
    """
    
    def __init__(self):
        self.recommendations: List[MaintenanceRecommendation] = []
    
    def check_and_generate(
        self,
        equipment_name: str,
        failure_probability: Optional[float] = None,
        rul_days: Optional[int] = None,
        anomaly_detected: bool = False,
        sensor_readings: Optional[Dict[str, float]] = None
    ) -> List[MaintenanceRecommendation]:
        """
        Check conditions and generate recommendations.
        
        Args:
            equipment_name: Name of equipment
            failure_probability: Failure probability
            rul_days: Remaining useful life
            anomaly_detected: Whether anomaly was detected
            sensor_readings: Current sensor readings
            
        Returns:
            List of maintenance recommendations
        """
        recommendations = []
        
        # Critical failure probability
        if failure_probability is not None and failure_probability > 0.8:
            recommendations.append(MaintenanceRecommendation(
                recommendation_id=str(uuid.uuid4()),
                equipment_name=equipment_name,
                priority='immediate',
                category='replacement',
                action='Schedule immediate equipment inspection and potential replacement',
                reason=f"High failure probability: {failure_probability * 100:.0f}%",
                triggered_by='failure_probability',
                created_at=datetime.now()
            ))
        
        # Very low RUL
        if rul_days is not None and rul_days < 15:
            recommendations.append(MaintenanceRecommendation(
                recommendation_id=str(uuid.uuid4()),
                equipment_name=equipment_name,
                priority='immediate',
                category='replacement',
                action='Prepare for equipment replacement within 2 weeks',
                reason=f"Remaining useful life: {rul_days} days",
                triggered_by='rul',
                created_at=datetime.now()
            ))
        
        # Low RUL
        if rul_days is not None and rul_days < 30:
            recommendations.append(MaintenanceRecommendation(
                recommendation_id=str(uuid.uuid4()),
                equipment_name=equipment_name,
                priority='urgent',
                category='inspection',
                action='Schedule comprehensive equipment inspection',
                reason=f"RUL declining: {rul_days} days remaining",
                triggered_by='rul',
                created_at=datetime.now()
            ))
        
        # Anomaly detected
        if anomaly_detected and sensor_readings:
            issues = self._identify_issues(sensor_readings)
            if issues:
                recommendations.append(MaintenanceRecommendation(
                    recommendation_id=str(uuid.uuid4()),
                    equipment_name=equipment_name,
                    priority='urgent',
                    category='inspection',
                    action=f"Inspect equipment for: {', '.join(issues)}",
                    reason="Anomaly detected in sensor patterns",
                    triggered_by='anomaly',
                    created_at=datetime.now()
                ))
        
        # Store recommendations
        for rec in recommendations:
            self.recommendations.append(rec)
        
        return recommendations
    
    def _identify_issues(
        self,
        readings: Dict[str, float]
    ) -> List[str]:
        """Identify specific issues from sensor readings."""
        issues = []
        
        if readings.get('temperature', 0) > 95:
            issues.append('overheating')
        if readings.get('vibration', 0) > 3.0:
            issues.append('excessive vibration')
        if readings.get('current', 0) > 28:
            issues.append('electrical issues')
        if readings.get('pressure', 0) > 90:
            issues.append('pressure abnormality')
        if readings.get('rpm', 0) > 2200:
            issues.append('speed irregularities')
        
        return issues
    
    def get_recommendations(
        self,
        equipment_name: Optional[str] = None,
        priority: Optional[str] = None
    ) -> List[MaintenanceRecommendation]:
        """Get maintenance recommendations."""
        recs = self.recommendations
        
        if equipment_name:
            recs = [r for r in recs if r.equipment_name == equipment_name]
        
        if priority:
            recs = [r for r in recs if r.priority == priority]
        
        return recs


# Singleton instances
_degradation_engine: Optional[DegradationEngine] = None
_warning_engine: Optional[EarlyWarningEngine] = None
_risk_engine: Optional[RiskAssessmentEngine] = None
_recommendation_engine: Optional[MaintenanceRecommendationEngine] = None


def get_degradation_engine() -> DegradationEngine:
    """Get global degradation engine instance."""
    global _degradation_engine
    if _degradation_engine is None:
        _degradation_engine = DegradationEngine()
    return _degradation_engine


def get_warning_engine() -> EarlyWarningEngine:
    """Get global warning engine instance."""
    global _warning_engine
    if _warning_engine is None:
        _warning_engine = EarlyWarningEngine()
    return _warning_engine


def get_risk_engine() -> RiskAssessmentEngine:
    """Get global risk assessment engine instance."""
    global _risk_engine
    if _risk_engine is None:
        _risk_engine = RiskAssessmentEngine()
    return _risk_engine


def get_recommendation_engine() -> MaintenanceRecommendationEngine:
    """Get global recommendation engine instance."""
    global _recommendation_engine
    if _recommendation_engine is None:
        _recommendation_engine = MaintenanceRecommendationEngine()
    return _recommendation_engine