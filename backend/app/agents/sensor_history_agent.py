"""Sensor History Agent — retrieves and summarizes sensor trends over time."""
import time
from typing import Dict, Any
from app.agents.base_agent import BaseAgent, AgentResult


class SensorHistoryAgent(BaseAgent):
    name = "sensor_history"

    async def run(self, context: Dict[str, Any]) -> AgentResult:
        t0 = time.time()
        eq = context.get("equipment_name", "")
        query = context.get("query", "")

        # Detect hours from query
        hours = 168  # default 7 days
        q = query.lower()
        if "24h" in q or "1 day" in q or "today" in q:
            hours = 24
        elif "3 day" in q:
            hours = 72
        elif "7 day" in q or "week" in q or "last week" in q:
            hours = 168
        elif "30 day" in q or "month" in q:
            hours = 720

        try:
            from app.database import async_session_maker
            from app.models.models import SensorData
            from sqlalchemy import select, desc
            from datetime import datetime, timedelta

            cutoff = datetime.now() - timedelta(hours=hours)

            async with async_session_maker() as db:
                rows = (await db.execute(
                    select(SensorData)
                    .where(SensorData.equipment_name.ilike(f"%{eq}%"))
                    .where(SensorData.created_at >= cutoff)
                    .order_by(desc(SensorData.created_at))
                    .limit(500)
                )).scalars().all()

            if not rows:
                return AgentResult(agent_name=self.name, success=True, data={
                    "message": f"No sensor data found for {eq} in the last {hours} hours.",
                    "equipment_name": eq, "hours": hours, "total_readings": 0
                }, execution_ms=(time.time()-t0)*1000)

            # Calculate stats per sensor
            sensors = ["temperature", "vibration", "current", "pressure", "rpm",
                       "voltage", "flow_rate", "humidity", "power_consumption",
                       "lubrication_level", "bearing_temperature"]

            stats = {}
            for s in sensors:
                vals = [getattr(r, s) for r in rows if getattr(r, s) is not None]
                if vals:
                    stats[s] = {
                        "min":   round(min(vals), 2),
                        "max":   round(max(vals), 2),
                        "avg":   round(sum(vals)/len(vals), 2),
                        "latest": round(vals[0], 2),
                        "readings": len(vals),
                    }

            # Trend analysis (compare first half vs second half)
            mid = len(rows) // 2
            trends = {}
            for s in ["temperature", "vibration", "current", "pressure", "rpm"]:
                first_half  = [getattr(r, s) for r in rows[mid:] if getattr(r, s) is not None]
                second_half = [getattr(r, s) for r in rows[:mid] if getattr(r, s) is not None]
                if first_half and second_half:
                    avg_old = sum(first_half) / len(first_half)
                    avg_new = sum(second_half) / len(second_half)
                    change = round(((avg_new - avg_old) / avg_old) * 100, 1) if avg_old else 0
                    trends[s] = {
                        "direction": "increasing" if change > 2 else "decreasing" if change < -2 else "stable",
                        "change_pct": change,
                    }

            # Recent readings (last 10)
            recent = []
            for r in rows[:10]:
                recent.append({
                    "timestamp": r.created_at.isoformat() if r.created_at else r.timestamp.isoformat(),
                    "temperature": r.temperature, "vibration": r.vibration,
                    "current": r.current, "pressure": r.pressure, "rpm": r.rpm,
                })

            # Check for anomalies in the period
            anomalies = []
            thresholds = {"temperature": 95, "vibration": 2.8, "current": 28, "pressure": 90}
            for s, thresh in thresholds.items():
                if s in stats and stats[s]["max"] >= thresh:
                    anomalies.append(f"{s} peaked at {stats[s]['max']} (threshold: {thresh})")

            return AgentResult(agent_name=self.name, success=True, data={
                "equipment_name": eq,
                "period_hours": hours,
                "period_label": f"Last {hours//24} day(s)" if hours >= 24 else f"Last {hours}h",
                "total_readings": len(rows),
                "first_reading":  rows[-1].created_at.isoformat() if rows else None,
                "latest_reading": rows[0].created_at.isoformat() if rows else None,
                "sensor_stats":   stats,
                "trends":         trends,
                "anomalies_in_period": anomalies,
                "recent_readings": recent,
            }, execution_ms=(time.time()-t0)*1000)

        except Exception as e:
            return AgentResult(agent_name=self.name, success=False, error=str(e),
                               execution_ms=(time.time()-t0)*1000)
