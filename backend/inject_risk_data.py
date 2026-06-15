"""Inject high-risk sensor readings to show realistic predictions."""
import requests
BASE = 'http://localhost:8000'

# Critical readings for each equipment
readings = [
    {'equipment_name': 'Rolling Mill Motor', 'temperature': 108, 'vibration': 4.1, 'current': 30, 'pressure': 87, 'rpm': 2050},
    {'equipment_name': 'Blast Furnace Fan',  'temperature': 91,  'vibration': 3.9, 'current': 54, 'pressure': 242,'rpm': 1012},
    {'equipment_name': 'Cooling Pump A',     'temperature': 79,  'vibration': 3.0, 'current': 32, 'pressure': 51, 'rpm': 1755},
    {'equipment_name': 'Main Compressor',    'temperature': 93,  'vibration': 3.4, 'current': 57, 'pressure': 11, 'rpm': 1542},
    {'equipment_name': 'Conveyor Belt System','temperature': 55, 'vibration': 2.1, 'current': 23, 'pressure': 7,  'rpm': 1150},
]
for r in readings:
    requests.post(BASE+'/api/anomaly/predict', json=r)

# Check predictions
preds = requests.get(BASE+'/api/prediction/equipment-predictions').json()
seen = set()
print("Equipment Predictions:")
for p in preds['predictions']:
    if p['equipment_name'] not in seen:
        seen.add(p['equipment_name'])
        name = p['equipment_name'][:28]
        fp   = str(round(p['failure_probability'], 1))
        rul  = str(p['rul_days'])
        risk = p['risk_level']
        deg  = p['degradation_level']
        print(f"  {name:<28} Fail:{fp}%  RUL:{rul}d  [{risk}]  {deg}")

print()
print("Total:", preds['total'], "| Critical:", preds['critical_count'], "| High:", preds['high_risk_count'])
print()
print("Page is live at: http://localhost:5173/predictive")
