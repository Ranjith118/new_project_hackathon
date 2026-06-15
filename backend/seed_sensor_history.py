"""Seed realistic 24-hour sensor history with gradual degradation for charts."""
import requests, time, math, random
from datetime import datetime, timedelta

BASE = 'http://localhost:8000'

equipment_list = [
    'Rolling Mill Motor',
    'Blast Furnace Fan',
    'Cooling Pump A',
    'Main Compressor',
    'Conveyor Belt System',
]

# Profiles: (base_temp, base_vib, base_curr, base_press, base_rpm)
BASES = {
    'Rolling Mill Motor':   (88, 1.8, 22, 82, 1500),
    'Blast Furnace Fan':    (72, 1.5, 42, 200, 980),
    'Cooling Pump A':       (55, 1.0, 27, 42, 1600),
    'Main Compressor':      (78, 1.6, 45, 8, 1500),
    'Conveyor Belt System': (35, 0.8, 16, 4, 1000),
}

# Add 48 readings per equipment (every 30 min = 24h)
total = 0
for eq in equipment_list:
    base = BASES[eq]
    for i in range(48):
        # Time going back 24h
        t = datetime.now() - timedelta(minutes=(48-i)*30)
        # Gradual increase for Rolling Mill Motor (showing degradation)
        drift = i / 48 * 0.3 if eq == 'Rolling Mill Motor' else 0
        noise = lambda v: v + random.gauss(0, v * 0.04)
        
        payload = {
            'equipment_name': eq,
            'temperature': round(noise(base[0] * (1 + drift * 0.25)), 2),
            'vibration':   round(noise(base[1] * (1 + drift * 0.6)), 2),
            'current':     round(noise(base[2] * (1 + drift * 0.15)), 2),
            'pressure':    round(noise(base[3]), 2),
            'rpm':         round(noise(base[4]), 0),
            'timestamp':   t.isoformat(),
        }
        r = requests.post(BASE+'/api/sensor-data/', json=payload)
        if r.status_code == 201:
            total += 1
    print(f'  {eq}: 48 readings seeded')

print(f'\nTotal seeded: {total} readings')

# Final check
ls = requests.get(BASE+'/api/sensor-data/live-status').json()
print('\nLive Status:')
for eq in ls['equipment']:
    alerts = [s for s in eq['sensors'] if s['status'] != 'normal']
    alert_str = f' | ALERTS: {[a["sensor_type"] for a in alerts]}' if alerts else ''
    print(f"  {eq['equipment_name']:<28} Health:{eq['health_score']}% [{eq['health_status']}]{alert_str}")

total_rows = requests.get(BASE+'/api/sensor-data/count/total').json()['count']
print(f'\nTotal sensor readings in DB: {total_rows}')
