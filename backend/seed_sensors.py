import requests, time

BASE = 'http://localhost:8000'
total = 0
for i in range(20):
    r = requests.post(BASE+'/api/sensor-data/simulate-all')
    total += r.json().get('count', 0)
    time.sleep(0.3)
print(f'Seeded {total} readings across 20 rounds')

ls = requests.get(BASE+'/api/sensor-data/live-status').json()
for eq in ls['equipment']:
    print(f"  {eq['equipment_name']:<28} Health:{eq['health_score']}% [{eq['health_status']}] Sensors:{eq['sensor_count']}")

hist = requests.get(BASE+'/api/sensor-data/history/Rolling%20Mill%20Motor?hours=2').json()
print(f'History rows (Rolling Mill Motor): {hist["total"]}')
