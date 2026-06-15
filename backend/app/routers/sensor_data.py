"""Sensor data API endpoints."""
import random
import math
from datetime import datetime, timedelta
from typing import Optional, List, Set

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.models import SensorData
from app.schemas.schemas import SensorDataCreate, SensorDataBulk, SensorDataResponse

router = APIRouter(prefix="/api/sensor-data", tags=["Sensor Data"])

# ── In-memory anomaly pin registry ───────────────────────────
# Equipment names added here will be SKIPPED by simulate-all
# so their injected critical readings persist until explicitly cleared.
_pinned_anomalies: Set[str] = set()

# ── Resolve grace set ─────────────────────────────────────────
# After Resolve, machines are added here for 15 seconds so
# simulate-all cannot immediately overwrite the normal reading.
_resolve_graced: Set[str] = set()

import asyncio as _asyncio

async def _remove_grace(name: str, delay: float = 15.0):
    """Remove a machine from the grace set after delay seconds."""
    await _asyncio.sleep(delay)
    _resolve_graced.discard(name)

# ── Equipment sensor profiles ─────────────────────────────────
# (lo, hi, normal, unit, warn, crit)
EQUIPMENT_PROFILES = {
    "Rolling Mill Motor": {
        "temperature": (65, 115, 90,  "°C",   95,  110),
        "vibration":   (0.5, 5.0, 1.8,"mm/s",  2.8, 4.0),
        "current":     (18,  32,  22,  "A",    28,  32),
        "pressure":    (70,  95,  80,  "bar",  90,  95),
        "rpm":         (1400,2200,1500,"rpm", 2000, 2200),
    },
    "Blast Furnace Fan": {
        "temperature": (50, 95,  72, "°C",    85,  93),
        "vibration":   (0.5,4.5, 1.5,"mm/s",  3.0, 4.5),
        "current":     (38, 58,  42, "A",     52,  58),
        "pressure":    (180,250,200, "mbar",  230, 248),
        "rpm":         (940,1020,980,"rpm",  1010,1020),
    },
    "Cooling Pump A": {
        "temperature": (30, 85,  55, "°C",   75,  85),
        "vibration":   (0.3,3.5, 1.0,"mm/s", 2.5, 3.5),
        "current":     (20, 35,  27, "A",    30,  35),
        "pressure":    (30, 55,  42, "bar",  50,  54),
        "rpm":         (1400,1800,1600,"rpm",1750,1800),
    },
    "Main Compressor": {
        "temperature": (60,100,  78, "°C",   90, 100),
        "vibration":   (0.5,4.0, 1.6,"mm/s", 2.8, 4.0),
        "current":     (30, 60,  45, "A",    55,  60),
        "pressure":    (5,  12,  8,  "bar",  11,  12),
        "rpm":         (1450,1550,1500,"rpm",1530,1550),
    },
    "Conveyor Belt System": {
        "temperature": (20, 60,  35, "°C",   50,  60),
        "vibration":   (0.2,2.5, 0.8,"mm/s", 2.0, 2.5),
        "current":     (10, 25,  16, "A",    22,  25),
        "pressure":    (2,  8,   4,  "bar",   7,   8),
        "rpm":         (800,1200,1000,"rpm",1150,1200),
    },
}
DEFAULT_PROFILE = {
    "temperature": (40,100, 70,"°C",   90,100),
    "vibration":   (0.5,4.0,1.5,"mm/s",3.0,4.0),
    "current":     (15, 35, 22,"A",    30, 35),
    "pressure":    (2,  10,  6,"bar",   9, 10),
    "rpm":         (900,1800,1200,"rpm",1700,1800),
}


def _sim_value(profile_key: str, equipment: str) -> dict:
    profile = EQUIPMENT_PROFILES.get(equipment, DEFAULT_PROFILE)
    if profile_key not in profile:
        return None
    lo, hi, normal, unit, warn, crit = profile[profile_key]
    base  = normal + (hi - lo) * 0.12 * math.sin(datetime.now().timestamp() / 55)
    noise = random.gauss(0, (hi - lo) * 0.035)
    value = round(max(lo, min(hi, base + noise)), 2)
    status = "critical" if value >= crit else ("warning" if value >= warn else "normal")
    return {"value": value, "unit": unit, "warn": warn, "crit": crit,
            "lo": lo, "hi": hi, "normal": normal, "status": status}


# ── SPECIFIC routes FIRST (before /{sensor_id}) ──────────────

@router.get("/count/total")
async def count_sensor_data(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(func.count()).select_from(SensorData))
    return {"count": result.scalar()}


@router.get("/anomaly-pins")
async def get_anomaly_pins():
    """Return the set of equipment names currently pinned with anomaly readings."""
    return {"pinned": list(_pinned_anomalies)}


@router.post("/clear-anomaly")
async def clear_anomaly(equipment_name: str):
    """Remove equipment from the anomaly pin registry so simulate-all resumes normal values."""
    _pinned_anomalies.discard(equipment_name)
    return {"status": "cleared", "equipment_name": equipment_name, "pinned": list(_pinned_anomalies)}


@router.post("/simulate")
async def simulate_sensor_reading(equipment_name: str, db: AsyncSession = Depends(get_db)):
    """Generate and store one simulated reading for a named equipment."""
    profile = EQUIPMENT_PROFILES.get(equipment_name, DEFAULT_PROFILE)
    readings = {k: _sim_value(k, equipment_name)["value"] for k in profile}
    db_sensor = SensorData(
        equipment_name=equipment_name,
        temperature=readings.get("temperature"),
        vibration=readings.get("vibration"),
        current=readings.get("current"),
        pressure=readings.get("pressure"),
        rpm=int(round(readings.get("rpm", 1500))),
        timestamp=datetime.now(),
        created_at=datetime.now(),
    )
    db.add(db_sensor); await db.flush(); await db.refresh(db_sensor)
    return db_sensor


@router.post("/simulate-normal")
async def simulate_normal_reading(equipment_name: str, db: AsyncSession = Depends(get_db)):
    """
    Force-insert a reading with all sensors at their NORMAL target value.
    Used by the Resolve button — guarantees the machine returns to healthy state
    regardless of what the random simulator would generate.
    """
    import time as _time
    profile = EQUIPMENT_PROFILES.get(equipment_name, DEFAULT_PROFILE)

    # Use the 'normal' value (index 2) from each sensor profile — well within safe range
    normal_readings = {}
    for sensor_key, params in profile.items():
        lo, hi, normal, unit, warn, crit = params
        normal_readings[sensor_key] = normal

    # Small sleep to guarantee created_at is strictly after any previous row
    await __import__('asyncio').sleep(0.05)

    db_sensor = SensorData(
        equipment_name=equipment_name,
        temperature=normal_readings.get("temperature"),
        vibration=normal_readings.get("vibration"),
        current=normal_readings.get("current"),
        pressure=normal_readings.get("pressure"),
        rpm=int(round(normal_readings.get("rpm", 1500))),
        timestamp=datetime.now(),
        created_at=datetime.now(),
    )
    db.add(db_sensor)
    await db.flush()
    await db.refresh(db_sensor)

    # Add to grace set — simulate-all will skip this machine for 15 seconds
    _resolve_graced.add(equipment_name)
    _asyncio.ensure_future(_remove_grace(equipment_name, 15.0))

    return {
        "status": "resolved",
        "equipment_name": equipment_name,
        "readings": normal_readings,
        "message": f"{equipment_name} restored to normal values",
    }


@router.post("/inject-anomaly")
async def inject_anomaly(
    equipment_name: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """
    Force-insert a critical-level anomaly reading for the given equipment.
    All sensor values are pushed well above their CRITICAL thresholds so the
    health score drops to near 0 and threshold alerts fire immediately.
    """
    profile = EQUIPMENT_PROFILES.get(equipment_name, DEFAULT_PROFILE)

    # Build readings that are above critical threshold for every sensor
    anomaly_readings = {}
    for sensor_key, params in profile.items():
        # params layout: (lo, hi, normal, unit, warn, crit)
        lo, hi, normal, unit, warn, crit = params
        # Go 5 % above crit, capped at hi
        anomaly_val = round(min(hi, crit * 1.05), 2)
        anomaly_readings[sensor_key] = anomaly_val

    db_sensor = SensorData(
        equipment_name=equipment_name,
        temperature=anomaly_readings.get("temperature"),
        vibration=anomaly_readings.get("vibration"),
        current=anomaly_readings.get("current"),
        pressure=anomaly_readings.get("pressure"),
        rpm=int(round(anomaly_readings.get("rpm", 1500))),
        timestamp=datetime.now(),
        created_at=datetime.now(),
    )
    db.add(db_sensor)
    await db.flush()

    # Trigger threshold alert check as background task
    async def _check_anomaly_alerts(eq_name: str, rdg: dict):
        try:
            from app.health.alert_engine import get_alert_engine
            from app.models.models import AlertRecord
            from app.database import async_session_maker
            from sqlalchemy import select as _select
            from datetime import datetime as _dt

            engine = get_alert_engine()
            alerts = engine.check_thresholds(eq_name, rdg)
            async with async_session_maker() as adb:
                old = (await adb.execute(
                    _select(AlertRecord)
                    .where(AlertRecord.equipment_name == eq_name)
                    .where(AlertRecord.status == "active")
                )).scalars().all()
                for o in old:
                    o.status = "resolved"
                    o.resolved_at = _dt.now()
                for a in alerts:
                    adb.add(AlertRecord(
                        alert_id=a.alert_id,
                        equipment_name=a.equipment_name,
                        alert_type=a.alert_type,
                        severity=a.severity,
                        message=a.message,
                        source="anomaly_injection",
                        status="active",
                        created_at=_dt.now(),
                    ))
                await adb.commit()
        except Exception:
            pass

    float_rdg = {k: float(v) for k, v in anomaly_readings.items()}
    background_tasks.add_task(_check_anomaly_alerts, equipment_name, float_rdg)

    # Pin this machine — simulate-all will skip it until cleared
    _pinned_anomalies.add(equipment_name)

    return {
        "status": "anomaly_injected",
        "equipment_name": equipment_name,
        "readings": anomaly_readings,
        "message": f"Critical anomaly injected for {equipment_name} — pinned until cleared",
    }


@router.post("/simulate-all")
async def simulate_all_equipment(
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """Generate one reading for every registered equipment."""
    from app.models.models import Equipment as EquipmentModel
    result = await db.execute(select(EquipmentModel))
    equipment_list = result.scalars().all()
    created = []
    sim_readings = {}  # collect readings for background alert check

    for eq in equipment_list:
        # Skip equipment that has an active injected anomaly — preserve their critical readings
        if eq.equipment_name in _pinned_anomalies:
            continue
        # Skip equipment in resolve grace period — let normal readings settle
        if eq.equipment_name in _resolve_graced:
            continue

        profile = EQUIPMENT_PROFILES.get(eq.equipment_name, DEFAULT_PROFILE)
        readings = {k: _sim_value(k, eq.equipment_name)["value"] for k in profile}
        db_sensor = SensorData(
            equipment_name=eq.equipment_name,
            temperature=readings.get("temperature"),
            vibration=readings.get("vibration"),
            current=readings.get("current"),
            pressure=readings.get("pressure"),
            rpm=int(round(readings.get("rpm", 1500))),
            timestamp=datetime.now(),
        )
        db.add(db_sensor)
        await db.flush()
        created.append(eq.equipment_name)
        sim_readings[eq.equipment_name] = {
            'temperature': readings.get("temperature"),
            'vibration':   readings.get("vibration"),
            'current':     readings.get("current"),
            'pressure':    readings.get("pressure"),
            'rpm':         float(readings.get("rpm", 1500)),
        }

    # Single background task handles all equipment alerts — no ML, just thresholds
    async def _check_all_alerts(all_readings: dict):
        try:
            from app.health.alert_engine import get_alert_engine
            from app.models.models import AlertRecord
            from app.database import async_session_maker
            from sqlalchemy import select as _select
            from datetime import datetime as _dt
            engine = get_alert_engine()
            async with async_session_maker() as adb:
                for eq_name, rdg in all_readings.items():
                    alerts = engine.check_thresholds(eq_name, rdg)
                    old = (await adb.execute(
                        _select(AlertRecord)
                        .where(AlertRecord.equipment_name == eq_name)
                        .where(AlertRecord.status == "active")
                    )).scalars().all()
                    for o in old:
                        o.status = "resolved"; o.resolved_at = _dt.now()
                    for a in alerts:
                        adb.add(AlertRecord(
                            alert_id=a.alert_id, equipment_name=a.equipment_name,
                            alert_type=a.alert_type, severity=a.severity,
                            message=a.message, source="threshold", status="active",
                        ))
                await adb.commit()
        except Exception:
            pass

    if sim_readings:
        background_tasks.add_task(_check_all_alerts, sim_readings)
    return {"status": "ok", "simulated": created, "count": len(created)}


@router.get("/live-status")
async def get_live_status(db: AsyncSession = Depends(get_db)):
    """Latest sensor reading + health score per equipment."""
    from sqlalchemy import text

    # Use subquery: get max(created_at) per equipment, then join to get that exact row
    # This guarantees the most recently INSERTED row wins — not the one with highest fake timestamp
    subq = (
        select(SensorData.equipment_name, func.max(SensorData.created_at).label("max_ca"))
        .group_by(SensorData.equipment_name)
        .subquery()
    )
    stmt = (
        select(SensorData)
        .join(subq, (SensorData.equipment_name == subq.c.equipment_name) &
                    (SensorData.created_at == subq.c.max_ca))
    )
    all_rows = (await db.execute(stmt)).scalars().all()
    latest: dict = { row.equipment_name: row for row in all_rows }

    output = []
    for eq_name, row in latest.items():
        profile = EQUIPMENT_PROFILES.get(eq_name, DEFAULT_PROFILE)
        sensors, penalties = [], []
        for sensor_type, (lo, hi, normal, unit, warn, crit) in profile.items():
            val = getattr(row, sensor_type, None)
            if val is None: continue
            if val >= crit:       st, pen = "critical", 40
            elif val >= warn:     st, pen = "warning",  15
            else:                 st, pen = "normal",   0
            penalties.append(pen)
            sensors.append({"sensor_type": sensor_type, "value": val, "unit": unit,
                             "normal_range": f"{lo}–{hi}", "warn_threshold": warn,
                             "crit_threshold": crit, "status": st,
                             "last_updated": row.timestamp.isoformat()})

        score = max(0, min(100, round(100 - (sum(penalties)/len(penalties) if penalties else 0))))
        if score >= 85:   risk, hs = "Low",      "Healthy"
        elif score >= 60: risk, hs = "Medium",   "Warning"
        elif score >= 40: risk, hs = "High",     "High Risk"
        else:             risk, hs = "Critical", "Critical"

        output.append({"equipment_name": eq_name, "health_score": score,
                        "health_status": hs, "risk_level": risk,
                        "sensors": sensors, "last_updated": row.timestamp.isoformat(),
                        "sensor_count": len(sensors)})

    output.sort(key=lambda x: x["health_score"])
    return {"equipment": output, "total": len(output)}


@router.get("/history/{equipment_name}")
async def get_sensor_history(
    equipment_name: str,
    hours: int = Query(24, ge=1, le=720),
    db: AsyncSession = Depends(get_db)
):
    """Sensor history for one equipment over last N hours."""
    since = datetime.now() - timedelta(hours=hours)
    rows = (await db.execute(
        select(SensorData)
        .where(SensorData.equipment_name == equipment_name)
        .where(SensorData.timestamp >= since)
        .order_by(SensorData.timestamp.asc())
    )).scalars().all()
    return {
        "equipment_name": equipment_name, "hours": hours, "total": len(rows),
        "readings": [{"timestamp": r.timestamp.isoformat(), "temperature": r.temperature,
                       "vibration": r.vibration, "current": r.current,
                       "pressure": r.pressure, "rpm": r.rpm} for r in rows],
    }


# ── CRUD routes ───────────────────────────────────────────────

@router.post("/", response_model=SensorDataResponse, status_code=201)
async def create_sensor_data(
    sensor_data: SensorDataCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    db_sensor = SensorData(**sensor_data.model_dump())
    db.add(db_sensor); await db.flush(); await db.refresh(db_sensor)

    async def _save_alerts(eq_name, readings):
        try:
            from app.health.alert_engine import get_alert_engine
            from app.models.models import AlertRecord
            from app.database import async_session_maker
            from sqlalchemy import select
            from datetime import datetime as _dt
            engine = get_alert_engine()
            threshold_alerts = engine.check_thresholds(eq_name, readings)
            async with async_session_maker() as adb:
                existing = (await adb.execute(
                    select(AlertRecord)
                    .where(AlertRecord.equipment_name == eq_name)
                    .where(AlertRecord.status == "active")
                )).scalars().all()
                for o in existing:
                    o.status = "resolved"; o.resolved_at = _dt.now()
                for a in threshold_alerts:
                    adb.add(AlertRecord(
                        alert_id=a.alert_id, equipment_name=a.equipment_name,
                        alert_type=a.alert_type, severity=a.severity,
                        message=a.message, source="threshold", status="active",
                    ))
                await adb.commit()
        except Exception:
            pass

    readings = {}
    if db_sensor.temperature is not None: readings['temperature'] = db_sensor.temperature
    if db_sensor.vibration   is not None: readings['vibration']   = db_sensor.vibration
    if db_sensor.current     is not None: readings['current']     = db_sensor.current
    if db_sensor.pressure    is not None: readings['pressure']    = db_sensor.pressure
    if db_sensor.rpm         is not None: readings['rpm']         = float(db_sensor.rpm)

    if readings:
        background_tasks.add_task(_save_alerts, db_sensor.equipment_name, readings)

    return db_sensor


async def _save_alerts(eq_name: str, readings: dict):
    """Save threshold alerts + auto-generate failure report if failure probability is high."""
    try:
        from app.health.alert_engine import get_alert_engine
        from app.models.models import AlertRecord, FailureReport
        from app.database import async_session_maker
        from sqlalchemy import select
        from datetime import datetime as _dt, date as _date

        engine = get_alert_engine()
        threshold_alerts = engine.check_thresholds(eq_name, readings)

        async with async_session_maker() as adb:
            # Resolve old active alerts
            old = (await adb.execute(
                select(AlertRecord)
                .where(AlertRecord.equipment_name == eq_name)
                .where(AlertRecord.status == "active")
            )).scalars().all()
            for o in old:
                o.status = "resolved"; o.resolved_at = _dt.now()

            # Save new threshold alerts
            for a in threshold_alerts:
                adb.add(AlertRecord(
                    alert_id=a.alert_id, equipment_name=a.equipment_name,
                    alert_type=a.alert_type, severity=a.severity,
                    message=a.message, source="threshold", status="active",
                ))

            # Auto failure report when critical conditions detected
            if threshold_alerts:
                critical = [a for a in threshold_alerts if a.alert_type == "critical"]
                if critical:
                    # Check if failure probability is high
                    try:
                        import numpy as np
                        from app.prediction.failure_model import get_failure_predictor
                        fp = get_failure_predictor()
                        if fp.is_trained:
                            t  = readings.get("temperature", 75)
                            v  = readings.get("vibration", 1.5)
                            c  = readings.get("current", 20)
                            p  = readings.get("pressure", 70)
                            r  = readings.get("rpm", 1500)
                            X  = np.array([[t, v, c, p, r]])
                            prob = float(fp.predict_proba(X)[0])
                            if prob >= 0.6:  # 60%+ failure probability
                                cause = "Sensor threshold exceeded"
                                if t > 110: cause = "Overheating — temperature critically high"
                                elif v > 4.0: cause = "Excessive vibration — bearing/mechanical fault"
                                elif c > 32: cause = "Overcurrent — electrical fault"
                                report = FailureReport(
                                    equipment_name=eq_name,
                                    failure_type="Predicted Failure — Critical Sensor Alert",
                                    root_cause=cause,
                                    downtime_hours=0.0,
                                    report_date=_date.today(),
                                )
                                adb.add(report)
                    except Exception:
                        pass

            await adb.commit()
    except Exception:
        pass


@router.post("/bulk", status_code=201)
async def bulk_create_sensor_data(bulk_data: SensorDataBulk, db: AsyncSession = Depends(get_db)):
    created, errors = 0, []
    for idx, reading in enumerate(bulk_data.readings):
        try:
            db.add(SensorData(**reading.model_dump())); created += 1
        except Exception as e:
            errors.append({"row": idx + 1, "error": str(e)})
    await db.flush()
    return {"created": created, "errors": errors or None, "total": len(bulk_data.readings)}


@router.get("/", response_model=List[SensorDataResponse])
async def list_sensor_data(
    skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=1000),
    equipment_name: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    query = select(SensorData)
    if equipment_name:
        query = query.where(SensorData.equipment_name.ilike(f"%{equipment_name}%"))
    query = query.offset(skip).limit(limit).order_by(SensorData.timestamp.desc())
    return (await db.execute(query)).scalars().all()


@router.get("/{sensor_id}", response_model=SensorDataResponse)
async def get_sensor_data(sensor_id: str, db: AsyncSession = Depends(get_db)):
    sensor = (await db.execute(select(SensorData).where(SensorData.sensor_id == sensor_id))).scalar_one_or_none()
    if not sensor: raise HTTPException(404, "Sensor data not found")
    return sensor


@router.delete("/{sensor_id}", status_code=204)
async def delete_sensor_data(sensor_id: str, db: AsyncSession = Depends(get_db)):
    sensor = (await db.execute(select(SensorData).where(SensorData.sensor_id == sensor_id))).scalar_one_or_none()
    if not sensor: raise HTTPException(404, "Sensor data not found")
    await db.delete(sensor)
