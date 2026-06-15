"""
Confidence Scoring Engine.

This module calculates confidence scores for root cause analysis
based on multiple evidence sources.
"""
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime

from app.rca.pattern_engine import FailurePattern, get_pattern_engine
from app.rca.similar_case_retriever import SimilarCase


@dataclass
class ConfidenceComponent:
    """Component contributing to overall confidence."""
    source: str  # 'pattern', 'historical', 'sensor', 'documentation'
    weight: float  # 0-1, importance of this source
    score: float  # 0-1, how well this source supports the conclusion
    evidence: List[str] = field(default_factory=list)  # Evidence items
    details: str = ""  # Additional details


@dataclass
class ConfidenceResult:
    """Overall confidence result."""
    overall_confidence: float  # 0-100
    level: str  # 'Very High', 'High', 'Medium', 'Low'
    components: List[ConfidenceComponent]
    explanation: str
    supporting_evidence: List[str]
    conflicting_evidence: List[str]


class ConfidenceEngine:
    """
    Calculate confidence scores for root cause analysis.
    
    Combines evidence from:
    - Pattern matching
    - Historical similar cases
    - Sensor reading analysis
    - Documentation matches
    - Failure prediction scores
    """
    
    # Weights for different evidence sources
    SOURCE_WEIGHTS = {
        'pattern': 0.30,
        'historical': 0.25,
        'sensor': 0.20,
        'documentation': 0.15,
        'ai_prediction': 0.10
    }
    
    # Confidence thresholds
    CONFIDENCE_THRESHOLDS = {
        'very_high': 85,
        'high': 70,
        'medium': 50,
        'low': 0
    }
    
    def __init__(self):
        self.pattern_engine = get_pattern_engine()
    
    def calculate_confidence(
        self,
        root_cause: str,
        pattern_matches: Optional[List[tuple]] = None,
        similar_cases: Optional[List[SimilarCase]] = None,
        sensor_readings: Optional[Dict[str, float]] = None,
        anomaly_score: Optional[float] = None,
        failure_probability: Optional[float] = None,
        documentation_matches: Optional[List[str]] = None
    ) -> ConfidenceResult:
        """
        Calculate overall confidence for a root cause.
        
        Args:
            root_cause: Identified root cause
            pattern_matches: List of (pattern, score) tuples
            similar_cases: List of similar historical cases
            sensor_readings: Current sensor readings
            anomaly_score: Anomaly score from Isolation Forest
            failure_probability: Failure probability from prediction
            documentation_matches: List of matching document references
            
        Returns:
            ConfidenceResult with overall confidence and components
        """
        components = []
        
        # 1. Pattern matching contribution
        pattern_component = self._calculate_pattern_confidence(
            root_cause, pattern_matches
        )
        if pattern_component:
            components.append(pattern_component)
        
        # 2. Historical cases contribution
        historical_component = self._calculate_historical_confidence(
            root_cause, similar_cases
        )
        if historical_component:
            components.append(historical_component)
        
        # 3. Sensor readings contribution
        sensor_component = self._calculate_sensor_confidence(
            root_cause, sensor_readings
        )
        if sensor_component:
            components.append(sensor_component)
        
        # 4. Anomaly detection contribution
        if anomaly_score is not None:
            anomaly_component = self._calculate_anomaly_confidence(
                root_cause, anomaly_score
            )
            components.append(anomaly_component)
        
        # 5. Failure prediction contribution
        if failure_probability is not None:
            prediction_component = self._calculate_prediction_confidence(
                root_cause, failure_probability
            )
            components.append(prediction_component)
        
        # 6. Documentation contribution
        if documentation_matches:
            doc_component = self._calculate_documentation_confidence(
                root_cause, documentation_matches
            )
            components.append(doc_component)
        
        # Calculate weighted overall confidence
        overall = self._compute_weighted_confidence(components)
        
        # Determine level
        level = self._get_confidence_level(overall)
        
        # Generate explanation
        explanation = self._generate_explanation(root_cause, components, overall)
        
        # Collect evidence
        supporting = self._collect_supporting_evidence(components)
        conflicting = self._collect_conflicting_evidence(components)
        
        return ConfidenceResult(
            overall_confidence=overall,
            level=level,
            components=components,
            explanation=explanation,
            supporting_evidence=supporting,
            conflicting_evidence=conflicting
        )
    
    def _calculate_pattern_confidence(
        self,
        root_cause: str,
        pattern_matches: Optional[List[tuple]]
    ) -> Optional[ConfidenceComponent]:
        """Calculate confidence from pattern matching."""
        if not pattern_matches:
            return None
        
        evidence = []
        max_score = 0.0
        
        for pattern, score in pattern_matches:
            if pattern.probable_cause.lower() == root_cause.lower():
                evidence.append(f"Pattern match: {pattern.name} (score: {score:.2f})")
                max_score = max(max_score, score)
        
        if not evidence:
            return None
        
        return ConfidenceComponent(
            source='pattern',
            weight=self.SOURCE_WEIGHTS['pattern'],
            score=max_score,
            evidence=evidence,
            details=f"Best pattern match: {max_score:.2f}"
        )
    
    def _calculate_historical_confidence(
        self,
        root_cause: str,
        similar_cases: Optional[List[SimilarCase]]
    ) -> Optional[ConfidenceComponent]:
        """Calculate confidence from historical cases."""
        if not similar_cases:
            return None
        
        matching_cases = [
            c for c in similar_cases 
            if c.root_cause and c.root_cause.lower() == root_cause.lower()
        ]
        
        if not matching_cases:
            return None
        
        # Calculate confidence based on number and quality of matches
        avg_score = sum(c.match_score for c in matching_cases) / len(matching_cases)
        count_bonus = min(0.2, len(matching_cases) * 0.05)  # Up to 20% bonus for multiple matches
        
        evidence = [
            f"Historical case {c.case_id}: {c.issue[:50]}... (similarity: {c.match_score:.2f})"
            for c in matching_cases[:3]
        ]
        
        return ConfidenceComponent(
            source='historical',
            weight=self.SOURCE_WEIGHTS['historical'],
            score=min(1.0, avg_score + count_bonus),
            evidence=evidence,
            details=f"{len(matching_cases)} similar cases found"
        )
    
    def _calculate_sensor_confidence(
        self,
        root_cause: str,
        sensor_readings: Optional[Dict[str, float]]
    ) -> Optional[ConfidenceComponent]:
        """Calculate confidence from sensor readings."""
        if not sensor_readings:
            return None
        
        evidence = []
        matching_symptoms = 0
        
        cause_symptoms = {
            'bearing wear': ['vibration', 'temperature'],
            'bearing failure': ['vibration', 'temperature', 'current'],
            'pump blockage': ['pressure', 'current', 'vibration'],
            'motor overheating': ['temperature', 'current'],
            'mechanical load increase': ['current', 'rpm'],
            'shaft misalignment': ['vibration', 'rpm'],
            'lubrication failure': ['temperature', 'vibration'],
            'electrical fault': ['current', 'temperature'],
            'cooling system failure': ['temperature', 'current']
        }
        
        expected_symptoms = cause_symptoms.get(root_cause.lower(), [])
        
        for symptom in expected_symptoms:
            value = sensor_readings.get(symptom)
            if value is not None:
                # Check if value indicates the issue
                if symptom == 'vibration' and value > 2.5:
                    evidence.append(f"Elevated {symptom}: {value} mm/s")
                    matching_symptoms += 1
                elif symptom == 'temperature' and value > 85:
                    evidence.append(f"Elevated {symptom}: {value}°C")
                    matching_symptoms += 1
                elif symptom == 'current' and value > 25:
                    evidence.append(f"Elevated {symptom}: {value}A")
                    matching_symptoms += 1
                elif symptom == 'pressure' and value < 55:
                    evidence.append(f"Low {symptom}: {value} bar")
                    matching_symptoms += 1
        
        if not evidence:
            return None
        
        score = matching_symptoms / max(len(expected_symptoms), 1)
        
        return ConfidenceComponent(
            source='sensor',
            weight=self.SOURCE_WEIGHTS['sensor'],
            score=score,
            evidence=evidence,
            details=f"{matching_symptoms} sensor symptoms match expected pattern"
        )
    
    def _calculate_anomaly_confidence(
        self,
        root_cause: str,
        anomaly_score: float
    ) -> ConfidenceComponent:
        """Calculate confidence from anomaly detection."""
        # Lower anomaly score = more anomalous
        if anomaly_score < -0.5:
            score = 0.9
            evidence = ["Strong anomaly detected in sensor patterns"]
        elif anomaly_score < -0.2:
            score = 0.7
            evidence = ["Moderate anomaly detected"]
        else:
            score = 0.4
            evidence = ["Minor anomaly detected"]
        
        return ConfidenceComponent(
            source='ai_prediction',
            weight=self.SOURCE_WEIGHTS['ai_prediction'] * 2,  # Double weight for anomaly
            score=score,
            evidence=evidence,
            details=f"Anomaly score: {anomaly_score:.3f}"
        )
    
    def _calculate_prediction_confidence(
        self,
        root_cause: str,
        failure_probability: float
    ) -> ConfidenceComponent:
        """Calculate confidence from failure prediction."""
        # Higher failure probability supports root cause
        if failure_probability > 0.8:
            score = 0.9
            evidence = [f"High failure probability: {failure_probability*100:.0f}%"]
        elif failure_probability > 0.5:
            score = 0.7
            evidence = [f"Moderate failure probability: {failure_probability*100:.0f}%"]
        else:
            score = 0.5
            evidence = [f"Low failure probability: {failure_probability*100:.0f}%"]
        
        return ConfidenceComponent(
            source='ai_prediction',
            weight=self.SOURCE_WEIGHTS['ai_prediction'],
            score=score,
            evidence=evidence,
            details=f"Failure probability: {failure_probability:.2f}"
        )
    
    def _calculate_documentation_confidence(
        self,
        root_cause: str,
        documentation_matches: List[str]
    ) -> ConfidenceComponent:
        """Calculate confidence from documentation matches."""
        if not documentation_matches:
            return ConfidenceComponent(
                source='documentation',
                weight=self.SOURCE_WEIGHTS['documentation'],
                score=0.3,
                evidence=[],
                details="No documentation matches found"
            )
        
        evidence = [f"Document: {doc}" for doc in documentation_matches[:5]]
        
        return ConfidenceComponent(
            source='documentation',
            weight=self.SOURCE_WEIGHTS['documentation'],
            score=min(1.0, 0.5 + len(documentation_matches) * 0.1),
            evidence=evidence,
            details=f"{len(documentation_matches)} documents support this cause"
        )
    
    def _compute_weighted_confidence(
        self,
        components: List[ConfidenceComponent]
    ) -> float:
        """Compute weighted overall confidence score."""
        if not components:
            return 0.0
        
        total_weight = 0.0
        weighted_sum = 0.0
        
        for comp in components:
            weighted_sum += comp.weight * comp.score
            total_weight += comp.weight
        
        if total_weight == 0:
            return 0.0
        
        return (weighted_sum / total_weight) * 100
    
    def _get_confidence_level(self, confidence: float) -> str:
        """Get confidence level label."""
        if confidence >= self.CONFIDENCE_THRESHOLDS['very_high']:
            return "Very High"
        elif confidence >= self.CONFIDENCE_THRESHOLDS['high']:
            return "High"
        elif confidence >= self.CONFIDENCE_THRESHOLDS['medium']:
            return "Medium"
        else:
            return "Low"
    
    def _generate_explanation(
        self,
        root_cause: str,
        components: List[ConfidenceComponent],
        overall: float
    ) -> str:
        """Generate human-readable explanation."""
        explanations = [f"Root cause '{root_cause}' identified with {overall:.0f}% confidence"]
        
        # Add component explanations
        for comp in sorted(components, key=lambda x: x.score, reverse=True)[:3]:
            if comp.evidence:
                explanations.append(f"- {comp.source.title()}: {comp.score*100:.0f}% ({comp.details})")
        
        return " ".join(explanations)
    
    def _collect_supporting_evidence(
        self,
        components: List[ConfidenceComponent]
    ) -> List[str]:
        """Collect all supporting evidence."""
        evidence = []
        for comp in components:
            if comp.score >= 0.5:
                evidence.extend(comp.evidence)
        return evidence
    
    def _collect_conflicting_evidence(
        self,
        components: List[ConfidenceComponent]
    ) -> List[str]:
        """Collect any conflicting evidence."""
        evidence = []
        for comp in components:
            if comp.score < 0.3 and comp.evidence:
                evidence.append(f"Low {comp.source} support")
        return evidence


# Singleton instance
_confidence_engine: Optional[ConfidenceEngine] = None


def get_confidence_engine() -> ConfidenceEngine:
    """Get global confidence engine instance."""
    global _confidence_engine
    if _confidence_engine is None:
        _confidence_engine = ConfidenceEngine()
    return _confidence_engine