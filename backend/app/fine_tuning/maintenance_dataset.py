"""
Steel Plant Maintenance Q&A Dataset for LoRA Fine-Tuning.
Domain-specific instruction-tuning data for industrial maintenance LLM.
"""

MAINTENANCE_QA_DATASET = [
    # ── Bearing Failures ────────────────────────────────────
    {
        "instruction": "Why is the Rolling Mill Motor vibrating excessively?",
        "context": "Rolling Mill Motor | Vibration: 4.8 mm/s | Temperature: 95°C | RPM: 1520 | Last bearing replacement: 14 months ago",
        "response": "DIAGNOSIS: Bearing wear is the primary cause.\n\nEVIDENCE:\n- Vibration at 4.8 mm/s exceeds critical threshold of 4.0 mm/s\n- Temperature at 95°C indicates friction from worn bearing surfaces\n- Bearing age of 14 months exceeds typical 12-month replacement interval\n\nROOT CAUSE: Bearing B6205 wear due to lubrication degradation\n\nIMMEDIATE ACTIONS:\n1. Reduce motor load by 30% immediately\n2. Check lubrication level and quality\n3. Schedule bearing replacement within 48 hours\n4. Order spare bearing B6205 from supplier\n\nRISK: Critical — continued operation risks bearing seizure and catastrophic motor failure\nCONFIDENCE: 94%"
    },
    {
        "instruction": "What is the procedure to replace bearing B6205 on Rolling Mill Motor?",
        "context": "Equipment: Rolling Mill Motor | Bearing type: B6205 deep groove ball bearing | Motor power: 75kW",
        "response": "BEARING REPLACEMENT PROCEDURE — Rolling Mill Motor B6205:\n\n⚠️ SAFETY FIRST: Lockout/Tagout (LOTO) before starting\n\nTOOLS REQUIRED: Bearing puller, hydraulic press, torque wrench, temperature gun\n\nSTEPS:\n1. Isolate motor from power supply — apply LOTO\n2. Drain residual lubrication from bearing housing\n3. Remove end cover bolts (8x M12, torque: 45 Nm)\n4. Use bearing puller to extract worn B6205 bearing\n5. Clean bearing housing with solvent — inspect for scoring\n6. Heat new bearing to 80°C using induction heater\n7. Press new bearing onto shaft — do not hammer directly\n8. Apply fresh grease — Shell Gadus S2 V220 2, 15g\n9. Reassemble end cover, torque to 45 Nm in cross pattern\n10. Reconnect power, run at 50% load for 30 minutes\n11. Check vibration (<2.8 mm/s) and temperature (<90°C)\n\nESTIMATED TIME: 3–4 hours\nPARTS: Bearing B6205, Grease, Gasket set"
    },
    {
        "instruction": "What spare parts are needed for Rolling Mill Motor bearing failure?",
        "context": "Failure type: Bearing seizure | Equipment: Rolling Mill Motor 75kW",
        "response": "SPARE PARTS REQUIRED:\n\nCRITICAL (order immediately):\n1. Deep groove ball bearing B6205 — Qty: 2 (1 install + 1 spare)\n2. Bearing housing gasket set — Qty: 1 set\n3. Shell Gadus S2 V220 2 grease — Qty: 500g\n\nRECOMMENDED (order with bearing):\n4. Oil seal 45x62x8 — Qty: 2\n5. M12 hex bolts grade 8.8 — Qty: 8\n6. Loctite 243 thread locker — Qty: 1 tube\n\nSUPPLIER: SKF India Ltd\nLEAD TIME: 3–5 days standard, 1 day express\nUNIT COST: ₹2,800 per bearing B6205\nTOTAL ESTIMATED COST: ₹8,500"
    },

    # ── Blast Furnace Fan ────────────────────────────────────
    {
        "instruction": "Blast Furnace Fan pressure has dropped suddenly. What is the cause?",
        "context": "Blast Furnace Fan | Pressure: 165 mbar (normal: 200 mbar) | Vibration: 3.2 mm/s | Current: 48A | RPM: 975",
        "response": "DIAGNOSIS: Sudden pressure drop indicates impeller damage or ducting blockage.\n\nEVIDENCE:\n- Pressure at 165 mbar — 17.5% below normal operating range of 200 mbar\n- Vibration elevated to 3.2 mm/s suggests impeller imbalance or blade damage\n- Current at 48A is within normal range — eliminates motor fault\n- RPM normal at 975 — eliminates speed control issue\n\nPROBABLE CAUSES (ranked by confidence):\n1. Impeller blade erosion — 78% confidence\n2. Ducting obstruction or leak — 65% confidence\n3. Inlet filter blockage — 55% confidence\n\nIMMEDIATE ACTIONS:\n1. Inspect inlet filter — clean or replace if >70% blocked\n2. Check ducting for leaks, cracks, or loose flanges\n3. If no ducting issue, shut down and inspect impeller blades\n4. Do NOT increase RPM to compensate — risks catastrophic imbalance\n\nRISK: High — reduced blast affects furnace temperature and steel quality\nCONFIDENCE: 82%"
    },
    {
        "instruction": "What is the maintenance schedule for Blast Furnace Fan?",
        "context": "Equipment: Blast Furnace Fan | Running hours: 8760/year (continuous operation)",
        "response": "BLAST FURNACE FAN — MAINTENANCE SCHEDULE:\n\nDAILY (every shift):\n- Check inlet pressure and flow rate\n- Verify vibration levels (<3.0 mm/s)\n- Check bearing temperature (<85°C)\n- Inspect for unusual noise\n\nWEEKLY:\n- Clean inlet filter screens\n- Check belt tension (if belt drive)\n- Inspect flexible coupling for wear\n- Verify lubrication level in bearing housing\n\nMONTHLY:\n- Full vibration analysis with spectrum analyzer\n- Bearing re-lubrication: Shell Gadus S2 V100, 20g per bearing\n- Check impeller for erosion or deposits\n- Inspect shaft seal for leaks\n- Measure motor insulation resistance\n\nQUARTERLY:\n- Impeller dynamic balance check\n- Full ducting inspection for erosion\n- Motor winding resistance measurement\n- Coupling alignment check — max 0.05mm offset\n\nANNUAL SHUTDOWN:\n- Replace all bearings\n- Impeller surface coating inspection\n- Full motor overhaul\n- Non-destructive testing of fan casing welds"
    },

    # ── Cooling Pump ─────────────────────────────────────────
    {
        "instruction": "Cooling Pump A is showing high current draw. What does this indicate?",
        "context": "Cooling Pump A | Current: 33A (normal: 27A) | Temperature: 72°C | Pressure: 36 bar | RPM: 1590",
        "response": "DIAGNOSIS: High current draw of 33A (22% above normal) indicates mechanical overload.\n\nEVIDENCE:\n- Current 33A exceeds warning threshold of 30A and approaches critical 35A\n- Temperature at 72°C is elevated (normal: 55°C) — confirms increased work\n- Pressure at 36 bar is normal — eliminates system pressure issue\n- RPM normal at 1590\n\nPROBABLE CAUSES:\n1. Pump cavitation — 72% confidence (most common cause of current spike)\n2. Mechanical seal failure causing friction — 65% confidence\n3. Impeller clogging with debris — 58% confidence\n4. Motor winding degradation — 35% confidence\n\nIMMEDIATE ACTIONS:\n1. Check suction valve — ensure fully open (cavitation cause)\n2. Inspect strainer/filter on suction side — clean if blocked\n3. Listen for rattling sound (confirms cavitation)\n4. Check mechanical seal for leakage around pump shaft\n5. If no improvement in 2 hours — reduce load and inspect\n\nSAFETY: Do not run >35A for extended period — risk of motor burnout\nRISK: Medium-High\nCONFIDENCE: 87%"
    },

    # ── Main Compressor ──────────────────────────────────────
    {
        "instruction": "Main Compressor discharge pressure is fluctuating. What should I check?",
        "context": "Main Compressor | Pressure oscillating 7–11 bar (normal: 8 bar steady) | Vibration: 2.1 mm/s | Temperature: 82°C",
        "response": "DIAGNOSIS: Pressure oscillation indicates valve issues or load cycling problems.\n\nEVIDENCE:\n- Pressure swings of ±2 bar around setpoint indicate unstable compression\n- Vibration within normal range — eliminates mechanical unbalance\n- Temperature slightly elevated — consistent with inefficient compression\n\nPROBABLE CAUSES:\n1. Suction/discharge valve wear — 81% confidence\n2. Pressure regulator malfunction — 70% confidence\n3. Air leak in discharge piping — 62% confidence\n4. Piston ring wear causing blow-by — 45% confidence\n\nDIAGNOSTIC STEPS:\n1. Check pressure regulator setpoint and response\n2. Listen for valve chatter during operation\n3. Perform leak-down test on discharge system\n4. Check intercooler for blockage\n5. Review valve condition on last maintenance record\n\nIMMEDIATE ACTIONS:\n1. Reduce compressor load to 70% while investigating\n2. Inspect check valves on discharge side\n3. Verify safety relief valve is not leaking\n\nRISK: Medium — process disruption if pressure falls below 6 bar\nCONFIDENCE: 79%"
    },

    # ── General Maintenance Knowledge ────────────────────────
    {
        "instruction": "What does a health score of 45% mean for steel plant equipment?",
        "context": "Equipment health monitoring system | Health score calculated from sensor deviations",
        "response": "HEALTH SCORE 45% — INTERPRETATION:\n\nA health score of 45% places the equipment in the HIGH RISK zone (40–59% range).\n\nWHAT IT MEANS:\n- Multiple sensor parameters showing degraded performance\n- Equipment is functional but operating inefficiently\n- Failure probability is elevated — likely 55–70%\n- Remaining useful life estimate: 15–30 days\n\nTYPICAL CAUSES AT THIS SCORE:\n- Temperature 10–15°C above optimal\n- Vibration 1.5–2x normal baseline\n- Current draw elevated by 15–25%\n- Or any single sensor in critical zone\n\nREQUIRED ACTIONS:\n1. Increase monitoring frequency to every 2 hours\n2. Schedule maintenance inspection within 72 hours\n3. Prepare spare parts for likely failure components\n4. Notify maintenance supervisor\n5. Prepare contingency plan for emergency shutdown\n\nDO NOT:\n- Increase production load on this equipment\n- Defer maintenance beyond 3 days\n\nREFERENCE THRESHOLD TABLE:\n- 85–100%: Healthy — normal monitoring\n- 60–84%: Warning — increased monitoring\n- 40–59%: High Risk — schedule maintenance\n- 0–39%: Critical — immediate action required"
    },
    {
        "instruction": "How often should lubrication be applied to motor bearings in a steel plant?",
        "context": "Steel plant environment | High dust, high temperature, continuous operation",
        "response": "LUBRICATION SCHEDULE FOR STEEL PLANT MOTOR BEARINGS:\n\nSTANDARD SCHEDULE (ISO 6743-9 guidelines, steel plant conditions):\n\nSMALL MOTORS (< 15kW):\n- Grease interval: Every 2,000 hours or 3 months\n- Grease type: NLGI Grade 2, high-temperature\n- Quantity: 5–10g per bearing\n\nMEDIUM MOTORS (15–75kW) — e.g., Rolling Mill Motor:\n- Grease interval: Every 1,500 hours or 2 months\n- Grease type: Shell Gadus S2 V220 2\n- Quantity: 15–20g per bearing\n\nLARGE MOTORS (> 75kW):\n- Grease interval: Every 1,000 hours or 6 weeks\n- Grease type: Shell Gadus S3 V220 C2 (high-temp, high-load)\n- Quantity: 25–35g per bearing\n\nSTEEL PLANT ADJUSTMENT FACTORS:\n- High dust environment: Reduce interval by 25%\n- Temperature >80°C: Reduce interval by 30%\n- Continuous 24/7 operation: Reduce interval by 20%\n\nWARNING SIGNS OF UNDER-LUBRICATION:\n- Bearing temperature >10°C above baseline\n- High-pitched squealing noise\n- Vibration increase >0.5 mm/s\n\nWARNING SIGNS OF OVER-LUBRICATION:\n- Bearing running hot without increased load\n- Grease leaking from seals\n- Increased current draw"
    },
    {
        "instruction": "What is Remaining Useful Life (RUL) and how is it calculated?",
        "context": "Predictive maintenance system | AI-based RUL calculation",
        "response": "REMAINING USEFUL LIFE (RUL) — EXPLANATION:\n\nDEFINITION:\nRUL is the estimated number of days a piece of equipment can continue operating before it requires major maintenance or replacement.\n\nHOW IT IS CALCULATED IN THIS SYSTEM:\n\n1. SENSOR BASELINE COMPARISON\n   - Current sensor values compared to healthy operating baseline\n   - Deviation score calculated for each parameter\n\n2. DEGRADATION RATE ANALYSIS\n   - Historical trend of each sensor over past 30 days\n   - Rate of degradation extrapolated to failure threshold\n\n3. MACHINE LEARNING MODEL\n   - Random Forest Regressor trained on steel plant failure history\n   - Features: Temperature, Vibration, Current, Pressure, RPM\n   - Output: Days until predicted failure (0–100 day range)\n\n4. CONFIDENCE INTERVAL\n   - 95% confidence bounds provided (lower/upper RUL)\n   - Based on prediction variance across 100 decision trees\n\nINTERPRETATION GUIDE:\n- RUL > 60 days: Plan maintenance in next scheduled shutdown\n- RUL 30–60 days: Schedule maintenance within 4 weeks\n- RUL 15–30 days: Schedule maintenance within 2 weeks — URGENT\n- RUL 7–15 days: Immediate maintenance planning required\n- RUL < 7 days: CRITICAL — prepare for emergency shutdown\n\nACCURACY: ±5 days (MAE) based on model validation"
    },
    {
        "instruction": "Conveyor Belt System is showing intermittent stops. What is the root cause?",
        "context": "Conveyor Belt System | Current spikes to 24A then drops | Vibration: 1.8 mm/s | Temperature: 42°C | RPM: fluctuating 950–1050",
        "response": "DIAGNOSIS: Intermittent stops with current spikes indicate drive or mechanical issue.\n\nEVIDENCE:\n- Current spikes to 24A (normal: 16A) — 50% overload during stops\n- RPM fluctuation 950–1050 (normal: 1000 steady) — speed control instability\n- Vibration within normal range — no bearing issue\n- Temperature normal — no thermal issue\n\nPROBABLE CAUSES:\n1. Belt slippage or misalignment — 76% confidence\n2. Overload on belt (material buildup) — 71% confidence\n3. Drive coupling wear or failure — 65% confidence\n4. VFD/drive controller fault — 58% confidence\n5. Belt tension too low — 52% confidence\n\nDIAGNOSTIC STEPS:\n1. Check belt tension — should be 2–3% elongation under load\n2. Inspect belt for misalignment at tail pulley\n3. Check for material buildup at transfer points\n4. Inspect drive coupling for wear, backlash, or cracks\n5. Review VFD fault log for overcurrent trips\n\nIMMEDIATE ACTIONS:\n1. Reduce belt loading by 20%\n2. Check and adjust belt tracking screws\n3. Clear any material blockages at chutes\n4. If stops continue — check VFD parameters\n\nRISK: Medium — production disruption\nCONFIDENCE: 83%"
    },
    {
        "instruction": "What safety precautions must be followed before any maintenance on steel plant equipment?",
        "context": "Steel plant safety protocol | Equipment maintenance | ISO 45001 compliance",
        "response": "MANDATORY SAFETY PRECAUTIONS — STEEL PLANT EQUIPMENT MAINTENANCE:\n\n🔴 LOCKOUT/TAGOUT (LOTO) — MANDATORY FOR ALL WORK:\n1. Identify ALL energy sources (electrical, hydraulic, pneumatic, thermal)\n2. Notify shift supervisor before starting\n3. Shut down equipment using normal stopping procedure\n4. Isolate main power at MCC (Motor Control Center)\n5. Apply personal lock + danger tag — EACH TECHNICIAN applies own lock\n6. Verify zero energy state — test with voltage meter\n7. Drain/bleed all hydraulic/pneumatic pressure\n8. Allow thermal equipment to cool to <40°C before touching\n\nPERSONAL PROTECTIVE EQUIPMENT (PPE):\n- Safety helmet\n- Safety glasses or face shield\n- Insulated gloves (Class 00 minimum for electrical)\n- Safety boots (steel toe cap)\n- High-visibility vest\n- Hearing protection (>85 dB areas)\n\nHOT WORK ADDITIONAL REQUIREMENTS:\n- Hot work permit from safety officer\n- Fire extinguisher within 10 meters\n- Fire watch during and 30 minutes after work\n\nCONFINED SPACE ENTRY:\n- Confined space entry permit\n- Gas test (O2, CO, H2S, explosive gases)\n- Standby man posted at entry\n- Rescue equipment on standby\n\nDO NOT START WORK WITHOUT:\n✅ LOTO applied and verified\n✅ Permit to Work signed\n✅ All PPE worn\n✅ Supervisor notified"
    },
]


def get_dataset() -> list:
    """Return the full maintenance Q&A dataset."""
    return MAINTENANCE_QA_DATASET


def get_dataset_stats() -> dict:
    """Return dataset statistics."""
    return {
        "total_samples": len(MAINTENANCE_QA_DATASET),
        "equipment_covered": [
            "Rolling Mill Motor",
            "Blast Furnace Fan",
            "Cooling Pump A",
            "Main Compressor",
            "Conveyor Belt System"
        ],
        "topic_categories": [
            "Bearing Failure Diagnosis",
            "Replacement Procedures",
            "Spare Parts",
            "Maintenance Schedules",
            "Health Score Interpretation",
            "Lubrication",
            "RUL Explanation",
            "Root Cause Analysis",
            "Safety Procedures"
        ],
        "format": "instruction-context-response (Alpaca format)",
        "domain": "Steel Plant Industrial Maintenance",
        "language": "English"
    }
