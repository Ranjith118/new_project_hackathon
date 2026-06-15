import requests
BASE = 'http://localhost:8000'

r = requests.post(BASE+'/api/sensor-data/simulate-all')
print('simulate-all:', r.status_code, r.json()['count'], 'equipment')

r2 = requests.get(BASE+'/api/sensor-data/live-status')
d = r2.json()
print('live-status:', r2.status_code, d['total'], 'equipment')
for eq in d['equipment']:
    parts = [s['sensor_type']+'='+str(s['value'])+s['unit']+'['+s['status']+']' for s in eq['sensors']]
    print(' ', eq['equipment_name'][:28], 'Health:'+str(eq['health_score'])+'%', '|', ' '.join(parts[:3]))

r3 = requests.get(BASE+'/api/sensor-data/history/Rolling%20Mill%20Motor?hours=2')
print('history (2h):', r3.status_code, r3.json()['total'], 'readings')

r4 = requests.get(BASE+'/api/sensor-data/history/Blast%20Furnace%20Fan?hours=2')
print('history BFF  :', r4.status_code, r4.json()['total'], 'readings')

print('ALL SENSOR ENDPOINTS OK')
