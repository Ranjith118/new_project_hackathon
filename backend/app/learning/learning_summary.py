"""
Learning Summary Engine.

This module generates executive summaries of learning
and improvement activities across the system.
"""
import uuid
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from app.learning.feedback_engine import get_feedback_engine
from app.learning.recommendation_scoring import get_scoring_engine
from app.learning.performance_monitor import get_performance_monitor
from app.learning.retraining_engine import get_retraining_engine


@dataclass
class LearningSummary:
    """Executive learning summary."""
    summary_id: str
    generated_at: datetime
    period: str  # weekly, monthly, quarterly
    period_start: datetime
    period_end: datetime
    
    # Feedback statistics
    total_feedback: int
    positive_feedback: int
    negative_feedback: int
    acceptance_rate: float
    
    # Outcome statistics
    total_outcomes: int
    success_rate: float
    prediction_accuracy: float
    
    # Model performance
    average_accuracy: float
    accuracy_change: float
    models_improved: List[str]
    
    # Retraining activity
    retraining_jobs: int
    models_retrained: int
    average_improvement: float
    
    # Key insights
    top_improvements: List[str]
    areas_of_concern: List[str]
    recommendations: List[str]
    
    # Natural language summary
    summary_text: str
    detailed_report: str


class LearningSummaryEngine:
    """
    Generate executive learning summaries.
    
    Produces:
    - Weekly/monthly summaries
    - Performance trends
    - Improvement insights
    - Recommendations
    """
    
    def __init__(self):
        self.feedback_engine = get_feedback_engine()
        self.scoring_engine = get_scoring_engine()
        self.performance_monitor = get_performance_monitor()
        self.retraining_engine = get_retraining_engine()
    
    def generate_summary(
        self,
        period: str = 'monthly',
        days: int = 30
    ) -> LearningSummary:
        """
        Generate comprehensive learning summary.
        
        Args:
            period: Summary period ('weekly', 'monthly', 'quarterly')
            days: Number of days to analyze
            
        Returns:
            LearningSummary with all components
        """
        summary_id = str(uuid.uuid4())
        period_end = datetime.now()
        period_start = period_end - timedelta(days=days)
        
        # Get feedback data
        recent_feedback = self.feedback_engine.get_recent_feedback(days)
        feedback_summaries = self.feedback_engine.get_all_summaries()
        
        # Get outcome data
        recent_outcomes = self.feedback_engine.get_recent_outcomes(days)
        outcome_summary = self.feedback_engine.get_outcome_summary()
        
        # Get performance data
        performance_summary = self.performance_monitor.get_dashboard_summary()
        trends = self.performance_monitor.get_all_trends(days)
        
        # Get retraining data
        retraining_summary = self.retraining_engine.get_retraining_summary()
        
        # Calculate statistics
        total_feedback = len(recent_feedback)
        positive = sum(1 for f in recent_feedback if f.rating >= 4)
        negative = sum(1 for f in recent_feedback if f.rating <= 2)
        
        # Calculate acceptance rate
        accepted = sum(1 for f in recent_feedback if f.feedback_type.value == 'recommendation_accepted')
        total_recs = sum(1 for f in recent_feedback if f.feedback_type.value in [
            'recommendation_accepted', 'recommendation_rejected'
        ])
        acceptance_rate = accepted / total_recs if total_recs else 0
        
        # Model performance
        models = self.scoring_engine.get_all_performance()
        avg_accuracy = sum(p.accuracy for p in models) / len(models) if models else 0
        
        # Calculate accuracy change
        accuracy_change = 0
        for trend in trends:
            if trend.metric_name == 'failure_prediction_accuracy':
                accuracy_change = trend.change
        
        # Identify improvements
        top_improvements = []
        for trend in trends:
            if trend.trend == 'improving' and abs(trend.change) > 2:
                top_improvements.append(
                    f"{trend.metric_name} improved by {trend.change:.1f}%"
                )
        
        # Identify concerns
        areas_of_concern = []
        for trend in trends:
            if trend.trend == 'declining' and abs(trend.change) > 2:
                areas_of_concern.append(
                    f"{trend.metric_name} declined by {abs(trend.change):.1f}%"
                )
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            top_improvements, areas_of_concern, 
            outcome_summary, performance_summary
        )
        
        # Models improved
        models_improved = []
        for job in self.retraining_engine.get_recent_jobs(5):
            if job.status == 'completed' and job.improvement > 0:
                models_improved.append(job.model_name)
        
        # Generate summary text
        summary_text = self._generate_summary_text(
            period, total_feedback, positive, acceptance_rate,
            outcome_summary.get('success_rate', 0), avg_accuracy,
            len(models_improved), top_improvements
        )
        
        # Generate detailed report
        detailed_report = self._generate_detailed_report(
            feedback_summaries, outcome_summary, 
            performance_summary, retraining_summary
        )
        
        return LearningSummary(
            summary_id=summary_id,
            generated_at=datetime.now(),
            period=period,
            period_start=period_start,
            period_end=period_end,
            total_feedback=total_feedback,
            positive_feedback=positive,
            negative_feedback=negative,
            acceptance_rate=acceptance_rate,
            total_outcomes=len(recent_outcomes),
            success_rate=outcome_summary.get('success_rate', 0),
            prediction_accuracy=outcome_summary.get('prediction_accuracy', 0),
            average_accuracy=avg_accuracy,
            accuracy_change=accuracy_change,
            models_improved=models_improved,
            retraining_jobs=retraining_summary['total_jobs'],
            models_retrained=len(models_improved),
            average_improvement=retraining_summary['average_improvement'],
            top_improvements=top_improvements,
            areas_of_concern=areas_of_concern,
            recommendations=recommendations,
            summary_text=summary_text,
            detailed_report=detailed_report
        )
    
    def _generate_recommendations(
        self,
        improvements: List[str],
        concerns: List[str],
        outcomes: Dict,
        performance: Dict
    ) -> List[str]:
        """Generate actionable recommendations."""
        recommendations = []
        
        # Based on concerns
        if concerns:
            recommendations.append(
                "Review models showing declining accuracy and consider retraining"
            )
        
        # Based on success rate
        if outcomes.get('success_rate', 0) < 0.85:
            recommendations.append(
                "Root cause prediction accuracy needs improvement - consider more training data"
            )
        
        # Based on acceptance rate
        if self._get_overall_acceptance() < 0.80:
            recommendations.append(
                "Recommendation acceptance is below target - review recommendation criteria"
            )
        
        # Based on downtime variance
        if outcomes.get('downtime_variance', 0) > 2:
            recommendations.append(
                "Downtime predictions are underestimated - recalibrate prediction models"
            )
        
        # General recommendations
        recommendations.append(
            "Continue collecting feedback to improve model accuracy"
        )
        recommendations.append(
            "Review equipment with multiple failed predictions for pattern analysis"
        )
        
        return recommendations[:5]  # Limit to top 5
    
    def _get_overall_acceptance(self) -> float:
        """Get overall recommendation acceptance rate."""
        summaries = self.feedback_engine.get_all_summaries()
        
        total_accepted = sum(s.positive_count for s in summaries)
        total = sum(s.total_feedback for s in summaries)
        
        return total_accepted / total if total > 0 else 0
    
    def _generate_summary_text(
        self,
        period: str,
        total_feedback: int,
        positive: int,
        acceptance: float,
        success_rate: float,
        avg_accuracy: float,
        models_retrained: int,
        improvements: List[str]
    ) -> str:
        """Generate natural language summary."""
        lines = []
        
        lines.append(f"## {period.title()} Learning Summary")
        lines.append("")
        lines.append(f"**Period:** Last {period}")
        lines.append("")
        
        # Feedback summary
        lines.append("### Feedback Overview")
        lines.append(f"- Total feedback received: {total_feedback}")
        lines.append(f"- Positive feedback: {positive} ({positive/total_feedback*100:.0f}%)" if total_feedback > 0 else "- No feedback received")
        lines.append(f"- Recommendation acceptance rate: {acceptance*100:.0f}%")
        lines.append("")
        
        # Outcome summary
        lines.append("### Maintenance Outcomes")
        lines.append(f"- Success rate: {success_rate*100:.0f}%")
        lines.append(f"- Average model accuracy: {avg_accuracy*100:.0f}%")
        lines.append("")
        
        # Improvements
        if improvements:
            lines.append("### Key Improvements")
            for imp in improvements[:3]:
                lines.append(f"- {imp}")
            lines.append("")
        
        # Models retrained
        if models_retrained > 0:
            lines.append(f"- {models_retrained} models retrained this period")
        
        return "\n".join(lines)
    
    def _generate_detailed_report(
        self,
        feedback_summaries: List,
        outcome_summary: Dict,
        performance: Dict,
        retraining: Dict
    ) -> str:
        """Generate detailed report."""
        lines = []
        
        lines.append("## Detailed Learning Report")
        lines.append("")
        
        # Module performance
        lines.append("### Module Performance")
        for summary in feedback_summaries:
            lines.append(f"**{summary.module_name.upper()}**")
            lines.append(f"- Total feedback: {summary.total_feedback}")
            lines.append(f"- Acceptance rate: {summary.acceptance_rate*100:.0f}%")
            lines.append(f"- Average rating: {summary.average_rating:.1f}/5")
            lines.append("")
        
        # Outcome analysis
        lines.append("### Outcome Analysis")
        lines.append(f"- Total outcomes tracked: {outcome_summary.get('total_outcomes', 0)}")
        lines.append(f"- Success rate: {outcome_summary.get('success_rate', 0)*100:.0f}%")
        lines.append(f"- Prediction accuracy: {outcome_summary.get('prediction_accuracy', 0)*100:.0f}%")
        lines.append(f"- Average downtime variance: {outcome_summary.get('downtime_variance', 0):.1f} hours")
        lines.append(f"- Average cost variance: ${outcome_summary.get('cost_variance', 0):.0f}")
        lines.append("")
        
        # Retraining activity
        lines.append("### Retraining Activity")
        lines.append(f"- Total retraining jobs: {retraining.get('total_jobs', 0)}")
        lines.append(f"- Completed: {retraining.get('completed', 0)}")
        lines.append(f"- Failed: {retraining.get('failed', 0)}")
        lines.append(f"- Average improvement: {retraining.get('average_improvement', 0)*100:.1f}%")
        lines.append("")
        
        return "\n".join(lines)
    
    def get_quick_summary(self) -> Dict[str, Any]:
        """Get quick summary for dashboard."""
        performance = self.performance_monitor.get_dashboard_summary()
        retraining = self.retraining_engine.get_retraining_summary()
        
        return {
            'feedback_count': performance.get('total_feedback_count', 0),
            'acceptance_rate': performance.get('recommendation_acceptance', 0),
            'success_rate': performance.get('outcome_success_rate', 0),
            'average_accuracy': performance.get('prediction_accuracy', 0),
            'models_need_retraining': len(retraining.get('models_needing_retraining', [])),
            'retraining_jobs': retraining.get('total_jobs', 0),
            'recent_improvement': retraining.get('average_improvement', 0)
        }


# Singleton instance
_learning_summary_engine: Optional[LearningSummaryEngine] = None


def get_learning_summary_engine() -> LearningSummaryEngine:
    """Get global learning summary engine instance."""
    global _learning_summary_engine
    if _learning_summary_engine is None:
        _learning_summary_engine = LearningSummaryEngine()
    return _learning_summary_engine