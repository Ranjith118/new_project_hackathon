"""Retrieval engine for semantic search and context retrieval."""
from typing import List, Optional, Dict, Any, Tuple
from dataclasses import dataclass
from datetime import datetime

from app.services.vector_db.chroma_service import get_vector_store


@dataclass
class RetrievedChunk:
    """Represents a retrieved document chunk with metadata."""
    chunk_id: str
    content: str
    source_document: str
    document_type: str
    similarity_score: float
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'chunk_id': self.chunk_id,
            'content': self.content,
            'source_document': self.source_document,
            'document_type': self.document_type,
            'similarity_score': round(self.similarity_score, 4),
            'metadata': self.metadata
        }


@dataclass
class RetrievalResult:
    """Contains the retrieval results with summary statistics."""
    query: str
    chunks: List[RetrievedChunk]
    total_chunks: int
    max_score: float
    avg_score: float
    retrieval_time_ms: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'query': self.query,
            'chunks': [chunk.to_dict() for chunk in self.chunks],
            'total_chunks': self.total_chunks,
            'max_score': round(self.max_score, 4),
            'avg_score': round(self.avg_score, 4),
            'retrieval_time_ms': round(self.retrieval_time_ms, 2)
        }
    
    def get_context_for_llm(self, max_chunks: int = 5) -> str:
        """Format retrieved chunks into context for LLM."""
        if not self.chunks:
            return "No relevant information found."
        
        chunks_to_use = self.chunks[:max_chunks]
        
        context_parts = []
        for i, chunk in enumerate(chunks_to_use, 1):
            context_parts.append(
                f"[Source {i}]: {chunk.source_document}\n"
                f"Type: {chunk.document_type}\n"
                f"Content: {chunk.content}\n"
            )
        
        return "\n---\n".join(context_parts)


class RetrievalEngine:
    """
    Semantic search and retrieval engine for the maintenance knowledge base.
    
    Handles query processing, chunk retrieval, and result formatting.
    """
    
    def __init__(self, top_k: int = 5, min_score: float = 0.0):
        """
        Initialize the retrieval engine.
        
        Args:
            top_k: Number of top chunks to retrieve
            min_score: Minimum similarity score threshold
        """
        self.top_k = top_k
        self.min_score = min_score
        self.vector_store = get_vector_store()
    
    def retrieve(self, query: str, top_k: Optional[int] = None) -> RetrievalResult:
        """
        Retrieve relevant document chunks for a query.
        
        Args:
            query: User query string
            top_k: Override default number of results
            
        Returns:
            RetrievalResult with retrieved chunks and statistics
        """
        import time
        start_time = time.time()
        
        # Determine number of results
        k = top_k or self.top_k
        
        # Perform similarity search
        raw_results = self.vector_store.similarity_search(
            query=query,
            n_results=k * 2  # Get more than needed for filtering
        )
        
        # Process and filter results
        chunks = []
        for result in raw_results:
            score = result.get('score', 0)
            
            # Filter by minimum score
            if score >= self.min_score:
                chunk = RetrievedChunk(
                    chunk_id=result.get('id', ''),
                    content=result.get('content', ''),
                    source_document=result.get('metadata', {}).get('document_name', 'Unknown'),
                    document_type=result.get('metadata', {}).get('document_type', 'unknown'),
                    similarity_score=score,
                    metadata=result.get('metadata', {})
                )
                chunks.append(chunk)
        
        # Limit to top_k
        chunks = chunks[:k]
        
        # Calculate statistics
        retrieval_time = (time.time() - start_time) * 1000
        
        max_score = max([c.similarity_score for c in chunks], default=0)
        avg_score = sum([c.similarity_score for c in chunks]) / len(chunks) if chunks else 0
        
        return RetrievalResult(
            query=query,
            chunks=chunks,
            total_chunks=len(chunks),
            max_score=max_score,
            avg_score=avg_score,
            retrieval_time_ms=retrieval_time
        )
    
    def retrieve_by_type(
        self, 
        query: str, 
        document_type: str, 
        top_k: Optional[int] = None
    ) -> RetrievalResult:
        """
        Retrieve documents filtered by type.
        
        Args:
            query: User query string
            document_type: Type of documents to search
            top_k: Number of results
            
        Returns:
            RetrievalResult with filtered results
        """
        import time
        start_time = time.time()
        
        k = top_k or self.top_k
        
        # Search with type filter
        raw_results = self.vector_store.similarity_search(
            query=query,
            n_results=k * 2,
            where={"document_type": document_type}
        )
        
        chunks = []
        for result in raw_results:
            score = result.get('score', 0)
            if score >= self.min_score:
                chunk = RetrievedChunk(
                    chunk_id=result.get('id', ''),
                    content=result.get('content', ''),
                    source_document=result.get('metadata', {}).get('document_name', 'Unknown'),
                    document_type=document_type,
                    similarity_score=score,
                    metadata=result.get('metadata', {})
                )
                chunks.append(chunk)
        
        chunks = chunks[:k]
        
        retrieval_time = (time.time() - start_time) * 1000
        
        max_score = max([c.similarity_score for c in chunks], default=0)
        avg_score = sum([c.similarity_score for c in chunks]) / len(chunks) if chunks else 0
        
        return RetrievalResult(
            query=query,
            chunks=chunks,
            total_chunks=len(chunks),
            max_score=max_score,
            avg_score=avg_score,
            retrieval_time_ms=retrieval_time
        )
    
    def multi_query_retrieval(
        self,
        queries: List[str],
        top_k: Optional[int] = None
    ):
        """
        Perform retrieval for multiple queries and merge results.
        
        Args:
            queries: List of query strings
            top_k: Number of results per query
            
        Returns:
            List of RetrievalResults
        """
        results = []
        seen_ids = set()
        merged_chunks = []
        
        for query in queries:
            result = self.retrieve(query, top_k)
            results.append(result)
            
            # Collect unique chunks
            for chunk in result.chunks:
                if chunk.chunk_id not in seen_ids:
                    seen_ids.add(chunk.chunk_id)
                    merged_chunks.append(chunk)
        
        return results
    
    def get_confidence_level(self, avg_score: float) -> str:
        """
        Determine confidence level based on average score.
        
        Args:
            avg_score: Average similarity score
            
        Returns:
            Confidence level string
        """
        if avg_score >= 0.8:
            return "high"
        elif avg_score >= 0.6:
            return "medium"
        elif avg_score >= 0.4:
            return "low"
        else:
            return "very_low"


# Singleton instance
_retrieval_engine: Optional[RetrievalEngine] = None


def get_retrieval_engine() -> RetrievalEngine:
    """Get or create the global retrieval engine instance."""
    global _retrieval_engine
    if _retrieval_engine is None:
        _retrieval_engine = RetrievalEngine()
    return _retrieval_engine