import asyncio, httpx
from datetime import datetime

async def test():
    async with httpx.AsyncClient() as c:
        # Test 1: check alert engine thresholds directly
        from app.health.alert_engine import get_alert_engine
        engine = get_alert_engine()
        readings = {'temperature': 125.0, 'vibration': 5.5, 'current': 35.0, 'pressure': 98.0, 'rpm': 2300.0}
        # Clear dedup keys first
        engine._active_keys.clear()
        alerts = engine.check_thresholds('Rolling Mill Motor', readings)
        print(f"Direct threshold check: {len(alerts)} alerts")
        for a in alerts:
            print(f"  [{a.alert_type.upper()}] {a.message[:60]}")

        # Test 2: now save via API and check DB
        critical = {
            'equipment_name': 'Rolling Mill Motor',
            'temperature': 125.0, 'vibration': 5.5, 'current': 35.0,
            'pressure': 98.0, 'rpm': 2300,
            'timestamp': datetime.now().isoformat()
        }
        r = await c.post('http://localhost:8000/api/sensor-data/', json=critical, timeout=10)
        print(f"\nSensor save: {r.status_code}")
        await asyncio.sleep(3)

        r2 = await c.get('http://localhost:8000/api/alerts', timeout=10)
        d = r2.json()
        print(f"DB alerts after save: total={d.get('total')} active={d.get('active_count')}")
        for a in d.get('alerts', [])[:5]:
            print(f"  [{a.get('alert_type','').upper()}] {a.get('status')} | {a.get('message','')[:55]}")

asyncio.run(test())
