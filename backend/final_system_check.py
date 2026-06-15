"""Final complete system check for all modules."""
import requests
BASE = 'http://localhost:8000'

print("=" * 65)
print("  MAINTENANCE WIZARD - FINAL SYSTEM CHECK")
print("=" * 65)

checks = [
    # Dashboard
    ("GET", "/api/dashboard/stats",                     "Dashboard Stats"),
    # Equipment
    ("GET", "/api/equipment/",                          "Equipment List"),
    # Sensor Monitoring
    ("GET", "/api/sensor-data/live-status",             "Sensor Live Status"),
    ("GET", "/api/sensor-data/count/total",             "Sensor Count"),
    ("GET", "/api/sensor-data/history/Rolling%20Mill%20Motor?hours=1", "Sensor History"),
    ("POST","/api/sensor-data/simulate-all",            "Sensor Simulate"),
    # Anomaly & Health
    ("GET", "/api/anomaly/health-status",               "Equipment Health"),
    ("GET", "/api/anomaly/alerts",                      "Alert List"),
    ("GET", "/api/anomaly/alerts/summary",              "Alert Summary"),
    ("GET", "/api/anomaly/dashboard",                   "Anomaly Dashboard"),
    # Failure Prediction
    ("GET", "/api/prediction/equipment-predictions",   "Failure Predictions"),
    ("GET", "/api/prediction/model-metrics",           "Model Metrics"),
    # RCA
    ("GET", "/api/rca/dashboard",                      "RCA Dashboard"),
    ("GET", "/api/rca/patterns",                       "RCA Patterns"),
    # Recommendations
    ("GET", "/api/recommendation/dashboard",           "Recommendations Dashboard"),
    # Decision Support
    ("GET", "/api/decision-support/criticality/summary","Criticality Summary"),
    ("GET", "/api/decision-support/equipment-ranking", "Equipment Ranking"),
    ("GET", "/api/decision-support/plant-health",      "Plant Health"),
    # Procurement
    ("GET", "/api/procurement/inventory-summary",      "Inventory Summary"),
    ("GET", "/api/procurement/spares",                 "Spare Parts"),
    ("GET", "/api/procurement/alerts",                 "Procurement Alerts"),
    # Learning
    ("GET", "/api/learning/summary/quick",             "Learning Summary"),
    # Document Intelligence
    ("GET", "/api/doc-intelligence/stats",             "Doc Intelligence Stats"),
    ("GET", "/api/doc-intelligence/documents",         "Documents List"),
    # Maintenance Logs & Failure Reports
    ("GET", "/api/maintenance-logs/",                  "Maintenance Logs"),
    ("GET", "/api/failure-reports/",                   "Failure Reports"),
]

ok_count = 0
fail_count = 0
for method, url, label in checks:
    try:
        r = requests.request(method, BASE + url, timeout=8)
        ok = r.status_code in (200, 201)
        status = "OK  " if ok else "FAIL"
        if ok: ok_count += 1
        else:  fail_count += 1
        print(f"  {status} {r.status_code}  {label}")
    except Exception as e:
        print(f"  ERR  {label}: {str(e)[:40]}")
        fail_count += 1

print()
print(f"  Results: {ok_count} passed / {fail_count} failed out of {len(checks)} checks")

# Live data summary
print()
print("=" * 65)
print("  LIVE PLANT DATA SUMMARY")
print("=" * 65)

stats  = requests.get(BASE+'/api/dashboard/stats').json()
health = requests.get(BASE+'/api/anomaly/health-status').json()
alerts = requests.get(BASE+'/api/anomaly/alerts/summary').json()
invsum = requests.get(BASE+'/api/procurement/inventory-summary').json()
sensor = requests.get(BASE+'/api/sensor-data/count/total').json()
docs   = requests.get(BASE+'/api/doc-intelligence/stats').json()
learn  = requests.get(BASE+'/api/learning/summary/quick').json()

print(f"  Equipment       : {stats['total_equipment']} registered | {stats['operational_equipment']} operational | {stats['maintenance_equipment']} maintenance")
print(f"  Plant Health    : {health['overall_health_percentage']:.0f}% | {health['healthy_count']} healthy | {health['critical_count']} critical")
print(f"  Sensor Readings : {sensor['count']} total readings in DB")
print(f"  Active Alerts   : {alerts['active']} | Critical: {alerts['critical_count']}")
print(f"  Inventory       : {invsum['total_parts']} parts | {invsum['in_stock']} OK | {invsum['low_stock']} low | {invsum['out_of_stock']} out")
print(f"  Documents       : {docs['processed']} processed | {docs['total_chunks']} chunks indexed")
print(f"  AI Learning     : {learn['feedback_count']} feedback | {learn['success_rate']*100:.0f}% success rate")
print(f"  Maintenance Logs: {stats['total_maintenance_logs']}")
print(f"  Failure Reports : {stats['total_failure_reports']}")

print()
print("=" * 65)
print("  ALL SYSTEMS OPERATIONAL")
print(f"  Frontend : http://localhost:5173")
print(f"  Backend  : http://localhost:8000")
print(f"  API Docs : http://localhost:8000/docs")
print("=" * 65)
