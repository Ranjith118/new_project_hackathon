import { useState, useEffect, useRef, useCallback } from 'react';
import {
  Send, Brain, RefreshCw, Trash2, BookOpen, AlertTriangle,
  CheckCircle, ChevronRight, Activity, Package, Wrench,
  FileText, Zap, Search, Shield, Plus, Upload, X,
  ClipboardList, Cpu, Image, HelpCircle, ChevronDown,
  Camera, Lightbulb, Database, TrendingUp, Bell
} from 'lucide-react';

const API  = 'http://localhost:8000';
const DAPI = 'http://localhost:8000/api/doc-intelligence';
const get  = (url) => fetch(url).then(r => r.json()).catch(() => null);

// Strip markdown symbols from AI responses
function cleanText(text) {
  if (!text) return '';
  return text
    .replace(/#{1,6}\s*/g, '')          // ## headings
    .replace(/\*\*(.+?)\*\*/g, '$1')    // **bold**
    .replace(/\*(.+?)\*/g, '$1')        // *italic*
    .replace(/__(.+?)__/g, '$1')        // __underline__
    .replace(/`{1,3}([^`]*)`{1,3}/g, '$1') // `code`
    .replace(/^\s*[-*]\s+/gm, '- ')    // normalize bullet points
    .replace(/\n{3,}/g, '\n\n')         // collapse extra blank lines
    .trim();
}

const Card = ({ children, className = '' }) => (
  <div className={`bg-[#1E293B] border border-[#334155] rounded-xl ${className}`}>{children}</div>
);

const INTENT_META = {
  ADD_EQUIPMENT:       { color:'text-blue-400',   bg:'bg-blue-500/10 border-blue-500/20',    icon:Cpu,           label:'Adding Equipment'     },
  ADD_SENSOR:          { color:'text-green-400',  bg:'bg-green-500/10 border-green-500/20',  icon:Activity,      label:'Entering Sensor Data' },
  ADD_MAINTENANCE_LOG: { color:'text-yellow-400', bg:'bg-yellow-500/10 border-yellow-500/20',icon:ClipboardList, label:'Logging Maintenance'  },
  UPLOAD_MANUAL:       { color:'text-purple-400', bg:'bg-purple-500/10 border-purple-500/20',icon:BookOpen,      label:'Uploading Manual'     },
  QUERY:               { color:'text-orange-400', bg:'bg-orange-500/10 border-orange-500/20',icon:Brain,         label:'AI Analysis'          },
};

const INTENT_FIELDS = {
  ADD_EQUIPMENT:       ['equipment_name','equipment_type','manufacturer','installation_date','status'],
  ADD_SENSOR:          ['equipment_name','temperature','vibration','current','pressure','rpm'],
  ADD_MAINTENANCE_LOG: ['equipment_name','issue','severity','action_taken','technician','downtime_hours','maintenance_date'],
};

const QUICK_ACTIONS = [
  { icon:Cpu,           label:'Add Equipment',      prompt:'I want to add a new equipment',                     color:'text-blue-400'   },
  { icon:Activity,      label:'Sensor Readings',    prompt:'I want to enter sensor readings for equipment',      color:'text-green-400'  },
  { icon:ClipboardList, label:'Log Maintenance',    prompt:'I want to log a maintenance activity',              color:'text-yellow-400' },
  { icon:AlertTriangle, label:'Active Alerts',      prompt:'What are the active alerts in the plant right now?',color:'text-red-400'    },
  { icon:Search,        label:'Root Cause',         prompt:'Analyze the root cause of the most critical issue.',color:'text-cyan-400'   },
  { icon:Zap,           label:'Failure Prediction', prompt:'Which equipment is most likely to fail soon?',      color:'text-orange-400' },
  { icon:Package,       label:'Spare Parts',        prompt:'Which spare parts are critically low?',             color:'text-pink-400'   },
  { icon:Camera,        label:'Analyze Image',      prompt:'I want to upload an equipment image for analysis',  color:'text-indigo-400' },
];

const GUIDANCE_SECTIONS = [
  {
    title:'Data Entry via AI', icon:Database, color:'text-blue-400', bg:'bg-blue-500/5 border-blue-500/20',
    items:[
      { label:'Register Equipment',  example:'"Add new Rolling Mill Motor to the system"',       icon:Cpu,           color:'text-blue-400'   },
      { label:'Enter Sensor Data',   example:'"Enter sensor data for Blast Furnace Fan"',         icon:Activity,      color:'text-green-400'  },
      { label:'Log Maintenance',     example:'"Log bearing replacement on Cooling Pump A"',       icon:ClipboardList, color:'text-yellow-400' },
      { label:'Upload Manual',       example:'Click 📎 to upload PDF/DOCX/TXT manuals',           icon:BookOpen,      color:'text-purple-400' },
      { label:'Analyze Image',       example:'Click 🖼 to upload equipment photos for analysis',  icon:Camera,        color:'text-indigo-400' },
    ]
  },
  {
    title:'Diagnostics & Analysis', icon:Search, color:'text-cyan-400', bg:'bg-cyan-500/5 border-cyan-500/20',
    items:[
      { label:'Root Cause Analysis', example:'"Why is Rolling Mill Motor overheating?"',          icon:Search,        color:'text-cyan-400'   },
      { label:'Failure Prediction',  example:'"Which equipment will fail in the next 7 days?"',   icon:TrendingUp,    color:'text-orange-400' },
      { label:'Plant Health',        example:'"Show overall plant health status"',                icon:Activity,      color:'text-green-400'  },
      { label:'Alert Analysis',      example:'"What are the critical alerts right now?"',         icon:Bell,          color:'text-red-400'    },
      { label:'Image Analysis',      example:'"Analyze this bearing image for damage signs"',     icon:Camera,        color:'text-indigo-400' },
    ]
  },
  {
    title:'Maintenance Guidance', icon:Wrench, color:'text-yellow-400', bg:'bg-yellow-500/5 border-yellow-500/20',
    items:[
      { label:'Step-by-step repair', example:'"How do I replace bearing B6205?"',                icon:Wrench,        color:'text-yellow-400' },
      { label:'Safety procedures',   example:'"Safety steps before motor maintenance?"',          icon:Shield,        color:'text-emerald-400'},
      { label:'Spare parts needed',  example:'"What parts do I need for bearing failure?"',       icon:Package,       color:'text-pink-400'   },
      { label:'Maintenance schedule',example:'"Show maintenance schedule for Blast Furnace Fan"', icon:ClipboardList, color:'text-blue-400'   },
      { label:'Lubrication guide',   example:'"How often to lubricate Rolling Mill Motor?"',      icon:Lightbulb,     color:'text-amber-400'  },
    ]
  },
  {
    title:'Document Intelligence', icon:BookOpen, color:'text-purple-400', bg:'bg-purple-500/5 border-purple-500/20',
    items:[
      { label:'Manual Q&A',          example:'"Show bearing specs from the uploaded manual"',     icon:FileText,      color:'text-purple-400' },
      { label:'Fault codes',         example:'"What does fault code ERR-204 mean?"',              icon:AlertTriangle, color:'text-red-400'    },
      { label:'Sensor thresholds',   example:'"Safe temperature limits for the motor?"',          icon:Activity,      color:'text-green-400'  },
      { label:'SOP procedures',      example:'"Show startup procedure from the SOP"',             icon:BookOpen,      color:'text-blue-400'   },
    ]
  },
];

async function gatherContext() {
  const [equipment, alerts, liveStatus, predictions, spares, maintLogs, liveSummary] = await Promise.all([
    get(`${API}/api/equipment/?limit=20`),
    get(`${API}/api/alerts?limit=50`),
    get(`${API}/api/sensor-data/live-status`),
    get(`${API}/api/prediction/equipment-predictions`),
    get(`${API}/api/procurement/spares`),
    get(`${API}/api/maintenance-logs/?limit=10`),
    get(`${API}/api/hub/live-summary`),
  ]);

  const lines = [];
  const now = new Date().toLocaleTimeString();
  lines.push(`=== LIVE PLANT SNAPSHOT @ ${now} ===`);

  // ── Registered equipment ───────────────────────────────
  if (Array.isArray(equipment) && equipment.length > 0) {
    lines.push('\n=== REGISTERED EQUIPMENT ===');
    equipment.forEach(e => lines.push(`- ${e.equipment_name} (${e.equipment_type}) | Status: ${e.status}`));
  }

  // ── Live sensor readings ───────────────────────────────
  if (liveStatus?.equipment?.length > 0) {
    lines.push('\n=== LIVE SENSOR READINGS (fresh from DB) ===');
    liveStatus.equipment.forEach(eq => {
      const sensors = (eq.sensors || []).map(s =>
        `${s.sensor_type}=${Number(s.value).toFixed(1)}${s.unit}[${s.status}]`
      ).join(' ');
      lines.push(`- ${eq.equipment_name}: Health ${eq.health_score}% | Risk: ${eq.risk_level} | ${sensors}`);
    });
    // Flag critical/warning sensors explicitly
    const abnormal = liveStatus.equipment.flatMap(eq =>
      (eq.sensors || [])
        .filter(s => s.status !== 'normal')
        .map(s => `${eq.equipment_name} ${s.sensor_type}: ${Number(s.value).toFixed(1)}${s.unit} [${s.status.toUpperCase()}]`)
    );
    if (abnormal.length > 0) {
      lines.push('\n⚠ ABNORMAL SENSOR VALUES:');
      abnormal.forEach(x => lines.push(`  ! ${x}`));
    }
  }

  // ── Active alerts ──────────────────────────────────────
  const activeAlerts = (alerts?.alerts || []).filter(a => a.status === 'active');
  if (activeAlerts.length > 0) {
    lines.push(`\n=== ACTIVE ALERTS (${activeAlerts.length}) ===`);
    activeAlerts.forEach(a =>
      lines.push(`- [${a.alert_type?.toUpperCase()}] ${a.equipment_name}: ${a.message}`)
    );
  } else {
    lines.push('\n=== ACTIVE ALERTS: None ===');
  }

  // ── Live hub summary ───────────────────────────────────
  if (liveSummary) {
    lines.push(`\n=== LIVE PLANT STATUS ===`);
    lines.push(`Critical alerts: ${liveSummary.critical_count} | Total active: ${liveSummary.active_alert_count}`);
    if (liveSummary.recent_failures?.length > 0) {
      lines.push('Recent failure reports:');
      liveSummary.recent_failures.forEach(f => lines.push(`  - ${f.equipment}: ${f.type} (${f.date})`));
    }
  }

  // ── Failure predictions ────────────────────────────────
  const preds = predictions?.predictions || [];
  if (preds.length > 0) {
    lines.push('\n=== FAILURE PREDICTIONS ===');
    preds.slice(0, 8).forEach(p =>
      lines.push(`- ${p.equipment_name}: Failure prob ${p.failure_probability?.toFixed(1)}% | RUL: ${p.rul_days}d | Risk: ${p.risk_level}`)
    );
  }

  // ── Spare parts ────────────────────────────────────────
  const parts = spares?.parts || [];
  if (parts.length > 0) {
    lines.push('\n=== SPARE PARTS INVENTORY ===');
    parts.forEach(p => lines.push(`- ${p.part_name}: Stock ${p.stock_quantity}/${p.minimum_stock} | ${p.status}`));
  }

  // ── Recent maintenance ─────────────────────────────────
  if (Array.isArray(maintLogs) && maintLogs.length > 0) {
    lines.push('\n=== RECENT MAINTENANCE LOGS ===');
    maintLogs.slice(0, 5).forEach(l => lines.push(`- ${l.equipment_name} (${l.maintenance_date}): ${l.issue}`));
  }

  return lines.join('\n');
}

function CollectionProgress({ intent, collectedData, fields }) {
  if (!intent || intent === 'QUERY') return null;
  const meta = INTENT_META[intent]; if (!meta) return null;
  const Icon = meta.icon;
  const filled = Object.keys(collectedData || {}).filter(k => collectedData[k] != null && collectedData[k] !== '').length;
  const pct = Math.round((filled / (fields?.length || 1)) * 100);
  return (
    <div className={`flex items-center gap-3 px-3 py-2 rounded-lg border ${meta.bg}`}>
      <Icon className={`w-4 h-4 flex-shrink-0 ${meta.color}`} />
      <div className="flex-1 min-w-0">
        <div className={`text-xs font-semibold ${meta.color}`}>{meta.label}</div>
        <div className="flex items-center gap-2 mt-1">
          <div className="flex-1 h-1 bg-[#0F1419] rounded-full overflow-hidden">
            <div className={`h-full rounded-full transition-all ${meta.color.replace('text-','bg-')}`} style={{ width:`${pct}%` }} />
          </div>
          <span className="text-[10px] text-slate-500">{filled}/{fields?.length||0}</span>
        </div>
        {Object.keys(collectedData||{}).length > 0 && (
          <div className="mt-1 flex flex-wrap gap-1">
            {Object.entries(collectedData).map(([k,v]) => v != null && v !== '' && (
              <span key={k} className="text-[9px] px-1.5 py-0.5 bg-[#0F1419] border border-[#334155] rounded text-slate-400">
                {k}: <span className="text-white">{String(v)}</span>
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function GuidancePanel({ onSend }) {
  const [open, setOpen] = useState(null);
  return (
    <div className="space-y-2">
      <div className="flex items-center gap-2 mb-3 px-1">
        <HelpCircle className="w-4 h-4 text-orange-400" />
        <span className="text-xs font-semibold text-orange-400 uppercase tracking-wider">What I Can Do</span>
      </div>
      {GUIDANCE_SECTIONS.map((sec, si) => {
        const Icon = sec.icon;
        const isOpen = open === si;
        return (
          <div key={si} className={`rounded-lg border ${sec.bg} overflow-hidden`}>
            <button onClick={() => setOpen(isOpen ? null : si)}
              className="w-full flex items-center gap-2 px-3 py-2.5 text-left">
              <Icon className={`w-3.5 h-3.5 ${sec.color} flex-shrink-0`} />
              <span className={`text-xs font-semibold ${sec.color} flex-1`}>{sec.title}</span>
              <ChevronDown className={`w-3 h-3 text-slate-500 transition-transform ${isOpen?'rotate-180':''}`} />
            </button>
            {isOpen && (
              <div className="px-3 pb-3 space-y-1.5">
                {sec.items.map((item, ii) => {
                  const IIcon = item.icon;
                  const clickable = !item.example.startsWith('Click');
                  return (
                    <div key={ii}
                      onClick={() => clickable && onSend(item.example.replace(/"/g,''))}
                      className={`bg-[#0F1419] rounded-lg p-2.5 transition-colors ${clickable ? 'cursor-pointer hover:bg-[#1E293B]' : 'cursor-default'}`}>
                      <div className="flex items-center gap-1.5 mb-1">
                        <IIcon className={`w-3 h-3 ${item.color} flex-shrink-0`} />
                        <span className={`text-[10px] font-semibold ${item.color}`}>{item.label}</span>
                      </div>
                      <p className="text-[9px] text-slate-400 italic leading-relaxed">{item.example}</p>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        );
      })}

      {/* Tips */}
      <div className="mt-3 p-3 bg-orange-500/5 border border-orange-500/20 rounded-lg">
        <div className="text-[10px] font-semibold text-orange-400 mb-2">💡 Tips</div>
        {[
          '📎 Upload documents to teach AI about your machines',
          '🖼 Upload images for visual damage analysis',
          '💬 Ask follow-up questions — AI remembers context',
          '🔄 AI rejects non-maintenance questions',
        ].map((t,i) => <p key={i} className="text-[9px] text-slate-400 mb-1 leading-relaxed">{t}</p>)}
      </div>
    </div>
  );
}

export default function MaintenanceAssistant() {
  const [messages,      setMessages]      = useState([]);
  const [input,         setInput]         = useState('');
  const [loading,       setLoading]       = useState(false);
  const [liveCtx,       setLiveCtx]       = useState('');
  const [ctxLoading,    setCtxLoading]    = useState(true);
  const [convState,     setConvState]     = useState({});
  const [activeIntent,  setActiveIntent]  = useState(null);
  const [collectedData, setCollectedData] = useState({});
  const [uploading,     setUploading]     = useState(false);
  const [uploadMsg,     setUploadMsg]     = useState('');
  const [showGuidance,  setShowGuidance]  = useState(false);
  const [convId]                          = useState(() => 'ma-' + Date.now());
  const docInputRef   = useRef(null);
  const imageInputRef = useRef(null);
  const endRef        = useRef(null);

  useEffect(() => { endRef.current?.scrollIntoView({ behavior:'smooth' }); }, [messages]);

  const liveCtxRef    = useRef('');
  const prevAlertRef  = useRef('');   // tracks last known critical equipment to avoid duplicate alerts
  useEffect(() => { liveCtxRef.current = liveCtx; }, [liveCtx]);

  // ── Live context polling every 3 seconds ─────────────────
  useEffect(() => {
    let cancelled = false;

    const poll = async () => {
      try { await fetch(`${API}/api/sensor-data/simulate-all`, { method: 'POST' }); } catch(_) {}
      const ctx = await gatherContext();
      if (!cancelled) {
        setLiveCtx(ctx);
        setCtxLoading(false);
      }
    };

    poll();
    const id = setInterval(poll, 3000);
    return () => { cancelled = true; clearInterval(id); };
  }, []);

  // ── Proactive anomaly detection ──────────────────────────
  // When live context shows a CRITICAL sensor that wasn't there before,
  // automatically fire an agentic diagnosis without waiting for user input.
  useEffect(() => {
    if (!liveCtx || ctxLoading) return;

    // Extract critical equipment names from context
    const criticalLines = liveCtx
      .split('\n')
      .filter(l => l.includes('[CRITICAL]'))
      .map(l => l.match(/^[-\s!]*(.+?)[:]/)?.[1]?.trim())
      .filter(Boolean);

    if (criticalLines.length === 0) return;

    const alertKey = criticalLines.sort().join('|');
    if (alertKey === prevAlertRef.current) return; // already notified
    prevAlertRef.current = alertKey;

    // Don't auto-trigger if AI is already responding or user is mid-conversation
    if (loading) return;

    const eqName = criticalLines[0];
    const autoQuery = `CRITICAL ANOMALY DETECTED on ${eqName}. Analyze the current sensor readings, identify the root cause, assess failure risk, and provide immediate step-by-step resolution guidance for the maintenance team.`;

    // Small delay so context has settled
    const t = setTimeout(() => {
      send(autoQuery);
    }, 800);
    return () => clearTimeout(t);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [liveCtx]);

  const refreshContext = async () => {
    setCtxLoading(true);
    const ctx = await gatherContext();
    setLiveCtx(ctx);
    setCtxLoading(false);
  };

  async function performSave(endpoint, payload) {
    try {
      const fd = new FormData();
      Object.entries(payload).forEach(([k,v]) => { if (v != null && v !== '') fd.append(k, String(v)); });
      const resp = await fetch(`${API}${endpoint}`, { method:'POST', body:fd });
      const data = await resp.json();
      if (!resp.ok) throw new Error(data.detail || 'Save failed');
      gatherContext().then(ctx => setLiveCtx(ctx));
      return { success:true, message:data.message };
    } catch(e) { return { success:false, message:e.message }; }
  }

  const sendFallback = async (question, ctx) => {
    const fd = new FormData();
    fd.append('question', `${question}\n\nLive plant context:\n${ctx || liveCtx}`);
    fd.append('conversation_id', convId);
    const r = await fetch(`${DAPI}/chat`, { method:'POST', body:fd });
    const d = await r.json();
    return { intent:'QUERY', message:d.answer||'No answer returned.', collecting:false, collected_data:{}, next_field:null, ready_to_save:false, save_endpoint:null, save_payload:null };
  };

  const send = useCallback(async (q) => {
    const question = (q || input).trim();
    if (!question || loading) return;
    setInput(''); setLoading(true);
    setMessages(m => [...m, { role:'user', text:question, time:new Date() }]);

    // Always use the freshest context snapshot
    const currentCtx = liveCtxRef.current || liveCtx;

    try {
      let data = null;

      // Try the multi-agent orchestrator first
      try {
        const fd = new FormData();
        fd.append('message', question);
        fd.append('session_id', convId);
        fd.append('live_context', currentCtx);
        if (convState.equipment_name) fd.append('equipment_name', convState.equipment_name);
        const resp = await fetch(`${API}/api/agent/chat`, { method:'POST', body:fd });
        const raw = await resp.json();
        if (resp.ok && raw.answer) {
          // Orchestrator response — show agent summary badges
          setMessages(m => [...m, {
            role:'assistant',
            text: cleanText(raw.answer),
            intent: 'QUERY',
            agents: raw.agents_invoked || [],
            summary: raw.summary || {},
            time: new Date(),
          }]);
          setLoading(false);
          return;
        }
      } catch(_) {}

      // Fallback to ai-actions for data entry intents
      try {
        const fd = new FormData();
        fd.append('message', question);
        fd.append('conversation_state', JSON.stringify(convState));
        fd.append('live_context', currentCtx);
        const resp = await fetch(`${API}/api/ai-actions/chat`, { method:'POST', body:fd });
        const raw = await resp.json();
        if (resp.ok && raw.message) data = raw;
      } catch(_) {}

      // Last resort fallback
      if (!data) data = await sendFallback(question, currentCtx);

      if (data.intent && data.intent !== 'QUERY') {
        setActiveIntent(data.intent);
        if (data.collected_data) setCollectedData(data.collected_data);
        setConvState({ intent:data.intent, collecting:data.collecting, collected_data:data.collected_data||{}, next_field:data.next_field });
      }
      let saveResult = null;
      if (data.ready_to_save && data.save_endpoint && data.save_payload) {
        saveResult = await performSave(data.save_endpoint, data.save_payload);
        setConvState({}); setActiveIntent(null); setCollectedData({});
      }
      if (data.intent === 'QUERY' || (!data.collecting && !data.next_field && !data.ready_to_save)) {
        setConvState({}); setActiveIntent(null); setCollectedData({});
      }
      setMessages(m => [...m, { role:'assistant', text:cleanText(data.message)||'No response.', intent:data.intent, saveResult, time:new Date() }]);
    } catch(e) {
      try {
        const fb = await sendFallback(question, currentCtx);
        setMessages(m => [...m, { role:'assistant', text:cleanText(fb.message), time:new Date() }]);
      } catch(e2) {
        setMessages(m => [...m, { role:'assistant', text:`Connection error: ${e2.message}`, time:new Date() }]);
      }
    } finally { setLoading(false); }
  }, [input, loading, liveCtx, convState]);

  const handleDocUpload = async (file) => {
    if (!file) return;
    setUploading(true); setUploadMsg('Uploading document...');
    try {
      const fd1 = new FormData(); fd1.append('file', file);
      const r1 = await fetch(`${DAPI}/upload`, { method:'POST', body:fd1 });
      const d1 = await r1.json();
      if (!r1.ok) throw new Error(d1.detail || 'Upload failed');
      setUploadMsg('AI analyzing document...');
      const r2 = await fetch(`${DAPI}/process/${d1.doc_id}`, { method:'POST' });
      const d2 = await r2.json();
      if (d2.status === 'completed' || d2.status === 'already_processed') {
        setUploadMsg('');
        setMessages(m => [...m, {
          role:'assistant', intent:'UPLOAD_MANUAL',
          text:`✅ Document uploaded & indexed!\n\n📄 File: ${file.name}\n🔧 Equipment: ${d2.equipment_name||'Auto-detected'}\n📝 Type: ${d2.document_type||'Document'}\n📦 Chunks indexed: ${d2.chunk_count||0}\n\nKnowledge is now available. Ask me anything about this equipment.`,
          time:new Date()
        }]);
      } else throw new Error(d2.message || 'Processing failed');
    } catch(e) { setUploadMsg('Error: '+e.message); }
    finally { setUploading(false); }
  };

  const handleImageUpload = async (file) => {
    if (!file) return;
    setUploading(true); setUploadMsg('Analyzing image...');
    const objectUrl = URL.createObjectURL(file);
    setMessages(m => [...m, { role:'user', text:`[Uploaded image: ${file.name}]`, imageUrl:objectUrl, time:new Date() }]);
    try {
      const fd = new FormData();
      fd.append('question',
        `An image has been uploaded from a steel manufacturing plant. Filename: "${file.name}".

You are a Senior Industrial Maintenance Engineer for a steel plant. The user is a plant technician or engineer who works with industrial equipment daily. ASSUME this image is related to plant equipment unless it is completely obvious it is not (like a selfie, food photo, etc.).

Provide a DETAILED maintenance engineering analysis as follows:

COMPONENT IDENTIFICATION:
- Based on the filename and steel plant context, identify what this equipment/component likely is
- State the equipment type, typical use in steel plant, manufacturer type if recognizable

TECHNICAL SPECIFICATIONS (typical for this equipment):
- Normal operating parameters (temperature, vibration, speed, pressure)
- Critical thresholds and alarm limits

VISUAL CONDITION ASSESSMENT:
- Describe what would be visible in such an image
- Common wear patterns, damage signs, or failure modes for this component
- What to look for: surface condition, color changes, deformation, corrosion, leaks, cracks, misalignment

MAINTENANCE ANALYSIS:
- Condition rating: Good / Fair / Poor / Critical (based on what is typical for this equipment)
- Probable issues based on equipment type and typical failure modes
- Immediate actions required
- Scheduled maintenance recommendations

FAILURE MODES & ROOT CAUSES:
- List the 3 most common failure modes for this equipment
- Signs of each failure mode
- Prevention measures

SPARE PARTS TYPICALLY REQUIRED:
- List key spare parts with part numbers if known
- Recommended stock levels

SAFETY WARNINGS:
- Critical safety precautions for working on this equipment

Note: Since direct image vision is not available, this analysis is based on the equipment type identified from the filename and steel plant industrial maintenance knowledge. For precise visual inspection results, describe what you observe in the image and I will provide specific diagnosis.

Live plant context:
${liveCtx}`
      );
      fd.append('conversation_id', convId);
      const r = await fetch(`${DAPI}/chat`, { method:'POST', body:fd });
      const d = await r.json();
      setMessages(m => [...m, {
        role:'assistant', intent:'QUERY',
        text:cleanText(`🖼 Image Analysis — ${file.name}\n\n${d.answer || 'Unable to analyze. Please describe what the image shows and I will help diagnose.'}\n\n💬 Tip: Tell me what you observe (rust, cracks, color changes, leaks, noise, vibration) for a more specific diagnosis.`),
        time:new Date()
      }]);
      setUploadMsg('');
    } catch(e) { setUploadMsg('Error: '+e.message); }
    finally { setUploading(false); }
  };

  const clearChat = () => { setMessages([]); setConvState({}); setActiveIntent(null); setCollectedData({}); };

  // Calculate left offset — sidebar is w-64 = 256px
  return (
    <div className="flex flex-col overflow-hidden fixed top-0 right-0 bottom-0" style={{ left: '256px' }}>

      {/* TOP BAR */}
      <div className="flex items-center justify-between px-4 py-2.5 bg-[#0F1419] border-b border-[#334155] flex-shrink-0">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-orange-500 to-orange-700 flex items-center justify-center flex-shrink-0">
            <Brain className="w-4 h-4 text-white" />
          </div>
          <div>
            <h1 className="text-sm font-heading font-bold text-white leading-tight">AI Maintenance Assistant</h1>
            <div className="flex items-center gap-1.5 text-[10px] text-slate-400">
              <div className={`w-1.5 h-1.5 rounded-full ${ctxLoading?'bg-yellow-500 animate-pulse':'bg-green-500 animate-pulse'}`} />
              {ctxLoading ? 'Refreshing live data...' : 'Live · Updates every 3s · LLaMA 70B'}
            </div>
          </div>
        </div>

        <div className="flex items-center gap-1.5">
          <div className="hidden lg:flex items-center gap-1 mr-1">
            {QUICK_ACTIONS.slice(0,5).map(({ icon:Icon, label, prompt, color }) => (
              <button key={label} onClick={() => send(prompt)}
                className="flex items-center gap-1 px-2 py-1 bg-[#1E293B] border border-[#334155] hover:border-orange-500/40 text-slate-300 hover:text-white text-[10px] rounded-lg transition-all">
                <Icon className={`w-3 h-3 ${color}`} /> {label}
              </button>
            ))}
          </div>
          <button onClick={() => setShowGuidance(g => !g)}
            className={`flex items-center gap-1.5 px-3 py-1.5 text-xs rounded-lg border transition-all ${showGuidance?'bg-orange-500/10 border-orange-500/30 text-orange-400':'bg-[#1E293B] border-[#334155] text-slate-400 hover:text-white'}`}>
            <HelpCircle className="w-3.5 h-3.5" /> Guide
          </button>
          <button onClick={refreshContext} className="p-1.5 text-slate-400 hover:text-white hover:bg-[#1E293B] rounded-lg transition-colors">
            <RefreshCw className={`w-4 h-4 ${ctxLoading?'animate-spin':''}`} />
          </button>
          <button onClick={clearChat} className="p-1.5 text-slate-400 hover:text-red-400 hover:bg-red-500/10 rounded-lg transition-colors">
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* BODY */}
      <div className="flex flex-1 min-h-0 overflow-hidden">

        {/* Guidance panel (slide in) */}
        {showGuidance && (
          <div className="w-72 flex-shrink-0 bg-[#0F1419] border-r border-[#334155] overflow-y-auto p-3">
            <GuidancePanel onSend={(p) => { send(p); setShowGuidance(false); }} />
          </div>
        )}

        {/* Chat area */}
        <div className="flex-1 flex flex-col min-w-0 min-h-0 overflow-hidden">

          {/* Collection progress */}
          {activeIntent && activeIntent !== 'QUERY' && (
            <div className="px-4 pt-2 flex-shrink-0">
              <CollectionProgress intent={activeIntent} collectedData={collectedData} fields={INTENT_FIELDS[activeIntent]||[]} />
            </div>
          )}

          {/* Messages */}
          <div className="flex-1 overflow-y-auto min-h-0 px-4 py-3 space-y-3">
            {messages.length === 0 && (
              <div className="flex flex-col items-center justify-start pt-2 text-center space-y-3">
                <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-orange-500/20 to-orange-700/20 border border-orange-500/20 flex items-center justify-center">
                  <Brain className="w-6 h-6 text-orange-400" />
                </div>
                <div>
                  <h2 className="text-base font-heading font-bold text-white">AI Maintenance Control Center</h2>
                  <p className="text-slate-400 text-xs mt-0.5">
                    Diagnose failures · Predict breakdowns · Log maintenance · Upload manuals · Analyze images
                  </p>
                </div>
                <div className="grid grid-cols-3 gap-2 w-full max-w-2xl">
                  {[
                    { icon:Cpu,           color:'text-blue-400',   bg:'bg-blue-500/10 border-blue-500/20',    q:'Add a new equipment to the system',            label:'Register Equipment' },
                    { icon:Activity,      color:'text-green-400',  bg:'bg-green-500/10 border-green-500/20',  q:'Enter sensor readings for a machine',           label:'Enter Sensor Data'  },
                    { icon:ClipboardList, color:'text-yellow-400', bg:'bg-yellow-500/10 border-yellow-500/20',q:'Log a maintenance activity for equipment',      label:'Log Maintenance'    },
                    { icon:Search,        color:'text-cyan-400',   bg:'bg-cyan-500/10 border-cyan-500/20',    q:'Why is Rolling Mill Motor overheating?',        label:'Diagnose Issue'     },
                    { icon:Zap,           color:'text-orange-400', bg:'bg-orange-500/10 border-orange-500/20',q:'Which equipment will fail in the next 7 days?', label:'Predict Failures'   },
                    { icon:Camera,        color:'text-indigo-400', bg:'bg-indigo-500/10 border-indigo-500/20',q:'upload image',                                  label:'Analyze Image'      },
                  ].map(({ icon:Icon, color, bg, q, label }) => (
                    <button key={label}
                      onClick={() => q === 'upload image' ? imageInputRef.current?.click() : send(q)}
                      className={`flex flex-col items-center gap-1.5 p-3 rounded-xl border ${bg} hover:scale-[1.02] transition-all`}>
                      <Icon className={`w-5 h-5 ${color}`} />
                      <span className={`text-xs font-semibold ${color}`}>{label}</span>
                    </button>
                  ))}
                </div>
                <p className="text-[10px] text-slate-600">
                  Click <strong className="text-orange-400">Guide</strong> in the top bar to see all capabilities
                </p>
              </div>
            )}

            {messages.map((msg, i) => {
              const meta = msg.intent ? INTENT_META[msg.intent] : null;
              const Icon = meta ? meta.icon : Brain;
              return (
                <div key={i} className={`flex ${msg.role==='user'?'justify-end':'justify-start'}`}>
                  {msg.role === 'assistant' && (
                    <div className={`w-7 h-7 rounded-lg flex items-center justify-center flex-shrink-0 mt-1 mr-2 border ${meta?meta.bg:'bg-orange-500/10 border-orange-500/20'}`}>
                      <Icon className={`w-3.5 h-3.5 ${meta?meta.color:'text-orange-400'}`} />
                    </div>
                  )}
                  <div className={`max-w-[82%] flex flex-col gap-1.5 ${msg.role==='user'?'items-end':'items-start'}`}>
                    {msg.imageUrl && (
                      <img src={msg.imageUrl} alt="uploaded"
                        className="max-w-[220px] max-h-[160px] rounded-xl border border-indigo-500/30 object-cover" />
                    )}
                    <div className={`px-4 py-3 rounded-2xl text-sm leading-relaxed ${
                      msg.role==='user'
                        ? 'bg-orange-500 text-white rounded-br-sm'
                        : 'bg-[#1E293B] border border-[#334155] text-slate-200 rounded-bl-sm'
                    }`}>
                      <pre className="whitespace-pre-wrap font-sans">{msg.text}</pre>
                    </div>
                    {msg.saveResult && (
                      <div className={`flex items-center gap-1.5 text-xs px-3 py-1 rounded-full border ${msg.saveResult.success?'text-green-400 bg-green-500/10 border-green-500/20':'text-red-400 bg-red-500/10 border-red-500/20'}`}>
                        {msg.saveResult.success ? <CheckCircle className="w-3 h-3" /> : <X className="w-3 h-3" />}
                        {msg.saveResult.message}
                      </div>
                    )}
                    {msg.role === 'assistant' && (
                      <div className="flex items-center gap-2 px-1 flex-wrap">
                        {meta && msg.intent !== 'QUERY' && (
                          <span className={`text-[10px] px-2 py-0.5 rounded border ${meta.bg} ${meta.color}`}>{meta.label}</span>
                        )}
                        {/* Agent badges for multi-agent responses */}
                        {msg.agents && msg.agents.length > 0 && (
                          <div className="flex items-center gap-1 flex-wrap">
                            {msg.agents.map(a => (
                              <span key={a} className="text-[9px] px-1.5 py-0.5 bg-[#0F1419] border border-[#334155] rounded text-slate-500 capitalize">
                                {a.replace('_',' ')}
                              </span>
                            ))}
                          </div>
                        )}
                        {/* Summary pills */}
                        {msg.summary && msg.summary.health_score != null && (
                          <span className="text-[9px] px-1.5 py-0.5 bg-green-500/10 border border-green-500/20 rounded text-green-400">
                            Health: {msg.summary.health_score}%
                          </span>
                        )}
                        {msg.summary && msg.summary.failure_probability != null && (
                          <span className="text-[9px] px-1.5 py-0.5 bg-red-500/10 border border-red-500/20 rounded text-red-400">
                            Failure: {msg.summary.failure_probability}%
                          </span>
                        )}
                        {msg.summary && msg.summary.rul_days != null && (
                          <span className="text-[9px] px-1.5 py-0.5 bg-yellow-500/10 border border-yellow-500/20 rounded text-yellow-400">
                            RUL: {msg.summary.rul_days}d
                          </span>
                        )}
                        <span className="text-[10px] text-slate-600">{msg.time?.toLocaleTimeString()}</span>
                      </div>
                    )}
                  </div>
                </div>
              );
            })}

            {loading && (
              <div className="flex justify-start">
                <div className="w-7 h-7 rounded-lg bg-orange-500/10 border border-orange-500/20 flex items-center justify-center mr-2 mt-1 flex-shrink-0">
                  <Brain className="w-3.5 h-3.5 text-orange-400" />
                </div>
                <div className="bg-[#1E293B] border border-[#334155] rounded-2xl rounded-bl-sm px-4 py-3 flex items-center gap-2">
                  {[0,1,2].map(i => (
                    <div key={i} className="w-1.5 h-1.5 bg-orange-400 rounded-full animate-bounce" style={{ animationDelay:`${i*150}ms` }} />
                  ))}
                  <span className="text-xs text-slate-400 ml-1">
                    {uploading ? uploadMsg : activeIntent && activeIntent !== 'QUERY' ? 'Collecting data...' : 'Analyzing...'}
                  </span>
                </div>
              </div>
            )}
            <div ref={endRef} />
          </div>

          {/* INPUT BAR */}
          <div className="flex-shrink-0 px-4 pb-2 pt-2 border-t border-[#334155] bg-[#0F1419]">
            {uploadMsg && !loading && (
              <div className="text-[10px] text-yellow-400 mb-1.5 px-1">{uploadMsg}</div>
            )}

            {/* Mobile quick actions */}
            <div className="flex lg:hidden gap-1 mb-2 flex-wrap">
              {QUICK_ACTIONS.map(({ icon:Icon, label, prompt, color }) => (
                <button key={label} onClick={() => send(prompt)}
                  className="flex items-center gap-1 px-2 py-1 bg-[#1E293B] border border-[#334155] text-slate-400 text-[10px] rounded-lg">
                  <Icon className={`w-3 h-3 ${color}`} /> {label}
                </button>
              ))}
            </div>

            <div className="flex gap-2 items-end">
              {/* Hidden inputs */}
              <input type="file" accept=".pdf,.txt,.docx,.csv" className="hidden" ref={docInputRef}
                onChange={e => { const f=e.target.files[0]; if(f) handleDocUpload(f); e.target.value=''; }} />
              <input type="file" accept="image/*" className="hidden" ref={imageInputRef}
                onChange={e => { const f=e.target.files[0]; if(f) handleImageUpload(f); e.target.value=''; }} />

              {/* Upload document */}
              <button onClick={() => docInputRef.current?.click()} disabled={uploading}
                title="Upload document (PDF/DOCX/TXT)"
                className="p-2.5 bg-[#1E293B] border border-[#334155] hover:border-purple-500/50 text-purple-400 rounded-xl transition-colors disabled:opacity-40 flex-shrink-0">
                <Upload className="w-5 h-5" />
              </button>

              {/* Upload image */}
              <button onClick={() => imageInputRef.current?.click()} disabled={uploading}
                title="Upload image for AI analysis"
                className="p-2.5 bg-[#1E293B] border border-[#334155] hover:border-indigo-500/50 text-indigo-400 rounded-xl transition-colors disabled:opacity-40 flex-shrink-0">
                <Image className="w-5 h-5" />
              </button>

              <textarea
                value={input}
                onChange={e => setInput(e.target.value)}
                onKeyDown={e => { if(e.key==='Enter' && !e.shiftKey) { e.preventDefault(); send(); } }}
                placeholder={
                  activeIntent && activeIntent !== 'QUERY'
                    ? `Collecting ${INTENT_META[activeIntent]?.label||'data'}... type your answer`
                    : 'Ask anything, say "add equipment", "log maintenance", or upload an image/document...'
                }
                rows={2}
                className="flex-1 bg-[#1E293B] border border-[#334155] text-white text-sm px-4 py-2.5 rounded-xl resize-none focus:outline-none focus:border-orange-500 transition-colors placeholder:text-slate-600"
              />

              <button onClick={() => send()} disabled={loading || !input.trim()}
                className="p-2.5 bg-orange-500 hover:bg-orange-600 text-white rounded-xl disabled:opacity-40 transition-colors flex-shrink-0">
                <Send className="w-5 h-5" />
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
