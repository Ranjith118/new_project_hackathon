"""Index Blast Furnace Fan manual into ChromaDB."""
import sys, os, uuid, warnings
warnings.filterwarnings('ignore')
sys.path.insert(0, '.')

from app.services.vector_db.chroma_service import get_vector_store
from datetime import datetime

manual_path = os.path.join('..', 'data', 'manuals', 'blast_furnace_fan_manual.txt')
with open(manual_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Split by section dividers
raw_sections = content.split('=======================================================')
sections = [s.strip() for s in raw_sections if len(s.strip()) > 80]
print(f"Found {len(sections)} sections")

# Chunk each section
chunks = []
for section in sections:
    if len(section) <= 600:
        chunks.append(section)
    else:
        parts = section.split('\n\n')
        current = ''
        for part in parts:
            if len(current) + len(part) < 600:
                current += ('\n\n' + part) if current else part
            else:
                if current:
                    chunks.append(current)
                current = part
        if current:
            chunks.append(current)

print(f"Total chunks: {len(chunks)}")

texts, metadatas, ids = [], [], []
for i, chunk in enumerate(chunks):
    texts.append(chunk)
    metadatas.append({
        'document_name': 'Blast Furnace Fan Manual - Siemens SIF-BF 2800',
        'document_type': 'manual',
        'equipment': 'Blast Furnace Fan',
        'source': 'blast_furnace_fan_manual.txt',
        'chunk_index': str(i),
        'added_at': datetime.now().isoformat()
    })
    ids.append(f"bff-manual-{i:03d}")

vs = get_vector_store()
result_ids = vs.add_texts(texts=texts, metadatas=metadatas, ids=ids)
print(f"Indexed {len(result_ids)} chunks into vector DB")

info = vs.get_collection_info()
print(f"Total documents in vector DB now: {info.get('document_count', 0)}")

# Quick search test
print("\nSearch test: 'blast furnace fan bearing replacement'")
results = vs.similarity_search('blast furnace fan bearing replacement spare parts', n_results=3)
for r in results:
    doc = r.get('metadata', {}).get('document_name', '?')
    print(f"  [{r.get('score', 0):.4f}] {doc}")
    print(f"           {r.get('content', '')[:120]}")
