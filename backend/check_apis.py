import requests
BASE = 'http://localhost:8000'
apis = [
    '/api/dashboard/stats',
    '/api/anomaly/health-status',
    '/api/anomaly/alerts',
    '/api/anomaly/alerts/summary',
    '/api/prediction/equipment-predictions',
    '/api/decision-support/equipment-ranking',
    '/api/procurement/inventory-summary',
    '/api/procurement/spares',
    '/api/rca/dashboard',
    '/api/learning/summary/quick',
]
all_ok = True
for a in apis:
    try:
        r = requests.get(BASE + a, timeout=5)
        ok = r.status_code == 200
        if not ok:
            all_ok = False
        label = 'OK  ' if ok else 'FAIL'
        print(f'  {label} {r.status_code}  {a}')
    except Exception as e:
        print(f'  ERR  {a}: {e}')
        all_ok = False
print()
print('Result:', 'ALL APIS OK' if all_ok else 'SOME FAILED')
