"""Prediction Service combining anomaly detection, health scoring, and alerts."""
from typing import Dict, Any, Optional, List
from datetime import datetime
from dataclasses import dataclass, asdict

from app.anomaly_detection.detector import (
    get_anomaly_detector,
    get_preprocessor,
    train_initial_model,
    SensorPreprocessor
)
from app.health.health_score import (
    get_health_calculator,
    get_risk_classifier,
    explain_anomaly,
    HealthScoreCalculator,
    RiskClassifier,
    HealthScore
)
from app.health.alert_engine import (
    get_alert_engine,
    AlertEngine,
    Alert
)


@dataclass
class PredictionResult:
    """Combined prediction result for a sensor reading."""
    equipment_name: str
    timestamp: datetime
    anomaly: bool
    anomaly_score: float
    health_score: int
    health_status: str
    risk_level: str
    message: str
    recommendations: List[str]
    alerts: List[Dict[str, Any]]
    explanation: Dict[str, Any]
    sensor_readings: Dict[str, float]


class PredictionService:
    """
    Unified prediction service combining:
    - Anomaly Detection (Isolation Forest)
    - Health Score Calculation
    - Risk Classification
    - Alert Generation
    """
    
    def __init__(self):
        self.detector = get_anomaly_detector()
        self.preprocessor = get_preprocessor()
        self.health_calculator = get_health_calculator()
        self.risk_classifier = get_risk_classifier()
        self.alert_engine = get_alert_engine()
        
        # Initialize model if not already done
        self._ensure_model_ready()
    
    def _ensure_model_ready(self):
        """Ensure anomaly detection model is trained and ready."""
        if not self.detector.is_trained:
            try:
                train_initial_model()
                print("Anomaly detection model initialized")
            except Exception as e:
                print(f"Warning: Could not initialize anomaly model: {e}")
    
    def predict(
        self,
        equipment_name: str,
        temperature: float,
        vibration: float,
        current: float,
        pressure: float,
        rpm: float,
        include_explanation: bool = True
    ) -> PredictionResult:
        """
        Perform complete analysis on sensor readings.
        
        Args:
            equipment_name: Name of the equipment
            temperature: Temperature in °C
            vibration: Vibration in mm/s
            current: Current in A
            pressure: Pressure in bar
            rpm: RPM
            include_explanation: Whether to include detailed explanation
            
        Returns:
            PredictionResult with all analysis results
        """
        # Prepare readings
        readings = {
            'temperature': temperature,
            'vibration': vibration,
            'current': current,
            'pressure': pressure,
            'rpm': rpm
        }
        
        timestamp = datetime.now()
        
        # Step 1: Preprocess and predict anomaly
        anomaly_result = self._detect_anomaly(readings)
        
        # Step 2: Calculate health score
        health_result = self._calculate_health(readings, anomaly_result['score'])
        
        # Step 3: Classify risk
        risk_result = self._classify_risk(readings, health_result.score)
        
        # Step 4: Generate alerts
        alerts = self._generate_alerts(
            equipment_name,
            readings,
            anomaly_result,
            health_result.score
        )
        
        # Step 5: Generate message
        message = self._generate_message(
            anomaly_result['is_anomaly'],
            health_result.status,
            health_result.score,
            alerts
        )
        
        # Step 6: Generate explanation if requested
        explanation = {}
        if include_explanation:
            explanation = self._generate_explanation(
                readings,
                anomaly_result,
                health_result,
                risk_result
            )
        
        return PredictionResult(
            equipment_name=equipment_name,
            timestamp=timestamp,
            anomaly=anomaly_result['is_anomaly'],
            anomaly_score=anomaly_result['score'],
            health_score=health_result.score,
            health_status=health_result.status,
            risk_level=health_result.risk_level,
            message=message,
            recommendations=health_result.recommendations,
            alerts=alerts,
            explanation=explanation,
            sensor_readings=readings
        )
    
    def _detect_anomaly(self, readings: Dict[str, float]) -> Dict[str, Any]:
        """Detect anomaly using Isolation Forest."""
        if not self.detector.is_trained or not self.preprocessor.is_fitted:
            # Return default (normal) if model not ready
            return {
                'is_anomaly': False,
                'score': 0.0,
                'features': {}
            }
        
        try:
            import numpy as np
            # Prepare feature vector as numpy array
            features = np.array([[
                readings['temperature'],
                readings['vibration'],
                readings['current'],
                readings['pressure'],
                readings['rpm']
            ]], dtype=float)

            # Scale features
            scaled_features = self.preprocessor.transform(features)[0]

            # Convert to numpy array explicitly before passing
            scaled_arr = np.array([scaled_features])

            # Get anomaly score
            anomaly_score = self.detector.predict_proba(scaled_arr)[0]
            is_anomaly = self.detector.predict(scaled_arr)[0] == -1

            # Get feature importance
            feature_importance = self.detector.get_feature_importance(scaled_arr)

            return {
                'is_anomaly': bool(is_anomaly),
                'score': float(anomaly_score),
                'features': feature_importance
            }
        except Exception as e:
            print(f"Error in anomaly detection: {e}")
            return {
                'is_anomaly': False,
                'score': 0.0,
                'features': {}
            }
    
    def _calculate_health(
        self,
        readings: Dict[str, float],
        anomaly_score: Optional[float]
    ) -> HealthScore:
        """Calculate equipment health score."""
        return self.health_calculator.calculate_score(readings, anomaly_score)
    
    def _classify_risk(
        self,
        readings: Dict[str, float],
        health_score: int
    ) -> Dict[str, Any]:
        """Classify risk level."""
        return self.risk_classifier.classify_risk(readings, health_score)
    
    def _generate_alerts(
        self,
        equipment_name: str,
        readings: Dict[str, float],
        anomaly_result: Dict[str, Any],
        health_score: int
    ) -> List[Dict[str, Any]]:
        """Generate alerts."""
        alerts = get_alert_engine().generate_alerts(
            equipment_name,
            readings,
            anomaly_result if anomaly_result['is_anomaly'] else None,
            health_score
        )
        
        return [
            {
                'alert_id': a.alert_id,
                'type': a.alert_type,
                'severity': a.severity,
                'message': a.message,
                'timestamp': a.timestamp.isoformat(),
                'status': a.status,
                'source': a.source
            }
            for a in alerts
        ]
    
    def _generate_message(
        self,
        is_anomaly: bool,
        health_status: str,
        health_score: int,
        alerts: List[Dict]
    ) -> str:
        """Generate human-readable message."""
        messages = []
        
        if is_anomaly:
            messages.append("Anomaly detected in sensor patterns.")
        
        messages.append(f"Health Status: {health_status} (Score: {health_score})")
        
        if alerts:
            critical_alerts = [a for a in alerts if a['type'] == 'critical']
            if critical_alerts:
                messages.append(f"CRITICAL: {len(critical_alerts)} critical alert(s) require immediate attention.")
        
        if health_score <= 25:
            messages.append("IMMEDIATE ACTION REQUIRED - Equipment at risk of failure.")
        elif health_score <= 50:
            messages.append("Equipment requires attention. Schedule maintenance.")
        
        return " ".join(messages)
    
    def _generate_explanation(
        self,
        readings: Dict[str, float],
        anomaly_result: Dict[str, Any],
        health_result: HealthScore,
        risk_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate detailed explanation for predictions."""
        explanation = {
            'health_analysis': {
                'score': health_result.score,
                'status': health_result.status,
                'factors': health_result.factors,
                'explanation': health_result.explanation
            },
            'risk_analysis': {
                'level': risk_result['risk_level'],
                'alert_level': risk_result['alert_level'],
                'risk_factors': risk_result['risk_factors']
            },
            'anomaly_analysis': {
                'detected': anomaly_result['is_anomaly'],
                'score': anomaly_result['score'],
                'triggering_features': []
            }
        }
        
        # Add triggering features
        if anomaly_result['features']:
            for feature, importance in anomaly_result['features'].items():
                if feature in readings:
                    explanation['anomaly_analysis']['triggering_features'].append({
                        'feature': feature,
                        'value': readings[feature],
                        'importance': importance
                    })
        
        return explanation
    
    def get_equipment_health(
        self,
        equipment_name: str,
        recent_readings: List[Dict[str, float]]
    ) -> Dict[str, Any]:
        """
        Get overall health status for equipment based on recent readings.
        
        Args:
            equipment_name: Name of equipment
            recent_readings: List of recent sensor readings
            
        Returns:
            Health summary with trends
        """
        if not recent_readings:
            return {
                'equipment_name': equipment_name,
                'status': 'unknown',
                'message': 'No recent sensor data available'
            }
        
        # Calculate health for each reading
        health_scores = []
        anomaly_counts = 0
        
        for reading in recent_readings:
            try:
                # Calculate health score only — do NOT generate new alerts
                anomaly_result = self._detect_anomaly(reading)
                health_result  = self._calculate_health(reading, anomaly_result['score'])
                health_scores.append(health_result.score)
                if anomaly_result['is_anomaly']:
                    anomaly_counts += 1
            except Exception:
                continue
        
        if not health_scores:
            return {
                'equipment_name': equipment_name,
                'status': 'unknown',
                'message': 'Could not process sensor data'
            }
        
        # Calculate trends
        avg_score = sum(health_scores) / len(health_scores)
        latest_score = health_scores[-1]
        
        # Determine trend
        if len(health_scores) >= 3:
            recent_avg = sum(health_scores[-3:]) / 3
            older_avg = sum(health_scores[:-3]) / (len(health_scores) - 3) if len(health_scores) > 3 else recent_avg
            trend = 'improving' if recent_avg > older_avg else 'declining' if recent_avg < older_avg else 'stable'
        else:
            trend = 'stable'
        
        # Determine overall status
        if avg_score >= 80:
            status = 'healthy'
        elif avg_score >= 60:
            status = 'fair'
        elif avg_score >= 40:
            status = 'poor'
        else:
            status = 'critical'
        
        return {
            'equipment_name': equipment_name,
            'status': status,
            'health_score': int(avg_score),
            'latest_score': latest_score,
            'trend': trend,
            'anomaly_count': anomaly_counts,
            'total_readings': len(health_scores),
            'anomaly_rate': anomaly_counts / len(health_scores) if health_scores else 0
        }


# Singleton instance
_prediction_service: Optional[PredictionService] = None


def get_prediction_service() -> PredictionService:
    """Get global prediction service instance."""
    global _prediction_service
    if _prediction_service is None:
        _prediction_service = PredictionService()
    return _prediction_service