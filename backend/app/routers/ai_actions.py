"""
AI-Guided Data Entry Actions.
The AI assistant calls these endpoints to save data collected via conversation.
"""
import json
from datetime import datetime, date
from typing import Optional

from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.models import Equipment, SensorData, MaintenanceLog
from app.config import settings

router = APIRouter(prefix="/api/ai-actions", tags=["AI Actions"])


# ── Save Equipment ────────────────────────────────────────────
@router.post("/save-equipment")
async def ai_save_equipment(
    equipment_name: str = Form(...),
    equipment_type: str = Form(...),
    manufacturer: Optional[str] = Form(default=None),
    installation_date: Optional[str] = Form(default=None),
    status: str = Form(default="operational"),
    db: AsyncSession = Depends(get_db),
):
    inst_date = None
    if installation_date:
        try:
            inst_date = date.fromisoformat(installation_date)
        except Exception:
            pass

    eq = Equipment(
        equipment_name=equipment_name.strip(),
        equipment_type=equipment_type.strip(),
        manufacturer=manufacturer.strip() if manufacturer else None,
        installation_date=inst_date,
        status=status,
    )
    db.add(eq)
    await db.flush()
    await db.refresh(eq)
    return {
        "success": True,
        "message": f"Equipment '{equipment_name}' saved successfully.",
        "equipment_id": eq.equipment_id,
    }


# ── Save Sensor Reading ───────────────────────────────────────
@router.post("/save-sensor")
async def ai_save_sensor(
    equipment_name: str = Form(...),
    temperature: Optional[float] = Form(default=None),
    vibration: Optional[float] = Form(default=None),
    current: Optional[float] = Form(default=None),
    pressure: Optional[float] = Form(default=None),
    rpm: Optional[int] = Form(default=None),
    db: AsyncSession = Depends(get_db),
):
    reading = SensorData(
        equipment_name=equipment_name.strip(),
        temperature=temperature,
        vibration=vibration,
        current=current,
        pressure=pressure,
        rpm=rpm,
        timestamp=datetime.now(),
    )
    db.add(reading)
    await db.flush()
    await db.refresh(reading)
    return {
        "success": True,
        "message": f"Sensor reading for '{equipment_name}' saved successfully.",
        "sensor_id": reading.sensor_id,
    }


# ── Save Maintenance Log ──────────────────────────────────────
@router.post("/save-maintenance-log")
async def ai_save_maintenance_log(
    equipment_name: str = Form(...),
    issue: str = Form(...),
    action_taken: Optional[str] = Form(default=None),
    downtime_hours: float = Form(default=0.0),
    severity: str = Form(default="medium"),
    technician: Optional[str] = Form(default=None),
    maintenance_date: Optional[str] = Form(default=None),
    db: AsyncSession = Depends(get_db),
):
    mdate = date.today()
    if maintenance_date:
        try:
            mdate = date.fromisoformat(maintenance_date)
        except Exception:
            pass

    if severity not in ("low", "medium", "high", "critical"):
        severity = "medium"

    log = MaintenanceLog(
        equipment_name=equipment_name.strip(),
        issue=issue.strip(),
        action_taken=action_taken.strip() if action_taken else None,
        downtime_hours=downtime_hours,
        severity=severity,
        technician=technician.strip() if technician else None,
        maintenance_date=mdate,
    )
    db.add(log)
    await db.flush()
    await db.refresh(log)
    return {
        "success": True,
        "message": f"Maintenance log for '{equipment_name}' saved successfully.",
        "log_id": log.log_id,
    }


# ── Upload Manual via AI ──────────────────────────────────────
@router.post("/upload-manual")
async def ai_upload_manual(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    """Upload and auto-process a manual/document through the AI pipeline."""
    import uuid
    from pathlib import Path
    from app.models.models import IntelligentDocument

    suffix = Path(file.filename).suffix.lower()
    allowed = {".pdf", ".docx", ".txt", ".csv"}
    if suffix not in allowed:
        raise HTTPException(400, f"File type {suffix} not supported. Use: PDF, DOCX, TXT, CSV")

    upload_dir = Path("./data/intelligent_docs")
    upload_dir.mkdir(parents=True, exist_ok=True)

    doc_id = str(uuid.uuid4())
    saved_name = f"{doc_id}_{file.filename}"
    save_path = upload_dir / saved_name
    content = await file.read()

    with open(save_path, "wb") as f:
        f.write(content)

    doc = IntelligentDocument(
        doc_id=doc_id,
        file_name=file.filename,
        file_path=str(save_path),
        file_type=suffix,
        file_size=len(content),
        processing_status="uploaded",
    )
    db.add(doc)
    await db.flush()

    return {
        "success": True,
        "doc_id": doc_id,
        "file_name": file.filename,
        "message": f"'{file.filename}' uploaded. Starting AI analysis...",
        "next_step": "process",
    }


# ── AI Conversation handler ───────────────────────────────────
@router.post("/chat")
async def ai_action_chat(
    message: str = Form(...),
    conversation_state: str = Form(default="{}"),
    live_context: str = Form(default=""),
):
    """
    Central AI chat that handles both Q&A and conversational data entry.
    Returns structured response with optional action to perform.
    """
    from groq import Groq

    state = {}
    try:
        state = json.loads(conversation_state)
    except Exception:
        pass

    client = Groq(api_key=settings.GROQ_API_KEY)

    system_prompt = """You are an AI Maintenance Assistant for a steel manufacturing plant. You ONLY help with:

1. ANSWER questions about equipment, maintenance, failures, sensors, manuals, spare parts, plant operations.
2. COLLECT DATA from the user to save into the maintenance system.

STRICT RULE — OFF-TOPIC REJECTION:
If the user asks ANYTHING not related to industrial maintenance, equipment, steel plant operations,
sensors, spare parts, failures, or maintenance procedures — respond with:
"I can only assist with industrial maintenance and steel plant operations. Please ask me about
equipment health, failures, maintenance procedures, spare parts, sensor readings, or plant operations."

EXAMPLES OF OFF-TOPIC (MUST REJECT):
- Programming questions (Python, Java, algorithms)
- General science or math questions
- Weather, news, sports, entertainment
- Cooking, travel, personal advice

FORMATTING RULES — VERY IMPORTANT:
- Do NOT use markdown symbols like **, ##, ###, *, __, or backticks in your message field.
- Use plain text only in the "message" field.
- Use dash (-) for bullet points, numbers (1. 2. 3.) for steps.
- Use UPPERCASE for section headings (e.g. DIAGNOSIS:, RECOMMENDED ACTIONS:).
- Keep responses clean and readable without any markdown formatting.

INTENTS you can detect:
- ADD_EQUIPMENT: User wants to add/register new equipment
- ADD_SENSOR: User wants to enter sensor/measurement data
- ADD_MAINTENANCE_LOG: User wants to log a maintenance activity or issue
- UPLOAD_MANUAL: User wants to upload a machine manual or document
- QUERY: User is asking a question (default)

RESPONSE FORMAT (always return valid JSON):
{
  "intent": "QUERY|ADD_EQUIPMENT|ADD_SENSOR|ADD_MAINTENANCE_LOG|UPLOAD_MANUAL",
  "message": "Your conversational reply to the user",
  "collecting": true/false,
  "collected_data": { ...fields collected so far... },
  "next_field": "field_name_to_ask_next or null",
  "next_question": "The question to ask the user for the next field, or null",
  "ready_to_save": true/false,
  "save_endpoint": "/api/ai-actions/save-equipment etc or null",
  "save_payload": { ...final data to save... }
}

DATA COLLECTION FLOWS:

### ADD_EQUIPMENT fields (in order):
1. equipment_name (required) - "What is the name of the equipment?"
2. equipment_type (required) - "What type is it? (Motor, Fan, Pump, Compressor, Conveyor, etc.)"
3. manufacturer (optional) - "Who is the manufacturer? (or say 'skip')"
4. installation_date (optional) - "When was it installed? (YYYY-MM-DD or 'skip')"
5. status - default "operational", ask "What is its current status? (operational/maintenance/failed)"

### ADD_SENSOR fields (in order):
1. equipment_name (required) - "Which equipment are you reading sensors for?"
2. temperature (optional) - "Temperature in °C? (or skip)"
3. vibration (optional) - "Vibration in mm/s? (or skip)"
4. current (optional) - "Current in Amperes? (or skip)"
5. pressure (optional) - "Pressure in bar/mbar? (or skip)"
6. rpm (optional) - "RPM value? (or skip)"

### ADD_MAINTENANCE_LOG fields (in order):
1. equipment_name (required) - "Which equipment had the maintenance/issue?"
2. issue (required) - "Describe the issue or maintenance performed?"
3. severity (required) - "Severity level? (low/medium/high/critical)"
4. action_taken (optional) - "What action was taken? (or skip if not done yet)"
5. technician (optional) - "Technician name? (or skip)"
6. downtime_hours (optional) - "How many hours of downtime? (or 0)"
7. maintenance_date (optional) - "Date of maintenance? (YYYY-MM-DD or today)"

### UPLOAD_MANUAL:
- Just tell user to click the upload button in the chat

## RULES:
- If collecting data and user says "skip", move to next field
- When all required fields are collected, set ready_to_save=true and fill save_payload
- For dates, use today's date if user says "today"
- severity must be one of: low, medium, high, critical
- status must be: operational, maintenance, failed
- Always be friendly and confirm what you're collecting
- If intent is QUERY, just answer based on live_context and your knowledge
"""

    user_prompt = f"""Current conversation state: {json.dumps(state)}

User message: {message}

Live plant context:
{live_context[:3000] if live_context else 'Not available'}

Respond with valid JSON only."""

    try:
        completion = client.chat.completions.create(
            model=settings.LLM_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.2,
            max_tokens=1000,
        )
        raw = completion.choices[0].message.content.strip()

        # Extract JSON from the response
        if "```json" in raw:
            raw = raw.split("```json")[1].split("```")[0].strip()
        elif "```" in raw:
            raw = raw.split("```")[1].split("```")[0].strip()

        result = json.loads(raw)
        return result

    except json.JSONDecodeError:
        # Fallback: return as plain query answer
        return {
            "intent": "QUERY",
            "message": raw if 'raw' in dir() else "I couldn't process that. Please try again.",
            "collecting": False,
            "collected_data": {},
            "next_field": None,
            "next_question": None,
            "ready_to_save": False,
            "save_endpoint": None,
            "save_payload": None,
        }
    except Exception as e:
        return {
            "intent": "QUERY",
            "message": f"Error: {str(e)}",
            "collecting": False,
            "collected_data": {},
            "next_field": None,
            "next_question": None,
            "ready_to_save": False,
            "save_endpoint": None,
            "save_payload": None,
        }
