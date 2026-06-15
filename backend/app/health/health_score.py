"""Equipment Health Score and Risk Classification Engine."""
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime


@dataclass
class HealthScore:
    """Equipment health score result."""
    score: int  # 0-100
    status: str  # Healthy, Fair, Poor, Critical
    risk_level: str  # Low, Medium, High, Critical
    factors: Dict[str, float]  # Individual factor scores
    explanation: str  # Human-readable explanation
    recommendations: List[str]  # Recommended actions


@dataclass
class AnomalyExplanation:
    """Explainable AI results for anomaly detection."""
    is_anomaly: bool
    anomaly_score: float
    triggering_features: List[Dict[str, Any]]  # [{name, value, threshold, deviation}]
    risk_explanation: str
    confidence: float  # 0-1


class HealthScoreCalculator:
    """
    Calculate equipment health scores based on sensor readings.
    
    Health Score = 100 - penalties from:
    - Temperature deviation from optimal
    - Vibration deviation from optimal
    - Current deviation from optimal
    - Pressure deviation from optimal
    - RPM deviation from optimal
    - Anomaly score contribution
    """
    
    # Optimal values and acceptable ranges
    OPTIMAL_VALUES = {
        'temperature': {'optimal': 75, 'min': 20, 'max': 120, 'weight': 0.25},
        'vibration': {'optimal': 1.5, 'min': 0, 'max': 5, 'weight': 0.25},
        'current': {'optimal': 20, 'min': 5, 'max': 35, 'weight': 0.15},
        'pressure': {'optimal': 70, 'min': 40, 'max': 100, 'weight': 0.20},
        'rpm': {'optimal': 1500, 'min': 500, 'max': 2500, 'weight': 0.15}
    }
    
    # Risk thresholds
    RISK_THRESHOLDS = {
        'critical': (0, 25),
        'high': (26, 50),
        'medium': (51, 75),
        'low': (76, 100)
    }
    
    # Status thresholds
    STATUS_THRESHOLDS = {
        'healthy': 80,
        'fair': 60,
        'poor': 40,
        'critical': 0
    }
    
    def __init__(self):
        self.optimal_values = self.OPTIMAL_VALUES
    
    def calculate_score(
        self,
        readings: Dict[str, float],
        anomaly_score: Optional[float] = None,
        anomaly_penalty: float = 30
    ) -> HealthScore:
        """
        Calculate overall health score from sensor readings.
        
        Args:
            readings: Dictionary of sensor readings
            anomaly_score: Optional anomaly score from Isolation Forest (lower = more anomalous)
            anomaly_penalty: Penalty to apply if anomaly detected
            
        Returns:
            HealthScore dataclass with score and details
        """
        factors = {}
        total_penalty = 0
        total_weight = 0
        recommendations = []
        triggering_features = []
        
        for feature, config in self.optimal_values.items():
            if feature not in readings:
                continue
            
            value = readings[feature]
            optimal = config['optimal']
            min_val = config['min']
            max_val = config['max']
            weight = config['weight']
            
            # Calculate deviation penalty
            if value < min_val:
                # Below minimum - severe penalty
                penalty = 50 * weight
                factors[feature] = 0
                recommendations.append(f"{feature.capitalize()} critically low: {value}")
                triggering_features.append(feature)
            elif value > max_val:
                # Above maximum - severe penalty
                penalty = 50 * weight
                factors[feature] = 0
                recommendations.append(f"{feature.capitalize()} critically high: {value}")
                triggering_features.append(feature)
            else:
                # Calculate deviation from optimal
                range_size = max_val - min_val
                optimal_range = range_size * 0.3  # 30% around optimal is "good"
                
                deviation = abs(value - optimal)
                
                if deviation <= optimal_range:
                    # Within optimal range
                    penalty = 0
                    factors[feature] = 100
                else:
                    # Outside optimal range
                    excess = deviation - optimal_range
                    max_excess = range_size - optimal_range
                    penalty = (excess / max_excess) * 50 * weight
                    factors[feature] = max(0, 100 - (excess / max_excess) * 100)
                    
                    if penalty > 25 * weight:
                        recommendations.append(f"{feature.capitalize()} outside optimal range: {value}")
                        triggering_features.append(feature)
            
            total_penalty += penalty
            total_weight += weight
        
        # Apply anomaly penalty if detected
        if anomaly_score is not None:
            # Convert anomaly score to penalty (scores are typically negative)
            # More negative = more anomalous
            anomaly_contribution = min(anomaly_penalty, abs(min(anomaly_score, 0)) * 2)
            total_penalty += anomaly_contribution
        
        # Calculate final score
        final_score = max(0, min(100, int(100 - total_penalty)))
        
        # Determine status
        status = self._get_status(final_score)
        
        # Determine risk level
        risk_level = self._get_risk_level(final_score)
        
        # Generate explanation
        explanation = self._generate_explanation(
            final_score, status, triggering_features, anomaly_score
        )
        
        return HealthScore(
            score=final_score,
            status=status,
            risk_level=risk_level,
            factors=factors,
            explanation=explanation,
            recommendations=recommendations if recommendations else ["All parameters within acceptable ranges"]
        )
    
    def _get_status(self, score: int) -> str:
        """Get health status from score."""
        if score >= self.STATUS_THRESHOLDS['healthy']:
            return "Healthy"
        elif score >= self.STATUS_THRESHOLDS['fair']:
            return "Fair"
        elif score >= self.STATUS_THRESHOLDS['poor']:
            return "Poor"
        else:
            return "Critical"
    
    def _get_risk_level(self, score: int) -> str:
        """Get risk level from score."""
        for level, (min_score, max_score) in self.RISK_THRESHOLDS.items():
            if min_score <= score <= max_score:
                return level.capitalize()
        return "Critical"
    
    def _generate_explanation(
        self,
        score: int,
        status: str,
        triggering_features: List[str],
        anomaly_score: Optional[float]
    ) -> str:
        """Generate human-readable explanation."""
        explanations = []
        
        explanations.append(f"Overall health score: {score}/100 ({status})")
        
        if triggering_features:
            explanations.append(f"Issues detected in: {', '.join(triggering_features)}")
        
        if anomaly_score is not None and anomaly_score < 0:
            explanations.append("Anomaly detection flagged unusual patterns")
        
        if status == "Healthy":
            explanations.append("Equipment operating within normal parameters")
        elif status == "Fair":
            explanations.append("Some parameters require attention")
        elif status == "Poor":
            explanations.append("Multiple parameters need attention. Schedule inspection.")
        else:
            explanations.append("IMMEDIATE ACTION REQUIRED. Risk of failure.")
        
        return ". ".join(explanations)
    
    def calculate_factors_from_raw(
        self,
        readings: Dict[str, float]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Calculate detailed factor analysis for each sensor.
        
        Returns:
            Dictionary with detailed factor analysis
        """
        factors = {}
        
        for feature, config in self.optimal_values.items():
            if feature not in readings:
                continue
            
            value = readings[feature]
            optimal = config['optimal']
            min_val = config['min']
            max_val = config['max']
            
            # Calculate current state
            if value < min_val:
                status = "critical_low"
                deviation = (min_val - value) / min_val if min_val > 0 else 0
            elif value > max_val:
                status = "critical_high"
                deviation = (value - max_val) / max_val if max_val > 0 else 0
            elif abs(value - optimal) < (max_val - min_val) * 0.1:
                status = "optimal"
                deviation = 0
            else:
                status = "warning"
                deviation = abs(value - optimal) / ((max_val - min_val) / 2)
            
            factors[feature] = {
                'value': value,
                'optimal': optimal,
                'min': min_val,
                'max': max_val,
                'status': status,
                'deviation': round(deviation, 3)
            }
        
        return factors


class RiskClassifier:
    """
    Classify equipment risk levels and generate alerts.
    
    Risk Categories:
    - Critical (0-25): Immediate action required
    - High (26-50): Action needed soon
    - Medium (51-75): Monitor closely
    - Low (76-100): Normal operation
    """
    
    ALERT_THRESHOLDS = {
        'temperature': {'warning': 95, 'critical': 110},
        'vibration': {'warning': 3.0, 'critical': 4.5},
        'current': {'warning': 28, 'critical': 32},
        'pressure': {'warning': 90, 'critical': 98},
        'rpm': {'warning': 2200, 'critical': 2400}
    }
    
    def __init__(self):
        self.thresholds = self.ALERT_THRESHOLDS
    
    def classify_risk(
        self,
        readings: Dict[str, float],
        health_score: int
    ) -> Dict[str, Any]:
        """
        Classify equipment risk level.
        
        Args:
            readings: Sensor readings
            health_score: Calculated health score
            
        Returns:
            Dictionary with risk classification and alerts
        """
        alerts = []
        risk_factors = []
        
        # Check each sensor against thresholds
        for feature, thresholds in self.thresholds.items():
            if feature not in readings:
                continue
            
            value = readings[feature]
            
            if value >= thresholds['critical']:
                alerts.append({
                    'type': 'critical',
                    'feature': feature,
                    'value': value,
                    'threshold': thresholds['critical'],
                    'message': f"CRITICAL: {feature} = {value} exceeds critical threshold ({thresholds['critical']})"
                })
                risk_factors.append(feature)
            elif value >= thresholds['warning']:
                alerts.append({
                    'type': 'high',
                    'feature': feature,
                    'value': value,
                    'threshold': thresholds['warning'],
                    'message': f"WARNING: {feature} = {value} exceeds warning threshold ({thresholds['warning']})"
                })
                risk_factors.append(feature)
        
        # Determine overall risk level
        if health_score <= 25:
            risk_level = 'Critical'
            alert_level = 'critical'
        elif health_score <= 50:
            risk_level = 'High'
            alert_level = 'high' if alerts else 'medium'
        elif health_score <= 75:
            risk_level = 'Medium'
            alert_level = 'medium' if alerts else 'low'
        else:
            risk_level = 'Low'
            alert_level = 'low'
        
        return {
            'risk_level': risk_level,
            'alert_level': alert_level,
            'health_score': health_score,
            'alerts': alerts,
            'risk_factors': risk_factors,
            'requires_immediate_action': health_score <= 25 or any(a['type'] == 'critical' for a in alerts)
        }
    
    def get_risk_category(self, score: int) -> str:
        """Get risk category from score."""
        if score <= 25:
            return "Critical"
        elif score <= 50:
            return "High"
        elif score <= 75:
            return "Medium"
        else:
            return "Low"


def explain_anomaly(
    readings: Dict[str, float],
    anomaly_score: float,
    feature_importance: Dict[str, float],
    thresholds: Dict[str, Dict[str, float]]
) -> AnomalyExplanation:
    """
    Generate explainable AI results for anomaly detection.
    
    Args:
        readings: Sensor readings
        anomaly_score: Isolation Forest score
        feature_importance: Feature importance scores
        thresholds: Sensor thresholds
        
    Returns:
        AnomalyExplanation with detailed reasoning
    """
    is_anomaly = anomaly_score < 0
    
    triggering_features = []
    for feature, importance in feature_importance.items():
        if feature in readings:
            value = readings[feature]
            threshold = thresholds.get(feature, {}).get('critical', float('inf'))
            
            triggering_features.append({
                'name': feature,
                'value': value,
                'threshold': threshold,
                'deviation': round(abs(value - threshold) / threshold, 3) if threshold > 0 else 0,
                'importance': importance
            })
    
    # Sort by importance
    triggering_features.sort(key=lambda x: x['importance'], reverse=True)
    
    # Generate risk explanation
    if is_anomaly:
        risk_explanation = f"Anomaly detected with score {anomaly_score:.3f}. "
        
        if triggering_features:
            top_features = [f['name'] for f in triggering_features[:3]]
            risk_explanation += f"Primary contributing factors: {', '.join(top_features)}."
        
        if any(f['value'] > f['threshold'] for f in triggering_features):
            exceeded = [f for f in triggering_features if f['value'] > f['threshold']]
            risk_explanation += f" Thresholds exceeded: {', '.join([f['name'] for f in exceeded])}."
    else:
        risk_explanation = "Equipment operating within normal parameters. No anomalies detected."
    
    # Calculate confidence
    confidence = min(1.0, abs(anomaly_score) / 10 + 0.5) if is_anomaly else 0.9
    
    return AnomalyExplanation(
        is_anomaly=is_anomaly,
        anomaly_score=anomaly_score,
        triggering_features=triggering_features,
        risk_explanation=risk_explanation,
        confidence=confidence
    )


# Singleton instance
_health_calculator: Optional[HealthScoreCalculator] = None
_risk_classifier: Optional[RiskClassifier] = None


def get_health_calculator() -> HealthScoreCalculator:
    """Get global health calculator instance."""
    global _health_calculator
    if _health_calculator is None:
        _health_calculator = HealthScoreCalculator()
    return _health_calculator


def get_risk_classifier() -> RiskClassifier:
    """Get global risk classifier instance."""
    global _risk_classifier
    if _risk_classifier is None:
        _risk_classifier = RiskClassifier()
    return _risk_classifier