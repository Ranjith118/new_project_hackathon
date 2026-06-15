"""End-to-end test of Document Intelligence system."""
import requests, json, time

BASE = "http://localhost:8000/api/doc-intelligence"

def sep(title):
    print(f"\n{'='*60}\n  {title}\n{'='*60}")

# 1. Stats before
sep("1. INITIAL STATS")
r = requests.get(f"{BASE}/stats")
d = r.json()
print(f"  Documents processed : {d['processed']}")
print(f"  Total chunks        : {d['total_chunks']}")
print(f"  Unique equipment    : {d['unique_equipment']}")
print(f"  Equipment list      : {d['equipment_list']}")
print(f"  Document types      : {d['document_types']}")

# 2. Upload Blast Furnace Fan manual
sep("2. UPLOAD - Blast Furnace Fan Manual")
with open("../data/manuals/blast_furnace_fan_manual.txt", "rb") as f:
    r = requests.post(f"{BASE}/upload", files={"file": ("blast_furnace_fan_manual.txt", f, "text/plain")})
d = r.json()
print(f"  Status   : {d['status']}")
print(f"  Doc ID   : {d['doc_id']}")
print(f"  Filename : {d['file_name']}")
print(f"  Size     : {d['file_size']:,} bytes")
doc_id = d["doc_id"]

# 3. Process (AI analysis)
sep("3. PROCESS - AI Analysis Pipeline")
print("  Running AI analysis (classify + extract + summarize + chunk + index)...")
start = time.time()
r = requests.post(f"{BASE}/process/{doc_id}")
elapsed = time.time() - start
d = r.json()
print(f"  Status           : {d['status']}")
print(f"  Document Type    : {d.get('document_type')} ({d.get('type_confidence')} confidence)")
print(f"  Equipment        : {d.get('equipment_name')}")
print(f"  Manufacturer     : {d.get('manufacturer')}")
print(f"  Model            : {d.get('model_number')}")
print(f"  Pages            : {d.get('page_count')}")
print(f"  Chunks indexed   : {d.get('chunk_count')}")
print(f"  Faults extracted : {d.get('faults_extracted')}")
print(f"  Tasks extracted  : {d.get('tasks_extracted')}")
print(f"  Parts extracted  : {d.get('parts_extracted')}")
print(f"  Keywords         : {d.get('keywords', [])}")
print(f"  Processing time  : {elapsed:.1f}s")
print(f"\n  EXECUTIVE SUMMARY:\n  {d.get('executive_summary','')}")
print(f"\n  TECHNICAL SUMMARY:\n  {d.get('technical_summary','')}")
print(f"\n  MAINTENANCE SUMMARY:\n  {d.get('maintenance_summary','')}")

# 4. Get full document with knowledge
sep("4. EXTRACTED KNOWLEDGE - Full Detail")
r = requests.get(f"{BASE}/documents/{doc_id}")
d = r.json()
k = d.get("knowledge", {})

print(f"\n  OPERATING CONDITIONS:")
for key, val in (k.get("operating_conditions") or {}).items():
    if val: print(f"    {key}: {val}")

print(f"\n  SENSOR THRESHOLDS:")
for key, val in (k.get("sensor_thresholds") or {}).items():
    if val: print(f"    {key}: {val}")

print(f"\n  FAULT MODES ({len(k.get('fault_modes',[]))}):")
for f in (k.get("fault_modes") or [])[:5]:
    print(f"    [{f.get('fault','')}] Cause: {f.get('cause','')} | Action: {f.get('action','')}")

print(f"\n  MAINTENANCE TASKS ({len(k.get('maintenance_tasks',[]))}):")
for t in (k.get("maintenance_tasks") or [])[:5]:
    print(f"    [{t.get('interval','')}] {t.get('task','')}")

print(f"\n  SPARE PARTS ({len(k.get('spare_parts',[]))}):")
for p in (k.get("spare_parts") or [])[:5]:
    print(f"    {p.get('part_name','')} | P/N: {p.get('part_number','')} | Qty: {p.get('quantity','')}")

print(f"\n  SAFETY INSTRUCTIONS ({len(k.get('safety_instructions',[]))}):")
for s in (k.get("safety_instructions") or [])[:4]:
    print(f"    - {s}")

print(f"\n  MAINTENANCE INTERVALS:")
for period, tasks in (k.get("maintenance_intervals") or {}).items():
    if tasks and any(t for t in tasks if t):
        print(f"    {period.upper()}: {[t for t in tasks if t][:2]}")

# 5. List all documents
sep("5. DOCUMENTS LIST")
r = requests.get(f"{BASE}/documents")
d = r.json()
print(f"  Total documents: {d['total']}")
for doc in d["documents"]:
    print(f"  [{doc['processing_status'].upper()}] {doc['file_name'][:40]:<40} | {doc['document_type']} | {doc['equipment_name']}")

# 6. Equipment knowledge endpoint
sep("6. EQUIPMENT KNOWLEDGE - Blast Furnace Fan")
r = requests.get(f"{BASE}/knowledge/Blast Furnace Fan")
if r.status_code == 200:
    d = r.json()
    print(f"  Equipment       : {d['equipment_name']}")
    print(f"  Documents count : {d['documents_count']}")
    print(f"  Fault modes     : {len(d['fault_modes'])}")
    print(f"  Spare parts     : {len(d['spare_parts'])}")
    print(f"  Critical comps  : {d['critical_components'][:3]}")
else:
    print(f"  Status: {r.status_code}")

# 7. Semantic search
sep("7. SEMANTIC SEARCH")
queries = [
    "blast furnace fan bearing replacement spare parts",
    "vibration limits warning critical",
    "safety lockout tagout high voltage",
]
for q in queries:
    r = requests.get(f"{BASE}/search", params={"query": q, "top_k": 3})
    d = r.json()
    print(f"\n  Query: '{q}'")
    print(f"  Results: {d['total_results']} | Time: {d['retrieval_time_ms']:.0f}ms")
    for res in d["results"][:2]:
        print(f"    [{res['similarity_score']:.3f}] {res['source_document']} | {res['content'][:90]}")

# 8. AI Chat
sep("8. AI CHAT - Blast Furnace Fan specific questions")
chat_questions = [
    "What is the bearing replacement procedure for Blast Furnace Fan? List exact steps.",
    "What are the vibration alarm levels for Blast Furnace Fan?",
    "What spare parts are needed for Blast Furnace Fan bearing replacement with part numbers?",
    "What are the special safety requirements for Blast Furnace Fan that differ from normal motors?",
]
for q in chat_questions:
    print(f"\n  Q: {q}")
    fd = {"question": q, "conversation_id": "bff-e2e"}
    r = requests.post(f"{BASE}/chat", data=fd)
    d = r.json()
    print(f"  Confidence : {d['confidence_score']:.4f} | Sources: {d['sources']}")
    # Show first 400 chars of answer
    ans = d['answer'].replace('\n', ' ')
    print(f"  Answer: {ans[:400]}{'...' if len(ans)>400 else ''}")

# 9. Stats after
sep("9. FINAL STATS")
r = requests.get(f"{BASE}/stats")
d = r.json()
print(f"  Documents processed : {d['processed']}")
print(f"  Total chunks        : {d['total_chunks']}")
print(f"  Unique equipment    : {d['unique_equipment']}")
print(f"  Equipment list      : {d['equipment_list']}")
print(f"  Document types      : {d['document_types']}")

print("\n" + "="*60)
print("  DOCUMENT INTELLIGENCE SYSTEM - COMPLETE")
print("  Frontend: http://localhost:5173/doc-intelligence")
print("  API Docs: http://localhost:8000/docs#/Document Intelligence")
print("="*60)
