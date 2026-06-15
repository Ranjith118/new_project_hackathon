"""Test chat quality after embedder warm-up."""
import requests

BASE = "http://localhost:8000"

questions = [
    # Rolling Mill Motor specific
    ("Why is my Rolling Mill Motor overheating?",                        "rmm-chat"),
    ("What are the bearing replacement steps for Rolling Mill Motor?",   "rmm-chat"),
    ("What grease and part number for Rolling Mill Motor bearing?",      "rmm-chat"),
    ("What is the vibration limit for Rolling Mill Motor?",              "rmm-chat"),
    # Blast Furnace Fan specific
    ("Why is my Blast Furnace Fan vibrating at 4.2 mm/s?",              "bff-chat"),
    ("What spare parts for Blast Furnace Fan bearing? Give part numbers","bff-chat"),
    ("What are the safety steps before Blast Furnace Fan maintenance?",  "bff-chat"),
    # Cross-machine
    ("What is the difference between Rolling Mill Motor and Blast Furnace Fan maintenance?", "cross"),
]

for question, conv in questions:
    r = requests.post(f"{BASE}/api/doc-intelligence/chat",
                      data={"question": question, "conversation_id": conv})
    d = r.json()
    conf    = d.get("confidence_score", 0)
    sources = d.get("sources", [])
    answer  = d.get("answer", "").replace("\n", " ")
    print(f"\nQ: {question}")
    print(f"   Confidence: {conf:.4f}  Sources: {sources}")
    print(f"   Answer: {answer[:300]}{'...' if len(answer)>300 else ''}")
