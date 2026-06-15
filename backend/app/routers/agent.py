"""Agentic AI Maintenance Assistant API."""
import json
from typing import Optional, List, Dict
from fastapi import APIRouter, Form
from app.agents.orchestrator import orchestrate

router = APIRouter(prefix="/api/agent", tags=["Agentic AI"])

# In-memory conversation store  {session_id: [messages]}
_conversations: Dict[str, List[Dict]] = {}


@router.post("/chat")
async def agent_chat(
    message: str = Form(...),
    session_id: str = Form(default="default"),
    equipment_name: str = Form(default=""),
    sensor_readings: str = Form(default="{}"),
    live_context: str = Form(default=""),
):
    """
    Agentic AI chat endpoint.
    Orchestrates multiple specialized agents and returns a unified response.
    """
    # Parse sensor readings
    try:
        readings = json.loads(sensor_readings) if sensor_readings else {}
    except Exception:
        readings = {}

    # Get conversation history
    history = _conversations.get(session_id, [])

    # Run orchestration
    result = await orchestrate(
        query=message,
        conversation_history=history,
        equipment_name=equipment_name,
        sensor_readings=readings,
        live_context=live_context,
    )

    # Update conversation history
    history.append({"role": "user", "content": message})
    history.append({"role": "assistant", "content": result["answer"]})
    # Keep last 20 messages
    _conversations[session_id] = history[-20:]

    return result


@router.delete("/chat/{session_id}")
async def clear_conversation(session_id: str):
    """Clear conversation history for a session."""
    _conversations.pop(session_id, None)
    return {"status": "cleared", "session_id": session_id}


@router.get("/agents")
async def list_agents():
    """List all available agents."""
    return {
        "agents": [
            {"id": "sensor",          "name": "Sensor Analysis Agent",           "description": "Analyzes sensor data and detects abnormalities"},
            {"id": "prediction",      "name": "Failure Prediction Agent",        "description": "Predicts failure probability and RUL using ML models"},
            {"id": "rca",             "name": "Root Cause Analysis Agent",       "description": "Identifies probable failure causes with evidence"},
            {"id": "document",        "name": "Document Intelligence Agent",     "description": "Searches manuals, SOPs, and maintenance records via RAG"},
            {"id": "inventory",       "name": "Inventory Agent",                 "description": "Checks spare availability and procurement needs"},
            {"id": "recommendation",  "name": "Maintenance Recommendation Agent","description": "Generates immediate actions and long-term plans"},
            {"id": "reporting",       "name": "Reporting Agent",                 "description": "Creates maintenance reports and decision summaries"},
        ],
        "orchestrator": "Auto-selects agents based on query intent"
    }
