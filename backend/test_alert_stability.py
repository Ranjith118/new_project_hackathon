import requests
BASE = 'http://localhost:8000'

print("Simulating 10 rapid dashboard refreshes...")
for i in range(10):
    requests.get(BASE+'/api/dashboard/stats')
    requests.get(BASE+'/api/anomaly/health-status')
    requests.get(BASE+'/api/anomaly/alerts/summary')
    requests.get(BASE+'/api/anomaly/alerts')

r = requests.get(BASE+'/api/anomaly/alerts/summary').json()
total    = r['total']
active   = r['active']
critical = r['critical_count']
print("Total   :", total)
print("Active  :", active)
print("Critical:", critical)
print()
if total <= 10:
    print("STABLE - alerts do not grow on dashboard refresh")
else:
    print("PROBLEM - alert count too high")
