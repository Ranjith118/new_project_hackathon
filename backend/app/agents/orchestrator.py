"""
Orchestrator Agent — decides which agents to invoke and synthesizes a unified response.
Uses Groq LLM to generate the final structured answer from all agent outputs.
"""
import asyncio
import json
import time
from typing import Dict, Any, List, Optional

from app.agents.base_agent import AgentResult
from app.agents.sensor_agent import SensorAnalysisAgent
from app.agents.sensor_history_agent import SensorHistoryAgent
from app.agents.prediction_agent import FailurePredictionAgent
from app.agents.rca_agent import RCAAgent
from app.agents.document_agent import DocumentIntelligenceAgent
from app.agents.inventory_agent import InventoryAgent
from app.agents.recommendation_agent import MaintenanceRecommendationAgent
from app.agents.reporting_agent import ReportingAgent


# Agent registry
ALL_AGENTS = {
    "sensor":          SensorAnalysisAgent(),
    "sensor_history":  SensorHistoryAgent(),
    "prediction":      FailurePredictionAgent(),
    "rca":             RCAAgent(),
    "document":        DocumentIntelligenceAgent(),
    "inventory":       InventoryAgent(),
    "recommendation":  MaintenanceRecommendationAgent(),
    "reporting":       ReportingAgent(),
}

# Intent → agents mapping
INTENT_AGENTS = {
    "sensor_history":   ["sensor_history"],
    "diagnosis":        ["sensor", "prediction", "rca", "document", "recommendation"],
    "prediction":       ["sensor", "prediction", "recommendation"],
    "maintenance":      ["rca", "recommendation", "inventory", "reporting"],
    "inventory":        ["inventory", "recommendation"],
    "history":          ["reporting"],
    "document":         ["document"],
    "alert":            ["sensor", "reporting"],
    "general":          ["sensor", "prediction", "rca", "recommendation"],
}


def detect_intent(query: str) -> str:
    """Detect query intent to decide which agents to run."""
    q = query.lower()
    if any(w in q for w in ["7 day", "7day", "last week", "history", "trend", "past", "previous",
                              "sensor detail", "sensor data", "sensor history", "readings", "show sensor"]):
        return "sensor_history"
    if any(w in q for w in ["why", "cause", "diagnose", "what is wrong", "problem", "fault",
                              "failure reason", "anomaly", "abnormal", "overheating", "overheat",
                              "vibrat", "high temp", "critical sensor", "what happened"]):
        return "diagnosis"
    if any(w in q for w in ["predict", "fail", "rul", "remaining", "when will", "how long"]):
        return "prediction"
    if any(w in q for w in ["replace", "repair", "maintenance", "how to fix", "procedure", "steps",
                              "resolve", "fix", "solution", "what should i do", "guide me"]):
        return "maintenance"
    if any(w in q for w in ["spare", "part", "stock", "inventory", "order", "procurement"]):
        return "inventory"
    if any(w in q for w in ["manual", "document", "sop", "specification", "spec", "datasheet"]):
        return "document"
    if any(w in q for w in ["alert", "alarm", "warning", "critical", "active alert", "current alert"]):
        return "alert"
    return "general"


def extract_equipment_from_context(live_context: str) -> tuple[str, dict]:
    """
    Parse live_context string to find the most critical equipment and its sensor readings.
    Returns (equipment_name, sensor_readings_dict).
    """
    import re
    critical_eq = ""
    worst_health = 101
    sensor_readings = {}

    if not live_context:
        return "", {}

    # Find equipment with lowest health score — most critical first
    # Pattern: "- Equipment Name: Health 45% | Risk: High | temp=90.2°C[warning] ..."
    for line in live_context.splitlines():
        if "Health " in line and "%" in line and "Risk:" in line:
            health_match = re.search(r'Health\s+(\d+)%', line)
            if health_match:
                score = int(health_match.group(1))
                if score < worst_health:
                    worst_health = score
                    # Extract equipment name — before the colon
                    eq_match = re.match(r'[-\s]*(.+?):\s+Health', line)
                    if eq_match:
                        critical_eq = eq_match.group(1).strip()
                    # Extract sensor readings from same line
                    rdgs = {}
                    for sensor in ["temperature", "vibration", "current", "pressure", "rpm"]:
                        m = re.search(rf'{sensor}=([\d.]+)', line)
                        if m:
                            try:
                                rdgs[sensor] = float(m.group(1))
                            except ValueError:
                                pass
                    if rdgs:
                        sensor_readings = rdgs

    return critical_eq, sensor_readings


def extract_equipment(query: str, context: Dict) -> str:
    """Extract equipment name from query or context."""
    if context.get("equipment_name"):
        return context["equipment_name"]
    known = [
        "Rolling Mill Motor", "Blast Furnace Fan",
        "Cooling Pump A", "Main Compressor", "Conveyor Belt System",
        "Slab Reheating Furnace", "Hot Rolling Mill", "Cold Rolling Mill",
        "Crane Motor 1", "Cooling Pump B", "Central Lubrication System",
        "Hydraulic Power Unit",
    ]
    q = query.lower()
    for eq in known:
        if any(w in q for w in eq.lower().split()):
            return eq
    return ""


async def run_agents(agent_names: List[str], context: Dict) -> Dict[str, AgentResult]:
    """Run selected agents in parallel."""
    tasks = {}
    for name in agent_names:
        if name in ALL_AGENTS:
            tasks[name] = ALL_AGENTS[name].run(context)
    results = await asyncio.gather(*tasks.values(), return_exceptions=True)
    output = {}
    for name, result in zip(tasks.keys(), results):
        if isinstance(result, Exception):
            output[name] = AgentResult(agent_name=name, success=False, error=str(result))
        else:
            output[name] = result
    return output


def build_synthesis_prompt(query: str, agent_results: Dict[str, AgentResult], context: Dict) -> str:
    """Build the LLM prompt to synthesize all agent outputs."""
    eq = context.get("equipment_name", "the equipment")

    sections = [f"USER QUERY: {query}\nEQUIPMENT: {eq}\n"]

    for name, result in agent_results.items():
        if result.success and result.data:
            sections.append(f"=== {name.upper().replace('_',' ')} AGENT ===")
            sections.append(json.dumps(result.data, indent=2, default=str))

    sections.append("""
Based on ALL the above agent outputs, provide a comprehensive maintenance engineering response.

RESPOND IN THIS EXACT STRUCTURE (plain text, no markdown ** or ## symbols):

DIAGNOSIS:
[Clear diagnosis of what is happening with the equipment]

ROOT CAUSE:
[Primary root cause with confidence percentage]

RISK LEVEL: [Critical/High/Medium/Low]
FAILURE PROBABILITY: [X%]
REMAINING USEFUL LIFE: [X days]

EVIDENCE:
- [evidence item 1]
- [evidence item 2]
- [evidence item 3]

IMMEDIATE ACTIONS:
1. [action]
2. [action]
3. [action]

REPAIR PROCEDURE:
1. [step]
2. [step]
3. [step]

SPARE PARTS REQUIRED:
- [part name] - Stock: [available/quantity] - Lead time: [days]

LONG-TERM RECOMMENDATIONS:
- [recommendation]
- [recommendation]

SUPPORTING EVIDENCE FROM DOCUMENTS:
[Mention any relevant documents/manuals found]

CONFIDENCE SCORE: [X%]
[Brief explanation of confidence]
""")

    return "\n".join(sections)


async def orchestrate(
    query: str,
    conversation_history: List[Dict] = None,
    equipment_name: str = "",
    sensor_readings: Dict = None,
    live_context: str = "",
) -> Dict[str, Any]:
    """
    Main orchestration function.
    Detects intent → parses live context for critical equipment →
    runs relevant agents → synthesizes response via LLM.
    """
    t0 = time.time()
    conversation_history = conversation_history or []
    sensor_readings = sensor_readings or {}

    # ── Parse live_context to find most critical equipment & readings ──
    ctx_eq, ctx_readings = extract_equipment_from_context(live_context)

    # Equipment resolution priority:
    # 1. Explicit equipment_name from UI
    # 2. Mentioned in query text
    # 3. Most critical equipment extracted from live_context
    eq = equipment_name or extract_equipment(query, {}) or ctx_eq

    # Sensor readings: prefer passed-in readings, then parsed from live_context
    if not sensor_readings and ctx_readings and (not eq or ctx_eq == eq):
        sensor_readings = ctx_readings

    # ── Detect intent ──────────────────────────────────────────────────
    intent = detect_intent(query)

    # If live context shows critical anomaly and query asks for general help / alerts,
    # escalate to full diagnosis pipeline
    if intent in ("alert", "general") and ctx_eq:
        import re
        critical_keywords = re.findall(r'\[CRITICAL\]|\[WARNING\]|Health [0-3]\d%|Health [4-5]\d%', live_context)
        if critical_keywords:
            intent = "diagnosis"

    # ── Build agent context ────────────────────────────────────────────
    agent_context = {
        "query":            query,
        "equipment_name":   eq,
        "equipment_type":   "motor",
        "sensor_readings":  sensor_readings,
        "issue":            query,
        "live_context":     live_context,
        # Pre-populate health hint from context so agents have a starting point
        "health_score":     None,
        "risk_level":       None,
        "primary_cause":    "",
        "failure_probability": 0,
        "rul_days":         60,
    }

    # Extract health score from live_context if available
    if ctx_eq == eq and live_context:
        import re
        m = re.search(r'Health\s+(\d+)%.*?Risk:\s*(\w+)', live_context)
        if m:
            agent_context["health_score"] = int(m.group(1))
            agent_context["risk_level"]   = m.group(2)

    # ── Select and run agents ──────────────────────────────────────────
    agent_names = INTENT_AGENTS.get(intent, INTENT_AGENTS["general"])
    agent_results = await run_agents(agent_names, agent_context)

    # ── Enrich context with agent results ─────────────────────────────
    if "sensor" in agent_results and agent_results["sensor"].success:
        sd = agent_results["sensor"].data or {}
        if not sensor_readings and sd.get("sensor_readings"):
            sensor_readings = sd["sensor_readings"]
        agent_context["health_score"] = sd.get("health_score") or agent_context["health_score"]
        agent_context["risk_level"]   = sd.get("risk_level",   agent_context.get("risk_level", "Unknown"))
        agent_context["sensor_readings"] = sensor_readings

    if "prediction" in agent_results and agent_results["prediction"].success:
        pd = agent_results["prediction"].data or {}
        agent_context["failure_probability"] = pd.get("failure_probability", 0)
        agent_context["rul_days"]            = pd.get("rul_days", 60)
        agent_context["risk_level"]          = pd.get("risk_level", agent_context.get("risk_level","Low"))

    if "rca" in agent_results and agent_results["rca"].success:
        rd = agent_results["rca"].data or {}
        agent_context["primary_cause"] = rd.get("primary_cause", "")

    # Run inventory + recommendation with enriched context
    extra_agents = []
    if "inventory" not in agent_results and intent in ("diagnosis", "general", "maintenance", "alert"):
        extra_agents.append("inventory")
    if "recommendation" not in agent_results and intent in ("diagnosis", "general", "alert"):
        extra_agents.append("recommendation")
    if extra_agents:
        extra_results = await run_agents(extra_agents, agent_context)
        agent_results.update(extra_results)

    # ── Build synthesis prompt ─────────────────────────────────────────
    from app.config import settings
    from groq import Groq

    synthesis_prompt = build_synthesis_prompt(query, agent_results, agent_context)

    system_prompt = (
        "You are a Senior Industrial Maintenance Engineer and Agentic AI for a steel manufacturing plant. "
        "Your PRIMARY job is to detect anomalies from live sensor data and guide maintenance technicians. "
        "When sensors are in CRITICAL or WARNING state, immediately diagnose the problem, identify root cause, "
        "and provide step-by-step resolution guidance. "
        "Synthesize the multi-agent analysis outputs into a clear, actionable maintenance response. "
        "Use plain text only — no ** bold, no ## headers, no markdown. "
        "Use UPPERCASE for section names (DIAGNOSIS:, ROOT CAUSE:, IMMEDIATE ACTIONS:, REPAIR PROCEDURE:). "
        "Use numbers and dashes for lists. Be specific with values, thresholds, part numbers, and procedures. "
        "If critical sensors are detected, lead with CRITICAL ALERT and prioritize immediate safety actions."
    )

    messages = [{"role": "system", "content": system_prompt}]
    for h in conversation_history[-6:]:
        messages.append({"role": h["role"], "content": h["content"]})
    messages.append({"role": "user", "content": synthesis_prompt})

    try:
        client = Groq(api_key=settings.GROQ_API_KEY)
        completion = client.chat.completions.create(
            model=settings.LLM_MODEL,
            messages=messages,
            temperature=0.2,
            max_tokens=1800,
        )
        answer = completion.choices[0].message.content.strip()
        tokens = completion.usage.total_tokens if completion.usage else 0
    except Exception as e:
        answer = f"Agent analysis complete but synthesis failed: {str(e)}"
        tokens = 0

    total_ms = (time.time() - t0) * 1000

    return {
        "answer":          answer,
        "intent":          intent,
        "equipment_name":  eq,
        "agents_invoked":  list(agent_results.keys()),
        "agent_results":   {k: v.to_dict() for k, v in agent_results.items()},
        "summary": {
            "health_score":        agent_context.get("health_score"),
            "failure_probability": agent_context.get("failure_probability"),
            "rul_days":            agent_context.get("rul_days"),
            "risk_level":          agent_context.get("risk_level"),
            "primary_cause":       agent_context.get("primary_cause"),
        },
        "tokens_used": tokens,
        "total_ms":    round(total_ms, 1),
    }
