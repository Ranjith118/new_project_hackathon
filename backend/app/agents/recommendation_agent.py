"""Maintenance Recommendation Agent — generates immediate actions and long-term plans."""
import time
from typing import Dict, Any
from app.agents.base_agent import BaseAgent, AgentResult


class MaintenanceRecommendationAgent(BaseAgent):
    name = "maintenance_recommendation"

    async def run(self, context: Dict[str, Any]) -> AgentResult:
        t0 = time.time()
        eq = context.get("equipment_name", "Unknown")
        root_cause = context.get("primary_cause", "")
        fail_prob = context.get("failure_probability", 0)
        rul = context.get("rul_days", 60)
        health = context.get("health_score", 80)
        risk = context.get("risk_level", "Low")
        try:
            from app.recommendation.recommendation_engine import get_recommendation_engine
            engine = get_recommendation_engine()
            result = engine.generate_recommendations(
                equipment_name=eq,
                root_cause=root_cause,
                failure_probability=fail_prob/100 if fail_prob else None,
                rul_days=int(rul) if rul else None,
                health_score=int(health) if health else None,
                risk_level=risk.lower() if risk else None,
            )
            immediate = [{"action": r.action, "reason": r.reason, "priority": r.priority} for r in result.immediate_actions[:4]]
            repair    = [{"action": r.action, "reason": r.reason} for r in result.repair_actions[:4]]
            monitoring= [{"action": r.action} for r in result.monitoring_actions[:3]]
            preventive= [{"action": r.action} for r in result.preventive_actions[:3]]
            safety    = [{"action": r.action} for r in result.safety_actions[:3]]

            return AgentResult(agent_name=self.name, success=True, data={
                "priority": result.priority,
                "overall_reason": result.overall_reason,
                "confidence": round(result.confidence * 100, 1),
                "estimated_downtime_hours": result.estimated_total_downtime,
                "immediate_actions": immediate,
                "repair_actions": repair,
                "monitoring_actions": monitoring,
                "preventive_actions": preventive,
                "safety_actions": safety,
            }, execution_ms=(time.time()-t0)*1000)
        except Exception as e:
            return AgentResult(agent_name=self.name, success=False, error=str(e), execution_ms=(time.time()-t0)*1000)
