"""
Seed script — populates the Maintenance Wizard database with realistic
steel plant data: equipment, sensor readings, maintenance logs,
failure reports, and spare parts.
"""
import asyncio
import uuid
from datetime import datetime, date, timedelta
import random
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from app.database import async_session_maker, engine, Base
from app.models.models import Equipment, SensorData, MaintenanceLog, FailureReport, SparePart

random.seed(42)

# ── Equipment ────────────────────────────────────────────────────────────────
EQUIPMENT = [
    {"equipment_name": "Blast Furnace Fan #1",      "equipment_type": "compressor", "manufacturer": "Siemens",    "status": "operational",   "installation_date": date(2018, 3, 15)},
    {"equipment_name": "Blast Furnace Fan #2",      "equipment_type": "compressor", "manufacturer": "Siemens",    "status": "maintenance",   "installation_date": date(2018, 3, 15)},
    {"equipment_name": "Rolling Mill Motor A",      "equipment_type": "motor",      "manufacturer": "ABB",        "status": "operational",   "installation_date": date(2019, 7, 20)},
    {"equipment_name": "Rolling Mill Motor B",      "equipment_type": "motor",      "manufacturer": "ABB",        "status": "operational",   "installation_date": date(2019, 7, 20)},
    {"equipment_name": "Main Cooling Pump #1",      "equipment_type": "pump",       "manufacturer": "Grundfos",   "status": "operational",   "installation_date": date(2020, 1, 10)},
    {"equipment_name": "Main Cooling Pump #2",      "equipment_type": "pump",       "manufacturer": "Grundfos",   "status": "failed",        "installation_date": date(2020, 1, 10)},
    {"equipment_name": "Slab Reheating Furnace",    "equipment_type": "furnace",    "manufacturer": "Tenova",     "status": "operational",   "installation_date": date(2017, 5, 5)},
    {"equipment_name": "Hot Rolling Mill",          "equipment_type": "mill",       "manufacturer": "SMS Group",  "status": "operational",   "installation_date": date(2016, 11, 30)},
    {"equipment_name": "Cold Rolling Mill",         "equipment_type": "mill",       "manufacturer": "SMS Group",  "status": "operational",   "installation_date": date(2017, 2, 14)},
    {"equipment_name": "Conveyor Belt System #1",   "equipment_type": "conveyor",   "manufacturer": "Rexnord",    "status": "operational",   "installation_date": date(2021, 6, 1)},
    {"equipment_name": "Conveyor Belt System #2",   "equipment_type": "conveyor",   "manufacturer": "Rexnord",    "status": "operational",   "installation_date": date(2021, 6, 1)},
    {"equipment_name": "Overhead Crane Motor #1",   "equipment_type": "crane",      "manufacturer": "Konecranes", "status": "operational",   "installation_date": date(2015, 9, 18)},
    {"equipment_name": "Overhead Crane Motor #2",   "equipment_type": "crane",      "manufacturer": "Konecranes", "status": "maintenance",   "installation_date": date(2015, 9, 18)},
    {"equipment_name": "Air Compressor Unit",       "equipment_type": "compressor", "manufacturer": "Atlas Copco","status": "operational",   "installation_date": date(2022, 3, 7)},
    {"equipment_name": "Hydraulic Power Unit",      "equipment_type": "hydraulic",  "manufacturer": "Bosch Rexroth","status": "operational", "installation_date": date(2020, 8, 22)},
    {"equipment_name": "Lubrication System",        "equipment_type": "system",     "manufacturer": "SKF",        "status": "operational",   "installation_date": date(2019, 4, 11)},
    {"equipment_name": "Water Treatment Pump",      "equipment_type": "pump",       "manufacturer": "Sulzer",     "status": "operational",   "installation_date": date(2023, 1, 5)},
    {"equipment_name": "Dust Collection Fan",       "equipment_type": "fan",        "manufacturer": "Howden",     "status": "operational",   "installation_date": date(2021, 11, 20)},
]

# ── Sensor profiles per equipment type ───────────────────────────────────────
SENSOR_PROFILES = {
    "compressor": {"temp": (70, 15), "vib": (1.2, 0.4), "curr": (22, 4),  "press": (75, 8),  "rpm": (1450, 150)},
    "motor":      {"temp": (75, 12), "vib": (1.5, 0.5), "curr": (20, 3),  "press": (70, 7),  "rpm": (1500, 200)},
    "pump":       {"temp": (65, 10), "vib": (1.0, 0.3), "curr": (18, 3),  "press": (80, 10), "rpm": (1200, 100)},
    "furnace":    {"temp": (90, 20), "vib": (0.8, 0.2), "curr": (30, 5),  "press": (60, 5),  "rpm": (800, 80)},
    "mill":       {"temp": (80, 15), "vib": (2.0, 0.6), "curr": (25, 5),  "press": (72, 8),  "rpm": (1350, 180)},
    "conveyor":   {"temp": (55, 8),  "vib": (0.9, 0.3), "curr": (15, 3),  "press": (50, 5),  "rpm": (900, 100)},
    "crane":      {"temp": (60, 10), "vib": (1.1, 0.4), "curr": (17, 3),  "press": (55, 6),  "rpm": (1000, 120)},
    "hydraulic":  {"temp": (68, 12), "vib": (0.7, 0.2), "curr": (16, 2),  "press": (85, 10), "rpm": (1100, 100)},
    "system":     {"temp": (50, 8),  "vib": (0.5, 0.2), "curr": (12, 2),  "press": (45, 5),  "rpm": (700, 80)},
    "fan":        {"temp": (58, 10), "vib": (1.3, 0.4), "curr": (16, 3),  "press": (52, 6),  "rpm": (1300, 150)},
}

# ── Maintenance log templates ─────────────────────────────────────────────────
MAINTENANCE_TEMPLATES = [
    {"issue": "High vibration detected during routine check",              "action": "Bearing inspected and lubricated. Vibrat