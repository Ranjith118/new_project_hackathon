"""Test RAG chat with Rolling Mill Motor context after knowledge base indexing."""
import requests
import json

BASE = "http://localhost:8000"

queries = [
    (
        "Tell me about Rolling Mill Motor - its failures, maintenance history, and current issues",
        "rmm-session"
    ),
    (
        "What is the root cause of Rolling Mill Motor bearing failure and what maintenance was done previously?",
        "rmm-session"
    ),
    (
        "Rolling Mill Motor has vibration 4.3 mm/s and temperature 110C. RUL is 6 days. What are the exact steps to replace the bearing and what spare parts are needed?",
        "rmm-session"
    ),
    (
        "What safety precautions must be followed when doing bearing replacement on the Rolling Mill Motor?",
        "rmm-session"
    ),
]

for i, (question, conv_id) in enumerate(queries, 1):
    print()
    print("=" * 65)
    print(f"Q{i}: {question}")
    print("=" * 65)

    r = requests.post(
        f"{BASE}/api/rag/chat",
        json={"question": question, "conversation_id": conv_id}
    )
    d = r.json()

    model    = d.get("model_used", "N/A")
    tokens   = d.get("tokens_used", 0)
    conf     = d.get("confidence_score", 0)
    sources  = d.get("sources", [])
    answer   = d.get("answer", "No answer")

    print(f"Model      : {model}")
    print(f"Tokens     : {tokens}")
    print(f"Confidence : {conf:.4f}  {'(context found)' if conf > 0 else '(no context - generic answer)'}")
    print(f"Sources    : {sources}")
    print()
    print("ANSWER:")
    print(answer)

print()
print("=" * 65)
print("CHAT HISTORY - Full conversation")
print("=" * 65)
r = requests.get(f"{BASE}/api/rag/chat/history/rmm-session")
d = r.json()
print(f"Total messages: {d.get('message_count', 0)}")
for msg in d.get("messages", []):
    role    = msg.get("role", "?").upper()
    content = msg.get("content", "")
    print(f"\n[{role}] {content[:200]}")
