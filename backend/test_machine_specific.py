"""Test that RAG returns machine-specific answers for different equipment."""
import requests

BASE = "http://localhost:8000"

tests = [
    # (question, conversation_id, expected_machine)
    (
        "What are the bearing replacement steps for Blast Furnace Fan? What spare parts are needed?",
        "bff-test",
        "Blast Furnace Fan"
    ),
    (
        "What are the normal operating parameters for Blast Furnace Fan - temperature, vibration, current and flow rate?",
        "bff-test",
        "Blast Furnace Fan"
    ),
    (
        "Blast Furnace Fan vibration is 4.2 mm/s and bearing temperature is 88C. What is wrong and what should I do immediately?",
        "bff-test",
        "Blast Furnace Fan"
    ),
    (
        "What is the preventive maintenance schedule for Blast Furnace Fan?",
        "bff-test",
        "Blast Furnace Fan"
    ),
    (
        "What are the special safety requirements for Blast Furnace Fan maintenance that are different from normal motors?",
        "bff-test",
        "Blast Furnace Fan"
    ),
    (
        "Now tell me about Rolling Mill Motor bearing replacement - how is it different from Blast Furnace Fan?",
        "compare-test",
        "Both machines"
    ),
]

for i, (question, conv, expected) in enumerate(tests, 1):
    print(f"\n{'='*65}")
    print(f"Q{i} [{expected}]: {question}")
    print("="*65)

    r = requests.post(f"{BASE}/api/rag/chat", json={
        "question": question,
        "conversation_id": conv
    })
    d = r.json()

    conf    = d.get("confidence_score", 0)
    sources = d.get("sources", [])
    answer  = d.get("answer", "")
    tokens  = d.get("tokens_used", 0)

    print(f"Confidence : {conf:.4f} | Tokens: {tokens}")
    print(f"Sources    : {sources}")
    print()
    print(answer)
