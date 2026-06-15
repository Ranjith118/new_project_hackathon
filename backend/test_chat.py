"""Test RAG chat with knowledge base."""
import requests
import json

BASE = "http://localhost:8000"

def chat(question, conv_id):
    r = requests.post(f"{BASE}/api/rag/chat", json={
        "question": question,
        "conversation_id": conv_id
    })
    d = r.json()
    print(f"\nQ: {question}")
    print(f"Model: {d.get('model_used')} | Tokens: {d.get('tokens_used')} | Confidence: {d.get('confidence_score', 0):.2f}")
    print(f"Sources: {d.get('sources', [])}")
    print(f"\nANSWER:\n{d.get('answer', 'N/A')}")
    print("-" * 60)
    return d

# First check index stats
stats = requests.get(f"{BASE}/api/rag/index/stats").json()
print(f"Vector DB: {stats['total_documents']} documents indexed\n")

print("=" * 60)
print("TEST 1: Rolling Mill Motor history")
print("=" * 60)
chat(
    "Tell me about the Rolling Mill Motor. What failures has it had and what maintenance was done?",
    "rmm-session-01"
)

print("=" * 60)
print("TEST 2: Bearing failure guidance")
print("=" * 60)
chat(
    "Rolling Mill Motor has vibration 4.3 mm/s and temperature 110C with RUL of 6 days. Root cause is bearing failure. What exact steps should the technician take?",
    "rmm-session-01"
)

print("=" * 60)
print("TEST 3: Cooling Pump A issues")
print("=" * 60)
chat(
    "What issues has Cooling Pump A experienced? What was done to fix them?",
    "pump-session-01"
)

print("=" * 60)
print("TEST 4: Safety procedures")
print("=" * 60)
chat(
    "What safety precautions should be followed before replacing a bearing on a motor?",
    "safety-session-01"
)

print("=" * 60)
print("TEST 5: Spare parts question")
print("=" * 60)
chat(
    "What spare parts do I need for bearing replacement on the Rolling Mill Motor?",
    "spares-session-01"
)
