"""
Similar Case Retrieval System.

This module retrieves similar historical cases from maintenance logs
and failure reports to support root cause analysis.
"""
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from collections import defaultdict
import numpy as np

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    TfidfVectorizer = None


@dataclass
class SimilarCase:
    """Represents a similar historical case."""
    case_id: str
    case_type: str  # 'maintenance_log' or 'failure_report'
    equipment_name: str
    issue: str
    root_cause: Optional[str]
    action_taken: Optional[str]
    outcome: Optional[str]
    severity: str
    match_score: float
    date: datetime
    similarity_details: Dict[str, Any]


class SimilarCaseRetriever:
    """
    Retrieve similar historical cases based on current sensor readings
    and equipment context.
    """
    
    # Severity mapping for matching
    SEVERITY_WEIGHTS = {
        'critical': 4,
        'high': 3,
        'medium': 2,
        'low': 1
    }
    
    def __init__(self):
        self.vectorizer = TfidfVectorizer(
            max_features=100,
            stop_words='english',
            ngram_range=(1, 2)
        ) if SKLEARN_AVAILABLE else None
        self._maintenance_cache: List[Dict] = []
        self._failure_reports_cache: List[Dict] = []
    
    def find_similar_maintenance_logs(
        self,
        equipment_name: str,
        issue_description: str,
        severity: Optional[str] = None,
        limit: int = 5
    ) -> List[SimilarCase]:
        """
        Find similar maintenance logs based on issue description.
        
        Args:
            equipment_name: Name of equipment
            issue_description: Description of current issue
            severity: Target severity level
            limit: Maximum number of results
            
        Returns:
            List of similar maintenance log cases
        """
        # For demo purposes, generate synthetic similar cases
        # In production, this would query the database
        cases = self._generate_synthetic_maintenance_cases(equipment_name, limit)
        
        if issue_description and SKLEARN_AVAILABLE and self.vectorizer:
            # Use TF-IDF similarity
            cases = self._rank_by_text_similarity(cases, issue_description)
        
        return cases[:limit]
    
    def find_similar_failure_reports(
        self,
        equipment_name: str,
        issue_description: str,
        failure_type: Optional[str] = None,
        limit: int = 5
    ) -> List[SimilarCase]:
        """
        Find similar failure reports based on issue description.
        
        Args:
            equipment_name: Name of equipment
            issue_description: Description of current issue
            failure_type: Target failure type
            limit: Maximum number of results
            
        Returns:
            List of similar failure report cases
        """
        cases = self._generate_synthetic_failure_cases(equipment_name, limit)
        
        if issue_description and SKLEARN_AVAILABLE and self.vectorizer:
            cases = self._rank_by_text_similarity(cases, issue_description)
        
        return cases[:limit]
    
    def find_similar_cases_by_readings(
        self,
        equipment_name: str,
        temperature: Optional[float] = None,
        vibration: Optional[float] = None,
        current: Optional[float] = None,
        pressure: Optional[float] = None,
        rpm: Optional[float] = None,
        limit: int = 5
    ) -> List[SimilarCase]:
        """
        Find similar cases based on sensor readings.
        
        Args:
            equipment_name: Name of equipment
            sensor readings: Current sensor values
            limit: Maximum number of results
            
        Returns:
            List of similar cases with matching sensor patterns
        """
        readings = {
            'temperature': temperature,
            'vibration': vibration,
            'current': current,
            'pressure': pressure,
            'rpm': rpm
        }
        
        # Generate synthetic cases based on sensor similarity
        cases = self._generate_similar_cases_by_readings(equipment_name, readings, limit)
        
        return cases
    
    def get_all_similar_cases(
        self,
        equipment_name: str,
        issue_description: str,
        sensor_readings: Dict[str, float],
        severity: Optional[str] = None,
        limit: int = 5
    ) -> List[SimilarCase]:
        """
        Get all similar cases from multiple sources.
        
        Args:
            equipment_name: Name of equipment
            issue_description: Issue description
            sensor_readings: Current sensor readings
            severity: Target severity
            limit: Maximum per category
            
        Returns:
            Combined list of similar cases sorted by relevance
        """
        all_cases = []
        
        # Get from maintenance logs
        maintenance_cases = self.find_similar_maintenance_logs(
            equipment_name, issue_description, severity, limit
        )
        all_cases.extend(maintenance_cases)
        
        # Get from failure reports
        failure_cases = self.find_similar_failure_reports(
            equipment_name, issue_description, None, limit
        )
        all_cases.extend(failure_cases)
        
        # Get by sensor readings
        reading_cases = self.find_similar_cases_by_readings(
            equipment_name, 
            sensor_readings.get('temperature'),
            sensor_readings.get('vibration'),
            sensor_readings.get('current'),
            sensor_readings.get('pressure'),
            sensor_readings.get('rpm'),
            limit
        )
        all_cases.extend(reading_cases)
        
        # Remove duplicates and sort by match score
        seen_ids = set()
        unique_cases = []
        for case in all_cases:
            if case.case_id not in seen_ids:
                seen_ids.add(case.case_id)
                unique_cases.append(case)
        
        unique_cases.sort(key=lambda x: x.match_score, reverse=True)
        
        return unique_cases[:limit * 3]
    
    def _rank_by_text_similarity(
        self,
        cases: List[SimilarCase],
        query: str
    ) -> List[SimilarCase]:
        """Rank cases by text similarity to query."""
        if not cases or not query:
            return cases
        
        try:
            texts = [query] + [c.issue for c in cases]
            tfidf_matrix = self.vectorizer.fit_transform(texts)
            
            similarities = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:])[0]
            
            for i, case in enumerate(cases):
                case.match_score = max(case.match_score, float(similarities[i]))
            
            cases.sort(key=lambda x: x.match_score, reverse=True)
        except Exception:
            pass
        
        return cases
    
    def _generate_synthetic_maintenance_cases(
        self,
        equipment_name: str,
        limit: int
    ) -> List[SimilarCase]:
        """Generate synthetic maintenance cases for demo."""
        cases = []
        base_issues = [
            ("Excessive vibration detected during operation", "Bearing replacement", "Resolved"),
            ("Equipment overheating, cooling system checked", "Cooling fan maintenance", "Resolved"),
            ("Unusual noise from motor assembly", "Bearing inspection and lubrication", "Resolved"),
            ("Current fluctuations observed", "Electrical connection check", "Resolved"),
            ("Pressure drop in hydraulic system", "Filter replacement", "Resolved")
        ]
        
        for i, (issue, action, outcome) in enumerate(base_issues[:limit]):
            days_ago = (i + 1) * 15
            cases.append(SimilarCase(
                case_id=f"ML-{1000 + i}",
                case_type="maintenance_log",
                equipment_name=equipment_name,
                issue=issue,
                root_cause=self._infer_cause(issue),
                action_taken=action,
                outcome=outcome,
                severity="high" if i < 2 else "medium",
                match_score=0.85 - (i * 0.1),
                date=datetime.now() - timedelta(days=days_ago),
                similarity_details={
                    "matched_terms": ["vibration", "bearing"] if "vibration" in issue.lower() else ["overheating"],
                    "sensor_similarity": 0.9 - (i * 0.1)
                }
            ))
        
        return cases
    
    def _generate_synthetic_failure_cases(
        self,
        equipment_name: str,
        limit: int
    ) -> List[SimilarCase]:
        """Generate synthetic failure cases for demo."""
        cases = []
        base_failures = [
            ("Motor bearing failure - complete replacement required", "Bearing Failure", "Bearing replaced"),
            ("Cooling system malfunction caused overheating", "Cooling Failure", "Fan motor replaced"),
            ("Pump blockage due to debris accumulation", "Blockage", "Pump cleaned and filters replaced"),
            ("Electrical insulation failure in motor windings", "Electrical Fault", "Motor rewound"),
            ("Shaft misalignment causing excessive vibration", "Misalignment", "Alignment corrected")
        ]
        
        for i, (issue, cause, resolution) in enumerate(base_failures[:limit]):
            days_ago = (i + 1) * 20
            cases.append(SimilarCase(
                case_id=f"FR-{2000 + i}",
                case_type="failure_report",
                equipment_name=equipment_name,
                issue=issue,
                root_cause=cause,
                action_taken=resolution,
                outcome="Equipment restored to operation",
                severity="critical" if i < 2 else "high",
                match_score=0.88 - (i * 0.12),
                date=datetime.now() - timedelta(days=days_ago),
                similarity_details={
                    "matched_pattern": cause,
                    "sensor_similarity": 0.85 - (i * 0.1)
                }
            ))
        
        return cases
    
    def _generate_similar_cases_by_readings(
        self,
        equipment_name: str,
        readings: Dict[str, Optional[float]],
        limit: int
    ) -> List[SimilarCase]:
        """Generate cases based on sensor reading similarity."""
        cases = []
        
        # Simulate cases with similar readings
        if readings.get('vibration', 0) and readings['vibration'] > 2.5:
            cases.append(SimilarCase(
                case_id="CASE-VIB-001",
                case_type="failure_report",
                equipment_name=equipment_name,
                issue=f"High vibration reading: {readings['vibration']} mm/s",
                root_cause="Bearing Wear",
                action_taken="Bearing replacement",
                outcome="Resolved",
                severity="high",
                match_score=0.92,
                date=datetime.now() - timedelta(days=30),
                similarity_details={"sensor_type": "vibration", "value": readings['vibration']}
            ))
        
        if readings.get('temperature', 0) and readings['temperature'] > 90:
            cases.append(SimilarCase(
                case_id="CASE-TEMP-001",
                case_type="maintenance_log",
                equipment_name=equipment_name,
                issue=f"Temperature exceeded threshold: {readings['temperature']}°C",
                root_cause="Cooling System Failure",
                action_taken="Cooling fan inspection and cleaning",
                outcome="Resolved",
                severity="high",
                match_score=0.89,
                date=datetime.now() - timedelta(days=45),
                similarity_details={"sensor_type": "temperature", "value": readings['temperature']}
            ))
        
        if readings.get('current', 0) and readings['current'] > 28:
            cases.append(SimilarCase(
                case_id="CASE-CURR-001",
                case_type="failure_report",
                equipment_name=equipment_name,
                issue=f"High current draw: {readings['current']}A",
                root_cause="Motor Overload",
                action_taken="Load analysis and motor inspection",
                outcome="Load reduced",
                severity="medium",
                match_score=0.85,
                date=datetime.now() - timedelta(days=60),
                similarity_details={"sensor_type": "current", "value": readings['current']}
            ))
        
        return cases[:limit]
    
    def _infer_cause(self, issue: str) -> str:
        """Infer root cause from issue description."""
        issue_lower = issue.lower()
        
        if 'vibration' in issue_lower:
            return 'Bearing Wear'
        elif 'overheat' in issue_lower:
            return 'Cooling System Failure'
        elif 'current' in issue_lower:
            return 'Electrical Issue'
        elif 'pressure' in issue_lower:
            return 'Hydraulic Problem'
        else:
            return 'Mechanical Failure'


# Singleton instance
_similar_case_retriever: Optional[SimilarCaseRetriever] = None


def get_similar_case_retriever() -> SimilarCaseRetriever:
    """Get global similar case retriever instance."""
    global _similar_case_retriever
    if _similar_case_retriever is None:
        _similar_case_retriever = SimilarCaseRetriever()
    return _similar_case_retriever