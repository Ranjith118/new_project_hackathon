"""Re-index all documents into ChromaDB with the new TF-IDF embedder."""
import os, sys, warnings, requests, json
warnings.filterwarnings('ignore')
sys.path.insert(0, '.')

from app.services.vector_db.chroma_service import get_vector_store
from app.services.embeddings.embeddings import get_embedding_service, _USE_ST
from app.doc_intelligence.chunker import chunk_text
from app.doc_intelligence.file_reader import read_file
from datetime import datetime
import uuid

BASE = "http://localhost:8000"
print(f"Embedding mode: {'sentence-transformers' if _USE_ST else 'TF-IDF (fast)'}")

vs  = get_vector_store()
emb = get_embedding_service()

manuals = [
    {
        "path": "../data/manuals/rolling_mill_motor_manual.txt",
        "name": "Rolling Mill Motor Manual - ABB M3BP",
        "type": "manual",
        "equipment": "Rolling Mill Motor"
    },
    {
        "path": "../data/manuals/blast_furnace_fan_manual.txt",
        "name": "Blast Furnace Fan Manual - Siemens SIF-BF 2800",
        "type": "manual",
        "equipment": "Blast Furnace Fan"
    },
]

all_texts = []
all_meta  = []
all_ids   = []

# ── Collect all text chunks from manuals ──────────────────────
for m in manuals:
    if not os.path.exists(m["path"]):
        print(f"  SKIP (not found): {m['path']}")
        continue
    text, pages = read_file(m["path"])
    chunks = chunk_text(
        text=text,
        document_id=str(uuid.uuid4()),
        document_name=m["name"],
        document_type=m["type"],
        equipment_name=m["equipment"],
        chunk_size=500,
        overlap=75,
    )
    for c in chunks:
        all_texts.append(c["text"])
        all_meta.append(c["metadata"])
        all_ids.append(c["id"])
    print(f"  Manual: {m['name']} — {len(chunks)} chunks")

# ── Import DB records via API ──────────────────────────────────
print("\nImporting DB records via API...")
r = requests.post(f"{BASE}/api/rag/index/import-maintenance-logs")
logs_data = r.json()
print(f"  Maintenance logs: {logs_data.get('logs_imported',0)} imported")

r = requests.post(f"{BASE}/api/rag/index/import-failure-reports")
rep_data = r.json()
print(f"  Failure reports : {rep_data.get('reports_imported',0)} imported")

# ── Build IDF over ALL texts before indexing ──────────────────
if not _USE_ST:
    print(f"\nBuilding TF-IDF corpus over {len(all_texts)} manual chunks...")
    # Prime the embedder corpus so IDF is rich
    _ = emb.embed_texts(all_texts[:10])   # warm-up

# ── Index manuals into ChromaDB ───────────────────────────────
if all_texts:
    print(f"\nIndexing {len(all_texts)} chunks into ChromaDB...")
    batch = 50
    for i in range(0, len(all_texts), batch):
        vs.add_texts(
            texts=all_texts[i:i+batch],
            metadatas=all_meta[i:i+batch],
            ids=all_ids[i:i+batch]
        )
    print(f"  Done.")

# ── Verify ────────────────────────────────────────────────────
info = vs.get_collection_info()
total = info.get('document_count', 0)
print(f"\nTotal documents in vector DB: {total}")

# ── Quick search test ─────────────────────────────────────────
print("\nSearch test: 'bearing replacement steps blast furnace fan'")
results = vs.similarity_search('bearing replacement steps blast furnace fan', n_results=4)
for r in results:
    doc  = r.get('metadata', {}).get('document_name', '?')
    equip = r.get('metadata', {}).get('equipment_name', '?')
    score = r.get('score', 0)
    preview = r.get('content', '')[:100].replace('\n', ' ')
    print(f"  [{score:.4f}] {equip} | {doc[:40]}")
    print(f"           {preview}")

print("\nSearch test: 'Rolling Mill Motor lubrication interval grease'")
results = vs.similarity_search('Rolling Mill Motor lubrication interval grease', n_results=4)
for r in results:
    doc  = r.get('metadata', {}).get('document_name', '?')
    equip = r.get('metadata', {}).get('equipment_name', '?')
    score = r.get('score', 0)
    preview = r.get('content', '')[:100].replace('\n', ' ')
    print(f"  [{score:.4f}] {equip} | {doc[:40]}")
    print(f"           {preview}")

print("\nDone. All documents indexed.")
