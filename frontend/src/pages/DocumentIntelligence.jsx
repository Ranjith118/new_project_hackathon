import { useState, useEffect, useRef } from 'react';
import {
  Upload, FileText, Brain, Search, Trash2,
  CheckCircle, Clock, AlertCircle, ChevronLeft,
  Shield, Wrench, Package, Activity, Send,
  AlertTriangle, Settings, Eye, FileSearch
} from 'lucide-react';
import {
  AreaChart, Area, Tooltip, ResponsiveContainer
} from 'recharts';

const API = 'http://localhost:8000/api/doc-intelligence';

const SC = {
  completed:  'text-green-400 bg-green-400/10 border-green-400/30',
  processing: 'text-yellow-400 bg-yellow-400/10 border-yellow-400/30',
  uploaded:   'text-blue-400 bg-blue-400/10 border-blue-400/30',
  failed:     'text-red-400 bg-red-400/10 border-red-400/30',
};

const Card = ({ children, className = '' }) => (
  <div className={`bg-[#1E293B] border border-[#334155] rounded-xl ${className}`}>{children}</div>
);

const Sec = ({ icon: I, label, color = 'text-orange-400', children }) => (
  <div className="mb-4">
    <h4 className={`flex items-center gap-2 text-xs font-semibold uppercase tracking-wider ${color} mb-3`}>
      <I className="w-3.5 h-3.5" />{label}
    </h4>
    {children}
  </div>
);

const Empty = ({ msg }) => (
  <p className="text-slate-500 text-xs italic">{msg || 'No data extracted'}</p>
);

const Tab = ({ label, active, count, onClick }) => (
  <button onClick={onClick}
    className={`flex items-center gap-1.5 px-4 py-2 text-sm font-medium rounded-lg transition-all ${
      active ? 'bg-orange-500 text-white' : 'text-slate-400 hover:text-white hover:bg-[#334155]'
    }`}>
    {label}
    {count !== undefined && (
      <span className={`text-[10px] px-1.5 py-0.5 rounded-full ${active ? 'bg-white/20' : 'bg-[#334155] text-slate-400'}`}>
        {count}
      </span>
    )}
  </button>
);

function AIChat() {
  const [msgs, setMsgs] = useState([
    { role: 'assistant', text: 'Document Intelligence AI ready. Ask me anything about your uploaded documents.' }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [convId] = useState(() => 'dic-' + Date.now());
  const endRef = useRef(null);
  useEffect(() => { endRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [msgs]);

  const send = async () => {
    if (!input.trim() || loading) return;
    const q = input; setInput('');
    setMsgs(m => [...m, { role: 'user', text: q }]);
    setLoading(true);
    try {
      const fd = new FormData();
      fd.append('question', q);
      fd.append('conversation_id', convId);
      const r = await fetch(`${API}/chat`, { method: 'POST', body: fd });
      const d = await r.json();
      setMsgs(m => [...m, {
        role: 'assistant',
        text: d.answer || 'No response',
        sources: d.sources,
        conf: d.confidence_score,
        evidence: d.evidence
      }]);
    } catch {
      setMsgs(m => [...m, { role: 'assistant', text: 'Connection error.' }]);
    } finally { setLoading(false); }
  };

  const suggestions = [
    'What are the maintenance procedures?',
    'List spare parts with part numbers',
    'What causes bearing failure?',
    'What are the safety requirements?',
    'Show vibration alarm levels',
    'What is the lubrication interval?',
  ];

  return (
    <Card className="flex flex-col h-[500px]">
      <div className="p-4 border-b border-[#334155] flex items-center gap-2">
        <Brain className="w-4 h-4 text-orange-400" />
        <span className="font-semibold text-white text-sm">AI Document Assistant</span>
        <span className="text-[10px] text-slate-500 ml-auto">Groq LLaMA</span>
      </div>
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {msgs.map((m, i) => (
          <div key={i} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-[85%] px-3 py-2 rounded-xl text-xs leading-relaxed ${
              m.role === 'user'
                ? 'bg-orange-500/20 text-white border border-orange-500/20 rounded-br-sm'
                : 'bg-[#0F1419] text-slate-300 border border-[#334155] rounded-bl-sm'
            }`}>
              <p className="whitespace-pre-wrap">{m.text}</p>
              {m.sources && m.sources.length > 0 && (
                <div className="mt-2 pt-1.5 border-t border-[#334155] space-y-0.5">
                  <p className="text-[10px] text-orange-400">
                    Sources: {m.sources.slice(0, 3).join(' · ')}
                  </p>
                  {m.conf !== undefined && (
                    <p className="text-[10px] text-slate-500">
                      Confidence: {(m.conf * 100).toFixed(0)}%
                    </p>
                  )}
                </div>
              )}
              {m.evidence && m.evidence.length > 0 && (
                <details className="mt-1">
                  <summary className="text-[10px] text-slate-500 cursor-pointer">
                    View evidence ({m.evidence.length})
                  </summary>
                  <div className="mt-1 space-y-1">
                    {m.evidence.map((ev, j) => (
                      <div key={j} className="text-[10px] bg-[#1E293B] rounded p-1.5 border border-[#334155]">
                        <span className="text-orange-400">{ev.source_document}: </span>
                        <span className="text-slate-400">{ev.excerpt ? ev.excerpt.slice(0, 100) : ''}...</span>
                      </div>
                    ))}
                  </div>
                </details>
              )}
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex justify-start">
            <div className="bg-[#0F1419] border border-[#334155] px-3 py-2 rounded-xl flex gap-1">
              {[0, 1, 2].map(i => (
                <div key={i} className="w-1.5 h-1.5 bg-orange-400 rounded-full animate-bounce"
                  style={{ animationDelay: `${i * 0.15}s` }} />
              ))}
            </div>
          </div>
        )}
        <div ref={endRef} />
      </div>
      <div className="p-3 border-t border-[#334155] space-y-2">
        <div className="flex flex-wrap gap-1">
          {suggestions.map(s => (
            <button key={s} onClick={() => setInput(s)}
              className="text-[10px] px-2 py-1 rounded border border-[#334155] text-slate-400 hover:text-white hover:border-orange-500/40 transition-colors">
              {s}
            </button>
          ))}
        </div>
        <div className="flex gap-2">
          <input value={input} onChange={e => setInput(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && send()}
            placeholder="Ask about any uploaded document..."
            className="flex-1 bg-[#0F1419] border border-[#334155] text-white text-xs px-3 py-2 rounded-lg focus:outline-none focus:border-orange-500" />
          <button onClick={send} disabled={loading || !input.trim()}
            className="px-3 py-2 bg-orange-500 hover:bg-orange-600 text-white rounded-lg disabled:opacity-40 transition-colors">
            <Send className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>
    </Card>
  );
}

function DocDetail({ doc, onBack }) {
  const [full, setFull] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState(0);

  useEffect(() => {
    fetch(`${API}/documents/${doc.doc_id}`)
      .then(r => r.json())
      .then(d => { setFull(d); setLoading(false); })
      .catch(() => setLoading(false));
  }, [doc.doc_id]);

  const k = full ? full.knowledge || {} : {};
  const s = full ? full.summaries  || {} : {};

  const TABS = [
    { label: 'Summary' },
    { label: 'Fault Modes',  count: k.fault_modes ? k.fault_modes.length : 0 },
    { label: 'Maintenance',  count: k.maintenance_tasks ? k.maintenance_tasks.length : 0 },
    { label: 'Spare Parts',  count: k.spare_parts ? k.spare_parts.length : 0 },
    { label: 'Safety' },
    { label: 'Thresholds' },
  ];

  return (
    <div className="space-y-5">
      <button onClick={onBack}
        className="flex items-center gap-1 text-slate-400 hover:text-white text-sm transition-colors">
        <ChevronLeft className="w-4 h-4" /> Back to Documents
      </button>

      <Card className="p-5">
        <div className="flex items-start justify-between flex-wrap gap-4">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-xl bg-orange-500/10 border border-orange-500/20 flex items-center justify-center">
              <FileText className="w-6 h-6 text-orange-400" />
            </div>
            <div>
              <h2 className="text-xl font-heading font-bold text-white">{doc.file_name}</h2>
              <div className="flex flex-wrap gap-3 mt-1 text-xs text-slate-400">
                {doc.document_type && (
                  <span className="px-2 py-0.5 bg-orange-500/10 border border-orange-500/20 text-orange-400 rounded">
                    {doc.document_type}
                  </span>
                )}
                <span>{doc.type_confidence} confidence</span>
                {doc.chunk_count > 0 && <span>{doc.chunk_count} chunks indexed</span>}
                <span>{new Date(doc.upload_date).toLocaleDateString()}</span>
              </div>
            </div>
          </div>
          <span className={`flex items-center gap-1.5 px-2 py-1 rounded border text-xs ${SC[doc.processing_status] || SC.uploaded}`}>
            {doc.processing_status === 'completed' && <CheckCircle className="w-3 h-3" />}
            {doc.processing_status === 'processing' && <Clock className="w-3 h-3 animate-spin" />}
            {doc.processing_status === 'failed' && <AlertCircle className="w-3 h-3" />}
            {doc.processing_status}
          </span>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mt-5 pt-5 border-t border-[#334155]">
          {[
            { label: 'Equipment',    val: doc.equipment_name },
            { label: 'Manufacturer', val: doc.manufacturer },
            { label: 'Model',        val: doc.model_number },
            { label: 'File Type',    val: doc.file_type },
          ].map(({ label, val }) => (
            <div key={label}>
              <div className="text-[10px] text-slate-500 mb-1">{label}</div>
              <div className="text-xs text-white font-medium">{val || '—'}</div>
            </div>
          ))}
        </div>

        {full && full.keywords && full.keywords.length > 0 && (
          <div className="flex flex-wrap gap-1.5 mt-4 pt-4 border-t border-[#334155]">
            {full.keywords.map(kw => (
              <span key={kw} className="px-2 py-0.5 bg-purple-500/10 border border-purple-500/20 text-purple-400 rounded-full text-[10px]">
                {kw}
              </span>
            ))}
          </div>
        )}
      </Card>

      {loading ? (
        <div className="flex items-center justify-center py-20">
          <div className="w-8 h-8 border-2 border-orange-500 border-t-transparent rounded-full animate-spin" />
        </div>
      ) : (
        <>
          <div className="flex gap-1 flex-wrap bg-[#1E293B] p-1 rounded-xl border border-[#334155] w-fit">
            {TABS.map((t, i) => (
              <Tab key={t.label} label={t.label} count={t.count} active={activeTab === i} onClick={() => setActiveTab(i)} />
            ))}
          </div>

          {activeTab === 0 && (
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
              <div className="lg:col-span-2 space-y-4">
                {[
                  { label: 'Executive Summary',   text: s.executive },
                  { label: 'Technical Summary',   text: s.technical },
                  { label: 'Maintenance Summary', text: s.maintenance },
                ].map(({ label, text }) => text ? (
                  <Card key={label} className="p-4">
                    <div className="text-xs text-orange-400 font-semibold mb-2">{label}</div>
                    <p className="text-sm text-slate-300 leading-relaxed">{text}</p>
                  </Card>
                ) : null)}
              </div>
              <div className="space-y-4">
                {k.operating_conditions && Object.values(k.operating_conditions).some(Boolean) && (
                  <Card className="p-4">
                    <Sec icon={Activity} label="Operating Conditions">
                      {Object.entries(k.operating_conditions).map(([key, val]) =>
                        val ? (
                          <div key={key} className="flex justify-between text-xs py-1.5 border-b border-[#334155] last:border-0">
                            <span className="text-slate-400 capitalize">{key.replace(/_/g, ' ')}</span>
                            <span className="text-white text-right max-w-[55%]">{String(val)}</span>
                          </div>
                        ) : null
                      )}
                    </Sec>
                  </Card>
                )}
                {k.critical_components && k.critical_components.length > 0 && (
                  <Card className="p-4">
                    <Sec icon={Settings} label="Critical Components" color="text-red-400">
                      <div className="flex flex-wrap gap-1.5">
                        {k.critical_components.map((c, i) => (
                          <span key={i} className="text-[10px] px-2 py-0.5 bg-red-500/10 border border-red-500/20 text-red-400 rounded">
                            {c}
                          </span>
                        ))}
                      </div>
                    </Sec>
                  </Card>
                )}
              </div>
            </div>
          )}

          {activeTab === 1 && (
            <div className="space-y-3">
              {k.fault_modes && k.fault_modes.length > 0 ? k.fault_modes.map((f, i) => (
                <Card key={i} className="p-4 border-l-4 border-l-red-500">
                  <div className="flex items-start justify-between flex-wrap gap-2">
                    <div>
                      <div className="text-white text-sm font-semibold">{f.fault}</div>
                      {f.symptom && <p className="text-xs text-yellow-400 mt-1">Symptom: {f.symptom}</p>}
                      {f.cause && <p className="text-xs text-slate-400 mt-0.5">Cause: {f.cause}</p>}
                    </div>
                    {f.action && (
                      <span className="text-[10px] px-2 py-1 bg-green-500/10 border border-green-500/20 text-green-400 rounded">
                        Action: {f.action}
                      </span>
                    )}
                  </div>
                </Card>
              )) : (
                <Card className="p-8 text-center"><Empty msg="No fault modes extracted" /></Card>
              )}
            </div>
          )}

          {activeTab === 2 && (
            <div className="space-y-4">
              {k.maintenance_tasks && k.maintenance_tasks.length > 0 && (
                <div className="space-y-3">
                  {k.maintenance_tasks.map((t, i) => (
                    <Card key={i} className="p-4 border-l-4 border-l-orange-500">
                      <div className="flex items-start justify-between flex-wrap gap-2">
                        <div>
                          <div className="text-white text-sm font-semibold">{t.task}</div>
                          {t.procedure && <p className="text-xs text-slate-400 mt-1">{t.procedure}</p>}
                        </div>
                        {t.interval && (
                          <span className="text-[10px] px-2 py-1 bg-orange-500/10 border border-orange-500/20 text-orange-400 rounded">
                            {t.interval}
                          </span>
                        )}
                      </div>
                    </Card>
                  ))}
                </div>
              )}
              {k.maintenance_intervals && Object.values(k.maintenance_intervals).some(v => v && v.length > 0) && (
                <Card className="p-4">
                  <div className="text-xs font-semibold text-orange-400 mb-3 uppercase tracking-wider">Maintenance Schedule</div>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    {Object.entries(k.maintenance_intervals).map(([period, tasks]) =>
                      tasks && tasks.length > 0 ? (
                        <div key={period}>
                          <div className="text-[10px] text-slate-500 uppercase font-semibold mb-2">{period}</div>
                          {tasks.filter(Boolean).map((t, i) => (
                            <div key={i} className="text-xs text-slate-300 flex gap-1.5 items-start mb-1">
                              <span className="text-orange-400 mt-0.5">·</span> {t}
                            </div>
                          ))}
                        </div>
                      ) : null
                    )}
                  </div>
                </Card>
              )}
              {k.inspection_checklist && k.inspection_checklist.length > 0 && (
                <Card className="p-4">
                  <div className="text-xs font-semibold text-blue-400 mb-3 uppercase tracking-wider">Inspection Checklist</div>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                    {k.inspection_checklist.filter(Boolean).map((item, i) => (
                      <div key={i} className="flex items-center gap-2 text-xs text-slate-300">
                        <CheckCircle className="w-3 h-3 text-blue-400 flex-shrink-0" />{item}
                      </div>
                    ))}
                  </div>
                </Card>
              )}
            </div>
          )}

          {activeTab === 3 && (
            <div>
              {k.spare_parts && k.spare_parts.length > 0 ? (
                <Card className="overflow-hidden">
                  <table className="industrial-table">
                    <thead>
                      <tr>
                        <th>Part Name</th>
                        <th>Part Number</th>
                        <th>Quantity</th>
                        <th>Notes</th>
                      </tr>
                    </thead>
                    <tbody>
                      {k.spare_parts.map((p, i) => (
                        <tr key={i}>
                          <td className="font-medium">{p.part_name}</td>
                          <td className="font-mono text-sm text-orange-400">{p.part_number || '—'}</td>
                          <td className="font-mono">{p.quantity || '—'}</td>
                          <td className="text-slate-400 text-xs">{p.notes || '—'}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </Card>
              ) : (
                <Card className="p-8 text-center"><Empty msg="No spare parts extracted" /></Card>
              )}
            </div>
          )}

          {activeTab === 4 && (
            <div className="space-y-3">
              {k.safety_instructions && k.safety_instructions.length > 0 ? (
                <Card className="p-5">
                  <Sec icon={Shield} label="Safety Instructions" color="text-yellow-400">
                    <div className="space-y-2">
                      {k.safety_instructions.filter(Boolean).map((si, i) => (
                        <div key={i} className="flex items-start gap-2 p-2.5 bg-yellow-500/5 border border-yellow-500/20 rounded-lg">
                          <AlertTriangle className="w-3.5 h-3.5 text-yellow-400 flex-shrink-0 mt-0.5" />
                          <span className="text-xs text-slate-300">{si}</span>
                        </div>
                      ))}
                    </div>
                  </Sec>
                </Card>
              ) : (
                <Card className="p-8 text-center"><Empty msg="No safety instructions extracted" /></Card>
              )}
              {k.troubleshooting_procedures && k.troubleshooting_procedures.length > 0 && (
                <Card className="p-5">
                  <Sec icon={Wrench} label="Troubleshooting Procedures" color="text-blue-400">
                    <div className="space-y-3">
                      {k.troubleshooting_procedures.filter(t => t.symptom).map((t, i) => (
                        <div key={i} className="p-3 bg-[#0F1419] rounded-lg border border-[#334155]">
                          <div className="text-sm text-white font-medium">{t.symptom}</div>
                          {t.steps && t.steps.filter(Boolean).map((step, j) => (
                            <div key={j} className="text-xs text-slate-400 flex gap-1.5 mt-1">
                              <span className="text-blue-400">{j + 1}.</span>{step}
                            </div>
                          ))}
                        </div>
                      ))}
                    </div>
                  </Sec>
                </Card>
              )}
            </div>
          )}

          {activeTab === 5 && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
              {k.sensor_thresholds && Object.values(k.sensor_thresholds).some(Boolean) && (
                <Card className="p-4">
                  <Sec icon={AlertCircle} label="Sensor Thresholds" color="text-red-400">
                    {Object.entries(k.sensor_thresholds).map(([key, val]) =>
                      val ? (
                        <div key={key} className="flex justify-between text-xs py-2 border-b border-[#334155] last:border-0">
                          <span className="text-slate-400 capitalize">{key.replace(/_/g, ' ')}</span>
                          <span className="text-red-400 font-mono font-semibold">{String(val)}</span>
                        </div>
                      ) : null
                    )}
                  </Sec>
                </Card>
              )}
              {k.operating_conditions && (
                <Card className="p-4">
                  <Sec icon={Activity} label="Normal Operating Range" color="text-green-400">
                    {Object.entries(k.operating_conditions).map(([key, val]) =>
                      val ? (
                        <div key={key} className="flex justify-between text-xs py-2 border-b border-[#334155] last:border-0">
                          <span className="text-slate-400 capitalize">{key.replace(/_/g, ' ')}</span>
                          <span className="text-green-400 font-mono">{String(val)}</span>
                        </div>
                      ) : null
                    )}
                  </Sec>
                </Card>
              )}
            </div>
          )}
        </>
      )}
    </div>
  );
}

export default function DocumentIntelligence() {
  const [mainTab, setMainTab]         = useState(0);
  const [stats, setStats]             = useState(null);
  const [docs, setDocs]               = useState([]);
  const [selectedDoc, setSelectedDoc] = useState(null);
  const [uploading, setUploading]     = useState(false);
  const [processing, setProcessing]   = useState({});
  const [dragOver, setDragOver]       = useState(false);
  const [searchQ, setSearchQ]         = useState('');
  const [searchResults, setSearchResults] = useState(null);
  const [searching, setSearching]     = useState(false);
  const fileRef = useRef(null);

  useEffect(() => { loadStats(); loadDocs(); }, []);

  const loadStats = () =>
    fetch(`${API}/stats`).then(r => r.json()).then(setStats).catch(() => {});

  const loadDocs = () =>
    fetch(`${API}/documents`).then(r => r.json())
      .then(d => setDocs(d.documents || [])).catch(() => {});

  const handleFiles = async (files) => {
    for (const file of files) {
      setUploading(true);
      try {
        const fd = new FormData();
        fd.append('file', file);
        const up = await fetch(`${API}/upload`, { method: 'POST', body: fd });
        const upData = await up.json();
        const docId = upData.doc_id;
        if (!docId) continue;
        await loadDocs();
        setProcessing(p => ({ ...p, [docId]: true }));
        try {
          await fetch(`${API}/process/${docId}`, { method: 'POST' });
          await loadDocs();
          await loadStats();
        } finally {
          setProcessing(p => { const n = { ...p }; delete n[docId]; return n; });
        }
      } catch (e) { alert('Upload failed: ' + e.message); }
      finally { setUploading(false); }
    }
  };

  const deleteDoc = async (docId) => {
    if (!confirm('Delete this document and all extracted knowledge?')) return;
    await fetch(`${API}/documents/${docId}`, { method: 'DELETE' });
    loadDocs(); loadStats();
  };

  const doSearch = async () => {
    if (!searchQ.trim()) return;
    setSearching(true);
    try {
      const r = await fetch(`${API}/search?query=${encodeURIComponent(searchQ)}&top_k=8`);
      setSearchResults(await r.json());
    } finally { setSearching(false); }
  };

  if (selectedDoc) {
    return <DocDetail doc={selectedDoc} onBack={() => setSelectedDoc(null)} />;
  }

  const MAIN_TABS = [
    { label: 'Documents',    count: docs.length },
    { label: 'Smart Search' },
    { label: 'AI Assistant' },
  ];

  return (
    <div className="space-y-6">
      <input ref={fileRef} type="file" multiple accept=".pdf,.docx,.txt,.csv"
        className="hidden" onChange={e => handleFiles([...e.target.files])} />

      <div className="flex items-start justify-between flex-wrap gap-4">
        <div>
          <h1 className="text-2xl font-heading font-bold text-white flex items-center gap-2">
            <Brain className="w-6 h-6 text-orange-500" /> Document Intelligence Center
          </h1>
          <p className="text-slate-400 text-sm mt-0.5">
            Upload documents · AI extracts knowledge · Powers all AI features
          </p>
        </div>
        <button onClick={() => fileRef.current && fileRef.current.click()}
          className="flex items-center gap-2 px-4 py-2 bg-orange-500 hover:bg-orange-600 text-white rounded-lg font-medium text-sm transition-colors">
          <Upload className="w-4 h-4" /> Upload Document
        </button>
      </div>

      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
          {[
            { label: 'Total Documents',  val: stats.total_documents,  color: 'text-white',     bg: 'bg-slate-500/10 border-slate-500/20' },
            { label: 'Processed',        val: stats.processed,        color: 'text-green-400', bg: 'bg-green-500/10 border-green-500/20' },
            { label: 'Pending',          val: stats.pending,          color: 'text-yellow-400',bg: 'bg-yellow-500/10 border-yellow-500/20' },
            { label: 'Chunks Indexed',   val: stats.total_chunks,     color: 'text-blue-400',  bg: 'bg-blue-500/10 border-blue-500/20' },
            { label: 'Unique Equipment', val: stats.unique_equipment, color: 'text-orange-400',bg: 'bg-orange-500/10 border-orange-500/20' },
          ].map(({ label, val, color, bg }) => (
            <div key={label} className={`rounded-xl border p-3 text-center ${bg}`}>
              <div className={`text-2xl font-heading font-bold ${color}`}>{val || 0}</div>
              <div className="text-[10px] text-slate-400 mt-1">{label}</div>
            </div>
          ))}
        </div>
      )}

      <Card className="p-4">
        <div className="text-xs text-orange-400 font-semibold mb-3 uppercase tracking-wider">
          AI Processing Pipeline
        </div>
        <div className="grid grid-cols-3 md:grid-cols-9 gap-2 text-center">
          {[
            'Extract Text', 'Clean Text', 'Classify Type', 'Identify Equipment',
            'Extract Knowledge', 'Generate Summary', 'Create Embeddings',
            'Index ChromaDB', 'Enable AI Search'
          ].map((step, i) => (
            <div key={step} className="flex flex-col items-center gap-1">
              <div className="w-7 h-7 rounded-full bg-orange-500/10 border border-orange-500/20 flex items-center justify-center text-[10px] font-bold text-orange-400">
                {i + 1}
              </div>
              <span className="text-[9px] text-slate-500 leading-tight">{step}</span>
            </div>
          ))}
        </div>
      </Card>

      <div className="flex gap-1 bg-[#1E293B] p-1 rounded-xl border border-[#334155] w-fit">
        {MAIN_TABS.map((t, i) => (
          <Tab key={t.label} label={t.label} count={t.count} active={mainTab === i} onClick={() => setMainTab(i)} />
        ))}
      </div>

      {mainTab === 0 && (
        <div className="space-y-4">
          <div
            onDrop={e => { e.preventDefault(); setDragOver(false); handleFiles([...e.dataTransfer.files]); }}
            onDragOver={e => { e.preventDefault(); setDragOver(true); }}
            onDragLeave={() => setDragOver(false)}
            onClick={() => fileRef.current && fileRef.current.click()}
            className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all ${
              dragOver ? 'border-orange-500 bg-orange-500/5' : 'border-[#334155] hover:border-orange-500/40'
            }`}>
            <Upload className="w-10 h-10 text-orange-400 mx-auto mb-3" />
            <p className="text-white font-medium">Drop documents here or click to browse</p>
            <p className="text-slate-400 text-xs mt-1">PDF · DOCX · TXT · CSV</p>
            {uploading && (
              <div className="mt-3 flex items-center justify-center gap-2 text-yellow-400 text-sm">
                <Clock className="w-4 h-4 animate-spin" /> Uploading and analyzing...
              </div>
            )}
          </div>

          {docs.length === 0 ? (
            <Card className="p-12 text-center">
              <FileText className="w-12 h-12 text-slate-600 mx-auto mb-3" />
              <p className="text-slate-400">No documents yet</p>
              <p className="text-slate-500 text-xs mt-1">
                Upload a maintenance manual, SOP, or failure report to get started
              </p>
            </Card>
          ) : (
            <Card className="overflow-hidden">
              <table className="industrial-table">
                <thead>
                  <tr>
                    <th>Document</th>
                    <th>Type</th>
                    <th>Equipment</th>
                    <th>Manufacturer</th>
                    <th>Chunks</th>
                    <th>Uploaded</th>
                    <th>Status</th>
                    <th className="text-right">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {docs.map(doc => {
                    const status = processing[doc.doc_id] ? 'processing' : doc.processing_status;
                    return (
                      <tr key={doc.doc_id} className="cursor-pointer" onClick={() => setSelectedDoc(doc)}>
                        <td>
                          <div className="flex items-center gap-2">
                            <FileText className="w-4 h-4 text-orange-400 flex-shrink-0" />
                            <span className="font-medium truncate max-w-[180px]">{doc.file_name}</span>
                          </div>
                        </td>
                        <td>
                          {doc.document_type ? (
                            <span className="text-xs px-2 py-0.5 bg-orange-500/10 border border-orange-500/20 text-orange-400 rounded">
                              {doc.document_type}
                            </span>
                          ) : '—'}
                        </td>
                        <td className="text-slate-300">{doc.equipment_name || '—'}</td>
                        <td className="text-slate-400 text-xs">{doc.manufacturer || '—'}</td>
                        <td className="font-mono text-sm">{doc.chunk_count || 0}</td>
                        <td className="text-slate-400 text-xs">
                          {new Date(doc.upload_date).toLocaleDateString()}
                        </td>
                        <td onClick={e => e.stopPropagation()}>
                          <span className={`flex items-center gap-1 w-fit px-2 py-0.5 rounded border text-xs ${SC[status] || SC.uploaded}`}>
                            {status === 'completed' && <CheckCircle className="w-3 h-3" />}
                            {status === 'processing' && <Clock className="w-3 h-3 animate-spin" />}
                            {status === 'failed' && <AlertCircle className="w-3 h-3" />}
                            {status === 'uploaded' && <Clock className="w-3 h-3" />}
                            {status}
                          </span>
                        </td>
                        <td className="text-right" onClick={e => e.stopPropagation()}>
                          <div className="flex items-center justify-end gap-1">
                            <button onClick={() => setSelectedDoc(doc)}
                              className="p-1.5 text-blue-400 hover:bg-blue-500/20 rounded transition-colors">
                              <Eye className="w-3.5 h-3.5" />
                            </button>
                            <button onClick={() => deleteDoc(doc.doc_id)}
                              className="p-1.5 text-red-400 hover:bg-red-500/20 rounded transition-colors">
                              <Trash2 className="w-3.5 h-3.5" />
                            </button>
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </Card>
          )}
        </div>
      )}

      {mainTab === 1 && (
        <div className="space-y-4">
          <div className="flex gap-3">
            <div className="relative flex-1">
              <FileSearch className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
              <input value={searchQ} onChange={e => setSearchQ(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && doSearch()}
                placeholder="e.g. bearing replacement procedure, vibration limits, lubrication schedule..."
                className="input-industrial pl-10" />
            </div>
            <button onClick={doSearch} disabled={searching}
              className="px-5 py-2 bg-orange-500 hover:bg-orange-600 text-white rounded-lg font-medium text-sm flex items-center gap-2 transition-colors disabled:opacity-50">
              <Search className="w-4 h-4" />
              {searching ? 'Searching...' : 'Search'}
            </button>
          </div>

          {!searchResults && (
            <Card className="p-5">
              <div className="text-xs text-orange-400 font-semibold mb-3 uppercase tracking-wider">
                Suggested Searches
              </div>
              <div className="flex flex-wrap gap-2">
                {[
                  'bearing replacement', 'lubrication interval', 'overheating causes',
                  'vibration limits', 'safety lockout tagout', 'spare parts list',
                  'maintenance schedule', 'troubleshooting steps', 'inspection checklist',
                ].map(q => (
                  <button key={q} onClick={() => setSearchQ(q)}
                    className="text-xs px-3 py-1.5 rounded-lg border border-[#334155] text-slate-300 hover:text-white hover:border-orange-500/40 transition-colors">
                    {q}
                  </button>
                ))}
              </div>
            </Card>
          )}

          {searchResults && (
            <div className="space-y-3">
              <div className="flex items-center gap-3 text-sm text-slate-400">
                <span>{searchResults.total_results} results</span>
                <span>·</span>
                <span>{searchResults.retrieval_time_ms ? searchResults.retrieval_time_ms.toFixed(0) : 0}ms</span>
              </div>
              {searchResults.results && searchResults.results.map((r, i) => (
                <Card key={i} className="p-4">
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1">
                      <div className="flex items-center flex-wrap gap-2 mb-2">
                        <span className="text-xs font-semibold text-orange-400">{r.source_document}</span>
                        <span className="text-[10px] text-blue-400 bg-blue-500/10 border border-blue-500/20 px-1.5 py-0.5 rounded">
                          {r.document_type}
                        </span>
                        {r.equipment_name && (
                          <span className="text-[10px] text-green-400">{r.equipment_name}</span>
                        )}
                      </div>
                      <p className="text-sm text-slate-300 leading-relaxed">{r.content}</p>
                    </div>
                    <div className="text-right flex-shrink-0">
                      <div className="text-[10px] text-slate-500">Relevance</div>
                      <div className="text-lg font-bold text-orange-400">
                        {(r.similarity_score * 100).toFixed(0)}%
                      </div>
                    </div>
                  </div>
                </Card>
              ))}
            </div>
          )}
        </div>
      )}

      {mainTab === 2 && (
        <div className="grid grid-cols-1 xl:grid-cols-3 gap-5">
          <div className="xl:col-span-2">
            <AIChat />
          </div>
          <div className="space-y-4">
            <Card className="p-4">
              <div className="text-xs text-orange-400 font-semibold mb-3 uppercase tracking-wider">
                Knowledge Base Status
              </div>
              {stats && (
                <div className="space-y-2">
                  {[
                    { label: 'Documents Indexed', val: stats.processed },
                    { label: 'Chunks in Vector DB', val: stats.total_chunks },
                    { label: 'Equipment Covered', val: stats.unique_equipment },
                  ].map(({ label, val }) => (
                    <div key={label} className="flex justify-between text-xs py-1.5 border-b border-[#334155] last:border-0">
                      <span className="text-slate-400">{label}</span>
                      <span className="text-white font-mono font-bold">{val}</span>
                    </div>
                  ))}
                  {stats.equipment_list && stats.equipment_list.length > 0 && (
                    <div className="pt-2">
                      <div className="text-[10px] text-slate-500 mb-2">Equipment in knowledge base:</div>
                      <div className="flex flex-wrap gap-1.5">
                        {stats.equipment_list.map(eq => (
                          <span key={eq} className="text-[10px] px-2 py-0.5 bg-green-500/10 border border-green-500/20 text-green-400 rounded">
                            {eq}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </Card>
            <Card className="p-4">
              <p className="text-[10px] text-slate-500 leading-relaxed">
                <span className="text-orange-400 font-semibold">How it works: </span>
                The AI answers using only documents you upload. More documents means more accurate answers.
                Fault modes, procedures, spare parts, and safety instructions are extracted automatically.
              </p>
            </Card>
          </div>
        </div>
      )}
    </div>
  );
}
