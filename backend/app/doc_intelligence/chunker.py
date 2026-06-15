"""Smart document chunker with overlap."""
from typing import List, Dict, Any
import uuid


def chunk_text(
    text: str,
    document_id: str,
    document_name: str,
    document_type: str,
    equipment_name: str,
    chunk_size: int = 500,
    overlap: int = 75,
) -> List[Dict[str, Any]]:
    """
    Split text into overlapping chunks with metadata.
    Returns list of chunk dicts ready for vector store.
    """
    # Clean text
    text = text.replace("\x00", "").strip()
    if not text:
        return []

    # Split into paragraphs first (preserve context boundaries)
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

    chunks = []
    current_chunk = ""
    chunk_index = 0

    for para in paragraphs:
        # If paragraph alone exceeds chunk_size, split it by sentences
        if len(para) > chunk_size:
            sentences = para.replace(". ", ".\n").split("\n")
            for sent in sentences:
                if len(current_chunk) + len(sent) + 1 <= chunk_size:
                    current_chunk += (" " if current_chunk else "") + sent
                else:
                    if current_chunk:
                        chunks.append(_make_chunk(
                            current_chunk, chunk_index, document_id,
                            document_name, document_type, equipment_name
                        ))
                        chunk_index += 1
                        # Overlap: keep last overlap chars
                        current_chunk = current_chunk[-overlap:] + " " + sent
                    else:
                        current_chunk = sent
        else:
            if len(current_chunk) + len(para) + 2 <= chunk_size:
                current_chunk += ("\n\n" if current_chunk else "") + para
            else:
                if current_chunk:
                    chunks.append(_make_chunk(
                        current_chunk, chunk_index, document_id,
                        document_name, document_type, equipment_name
                    ))
                    chunk_index += 1
                    current_chunk = current_chunk[-overlap:] + "\n\n" + para
                else:
                    current_chunk = para

    # Last chunk
    if current_chunk.strip():
        chunks.append(_make_chunk(
            current_chunk, chunk_index, document_id,
            document_name, document_type, equipment_name
        ))

    return chunks


def _make_chunk(
    text: str,
    index: int,
    document_id: str,
    document_name: str,
    document_type: str,
    equipment_name: str,
) -> Dict[str, Any]:
    return {
        "id": f"{document_id}-chunk-{index:04d}",
        "text": text.strip(),
        "metadata": {
            "chunk_id": f"{document_id}-chunk-{index:04d}",
            "document_id": document_id,
            "document_name": document_name,
            "document_type": document_type,
            "equipment_name": equipment_name,
            "chunk_index": str(index),
        }
    }
