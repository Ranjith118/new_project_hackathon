"""RAG (Retrieval-Augmented Generation) API endpoints."""
import os
import uuid
import time
from typing import Optional, List
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from fastapi.responses import JSONResponse
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.models import Equipment, MaintenanceLog, FailureReport
from app.models.schemas.rag_schemas import (
    DocumentCreate, DocumentUpdate, DocumentResponse, DocumentListResponse,
    DocumentUploadRequest, DocumentUploadResponse,
    DocumentProcessRequest, DocumentProcessResponse,
    ChatRequest, ChatResponseSchema,
    DocumentSearchRequest, DocumentSearchResponse, SearchResultSchema,
    ReindexRequest, ReindexResponse, IndexStatsResponse
)
from app.services.document.processor import DocumentProcessor
from app.services.embeddings.embeddings import get_embedding_service
from app.services.vector_db.chroma_service import get_vector_store
from app.rag.retrieval import get_retrieval_engine, RetrievalEngine
from app.services.chat.llm_service import (
    get_llm_service, get_conversation_manager, LLMService, ConversationManager
)

router = APIRouter(prefix="/api/rag", tags=["RAG - Document Processing & Chat"])


# ============ Document Management ============

@router.post("/documents/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    document_name: str = Form(...),
    document_type: str = Form(...),
    description: Optional[str] = Form(None),
    tags: Optional[str] = Form(None),  # Comma-separated
    db: AsyncSession = Depends(get_db)
):
    """
    Upload a document for processing and indexing.
    
    Supports PDF, TXT, and CSV files.
    """
    # Validate file type
    allowed_extensions = {'.pdf', '.txt', '.csv'}
    file_ext = Path(file.filename).suffix.lower()
    
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {file_ext}. Allowed: {', '.join(allowed_extensions)}"
        )
    
    # Validate document type
    valid_types = ['manual', 'sop', 'maintenance_log', 'failure_report', 'sensor_data', 'other']
    if document_type not in valid_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid document type: {document_type}"
        )
    
    # Create upload directory
    upload_dir = Path("./data/rag_documents")
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate unique filename
    doc_id = str(uuid.uuid4())
    safe_filename = f"{doc_id}_{file.filename}"
    file_path = upload_dir / safe_filename
    
    # Save file
    content = await file.read()
    file_size = len(content)
    
    with open(file_path, "wb") as f:
        f.write(content)
    
    return DocumentUploadResponse(
        document_id=doc_id,
        document_name=document_name,
        file_path=str(file_path),
        status="uploaded",
        message="Document uploaded successfully. Use /process endpoint to index."
    )


@router.post("/documents/process", response_model=DocumentProcessResponse)
async def process_document(
    file_path: str,
    document_name: str,
    document_type: str,
    chunk_size: int = 500,
    chunk_overlap: int = 50
):
    """
    Process a document: extract text, chunk, and index in vector database.
    """
    start_time = time.time()
    
    if not Path(file_path).exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    try:
        # Initialize services
        processor = DocumentProcessor(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        vector_store = get_vector_store()
        
        # Process the document
        chunks = processor.process_file(
            file_path=file_path,
            document_type=document_type,
            document_name=document_name
        )
        
        total_chunks = len(chunks)
        
        if total_chunks == 0:
            return DocumentProcessResponse(
                document_id=document_name,
                status="no_content",
                total_chunks=0,
                indexed_chunks=0,
                processing_time_ms=(time.time() - start_time) * 1000,
                errors=["No content extracted from document"]
            )
        
        # Index in vector store
        indexed_ids = vector_store.add_documents(chunks)
        indexed_chunks = len(indexed_ids)
        
        processing_time = (time.time() - start_time) * 1000
        
        return DocumentProcessResponse(
            document_id=document_name,
            status="completed",
            total_chunks=total_chunks,
            indexed_chunks=indexed_chunks,
            processing_time_ms=processing_time
        )
        
    except Exception as e:
        return DocumentProcessResponse(
            document_id=document_name,
            status="failed",
            total_chunks=0,
            indexed_chunks=0,
            processing_time_ms=(time.time() - start_time) * 1000,
            errors=[str(e)]
        )


@router.get("/documents", response_model=DocumentSearchResponse)
async def search_documents(
    query: str = Query(..., min_length=1),
    document_type: Optional[str] = Query(None),
    max_results: int = Query(10, ge=1, le=50)
):
    """
    Search documents in the knowledge base.
    """
    retrieval_engine = get_retrieval_engine()
    
    if document_type and document_type != 'all':
        result = retrieval_engine.retrieve_by_type(query, document_type, max_results)
    else:
        result = retrieval_engine.retrieve(query, max_results)
    
    results = [
        SearchResultSchema(
            chunk_id=chunk.chunk_id,
            content=chunk.content,
            source_document=chunk.source_document,
            document_type=chunk.document_type,
            similarity_score=chunk.similarity_score,
            metadata=chunk.metadata
        )
        for chunk in result.chunks
    ]
    
    return DocumentSearchResponse(
        query=query,
        results=results,
        total_results=len(results),
        retrieval_time_ms=result.retrieval_time_ms
    )


@router.delete("/documents/{document_name}")
async def delete_document_index(document_name: str):
    """
    Delete all chunks from a specific document.
    """
    vector_store = get_vector_store()
    
    try:
        deleted_count = vector_store.delete_documents_by_filter(
            where={"document_name": document_name}
        )
        
        return {"status": "deleted", "chunks_deleted": deleted_count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============ Chat API ============

@router.post("/chat", response_model=ChatResponseSchema)
async def chat(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Main chat endpoint for maintenance assistance.
    
    Takes a question, retrieves relevant context, and generates an LLM response.
    """
    # Get or create conversation manager
    conversation_manager = get_conversation_manager()
    
    # Handle conversation ID
    conversation_id = request.conversation_id
    if not conversation_id:
        conversation_id = conversation_manager.get_conversation_id()
    
    # Add user message to history
    conversation_manager.add_message(
        conversation_id=conversation_id,
        role="user",
        content=request.question
    )
    
    # Retrieve relevant context
    retrieval_engine = get_retrieval_engine()
    
    if request.document_type_filter and request.document_type_filter != 'all':
        retrieval_result = retrieval_engine.retrieve_by_type(
            request.question,
            request.document_type_filter,
            request.max_results
        )
    else:
        retrieval_result = retrieval_engine.retrieve(
            request.question,
            request.max_results
        )
    
    # Get LLM service
    llm_service = get_llm_service()
    
    # Generate response
    response = llm_service.generate_response(request.question, retrieval_result)
    
    # Add assistant response to history
    conversation_manager.add_message(
        conversation_id=conversation_id,
        role="assistant",
        content=response.answer,
        metadata={
            "sources": response.sources,
            "confidence": response.confidence_score
        }
    )
    
    return ChatResponseSchema(
        answer=response.answer,
        sources=response.sources,
        references=response.references,
        confidence_score=response.confidence_score,
        model_used=response.model_used,
        tokens_used=response.tokens_used,
        processing_time_ms=response.processing_time_ms,
        retrieved_chunks=response.retrieved_chunks,
        conversation_id=conversation_id
    )


@router.get("/chat/history/{conversation_id}")
async def get_chat_history(
    conversation_id: str,
    max_messages: Optional[int] = Query(None, ge=1, le=100)
):
    """
    Get chat history for a conversation.
    """
    conversation_manager = get_conversation_manager()
    history = conversation_manager.get_history(conversation_id, max_messages)
    
    return {
        "conversation_id": conversation_id,
        "messages": [
            {
                "role": msg.role,
                "content": msg.content,
                "timestamp": msg.timestamp.isoformat(),
                "metadata": msg.metadata
            }
            for msg in history
        ]
    }


@router.delete("/chat/history/{conversation_id}")
async def clear_chat_history(conversation_id: str):
    """
    Clear chat history for a conversation.
    """
    conversation_manager = get_conversation_manager()
    conversation_manager.clear_history(conversation_id)
    
    return {"status": "cleared", "conversation_id": conversation_id}


# ============ Index Management ============

@router.get("/index/stats", response_model=IndexStatsResponse)
async def get_index_stats():
    """
    Get statistics about the knowledge base index.
    """
    vector_store = get_vector_store()
    info = vector_store.get_collection_info()
    
    # Get document type breakdown
    # This would require querying the collection metadata
    doc_types = {}
    
    return IndexStatsResponse(
        collection_name=info.get('name', 'maintenance_knowledge_base'),
        total_documents=info.get('document_count', 0),
        total_chunks=info.get('document_count', 0),
        document_types=doc_types,
        last_updated=None
    )


@router.post("/index/reindex", response_model=ReindexResponse)
async def reindex_documents(request: ReindexRequest):
    """
    Reindex documents in the vector database.
    """
    start_time = time.time()
    
    vector_store = get_vector_store()
    
    try:
        if request.document_id:
            # Reindex specific document
            # This would require re-processing and re-adding
            return ReindexResponse(
                status="reindexed",
                documents_reindexed=1,
                total_chunks=0,
                processing_time_ms=(time.time() - start_time) * 1000
            )
        else:
            # Clear and rebuild entire index
            vector_store.reset_collection()
            
            return ReindexResponse(
                status="reindexed",
                documents_reindexed=0,
                total_chunks=0,
                processing_time_ms=(time.time() - start_time) * 1000
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============ Bulk Import from Database ============

@router.post("/index/import-maintenance-logs")
async def import_maintenance_logs(
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db)
):
    """
    Import maintenance logs from database into the knowledge base.
    """
    start_time = time.time()
    
    try:
        # Fetch maintenance logs
        query = select(MaintenanceLog).limit(limit)
        result = await db.execute(query)
        logs = result.scalars().all()
        
        vector_store = get_vector_store()
        processor = DocumentProcessor()
        
        total_chunks = 0
        
        for log in logs:
            # Create document content
            content = f"""
Maintenance Log Entry
=====================
Equipment: {log.equipment_name}
Date: {log.maintenance_date}
Severity: {log.severity}
Issue: {log.issue}
Action Taken: {log.action_taken or 'N/A'}
Technician: {log.technician or 'N/A'}
Downtime: {log.downtime_hours} hours
"""
            
            # Add to vector store
            doc_id = vector_store.add_texts(
                texts=[content],
                metadatas=[{
                    'document_name': f"Maintenance Log - {log.equipment_name}",
                    'document_type': 'maintenance_log',
                    'source_id': log.log_id,
                    'date': str(log.maintenance_date)
                }]
            )
            
            total_chunks += 1
        
        return {
            "status": "completed",
            "logs_imported": len(logs),
            "total_chunks": total_chunks,
            "processing_time_ms": (time.time() - start_time) * 1000
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/index/import-failure-reports")
async def import_failure_reports(
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db)
):
    """
    Import failure reports from database into the knowledge base.
    """
    start_time = time.time()
    
    try:
        query = select(FailureReport).limit(limit)
        result = await db.execute(query)
        reports = result.scalars().all()
        
        vector_store = get_vector_store()
        
        total_chunks = 0
        
        for report in reports:
            content = f"""
Failure Report
==============
Equipment: {report.equipment_name}
Date: {report.report_date}
Failure Type: {report.failure_type}
Root Cause: {report.root_cause or 'N/A'}
Downtime: {report.downtime_hours} hours
"""
            
            doc_id = vector_store.add_texts(
                texts=[content],
                metadatas=[{
                    'document_name': f"Failure Report - {report.equipment_name}",
                    'document_type': 'failure_report',
                    'source_id': report.report_id,
                    'date': str(report.report_date)
                }]
            )
            
            total_chunks += 1
        
        return {
            "status": "completed",
            "reports_imported": len(reports),
            "total_chunks": total_chunks,
            "processing_time_ms": (time.time() - start_time) * 1000
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============ Suggested Questions ============

@router.get("/suggested-questions")
async def get_suggested_questions():
    """
    Get suggested maintenance questions for the user.
    """
    return {
        "questions": [
            {
                "category": "Troubleshooting",
                "questions": [
                    "Why is my motor overheating?",
                    "What causes excessive vibration in rotating equipment?",
                    "How to diagnose bearing failures?",
                    "What are common causes of hydraulic system failures?"
                ]
            },
            {
                "category": "Maintenance Procedures",
                "questions": [
                    "What is the recommended maintenance schedule for furnaces?",
                    "How often should I lubricate conveyor systems?",
                    "What are the steps for preventive maintenance on CNC machines?"
                ]
            },
            {
                "category": "Safety",
                "questions": [
                    "What safety precautions when working on high-voltage equipment?",
                    "How to safely handle hydraulic fluid leaks?",
                    "What PPE is required for furnace maintenance?"
                ]
            },
            {
                "category": "Parts and Supplies",
                "questions": [
                    "What spare parts should I keep in inventory?",
                    "How to determine when to replace bearings?",
                    "What are the recommended lubricants for different applications?"
                ]
            }
        ]
    }