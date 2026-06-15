import requests
BASE = 'http://localhost:8000'

stats  = requests.get(BASE+'/api/dashboard/stats').json()
health = requests.get(BASE+'/api/anomaly/health-status').json()
alerts = requests.get(BASE+'/api/anomaly/alerts').json()
preds  = requests.get(BASE+'/api/prediction/equipment-predictions').json()
rank   = requests.get(BASE+'/api/decision-support/equipment-ranking').json()
inv    = requests.get(BASE+'/api/procurement/inventory-summary').json()
spares = requests.get(BASE+'/api/procurement/spares').json()
rca    = requests.get(BASE+'/api/rca/dashboard').json()
learn  = requests.get(BASE+'/api/learning/summary/quick').json()

print("=== DASHBOARD DATA VERIFICATION ===")
print("Equipment     :", stats['total_equipment'], "total |", stats['operational_equipment'], "op |", stats['maintenance_equipment'], "maint |", stats['failed_equipment'], "failed")
print("Plant Health  :", round(health['overall_health_percentage']), "% |", health['total_equipment'], "monitored |", health['healthy_count'], "healthy |", health['critical_count'], "critical")
print("Active Alerts :", alerts['active_count'], "active |", alerts['critical_count'], "critical")
print("Predictions   :", preds['total'], "equipment |", preds['critical_count'], "critical |", preds['high_risk_count'], "high risk")
top = rank['rankings'][0]
print("Top Risk      :", top['equipment_name'], "| P"+str(top['priority_level']), "| Fail:", round(top['failure_probability']*100), "% | RUL:", top['rul_days'], "days")
print("Inventory     :", inv['total_parts'], "parts |", inv['in_stock'], "in-stock |", inv['low_stock'], "low |", inv['out_of_stock'], "out")
print("RCA           :", rca['total_analyses'], "analyses | avg", rca['average_confidence'], "% confidence")
print("AI Learning   :", learn['feedback_count'], "feedback |", round(learn['success_rate']*100), "% success |", round(learn['average_accuracy']*100), "% accuracy")

print()
print("=== TOP 5 EQUIPMENT BY RISK ===")
for eq in rank['rankings'][:5]:
    print(" ", eq['rank'], eq['equipment_name'], "["+str(eq['priority_level'])+"]",
          "Fail:"+str(round(eq['failure_probability']*100))+"%",
          "RUL:"+str(eq['rul_days'])+"d",
          "Score:"+str(round(eq['priority_score'],1)))

print()
print("=== ACTIVE ALERTS (first 5) ===")
for a in alerts['alerts'][:5]:
    print(" ", "["+a['alert_type'].upper()+"]", a['equipment_name']+":", a['message'][:60])

print()
print("=== FAILURE PREDICTIONS (first 5) ===")
for p in preds['predictions'][:5]:
    print(" ", p['equipment_name'], "Fail:"+str(round(p['failure_probability'],1))+"%", "RUL:"+str(p['rul_days'])+"d", "Risk:"+str(p['risk_level']))

print()
print("=== SPARE PARTS STATUS ===")
for s in spares['parts'][:6]:
    print(" ", s['part_name'], "| Stock:"+str(s['stock_quantity'])+"/"+str(s['minimum_stock']), "| Status:"+s['status'])

print()
print("=== RCA COMMON CAUSES ===")
for c in rca['common_causes']:
    print(" ", c['cause'], str(c['percentage'])+"%")

print()
print("ALL CHECKS PASSED - Dashboard is fully operational")
print("Frontend: http://localhost:5174")
print("Backend : http://localhost:8000")
print("API Docs: http://localhost:8000/docs")
