"""
Recommendation Scoring Engine.

This module measures recommendation effectiveness and adjusts
confidence scores based on historical performance.
"""
import uuid
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from app.learning.feedback_engine import get_feedback_engine, FeedbackType, OutcomeType


@dataclass
class RecommendationScore:
    """Score for a recommendation type."""
    recommendation_type: str
    module_name: str
    total_count: int
    acceptance_count: int
    success_count: int
    avg_effectiveness: float
    confidence_adjustment: float  # -1 to +1 adjustment factor
    last_updated: datetime = field(default_factory=datetime.now)


@dataclass
class ModelPerformance:
    """Performance metrics for a model."""
    model_name: str
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    mae: float  # Mean Absolute Error
    rmse: float  # Root Mean Square Error
    sample_count: int
    last_updated: datetime = field(default_factory=datetime.now)


class RecommendationScoringEngine:
    """
    Score recommendations based on historical performance.
    
    Tracks:
    - Acceptance rates
    - Success rates
    - Prediction accuracy
    - Confidence adjustments
    """
    
    # Default recommendation types
    DEFAULT_RECOMMENDATIONS = {
        'recommendation': [
            {'type': 'bearing_replacement', 'module': 'recommendation', 'base_confidence': 0.75},
            {'type': 'seal_replacement', 'module': 'recommendation', 'base_confidence': 0.70},
            {'type': 'motor_inspection', 'module': 'recommendation', 'base_confidence': 0.80},
            {'type': 'filter_replacement', 'module': 'recommendation', 'base_confidence': 0.85},
            {'type': 'lubrication', 'module': 'recommendation', 'base_confidence': 0.90}
        ],
        'rca': [
            {'type': 'bearing_wear', 'module': 'rca', 'base_confidence': 0.75},
            {'type': 'motor_overheating', 'module': 'rca', 'base_confidence': 0.70},
            {'type': 'pump_blockage', 'module': 'rca', 'base_confidence': 0.80},
            {'type': 'electrical_fault', 'module': 'rca', 'base_confidence': 0.65},
            {'type': 'cooling_failure', 'module': 'rca', 'base_confidence': 0.75}
        ]
    }
    
    def __init__(self):
        self.feedback_engine = get_feedback_engine()
        self.scores: Dict[str, RecommendationScore] = {}
        self.model_performance: Dict[str, ModelPerformance] = {}
        self._initialize_scores()
    
    def _initialize_scores(self):
        """Initialize default scores."""
        # Initialize recommendation scores
        for module, recs in self.DEFAULT_RECOMMENDATIONS.items():
            for rec in recs:
                key = f"{module}_{rec['type']}"
                self.scores[key] = RecommendationScore(
                    recommendation_type=rec['type'],
                    module_name=rec['module'],
                    total_count=50,
                    acceptance_count=40,
                    success_count=35,
                    avg_effectiveness=0.80,
                    confidence_adjustment=0.0
                )
        
        # Initialize model performance
        self.model_performance['failure_prediction'] = ModelPerformance(
            model_name='failure_prediction',
            accuracy=0.88,
            precision=0.85,
            recall=0.90,
            f1_score=0.87,
            mae=5.2,
            rmse=7.1,
            sample_count=500
        )
        
        self.model_performance['rul_prediction'] = ModelPerformance(
            model_name='rul_prediction',
            accuracy=0.82,
            precision=0.80,
            recall=0.85,
            f1_score=0.82,
            mae=8.3,
            rmse=10.5,
            sample_count=500
        )
        
        self.model_performance['anomaly_detection'] = ModelPerformance(
            model_name='anomaly_detection',
            accuracy=0.91,
            precision=0.88,
            recall=0.93,
            f1_score=0.90,
            mae=0.15,
            rmse=0.22,
            sample_count=1000
        )
        
        self.model_performance['rca'] = ModelPerformance(
            model_name='rca',
            accuracy=0.85,
            precision=0.82,
            recall=0.88,
            f1_score=0.85,
            mae=0.18,
            rmse=0.25,
            sample_count=300
        )
    
    def update_scores_from_feedback(self) -> Dict[str, RecommendationScore]:
        """
        Update recommendation scores based on recent feedback.
        
        Returns:
            Updated scores
        """
        # Calculate acceptance rates from feedback
        feedback = self.feedback_engine.get_recent_feedback(days=30)
        
        for module in ['recommendation', 'rca']:
            module_feedback = [f for f in feedback if f.module_name == module]
            
            accepted = [f for f in module_feedback if f.feedback_type == FeedbackType.RECOMMENDATION_ACCEPTED]
            rejected = [f for f in module_feedback if f.feedback_type == FeedbackType.RECOMMENDATION_REJECTED]
            
            if accepted or rejected:
                total = len(accepted) + len(rejected)
                acceptance_rate = len(accepted) / total
                
                # Adjust confidence based on acceptance rate
                for score in self.scores.values():
                    if score.module_name == module:
                        # Calculate adjustment
                        delta = (acceptance_rate - 0.75) * 0.3  # Scale to max +/- 0.15
                        score.confidence_adjustment = max(-0.3, min(0.3, delta))
                        score.acceptance_count = len(accepted)
                        score.last_updated = datetime.now()
        
        return self.scores
    
    def get_recommendation_confidence(
        self,
        recommendation_type: str,
        module_name: str
    ) -> float:
        """
        Get adjusted confidence for a recommendation.
        
        Args:
            recommendation_type: Type of recommendation
            module_name: Module name
            
        Returns:
            Adjusted confidence (0-1)
        """
        key = f"{module_name}_{recommendation_type}"
        
        if key in self.scores:
            base = self.scores[key].avg_effectiveness
            adjustment = self.scores[key].confidence_adjustment
            return max(0.1, min(1.0, base + adjustment))
        
        return 0.7  # Default confidence
    
    def get_all_scores(self) -> List[RecommendationScore]:
        """Get all recommendation scores."""
        return list(self.scores.values())
    
    def get_module_scores(self, module_name: str) -> List[RecommendationScore]:
        """Get scores for a specific module."""
        return [s for s in self.scores.values() if s.module_name == module_name]
    
    def update_model_performance(
        self,
        model_name: str,
        accuracy: float,
        precision: float,
        recall: float,
        f1_score: float,
        mae: float,
        rmse: float,
        sample_count: int
    ) -> ModelPerformance:
        """Update model performance metrics."""
        performance = ModelPerformance(
            model_name=model_name,
            accuracy=accuracy,
            precision=precision,
            recall=recall,
            f1_score=f1_score,
            mae=mae,
            rmse=rmse,
            sample_count=sample_count,
            last_updated=datetime.now()
        )
        
        self.model_performance[model_name] = performance
        return performance
    
    def get_model_performance(self, model_name: str) -> Optional[ModelPerformance]:
        """Get performance for a specific model."""
        return self.model_performance.get(model_name)
    
    def get_all_performance(self) -> List[ModelPerformance]:
        """Get performance for all models."""
        return list(self.model_performance.values())
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get summary of all model performance."""
        total_samples = sum(p.sample_count for p in self.model_performance.values())
        avg_accuracy = sum(p.accuracy for p in self.model_performance.values()) / len(self.model_performance) if self.model_performance else 0
        avg_f1 = sum(p.f1_score for p in self.model_performance.values()) / len(self.model_performance) if self.model_performance else 0
        
        return {
            'total_samples': total_samples,
            'average_accuracy': avg_accuracy,
            'average_f1_score': avg_f1,
            'model_count': len(self.model_performance),
            'best_model': max(self.model_performance.values(), key=lambda p: p.f1_score).model_name if self.model_performance else None,
            'needs_retraining': avg_accuracy < 0.85
        }


# Singleton instance
_scoring_engine: Optional[RecommendationScoringEngine] = None


def get_scoring_engine() -> RecommendationScoringEngine:
    """Get global scoring engine instance."""
    global _scoring_engine
    if _scoring_engine is None:
        _scoring_engine = RecommendationScoringEngine()
    return _scoring_engine