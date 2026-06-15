"""
AI-Powered Document Intelligence API.
Dynamically learns from every uploaded document.
No hardcoded knowledge — all extracted by AI from the document.
"""
import json
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.models import IntelligentDocument, DocumentKnowledge
from app.doc_intelligence.file_reader import read_file
from app.doc_intelligence.ai_analyzer import analyze_document
from app.doc_intelligence.chunker import chunk_text
from app.services.vector_db.chroma_service import get_vector_store
from app.services.chat.llm_service import get_llm_service, get_conversation_manager
from app.rag.retrieval import get_retrieval_engine

router = APIRouter(prefix="/api/doc-intelligence", tags=["Document Intelligence"])

UPLOAD_DIR = Path("./data/intelligent_docs")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED = {".pdf", ".docx", ".txt", ".csv"}


# ─────────────────────────────────────────────
# 1. UPLOAD + PROCESS
# ─────────────────────────────────────────────
@router.post("/upload")
async def upload_and_process(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    """
    Upload a document. AI will automatically:
    - Classify document type
    - Identify equipment
    - Extract all knowledge
    - Generate summaries
    - Chunk and index into vector DB
    """
    suffix = Path(file.filename).suffix.lower()
    if suffix not in ALLOWED:
        raise HTTPException(400, f"Unsupported type {suffix}. Allowed: {', '.join(ALLOWED)}")

    # Save file
    doc_id   = str(uuid.uuid4())
    saved_name = f"{doc_id}_{file.filename}"
    save_path  = UPLOAD_DIR / saved_name
    content    = await file.read()

    with open(save_path, "wb") as f:
        f.write(content)

    # Create DB record
    doc = IntelligentDocument(
        doc_id=doc_id,
        file_name=file.filename,
        file_path=str(save_path),
        file_type=suffix,
        file_size=len(content),
        processing_status="uploaded"
    )
    db.add(doc)
    await db.flush()
    await db.commit()   # persist so the record survives if process is called after a restart

    return {
        "doc_id": doc_id,
        "file_name": file.filename,
        "file_size": len(content),
        "status": "uploaded",
        "message": "File uploaded. Call /process/{doc_id} to start AI analysis."
    }


@router.post("/process/{doc_id}")
async def process_document(
    doc_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Run full AI analysis pipeline on an uploaded document.
    Steps: Read → Classify → Extract → Summarize → Chunk → Embed → Index
    """
    result = await db.execute(
        select(IntelligentDocument).where(IntelligentDocument.doc_id == doc_id)
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(404, "Document not found")
    if doc.processing_status == "completed":
        return {"doc_id": doc_id, "status": "already_processed",
                "message": "Document already processed"}

    doc.processing_status = "processing"
    await db.flush()

    try:
        # Step 1: Read file
        full_text, page_count = read_file(doc.file_path)
        if not full_text.strip():
            raise ValueError("No text could be extracted from file")

        # Step 2-4: AI Analysis (classify + extract + summarize)
        analysis = analyze_document(full_text, doc.file_name)

        classification = analysis["classification"]
        knowledge_data  = analysis["knowledge"]
        summaries       = analysis["summaries"]

        # Step 5: Update document record
        doc.document_type      = classification.get("document_type")
        doc.type_confidence    = classification.get("confidence")
        doc.equipment_name     = classification.get("equipment_name")
        doc.equipment_type     = classification.get("equipment_type")
        doc.manufacturer       = classification.get("manufacturer")
        doc.model_number       = classification.get("model_number")
        doc.keywords           = json.dumps(classification.get("keywords", []))
        doc.executive_summary  = summaries.get("executive_summary")
        doc.technical_summary  = summaries.get("technical_summary")
        doc.maintenance_summary = summaries.get("maintenance_summary")
        doc.page_count         = page_count
        doc.processed_date     = datetime.now()

        # Step 6: Store structured knowledge
        knowledge = DocumentKnowledge(
            doc_id=doc_id,
            equipment_name=doc.equipment_name or "Unknown",
            operating_conditions  = json.dumps(knowledge_data.get("operating_conditions", {})),
            fault_modes           = json.dumps(knowledge_data.get("fault_modes", [])),
            maintenance_tasks     = json.dumps(knowledge_data.get("maintenance_tasks", [])),
            safety_instructions   = json.dumps(knowledge_data.get("safety_instructions", [])),
            spare_parts           = json.dumps(knowledge_data.get("spare_parts", [])),
            sensor_thresholds     = json.dumps(knowledge_data.get("sensor_thresholds", {})),
            maintenance_intervals = json.dumps(knowledge_data.get("maintenance_intervals", {})),
            critical_components   = json.dumps(knowledge_data.get("critical_components", [])),
            inspection_checklist  = json.dumps(knowledge_data.get("inspection_checklist", [])),
            troubleshooting_procedures = json.dumps(knowledge_data.get("troubleshooting_procedures", [])),
        )
        db.add(knowledge)

        # Step 7: Chunk text
        chunks = chunk_text(
            text=full_text,
            document_id=doc_id,
            document_name=doc.file_name,
            document_type=doc.document_type or "Manual",
            equipment_name=doc.equipment_name or "Unknown",
            chunk_size=500,
            overlap=75,
        )

        # Step 8: Index chunks into ChromaDB
        vs = get_vector_store()
        texts     = [c["text"] for c in chunks]
        metadatas = [c["metadata"] for c in chunks]
        ids       = [c["id"] for c in chunks]

        if texts:
            vs.add_texts(texts=texts, metadatas=metadatas, ids=ids)

        doc.chunk_count        = len(chunks)
        doc.processing_status  = "completed"
        await db.flush()
        await db.commit()   # persist all changes so they survive a server restart

        return {
            "doc_id": doc_id,
            "status": "completed",
            "document_type": doc.document_type,
            "type_confidence": f"{(doc.type_confidence or 0)*100:.0f}%",
            "equipment_name": doc.equipment_name,
            "manufacturer": doc.manufacturer,
            "model_number": doc.model_number,
            "page_count": page_count,
            "chunk_count": len(chunks),
            "keywords": classification.get("keywords", []),
            "executive_summary": doc.executive_summary,
            "technical_summary": doc.technical_summary,
            "maintenance_summary": doc.maintenance_summary,
            "faults_extracted": len(knowledge_data.get("fault_modes", [])),
            "tasks_extracted":  len(knowledge_data.get("maintenance_tasks", [])),
            "parts_extracted":  len(knowledge_data.get("spare_parts", [])),
        }

    except Exception as e:
        doc.processing_status = "failed"
        doc.processing_error  = str(e)
        await db.flush()
        await db.commit()
        raise HTTPException(500, f"Processing failed: {str(e)}")


# ─────────────────────────────────────────────
# 2. LIST & GET DOCUMENTS
# ─────────────────────────────────────────────
@router.get("/documents")
async def list_documents(
    status: Optional[str] = None,
    equipment: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """List all intelligent documents."""
    query = select(IntelligentDocument).order_by(IntelligentDocument.upload_date.desc())
    result = await db.execute(query)
    docs = result.scalars().all()

    if status:
        docs = [d for d in docs if d.processing_status == status]
    if equipment:
        docs = [d for d in docs if d.equipment_name and equipment.lower() in d.equipment_name.lower()]

    return {
        "total": len(docs),
        "documents": [
            {
                "doc_id": d.doc_id,
                "file_name": d.file_name,
                "file_type": d.file_type,
                "document_type": d.document_type,
                "type_confidence": f"{(d.type_confidence or 0)*100:.0f}%",
                "equipment_name": d.equipment_name,
                "manufacturer": d.manufacturer,
                "model_number": d.model_number,
                "processing_status": d.processing_status,
                "chunk_count": d.chunk_count,
                "page_count": d.page_count,
                "upload_date": d.upload_date.isoformat() if d.upload_date else None,
                "executive_summary": d.executive_summary,
            }
            for d in docs
        ]
    }


@router.get("/documents/{doc_id}")
async def get_document(doc_id: str, db: AsyncSession = Depends(get_db)):
    """Get full document details including all AI-extracted information."""
    result = await db.execute(
        select(IntelligentDocument).where(IntelligentDocument.doc_id == doc_id)
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(404, "Document not found")

    # Get knowledge
    k_result = await db.execute(
        select(DocumentKnowledge).where(DocumentKnowledge.doc_id == doc_id)
    )
    knowledge = k_result.scalar_one_or_none()

    def _json_or_empty(val, default):
        if not val:
            return default
        try:
            return json.loads(val)
        except Exception:
            return default

    return {
        "doc_id": doc.doc_id,
        "file_name": doc.file_name,
        "file_type": doc.file_type,
        "file_size": doc.file_size,
        "document_type": doc.document_type,
        "type_confidence": f"{(doc.type_confidence or 0)*100:.0f}%",
        "equipment_name": doc.equipment_name,
        "equipment_type": doc.equipment_type,
        "manufacturer": doc.manufacturer,
        "model_number": doc.model_number,
        "keywords": _json_or_empty(doc.keywords, []),
        "processing_status": doc.processing_status,
        "processing_error": doc.processing_error,
        "chunk_count": doc.chunk_count,
        "page_count": doc.page_count,
        "upload_date": doc.upload_date.isoformat() if doc.upload_date else None,
        "processed_date": doc.processed_date.isoformat() if doc.processed_date else None,
        "summaries": {
            "executive": doc.executive_summary,
            "technical": doc.technical_summary,
            "maintenance": doc.maintenance_summary,
        },
        "knowledge": {
            "operating_conditions":       _json_or_empty(knowledge.operating_conditions if knowledge else None, {}),
            "fault_modes":                _json_or_empty(knowledge.fault_modes if knowledge else None, []),
            "maintenance_tasks":          _json_or_empty(knowledge.maintenance_tasks if knowledge else None, []),
            "safety_instructions":        _json_or_empty(knowledge.safety_instructions if knowledge else None, []),
            "spare_parts":                _json_or_empty(knowledge.spare_parts if knowledge else None, []),
            "sensor_thresholds":          _json_or_empty(knowledge.sensor_thresholds if knowledge else None, {}),
            "maintenance_intervals":      _json_or_empty(knowledge.maintenance_intervals if knowledge else None, {}),
            "critical_components":        _json_or_empty(knowledge.critical_components if knowledge else None, []),
            "inspection_checklist":       _json_or_empty(knowledge.inspection_checklist if knowledge else None, []),
            "troubleshooting_procedures": _json_or_empty(knowledge.troubleshooting_procedures if knowledge else None, []),
        } if knowledge else {}
    }


@router.delete("/documents/{doc_id}")
async def delete_document(doc_id: str, db: AsyncSession = Depends(get_db)):
    """Delete document, its knowledge, and vector DB chunks."""
    result = await db.execute(
        select(IntelligentDocument).where(IntelligentDocument.doc_id == doc_id)
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(404, "Document not found")

    # Remove from vector DB
    try:
        vs = get_vector_store()
        vs.delete_documents_by_filter(where={"document_id": doc_id})
    except Exception:
        pass

    # Remove file
    try:
        if Path(doc.file_path).exists():
            os.remove(doc.file_path)
    except Exception:
        pass

    # Remove DB records
    k_result = await db.execute(
        select(DocumentKnowledge).where(DocumentKnowledge.doc_id == doc_id)
    )
    k = k_result.scalar_one_or_none()
    if k:
        await db.delete(k)
    await db.delete(doc)

    return {"status": "deleted", "doc_id": doc_id}


# ─────────────────────────────────────────────
# 3. KNOWLEDGE VIEW
# ─────────────────────────────────────────────
@router.get("/knowledge/{equipment_name}")
async def get_equipment_knowledge(equipment_name: str, db: AsyncSession = Depends(get_db)):
    """Get all extracted knowledge for a specific equipment across all uploaded documents."""
    result = await db.execute(
        select(DocumentKnowledge).where(
            DocumentKnowledge.equipment_name.ilike(f"%{equipment_name}%")
        )
    )
    records = result.scalars().all()

    if not records:
        raise HTTPException(404, f"No knowledge found for equipment: {equipment_name}")

    def _j(val):
        if not val:
            return []
        try:
            return json.loads(val)
        except Exception:
            return []

    # Merge knowledge from all documents for this equipment
    all_faults    = []
    all_tasks     = []
    all_parts     = []
    all_safety    = []
    all_checklist = []
    all_troubleshoot = []
    thresholds    = {}
    intervals     = {}
    conditions    = {}
    components    = []

    for r in records:
        all_faults    += _j(r.fault_modes)
        all_tasks     += _j(r.maintenance_tasks)
        all_parts     += _j(r.spare_parts)
        all_safety    += _j(r.safety_instructions)
        all_checklist += _j(r.inspection_checklist)
        all_troubleshoot += _j(r.troubleshooting_procedures)
        components    += _j(r.critical_components)
        thresh = _j(r.sensor_thresholds) if isinstance(_j(r.sensor_thresholds), dict) else {}
        thresholds.update(thresh)
        ints = _j(r.maintenance_intervals) if isinstance(_j(r.maintenance_intervals), dict) else {}
        intervals.update(ints)
        cond = _j(r.operating_conditions) if isinstance(_j(r.operating_conditions), dict) else {}
        conditions.update(cond)

    return {
        "equipment_name": equipment_name,
        "documents_count": len(records),
        "operating_conditions": conditions,
        "fault_modes": all_faults,
        "maintenance_tasks": all_tasks,
        "spare_parts": all_parts,
        "safety_instructions": list(set(all_safety)),
        "sensor_thresholds": thresholds,
        "maintenance_intervals": intervals,
        "critical_components": list(set(components)),
        "inspection_checklist": list(set(all_checklist)),
        "troubleshooting_procedures": all_troubleshoot,
    }


# ─────────────────────────────────────────────
# 4. INTELLIGENT CHAT
# ─────────────────────────────────────────────
@router.post("/chat")
async def intelligent_chat(
    question: str = Form(...),
    conversation_id: Optional[str] = Form(default=None),
    equipment_filter: Optional[str] = Form(default=None),
):
    """
    Chat with AI using ONLY knowledge from uploaded documents.
    Gives direct, specific answers with exact values and part numbers.
    """
    from groq import Groq
    from app.config import settings

    retrieval_engine = get_retrieval_engine()
    conv_manager     = get_conversation_manager()

    if not conversation_id:
        conversation_id = conv_manager.get_conversation_id()

    conv_manager.add_message(conversation_id, "user", question)

    # Retrieve relevant chunks (more results = better coverage)
    retrieval_result = retrieval_engine.retrieve(question, 8)

    # Build context string from retrieved chunks
    context_parts = []
    for i, chunk in enumerate(retrieval_result.chunks[:6], 1):
        equip = chunk.metadata.get("equipment_name", "")
        src   = chunk.source_document
        context_parts.append(
            f"[Doc {i}: {src} | Equipment: {equip}]\n{chunk.content}"
        )
    context = "\n\n---\n\n".join(context_parts) if context_parts else "No relevant documents found in knowledge base."

    # Direct, technical system prompt — strict domain enforcement, no markdown symbols
    system_prompt = (
        "You are an expert industrial maintenance engineer for a steel manufacturing plant. "
        "You ONLY answer questions related to: equipment maintenance, machine failures, sensor readings, "
        "spare parts, maintenance procedures, root cause analysis, failure prediction, plant operations, "
        "industrial safety, and equipment manuals. "
        "If a question is NOT related to industrial maintenance, equipment, or steel plant operations, "
        "you MUST respond with exactly: "
        "'I can only answer questions related to industrial maintenance and steel plant operations. "
        "Please ask me about equipment health, failures, maintenance procedures, spare parts, or plant operations.' "
        "Do NOT answer general knowledge, programming, science, math, or any other off-topic questions. "
        "Answer ONLY using the document context provided for maintenance questions. "
        "Be direct and specific — include exact temperatures, vibration values, part numbers, step numbers, grease types, and intervals. "
        "IMPORTANT FORMATTING RULES: "
        "1. Do NOT use markdown symbols like **, ##, ###, *, __, or __ in your response. "
        "2. Use plain text only. "
        "3. Use bullet points starting with a dash (-) or numbers (1. 2. 3.) for lists. "
        "4. Use UPPERCASE for section headings instead of ## or **. "
        "5. Keep responses clean, readable, and professional without any markdown formatting."
    )
    user_prompt = (
        f"Question: {question}\n\n"
        f"Context from uploaded maintenance documents:\n\n{context}\n\n"
        "Answer directly and specifically using the document content above. "
        "Quote exact values, part numbers, and procedures from the documents."
    )

    try:
        client = Groq(api_key=settings.GROQ_API_KEY)
        # Try primary model, fall back to faster model if rate limited
        for model in [settings.LLM_MODEL, "llama-3.1-8b-instant"]:
            try:
                completion = client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user",   "content": user_prompt}
                    ],
                    temperature=0.1,
                    max_tokens=1500,
                )
                answer      = completion.choices[0].message.content
                tokens_used = completion.usage.total_tokens
                break
            except Exception as e:
                if "429" in str(e) or "rate" in str(e).lower():
                    # Try next model
                    continue
                raise
        else:
            answer      = "Rate limit reached for all models. Please wait a few minutes and try again."
            tokens_used = 0
    except Exception as e:
        answer      = f"Error: {str(e)}"
        tokens_used = 0

    conf    = retrieval_result.avg_score
    sources = list(set(c.source_document for c in retrieval_result.chunks))

    conv_manager.add_message(conversation_id, "assistant", answer,
                              metadata={"sources": sources, "confidence": conf})

    # Build evidence list
    evidence = [
        {
            "source_document":  c.source_document,
            "document_type":    c.document_type,
            "equipment":        c.metadata.get("equipment_name", ""),
            "similarity_score": round(c.similarity_score, 4),
            "excerpt": c.content[:200] + ("..." if len(c.content) > 200 else "")
        }
        for c in retrieval_result.chunks[:5]
    ]

    return {
        "answer":           answer,
        "confidence_score": conf,
        "model_used":       settings.LLM_MODEL,
        "tokens_used":      tokens_used,
        "sources":          sources,
        "evidence":         evidence,
        "conversation_id":  conversation_id,
        "source_count":     len(retrieval_result.chunks),
    }


# ─────────────────────────────────────────────
# 5. SEARCH
# ─────────────────────────────────────────────
@router.get("/search")
async def search_knowledge_base(
    query: str = Query(..., min_length=2),
    top_k: int = Query(5, ge=1, le=20),
):
    """Search the knowledge base with semantic search."""
    retrieval_engine = get_retrieval_engine()
    result = retrieval_engine.retrieve(query, top_k)

    return {
        "query": query,
        "total_results": result.total_chunks,
        "retrieval_time_ms": round(result.retrieval_time_ms, 2),
        "results": [
            {
                "content": c.content,
                "source_document": c.source_document,
                "document_type": c.document_type,
                "equipment_name": c.metadata.get("equipment_name", ""),
                "similarity_score": round(c.similarity_score, 4),
                "chunk_id": c.chunk_id,
            }
            for c in result.chunks
        ]
    }


# ─────────────────────────────────────────────
# 6. STATS
# ─────────────────────────────────────────────
@router.get("/stats")
async def get_stats(db: AsyncSession = Depends(get_db)):
    """Get knowledge base statistics."""
    result = await db.execute(select(IntelligentDocument))
    docs = result.scalars().all()

    vs   = get_vector_store()
    info = vs.get_collection_info()

    completed = [d for d in docs if d.processing_status == "completed"]
    equipment_set = set(d.equipment_name for d in completed if d.equipment_name)
    doc_types = {}
    for d in completed:
        dt = d.document_type or "Unknown"
        doc_types[dt] = doc_types.get(dt, 0) + 1

    return {
        "total_documents":   len(docs),
        "processed":         len(completed),
        "pending":           len([d for d in docs if d.processing_status in ("uploaded", "processing")]),
        "failed":            len([d for d in docs if d.processing_status == "failed"]),
        "total_chunks":      info.get("document_count", 0),
        "unique_equipment":  len(equipment_set),
        "equipment_list":    sorted(equipment_set),
        "document_types":    doc_types,
    }
