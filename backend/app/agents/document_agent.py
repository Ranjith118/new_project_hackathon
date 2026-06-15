"""Document Intelligence Agent — searches manuals, SOPs, maintenance records via RAG."""
import time
from typing import Dict, Any
from app.agents.base_agent import BaseAgent, AgentResult


class DocumentIntelligenceAgent(BaseAgent):
    name = "document_intelligence"

    async def run(self, context: Dict[str, Any]) -> AgentResult:
        t0 = time.time()
        query = context.get("query", "")
        eq = context.get("equipment_name", "")
        try:
            from app.rag.retrieval import get_retrieval_engine
            engine = get_retrieval_engine()
            search_query = f"{eq} {query}".strip() if eq else query
            result = engine.retrieve(search_query, top_k=6)

            chunks = []
            for c in result.chunks[:5]:
                chunks.append({
                    "source": c.source_document,
                    "type": c.document_type,
                    "equipment": c.metadata.get("equipment_name", ""),
                    "relevance": round(c.similarity_score * 100, 1),
                    "excerpt": c.content[:200] + ("..." if len(c.content) > 200 else ""),
                })

            sources = list({c["source"] for c in chunks})
            return AgentResult(agent_name=self.name, success=True, data={
                "chunks_found": result.total_chunks,
                "avg_relevance": round(result.avg_score * 100, 1),
                "sources": sources,
                "relevant_excerpts": chunks,
                "has_manual": any("manual" in c["type"].lower() for c in chunks if c["type"]),
                "has_sop": any("sop" in c["type"].lower() for c in chunks if c["type"]),
            }, execution_ms=(time.time()-t0)*1000)
        except Exception as e:
            return AgentResult(agent_name=self.name, success=False, error=str(e), execution_ms=(time.time()-t0)*1000)
