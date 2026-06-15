import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Brain, Database, FileText, Activity, Package, Wrench,
  AlertTriangle, CheckCircle, RefreshCw, Search, ChevronRight,
  Upload, Cpu, BarChart3, Shield, Clock, TrendingUp,
  Zap, BookOpen, Settings, ClipboardList, Timer
} from 'lucide-react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, LineChart, Line, PieChart, Pie, Cell, Legend
} from 'recharts';

const API = 'http://localhost:8000';
const get = url => fetch(url).then(r => r.json()).catch(() => null);

const COLORS = ['#10B981','#F97316','#EF4444','#3B82F6','#8B5CF6','#FBBF24','#EC4899','#14B8A6'];
const Card = ({ children, className = '' }) => (
  <div className={`bg-[#1E293B] border border-[#334155] rounded-xl ${className}`}>{children}</div>
);

const score_color = s => s >= 80 ? 'text-green-400' : s >= 60 ? 'text-yellow-400' : s >= 40 ? 'text-orange-400' : 'text-red-400';
const score_bg    = s => s >= 80 ? 'bg-green-500' : s >= 60 ? 'bg-yellow-500' : s >= 40 ? 'bg-orange-500' : 'bg-red-500';

// ── KPI card ────────────────────────────────────────────────
function KpiCard({ label, value, icon: Icon, color, bg, href, navigate }) {
  return (
    <div onClick={() => href && navigate(href)}
      className={`rounded-xl border p-4 ${bg} ${href ? 'cursor-pointer hover:scale-[1.02] transition-all' : ''}`}>
      <div className="flex items-center justify-between mb-2">
        <span className="text-[11px] text-slate-400">{label}</span>
        <Icon className={`w-4 h-4 ${color}`} />
      </div>
      <div className={`text-3xl font-heading font-bold ${color}`}>{value}</div>
      {href && <div className="text-[10px] text-slate-500 mt-1 flex items-center gap-1">View <ChevronRight className="w-3 h-3" /></div>}
    </div>
  );
}

// ── Score bar ────────────────────────────────────────────────
function ScoreBar({ label, score, total, complete }) {
  return (
    <div className="mb-3">
      <div className="flex items-center justify-between mb-1">
        <span className="text-xs text-slate-300">{label}</span>
        <span className={`text-xs font-mono font-bold ${score_color(score)}`}>{score}%</span>
      </div>
      <div className="w-full h-2 bg-[#0F1419] rounded-full overflow-hidden">
        <div className={`h-full rounded-full transition-all ${score_bg(score)}`} style={{ width: `${score}%` }} />
      </div>
      {total !== undefined && (
        <div className="text-[10px] text-slate-500 mt-0.5">{complete}/{total} records complete</div>
      )}
    </div>
  );
}

// ── Processing status badge ──────────────────────────────────
function StatusBadge({ status }) {
  const map = {
    completed:  'text-green-400 bg-green-500/10 border-green-500/20',
    processing: 'text-blue-400 bg-blue-500/10 border-blue-500/20',
    uploaded:   'text-yellow-400 bg-yellow-500/10 border-yellow-500/20',
    failed:     'text-red-400 bg-red-500/10 border-red-500/20',
  };
  return (
    <span className={`text-[10px] px-2 py-0.5 rounded border capitalize ${map[status] || 'text-slate-400 bg-slate-500/10 border-slate-500/20'}`}>
      {status}
    </span>
  );
}

const TABS = ['overview', 'data-quality', 'processing', 'activity'];

export default function InputIntelligenceCenter() {
  const navigate = useNavigate();
  const [tab,       setTab]       = useState('overview');
  const [kpis,      setKpis]      = useState(null);
  const [quality,   setQuality]   = useState(null);
  const [processing,setProcessing]= useState(null);
  const [activity,  setActivity]  = useState(null);
  const [loading,   setLoading]   = useState(true);
  const [search,    setSearch]    = useState('');
  const [searchRes, setSearchRes] = useState(null);
  const [searching, setSearching] = useState(false);

  const loadAll = useCallback(async () => {
    setLoading(true);
    const [k, q, p, a] = await Promise.all([
      get(`${API}/api/hub/kpis`),
      get(`${API}/api/hub/data-quality`),
      get(`${API}/api/hub/processing-status`),
      get(`${API}/api/hub/module-summary`),
    ]);
    if (k) setKpis(k);
    if (q) setQuality(q);
    if (p) setProcessing(p);
    if (a) setActivity(a);
    setLoading(false);
  }, []);

  useEffect(() => { loadAll(); }, [loadAll]);

  const doSearch = async () => {
    if (!search.trim()) return;
    setSearching(true);
    const r = await get(`${API}/api/search?q=${encodeURIComponent(search)}`);
    if (r) setSearchRes(r);
    setSearching(false);
  };

  const clearSearch = () => { setSearch(''); setSearchRes(null); };

  const modules = [
    { label:'Equipment',          icon: Settings,      color:'text-blue-400',   bg:'bg-blue-500/10 border-blue-500/20',    href:'/equipment',        key:'equipment'        },
    { label:'Sensor Data',        icon: Activity,      color:'text-green-400',  bg:'bg-green-500/10 border-green-500/20',  href:'/sensor-data',      key:'sensor_records'   },
    { label:'Maintenance Logs',   icon: Wrench,        color:'text-yellow-400', bg:'bg-yellow-500/10 border-yellow-500/20',href:'/maintenance-logs', key:'maintenance_logs' },
    { label:'Failure Reports',    icon: AlertTriangle, color:'text-red-400',    bg:'bg-red-500/10 border-red-500/20',      href:'/failure-reports',  key:'failure_reports'  },
    { label:'Spare Parts',        icon: Package,       color:'text-pink-400',   bg:'bg-pink-500/10 border-pink-500/20',    href:'/spare-parts',      key:'spare_parts'      },
    { label:'Documents',          icon: BookOpen,      color:'text-purple-400', bg:'bg-purple-500/10 border-purple-500/20',href:'/doc-intelligence', key:'documents'        },
    { label:'Active Alerts',      icon: Zap,           color:'text-orange-400', bg:'bg-orange-500/10 border-orange-500/20',href:'/alerts',           key:'active_alerts'    },
    { label:'Operational Records',icon: ClipboardList, color:'text-cyan-400',   bg:'bg-cyan-500/10 border-cyan-500/20',    href:'/operational',      key:'operational_records'},
    { label:'AI-Ready Docs',      icon: Brain,         color:'text-emerald-400',bg:'bg-emerald-500/10 border-emerald-500/20',href:'/doc-intelligence',key:'ai_ready_docs'   },
  ];

  const qModules = quality ? [
    { label:'Equipment',       ...quality.modules.equipment        },
    { label:'Maintenance Logs',...quality.modules.maintenance_logs  },
    { label:'Sensor Data',     ...quality.modules.sensor_data       },
    { label:'Documents',       ...quality.modules.documents         },
    { label:'Failure Reports', ...quality.modules.failure_reports   },
    { label:'Spare Parts',     ...quality.modules.spare_parts       },
  ] : [];

  const qualityChartData = qModules.map(m => ({ name: m.label.split(' ')[0], score: m.score }));

  return (
    <div className="space-y-6">

      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-orange-500 to-orange-700 flex items-center justify-center">
            <Brain className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="text-2xl font-heading font-bold text-white">Input Intelligence Center</h1>
            <p className="text-slate-400 text-sm">Central data hub · All modules connected · AI-powered processing</p>
          </div>
        </div>
        <button onClick={loadAll} className="p-2 bg-[#1E293B] border border-[#334155] hover:border-orange-500/40 text-slate-400 hover:text-white rounded-lg transition-all">
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
        </button>
      </div>

      {/* Global Search */}
      <Card className="p-4">
        <div className="flex items-center gap-3">
          <div className="flex-1 relative">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              value={search}
              onChange={e => setSearch(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && doSearch()}
              placeholder="Search across all modules — equipment, documents, faults, maintenance, inventory..."
              className="w-full bg-[#0F1419] border border-[#334155] text-white text-sm pl-9 pr-4 py-2.5 rounded-lg focus:outline-none focus:border-orange-500 transition-colors"
            />
          </div>
          <button onClick={doSearch} disabled={!search.trim() || searching}
            className="px-4 py-2.5 bg-orange-500 hover:bg-orange-600 text-white text-sm rounded-lg disabled:opacity-40 transition-colors flex items-center gap-2">
            {searching ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4" />}
            Search
          </button>
          {searchRes && <button onClick={clearSearch} className="text-xs text-slate-400 hover:text-white px-3 py-2 border border-[#334155] rounded-lg">Clear</button>}
        </div>

        {/* Search Results */}
        {searchRes && (
          <div className="mt-4 space-y-2">
            <div className="text-xs text-slate-400 mb-2">{searchRes.total} results for "{searchRes.query}"</div>
            {searchRes.total === 0 ? (
              <p className="text-slate-500 text-sm text-center py-4">No results found</p>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-2 max-h-72 overflow-y-auto pr-1">
                {searchRes.results.map((r, i) => (
                  <div key={i} onClick={() => navigate(r.href)}
                    className="flex items-center gap-3 p-3 bg-[#0F1419] border border-[#334155] hover:border-orange-500/40 rounded-lg cursor-pointer transition-all group">
                    <div className={`text-[10px] px-2 py-0.5 rounded border border-current/30 font-medium ${r.color} bg-current/5 flex-shrink-0`}>
                      {r.type}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="text-xs font-semibold text-white truncate">{r.title}</div>
                      <div className="text-[10px] text-slate-400 truncate">{r.subtitle}</div>
                    </div>
                    <ChevronRight className="w-3 h-3 text-slate-600 group-hover:text-orange-400 flex-shrink-0" />
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </Card>

      {/* Tabs */}
      <div className="flex gap-1 bg-[#0F1419] border border-[#334155] rounded-xl p-1">
        {[
          { id:'overview',    label:'Overview'         },
          { id:'data-quality',label:'Data Quality'     },
          { id:'processing',  label:'Processing Status'},
          { id:'activity',    label:'Recent Activity'  },
        ].map(t => (
          <button key={t.id} onClick={() => setTab(t.id)}
            className={`flex-1 py-2 text-xs rounded-lg font-medium transition-all ${tab === t.id ? 'bg-orange-500 text-white' : 'text-slate-400 hover:text-white'}`}>
            {t.label}
          </button>
        ))}
      </div>

      {/* ── OVERVIEW TAB ─────────────────────────────────── */}
      {tab === 'overview' && (
        <div className="space-y-6">
          {/* KPI Grid */}
          <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-5 gap-3">
            {modules.map(m => (
              <KpiCard key={m.key} label={m.label} value={kpis ? (kpis[m.key] ?? 0) : '—'}
                icon={m.icon} color={m.color} bg={`rounded-xl border ${m.bg}`}
                href={m.href} navigate={navigate} />
            ))}
          </div>

          {/* AI Readiness + Module links */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
            <Card className="p-5 lg:col-span-2">
              <h2 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
                <Brain className="w-4 h-4 text-orange-400" /> AI Readiness Score
              </h2>
              {quality ? (
                <>
                  <div className="flex items-center gap-4 mb-6">
                    <div className={`text-5xl font-heading font-bold ${score_color(quality.overall_ai_readiness)}`}>
                      {quality.overall_ai_readiness}%
                    </div>
                    <div>
                      <div className="text-sm text-white font-medium">
                        {quality.overall_ai_readiness >= 80 ? 'Excellent' : quality.overall_ai_readiness >= 60 ? 'Good' : quality.overall_ai_readiness >= 40 ? 'Fair' : 'Needs Improvement'}
                      </div>
                      <div className="text-xs text-slate-400 mt-0.5">Data quality across all modules</div>
                    </div>
                  </div>
                  <ResponsiveContainer width="100%" height={160}>
                    <BarChart data={qualityChartData} margin={{ top:0, right:0, bottom:0, left:-20 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#1E293B" />
                      <XAxis dataKey="name" tick={{ fontSize:10, fill:'#64748B' }} />
                      <YAxis tick={{ fontSize:10, fill:'#64748B' }} domain={[0,100]} />
                      <Tooltip contentStyle={{ background:'#1E293B', border:'1px solid #334155', fontSize:11 }} formatter={v => [`${v}%`, 'Score']} />
                      <Bar dataKey="score" radius={[4,4,0,0]}>
                        {qualityChartData.map((entry, i) => (
                          <Cell key={i} fill={entry.score >= 80 ? '#10B981' : entry.score >= 60 ? '#FBBF24' : entry.score >= 40 ? '#F97316' : '#EF4444'} />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </>
              ) : <div className="text-slate-500 text-sm">Loading...</div>}
            </Card>

            <Card className="p-5">
              <h2 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
                <Database className="w-4 h-4 text-orange-400" /> Quick Access
              </h2>
              <div className="space-y-1">
                {[
                  { label:'Equipment Registry',   href:'/equipment',        icon: Settings,      color:'text-blue-400'    },
                  { label:'Sensor Monitoring',     href:'/sensor-data',      icon: Activity,      color:'text-green-400'   },
                  { label:'Maintenance Logs',      href:'/maintenance-logs', icon: Wrench,        color:'text-yellow-400'  },
                  { label:'Failure Reports',       href:'/failure-reports',  icon: AlertTriangle, color:'text-red-400'     },
                  { label:'Document Intelligence', href:'/doc-intelligence', icon: BookOpen,      color:'text-purple-400'  },
                  { label:'Alert Center',          href:'/alerts',           icon: Zap,           color:'text-orange-400'  },
                  { label:'Operational Data',      href:'/operational',      icon: ClipboardList, color:'text-cyan-400'    },
                  { label:'AI Assistant',          href:'/assistant',        icon: Brain,         color:'text-emerald-400' },
                  { label:'Spare Parts',           href:'/spare-parts',      icon: Package,       color:'text-pink-400'    },
                ].map(({ label, href, icon: Icon, color }) => (
                  <button key={label} onClick={() => navigate(href)}
                    className="flex items-center gap-2.5 w-full py-2 px-2.5 text-xs text-slate-400 hover:text-white hover:bg-[#334155] rounded-lg transition-colors text-left group">
                    <Icon className={`w-3.5 h-3.5 ${color} flex-shrink-0`} />
                    <span>{label}</span>
                    <ChevronRight className="w-3 h-3 ml-auto opacity-0 group-hover:opacity-100" />
                  </button>
                ))}
              </div>
            </Card>
          </div>

          {/* Sensor trend + maintenance trend */}
          {processing && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              <Card className="p-4">
                <h3 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
                  <Activity className="w-4 h-4 text-green-400" /> Sensor Data (Last 7 Days)
                </h3>
                <ResponsiveContainer width="100%" height={140}>
                  <LineChart data={processing.sensor_data_trend}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#1E293B" />
                    <XAxis dataKey="date" tick={{ fontSize:9, fill:'#64748B' }} tickFormatter={d => d.slice(5)} />
                    <YAxis tick={{ fontSize:9, fill:'#64748B' }} width={30} />
                    <Tooltip contentStyle={{ background:'#1E293B', border:'1px solid #334155', fontSize:10 }} />
                    <Line type="monotone" dataKey="count" stroke="#10B981" strokeWidth={2} dot={{ r:3, fill:'#10B981' }} />
                  </LineChart>
                </ResponsiveContainer>
              </Card>
              <Card className="p-4">
                <h3 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
                  <Wrench className="w-4 h-4 text-yellow-400" /> Maintenance Logs (Last 7 Days)
                </h3>
                <ResponsiveContainer width="100%" height={140}>
                  <BarChart data={processing.maintenance_trend}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#1E293B" />
                    <XAxis dataKey="date" tick={{ fontSize:9, fill:'#64748B' }} tickFormatter={d => d.slice(5)} />
                    <YAxis tick={{ fontSize:9, fill:'#64748B' }} width={30} />
                    <Tooltip contentStyle={{ background:'#1E293B', border:'1px solid #334155', fontSize:10 }} />
                    <Bar dataKey="count" fill="#FBBF24" radius={[3,3,0,0]} />
                  </BarChart>
                </ResponsiveContainer>
              </Card>
            </div>
          )}
        </div>
      )}

      {/* ── DATA QUALITY TAB ─────────────────────────────── */}
      {tab === 'data-quality' && (
        <div className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
            {/* Overall score */}
            <Card className="p-6 flex flex-col items-center justify-center text-center">
              <div className={`text-6xl font-heading font-bold mb-2 ${score_color(quality?.overall_ai_readiness || 0)}`}>
                {quality?.overall_ai_readiness || 0}%
              </div>
              <div className="text-white font-semibold">Overall AI Readiness</div>
              <div className="text-slate-400 text-xs mt-1">Across all data modules</div>
              <div className="w-full mt-4 h-2 bg-[#0F1419] rounded-full overflow-hidden">
                <div className={`h-full rounded-full ${score_bg(quality?.overall_ai_readiness || 0)}`}
                  style={{ width: `${quality?.overall_ai_readiness || 0}%` }} />
              </div>
            </Card>

            {/* Module scores */}
            <Card className="p-5 lg:col-span-2">
              <h3 className="text-sm font-semibold text-white mb-4">Module Data Quality</h3>
              {qModules.map(m => (
                <ScoreBar key={m.label} label={m.label} score={m.score} total={m.total} complete={m.complete} />
              ))}
            </Card>
          </div>

          {/* Issues */}
          {quality?.issues && (
            <Card className="p-5">
              <h3 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 text-yellow-400" /> Data Quality Issues
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                {[
                  { label:'Missing Equipment Info',    val: quality.issues.missing_equipment_info,    color:'text-yellow-400', bg:'bg-yellow-500/10 border-yellow-500/20' },
                  { label:'Incomplete Maintenance Logs',val: quality.issues.incomplete_maintenance_logs,color:'text-orange-400', bg:'bg-orange-500/10 border-orange-500/20'},
                  { label:'Unprocessed Documents',     val: quality.issues.unprocessed_documents,     color:'text-red-400',    bg:'bg-red-500/10 border-red-500/20'       },
                ].map(({ label, val, color, bg }) => (
                  <div key={label} className={`rounded-xl border p-4 ${bg}`}>
                    <div className={`text-3xl font-heading font-bold ${color}`}>{val}</div>
                    <div className="text-xs text-slate-400 mt-1">{label}</div>
                    <div className="text-[10px] text-slate-500 mt-1">{val === 0 ? '✅ All good' : '⚠️ Needs attention'}</div>
                  </div>
                ))}
              </div>
            </Card>
          )}

          {/* Quality chart */}
          <Card className="p-5">
            <h3 className="text-sm font-semibold text-white mb-4">Quality Score Comparison</h3>
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={qualityChartData} margin={{ top:5, right:10, bottom:5, left:-10 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1E293B" />
                <XAxis dataKey="name" tick={{ fontSize:11, fill:'#64748B' }} />
                <YAxis tick={{ fontSize:11, fill:'#64748B' }} domain={[0,100]} />
                <Tooltip contentStyle={{ background:'#1E293B', border:'1px solid #334155', fontSize:11 }} formatter={v => [`${v}%`, 'Quality']} />
                <Bar dataKey="score" radius={[4,4,0,0]}>
                  {qualityChartData.map((entry, i) => (
                    <Cell key={i} fill={entry.score >= 80 ? '#10B981' : entry.score >= 60 ? '#FBBF24' : entry.score >= 40 ? '#F97316' : '#EF4444'} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </Card>
        </div>
      )}

      {/* ── PROCESSING STATUS TAB ────────────────────────── */}
      {tab === 'processing' && (
        <div className="space-y-4">
          {/* Status counts */}
          {processing?.status_counts && (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              {[
                { key:'completed',  label:'Completed',  color:'text-green-400',  bg:'bg-green-500/10 border-green-500/20'  },
                { key:'processing', label:'Processing', color:'text-blue-400',   bg:'bg-blue-500/10 border-blue-500/20'   },
                { key:'uploaded',   label:'Pending',    color:'text-yellow-400', bg:'bg-yellow-500/10 border-yellow-500/20'},
                { key:'failed',     label:'Failed',     color:'text-red-400',    bg:'bg-red-500/10 border-red-500/20'     },
              ].map(({ key, label, color, bg }) => (
                <div key={key} className={`rounded-xl border p-4 text-center ${bg}`}>
                  <div className={`text-3xl font-heading font-bold ${color}`}>{processing.status_counts[key] || 0}</div>
                  <div className="text-xs text-slate-400 mt-1">{label}</div>
                </div>
              ))}
            </div>
          )}

          {/* Document pipeline */}
          <Card className="overflow-hidden">
            <div className="p-4 border-b border-[#334155] flex items-center justify-between">
              <h3 className="text-sm font-semibold text-white flex items-center gap-2">
                <FileText className="w-4 h-4 text-purple-400" /> Document Processing Pipeline
              </h3>
              <button onClick={() => navigate('/doc-intelligence')}
                className="text-xs text-orange-400 hover:text-orange-300 flex items-center gap-1">
                View All <ChevronRight className="w-3 h-3" />
              </button>
            </div>
            {processing?.document_pipeline?.length === 0 ? (
              <div className="p-8 text-center text-slate-500 text-sm">No documents uploaded yet</div>
            ) : (
              <table className="industrial-table">
                <thead><tr><th>File</th><th>Type</th><th>Equipment</th><th>Status</th><th>Chunks</th><th>Uploaded</th></tr></thead>
                <tbody>
                  {(processing?.document_pipeline || []).map((doc, i) => (
                    <tr key={i}>
                      <td className="font-medium text-white max-w-[180px] truncate">{doc.file_name}</td>
                      <td className="text-slate-400 uppercase text-xs">{doc.file_type}</td>
                      <td className="text-slate-300 text-xs">{doc.equipment_name || '—'}</td>
                      <td><StatusBadge status={doc.status} /></td>
                      <td className="font-mono text-slate-300">{doc.chunk_count || 0}</td>
                      <td className="text-slate-500 text-xs font-mono">{doc.upload_date ? new Date(doc.upload_date).toLocaleDateString() : '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </Card>

          {/* Upload CTA */}
          <Card className="p-5">
            <h3 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
              <Upload className="w-4 h-4 text-orange-400" /> Add More Data
            </h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              {[
                { label:'Upload Document', href:'/doc-intelligence', icon: BookOpen, color:'text-purple-400', desc:'PDF, DOCX, TXT manuals' },
                { label:'Add Equipment',   href:'/equipment',        icon: Settings,  color:'text-blue-400',   desc:'Register new machine' },
                { label:'Log Maintenance', href:'/maintenance-logs', icon: Wrench,    color:'text-yellow-400', desc:'Record maintenance work' },
                { label:'Enter Fault',     href:'/operational',      icon: Zap,       color:'text-red-400',    desc:'Log fault or incident' },
              ].map(({ label, href, icon: Icon, color, desc }) => (
                <button key={label} onClick={() => navigate(href)}
                  className="p-4 bg-[#0F1419] border border-[#334155] hover:border-orange-500/40 rounded-xl text-left transition-all hover:scale-[1.02]">
                  <Icon className={`w-5 h-5 ${color} mb-2`} />
                  <div className="text-sm font-medium text-white">{label}</div>
                  <div className="text-[10px] text-slate-500 mt-0.5">{desc}</div>
                </button>
              ))}
            </div>
          </Card>
        </div>
      )}

      {/* ── ACTIVITY TAB ─────────────────────────────────── */}
      {tab === 'activity' && (
        <Card className="overflow-hidden">
          <div className="p-4 border-b border-[#334155]">
            <h3 className="text-sm font-semibold text-white flex items-center gap-2">
              <Clock className="w-4 h-4 text-orange-400" /> Recent Data Activity
            </h3>
          </div>
          {!activity?.recent_activity?.length ? (
            <div className="p-12 text-center text-slate-500">No activity yet. Start adding data to the system.</div>
          ) : (
            <div className="divide-y divide-[#334155]">
              {activity.recent_activity.map((a, i) => (
                <div key={i} className="flex items-center gap-4 px-4 py-3 hover:bg-[#0F1419] transition-colors">
                  <span className={`text-[10px] px-2 py-0.5 rounded border border-current/20 bg-current/5 font-medium flex-shrink-0 ${a.color}`}>
                    {a.module}
                  </span>
                  <span className="text-sm text-slate-300 flex-1 truncate">{a.text}</span>
                  <span className="text-[10px] text-slate-500 flex-shrink-0 font-mono">
                    {new Date(a.time).toLocaleString()}
                  </span>
                </div>
              ))}
            </div>
          )}
        </Card>
      )}
    </div>
  );
}
