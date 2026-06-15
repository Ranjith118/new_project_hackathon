"""Pydantic schemas for RAG and document processing APIs."""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


# ============ Document Schemas ============

class DocumentBase(BaseModel):
    """Base document schema."""
    document_name: str = Field(..., min_length=1, max_length=500)
    document_type: str = Field(..., pattern="^(manual|sop|maintenance_log|failure_report|sensor_data|other)$")
    description: Optional[str] = None
    tags: Optional[List[str]] = []


class DocumentCreate(DocumentBase):
    """Schema for creating a document record."""
    file_path: str
    file_size: int
    file_type: str


class DocumentUpdate(BaseModel):
    """Schema for updating a document."""
    document_name: Optional[str] = Field(None, min_length=1, max_length=500)
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    processing_status: Optional[str] = None


class DocumentResponse(DocumentBase):
    """Schema for document response."""
    document_id: str
    file_path: str
    file_size: int
    file_type: str
    processing_status: str
    total_chunks: int
    indexed_chunks: int
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class DocumentListResponse(BaseModel):
    """Schema for paginated document list."""
    documents: List[DocumentResponse]
    total: int
    page: int
    page_size: int


# ============ Upload Schemas ============

class DocumentUploadRequest(BaseModel):
    """Schema for document upload request."""
    document_name: str = Field(..., min_length=1, max_length=500)
    document_type: str = Field(..., pattern="^(manual|sop|maintenance_log|failure_report|sensor_data|other)$")
    description: Optional[str] = None
    tags: Optional[List[str]] = []


class DocumentUploadResponse(BaseModel):
    """Schema for document upload response."""
    document_id: str
    document_name: str
    file_path: str
    status: str
    message: str


# ============ Processing Schemas ============

class DocumentProcessRequest(BaseModel):
    """Schema for document processing request."""
    document_id: str
    chunk_size: int = Field(default=500, ge=100, le=2000)
    chunk_overlap: int = Field(default=50, ge=0, le=200)


class DocumentProcessResponse(BaseModel):
    """Schema for document processing response."""
    document_id: str
    status: str
    total_chunks: int
    indexed_chunks: int
    processing_time_ms: float
    errors: Optional[List[str]] = None


# ============ Chat Schemas ============

class ChatMessageSchema(BaseModel):
    """Schema for a chat message."""
    role: str = Field(..., pattern="^(user|assistant|system)$")
    content: str
    metadata: Optional[Dict[str, Any]] = None


class ChatRequest(BaseModel):
    """Schema for chat request."""
    question: str = Field(..., min_length=1, max_length=2000)
    conversation_id: Optional[str] = None
    document_type_filter: Optional[str] = Field(None, pattern="^(manual|sop|maintenance_log|failure_report|sensor_data|all)$")
    max_results: int = Field(default=5, ge=1, le=20)


class ChatResponseSchema(BaseModel):
    """Schema for chat response."""
    answer: str
    sources: List[str]
    references: List[Dict[str, Any]]
    confidence_score: float
    model_used: str
    tokens_used: int
    processing_time_ms: float
    retrieved_chunks: List[Dict[str, Any]]
    conversation_id: str


class ChatHistoryResponse(BaseModel):
    """Schema for chat history response."""
    conversation_id: str
    messages: List[ChatMessageSchema]
    created_at: datetime


# ============ Search Schemas ============

class DocumentSearchRequest(BaseModel):
    """Schema for document search request."""
    query: str = Field(..., min_length=1, max_length=500)
    document_type: Optional[str] = Field(None, pattern="^(manual|sop|maintenance_log|failure_report|sensor_data|all)$")
    max_results: int = Field(default=10, ge=1, le=50)


class SearchResultSchema(BaseModel):
    """Schema for a single search result."""
    chunk_id: str
    content: str
    source_document: str
    document_type: str
    similarity_score: float
    metadata: Dict[str, Any]


class DocumentSearchResponse(BaseModel):
    """Schema for document search response."""
    query: str
    results: List[SearchResultSchema]
    total_results: int
    retrieval_time_ms: float


# ============ Index Management Schemas ============

class ReindexRequest(BaseModel):
    """Schema for reindexing documents."""
    document_id: Optional[str] = None  # None means reindex all
    chunk_size: int = Field(default=500, ge=100, le=2000)
    chunk_overlap: int = Field(default=50, ge=0, le=200)


class ReindexResponse(BaseModel):
    """Schema for reindex response."""
    status: str
    documents_reindexed: int
    total_chunks: int
    processing_time_ms: float


class IndexStatsResponse(BaseModel):
    """Schema for index statistics."""
    collection_name: str
    total_documents: int
    total_chunks: int
    document_types: Dict[str, int]
    last_updated: Optional[datetime]


# ============ Explainability Schemas ============

class ExplanationSchema(BaseModel):
    """Schema for AI explainability."""
    confidence_level: str
    reasoning: str
    supporting_sources: List[str]
    confidence_breakdown: Dict[str, float]


class MaintenanceGuidanceSchema(BaseModel):
    """Schema for structured maintenance guidance."""
    probable_causes: List[str]
    recommended_actions: List[str]
    safety_considerations: List[str]
    additional_info: Optional[str] = None
    sources: List[str]
    confidence: float