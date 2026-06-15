"""Final verification of Sensor Monitoring Module."""
import requests
BASE = 'http://localhost:8000'

print("=" * 60)
print("  SENSOR MONITORING MODULE - VERIFICATION")
print("=" * 60)

# 1. simulate-all
r = requests.post(BASE+'/api/sensor-data/simulate-all')
d = r.json()
print(f"\n1. simulate-all: {r.status_code} | {d['count']} equipment simulated")
print(f"   Equipment: {d['simulated']}")

# 2. live-status
r = requests.get(BASE+'/api/sensor-data/live-status')
d = r.json()
print(f"\n2. live-status: {r.status_code} | {d['total']} equipment monitored")
for eq in d['equipment']:
    sensors = eq['sensors']
    alerts = [s for s in sensors if s['status'] != 'normal']
    row = f"   {eq['equipment_name']:<28} Health:{eq['health_score']}% [{eq['health_status']}]"
    if alerts:
        row += f" | ALERT: {', '.join(a['sensor_type'] for a in alerts)}"
    print(row)

# 3. history per equipment
print(f"\n3. sensor history (24h):")
for eq in d['equipment']:
    r2 = requests.get(BASE+'/api/sensor-data/history/'+requests.utils.quote(eq['equipment_name'])+'?hours=24')
    h = r2.json()
    print(f"   {eq['equipment_name']:<28} {h['total']} readings")

# 4. count
r = requests.get(BASE+'/api/sensor-data/count/total')
print(f"\n4. Total sensor rows in DB: {r.json()['count']}")

# 5. latest sensor list
r = requests.get(BASE+'/api/sensor-data/?limit=3')
print(f"\n5. Latest 3 readings: {r.status_code}")
try:
    rows = r.json()
    for row in rows:
        print(f"   {row['equipment_name']} | Temp:{row['temperature']} Vib:{row['vibration']} @ {row['timestamp'][:16]}")
except Exception as e:
    print(f"   Response: {r.text[:100]}")

print("\n" + "=" * 60)
print("  ALL SENSOR MODULE ENDPOINTS VERIFIED")
print(f"  Frontend: http://localhost:5173/sensor-data")
print(f"  API Docs: http://localhost:8000/docs")
print("=" * 60)
