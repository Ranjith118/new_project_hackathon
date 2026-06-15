"""Final RAG chat test with full knowledge base loaded."""
import requests, json

BASE = "http://localhost:8000"

QUESTIONS = [
    ("Tell me about Rolling Mill Motor - its failures, maintenance history and current status", "q1"),
    ("What are the exact steps to replace the bearing on the Rolling Mill Motor? What spare parts are needed?", "q1"),
    ("What are the normal operating parameters for Rolling Mill Motor temperature, vibration, current and RPM?", "q1"),
    ("What safety steps must be followed before doing any maintenance on the Rolling Mill Motor?", "q1"),
    ("Rolling Mill Motor vibration is 4.3 mm/s and temperature is 110C. What is the diagnosis and what should I do right now?", "q1"),
    ("What is the preventive maintenance schedule for Rolling Mill Motor?", "q1"),
]

for i, (question, conv) in enumerate(QUESTIONS, 1):
    print(f"\n{'='*65}")
    print(f"Q{i}: {question}")
    print("="*65)

    r = requests.post(f"{BASE}/api/rag/chat", json={
        "question": question,
        "conversation_id": conv
    })
    d = r.json()
    conf  = d.get("confidence_score", 0)
    model = d.get("model_used", "")
    tok   = d.get("tokens_used", 0)
    src   = d.get("sources", [])

    print(f"Confidence : {conf:.4f} | Model: {model} | Tokens: {tok}")
    print(f"Sources    : {src}")
    print()
    print(d.get("answer", ""))
