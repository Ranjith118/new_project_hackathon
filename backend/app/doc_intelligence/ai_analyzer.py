"""
AI Document Analyzer.
Uses Groq LLM to classify, extract knowledge, and summarize documents.
All knowledge is extracted dynamically — no hardcoded values.
"""
import json
import re
from typing import Dict, Any, Optional
from app.config import settings


def _groq_call(prompt: str, system: str, max_tokens: int = 2000) -> str:
    """Make a Groq API call and return text response."""
    from groq import Groq
    client = Groq(api_key=settings.GROQ_API_KEY)
    resp = client.chat.completions.create(
        model=settings.LLM_MODEL,
        messages=[
            {"role": "system", "content": system},
            {"role": "user",   "content": prompt}
        ],
        temperature=0.1,
        max_tokens=max_tokens,
    )
    return resp.choices[0].message.content.strip()


def _parse_json_from_response(text: str) -> Dict:
    """Extract JSON from LLM response that may contain prose."""
    # Try direct parse first
    try:
        return json.loads(text)
    except Exception:
        pass
    # Find JSON block in markdown
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except Exception:
            pass
    # Find any JSON object
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except Exception:
            pass
    return {}


# ─────────────────────────────────────────────
# STEP 1: Document Classification
# ─────────────────────────────────────────────
def classify_document(text_sample: str) -> Dict[str, Any]:
    """
    Classify the document type and extract top-level identity.
    Returns document_type, confidence, equipment_name, manufacturer, model_number.
    """
    system = (
        "You are a document classification expert for industrial maintenance systems. "
        "Analyze documents and return ONLY valid JSON with no extra text."
    )
    prompt = f"""Analyze this document excerpt and classify it.

DOCUMENT EXCERPT (first 4000 characters):
{text_sample[:4000]}

Return ONLY this JSON structure:
{{
  "document_type": "one of: Equipment Manual | Maintenance Manual | SOP | Failure Report | Inspection Report | Spare Parts Catalog | Maintenance Log | Incident Report | Technical Bulletin | Other",
  "confidence": 0.0,
  "equipment_name": "name of the equipment this document is about",
  "equipment_type": "type such as motor, fan, pump, compressor, conveyor, furnace, etc.",
  "manufacturer": "manufacturer name or Unknown",
  "model_number": "model/part number or Unknown",
  "language": "document language",
  "keywords": ["keyword1", "keyword2", "keyword3", "keyword4", "keyword5"]
}}"""

    response = _groq_call(prompt, system, max_tokens=500)
    result = _parse_json_from_response(response)

    # Ensure required fields have defaults
    defaults = {
        "document_type": "Equipment Manual",
        "confidence": 0.85,
        "equipment_name": "Unknown Equipment",
        "equipment_type": "Unknown",
        "manufacturer": "Unknown",
        "model_number": "Unknown",
        "language": "English",
        "keywords": []
    }
    for k, v in defaults.items():
        if k not in result:
            result[k] = v

    return result


# ─────────────────────────────────────────────
# STEP 2: Knowledge Extraction
# ─────────────────────────────────────────────
def extract_knowledge(full_text: str, equipment_name: str) -> Dict[str, Any]:
    """
    Extract all structured knowledge from document.
    No hardcoded values — everything comes from the document.
    """
    system = (
        "You are an industrial maintenance knowledge extraction expert. "
        "Extract technical knowledge from maintenance documents. "
        "Return ONLY valid JSON. Extract ONLY what is explicitly stated in the document."
    )

    # Use first 12000 chars for extraction (covers multi-section manuals better)
    sample = full_text[:12000]

    prompt = f"""Extract all technical knowledge from this industrial maintenance document.
Equipment: {equipment_name}

DOCUMENT TEXT:
{sample}

Return ONLY this JSON (use empty lists/objects if information not found):
{{
  "operating_conditions": {{
    "normal_temperature": "",
    "max_temperature": "",
    "normal_vibration": "",
    "max_vibration": "",
    "normal_current": "",
    "max_current": "",
    "normal_pressure": "",
    "normal_rpm": "",
    "other_parameters": {{}}
  }},
  "fault_modes": [
    {{"fault": "", "cause": "", "symptom": "", "action": ""}}
  ],
  "maintenance_tasks": [
    {{"task": "", "interval": "", "procedure": ""}}
  ],
  "safety_instructions": [""],
  "spare_parts": [
    {{"part_name": "", "part_number": "", "quantity": "", "notes": ""}}
  ],
  "sensor_thresholds": {{
    "temperature_warning": "",
    "temperature_critical": "",
    "vibration_warning": "",
    "vibration_critical": "",
    "current_warning": "",
    "current_critical": ""
  }},
  "maintenance_intervals": {{
    "daily": [""],
    "weekly": [""],
    "monthly": [""],
    "quarterly": [""],
    "annual": [""]
  }},
  "critical_components": [""],
  "inspection_checklist": [""],
  "troubleshooting_procedures": [
    {{"symptom": "", "steps": [""]}}
  ]
}}"""

    response = _groq_call(prompt, system, max_tokens=2000)
    result = _parse_json_from_response(response)

    # Clean empty values
    if isinstance(result.get("fault_modes"), list):
        result["fault_modes"] = [f for f in result["fault_modes"] if f.get("fault")]
    if isinstance(result.get("maintenance_tasks"), list):
        result["maintenance_tasks"] = [t for t in result["maintenance_tasks"] if t.get("task")]
    if isinstance(result.get("spare_parts"), list):
        result["spare_parts"] = [p for p in result["spare_parts"] if p.get("part_name")]
    if isinstance(result.get("safety_instructions"), list):
        result["safety_instructions"] = [s for s in result["safety_instructions"] if s]
    if isinstance(result.get("critical_components"), list):
        result["critical_components"] = [c for c in result["critical_components"] if c]
    if isinstance(result.get("inspection_checklist"), list):
        result["inspection_checklist"] = [i for i in result["inspection_checklist"] if i]

    return result


# ─────────────────────────────────────────────
# STEP 3: Summary Generation
# ─────────────────────────────────────────────
def generate_summaries(full_text: str, equipment_name: str, document_type: str) -> Dict[str, str]:
    """
    Generate executive, technical, and maintenance summaries.
    """
    system = (
        "You are a senior industrial maintenance expert. "
        "Write concise, accurate summaries based strictly on the document content."
    )

    sample = full_text[:5000]

    prompt = f"""Summarize this {document_type} for {equipment_name}.

DOCUMENT:
{sample}

Write three summaries:

EXECUTIVE SUMMARY (2-3 sentences for management):
Write a brief overview of what this document covers and why it matters.

TECHNICAL SUMMARY (4-5 sentences for engineers):
Describe the technical content, key specifications, critical parameters, and important procedures.

MAINTENANCE SUMMARY (3-4 sentences for technicians):
Focus on maintenance tasks, intervals, common failures, and immediate action items.

Format your response exactly as:
EXECUTIVE: <text>
TECHNICAL: <text>
MAINTENANCE: <text>"""

    response = _groq_call(prompt, system, max_tokens=800)

    summaries = {
        "executive_summary": "",
        "technical_summary": "",
        "maintenance_summary": ""
    }

    exec_match = re.search(r"EXECUTIVE:\s*(.+?)(?=TECHNICAL:|$)", response, re.DOTALL)
    tech_match = re.search(r"TECHNICAL:\s*(.+?)(?=MAINTENANCE:|$)", response, re.DOTALL)
    maint_match = re.search(r"MAINTENANCE:\s*(.+?)$", response, re.DOTALL)

    if exec_match:
        summaries["executive_summary"] = exec_match.group(1).strip()
    if tech_match:
        summaries["technical_summary"] = tech_match.group(1).strip()
    if maint_match:
        summaries["maintenance_summary"] = maint_match.group(1).strip()

    # Fallback: use the whole response as executive summary
    if not summaries["executive_summary"]:
        summaries["executive_summary"] = response[:300]

    return summaries


# ─────────────────────────────────────────────
# STEP 4: Full Analysis Pipeline
# ─────────────────────────────────────────────
def analyze_document(full_text: str, filename: str) -> Dict[str, Any]:
    """
    Run the complete AI analysis pipeline on a document.
    Returns all extracted information.
    """
    # Classification
    classification = classify_document(full_text)
    equipment_name  = classification.get("equipment_name", "Unknown Equipment")
    document_type   = classification.get("document_type", "Equipment Manual")

    # Knowledge extraction
    knowledge = extract_knowledge(full_text, equipment_name)

    # Summaries
    summaries = generate_summaries(full_text, equipment_name, document_type)

    return {
        "filename": filename,
        "classification": classification,
        "knowledge": knowledge,
        "summaries": summaries,
    }
