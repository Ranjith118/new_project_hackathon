"""
Feedback Collection Engine.

This module handles collection and management of engineer feedback
on system recommendations and predictions.
"""
import uuid
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum


class FeedbackType(Enum):
    """Types of feedback."""
    RECOMMENDATION_ACCEPTED = "recommendation_accepted"
    RECOMMENDATION_REJECTED = "recommendation_rejected"
    ROOT_CAUSE_CORRECT = "root_cause_correct"
    ROOT_CAUSE_INCORRECT = "root_cause_incorrect"
    PREDICTION_ACCURATE = "prediction_accurate"
    PREDICTION_INACCURATE = "prediction_inaccurate"
    ANOMALY_CONFIRMED = "anomaly_confirmed"
    ANOMALY_FALSE_ALARM = "anomaly_false_alarm"
    RUL_ACCURATE = "rul_accurate"
    RUL_INACCURATE = "rul_inaccurate"


class OutcomeType(Enum):
    """Maintenance outcome types."""
    SUCCESS = "success"
    PARTIAL_SUCCESS = "partial_success"
    FAILURE = "failure"
    FOLLOW_UP_REQUIRED = "follow_up_required"


@dataclass
class EngineerFeedback:
    """Engineer feedback on system recommendations."""
    feedback_id: str
    equipment_id: str
    equipment_name: str
    module_name: str  # rca, recommendation, prediction, anomaly
    recommendation: str
    feedback_type: FeedbackType
    rating: int  # 1-5 stars
    comments: str
    engineer_name: str
    timestamp: datetime = field(default_factory=datetime.now)
    resolved: bool = False


@dataclass
class MaintenanceOutcome:
    """Actual maintenance outcome tracking."""
    outcome_id: str
    equipment_id: str
    equipment_name: str
    predicted_cause: str
    actual_cause: str
    predicted_action: str
    actual_action: str
    outcome: OutcomeType
    predicted_downtime_hours: float
    actual_downtime_hours: float
    predicted_cost: float
    actual_cost: float
    spare_parts_used: List[str]
    success: bool
    notes: str
    engineer_name: str
    completed_at: datetime
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class FeedbackSummary:
    """Summary of feedback for a module."""
    module_name: str
    total_feedback: int
    positive_count: int
    negative_count: int
    acceptance_rate: float
    average_rating: float
    top_positive: List[str]
    top_negative: List[str]


class FeedbackEngine:
    """
    Collect and manage engineer feedback.
    
    Features:
    - Feedback collection
    - Feedback categorization
    - Outcome tracking
    - Summary generation
    """
    
    # Default feedback data for demonstration
    DEFAULT_FEEDBACK = [
        {
            'equipment_id': 'rolling_mill_motor',
            'equipment_name': 'Rolling Mill Motor',
            'module_name': 'recommendation',
            'recommendation': 'Replace bearing B6205 within 7 days',
            'feedback_type': 'recommendation_accepted',
            'rating': 5,
            'comments': 'Bearing was indeed worn. Good prediction.',
            'engineer_name': 'John Smith'
        },
        {
            'equipment_id': 'blast_furnace_fan',
            'equipment_name': 'Blast Furnace Fan',
            'module_name': 'rca',
            'recommendation': 'Bearing Failure due to lubrication issues',
            'feedback_type': 'root_cause_correct',
            'rating': 5,
            'comments': 'Correct diagnosis. Lubrication system needed repair.',
            'engineer_name': 'Sarah Johnson'
        },
        {
            'equipment_id': 'main_compressor',
            'equipment_name': 'Main Compressor',
            'module_name': 'prediction',
            'recommendation': 'Failure probability 85%, RUL 10 days',
            'feedback_type': 'prediction_accurate',
            'rating': 4,
            'comments': 'Accurate prediction. Scheduled maintenance accordingly.',
            'engineer_name': 'Mike Brown'
        },
        {
            'equipment_id': 'cooling_pump_a',
            'equipment_name': 'Cooling Pump A',
            'module_name': 'recommendation',
            'recommendation': 'Replace mechanical seal',
            'feedback_type': 'recommendation_rejected',
            'rating': 2,
            'comments': 'Issue was actually a blockage, not seal failure.',
            'engineer_name': 'Lisa Davis'
        },
        {
            'equipment_id': 'slab_reheating_furnace',
            'equipment_name': 'Slab Reheating Furnace',
            'module_name': 'anomaly',
            'recommendation': 'Temperature anomaly detected',
            'feedback_type': 'anomaly_confirmed',
            'rating': 4,
            'comments': 'Confirmed. Found debris in burner.',
            'engineer_name': 'Tom Wilson'
        }
    ]
    
    DEFAULT_OUTCOMES = [
        {
            'equipment_id': 'rolling_mill_motor',
            'equipment_name': 'Rolling Mill Motor',
            'predicted_cause': 'Bearing Wear',
            'actual_cause': 'Bearing Wear',
            'predicted_action': 'Replace Bearing',
            'actual_action': 'Replaced Bearing B6205',
            'outcome': 'success',
            'predicted_downtime_hours': 4.0,
            'actual_downtime_hours': 3.5,
            'predicted_cost': 475000.0,     # ₹4,75,000 (was $5,000 × 95)
            'actual_cost': 456000.0,         # ₹4,56,000 (was $4,800 × 95)
            'spare_parts_used': ['Bearing B6205', 'Lubricant'],
            'success': True,
            'notes': 'Smooth repair, no complications.',
            'engineer_name': 'John Smith',
            'completed_at': datetime.now() - timedelta(days=2)
        },
        {
            'equipment_id': 'main_compressor',
            'equipment_name': 'Main Compressor',
            'predicted_cause': 'Bearing Failure',
            'actual_cause': 'Piston Ring Wear',
            'predicted_action': 'Replace Bearing',
            'actual_action': 'Replaced Piston Rings',
            'outcome': 'partial_success',
            'predicted_downtime_hours': 6.0,
            'actual_downtime_hours': 8.0,
            'predicted_cost': 570000.0,     # ₹5,70,000 (was $6,000 × 95)
            'actual_cost': 712500.0,         # ₹7,12,500 (was $7,500 × 95)
            'spare_parts_used': ['Piston Rings', 'Gaskets'],
            'success': False,
            'notes': 'Initial prediction was incorrect. Additional work needed.',
            'engineer_name': 'Sarah Johnson',
            'completed_at': datetime.now() - timedelta(days=5)
        },
        {
            'equipment_id': 'cooling_pump_a',
            'equipment_name': 'Cooling Pump A',
            'predicted_cause': 'Seal Failure',
            'actual_cause': 'Pump Blockage',
            'predicted_action': 'Replace Mechanical Seal',
            'actual_action': 'Cleared Blockage, Replaced Gaskets',
            'outcome': 'success',
            'predicted_downtime_hours': 3.0,
            'actual_downtime_hours': 2.5,
            'predicted_cost': 332500.0,     # ₹3,32,500 (was $3,500 × 95)
            'actual_cost': 266000.0,         # ₹2,66,000 (was $2,800 × 95)
            'spare_parts_used': ['Gaskets', 'O-Rings'],
            'success': True,
            'notes': 'Different root cause but successful repair.',
            'engineer_name': 'Mike Brown',
            'completed_at': datetime.now() - timedelta(days=7)
        }
    ]
    
    def __init__(self):
        self.feedback_list: List[EngineerFeedback] = []
        self.outcomes: List[MaintenanceOutcome] = []
        self._load_default_data()
    
    def _load_default_data(self):
        """Load default feedback and outcomes."""
        for fb_data in self.DEFAULT_FEEDBACK:
            feedback = EngineerFeedback(
                feedback_id=str(uuid.uuid4()),
                equipment_id=fb_data['equipment_id'],
                equipment_name=fb_data['equipment_name'],
                module_name=fb_data['module_name'],
                recommendation=fb_data['recommendation'],
                feedback_type=FeedbackType(fb_data['feedback_type']),
                rating=fb_data['rating'],
                comments=fb_data['comments'],
                engineer_name=fb_data['engineer_name'],
                timestamp=datetime.now() - timedelta(days=fb_data.get('days_ago', 0))
            )
            self.feedback_list.append(feedback)
        
        for oc_data in self.DEFAULT_OUTCOMES:
            outcome = MaintenanceOutcome(
                outcome_id=str(uuid.uuid4()),
                equipment_id=oc_data['equipment_id'],
                equipment_name=oc_data['equipment_name'],
                predicted_cause=oc_data['predicted_cause'],
                actual_cause=oc_data['actual_cause'],
                predicted_action=oc_data['predicted_action'],
                actual_action=oc_data['actual_action'],
                outcome=OutcomeType(oc_data['outcome']),
                predicted_downtime_hours=oc_data['predicted_downtime_hours'],
                actual_downtime_hours=oc_data['actual_downtime_hours'],
                predicted_cost=oc_data['predicted_cost'],
                actual_cost=oc_data['actual_cost'],
                spare_parts_used=oc_data['spare_parts_used'],
                success=oc_data['success'],
                notes=oc_data['notes'],
                engineer_name=oc_data['engineer_name'],
                completed_at=oc_data['completed_at']
            )
            self.outcomes.append(outcome)
    
    def add_feedback(
        self,
        equipment_id: str,
        equipment_name: str,
        module_name: str,
        recommendation: str,
        feedback_type: str,
        rating: int,
        comments: str,
        engineer_name: str
    ) -> EngineerFeedback:
        """Add new feedback."""
        feedback = EngineerFeedback(
            feedback_id=str(uuid.uuid4()),
            equipment_id=equipment_id,
            equipment_name=equipment_name,
            module_name=module_name,
            recommendation=recommendation,
            feedback_type=FeedbackType(feedback_type),
            rating=rating,
            comments=comments,
            engineer_name=engineer_name
        )
        self.feedback_list.append(feedback)
        return feedback
    
    def add_outcome(
        self,
        equipment_id: str,
        equipment_name: str,
        predicted_cause: str,
        actual_cause: str,
        predicted_action: str,
        actual_action: str,
        outcome: str,
        predicted_downtime: float,
        actual_downtime: float,
        predicted_cost: float,
        actual_cost: float,
        spare_parts: List[str],
        success: bool,
        notes: str,
        engineer_name: str,
        completed_at: datetime
    ) -> MaintenanceOutcome:
        """Add maintenance outcome."""
        maintenance_outcome = MaintenanceOutcome(
            outcome_id=str(uuid.uuid4()),
            equipment_id=equipment_id,
            equipment_name=equipment_name,
            predicted_cause=predicted_cause,
            actual_cause=actual_cause,
            predicted_action=predicted_action,
            actual_action=actual_action,
            outcome=OutcomeType(outcome),
            predicted_downtime_hours=predicted_downtime,
            actual_downtime_hours=actual_downtime,
            predicted_cost=predicted_cost,
            actual_cost=actual_cost,
            spare_parts_used=spare_parts,
            success=success,
            notes=notes,
            engineer_name=engineer_name,
            completed_at=completed_at
        )
        self.outcomes.append(maintenance_outcome)
        return maintenance_outcome
    
    def get_feedback_by_module(self, module_name: str) -> List[EngineerFeedback]:
        """Get feedback for a specific module."""
        return [f for f in self.feedback_list if f.module_name == module_name]
    
    def get_recent_feedback(self, days: int = 30) -> List[EngineerFeedback]:
        """Get feedback from last N days."""
        cutoff = datetime.now() - timedelta(days=days)
        return [f for f in self.feedback_list if f.timestamp >= cutoff]
    
    def get_recent_outcomes(self, days: int = 30) -> List[MaintenanceOutcome]:
        """Get outcomes from last N days."""
        cutoff = datetime.now() - timedelta(days=days)
        return [o for o in self.outcomes if o.completed_at >= cutoff]
    
    def get_module_summary(self, module_name: str) -> FeedbackSummary:
        """Get summary of feedback for a module."""
        module_feedback = self.get_feedback_by_module(module_name)
        
        positive_types = [
            FeedbackType.RECOMMENDATION_ACCEPTED,
            FeedbackType.ROOT_CAUSE_CORRECT,
            FeedbackType.PREDICTION_ACCURATE,
            FeedbackType.ANOMALY_CONFIRMED,
            FeedbackType.RUL_ACCURATE
        ]
        
        positive = [f for f in module_feedback if f.feedback_type in positive_types]
        negative = [f for f in module_feedback if f.feedback_type not in positive_types]
        
        accepted = [f for f in module_feedback if f.feedback_type == FeedbackType.RECOMMENDATION_ACCEPTED]
        total_recs = accepted + [f for f in module_feedback if f.feedback_type == FeedbackType.RECOMMENDATION_REJECTED]
        
        acceptance_rate = len(accepted) / len(total_recs) if total_recs else 0.0
        avg_rating = sum(f.rating for f in module_feedback) / len(module_feedback) if module_feedback else 0.0
        
        return FeedbackSummary(
            module_name=module_name,
            total_feedback=len(module_feedback),
            positive_count=len(positive),
            negative_count=len(negative),
            acceptance_rate=acceptance_rate,
            average_rating=avg_rating,
            top_positive=[f.recommendation for f in positive[:3]],
            top_negative=[f.recommendation for f in negative[:3]]
        )
    
    def get_all_summaries(self) -> List[FeedbackSummary]:
        """Get summaries for all modules."""
        modules = ['rca', 'recommendation', 'prediction', 'anomaly']
        return [self.get_module_summary(m) for m in modules]
    
    def get_outcome_summary(self) -> Dict[str, Any]:
        """Get summary of maintenance outcomes."""
        total = len(self.outcomes)
        success_count = sum(1 for o in self.outcomes if o.success)
        partial = sum(1 for o in self.outcomes if o.outcome == OutcomeType.PARTIAL_SUCCESS)
        
        avg_predicted_downtime = sum(o.predicted_downtime_hours for o in self.outcomes) / total if total else 0
        avg_actual_downtime = sum(o.actual_downtime_hours for o in self.outcomes) / total if total else 0
        
        avg_predicted_cost = sum(o.predicted_cost for o in self.outcomes) / total if total else 0
        avg_actual_cost = sum(o.actual_cost for o in self.outcomes) / total if total else 0
        
        correct_predictions = sum(1 for o in self.outcomes if o.predicted_cause.lower() == o.actual_cause.lower())
        
        return {
            'total_outcomes': total,
            'success_count': success_count,
            'partial_success_count': partial,
            'failure_count': total - success_count - partial,
            'success_rate': success_count / total if total else 0,
            'prediction_accuracy': correct_predictions / total if total else 0,
            'avg_predicted_downtime': avg_predicted_downtime,
            'avg_actual_downtime': avg_actual_downtime,
            'avg_predicted_cost': avg_predicted_cost,
            'avg_actual_cost': avg_actual_cost,
            'downtime_variance': avg_actual_downtime - avg_predicted_downtime,
            'cost_variance': avg_actual_cost - avg_predicted_cost
        }


# Singleton instance
_feedback_engine: Optional[FeedbackEngine] = None


def get_feedback_engine() -> FeedbackEngine:
    """Get global feedback engine instance."""
    global _feedback_engine
    if _feedback_engine is None:
        _feedback_engine = FeedbackEngine()
    return _feedback_engine