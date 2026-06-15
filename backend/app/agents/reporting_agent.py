"""Reporting Agent — creates structured maintenance and alert reports."""
import time
from typing import Dict, Any
from app.agents.base_agent import BaseAgent, AgentResult


class ReportingAgent(BaseAgent):
    name = "reporting"

    async def run(self, context: Dict[str, Any]) -> AgentResult:
        t0 = time.time()
        eq = context.get("equipment_name", "Unknown")
        try:
            from app.database import async_session_maker
            from app.models.models import MaintenanceLog, FailureReport, AlertRecord
            from sqlalchemy import select, desc

            async with async_session_maker() as db:
                # Recent maintenance logs
                logs = (await db.execute(
                    select(MaintenanceLog)
                    .where(MaintenanceLog.equipment_name.ilike(f"%{eq}%"))
                    .order_by(desc(MaintenanceLog.maintenance_date)).limit(5)
                )).scalars().all()

                # Recent failure reports
                failures = (await db.execute(
                    select(FailureReport)
                    .where(FailureReport.equipment_name.ilike(f"%{eq}%"))
                    .order_by(desc(FailureReport.report_date)).limit(3)
                )).scalars().all()

                # Active alerts
                alerts = (await db.execute(
                    select(AlertRecord)
                    .where(AlertRecord.equipment_name.ilike(f"%{eq}%"))
                    .where(AlertRecord.status == "active")
                    .order_by(desc(AlertRecord.created_at)).limit(5)
                )).scalars().all()

            maint_history = [{
                "date": str(l.maintenance_date), "issue": l.issue,
                "action": l.action_taken or "Pending",
                "severity": l.severity, "downtime_hours": l.downtime_hours,
            } for l in logs]

            failure_history = [{
                "date": str(f.report_date), "type": f.failure_type,
                "root_cause": f.root_cause or "Unknown",
                "downtime_hours": f.downtime_hours,
            } for f in failures]

            active_alerts = [{
                "type": a.alert_type, "message": a.message,
                "source": a.source, "created_at": a.created_at.isoformat() if a.created_at else None,
            } for a in alerts]

            total_downtime = sum(l.downtime_hours for l in logs)
            recurring = {}
            for l in logs:
                k = l.issue[:40]
                recurring[k] = recurring.get(k, 0) + 1
            recurring_issues = [{"issue": k, "count": v} for k, v in sorted(recurring.items(), key=lambda x: -x[1]) if v > 1]

            return AgentResult(agent_name=self.name, success=True, data={
                "maintenance_history": maint_history,
                "failure_history": failure_history,
                "active_alerts": active_alerts,
                "total_maintenance_records": len(logs),
                "total_failure_reports": len(failures),
                "total_downtime_hours": round(total_downtime, 1),
                "recurring_issues": recurring_issues,
            }, execution_ms=(time.time()-t0)*1000)
        except Exception as e:
            return AgentResult(agent_name=self.name, success=False, error=str(e), execution_ms=(time.time()-t0)*1000)
