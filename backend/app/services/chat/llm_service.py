"""LLM Integration service - supports Groq, OpenAI, and Ollama."""
import os
import time
import uuid
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime

from app.rag.retrieval import RetrievalResult, RetrievedChunk


@dataclass
class ChatMessage:
    """Represents a chat message."""
    role: str  # 'user', 'assistant', 'system'
    content: str
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            'role': self.role,
            'content': self.content,
            'timestamp': self.timestamp.isoformat(),
            'metadata': self.metadata
        }


@dataclass
class ChatResponse:
    """Represents the LLM chat response."""
    answer: str
    sources: List[str]
    references: List[Dict[str, Any]]
    confidence_score: float
    model_used: str
    tokens_used: int
    processing_time_ms: float
    retrieved_chunks: List[Dict[str, Any]]

    def to_dict(self) -> Dict[str, Any]:
        return {
            'answer': self.answer,
            'sources': self.sources,
            'references': self.references,
            'confidence_score': round(self.confidence_score, 4),
            'model_used': self.model_used,
            'tokens_used': self.tokens_used,
            'processing_time_ms': round(self.processing_time_ms, 2),
            'retrieved_chunks': self.retrieved_chunks
        }


class MaintenancePromptTemplate:
    """Prompt templates for the maintenance expert system."""

    SYSTEM_PROMPT = """You are an Industrial Maintenance Expert assistant for a steel manufacturing plant.

STRICT SCOPE: You ONLY answer questions about industrial maintenance, equipment health, machine failures,
sensor readings, spare parts, maintenance procedures, root cause analysis, safety, and steel plant operations.

If a question is NOT related to industrial maintenance or steel plant operations, respond with:
"I can only assist with industrial maintenance and steel plant operations. Please ask me about
equipment health, failures, maintenance procedures, spare parts, or plant operations."

For valid maintenance questions, use the provided context and structure responses with:
Probable Causes, Recommended Actions, Safety Considerations, and References.
Prioritize safety. Be specific and technical."""

    @staticmethod
    def build_context_prompt(retrieval_result: RetrievalResult) -> str:
        if not retrieval_result.chunks:
            return "No relevant information available in the knowledge base."

        parts = ["## Retrieved Information\n"]
        for i, chunk in enumerate(retrieval_result.chunks, 1):
            parts.append(
                f"### Source {i}: {chunk.source_document}\n"
                f"- Type: {chunk.document_type}\n"
                f"- Relevance: {chunk.similarity_score:.2%}\n"
                f"- Content:\n{chunk.content}\n"
            )
        return "\n".join(parts)

    @staticmethod
    def build_user_prompt(question: str, context: str) -> str:
        return (
            f"## Question\n{question}\n\n"
            f"## Available Context\n{context}\n\n"
            "## Your Task\n"
            "Based on the context, provide a comprehensive maintenance expert response. "
            "If context is insufficient, state what additional information is needed."
        )


class LLMService:
    """
    LLM service supporting Groq, OpenAI, and Ollama.
    """

    def __init__(
        self,
        provider: str = "groq",
        model_name: str = "llama3-8b-8192",
        temperature: float = 0.3,
        max_tokens: int = 2000,
    ):
        self.provider = provider
        self.model_name = model_name
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.client = None
        self._init_client()

    def _init_client(self):
        """Initialize the LLM client based on provider."""
        if self.provider == "groq":
            try:
                from groq import Groq
                from app.config import settings
                api_key = settings.GROQ_API_KEY or os.environ.get("GROQ_API_KEY", "")
                self.client = Groq(api_key=api_key)
            except ImportError:
                raise ImportError("groq package not installed. Run: pip install groq")

        elif self.provider == "openai":
            try:
                from openai import OpenAI
                from app.config import settings
                self.client = OpenAI(api_key=settings.OPENAI_API_KEY or os.environ.get("OPENAI_API_KEY", ""))
            except ImportError:
                raise ImportError("openai package not installed.")

        elif self.provider == "ollama":
            try:
                from openai import OpenAI
                self.client = OpenAI(
                    base_url="http://localhost:11434/v1",
                    api_key="ollama"
                )
            except ImportError:
                raise ImportError("openai package required for Ollama.")

    def generate_response(
        self,
        question: str,
        retrieval_result: RetrievalResult
    ) -> ChatResponse:
        """Generate a response based on question and retrieved context."""
        start_time = time.time()

        context = MaintenancePromptTemplate.build_context_prompt(retrieval_result)
        user_prompt = MaintenancePromptTemplate.build_user_prompt(question, context)
        confidence_score = retrieval_result.avg_score if retrieval_result.chunks else 0.0

        try:
            completion = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": MaintenancePromptTemplate.SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )
            answer = completion.choices[0].message.content
            tokens_used = completion.usage.total_tokens if completion.usage else 0

        except Exception as e:
            answer = (
                f"Error generating response: {str(e)}\n\n"
                "Please check your API key and try again."
            )
            tokens_used = 0

        processing_time = (time.time() - start_time) * 1000
        sources = list(set(c.source_document for c in retrieval_result.chunks))
        references = [
            {
                'source': c.source_document,
                'document_type': c.document_type,
                'score': c.similarity_score,
                'preview': c.content[:200] + ('...' if len(c.content) > 200 else '')
            }
            for c in retrieval_result.chunks
        ]

        return ChatResponse(
            answer=answer,
            sources=sources,
            references=references,
            confidence_score=confidence_score,
            model_used=self.model_name,
            tokens_used=tokens_used,
            processing_time_ms=processing_time,
            retrieved_chunks=[c.to_dict() for c in retrieval_result.chunks]
        )


class ConversationManager:
    """Manages conversation history for multi-turn interactions."""

    def __init__(self, max_history: int = 20):
        self.max_history = max_history
        self.conversations: Dict[str, List[ChatMessage]] = {}
        self.llm_service: Optional[LLMService] = None

    def set_llm_service(self, llm_service: LLMService):
        self.llm_service = llm_service

    def get_conversation_id(self) -> str:
        return str(uuid.uuid4())

    def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ChatMessage:
        if conversation_id not in self.conversations:
            self.conversations[conversation_id] = []

        message = ChatMessage(role=role, content=content, timestamp=datetime.now(), metadata=metadata)
        self.conversations[conversation_id].append(message)

        if len(self.conversations[conversation_id]) > self.max_history:
            self.conversations[conversation_id] = self.conversations[conversation_id][-self.max_history:]

        return message

    def get_history(self, conversation_id: str, max_messages: Optional[int] = None) -> List[ChatMessage]:
        history = self.conversations.get(conversation_id, [])
        return history[-max_messages:] if max_messages else history

    def clear_history(self, conversation_id: str):
        self.conversations.pop(conversation_id, None)

    def get_context_for_llm(self, conversation_id: str, retrieval_result: RetrievalResult) -> str:
        history = self.get_history(conversation_id, max_messages=10)
        parts = []
        if history:
            parts.append("## Recent Conversation History\n")
            for msg in history:
                label = "User" if msg.role == "user" else "Assistant"
                parts.append(f"**{label}**: {msg.content}\n")
        parts.append("\n## Retrieved Knowledge Base Information\n")
        parts.append(MaintenancePromptTemplate.build_context_prompt(retrieval_result))
        return "\n".join(parts)


# Singleton instances
_llm_service: Optional[LLMService] = None
_conversation_manager: Optional[ConversationManager] = None


def get_llm_service(provider: str = None, model_name: str = None) -> LLMService:
    """Get or create the global LLM service instance."""
    global _llm_service
    from app.config import settings

    p = provider or settings.LLM_PROVIDER
    m = model_name or settings.LLM_MODEL

    if _llm_service is None or _llm_service.provider != p or _llm_service.model_name != m:
        _llm_service = LLMService(provider=p, model_name=m)
    return _llm_service


def get_conversation_manager() -> ConversationManager:
    """Get or create the global conversation manager instance."""
    global _conversation_manager
    if _conversation_manager is None:
        _conversation_manager = ConversationManager()
    return _conversation_manager
