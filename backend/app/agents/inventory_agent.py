"""Inventory Agent — checks spare availability and generates procurement recommendations."""
import time
from typing import Dict, Any
from app.agents.base_agent import BaseAgent, AgentResult


class InventoryAgent(BaseAgent):
    name = "inventory"

    async def run(self, context: Dict[str, Any]) -> AgentResult:
        t0 = time.time()
        root_cause = context.get("primary_cause", "")
        eq = context.get("equipment_name", "")
        eq_type = context.get("equipment_type", "motor")
        fail_prob = context.get("failure_probability", 0)
        try:
            from app.procurement.inventory_engine import get_inventory_engine
            from app.procurement.mapping_engine import get_mapping_engine
            from app.procurement.reorder_engine import get_reorder_engine

            inv = get_inventory_engine()
            mapper = get_mapping_engine()
            reorder = get_reorder_engine()

            # Get mapped parts for root cause
            mappings = mapper.get_spare_parts(eq_type, root_cause, fail_prob/100 if fail_prob else 0.5)
            required_parts = []
            for m in mappings[:5]:
                part = inv.get_part(m.part_id)
                stock_ok = part.stock_quantity >= m.quantity_required if part else False
                required_parts.append({
                    "part_name": m.part_name,
                    "part_number": m.part_number,
                    "quantity_needed": m.quantity_required,
                    "in_stock": part.stock_quantity if part else 0,
                    "available": stock_ok,
                    "urgency": m.urgency,
                    "lead_time_days": part.lead_time_days if part else 0,
                    "unit_cost": part.unit_cost if part else 0,
                })

            # Critical alerts
            alerts = inv.get_critical_alerts()
            critical_parts = [{"part": a.part_name, "stock": a.current_stock, "minimum": a.minimum_stock} for a in alerts[:3]]

            # Reorder recs
            recs = reorder.generate_all_recommendations()
            urgent_reorders = [{"part": r.part_name, "qty": r.recommended_quantity, "urgency": r.urgency, "cost": r.estimated_cost} for r in recs[:3] if r.urgency in ("critical","high")]

            all_available = all(p["available"] for p in required_parts)
            return AgentResult(agent_name=self.name, success=True, data={
                "required_parts": required_parts,
                "all_parts_available": all_available,
                "critical_stock_alerts": critical_parts,
                "urgent_reorders": urgent_reorders,
                "procurement_needed": not all_available,
                "estimated_parts_cost": sum(p["unit_cost"] * p["quantity_needed"] for p in required_parts if p.get("unit_cost")),
            }, execution_ms=(time.time()-t0)*1000)
        except Exception as e:
            return AgentResult(agent_name=self.name, success=False, error=str(e), execution_ms=(time.time()-t0)*1000)
