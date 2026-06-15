"""Seed 24h sensor history using bulk insert - fast."""
import asyncio, random, math
from datetime import datetime, timedelta

async def seed():
    import warnings; warnings.filterwarnings('ignore')
    import sys; sys.path.insert(0, '.')
    from app.database import async_session_maker
    from app.models.models import SensorData

    BASES = {
        'Rolling Mill Motor':   (88, 1.8, 22, 82, 1500),
        'Blast Furnace Fan':    (72, 1.5, 42, 200, 980),
        'Cooling Pump A':       (55, 1.0, 27, 42, 1600),
        'Main Compressor':      (78, 1.6, 45, 8, 1500),
        'Conveyor Belt System': (35, 0.8, 16, 4, 1000),
    }

    async with async_session_maker() as db:
        records = []
        for eq, (bt, bv, bc, bp, br) in BASES.items():
            for i in range(48):  # every 30 min = 24h
                t = datetime.now() - timedelta(minutes=(48 - i) * 30)
                drift = (i / 48) * 0.35 if eq == 'Rolling Mill Motor' else 0
                n = lambda v, pct=0.04: round(max(0, v * (1 + drift) + random.gauss(0, v * pct)), 2)
                records.append(SensorData(
                    equipment_name=eq,
                    temperature=n(bt, 0.05),
                    vibration=round(n(bv * (1 + drift * 0.8), 0.06), 3),
                    current=n(bc, 0.04),
                    pressure=n(bp, 0.03),
                    rpm=int(round(n(br, 0.02))),
                    timestamp=t,
                ))

        for rec in records:
            db.add(rec)
        await db.commit()
        print(f'Inserted {len(records)} records')

    # Show live status
    from app.routers.sensor_data import EQUIPMENT_PROFILES, DEFAULT_PROFILE, _sim_value
    from app.database import async_session_maker
    from app.models.models import SensorData as SD
    from sqlalchemy import select, desc
    async with async_session_maker() as db:
        rows = (await db.execute(select(SD).order_by(desc(SD.timestamp)))).scalars().all()
        latest = {}
        for r in rows:
            if r.equipment_name not in latest:
                latest[r.equipment_name] = r
        for eq, row in latest.items():
            temp = row.temperature or 0
            vib  = row.vibration  or 0
            status = 'CRITICAL' if (temp > 100 or vib > 3.5) else ('WARNING' if (temp > 90 or vib > 2.5) else 'normal')
            print(f"  {eq:<28} Temp:{temp:.1f} Vib:{vib:.2f} Status:{status}")

        total = (await db.execute(select(SD))).scalars().all()
        print(f'\nTotal sensor rows in DB: {len(total)}')

asyncio.run(seed())
