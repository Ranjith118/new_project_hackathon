"""Failure Prediction Agent — predicts failure probability and RUL."""
import time
import numpy as np
from typing import Dict, Any
from app.agents.base_agent import BaseAgent, AgentResult


class FailurePredictionAgent(BaseAgent):
    name = "failure_prediction"

    async def run(self, context: Dict[str, Any]) -> AgentResult:
        t0 = time.time()
        readings = context.get("sensor_readings", {})
        eq = context.get("equipment_name", "Unknown")
        try:
            from app.prediction.failure_model import get_failure_predictor, train_initial_failure_model
            from app.prediction.rul_model import get_rul_predictor, train_initial_rul_model

            fp = get_failure_predictor()
            rp = get_rul_predictor()
            if not fp.is_trained:
                train_initial_failure_model()
            if not rp.is_trained:
                train_initial_rul_model()

            defaults = {"temperature": 75, "vibration": 1.5, "current": 20, "pressure": 70, "rpm": 1500}
            r = {k: readings.get(k, defaults[k]) for k in ["temperature","vibration","current","pressure","rpm"]}
            X = np.array([[r["temperature"], r["vibration"], r["current"], r["pressure"], r["rpm"]]])

            fail_prob = float(fp.predict_proba(X)[0])
            rul = float(rp.predict(X)[0])
            expl = fp.explain_prediction(X)
            rul_expl = rp.explain_prediction(X)

            risk = "Critical" if fail_prob >= 0.8 else "High" if fail_prob >= 0.6 else "Medium" if fail_prob >= 0.4 else "Low"
            urgency = "Immediate" if rul <= 7 else "Urgent" if rul <= 15 else "Scheduled" if rul <= 30 else "Planned"

            return AgentResult(agent_name=self.name, success=True, data={
                "failure_probability": round(fail_prob * 100, 1),
                "rul_days": round(rul, 1),
                "risk_level": risk,
                "urgency": urgency,
                "contributing_factors": expl.get("contributing_factors", []),
                "feature_analysis": expl.get("feature_analysis", []),
                "rul_explanation": rul_expl.get("explanation", ""),
                "critical_factors": rul_expl.get("critical_factors", []),
            }, execution_ms=(time.time()-t0)*1000)
        except Exception as e:
            return AgentResult(agent_name=self.name, success=False, error=str(e), execution_ms=(time.time()-t0)*1000)
