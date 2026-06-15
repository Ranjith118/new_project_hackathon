"""Root Cause Analysis Agent — identifies probable failure causes."""
import time
from typing import Dict, Any
from app.agents.base_agent import BaseAgent, AgentResult


class RCAAgent(BaseAgent):
    name = "root_cause_analysis"

    async def run(self, context: Dict[str, Any]) -> AgentResult:
        t0 = time.time()
        eq = context.get("equipment_name", "Unknown")
        readings = context.get("sensor_readings", {})
        issue = context.get("issue", "")
        fail_prob = context.get("failure_probability")
        try:
            from app.rca.root_cause_engine import get_root_cause_engine
            engine = get_root_cause_engine()
            result = engine.analyze(
                equipment_name=eq,
                temperature=readings.get("temperature"),
                vibration=readings.get("vibration"),
                current=readings.get("current"),
                pressure=readings.get("pressure"),
                rpm=readings.get("rpm"),
                issue_description=issue or None,
                failure_probability=fail_prob,
            )
            similar = [{"case_id": c.case_id, "issue": c.issue, "root_cause": c.root_cause, "similarity": round(c.match_score*100,0)} for c in result.similar_cases[:3]]
            return AgentResult(agent_name=self.name, success=True, data={
                "primary_cause": result.primary_cause.cause,
                "confidence": round(result.primary_cause.confidence, 1),
                "confidence_level": result.primary_cause.confidence_level,
                "evidence": result.primary_cause.evidence[:5],
                "recommended_actions": result.primary_cause.recommended_actions[:5],
                "alternative_causes": [{"cause": a.cause, "confidence": round(a.confidence,1)} for a in result.secondary_causes[:2]],
                "contributing_factors": result.contributing_factors[:4],
                "similar_cases": similar,
                "reasoning_path": result.reasoning_path[:4],
                "investigation_steps": result.investigation_steps[:4],
            }, execution_ms=(time.time()-t0)*1000)
        except Exception as e:
            return AgentResult(agent_name=self.name, success=False, error=str(e), execution_ms=(time.time()-t0)*1000)
