"""Directly index the Rolling Mill Motor manual into ChromaDB."""
import sys
import os
import warnings
warnings.filterwarnings('ignore')

sys.path.insert(0, '.')

from app.services.vector_db.chroma_service import get_vector_store
from datetime import datetime

# Read the manual
manual_path = os.path.join('..', 'data', 'manuals', 'rolling_mill_motor_manual.txt')
with open(manual_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Split into meaningful sections
raw_sections = content.split('=======================================================')
sections = []
for s in raw_sections:
    s = s.strip()
    if len(s) > 80:
        sections.append(s)

print(f"Found {len(sections)} sections in manual")

# Further split long sections into smaller chunks (max 600 chars)
chunks = []
for section in sections:
    if len(section) <= 600:
        chunks.append(section)
    else:
        # Split by double newline
        parts = section.split('\n\n')
        current = ''
        for part in parts:
            if len(current) + len(part) < 600:
                current += '\n\n' + part if current else part
            else:
                if current:
                    chunks.append(current)
                current = part
        if current:
            chunks.append(current)

print(f"Total chunks to index: {len(chunks)}")

# Build metadata for each chunk
texts = []
metadatas = []
ids = []
import uuid

for i, chunk in enumerate(chunks):
    texts.append(chunk)
    metadatas.append({
        'document_name': 'Rolling Mill Motor Manual - ABB M3BP',
        'document_type': 'manual',
        'equipment': 'Rolling Mill Motor',
        'source': 'rolling_mill_motor_manual.txt',
        'chunk_index': str(i),
        'added_at': datetime.now().isoformat()
    })
    ids.append(f"rmm-manual-{i:03d}")

# Index into ChromaDB
vs = get_vector_store()
result_ids = vs.add_texts(texts=texts, metadatas=metadatas, ids=ids)
print(f"Indexed {len(result_ids)} chunks successfully")

# Verify
info = vs.get_collection_info()
print(f"Total documents in vector DB: {info.get('document_count', 0)}")

# Test a search
print("\nTest search: 'bearing replacement steps'")
results = vs.similarity_search('bearing replacement steps spare parts', n_results=3)
for r in results:
    print(f"  [{r.get('score', 0):.4f}] {r.get('metadata', {}).get('document_name', '?')}")
    print(f"           {r.get('content', '')[:150]}")
    print()
