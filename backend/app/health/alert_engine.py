"""Alert Engine for generating and managing equipment alerts."""
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, asdict
from collections import defaultdict


@dataclass
class Alert:
    """Equipment alert dataclass."""
    alert_id: str
    equipment_name: str
    alert_type: str  # low, medium, high, critical
    severity: int  # 1-4 (1=low, 4=critical)
    message: str
    timestamp: datetime
    status: str  # active, acknowledged, resolved
    source: str  # threshold, anomaly, health_score
    sensor_readings: Optional[Dict[str, float]] = None
    health_score: Optional[int] = None
    acknowledged_at: Optional[datetime] = None
    acknowledged_by: Optional[str] = None
    resolved_at: Optional[datetime] = None


class AlertEngine:
    """
    Generate alerts based on sensor readings and anomaly detection.
    
    Alert Types:
    - Threshold Alerts: When sensor values exceed defined thresholds
    - Anomaly Alerts: When Isolation Forest detects anomalies
    - Health Alerts: When health score drops below threshold
    - Trend Alerts: When sensor values show concerning trends
    """
    
    # Equipment-specific thresholds matching sensor profiles in sensor_data.py
    EQUIPMENT_THRESHOLDS = {
        "Rolling Mill Motor": {
            'temperature': {'low':20, 'warning':95,  'critical':110},
            'vibration':   {'low':0.3,'warning':2.8, 'critical':4.0},
            'current':     {'low':5,  'warning':28,  'critical':32},
            'pressure':    {'low':50, 'warning':90,  'critical':95},
            'rpm':         {'low':800,'warning':2000,'critical':2200},
        },
        "Blast Furnace Fan": {
            'temperature': {'low':20, 'warning':85,  'critical':93},
            'vibration':   {'low':0.3,'warning':3.0, 'critical':4.5},
            'current':     {'low':10, 'warning':52,  'critical':58},
            'pressure':    {'low':50, 'warning':230, 'critical':248},
            'rpm':         {'low':800,'warning':1010,'critical':1020},
        },
        "Cooling Pump A": {
            'temperature': {'low':10, 'warning':75,  'critical':85},
            'vibration':   {'low':0.2,'warning':2.5, 'critical':3.5},
            'current':     {'low':5,  'warning':30,  'critical':35},
            'pressure':    {'low':20, 'warning':50,  'critical':54},
            'rpm':         {'low':800,'warning':1750,'critical':1800},
        },
        "Main Compressor": {
            'temperature': {'low':20, 'warning':90,  'critical':100},
            'vibration':   {'low':0.3,'warning':2.8, 'critical':4.0},
            'current':     {'low':10, 'warning':55,  'critical':60},
            'pressure':    {'low':2,  'warning':11,  'critical':12},
            'rpm':         {'low':800,'warning':1530,'critical':1550},
        },
        "Conveyor Belt System": {
            'temperature': {'low':10, 'warning':50,  'critical':60},
            'vibration':   {'low':0.1,'warning':2.0, 'critical':2.5},
            'current':     {'low':3,  'warning':22,  'critical':25},
            'pressure':    {'low':1,  'warning':7,   'critical':8},
            'rpm':         {'low':400,'warning':1150,'critical':1200},
        },
    }

    # Fallback thresholds for unknown equipment
    DEFAULT_THRESHOLDS = {
        'temperature': {'low':20,  'warning':95,  'critical':110},
        'vibration':   {'low':0.3, 'warning':3.0, 'critical':4.5},
        'current':     {'low':5,   'warning':30,  'critical':38},
        'pressure':    {'low':1,   'warning':90,  'critical':98},
        'rpm':         {'low':500, 'warning':2100,'critical':2400},
    }
    
    ALERT_SEVERITY = {
        'low': 1,
        'medium': 2,
        'high': 3,
        'critical': 4
    }
    
    def __init__(self):
        self.thresholds = self.DEFAULT_THRESHOLDS
        self._alert_history: List[Alert] = []
        self._alert_counts = defaultdict(int)
        # Track active alert keys to prevent duplicates: (equipment, source, sensor)
        self._active_keys: set = set()
    
    def check_thresholds(
        self,
        equipment_name: str,
        readings: Dict[str, float]
    ) -> List[Alert]:
        alerts = []
        eq_thresholds = self.EQUIPMENT_THRESHOLDS.get(equipment_name, self.DEFAULT_THRESHOLDS)

        for sensor, value in readings.items():
            if sensor not in eq_thresholds:
                continue
            t = eq_thresholds[sensor]
            crit_val = t.get('critical', 9999)
            warn_val = t.get('warning', 9999)
            # Only fire on HIGH values — skip low threshold (causes too many false alerts)
            if value >= crit_val:
                alerts.append(self._create_alert(
                    equipment_name, 'critical',
                    f"{sensor.capitalize()}: critically high ({value:.1f})",
                    'threshold', {sensor: value}
                ))
            elif value >= warn_val:
                alerts.append(self._create_alert(
                    equipment_name, 'high',
                    f"{sensor.capitalize()}: approaching critical ({value:.1f})",
                    'threshold', {sensor: value}
                ))
        return alerts
    
    def check_anomaly(
        self,
        equipment_name: str,
        anomaly_score: float,
        readings: Dict[str, float],
        is_anomaly: bool
    ) -> Optional[Alert]:
        """
        Generate alert based on anomaly detection.
        
        Args:
            equipment_name: Name of the equipment
            anomaly_score: Isolation Forest score
            readings: Sensor readings
            is_anomaly: Whether anomaly was detected
            
        Returns:
            Alert if anomaly detected, None otherwise
        """
        if not is_anomaly:
            return None
        
        # Determine severity based on anomaly score
        if anomaly_score < -0.5:
            alert_type = 'critical'
        elif anomaly_score < -0.2:
            alert_type = 'high'
        else:
            alert_type = 'medium'
        
        # Find contributing factors
        factors = self._find_anomaly_factors(readings)
        
        message = f"Anomaly detected (score: {anomaly_score:.3f}). "
        if factors:
            message += f"Contributing factors: {', '.join(factors)}"
        else:
            message += "Unusual pattern detected in sensor data"
        
        return self._create_alert(
            equipment_name=equipment_name,
            alert_type=alert_type,
            message=message,
            source='anomaly',
            sensor_readings=readings
        )
    
    def check_health_score(
        self,
        equipment_name: str,
        health_score: int,
        readings: Dict[str, float]
    ) -> Optional[Alert]:
        """
        Generate alert based on health score.
        
        Args:
            equipment_name: Name of the equipment
            health_score: Calculated health score (0-100)
            readings: Sensor readings
            
        Returns:
            Alert if health score indicates issue, None otherwise
        """
        if health_score >= 80:
            return None  # Healthy, no alert
        
        if health_score <= 25:
            alert_type = 'critical'
            message = f"CRITICAL: Equipment health score {health_score}. Immediate action required."
        elif health_score <= 50:
            alert_type = 'high'
            message = f"HIGH RISK: Equipment health score {health_score}. Action needed soon."
        else:  # 51-79
            alert_type = 'medium'
            message = f"MEDIUM RISK: Equipment health score {health_score}. Monitor closely."
        
        return self._create_alert(
            equipment_name=equipment_name,
            alert_type=alert_type,
            message=message,
            source='health_score',
            sensor_readings=readings,
            health_score=health_score
        )
    
    def generate_alerts(
        self,
        equipment_name: str,
        readings: Dict[str, float],
        anomaly_result: Optional[Dict[str, Any]] = None,
        health_score: Optional[int] = None
    ) -> List[Alert]:
        """
        Generate all applicable alerts for equipment.
        
        Args:
            equipment_name: Name of the equipment
            readings: Sensor readings
            anomaly_result: Optional anomaly detection result
            health_score: Optional calculated health score
            
        Returns:
            List of all generated alerts
        """
        all_alerts = []
        
        # Threshold alerts
        threshold_alerts = self.check_thresholds(equipment_name, readings)
        all_alerts.extend(threshold_alerts)
        
        # Anomaly alert
        if anomaly_result:
            anomaly_alert = self.check_anomaly(
                equipment_name,
                anomaly_result.get('score', 0),
                readings,
                anomaly_result.get('is_anomaly', False)
            )
            if anomaly_alert:
                all_alerts.extend([anomaly_alert])
        
        # Health score alert
        if health_score is not None:
            health_alert = self.check_health_score(equipment_name, health_score, readings)
            if health_alert:
                all_alerts.extend([health_alert])
        
        # Store alerts — only if no active alert with same key already exists
        new_alerts = []
        for alert in all_alerts:
            key = (alert.equipment_name, alert.source, alert.alert_type, alert.message[:40])
            if key not in self._active_keys:
                self._active_keys.add(key)
                self._alert_history.append(alert)
                self._alert_counts[alert.alert_type] += 1
                new_alerts.append(alert)

        # Deduplicate by equipment and message type
        return self._deduplicate_alerts(new_alerts)
    
    def _create_alert(
        self,
        equipment_name: str,
        alert_type: str,
        message: str,
        source: str,
        sensor_readings: Optional[Dict[str, float]] = None,
        health_score: Optional[int] = None
    ) -> Alert:
        """Create an alert instance."""
        return Alert(
            alert_id=str(uuid.uuid4()),
            equipment_name=equipment_name,
            alert_type=alert_type,
            severity=self.ALERT_SEVERITY.get(alert_type, 1),
            message=message,
            timestamp=datetime.now(),
            status='active',
            source=source,
            sensor_readings=sensor_readings,
            health_score=health_score
        )
    
    def _find_anomaly_factors(self, readings: Dict[str, float]) -> List[str]:
        """Find which sensors are contributing to anomaly."""
        factors = []
        thresholds = self.DEFAULT_THRESHOLDS
        
        for sensor, value in readings.items():
            if sensor not in thresholds:
                continue
            
            t = thresholds[sensor]
            if value >= t['warning']['value']:
                factors.append(f"{sensor}={value}")
        
        return factors[:3]  # Return top 3
    
    def _deduplicate_alerts(self, alerts: List[Alert]) -> List[Alert]:
        """Remove duplicate alerts within a short time window."""
        seen = set()
        unique_alerts = []
        
        for alert in alerts:
            key = (alert.equipment_name, alert.alert_type, alert.source)
            if key not in seen:
                seen.add(key)
                unique_alerts.append(alert)
        
        return unique_alerts
    
    def acknowledge_alert(self, alert_id: str, acknowledged_by: str = 'system') -> bool:
        """Mark an alert as acknowledged."""
        for alert in self._alert_history:
            if alert.alert_id == alert_id:
                alert.status = 'acknowledged'
                alert.acknowledged_at = datetime.now()
                alert.acknowledged_by = acknowledged_by
                # Remove from active keys so re-trigger is possible
                key = (alert.equipment_name, alert.source, alert.alert_type, alert.message[:40])
                self._active_keys.discard(key)
                return True
        return False

    def resolve_alert(self, alert_id: str) -> bool:
        """Mark an alert as resolved."""
        for alert in self._alert_history:
            if alert.alert_id == alert_id:
                alert.status = 'resolved'
                alert.resolved_at = datetime.now()
                key = (alert.equipment_name, alert.source, alert.alert_type, alert.message[:40])
                self._active_keys.discard(key)
                return True
        return False
    
    def get_active_alerts(
        self,
        equipment_name: Optional[str] = None,
        alert_type: Optional[str] = None,
        limit: int = 100
    ) -> List[Alert]:
        """Get active (non-resolved) alerts."""
        alerts = [
            a for a in self._alert_history
            if a.status != 'resolved'
        ]
        
        if equipment_name:
            alerts = [a for a in alerts if a.equipment_name == equipment_name]
        
        if alert_type:
            alerts = [a for a in alerts if a.alert_type == alert_type]
        
        # Sort by severity (descending) and timestamp (descending)
        alerts.sort(key=lambda x: (-x.severity, -x.timestamp.timestamp()))
        
        return alerts[:limit]
    
    def get_alert_summary(self) -> Dict[str, Any]:
        """Get summary of alerts by type and status."""
        summary = {
            'total': len(self._alert_history),
            'active': len([a for a in self._alert_history if a.status == 'active']),
            'acknowledged': len([a for a in self._alert_history if a.status == 'acknowledged']),
            'resolved': len([a for a in self._alert_history if a.status == 'resolved']),
            'by_type': dict(self._alert_counts),
            'critical_count': len([a for a in self._alert_history if a.alert_type == 'critical' and a.status == 'active'])
        }
        return summary
    
    def clear_history(self):
        """Clear alert history."""
        self._alert_history = []
        self._alert_counts.clear()


# Singleton instance
_alert_engine: Optional[AlertEngine] = None


def get_alert_engine() -> AlertEngine:
    """Get global alert engine instance."""
    global _alert_engine
    if _alert_engine is None:
        _alert_engine = AlertEngine()
    return _alert_engine