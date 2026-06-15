"""
Failure Pattern Matching Engine.

This module provides rule-based pattern matching for identifying
common failure patterns based on sensor symptom combinations.
"""
import json
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime


@dataclass
class FailurePattern:
    """Represents a failure pattern."""
    pattern_id: str
    name: str
    symptoms: Dict[str, Any]  # Symptom conditions
    probable_cause: str
    confidence_weight: float  # 0-1
    description: str
    recommended_actions: List[str]


class PatternEngine:
    """
    Rule-based failure pattern matching engine.
    
    Matches sensor readings against known failure patterns
    to identify probable causes.
    """
    
    # Default failure patterns for steel plant equipment
    DEFAULT_PATTERNS = [
        FailurePattern(
            pattern_id="FP001",
            name="Bearing Wear Pattern",
            symptoms={
                "vibration": {"min": 2.5, "max": 5.0},
                "temperature": {"min": 80, "max": 110},
                "current": {"min": 20, "max": 35}
            },
            probable_cause="Bearing Wear",
            confidence_weight=0.85,
            description="High vibration with elevated temperature indicates bearing degradation",
            recommended_actions=["Inspect bearing", "Check lubrication", "Measure vibration amplitude"]
        ),
        FailurePattern(
            pattern_id="FP002",
            name="Bearing Failure Pattern",
            symptoms={
                "vibration": {"min": 4.0, "max": 20.0},
                "temperature": {"min": 95, "max": 150},
                "current": {"min": 25, "max": 50}
            },
            probable_cause="Bearing Failure",
            confidence_weight=0.92,
            description="Severe vibration and temperature indicate imminent bearing failure",
            recommended_actions=["Immediate inspection", "Replace bearing", "Check shaft alignment"]
        ),
        FailurePattern(
            pattern_id="FP003",
            name="Pump Blockage Pattern",
            symptoms={
                "pressure": {"min": 0, "max": 45},
                "current": {"min": 25, "max": 50},
                "vibration": {"min": 1.5, "max": 4.0}
            },
            probable_cause="Pump Blockage",
            confidence_weight=0.78,
            description="Low pressure with high current indicates flow restriction",
            recommended_actions=["Inspect pump inlet", "Check for debris", "Clean filters"]
        ),
        FailurePattern(
            pattern_id="FP004",
            name="Motor Overheating Pattern",
            symptoms={
                "temperature": {"min": 95, "max": 150},
                "current": {"min": 28, "max": 50},
                "vibration": {"min": 2.0, "max": 4.0}
            },
            probable_cause="Motor Overheating",
            confidence_weight=0.88,
            description="High temperature and current indicate motor thermal stress",
            recommended_actions=["Check cooling system", "Inspect ventilation", "Measure winding temperature"]
        ),
        FailurePattern(
            pattern_id="FP005",
            name="Mechanical Load Increase Pattern",
            symptoms={
                "current": {"min": 28, "max": 50},
                "rpm": {"min": 0, "max": 1200}
            },
            probable_cause="Mechanical Load Increase",
            confidence_weight=0.72,
            description="High current with reduced RPM indicates mechanical overload",
            recommended_actions=["Inspect drive system", "Check gearbox", "Verify load conditions"]
        ),
        FailurePattern(
            pattern_id="FP006",
            name="Shaft Misalignment Pattern",
            symptoms={
                "vibration": {"min": 3.0, "max": 5.0},
                "temperature": {"min": 70, "max": 95},
                "rpm": {"min": 1200, "max": 2500}
            },
            probable_cause="Shaft Misalignment",
            confidence_weight=0.75,
            description="Elevated vibration at specific frequencies indicates alignment issues",
            recommended_actions=["Check coupling alignment", "Inspect coupling wear", "Verify base mounting"]
        ),
        FailurePattern(
            pattern_id="FP007",
            name="Lubrication Failure Pattern",
            symptoms={
                "temperature": {"min": 85, "max": 120},
                "vibration": {"min": 2.0, "max": 4.5}
            },
            probable_cause="Lubrication Failure",
            confidence_weight=0.80,
            description="Temperature increase with vibration indicates inadequate lubrication",
            recommended_actions=["Check lubricant levels", "Inspect lubricant condition", "Replace lubricant"]
        ),
        FailurePattern(
            pattern_id="FP008",
            name="Electrical Fault Pattern",
            symptoms={
                "current": {"min": 30, "max": 50},
                "temperature": {"min": 80, "max": 130},
                "vibration": {"min": 0, "max": 2.0}
            },
            probable_cause="Electrical Fault",
            confidence_weight=0.82,
            description="High current without proportional vibration indicates electrical issues",
            recommended_actions=["Check motor windings", "Inspect electrical connections", "Test insulation"]
        ),
        FailurePattern(
            pattern_id="FP009",
            name="Cooling System Failure Pattern",
            symptoms={
                "temperature": {"min": 100, "max": 150},
                "current": {"min": 15, "max": 30}
            },
            probable_cause="Cooling System Failure",
            confidence_weight=0.85,
            description="High temperature with normal current indicates cooling system failure",
            recommended_actions=["Check coolant flow", "Inspect cooling fans", "Clean heat exchangers"]
        ),
        FailurePattern(
            pattern_id="FP010",
            name="Worn Gear Pattern",
            symptoms={
                "vibration": {"min": 3.5, "max": 6.0},
                "rpm": {"min": 500, "max": 2000},
                "temperature": {"min": 75, "max": 100}
            },
            probable_cause="Worn Gear",
            confidence_weight=0.77,
            description="Periodic vibration spikes indicate gear tooth wear",
            recommended_actions=["Inspect gearbox", "Check gear teeth", "Verify lubrication"]
        )
    ]
    
    def __init__(self, patterns_file: Optional[str] = None):
        self.patterns: List[FailurePattern] = []
        self.patterns_file = patterns_file
        self._load_patterns()
    
    def _load_patterns(self):
        """Load patterns from file or use defaults."""
        if self.patterns_file and Path(self.patterns_file).exists():
            try:
                with open(self.patterns_file, 'r') as f:
                    data = json.load(f)
                    for p in data:
                        self.patterns.append(FailurePattern(**p))
            except Exception:
                self.patterns = self.DEFAULT_PATTERNS.copy()
        else:
            self.patterns = self.DEFAULT_PATTERNS.copy()
    
    def save_patterns(self):
        """Save patterns to file."""
        if self.patterns_file:
            with open(self.patterns_file, 'w') as f:
                json.dump([{
                    'pattern_id': p.pattern_id,
                    'name': p.name,
                    'symptoms': p.symptoms,
                    'probable_cause': p.probable_cause,
                    'confidence_weight': p.confidence_weight,
                    'description': p.description,
                    'recommended_actions': p.recommended_actions
                } for p in self.patterns], f, indent=2)
    
    def match_patterns(
        self,
        temperature: Optional[float] = None,
        vibration: Optional[float] = None,
        current: Optional[float] = None,
        pressure: Optional[float] = None,
        rpm: Optional[float] = None,
        min_confidence: float = 0.5
    ) -> List[Tuple[FailurePattern, float]]:
        """
        Match sensor readings against known patterns.
        
        Args:
            temperature: Temperature reading (°C)
            vibration: Vibration reading (mm/s)
            current: Current reading (A)
            pressure: Pressure reading (bar)
            rpm: RPM reading
            min_confidence: Minimum confidence threshold
            
        Returns:
            List of (pattern, match_score) tuples sorted by score
        """
        readings = {
            'temperature': temperature,
            'vibration': vibration,
            'current': current,
            'pressure': pressure,
            'rpm': rpm
        }
        
        matches = []
        
        for pattern in self.patterns:
            score = self._calculate_match_score(pattern, readings)
            if score >= min_confidence:
                matches.append((pattern, score))
        
        # Sort by score descending
        matches.sort(key=lambda x: x[1], reverse=True)
        return matches
    
    def _calculate_match_score(
        self,
        pattern: FailurePattern,
        readings: Dict[str, Optional[float]]
    ) -> float:
        """
        Calculate how well sensor readings match a pattern.
        
        Returns score between 0 and 1.
        """
        matched_symptoms = 0
        total_symptoms = 0
        
        for symptom_name, condition in pattern.symptoms.items():
            value = readings.get(symptom_name)
            if value is None:
                continue
            
            total_symptoms += 1
            
            min_val = condition.get('min', float('-inf'))
            max_val = condition.get('max', float('inf'))
            
            if min_val <= value <= max_val:
                # Check how optimal the match is
                optimal = (min_val + max_val) / 2
                range_size = (max_val - min_val) / 2
                
                if range_size > 0:
                    deviation = abs(value - optimal) / range_size
                    symptom_score = 1.0 - (deviation * 0.3)  # Partial credit for deviation
                    matched_symptoms += max(0.5, symptom_score)
                else:
                    matched_symptoms += 1.0
        
        if total_symptoms == 0:
            return 0.0
        
        return (matched_symptoms / total_symptoms) * pattern.confidence_weight
    
    def get_pattern_by_cause(self, cause: str) -> Optional[FailurePattern]:
        """Get pattern by probable cause name."""
        for pattern in self.patterns:
            if pattern.probable_cause.lower() == cause.lower():
                return pattern
        return None
    
    def get_all_patterns(self) -> List[FailurePattern]:
        """Get all registered patterns."""
        return self.patterns.copy()
    
    def add_pattern(self, pattern: FailurePattern):
        """Add a new pattern."""
        self.patterns.append(pattern)
        self.save_patterns()
    
    def update_pattern(self, pattern_id: str, updates: Dict[str, Any]):
        """Update an existing pattern."""
        for i, pattern in enumerate(self.patterns):
            if pattern.pattern_id == pattern_id:
                for key, value in updates.items():
                    if hasattr(pattern, key):
                        setattr(pattern, key, value)
                self.save_patterns()
                return True
        return False
    
    def delete_pattern(self, pattern_id: str) -> bool:
        """Delete a pattern."""
        initial_len = len(self.patterns)
        self.patterns = [p for p in self.patterns if p.pattern_id != pattern_id]
        if len(self.patterns) < initial_len:
            self.save_patterns()
            return True
        return False


# Singleton instance
_pattern_engine: Optional[PatternEngine] = None


def get_pattern_engine() -> PatternEngine:
    """Get global pattern engine instance."""
    global _pattern_engine
    if _pattern_engine is None:
        _pattern_engine = PatternEngine()
    return _pattern_engine