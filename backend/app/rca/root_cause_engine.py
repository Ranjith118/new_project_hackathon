"""
Root Cause Analysis Engine.

This module provides the main RCA functionality combining
pattern matching, historical cases, and AI analysis.
"""
import uuid
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime

from app.rca.pattern_engine import FailurePattern, get_pattern_engine
from app.rca.similar_case_retriever import SimilarCase, get_similar_case_retriever
from app.rca.confidence_engine import ConfidenceResult, get_confidence_engine


@dataclass
class RootCause:
    """Identified root cause with supporting information."""
    cause: str
    confidence: float
    confidence_level: str
    evidence: List[str]
    recommended_actions: List[str]
    explanation: str
    pattern_matched: Optional[str] = None


@dataclass
class AlternativeCause:
    """Alternative cause with lower confidence."""
    cause: str
    confidence: float
    reasoning: str


@dataclass
class RCAResult:
    """Complete RCA result."""
    analysis_id: str
    equipment_name: str
    timestamp: datetime
    sensor_readings: Dict[str, float]
    primary_cause: RootCause
    secondary_causes: List[AlternativeCause]
    contributing_factors: List[str]
    similar_cases: List[SimilarCase]
    confidence_result: ConfidenceResult
    reasoning_path: List[str]
    recommended_actions: List[str]
    investigation_steps: List[str]


class RootCauseEngine:
    """
    Main Root Cause Analysis engine.
    
    Combines:
    - Pattern matching
    - Historical case retrieval
    - Confidence scoring
    - Multi-cause analysis
    """
    
    def __init__(self):
        self.pattern_engine = get_pattern_engine()
        self.similar_case_retriever = get_similar_case_retriever()
        self.confidence_engine = get_confidence_engine()
    
    def analyze(
        self,
        equipment_name: str,
        temperature: Optional[float] = None,
        vibration: Optional[float] = None,
        current: Optional[float] = None,
        pressure: Optional[float] = None,
        rpm: Optional[float] = None,
        issue_description: Optional[str] = None,
        severity: Optional[str] = None,
        anomaly_score: Optional[float] = None,
        failure_probability: Optional[float] = None
    ) -> RCAResult:
        """
        Perform comprehensive root cause analysis.
        
        Args:
            equipment_name: Name of equipment
            sensor readings: Current sensor values
            issue_description: Optional text description of issue
            severity: Issue severity level
            anomaly_score: Optional anomaly detection score
            failure_probability: Optional failure prediction score
            
        Returns:
            RCAResult with complete analysis
        """
        analysis_id = str(uuid.uuid4())
        sensor_readings = {
            'temperature': temperature,
            'vibration': vibration,
            'current': current,
            'pressure': pressure,
            'rpm': rpm
        }
        
        # Step 1: Pattern matching
        pattern_matches = self.pattern_engine.match_patterns(
            temperature=temperature,
            vibration=vibration,
            current=current,
            pressure=pressure,
            rpm=rpm,
            min_confidence=0.3
        )
        
        # Step 2: Similar case retrieval
        similar_cases = self.similar_case_retriever.get_all_similar_cases(
            equipment_name=equipment_name,
            issue_description=issue_description or "",
            sensor_readings=sensor_readings,
            severity=severity,
            limit=5
        )
        
        # Step 3: Identify primary cause from patterns
        primary_cause_data = self._identify_primary_cause(
            pattern_matches, similar_cases, sensor_readings
        )
        
        # Step 4: Calculate confidence
        confidence_result = self.confidence_engine.calculate_confidence(
            root_cause=primary_cause_data['cause'],
            pattern_matches=pattern_matches,
            similar_cases=similar_cases,
            sensor_readings=sensor_readings,
            anomaly_score=anomaly_score,
            failure_probability=failure_probability
        )
        
        # Step 5: Identify secondary causes
        secondary_causes = self._identify_alternative_causes(
            primary_cause_data['cause'],
            pattern_matches,
            sensor_readings
        )
        
        # Step 6: Identify contributing factors
        contributing_factors = self._identify_contributing_factors(
            primary_cause_data['cause'],
            sensor_readings
        )
        
        # Step 7: Generate recommended actions
        recommended_actions = self._generate_recommended_actions(
            primary_cause_data['cause'],
            pattern_matches,
            secondary_causes
        )
        
        # Step 8: Generate reasoning path
        reasoning_path = self._generate_reasoning_path(
            primary_cause_data,
            sensor_readings,
            pattern_matches,
            similar_cases
        )
        
        # Step 9: Generate investigation steps
        investigation_steps = self._generate_investigation_steps(
            primary_cause_data['cause'],
            sensor_readings
        )
        
        return RCAResult(
            analysis_id=analysis_id,
            equipment_name=equipment_name,
            timestamp=datetime.now(),
            sensor_readings=sensor_readings,
            primary_cause=RootCause(
                cause=primary_cause_data['cause'],
                confidence=confidence_result.overall_confidence,
                confidence_level=confidence_result.level,
                evidence=confidence_result.supporting_evidence,
                recommended_actions=recommended_actions,
                explanation=confidence_result.explanation,
                pattern_matched=primary_cause_data.get('pattern_name')
            ),
            secondary_causes=secondary_causes,
            contributing_factors=contributing_factors,
            similar_cases=similar_cases,
            confidence_result=confidence_result,
            reasoning_path=reasoning_path,
            recommended_actions=recommended_actions,
            investigation_steps=investigation_steps
        )
    
    def _identify_primary_cause(
        self,
        pattern_matches: List[tuple],
        similar_cases: List[SimilarCase],
        sensor_readings: Dict[str, float]
    ) -> Dict[str, Any]:
        """Identify primary root cause from available evidence."""
        
        # Check pattern matches first
        if pattern_matches:
            best_pattern, score = pattern_matches[0]
            return {
                'cause': best_pattern.probable_cause,
                'pattern_name': best_pattern.name,
                'source': 'pattern',
                'score': score
            }
        
        # Check historical cases
        if similar_cases:
            # Group by root cause
            cause_scores = {}
            for case in similar_cases:
                if case.root_cause:
                    if case.root_cause not in cause_scores:
                        cause_scores[case.root_cause] = []
                    cause_scores[case.root_cause].append(case.match_score)
            
            if cause_scores:
                best_cause = max(cause_scores.keys(), 
                               key=lambda c: sum(cause_scores[c]) / len(cause_scores[c]))
                return {
                    'cause': best_cause,
                    'source': 'historical',
                    'score': sum(cause_scores[best_cause]) / len(cause_scores[best_cause])
                }
        
        # Fall back to sensor-based inference
        inferred = self._infer_from_sensors(sensor_readings)
        return inferred
    
    def _infer_from_sensors(
        self,
        sensor_readings: Dict[str, float]
    ) -> Dict[str, Any]:
        """Infer root cause from sensor readings."""
        
        # Check each sensor against thresholds
        issues = []
        
        if sensor_readings.get('vibration', 0) > 3.0:
            issues.append(('Bearing Wear', 0.8))
        elif sensor_readings.get('vibration', 0) > 2.5:
            issues.append(('Bearing Wear', 0.6))
        
        if sensor_readings.get('temperature', 0) > 100:
            issues.append(('Cooling System Failure', 0.85))
        elif sensor_readings.get('temperature', 0) > 90:
            issues.append(('Motor Overheating', 0.7))
        
        if sensor_readings.get('pressure', 0) and sensor_readings['pressure'] < 50:
            issues.append(('Pump Blockage', 0.75))
        
        if sensor_readings.get('current', 0) and sensor_readings['current'] > 30:
            issues.append(('Electrical Fault', 0.7))
        
        if issues:
            # Return highest confidence issue
            issues.sort(key=lambda x: x[1], reverse=True)
            return {
                'cause': issues[0][0],
                'source': 'sensor',
                'score': issues[0][1]
            }
        
        return {
            'cause': 'Unknown',
            'source': 'sensor',
            'score': 0.0
        }
    
    def _identify_alternative_causes(
        self,
        primary_cause: str,
        pattern_matches: List[tuple],
        sensor_readings: Dict[str, float]
    ) -> List[AlternativeCause]:
        """Identify alternative possible causes."""
        alternatives = []
        
        # Check other pattern matches
        for pattern, score in pattern_matches[1:4]:
            if pattern.probable_cause.lower() != primary_cause.lower():
                alternatives.append(AlternativeCause(
                    cause=pattern.probable_cause,
                    confidence=score * 100,
                    reasoning=f"Pattern match: {pattern.name}"
                ))
        
        # Sensor-based alternatives
        if primary_cause.lower() != 'cooling system failure' and sensor_readings.get('temperature', 0) > 85:
            alternatives.append(AlternativeCause(
                cause='Cooling System Failure',
                confidence=50,
                reasoning='Elevated temperature detected'
            ))
        
        if primary_cause.lower() != 'bearing wear' and sensor_readings.get('vibration', 0) > 2.0:
            alternatives.append(AlternativeCause(
                cause='Bearing Wear',
                confidence=45,
                reasoning='Elevated vibration detected'
            ))
        
        # Sort by confidence
        alternatives.sort(key=lambda x: x.confidence, reverse=True)
        
        return alternatives[:3]
    
    def _identify_contributing_factors(
        self,
        primary_cause: str,
        sensor_readings: Dict[str, float]
    ) -> List[str]:
        """Identify contributing factors."""
        factors = []
        
        cause_lower = primary_cause.lower()
        
        if 'bearing' in cause_lower:
            if sensor_readings.get('temperature', 0) > 80:
                factors.append('Elevated operating temperature')
            if sensor_readings.get('vibration', 0) > 2.0:
                factors.append('High load operation')
            factors.append('Inadequate lubrication')
        
        elif 'overheat' in cause_lower or 'cooling' in cause_lower:
            if sensor_readings.get('current', 0) and sensor_readings['current'] > 25:
                factors.append('High electrical load')
            factors.append('Insufficient cooling')
        
        elif 'blockage' in cause_lower or 'pump' in cause_lower:
            if sensor_readings.get('current', 0) and sensor_readings['current'] > 25:
                factors.append('Increased system resistance')
        
        elif 'electrical' in cause_lower:
            if sensor_readings.get('rpm', 0) and sensor_readings['rpm'] < 1300:
                factors.append('Voltage fluctuations')
        
        if not factors:
            factors.append('Normal operating conditions with accumulated wear')
        
        return factors
    
    def _generate_recommended_actions(
        self,
        primary_cause: str,
        pattern_matches: List[tuple],
        secondary_causes: List[AlternativeCause]
    ) -> List[str]:
        """Generate recommended actions."""
        actions = []
        
        # Get actions from matching pattern
        for pattern, score in pattern_matches:
            if pattern.probable_cause.lower() == primary_cause.lower():
                actions.extend(pattern.recommended_actions)
                break
        
        # Add generic actions if no specific ones
        if not actions:
            actions = [
                f"Inspect equipment for {primary_cause}",
                "Document findings",
                "Schedule maintenance if needed"
            ]
        
        return list(dict.fromkeys(actions))[:5]  # Remove duplicates, limit to 5
    
    def _generate_reasoning_path(
        self,
        primary_cause_data: Dict[str, Any],
        sensor_readings: Dict[str, float],
        pattern_matches: List[tuple],
        similar_cases: List[SimilarCase]
    ) -> List[str]:
        """Generate step-by-step reasoning path."""
        path = []
        
        # Step 1: Sensor analysis
        abnormal_readings = []
        if sensor_readings.get('temperature', 0) and sensor_readings['temperature'] > 85:
            abnormal_readings.append(f"Temperature: {sensor_readings['temperature']}°C (elevated)")
        if sensor_readings.get('vibration', 0) and sensor_readings['vibration'] > 2.0:
            abnormal_readings.append(f"Vibration: {sensor_readings['vibration']} mm/s (elevated)")
        if sensor_readings.get('current', 0) and sensor_readings['current'] > 25:
            abnormal_readings.append(f"Current: {sensor_readings['current']}A (elevated)")
        
        if abnormal_readings:
            path.append(f"1. Sensor Analysis: Detected {len(abnormal_readings)} abnormal readings")
            for reading in abnormal_readings[:3]:
                path.append(f"   - {reading}")
        
        # Step 2: Pattern matching
        if pattern_matches:
            path.append(f"2. Pattern Matching: Found {len(pattern_matches)} matching patterns")
            path.append(f"   - Primary match: {pattern_matches[0][0].name} ({pattern_matches[0][1]*100:.0f}% match)")
        
        # Step 3: Historical cases
        if similar_cases:
            path.append(f"3. Historical Analysis: Found {len(similar_cases)} similar cases")
            matching = [c for c in similar_cases if c.root_cause and c.root_cause.lower() == primary_cause_data['cause'].lower()]
            if matching:
                path.append(f"   - {len(matching)} cases with same root cause")
        
        # Step 4: Conclusion
        path.append(f"4. Conclusion: Root cause identified as '{primary_cause_data['cause']}'")
        path.append(f"   - Confidence: {primary_cause_data.get('score', 0)*100:.0f}%")
        
        return path
    
    def _generate_investigation_steps(
        self,
        primary_cause: str,
        sensor_readings: Dict[str, float]
    ) -> List[str]:
        """Generate investigation steps for the root cause."""
        steps = []
        
        cause_lower = primary_cause.lower()
        
        if 'bearing' in cause_lower:
            steps = [
                "1. Check bearing temperature and compare to baseline",
                "2. Measure vibration amplitude at bearing housing",
                "3. Inspect bearing for visible wear or damage",
                "4. Check lubricant condition and level",
                "5. Verify shaft alignment",
                "6. Check for unusual noise or heat"
            ]
        elif 'overheat' in cause_lower or 'cooling' in cause_lower:
            steps = [
                "1. Check cooling fan operation",
                "2. Inspect heat exchanger for blockages",
                "3. Measure ambient temperature",
                "4. Check coolant flow rate",
                "5. Verify ventilation system",
                "6. Check for excessive load"
            ]
        elif 'blockage' in cause_lower or 'pump' in cause_lower:
            steps = [
                "1. Check inlet strainer for debris",
                "2. Inspect pump impeller",
                "3. Measure discharge pressure",
                "4. Check for air leaks in suction line",
                "5. Verify pipeline for obstructions",
                "6. Check system for deadheading"
            ]
        elif 'electrical' in cause_lower:
            steps = [
                "1. Check motor windings for hot spots",
                "2. Measure insulation resistance",
                "3. Inspect electrical connections",
                "4. Check voltage and current waveforms",
                "5. Verify grounding",
                "6. Test motor bearings electrically"
            ]
        else:
            steps = [
                "1. Review sensor data for anomalies",
                "2. Check maintenance history",
                "3. Inspect equipment for visible issues",
                "4. Compare to similar equipment",
                "5. Consult equipment manual",
                "6. Document all findings"
            ]
        
        return steps


# Singleton instance
_root_cause_engine: Optional[RootCauseEngine] = None


def get_root_cause_engine() -> RootCauseEngine:
    """Get global root cause engine instance."""
    global _root_cause_engine
    if _root_cause_engine is None:
        _root_cause_engine = RootCauseEngine()
    return _root_cause_engine