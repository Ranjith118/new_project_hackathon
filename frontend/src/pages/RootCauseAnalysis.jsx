import { useState, useEffect, useCallback } from 'react';
import {
  Search, AlertTriangle, CheckCircle, Clock, RefreshCw,
  FileText, ChevronRight, ChevronLeft, Brain, BarChart3,
  Activity, Wrench, Shield, Package, Zap, AlertCircle,
  ThermometerSun, Gauge, Wind, Cpu, ChevronDown, ChevronUp,
  Play, Eye, TrendingDown, Info
} from 'lucide-react';
import {
  AreaChart, Area, PieChart, Pie, Cell, BarChart, Bar,
  XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid
} from 'recharts';

const API = 'http://localhost:8000';
const get  = (u) => fetch(API + u).then(r => r.json()).catch(() => null);
const post = (u, b) => fetch(API + u, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(b) }).then(r => r.json()).catch(() => null);

const confColor = (c) => c >= 90 ? '#10B981' : c >= 75 ? '#3B82F6' : c >= 50 ? '#FBBF24' : '#EF4444';
const confLabel = (c) => c >= 90 ? 'Very High' : c >= 75 ? 'High' : c >= 50 ? 'Moderate' : 'Low';
const riskBadge = (r) => ({ Critical: 'bg-red-500/20 text-red-400 border-red-500/40', High: 'bg-orange-500/20 text-orange-400 border-orange-500/40', Medium: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/40', Low: 'bg-green-500/20 text-green-400 border-green-500/40' })[r] || 'bg-slate-500/20 text-slate-400';
const sevBadge  = (s) => ({ critical: 'bg-red-500/20 text-red-400 border-red-500/40', high: 'bg-orange-500/20 text-orange-400 border-orange-500/40', medium: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/40' })[s] || 'bg-blue-500/20 text-blue-400 border-blue-500/40';
const SENSOR_ICONS = { temperature: ThermometerSun, vibration: Activity, current: Zap, pressure: Wind, rpm: Cpu };

const Card = ({ children, className = '' }) => (
  <div className={`bg-[#1E293B] border border-[#334155] rounded-xl ${className}`}>{children}</div>
);

function ConfidenceMeter({ confidence }) {
  const c = confColor(confidence);
  return (
    <div className="flex items-center gap-3">
      <div className="flex-1 bg-[#0F1419] rounded-full h-2">
        <div className="h-2 rounded-full transition-all" style={{ width: `${confidence}%`, backgroundColor: c }} />
      </div>
      <span className="text-sm font-mono font-bold w-10 text-right" style={{ color: c }}>{confidence?.toFixed(0)}%</span>
      <span className="text-xs px-2 py-0.5 rounded border" style={{ color: c, borderColor: c+'40', backgroundColor: c+'15' }}>{confLabel(confidence)}</span>
    </div>
  );
}

function CauseChain({ factors, primaryCause }) {
  const chain = [...(factors || []), primaryCause].filter(Boolean);
  return (
    <div className="flex flex-col items-center gap-1">
      {chain.map((item, i) => (
        <div key={i} className="flex flex-col items-center gap-1 w-full">
          <div className={`px-3 py-2 rounded-lg border text-xs text-center w-full ${i === chain.length - 1 ? 'bg-red-500/10 border-red-500/30 text-red-400 font-semibold' : 'bg-[#0F1419] border-[#334155] text-slate-300'}`}>{item}</div>
          {i < chain.length - 1 && <TrendingDown className="w-3.5 h-3.5 text-orange-400" />}
        </div>
      ))}
    </div>
  );
}

function RCADetail({ result, onBack }) {
  const [spares,      setSpares]      = useState([]);
  const [sensorHist,  setSensorHist]  = useState([]);
  const [maintLogs,   setMaintLogs]   = useState([]);
  const [showEv,      setShowEv]      = useState(true);
  const eq = result.equipment_name;

  useEffect(() => {
    Promise.all([
      get('/api/procurement/spares'),
      get(`/api/sensor-data/history/${encodeURIComponent(eq)}?hours=24`),
      get(`/api/maintenance-logs/?equipment_name=${encodeURIComponent(eq)}&limit=5`),
    ]).then(([sp, sh, ml]) => {
      setSpares(sp?.parts || []);
      setSensorHist((sh?.readings || []).map(r => ({
        time: new Date(r.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        temp: r.temperature, vib: r.vibration, curr: r.current
      })));
      setMaintLogs(Array.isArray(ml) ? ml : []);
    });
  }, [eq]);

  const conf  = result.primary_cause?.confidence ?? result.confidence ?? 0;
  const cause = result.primary_cause?.cause ?? '—';
  const cc    = confColor(conf);

  const confChart = (result.confidence_components || []).map(c => ({
    source: c.source, score: Math.round(c.score * 100)
  }));

  return (
    <div className="space-y-5">
      <button onClick={onBack} className="flex items-center gap-1 text-slate-400 hover:text-white text-sm transition-colors">
        <ChevronLeft className="w-4 h-4" /> Root Cause Analysis Center
      </button>

      {/* Header */}
      <Card className="p-5 border-l-4 border-l-orange-500">
        <div className="flex items-start justify-between flex-wrap gap-4">
          <div>
            <div className="flex items-center gap-2 flex-wrap mb-1">
              <h2 className="text-xl font-heading font-bold text-white">{eq}</h2>
              <span className="text-xs px-2 py-0.5 rounded border bg-orange-500/15 text-orange-400 border-orange-500/30">
                {result.analysis_id?.slice(0, 8).toUpperCase()}
              </span>
              <span className="text-xs text-slate-400">{new Date(result.timestamp).toLocaleString()}</span>
            </div>
          </div>
          <div className="text-right">
            <div className="text-3xl font-bold font-mono" style={{ color: cc }}>{conf.toFixed(0)}%</div>
            <div className="text-xs" style={{ color: cc }}>{confLabel(conf)} Confidence</div>
          </div>
        </div>

        <div className="mt-4 p-4 bg-red-500/5 border border-red-500/20 rounded-xl">
          <div className="text-xs text-orange-400 font-semibold mb-1">AI IDENTIFIED ROOT CAUSE</div>
          <div className="text-2xl font-heading font-bold text-white">{cause}</div>
          <div className="mt-2"><ConfidenceMeter confidence={conf} /></div>
          {result.primary_cause?.explanation && (
            <p className="text-xs text-slate-400 mt-2 leading-relaxed">{result.primary_cause.explanation}</p>
          )}
        </div>

        {result.sensor_readings && Object.keys(result.sensor_readings).some(k => result.sensor_readings[k] != null) && (
          <div className="grid grid-cols-2 md:grid-cols-5 gap-2 mt-4">
            {Object.entries(result.sensor_readings).map(([k, v]) => {
              if (v == null) return null;
              const Icon = SENSOR_ICONS[k] || Gauge;
              return (
                <div key={k} className="bg-[#0F1419] rounded-lg p-2.5 border border-[#334155] text-center">
                  <Icon className="w-3.5 h-3.5 text-orange-400 mx-auto mb-1" />
                  <div className="text-sm font-mono font-bold text-white">{v}</div>
                  <div className="text-[10px] text-slate-500 capitalize">{k}</div>
                </div>
              );
            })}
          </div>
        )}
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        {/* Left column */}
        <div className="space-y-4">
          <Card className="p-4">
            <h3 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
              <TrendingDown className="w-4 h-4 text-red-400" /> Failure Chain
            </h3>
            <CauseChain factors={result.contributing_factors} primaryCause={cause} />
          </Card>

          {result.secondary_causes?.length > 0 && (
            <Card className="p-4">
              <h3 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
                <AlertCircle className="w-4 h-4 text-yellow-400" /> Alternative Causes
              </h3>
              {result.secondary_causes.slice(0, 4).map((c, i) => (
                <div key={i} className="flex items-center justify-between py-2 border-b border-[#334155] last:border-0">
                  <span className="text-xs text-slate-300">{c.cause}</span>
                  <div className="flex items-center gap-2">
                    <div className="w-16 bg-[#0F1419] rounded-full h-1">
                      <div className="h-1 rounded-full" style={{ width: `${c.confidence}%`, backgroundColor: confColor(c.confidence) }} />
                    </div>
                    <span className="text-xs font-mono" style={{ color: confColor(c.confidence) }}>{c.confidence.toFixed(0)}%</span>
                  </div>
                </div>
              ))}
            </Card>
          )}

          {confChart.length > 0 && (
            <Card className="p-4">
              <h3 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
                <BarChart3 className="w-4 h-4 text-blue-400" /> Evidence Sources
              </h3>
              <ResponsiveContainer width="100%" height={120}>
                <BarChart data={confChart} margin={{ left: -20 }}>
                  <XAxis dataKey="source" tick={{ fontSize: 9, fill: '#94A3B8' }} />
                  <YAxis tick={{ fontSize: 9, fill: '#64748B' }} domain={[0, 100]} />
                  <Tooltip contentStyle={{ background: '#1E293B', border: '1px solid #334155', fontSize: 10 }} />
                  <Bar dataKey="score" fill="#F97316" radius={[3, 3, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </Card>
          )}
        </div>

        {/* Center + right (col-span-2) */}
        <div className="lg:col-span-2 space-y-4">
          {/* Evidence */}
          <Card className="p-4">
            <button onClick={() => setShowEv(e => !e)} className="flex items-center justify-between w-full mb-3">
              <h3 className="text-sm font-semibold text-white flex items-center gap-2">
                <Shield className="w-4 h-4 text-green-400" /> Supporting Evidence ({(result.primary_cause?.evidence?.length || 0) + (result.contributing_factors?.length || 0)})
              </h3>
              {showEv ? <ChevronUp className="w-4 h-4 text-slate-400" /> : <ChevronDown className="w-4 h-4 text-slate-400" />}
            </button>
            {showEv && (
              <div className="space-y-2">
                {(result.primary_cause?.evidence || []).map((e, i) => (
                  <div key={i} className="flex items-start gap-2 p-2.5 bg-green-500/5 border border-green-500/15 rounded-lg">
                    <CheckCircle className="w-3.5 h-3.5 text-green-400 flex-shrink-0 mt-0.5" />
                    <span className="text-xs text-slate-300">{e}</span>
                  </div>
                ))}
                {(result.contributing_factors || []).map((f, i) => (
                  <div key={i} className="flex items-start gap-2 p-2.5 bg-orange-500/5 border border-orange-500/15 rounded-lg">
                    <AlertTriangle className="w-3.5 h-3.5 text-orange-400 flex-shrink-0 mt-0.5" />
                    <span className="text-xs text-slate-300">{f}</span>
                  </div>
                ))}
              </div>
            )}
          </Card>

          {/* Reasoning path */}
          {result.reasoning_path?.length > 0 && (
            <Card className="p-4">
              <h3 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
                <Brain className="w-4 h-4 text-purple-400" /> AI Reasoning Path
              </h3>
              {result.reasoning_path.map((step, i) => (
                <div key={i} className="text-xs text-slate-300 py-1 border-b border-[#334155] last:border-0 leading-relaxed">{step}</div>
              ))}
            </Card>
          )}

          {/* Investigation steps */}
          {result.investigation_steps?.length > 0 && (
            <Card className="p-4">
              <h3 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
                <Search className="w-4 h-4 text-cyan-400" /> Investigation Steps
              </h3>
              {result.investigation_steps.map((step, i) => (
                <div key={i} className="flex items-start gap-2.5 p-2 bg-[#0F1419] rounded border border-[#334155] mb-1.5 last:mb-0">
                  <span className="text-xs text-orange-400 font-mono mt-0.5 flex-shrink-0">{i+1}.</span>
                  <span className="text-xs text-slate-300">{step.replace(/^\d+\.\s*/, '')}</span>
                </div>
              ))}
            </Card>
          )}

          {/* Recommended actions */}
          {result.recommended_actions?.length > 0 && (
            <Card className="p-4">
              <h3 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
                <Wrench className="w-4 h-4 text-green-400" /> Recommended Actions
              </h3>
              {result.recommended_actions.map((action, i) => (
                <div key={i} className="flex items-start gap-2 p-2.5 bg-green-500/5 border border-green-500/20 rounded-lg mb-1.5 last:mb-0">
                  <span className="text-green-400 font-mono text-xs mt-0.5 flex-shrink-0">{i+1}.</span>
                  <span className="text-xs text-white">{action}</span>
                </div>
              ))}
            </Card>
          )}

          {/* Sensor trend */}
          {sensorHist.length > 0 && (
            <Card className="p-4">
              <h3 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
                <Activity className="w-4 h-4 text-blue-400" /> 24h Sensor Trend
              </h3>
              <div className="grid grid-cols-2 gap-3">
                {[{ key: 'temp', label: 'Temperature', color: '#EF4444' }, { key: 'vib', label: 'Vibration', color: '#F97316' }].map(({ key, label, color }) => (
                  <div key={key}>
                    <div className="text-[10px] text-slate-400 mb-1">{label}</div>
                    <ResponsiveContainer width="100%" height={55}>
                      <AreaChart data={sensorHist.filter(d => d[key] != null)} margin={{ top: 0, right: 0, bottom: 0, left: 0 }}>
                        <defs>
                          <linearGradient id={`rcag${key}`} x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%"  stopColor={color} stopOpacity={0.3} />
                            <stop offset="95%" stopColor={color} stopOpacity={0} />
                          </linearGradient>
                        </defs>
                        <Area type="monotone" dataKey={key} stroke={color} strokeWidth={1.5} fill={`url(#rcag${key})`} dot={false} />
                        <Tooltip contentStyle={{ background: '#1E293B', border: '1px solid #334155', fontSize: 10 }} formatter={v => [v?.toFixed(2), label]} labelFormatter={() => ''} />
                      </AreaChart>
                    </ResponsiveContainer>
                  </div>
                ))}
              </div>
            </Card>
          )}

          {/* Similar cases */}
          {result.similar_cases?.length > 0 && (
            <Card className="p-4">
              <h3 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
                <FileText className="w-4 h-4 text-blue-400" /> Similar Historical Cases
              </h3>
              {result.similar_cases.slice(0, 4).map((c, i) => (
                <div key={i} className="flex items-start gap-3 p-2.5 bg-[#0F1419] rounded border border-[#334155] mb-1.5 last:mb-0">
                  <div className="text-center flex-shrink-0">
                    <div className="text-xs font-mono text-blue-400 font-bold">{Math.round(c.match_score * 100)}%</div>
                    <div className="text-[9px] text-slate-500">match</div>
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="text-xs text-white truncate">{c.issue}</div>
                    <div className="text-[10px] text-slate-400">RC: {c.root_cause || '—'} · {c.action_taken || '—'}</div>
                  </div>
                  <span className={`text-[10px] px-1.5 py-0.5 rounded border flex-shrink-0 ${sevBadge(c.severity)}`}>{c.severity}</span>
                </div>
              ))}
            </Card>
          )}

          {/* Spare parts */}
          {spares.filter(s => s.category === 'Bearings' || s.category === 'Seals').length > 0 && (
            <Card className="p-4">
              <h3 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
                <Package className="w-4 h-4 text-yellow-400" /> Relevant Spare Parts
              </h3>
              {spares.filter(s => s.category === 'Bearings' || s.category === 'Seals').slice(0, 4).map((s, i) => {
                const ok = s.stock_quantity >= s.minimum_stock;
                return (
                  <div key={i} className="flex items-center justify-between text-xs py-1.5 border-b border-[#334155] last:border-0">
                    <div>
                      <div className="text-white">{s.part_name}</div>
                      <div className="text-slate-500 text-[10px]">P/N: {s.part_number} · Lead: {s.lead_time_days}d</div>
                    </div>
                    <div className="text-right">
                      <div className={`font-mono font-bold ${ok ? 'text-green-400' : 'text-red-400'}`}>{s.stock_quantity}/{s.minimum_stock}</div>
                      <div className={`text-[10px] ${ok ? 'text-green-400' : 'text-red-400'}`}>{ok ? 'OK' : 'Low'}</div>
                    </div>
                  </div>
                );
              })}
            </Card>
          )}

          {/* Timeline */}
          {maintLogs.length > 0 && (
            <Card className="p-4">
              <h3 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
                <Clock className="w-4 h-4 text-cyan-400" /> Investigation Timeline
              </h3>
              <div className="relative pl-4 border-l border-[#334155] space-y-3">
                <div className="flex items-start gap-3 relative">
                  <div className="w-2 h-2 rounded-full bg-orange-500 absolute -left-1 mt-1" />
                  <div className="text-xs ml-1">
                    <div className="text-orange-400 font-medium">RCA Triggered</div>
                    <div className="text-slate-400">{new Date(result.timestamp).toLocaleString()}</div>
                  </div>
                </div>
                {maintLogs.map((log, i) => (
                  <div key={i} className="flex items-start gap-3 relative">
                    <div className={`w-2 h-2 rounded-full absolute -left-1 mt-1 ${log.severity === 'critical' ? 'bg-red-500' : log.severity === 'high' ? 'bg-orange-500' : 'bg-yellow-500'}`} />
                    <div className="text-xs ml-1">
                      <div className="text-white">{log.issue}</div>
                      <div className="text-slate-400">{log.maintenance_date} · {log.technician || '—'}</div>
                    </div>
                  </div>
                ))}
              </div>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}

export default function RootCauseAnalysis() {
  const [equipment, setEquipment] = useState([]);
  const [dashboard, setDashboard] = useState(null);
  const [patterns,  setPatterns]  = useState([]);
  const [analyzing, setAnalyzing] = useState({});
  const [results,   setResults]   = useState([]);
  const [selected,  setSelected]  = useState(null);
  const [loading,   setLoading]   = useState(true);
  const [showForm,  setShowForm]  = useState(false);
  const [filterEq,  setFilterEq]  = useState('');
  const [formData,  setFormData]  = useState({ equipment: '', issue: '', severity: 'high', temperature: '', vibration: '', current: '', pressure: '', rpm: '' });

  const load = useCallback(async () => {
    const [eq, dash, pat] = await Promise.all([
      get('/api/equipment/'),
      get('/api/rca/dashboard'),
      get('/api/rca/patterns'),
    ]);
    setEquipment(Array.isArray(eq) ? eq : []);
    setDashboard(dash);
    setPatterns(pat?.patterns || []);
    setLoading(false);
  }, []);

  useEffect(() => { load(); }, [load]);

  const runEquipmentRCA = async (eqName) => {
    setAnalyzing(a => ({ ...a, [eqName]: true }));
    const r = await post(`/api/rca/analyze-equipment/${encodeURIComponent(eqName)}`);
    if (r) setResults(prev => [r, ...prev.filter(p => p.equipment_name !== eqName)]);
    setAnalyzing(a => { const n = { ...a }; delete n[eqName]; return n; });
  };

  const runAllRCA = async () => {
    const liveResp = await get('/api/sensor-data/live-status');
    for (const eq of (liveResp?.equipment || [])) {
      await runEquipmentRCA(eq.equipment_name);
    }
  };

  const runManualRCA = async () => {
    if (!formData.equipment) return;
    setAnalyzing(a => ({ ...a, [formData.equipment]: true }));
    const body = { equipment: formData.equipment, issue: formData.issue, severity: formData.severity };
    if (formData.temperature) body.temperature = parseFloat(formData.temperature);
    if (formData.vibration)   body.vibration   = parseFloat(formData.vibration);
    if (formData.current)     body.current     = parseFloat(formData.current);
    if (formData.pressure)    body.pressure    = parseFloat(formData.pressure);
    if (formData.rpm)         body.rpm         = parseFloat(formData.rpm);
    const r = await post('/api/rca/analyze', body);
    if (r) { setResults(prev => [r, ...prev.filter(p => p.equipment_name !== formData.equipment)]); setShowForm(false); }
    setAnalyzing(a => { const n = { ...a }; delete n[formData.equipment]; return n; });
  };

  const filtered = results.filter(r => !filterEq || r.equipment_name?.toLowerCase().includes(filterEq.toLowerCase()));
  const causePie = dashboard?.common_causes || [];
  const PIE_COLORS = ['#EF4444','#F97316','#FBBF24','#3B82F6','#8B5CF6'];
  const patternBar = patterns.slice(0, 6).map(p => ({ name: p.probable_cause.split(' ')[0], w: Math.round(p.confidence_weight * 100) }));
  const uniqueEq = equipment.filter((e, i, arr) => arr.findIndex(x => x.equipment_name === e.equipment_name) === i);

  if (selected) return <div className="p-6"><RCADetail result={selected} onBack={() => setSelected(null)} /></div>;

  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-2xl font-heading font-bold text-white flex items-center gap-2">
            <Search className="w-6 h-6 text-orange-500" /> Root Cause Analysis Center
          </h1>
          <p className="text-slate-400 text-sm mt-0.5">AI-powered failure investigation · Identify WHY failures occur</p>
        </div>
        <div className="flex gap-2 flex-wrap">
          <button onClick={runAllRCA}
            className="flex items-center gap-1.5 px-3 py-2 bg-orange-500 hover:bg-orange-600 text-white text-sm rounded-lg transition-colors">
            <Play className="w-4 h-4" /> Analyze All Equipment
          </button>
          <button onClick={() => setShowForm(f => !f)}
            className="flex items-center gap-1.5 px-3 py-2 bg-[#1E293B] border border-[#334155] hover:border-orange-500/40 text-slate-300 text-sm rounded-lg transition-all">
            <Search className="w-4 h-4 text-orange-400" /> Manual RCA
          </button>
          <button onClick={load}
            className="p-2 bg-[#1E293B] border border-[#334155] hover:border-orange-500/40 text-slate-400 rounded-lg transition-all">
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* KPIs */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {[
          { label: 'Total Analyses',   val: (dashboard?.total_analyses || 0) + results.length, color: 'text-white',     bg: 'bg-slate-500/10 border-slate-500/20' },
          { label: 'Session Cases',    val: results.length,          color: 'text-orange-400', bg: 'bg-orange-500/10 border-orange-500/20' },
          { label: 'Avg Confidence',   val: results.length > 0 ? Math.round(results.reduce((a, r) => a + (r.primary_cause?.confidence || r.confidence || 0), 0) / results.length) + '%' : (dashboard?.average_confidence || 0) + '%', color: 'text-green-400', bg: 'bg-green-500/10 border-green-500/20' },
          { label: 'Failure Patterns', val: patterns.length,         color: 'text-blue-400',   bg: 'bg-blue-500/10 border-blue-500/20' },
        ].map(({ label, val, color, bg }) => (
          <div key={label} className={`rounded-xl border p-3 text-center ${bg}`}>
            <div className={`text-2xl font-heading font-bold ${color}`}>{val}</div>
            <div className="text-[10px] text-slate-400 mt-1">{label}</div>
          </div>
        ))}
      </div>

      {/* Manual RCA form */}
      {showForm && (
        <Card className="p-5">
          <h3 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
            <Brain className="w-4 h-4 text-orange-400" /> New RCA Investigation
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
            <div className="lg:col-span-2">
              <label className="text-[10px] text-slate-400 mb-1 block">Equipment *</label>
              <select value={formData.equipment} onChange={e => setFormData(f => ({ ...f, equipment: e.target.value }))} className="select-industrial text-sm">
                <option value="">Select equipment...</option>
                {uniqueEq.map(e => <option key={e.equipment_id} value={e.equipment_name}>{e.equipment_name}</option>)}
              </select>
            </div>
            <div className="lg:col-span-2">
              <label className="text-[10px] text-slate-400 mb-1 block">Issue Description</label>
              <input value={formData.issue} onChange={e => setFormData(f => ({ ...f, issue: e.target.value }))} placeholder="Describe the observed problem..." className="input-industrial text-sm" />
            </div>
            {[
              { k: 'temperature', l: 'Temperature (°C)' }, { k: 'vibration', l: 'Vibration (mm/s)' },
              { k: 'current',     l: 'Current (A)'      }, { k: 'pressure',  l: 'Pressure (bar)'  },
              { k: 'rpm',         l: 'RPM'              },
            ].map(({ k, l }) => (
              <div key={k}>
                <label className="text-[10px] text-slate-400 mb-1 block">{l}</label>
                <input type="number" value={formData[k]} onChange={e => setFormData(f => ({ ...f, [k]: e.target.value }))} placeholder="Optional" className="input-industrial text-sm" />
              </div>
            ))}
            <div>
              <label className="text-[10px] text-slate-400 mb-1 block">Severity</label>
              <select value={formData.severity} onChange={e => setFormData(f => ({ ...f, severity: e.target.value }))} className="select-industrial text-sm">
                {['critical','high','medium','low'].map(s => <option key={s} value={s}>{s.charAt(0).toUpperCase()+s.slice(1)}</option>)}
              </select>
            </div>
          </div>
          <div className="flex gap-2 mt-4">
            <button onClick={runManualRCA} disabled={!formData.equipment || analyzing[formData.equipment]}
              className="flex items-center gap-2 px-4 py-2 bg-orange-500 hover:bg-orange-600 text-white text-sm rounded-lg transition-colors disabled:opacity-50">
              {analyzing[formData.equipment] ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Brain className="w-4 h-4" />}
              {analyzing[formData.equipment] ? 'Analyzing...' : 'Run RCA'}
            </button>
            <button onClick={() => setShowForm(false)} className="px-4 py-2 bg-[#334155] text-slate-300 text-sm rounded-lg hover:bg-[#475569] transition-colors">Cancel</button>
          </div>
        </Card>
      )}

      {/* Analyzing indicator */}
      {Object.keys(analyzing).length > 0 && (
        <Card className="p-3 border-orange-500/20 bg-orange-500/5">
          <div className="flex items-center gap-2">
            <Brain className="w-4 h-4 text-orange-400 animate-pulse" />
            <span className="text-sm text-orange-400">Analyzing: {Object.keys(analyzing).join(', ')}...</span>
          </div>
        </Card>
      )}

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        {/* Results list */}
        <div className="xl:col-span-2 space-y-3">
          <div className="flex items-center gap-3">
            <input value={filterEq} onChange={e => setFilterEq(e.target.value)} placeholder="Filter by equipment..." className="input-industrial text-sm flex-1 max-w-xs" />
            {results.length > 0 && <span className="text-xs text-slate-500">{filtered.length} results</span>}
          </div>

          {filtered.length === 0 && !Object.keys(analyzing).length && (
            <Card className="p-10 text-center">
              <Search className="w-12 h-12 text-slate-600 mx-auto mb-3" />
              <p className="text-slate-400 mb-3">No analyses yet. Click a button below or run all equipment.</p>
            </Card>
          )}

          {filtered.map((r, i) => {
            const conf  = r.primary_cause?.confidence ?? r.confidence ?? 0;
            const cause = r.primary_cause?.cause ?? '—';
            const cc    = confColor(conf);
            return (
              <Card key={i} className="p-4 hover:border-orange-500/30 cursor-pointer transition-all" onClick={() => setSelected(r)}>
                <div className="flex items-start justify-between gap-3">
                  <div className="flex items-center gap-3 flex-1 min-w-0">
                    <div className="w-10 h-10 rounded-xl bg-orange-500/10 border border-orange-500/20 flex items-center justify-center flex-shrink-0">
                      <Brain className="w-5 h-5 text-orange-400" />
                    </div>
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="text-white font-medium text-sm">{r.equipment_name}</span>
                        <span className="text-[10px] text-slate-500 font-mono">{new Date(r.timestamp).toLocaleTimeString()}</span>
                      </div>
                      <div className="text-sm text-orange-300 mt-0.5 font-semibold">{cause}</div>
                      <div className="flex flex-wrap gap-1 mt-1">
                        {(r.contributing_factors || []).slice(0, 2).map((f, j) => (
                          <span key={j} className="text-[10px] text-slate-400 px-1.5 py-0.5 bg-[#0F1419] rounded border border-[#334155]">{f}</span>
                        ))}
                      </div>
                    </div>
                  </div>
                  <div className="text-right flex-shrink-0">
                    <div className="text-xl font-bold font-mono" style={{ color: cc }}>{conf.toFixed(0)}%</div>
                    <div className="text-[10px] text-slate-500">{confLabel(conf)}</div>
                    <ChevronRight className="w-4 h-4 text-slate-500 ml-auto mt-1" />
                  </div>
                </div>
                <div className="mt-3"><ConfidenceMeter confidence={conf} /></div>
              </Card>
            );
          })}

          {/* Quick analysis buttons */}
          <Card className="p-4">
            <h3 className="text-xs text-slate-400 mb-3 uppercase font-semibold tracking-wider">Quick Equipment Analysis</h3>
            <div className="flex flex-wrap gap-2">
              {uniqueEq.map(eq => (
                <button key={eq.equipment_id} disabled={!!analyzing[eq.equipment_name]} onClick={() => runEquipmentRCA(eq.equipment_name)}
                  className="flex items-center gap-1.5 px-3 py-1.5 bg-[#0F1419] border border-[#334155] hover:border-orange-500/40 text-slate-300 hover:text-white text-xs rounded-lg transition-all disabled:opacity-50">
                  {analyzing[eq.equipment_name] ? <RefreshCw className="w-3 h-3 animate-spin text-orange-400" /> : <Play className="w-3 h-3 text-orange-400" />}
                  {eq.equipment_name}
                </button>
              ))}
            </div>
          </Card>
        </div>

        {/* Right: Analytics */}
        <div className="space-y-4">
          {causePie.length > 0 && (
            <Card className="p-4">
              <h3 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
                <BarChart3 className="w-4 h-4 text-orange-400" /> Common Root Causes
              </h3>
              <ResponsiveContainer width="100%" height={140}>
                <PieChart>
                  <Pie data={causePie} cx="50%" cy="50%" innerRadius={35} outerRadius={60} dataKey="percentage" nameKey="cause" strokeWidth={0}>
                    {causePie.map((_, i) => <Cell key={i} fill={PIE_COLORS[i % 5]} />)}
                  </Pie>
                  <Tooltip contentStyle={{ background: '#1E293B', border: '1px solid #334155', fontSize: 11 }} formatter={(v, n, p) => [v + '%', p.payload.cause]} />
                </PieChart>
              </ResponsiveContainer>
              <div className="space-y-1 mt-1">
                {causePie.map((c, i) => (
                  <div key={i} className="flex items-center gap-2 text-xs">
                    <div className="w-2 h-2 rounded-full flex-shrink-0" style={{ backgroundColor: PIE_COLORS[i % 5] }} />
                    <span className="text-slate-300 flex-1 truncate">{c.cause}</span>
                    <span className="text-slate-400 font-mono">{c.percentage}%</span>
                  </div>
                ))}
              </div>
            </Card>
          )}

          {patternBar.length > 0 && (
            <Card className="p-4">
              <h3 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 text-yellow-400" /> Failure Patterns ({patterns.length})
              </h3>
              <ResponsiveContainer width="100%" height={160}>
                <BarChart data={patternBar} layout="vertical" margin={{ left: 5, right: 20 }}>
                  <XAxis type="number" tick={{ fontSize: 9, fill: '#64748B' }} domain={[0, 100]} />
                  <YAxis type="category" dataKey="name" tick={{ fontSize: 9, fill: '#94A3B8' }} width={55} />
                  <Tooltip contentStyle={{ background: '#1E293B', border: '1px solid #334155', fontSize: 10 }} formatter={v => [v + '%', 'Confidence']} />
                  <Bar dataKey="w" fill="#F97316" radius={[0, 3, 3, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </Card>
          )}

          <Card className="p-4">
            <h3 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
              <Brain className="w-4 h-4 text-purple-400" /> RCA Engine Stats
            </h3>
            {[
              { label: 'Total Analyses',   val: (dashboard?.total_analyses || 0) + results.length },
              { label: 'Avg Confidence',   val: (dashboard?.average_confidence || 0) + '%' },
              { label: 'Patterns Loaded',  val: patterns.length },
              { label: 'Session Results',  val: results.length },
            ].map(({ label, val }) => (
              <div key={label} className="flex justify-between text-xs py-1.5 border-b border-[#334155] last:border-0">
                <span className="text-slate-400">{label}</span>
                <span className="text-white font-mono font-bold">{val}</span>
              </div>
            ))}
          </Card>
        </div>
      </div>
    </div>
  );
}
