"""
Executive Summary Engine.

This module generates natural language summaries and executive reports
for plant-level decision support.
"""
import uuid
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime

from app.decision_support.risk_engine import get_plant_risk_engine, RiskScore
from app.decision_support.prioritization_engine import get_prioritization_engine, MaintenancePriority
from app.decision_support.bottleneck_engine import get_bottleneck_engine, Bottleneck
from app.decision_support.scheduling_engine import get_scheduling_engine, MaintenanceSchedule


@dataclass
class ExecutiveSummary:
    """Executive summary with natural language report."""
    summary_id: str
    generated_at: datetime
    plant_name: str
    plant_health_score: float
    critical_equipment_count: int
    immediate_actions: List[str]
    short_term_actions: List[str]
    medium_term_actions: List[str]
    key_insights: List[str]
    risks: List[str]
    recommendations: List[str]
    summary_text: str
    detailed_report: str


class ExecutiveSummaryEngine:
    """
    Generate executive summaries and decision support reports.
    
    Produces:
    - Natural language plant status summaries
    - Prioritized action lists
    - Risk assessments
    - Recommendations
    """
    
    def __init__(self):
        self.risk_engine = get_plant_risk_engine()
        self.prioritization = get_prioritization_engine()
        self.bottleneck = get_bottleneck_engine()
        self.scheduling = get_scheduling_engine()
    
    def generate_summary(
        self,
        plant_name: str = "Steel Manufacturing Plant",
        include_detailed: bool = True
    ) -> ExecutiveSummary:
        """
        Generate comprehensive executive summary.
        
        Args:
            plant_name: Name of the plant
            include_detailed: Include detailed analysis
            
        Returns:
            ExecutiveSummary with all components
        """
        # Get risk summary
        risk_summary = self.risk_engine.get_risk_summary()
        
        # Calculate plant health score
        plant_health = 100 - (risk_summary.get('average_risk', 50))
        
        # Get critical equipment
        critical_risks = self.risk_engine.get_critical_risks()
        high_risks = self.risk_engine.get_high_risks()
        
        # Generate actions by timeframe
        immediate = self._generate_immediate_actions(critical_risks)
        short_term = self._generate_short_term_actions(high_risks)
        medium_term = self._generate_medium_term_actions()
        
        # Generate insights
        insights = self._generate_insights(risk_summary, critical_risks)
        
        # Generate risks
        risks = self._generate_risks(critical_risks, high_risks)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            critical_risks, high_risks, immediate, short_term
        )
        
        # Generate summary text
        summary_text = self._generate_summary_text(
            plant_name, plant_health, len(critical_risks), len(high_risks)
        )
        
        # Generate detailed report
        detailed_report = ""
        if include_detailed:
            detailed_report = self._generate_detailed_report(
                critical_risks, high_risks, immediate, recommendations
            )
        
        return ExecutiveSummary(
            summary_id=str(uuid.uuid4()),
            generated_at=datetime.now(),
            plant_name=plant_name,
            plant_health_score=plant_health,
            critical_equipment_count=len(critical_risks),
            immediate_actions=immediate,
            short_term_actions=short_term,
            medium_term_actions=medium_term,
            key_insights=insights,
            risks=risks,
            recommendations=recommendations,
            summary_text=summary_text,
            detailed_report=detailed_report
        )
    
    def _generate_immediate_actions(self, critical: List[RiskScore]) -> List[str]:
        """Generate immediate action list."""
        actions = []
        
        for risk in critical[:3]:
            if risk.rul_days <= 14:
                actions.append(
                    f"Schedule immediate maintenance for {risk.equipment_name} "
                    f"(RUL: {risk.rul_days} days)"
                )
            else:
                actions.append(
                    f"Monitor {risk.equipment_name} closely and prepare for maintenance"
                )
        
        return actions
    
    def _generate_short_term_actions(self, high: List[RiskScore]) -> List[str]:
        """Generate short-term action list (next 30 days)."""
        actions = []
        
        for risk in high[:5]:
            actions.append(
                f"Plan maintenance for {risk.equipment_name} within 2 weeks "
                f"(Failure probability: {risk.failure_probability*100:.0f}%)"
            )
        
        return actions
    
    def _generate_medium_term_actions(self) -> List[str]:
        """Generate medium-term action list."""
        return [
            "Review and update preventive maintenance schedule",
            "Audit spare parts inventory for critical equipment",
            "Conduct safety review for high-criticality assets",
            "Update equipment monitoring thresholds"
        ]
    
    def _generate_insights(
        self,
        risk_summary: Dict[str, Any],
        critical: List[RiskScore]
    ) -> List[str]:
        """Generate key insights."""
        insights = []
        
        # Plant health insight
        health = 100 - (risk_summary.get('average_risk', 50))
        if health < 60:
            insights.append("Plant health is below acceptable levels - immediate attention required")
        elif health < 75:
            insights.append("Plant health is acceptable but requires monitoring")
        else:
            insights.append("Plant health is good - continue current maintenance practices")
        
        # Critical equipment insight
        if critical:
            highest = critical[0]
            insights.append(
                f"{highest.equipment_name} has the highest risk with "
                f"{highest.failure_probability*100:.0f}% failure probability"
            )
        
        # RUL insight
        critical_with_short_rul = [r for r in critical if r.rul_days <= 14]
        if critical_with_short_rul:
            names = ", ".join([r.equipment_name for r in critical_with_short_rul[:3]])
            insights.append(f"Equipment requiring urgent attention: {names}")
        
        return insights
    
    def _generate_risks(
        self,
        critical: List[RiskScore],
        high: List[RiskScore]
    ) -> List[str]:
        """Generate risk assessment."""
        risks = []
        
        if len(critical) > 0:
            risks.append(
                f"{len(critical)} equipment items at critical risk level"
            )
        
        # Check for common failure modes
        bearing_issues = [r for r in critical + high if 'bearing' in r.reasons[0].lower() if r.reasons]
        if bearing_issues:
            risks.append(
                f"Bearing failures may affect {len(bearing_issues)} equipment items"
            )
        
        # Production impact
        critical_criticality = sum(r.criticality_score for r in critical) / max(len(critical), 1)
        if critical_criticality > 75:
            risks.append(
                "High production dependency on critical equipment increases downtime risk"
            )
        
        return risks
    
    def _generate_recommendations(
        self,
        critical: List[RiskScore],
        high: List[RiskScore],
        immediate: List[str],
        short_term: List[str]
    ) -> List[str]:
        """Generate actionable recommendations."""
        recommendations = []
        
        # P1 recommendations
        if immediate:
            recommendations.append(
                "URGENT: Execute immediate actions for critical equipment"
            )
        
        # Spare parts recommendation
        if critical:
            recommendations.append(
                "Review and confirm availability of critical spares for high-risk equipment"
            )
        
        # Monitoring recommendation
        recommendations.append(
            "Implement enhanced monitoring for all critical and high-risk equipment"
        )
        
        # Bottleneck recommendation
        bottlenecks = self.bottleneck.get_critical_bottlenecks()
        if bottlenecks:
            recommendations.append(
                f"Review mitigation plans for {len(bottlenecks)} identified bottlenecks"
            )
        
        # Maintenance schedule
        recommendations.append(
            "Generate optimized maintenance schedule to minimize production impact"
        )
        
        return recommendations
    
    def _generate_summary_text(
        self,
        plant_name: str,
        plant_health: float,
        critical_count: int,
        high_count: int
    ) -> str:
        """Generate natural language summary."""
        lines = []
        
        lines.append(f"## {plant_name} Status Summary")
        lines.append("")
        lines.append(f"Plant Health Score: {plant_health:.1f}%")
        lines.append(f"Critical Risk Equipment: {critical_count}")
        lines.append(f"High Risk Equipment: {high_count}")
        lines.append("")
        
        if critical_count > 0:
            lines.append(
                f"⚠️ ATTENTION: {critical_count} equipment items require immediate attention."
            )
        else:
            lines.append("✅ No critical risk equipment identified at this time.")
        
        lines.append("")
        lines.append("### Key Findings:")
        
        if plant_health < 60:
            lines.append("- Plant requires immediate maintenance intervention")
        elif plant_health < 75:
            lines.append("- Plant condition is acceptable but requires monitoring")
        else:
            lines.append("- Plant is operating within normal parameters")
        
        return "\n".join(lines)
    
    def _generate_detailed_report(
        self,
        critical: List[RiskScore],
        high: List[RiskScore],
        immediate: List[str],
        recommendations: List[str]
    ) -> str:
        """Generate detailed report."""
        lines = []
        
        lines.append("## Detailed Risk Analysis Report")
        lines.append("")
        
        # Critical Equipment Section
        lines.append("### Critical Risk Equipment")
        lines.append("")
        for i, risk in enumerate(critical, 1):
            lines.append(f"**{i}. {risk.equipment_name}**")
            lines.append(f"- Risk Score: {risk.risk_score:.1f}")
            lines.append(f"- Failure Probability: {risk.failure_probability*100:.0f}%")
            lines.append(f"- Remaining Useful Life: {risk.rul_days} days")
            lines.append(f"- Criticality Score: {risk.criticality_score:.0f}")
            if risk.reasons:
                lines.append(f"- Key Issue: {risk.reasons[0]}")
            lines.append("")
        
        # High Risk Equipment Section
        lines.append("### High Risk Equipment")
        lines.append("")
        for i, risk in enumerate(high[:5], 1):
            lines.append(f"**{i}. {risk.equipment_name}**")
            lines.append(f"- Risk Score: {risk.risk_score:.1f}")
            lines.append(f"- Failure Probability: {risk.failure_probability*100:.0f}%")
            lines.append(f"- RUL: {risk.rul_days} days")
            lines.append("")
        
        # Recommendations Section
        lines.append("### Recommendations")
        lines.append("")
        for rec in recommendations:
            lines.append(f"- {rec}")
        
        return "\n".join(lines)
    
    def generate_production_impact_report(
        self,
        equipment_name: str,
        downtime_hours: float,
        criticality: float
    ) -> Dict[str, Any]:
        """Generate production impact analysis."""
        hourly_cost = criticality * 100  # Simplified cost estimation
        
        return {
            'equipment': equipment_name,
            'expected_downtime_hours': downtime_hours,
            'production_loss_per_hour': hourly_cost,
            'total_production_impact': downtime_hours * hourly_cost,
            'impact_level': 'critical' if downtime_hours > 8 else 'high' if downtime_hours > 4 else 'medium',
            'recovery_actions': [
                'Notify production planning',
                'Prepare backup equipment',
                'Coordinate maintenance window',
                'Communicate timeline to stakeholders'
            ]
        }


# Singleton instance
_executive_summary_engine: Optional[ExecutiveSummaryEngine] = None


def get_executive_summary_engine() -> ExecutiveSummaryEngine:
    """Get global executive summary engine instance."""
    global _executive_summary_engine
    if _executive_summary_engine is None:
        _executive_summary_engine = ExecutiveSummaryEngine()
    return _executive_summary_engine