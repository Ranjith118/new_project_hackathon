"""Complete end-to-end test of all Maintenance Wizard API endpoints."""
import requests
import json
from datetime import datetime

BASE = "http://localhost:8000"

def sep(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print('='*60)

def ok(label, data):
    if isinstance(data, dict):
        print(f"  OK  {label}: {json.dumps(data, default=str)[:120]}")
    elif isinstance(data, list):
        print(f"  OK  {label}: [{len(data)} items]")
    else:
        print(f"  OK  {label}: {str(data)[:120]}")

def fail(label, e):
    print(f"  ERR {label}: {e}")

# ─────────────────────────────────────────────
# 1. LEARNING SUMMARY
# ─────────────────────────────────────────────
sep("LEARNING: FULL MONTHLY SUMMARY")
try:
    r = requests.get(f"{BASE}/api/learning/summary?period=monthly&days=30")
    d = r.json()
    print(f"  Period        : {d['period']} | {d['period_start'][:10]} to {d['period_end'][:10]}")
    print(f"  Feedback      : {d['total_feedback']} total | Positive:{d['positive_feedback']} Negative:{d['negative_feedback']}")
    print(f"  Accept Rate   : {d['acceptance_rate']*100:.0f}%")
    print(f"  Outcomes      : {d['total_outcomes']} | Success:{d['success_rate']*100:.0f}%")
    print(f"  Avg Accuracy  : {d['average_accuracy']*100:.0f}% | Change:+{d['accuracy_change']*100:.1f}%")
    print(f"  Retraining    : {d['retraining_jobs']} jobs | AvgImprovement:{d['average_improvement']*100:.1f}%")
    print(f"  Improvements  : {d['top_improvements']}")
    print(f"  Concerns      : {d['areas_of_concern']}")
    print(f"  Suggestions   : {d['recommendations']}")
    print(f"\n  SUMMARY TEXT:\n{d['summary_text']}")
except Exception as e:
    fail("learning/summary", e)

# ─────────────────────────────────────────────
# 2. LEARNING: PERFORMANCE TRENDS
# ─────────────────────────────────────────────
sep("LEARNING: PERFORMANCE TRENDS")
try:
    r = requests.get(f"{BASE}/api/learning/performance/trends?days=30")
    trends = r.json()
    for t in trends:
        print(f"  {t['metric_name']:<35} current:{t['current_value']:.3f} prev:{t['previous_value']:.3f} change:{t['change']:+.2f} trend:{t['trend']}")
except Exception as e:
    fail("performance/trends", e)

# ─────────────────────────────────────────────
# 3. LEARNING: MODEL PERFORMANCE
# ─────────────────────────────────────────────
sep("LEARNING: MODEL PERFORMANCE SCORES")
try:
    r = requests.get(f"{BASE}/api/learning/performance/models")
    models = r.json()
    for m in models:
        print(f"  {m['model_name']:<22} accuracy:{m['accuracy']:.2f} f1:{m['f1_score']:.2f} samples:{m['sample_count']}")
except Exception as e:
    fail("performance/models", e)

# ─────────────────────────────────────────────
# 4. LEARNING: RECOMMENDATION SCORES
# ─────────────────────────────────────────────
sep("LEARNING: RECOMMENDATION SCORES")
try:
    r = requests.get(f"{BASE}/api/learning/performance/recommendation-scores")
    scores = r.json()
    for s in scores:
        print(f"  [{s['module_name']}] {s['recommendation_type']:<25} total:{s['total_count']} accepted:{s['acceptance_count']} effectiveness:{s['avg_effectiveness']:.2f}")
except Exception as e:
    fail("recommendation-scores", e)

# ─────────────────────────────────────────────
# 5. LEARNING: RETRAINING JOBS
# ─────────────────────────────────────────────
sep("LEARNING: RETRAINING JOBS")
try:
    r = requests.get(f"{BASE}/api/learning/retraining/jobs?limit=10")
    jobs = r.json()
    for j in jobs:
        print(f"  [{j['status'].upper()}] {j['model_name']:<20} trigger:{j['trigger']} improvement:{j['improvement']:+.3f} samples:{j['samples_used']}")
except Exception as e:
    fail("retraining/jobs", e)

# ─────────────────────────────────────────────
# 6. TRIGGER RETRAINING
# ─────────────────────────────────────────────
sep("LEARNING: TRIGGER RETRAINING (rul_prediction)")
try:
    r = requests.post(f"{BASE}/api/learning/retraining/trigger?model_name=rul_prediction")
    d = r.json()
    print(f"  Status   : {d['status']}")
    print(f"  Job ID   : {d['job_id']}")
    print(f"  Model    : {d['model_name']}")
    print(f"  Message  : {d['message']}")
except Exception as e:
    fail("retraining/trigger", e)

# ─────────────────────────────────────────────
# 7. ANOMALY: TRAIN MODEL
# ─────────────────────────────────────────────
sep("ANOMALY: TRAIN ISOLATION FOREST MODEL")
try:
    r = requests.post(f"{BASE}/api/anomaly/train-model")
    d = r.json()
    print(f"  Status          : {d.get('status','N/A')}")
    print(f"  Training Samples: {d.get('training_samples','N/A')}")
    print(f"  Anomaly Rate    : {d.get('anomaly_rate','N/A')}")
except Exception as e:
    fail("anomaly/train-model", e)

# ─────────────────────────────────────────────
# 8. PREDICTION: TRAIN FAILURE MODEL
# ─────────────────────────────────────────────
sep("PREDICTION: TRAIN FAILURE MODEL")
try:
    r = requests.post(f"{BASE}/api/prediction/train-failure")
    d = r.json()
    print(f"  Status  : {d['status']}")
    print(f"  Model   : {d['model_name']} ({d['model_type']})")
    if d.get('metrics'):
        m = d['metrics']
        print(f"  Accuracy: {m.get('accuracy',0):.3f} | Precision:{m.get('precision',0):.3f} | Recall:{m.get('recall',0):.3f} | F1:{m.get('f1_score',0):.3f}")
        print(f"  ROC-AUC : {m.get('roc_auc',0):.3f} | Samples: train={m.get('training_samples',0)} test={m.get('test_samples',0)}")
except Exception as e:
    fail("train-failure", e)

# ─────────────────────────────────────────────
# 9. PREDICTION: TRAIN RUL MODEL
# ─────────────────────────────────────────────
sep("PREDICTION: TRAIN RUL MODEL")
try:
    r = requests.post(f"{BASE}/api/prediction/train-rul")
    d = r.json()
    print(f"  Status : {d['status']}")
    print(f"  Model  : {d['model_name']} ({d['model_type']})")
    if d.get('metrics'):
        m = d['metrics']
        print(f"  MAE    : {m.get('mae',0):.3f} | RMSE:{m.get('rmse',0):.3f} | R2:{m.get('r2_score',0):.3f}")
except Exception as e:
    fail("train-rul", e)

# ─────────────────────────────────────────────
# 10. RAG: INDEX STATS
# ─────────────────────────────────────────────
sep("RAG: VECTOR DB INDEX STATS")
try:
    r = requests.get(f"{BASE}/api/rag/index/stats")
    d = r.json()
    print(f"  Total Documents : {d.get('total_documents',0)}")
    print(f"  Total Chunks    : {d.get('total_chunks',0)}")
    print(f"  Collection      : {d.get('collection_name','N/A')}")
    print(f"  Embedding Dim   : {d.get('embedding_dimension',0)}")
except Exception as e:
    fail("rag/index/stats", e)

# ─────────────────────────────────────────────
# 11. RAG: IMPORT MAINTENANCE LOGS INTO VECTOR DB
# ─────────────────────────────────────────────
sep("RAG: IMPORT MAINTENANCE LOGS TO VECTOR DB")
try:
    r = requests.post(f"{BASE}/api/rag/index/import-maintenance-logs")
    d = r.json()
    print(f"  Status    : {d.get('status','N/A')}")
    print(f"  Indexed   : {d.get('indexed_count',0)} documents")
    print(f"  Message   : {d.get('message','N/A')}")
except Exception as e:
    fail("import-maintenance-logs", e)

# ─────────────────────────────────────────────
# 12. RAG: IMPORT FAILURE REPORTS INTO VECTOR DB
# ─────────────────────────────────────────────
sep("RAG: IMPORT FAILURE REPORTS TO VECTOR DB")
try:
    r = requests.post(f"{BASE}/api/rag/index/import-failure-reports")
    d = r.json()
    print(f"  Status    : {d.get('status','N/A')}")
    print(f"  Indexed   : {d.get('indexed_count',0)} documents")
    print(f"  Message   : {d.get('message','N/A')}")
except Exception as e:
    fail("import-failure-reports", e)

# ─────────────────────────────────────────────
# 13. RAG: INDEX STATS AFTER IMPORT
# ─────────────────────────────────────────────
sep("RAG: VECTOR DB STATS AFTER IMPORT")
try:
    r = requests.get(f"{BASE}/api/rag/index/stats")
    d = r.json()
    print(f"  Total Documents : {d.get('total_documents',0)}")
    print(f"  Total Chunks    : {d.get('total_chunks',0)}")
    print(f"  Collection Name : {d.get('collection_name','N/A')}")
except Exception as e:
    fail("rag/index/stats (post-import)", e)

# ─────────────────────────────────────────────
# 14. RAG: DOCUMENT SEARCH
# ─────────────────────────────────────────────
sep("RAG: SEMANTIC DOCUMENT SEARCH")
try:
    r = requests.post(f"{BASE}/api/rag/documents/process", json={
        "query": "bearing failure vibration motor",
        "top_k": 5
    })
    d = r.json()
    print(f"  Query   : bearing failure vibration motor")
    print(f"  Results : {d.get('total_chunks',0)}")
    for chunk in d.get('chunks', [])[:3]:
        print(f"  [{chunk.get('similarity_score',0):.2f}] {chunk.get('source_document','?')} - {chunk.get('content','')[:80]}")
except Exception as e:
    fail("rag/documents/process", e)

# ─────────────────────────────────────────────
# 15. RAG: SUGGESTED QUESTIONS
# ─────────────────────────────────────────────
sep("RAG: AI SUGGESTED QUESTIONS")
try:
    r = requests.get(f"{BASE}/api/rag/suggested-questions")
    d = r.json()
    print(f"  Suggested questions ({len(d.get('questions',[]))} total):")
    for q in d.get('questions', [])[:6]:
        print(f"  -> {q}")
except Exception as e:
    fail("rag/suggested-questions", e)

# ─────────────────────────────────────────────
# 16. RAG: AI CHAT WITH GROQ (after indexing)
# ─────────────────────────────────────────────
sep("RAG: AI CHAT - GROQ LLM (after knowledge base indexing)")
try:
    r = requests.post(f"{BASE}/api/rag/chat", json={
        "question": "Rolling Mill Motor has vibration 4.3 mm/s and temperature 110C. RUL is 6 days. What are the exact steps to replace the bearing and what parts do I need?",
        "conversation_id": "final-test-001"
    })
    d = r.json()
    print(f"  Model  : {d.get('model_used','?')}")
    print(f"  Tokens : {d.get('tokens_used',0)}")
    print(f"  Sources: {d.get('sources',[])}")
    print(f"\n  ANSWER:\n{d.get('answer','N/A')}")
except Exception as e:
    fail("rag/chat", e)

# ─────────────────────────────────────────────
# 17. RAG: CHAT HISTORY
# ─────────────────────────────────────────────
sep("RAG: CHAT HISTORY")
try:
    r = requests.get(f"{BASE}/api/rag/chat/history/final-test-001")
    d = r.json()
    print(f"  Conversation ID : final-test-001")
    print(f"  Messages        : {d.get('message_count',0)}")
    for msg in d.get('messages',[]):
        print(f"  [{msg.get('role','?').upper()}] {str(msg.get('content',''))[:80]}")
except Exception as e:
    fail("rag/chat/history", e)

# ─────────────────────────────────────────────
# 18. DECISION SUPPORT: EQUIPMENT RANKING
# ─────────────────────────────────────────────
sep("DECISION SUPPORT: EQUIPMENT RANKING")
try:
    r = requests.get(f"{BASE}/api/decision-support/equipment-ranking")
    d = r.json()
    rankings = d.get('rankings', d) if isinstance(d, dict) else d
    print(f"  Total ranked: {len(rankings)}")
    for eq in rankings[:8]:
        print(f"  Rank:{eq.get('rank',0)} {eq.get('equipment_name','?'):<28} Score:{eq.get('priority_score',0):.1f} Level:{eq.get('priority_level','?')} FailProb:{eq.get('failure_probability',0)*100:.0f}% RUL:{eq.get('rul_days',0)}d Action:{eq.get('recommended_action','?')[:40]}")
except Exception as e:
    fail("equipment-ranking", e)

# ─────────────────────────────────────────────
# 19. DECISION SUPPORT: PLANT HEALTH DASHBOARD
# ─────────────────────────────────────────────
sep("DECISION SUPPORT: PLANT HEALTH DASHBOARD")
try:
    r = requests.get(f"{BASE}/api/decision-support/plant-health")
    d = r.json()
    print(f"  Plant Health Score : {d.get('plant_health_score',0):.1f}%")
    print(f"  Critical Count     : {d.get('critical_count',0)}")
    print(f"  High Risk Count    : {d.get('high_count',0)}")
    print(f"  Total Equipment    : {d.get('total_equipment',0)}")
    print(f"  Avg Criticality    : {d.get('average_criticality',0):.1f}")
    print(f"  Total Downtime $/h : ${d.get('total_downtime_cost_per_hour',0):,.0f}")
    print(f"  Immediate Actions  : {d.get('immediate_actions',[])}")
    print(f"  Short Term Actions : {len(d.get('short_term_actions',[]))} items")
except Exception as e:
    fail("plant-health", e)

# ─────────────────────────────────────────────
# 20. COMPLETE SYSTEM SUMMARY
# ─────────────────────────────────────────────
sep("COMPLETE SYSTEM SUMMARY")
try:
    stats    = requests.get(f"{BASE}/api/dashboard/stats").json()
    crit     = requests.get(f"{BASE}/api/decision-support/criticality/summary").json()
    invsum   = requests.get(f"{BASE}/api/procurement/inventory-summary").json()
    quick    = requests.get(f"{BASE}/api/learning/summary/quick").json()
    health   = requests.get(f"{BASE}/api/anomaly/health-status").json()
    rpts     = requests.get(f"{BASE}/api/rca/reports").json()

    print(f"""
  +-------------------------------------------------+
  |      MAINTENANCE WIZARD - SYSTEM STATUS         |
  +-------------------------------------------------+
  | EQUIPMENT                                       |
  |   Total          : {stats['total_equipment']:<5}                         |
  |   Operational    : {stats['operational_equipment']:<5}                         |
  |   Under Maint.   : {stats['maintenance_equipment']:<5}                         |
  |   Failed         : {stats['failed_equipment']:<5}                         |
  +-------------------------------------------------+
  | RECORDS                                         |
  |   Maintenance Logs   : {stats['total_maintenance_logs']:<5}                    |
  |   Failure Reports    : {stats['total_failure_reports']:<5}                    |
  |   RCA Reports Saved  : {rpts['total']:<5}                    |
  +-------------------------------------------------+
  | PLANT CRITICALITY                               |
  |   Critical Equipment : {crit['critical_count']:<5}                         |
  |   High Risk          : {crit['high_count']:<5}                         |
  |   Avg Score          : {crit['average_criticality']:.1f}                        |
  |   Downtime Cost/hr   : ${crit['total_downtime_cost_per_hour']:>8,.0f}                |
  +-------------------------------------------------+
  | INVENTORY                                       |
  |   Total Parts    : {invsum['total_parts']:<5}                         |
  |   In Stock       : {invsum['in_stock']:<5}                         |
  |   Low Stock      : {invsum['low_stock']:<5}                         |
  |   Out of Stock   : {invsum['out_of_stock']:<5}                         |
  |   Total Value    : ${invsum['total_inventory_value']:>7,.0f}                 |
  +-------------------------------------------------+
  | HEALTH MONITORING                               |
  |   Total Monitored: {health['total_equipment']:<5}                         |
  |   Healthy        : {health['healthy_count']:<5}                         |
  |   Fair           : {health['fair_count']:<5}                         |
  |   Poor/Critical  : {health['poor_count'] + health['critical_count']:<5}                         |
  |   Overall Health : {health['overall_health_percentage']:.0f}%                         |
  +-------------------------------------------------+
  | AI LEARNING SYSTEM                              |
  |   Total Feedback : {quick['feedback_count']:<5}                         |
  |   Accept Rate    : {quick['acceptance_rate']*100:.0f}%                          |
  |   Success Rate   : {quick['success_rate']*100:.0f}%                          |
  |   Avg Accuracy   : {quick['average_accuracy']*100:.0f}%                          |
  |   Need Retrain   : {quick['models_need_retraining']:<5}                         |
  +-------------------------------------------------+
""")
except Exception as e:
    fail("system summary", e)

print("\n" + "="*60)
print("  ALL ENDPOINTS TESTED - MAINTENANCE WIZARD COMPLETE")
print("="*60)
print(f"  Backend  : http://localhost:8000")
print(f"  Frontend : http://localhost:5173")
print(f"  API Docs : http://localhost:8000/docs")
print("="*60)
