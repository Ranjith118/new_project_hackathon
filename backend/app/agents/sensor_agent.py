"""Sensor Analysis Agent — analyzes live sensor data and detects abnormalities."""
import time
from typing import Dict, Any
from app.agents.base_agent import BaseAgent, AgentResult


class SensorAnalysisAgent(BaseAgent):
    name = "sensor_analysis"

    async def run(self, context: Dict[str, Any]) -> AgentResult:
        t0 = time.time()
        eq = context.get("equipment_name", "")
        readings = context.get("sensor_readings", {})

        try:
            from app.health.health_score import get_health_calculator
            from app.health.alert_engine import get_alert_engine

            calc = get_health_calculator()
            result = {}

            if readings:
                health = calc.calculate_score(readings)
                alert_engine = get_alert_engine()
                alerts = alert_engine.check_thresholds(eq, readings)

                # Identify abnormal sensors
                abnormal = []
                for sensor, value in readings.items():
                    if sensor == "temperature" and value > 95:
                        abnormal.append({"sensor": sensor, "value": value, "status": "critical" if value > 110 else "warning"})
                    elif sensor == "vibration" and value > 2.8:
                        abnormal.append({"sensor": sensor, "value": value, "status": "critical" if value > 4.0 else "warning"})
                    elif sensor == "current" and value > 28:
                        abnormal.append({"sensor": sensor, "value": value, "status": "critical" if value > 32 else "warning"})

                result = {
                    "health_score": health.score,
                    "health_status": health.status,
                    "risk_level": health.risk_level,
                    "sensor_readings": readings,
                    "abnormal_sensors": abnormal,
                    "threshold_alerts": len(alerts),
                    "recommendations": health.recommendations[:3],
                    "factors": health.factors,
                }
            else:
                # Try to get from live status
                from app.database import async_session_maker
                from app.models.models import SensorData
                from sqlalchemy import select, desc
                async with async_session_maker() as db:
                    row = (await db.execute(
                        select(SensorData)
                        .where(SensorData.equipment_name == eq)
                        .order_by(desc(SensorData.created_at))
                        .limit(1)
                    )).scalar_one_or_none()

                if row:
                    rdg = {}
                    for k in ["temperature","vibration","current","pressure","rpm"]:
                        v = getattr(row, k, None)
                        if v is not None: rdg[k] = v
                    health = calc.calculate_score(rdg)
                    result = {
                        "health_score": health.score,
                        "health_status": health.status,
                        "risk_level": health.risk_level,
                        "sensor_readings": rdg,
                        "abnormal_sensors": [],
                        "last_reading": row.created_at.isoformat() if row.created_at else None,
                        "recommendations": health.recommendations[:3],
                    }
                else:
                    result = {"note": "No sensor data available", "health_score": None}

            return AgentResult(agent_name=self.name, success=True, data=result, execution_ms=(time.time()-t0)*1000)

        except Exception as e:
            return AgentResult(agent_name=self.name, success=False, error=str(e), execution_ms=(time.time()-t0)*1000)

    # alias
    @property
    def agent_name(self): return self.name
