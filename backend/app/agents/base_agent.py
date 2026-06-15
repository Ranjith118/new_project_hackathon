"""Base agent class for all maintenance agents."""
from typing import Any, Dict, Optional


class AgentResult:
    """Standardized output from any agent."""
    def __init__(self, agent_name: str = "", success: bool = True,
                 data: Dict[str, Any] = None, error: str = None,
                 execution_ms: float = 0.0):
        self.agent_name   = agent_name
        self.success      = success
        self.data         = data or {}
        self.error        = error
        self.execution_ms = execution_ms

    def to_dict(self) -> dict:
        return {
            "agent":        self.agent_name,
            "success":      self.success,
            "data":         self.data,
            "error":        self.error,
            "execution_ms": round(self.execution_ms, 1),
        }


class BaseAgent:
    name: str = "base"

    async def run(self, context: Dict[str, Any]) -> AgentResult:
        raise NotImplementedError
