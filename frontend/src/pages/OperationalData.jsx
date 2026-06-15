import { useState, useEffect, useCallback } from 'react';
import {
  AlertTriangle, Clock, Zap, FileText, Database,
  RefreshCw, Plus, X, CheckCircle, ChevronDown,
  BarChart3, TrendingUp, Activity, Brain, Trash2,
  AlertCircle, Timer, Wrench
} from 'lucide-react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, PieChart, Pie, Cell, LineChart,
  Line, Legend
} from 'recharts';

const API = 'http://localhost:8000/api/operational';
const EQ_API = 'http://localhost:8000/api/equipment';
const get = (url) => fetch(url).then(r => r.json()).catch(() => null);

const COLORS = ['#EF4444','#F97316','#FBBF24','#10B981','#3B82F6','#8B5CF6','#EC4899','#14B8A6'];

const SEV_COLOR = { critical:'text-red-400', high:'text-orange-400', medium:'text-yellow-400', low:'text-green-400' };
const SEV_BG    = { critical:'bg-red-500/10 border-red-500/30', high:'bg-orange-500/10 border-orange-500/30', medium:'bg-yellow-500/10 border-yellow-500/30', low:'bg-green-500/10 border-green-500/30' };
const STATUS_COLOR = { open:'text-red-400', active:'text-red-400', resolved:'text-green-400', acknowledged:'text-yellow-400', under_review:'text-blue-400', closed:'text-slate-400' };

const Card = ({ children, className='' }) => (
  <div className={`bg-[#1E293B] border border-[#334155] rounded-xl ${className}`}>{children}</div>
);

const Badge = ({ label, color='text-slate-400', bg='bg-slate-500/10 border-slate-500/20' }) => (
  <span className={`text-[10px] px-2 py-0.5 rounded border capitalize font-medium ${color} ${bg}`}>{label}</span>
);

const Input = ({ label, required, children, hint }) => (
  <div>
    <label className="block text-xs text-slate-400 mb-1">{label}{required && <span className="text-red-400 ml-0.5">*</span>}</label>
    {children}
    {hint && <p className="text-[10px] text-slate-600 mt-0.5">{hint}</p>}
  </div>
);

const TABS = [
  { id:'delays',     label:'Delay Logs',       icon: Timer,         color:'text-yellow-400' },
  { id:'faults',     label:'Fault & Error',    icon: Zap,           color:'text-red-400'    },
  { id:'incidents',  label:'Incidents',         icon: AlertTriangle, color:'text-orange-400' },
  { id:'breakdowns', label:'Breakdowns',        icon: Wrench,        color:'text-purple-400' },
  { id:'analytics',  label:'Analytics',         icon: BarChart3,     color:'text-blue-400'   },
];

// ── shared select style
const sel = "w-full bg-[#0F1419] border border-[#334155] text-white text-sm rounded-lg px-3 py-2 focus:outline-none focus:border-orange-500";
const inp = "w-full bg-[#0F1419] border border-[#334155] text-white text-sm rounded-lg px-3 py-2 focus:outline-none focus:border-orange-500";
const textArea = "w-full bg-[#0F1419] border border-[#334155] text-white text-sm rounded-lg px-3 py-2 focus:outline-none focus:border-orange-500 resize-none";

export default function OperationalData() {
  const [tab,        setTab]        = useState('delays');
  const [equipment,  setEquipment]  = useState([]);
  const [delays,     setDelays]     = useState([]);
  const [faults,     setFaults]     = useState([]);
  const [incidents,  setIncidents]  = useState([]);
  const [breakdowns, setBreakdowns] = useState([]);
  const [analytics,  setAnalytics]  = useState(null);
  const [insights,   setInsights]   = useState([]);
  const [insLoading, setInsLoading] = useState(false);
  const [loading,    setLoading]    = useState(false);
  const [showForm,   setShowForm]   = useState(false);
  const [saving,     setSaving]     = useState(false);
  const [msg,        setMsg]        = useState('');
  const [filterEq,   setFilterEq]   = useState('');
  const [filterSev,  setFilterSev]  = useState('');

  // Form states per tab
  const blankDelay     = { equipment_name:'', delay_start:'', delay_end:'', delay_duration_min:'', delay_category:'mechanical', production_impact:'medium', reason:'', operator_notes:'', reported_by:'', status:'open' };
  const blankFault     = { equipment_name:'', fault_code:'', error_message:'', fault_description:'', severity:'medium', fault_timestamp:'', status:'active', acknowledged_by:'', resolution_notes:'' };
  const blankIncident  = { equipment_name:'', incident_type:'equipment', description:'', incident_date:'', severity:'medium', affected_area:'', reported_by:'', corrective_action:'', preventive_action:'', status:'open' };
  const blankBreakdown = { equipment_name:'', failure_type:'', breakdown_date:'', downtime_hours:'', repair_time_hours:'', root_cause:'', failure_description:'', corrective_action:'', preventive_action:'', repair_cost:'', technician:'', parts_replaced:'' };

  const [form, setForm] = useState(blankDelay);
  const f = (k, v) => setForm(p => ({ ...p, [k]: v }));

  const loadAll = useCallback(async () => {
    setLoading(true);
    const [d, fl, i, b, eq] = await Promise.all([
      get(`${API}/delays?limit=100`),
      get(`${API}/faults?limit=100`),
      get(`${API}/incidents?limit=100`),
      get(`${API}/breakdowns?limit=100`),
      get(`${EQ_API}/?limit=100`),
    ]);
    if (d)  setDelays(d);
    if (fl) setFaults(fl);
    if (i)  setIncidents(i);
    if (b)  setBreakdowns(b);
    if (eq) setEquipment(Array.isArray(eq) ? eq : []);
    setLoading(false);
  }, []);

  const loadAnalytics = useCallback(async () => {
    const a = await get(`${API}/analytics`);
    if (a) setAnalytics(a);
  }, []);

  useEffect(() => { loadAll(); loadAnalytics(); }, [loadAll, loadAnalytics]);

  useEffect(() => {
    const blanks = { delays: blankDelay, faults: blankFault, incidents: blankIncident, breakdowns: blankBreakdown };
    setForm(blanks[tab] || blankDelay);
    setShowForm(false); setMsg('');
  }, [tab]);

  const loadInsights = async () => {
    setInsLoading(true);
    const r = await get(`${API}/ai-insights`);
    if (r?.insights) setInsights(r.insights);
    setInsLoading(false);
  };

  const handleSave = async (e) => {
    e.preventDefault();
    setSaving(true); setMsg('');
    const endpoints = { delays:'delays', faults:'faults', incidents:'incidents', breakdowns:'breakdowns' };
    try {
      const body = { ...form };
      // clean empty strings to null
      Object.keys(body).forEach(k => { if (body[k] === '') body[k] = null; });
      const r = await fetch(`${API}/${endpoints[tab]}`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
      });
      if (!r.ok) { const e = await r.json(); throw new Error(e.detail || 'Save failed'); }
      setMsg('Saved successfully!');
      setShowForm(false);
      await loadAll(); await loadAnalytics();
      setTimeout(() => setMsg(''), 3000);
    } catch (err) { setMsg('Error: ' + err.message); }
    finally { setSaving(false); }
  };

  const handleDelete = async (endpoint, id) => {
    if (!confirm('Delete this record?')) return;
    await fetch(`${API}/${endpoint}/${id}`, { method: 'DELETE' });
    await loadAll(); await loadAnalytics();
  };

  const handleStatusChange = async (endpoint, id, status) => {
    await fetch(`${API}/${endpoint}/${id}`, {
      method: 'PATCH', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status })
    });
    await loadAll();
  };

  const eqNames = equipment.map(e => e.equipment_name);

  // Filter helpers
  const filtered = (rows, nameKey='equipment_name') => rows.filter(r => {
    if (filterEq && !r[nameKey]?.toLowerCase().includes(filterEq.toLowerCase())) return false;
    if (filterSev && r.severity !== filterSev) return false;
    return true;
  });

  const totalRecords = delays.length + faults.length + incidents.length + breakdowns.length;
  const criticalFaults = faults.filter(f => f.severity === 'critical' && f.status === 'active').length;
  const openIncidents  = incidents.filter(i => i.status === 'open').length;
  const totalDowntime  = breakdowns.reduce((s, b) => s + (b.downtime_hours || 0), 0);

  // ── Form fields per tab ───────────────────────────────────
  const FORM_FIELDS = {
    delays: [
      { key:'equipment_name',    label:'Equipment',        type:'eq',      required:true  },
      { key:'delay_start',       label:'Delay Start',      type:'datetime', required:true  },
      { key:'delay_end',         label:'Delay End',        type:'datetime'                },
      { key:'delay_duration_min',label:'Duration (min)',   type:'number'                  },
      { key:'delay_category',    label:'Category',         type:'select',  options:['mechanical','electrical','process','planned','external','other'] },
      { key:'production_impact', label:'Production Impact',type:'select',  options:['none','low','medium','high','critical'] },
      { key:'reason',            label:'Reason',           type:'text',    required:true  },
      { key:'operator_notes',    label:'Operator Notes',   type:'textarea'                },
      { key:'reported_by',       label:'Reported By',      type:'text'                    },
      { key:'status',            label:'Status',           type:'select',  options:['open','under_review','resolved'] },
    ],
    faults: [
      { key:'equipment_name',    label:'Equipment',        type:'eq',      required:true  },
      { key:'fault_code',        label:'Fault Code',       type:'text',    placeholder:'e.g. ERR-204' },
      { key:'error_message',     label:'Error Message',    type:'text',    required:true  },
      { key:'fault_description', label:'Description',      type:'textarea'                },
      { key:'severity',          label:'Severity',         type:'select',  options:['low','medium','high','critical'] },
      { key:'fault_timestamp',   label:'Fault Time',       type:'datetime', required:true  },
      { key:'status',            label:'Status',           type:'select',  options:['active','acknowledged','resolved'] },
      { key:'acknowledged_by',   label:'Acknowledged By',  type:'text'                    },
      { key:'resolution_notes',  label:'Resolution Notes', type:'textarea'                },
    ],
    incidents: [
      { key:'equipment_name',    label:'Equipment',        type:'eq',      required:true  },
      { key:'incident_type',     label:'Incident Type',    type:'select',  options:['equipment','safety','process','environmental','other'] },
      { key:'description',       label:'Description',      type:'textarea', required:true  },
      { key:'incident_date',     label:'Date',             type:'date',    required:true  },
      { key:'severity',          label:'Severity',         type:'select',  options:['low','medium','high','critical'] },
      { key:'affected_area',     label:'Affected Area',    type:'text'                    },
      { key:'reported_by',       label:'Reported By',      type:'text'                    },
      { key:'corrective_action', label:'Corrective Action',type:'textarea'                },
      { key:'preventive_action', label:'Preventive Action',type:'textarea'                },
      { key:'status',            label:'Status',           type:'select',  options:['open','in_progress','closed'] },
    ],
    breakdowns: [
      { key:'equipment_name',    label:'Equipment',        type:'eq',      required:true  },
      { key:'failure_type',      label:'Failure Type',     type:'text',    required:true, placeholder:'e.g. Bearing Failure' },
      { key:'breakdown_date',    label:'Date',             type:'date',    required:true  },
      { key:'downtime_hours',    label:'Downtime (hours)', type:'number'                  },
      { key:'repair_time_hours', label:'Repair Time (hrs)',type:'number'                  },
      { key:'root_cause',        label:'Root Cause',       type:'textarea'                },
      { key:'failure_description',label:'Description',     type:'textarea', required:true  },
      { key:'corrective_action', label:'Corrective Action',type:'textarea'                },
      { key:'preventive_action', label:'Preventive Action',type:'textarea'                },
      { key:'repair_cost',       label:'Repair Cost (₹)', type:'number'                  },
      { key:'technician',        label:'Technician',       type:'text'                    },
      { key:'parts_replaced',    label:'Parts Replaced',   type:'text'                    },
    ],
  };

  const renderField = (field) => {
    const base = "w-full bg-[#0F1419] border border-[#334155] text-white text-sm rounded-lg px-3 py-2 focus:outline-none focus:border-orange-500";
    if (field.type === 'eq') return (
      <select value={form[field.key] || ''} onChange={e => f(field.key, e.target.value)} required={field.required} className={base}>
        <option value="">Select equipment...</option>
        {eqNames.map(n => <option key={n} value={n}>{n}</option>)}
      </select>
    );
    if (field.type === 'select') return (
      <select value={form[field.key] || ''} onChange={e => f(field.key, e.target.value)} className={base}>
        {(field.options || []).map(o => <option key={o} value={o}>{o}</option>)}
      </select>
    );
    if (field.type === 'textarea') return (
      <textarea value={form[field.key] || ''} onChange={e => f(field.key, e.target.value)}
        rows={2} className={`${base} resize-none`} placeholder={field.placeholder || ''} />
    );
    return (
      <input type={field.type === 'number' ? 'number' : field.type === 'datetime' ? 'datetime-local' : field.type === 'date' ? 'date' : 'text'}
        value={form[field.key] || ''} onChange={e => f(field.key, e.target.value)}
        required={field.required} placeholder={field.placeholder || ''}
        step={field.type === 'number' ? 'any' : undefined}
        className={base} />
    );
  };

  const currentTab = TABS.find(t => t.id === tab);
  const TabIcon = currentTab?.icon || BarChart3;

  return (
    <div className="space-y-5">

      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-2xl font-heading font-bold text-white flex items-center gap-2">
            <Database className="w-6 h-6 text-orange-500" /> Operational Data Center
          </h1>
          <p className="text-slate-400 text-sm mt-0.5">Delay logs · Fault records · Incidents · Breakdown history</p>
        </div>
        <div className="flex items-center gap-2">
          <button onClick={loadAll}
            className="p-2 bg-[#1E293B] border border-[#334155] hover:border-orange-500/40 text-slate-400 hover:text-white rounded-lg transition-all">
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* KPI cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {[
          { label:'Total Records',    val: totalRecords,   color:'text-white',      bg:'bg-slate-500/10 border-slate-500/20'   },
          { label:'Critical Faults',  val: criticalFaults, color:'text-red-400',    bg:'bg-red-500/10 border-red-500/20'       },
          { label:'Open Incidents',   val: openIncidents,  color:'text-orange-400', bg:'bg-orange-500/10 border-orange-500/20' },
          { label:'Total Downtime',   val: `${totalDowntime.toFixed(1)}h`, color:'text-yellow-400', bg:'bg-yellow-500/10 border-yellow-500/20' },
        ].map(({ label, val, color, bg }) => (
          <div key={label} className={`rounded-xl border p-4 ${bg}`}>
            <div className={`text-2xl font-heading font-bold ${color}`}>{val}</div>
            <div className="text-[10px] text-slate-400 mt-1">{label}</div>
          </div>
        ))}
      </div>

      {/* Tabs */}
      <div className="flex gap-1 bg-[#0F1419] border border-[#334155] rounded-xl p-1 flex-wrap">
        {TABS.map(t => (
          <button key={t.id} onClick={() => setTab(t.id)}
            className={`flex items-center gap-1.5 px-4 py-2 text-xs rounded-lg font-medium transition-all ${
              tab === t.id ? 'bg-orange-500 text-white' : 'text-slate-400 hover:text-white'
            }`}>
            <t.icon className="w-3.5 h-3.5" /> {t.label}
          </button>
        ))}
      </div>

      {/* Filter bar (not for analytics) */}
      {tab !== 'analytics' && (
        <div className="flex items-center gap-3 flex-wrap">
          <div className="relative flex-1 min-w-[180px]">
            <input value={filterEq} onChange={e => setFilterEq(e.target.value)}
              placeholder="Filter by equipment..." className="w-full bg-[#1E293B] border border-[#334155] text-white text-sm px-3 py-2 rounded-lg focus:outline-none focus:border-orange-500" />
          </div>
          {['faults','incidents'].includes(tab) && (
            <select value={filterSev} onChange={e => setFilterSev(e.target.value)}
              className="bg-[#1E293B] border border-[#334155] text-slate-300 text-sm rounded-lg px-3 py-2 focus:outline-none focus:border-orange-500">
              <option value="">All Severities</option>
              {['low','medium','high','critical'].map(s => <option key={s} value={s}>{s}</option>)}
            </select>
          )}
          <button onClick={() => setShowForm(f => !f)}
            className="flex items-center gap-1.5 px-4 py-2 bg-orange-500 hover:bg-orange-600 text-white text-sm rounded-lg font-medium transition-colors">
            <Plus className="w-4 h-4" /> {showForm ? 'Close' : `Add ${currentTab?.label || 'Record'}`}
          </button>
          {msg && <span className={`text-sm font-medium ${msg.startsWith('Error') ? 'text-red-400' : 'text-green-400'}`}>{msg}</span>}
        </div>
      )}

      {/* Add form */}
      {showForm && tab !== 'analytics' && (
        <Card className="p-5">
          <h3 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
            <TabIcon className={`w-4 h-4 ${currentTab?.color}`} /> Add {currentTab?.label}
          </h3>
          <form onSubmit={handleSave}>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-4">
              {(FORM_FIELDS[tab] || []).map(field => (
                <div key={field.key} className={field.type === 'textarea' ? 'md:col-span-2' : ''}>
                  <label className="block text-xs text-slate-400 mb-1">
                    {field.label}{field.required && <span className="text-red-400 ml-0.5">*</span>}
                  </label>
                  {renderField(field)}
                </div>
              ))}
            </div>
            <div className="flex items-center gap-3">
              <button type="submit" disabled={saving}
                className="flex items-center gap-2 px-5 py-2 bg-orange-500 hover:bg-orange-600 text-white text-sm rounded-lg font-medium disabled:opacity-50 transition-colors">
                {saving ? <RefreshCw className="w-4 h-4 animate-spin" /> : <CheckCircle className="w-4 h-4" />}
                {saving ? 'Saving...' : 'Save Record'}
              </button>
              <button type="button" onClick={() => setShowForm(false)}
                className="px-4 py-2 bg-[#334155] text-slate-300 text-sm rounded-lg hover:bg-[#475569] transition-colors">
                Cancel
              </button>
            </div>
          </form>
        </Card>
      )}

      {/* ── DELAY LOGS ───────────────────────────────────── */}
      {tab === 'delays' && (
        <Card className="overflow-hidden">
          {filtered(delays).length === 0 ? (
            <div className="p-12 text-center text-slate-500">
              <Timer className="w-10 h-10 mx-auto mb-3 opacity-30" />
              <p>No delay logs yet. Click <span className="text-orange-400">Add Delay Logs</span> to start.</p>
            </div>
          ) : (
            <table className="industrial-table">
              <thead><tr><th>ID</th><th>Equipment</th><th>Category</th><th>Duration</th><th>Reason</th><th>Impact</th><th>Status</th><th>Actions</th></tr></thead>
              <tbody>
                {filtered(delays).map(d => (
                  <tr key={d.delay_id}>
                    <td className="font-mono text-xs text-orange-400">{d.delay_code}</td>
                    <td className="font-medium">{d.equipment_name}</td>
                    <td className="capitalize text-slate-300">{d.delay_category}</td>
                    <td className="font-mono text-yellow-400">{d.delay_duration_min ? `${d.delay_duration_min} min` : '—'}</td>
                    <td className="text-slate-400 text-xs max-w-[200px] truncate">{d.reason}</td>
                    <td><Badge label={d.production_impact} color={d.production_impact === 'critical' ? 'text-red-400' : d.production_impact === 'high' ? 'text-orange-400' : 'text-yellow-400'} /></td>
                    <td><span className={`text-xs capitalize ${STATUS_COLOR[d.status] || 'text-slate-400'}`}>{d.status}</span></td>
                    <td>
                      <div className="flex items-center gap-1">
                        {d.status === 'open' && (
                          <button onClick={() => handleStatusChange('delays', d.delay_id, 'resolved')}
                            className="text-[10px] px-2 py-0.5 bg-green-500/10 text-green-400 border border-green-500/20 rounded hover:bg-green-500/20 transition-colors">Resolve</button>
                        )}
                        <button onClick={() => handleDelete('delays', d.delay_id)} className="text-slate-500 hover:text-red-400 transition-colors p-1">
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </Card>
      )}

      {/* ── FAULT LOGS ───────────────────────────────────── */}
      {tab === 'faults' && (
        <Card className="overflow-hidden">
          {filtered(faults).length === 0 ? (
            <div className="p-12 text-center text-slate-500">
              <Zap className="w-10 h-10 mx-auto mb-3 opacity-30" />
              <p>No fault logs yet. Click <span className="text-orange-400">Add Fault &amp; Error</span> to start.</p>
            </div>
          ) : (
            <table className="industrial-table">
              <thead><tr><th>Code</th><th>Equipment</th><th>Error Message</th><th>Severity</th><th>Time</th><th>Status</th><th>Actions</th></tr></thead>
              <tbody>
                {filtered(faults).map(f => (
                  <tr key={f.fault_id}>
                    <td className="font-mono text-xs text-orange-400">{f.fault_code || '—'}</td>
                    <td className="font-medium">{f.equipment_name}</td>
                    <td className="text-slate-400 text-xs max-w-[220px] truncate">{f.error_message}</td>
                    <td>
                      <Badge label={f.severity}
                        color={SEV_COLOR[f.severity] || 'text-slate-400'}
                        bg={SEV_BG[f.severity] || ''} />
                    </td>
                    <td className="text-slate-500 text-xs font-mono">{f.fault_timestamp ? new Date(f.fault_timestamp).toLocaleString() : '—'}</td>
                    <td><span className={`text-xs capitalize ${STATUS_COLOR[f.status] || 'text-slate-400'}`}>{f.status}</span></td>
                    <td>
                      <div className="flex items-center gap-1">
                        {f.status === 'active' && (
                          <button onClick={() => handleStatusChange('faults', f.fault_id, 'acknowledged')}
                            className="text-[10px] px-2 py-0.5 bg-yellow-500/10 text-yellow-400 border border-yellow-500/20 rounded hover:bg-yellow-500/20 transition-colors">Ack</button>
                        )}
                        {f.status !== 'resolved' && (
                          <button onClick={() => handleStatusChange('faults', f.fault_id, 'resolved')}
                            className="text-[10px] px-2 py-0.5 bg-green-500/10 text-green-400 border border-green-500/20 rounded hover:bg-green-500/20 transition-colors">Resolve</button>
                        )}
                        <button onClick={() => handleDelete('faults', f.fault_id)} className="text-slate-500 hover:text-red-400 transition-colors p-1">
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </Card>
      )}

      {/* ── INCIDENTS ────────────────────────────────────── */}
      {tab === 'incidents' && (
        <Card className="overflow-hidden">
          {filtered(incidents).length === 0 ? (
            <div className="p-12 text-center text-slate-500">
              <AlertTriangle className="w-10 h-10 mx-auto mb-3 opacity-30" />
              <p>No incidents yet. Click <span className="text-orange-400">Add Incidents</span> to start.</p>
            </div>
          ) : (
            <table className="industrial-table">
              <thead><tr><th>ID</th><th>Equipment</th><th>Type</th><th>Description</th><th>Severity</th><th>Date</th><th>Status</th><th>Actions</th></tr></thead>
              <tbody>
                {filtered(incidents).map(i => (
                  <tr key={i.incident_id}>
                    <td className="font-mono text-xs text-orange-400">{i.incident_code}</td>
                    <td className="font-medium">{i.equipment_name}</td>
                    <td className="capitalize text-slate-300 text-xs">{i.incident_type}</td>
                    <td className="text-slate-400 text-xs max-w-[200px] truncate">{i.description}</td>
                    <td><Badge label={i.severity} color={SEV_COLOR[i.severity] || 'text-slate-400'} bg={SEV_BG[i.severity] || ''} /></td>
                    <td className="text-slate-500 text-xs font-mono">{i.incident_date}</td>
                    <td><span className={`text-xs capitalize ${STATUS_COLOR[i.status] || 'text-slate-400'}`}>{i.status}</span></td>
                    <td>
                      <div className="flex items-center gap-1">
                        {i.status === 'open' && (
                          <button onClick={() => handleStatusChange('incidents', i.incident_id, 'closed')}
                            className="text-[10px] px-2 py-0.5 bg-green-500/10 text-green-400 border border-green-500/20 rounded hover:bg-green-500/20 transition-colors">Close</button>
                        )}
                        <button onClick={() => handleDelete('incidents', i.incident_id)} className="text-slate-500 hover:text-red-400 transition-colors p-1">
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </Card>
      )}

      {/* ── BREAKDOWNS ───────────────────────────────────── */}
      {tab === 'breakdowns' && (
        <Card className="overflow-hidden">
          {breakdowns.length === 0 ? (
            <div className="p-12 text-center text-slate-500">
              <Wrench className="w-10 h-10 mx-auto mb-3 opacity-30" />
              <p>No breakdown records yet. Click <span className="text-orange-400">Add Breakdowns</span> to start.</p>
            </div>
          ) : (
            <table className="industrial-table">
              <thead><tr><th>ID</th><th>Equipment</th><th>Failure Type</th><th>Date</th><th>Downtime</th><th>Root Cause</th><th>Cost</th><th>Actions</th></tr></thead>
              <tbody>
                {breakdowns.filter(b => !filterEq || b.equipment_name?.toLowerCase().includes(filterEq.toLowerCase())).map(b => (
                  <tr key={b.breakdown_id}>
                    <td className="font-mono text-xs text-orange-400">{b.breakdown_code}</td>
                    <td className="font-medium">{b.equipment_name}</td>
                    <td className="text-slate-300 text-xs">{b.failure_type}</td>
                    <td className="text-slate-500 text-xs font-mono">{b.breakdown_date}</td>
                    <td className="font-mono text-red-400">{b.downtime_hours}h</td>
                    <td className="text-slate-400 text-xs max-w-[160px] truncate">{b.root_cause || '—'}</td>
                    <td className="font-mono text-yellow-400">{b.repair_cost ? `₹${b.repair_cost.toLocaleString()}` : '—'}</td>
                    <td>
                      <button onClick={() => handleDelete('breakdowns', b.breakdown_id)} className="text-slate-500 hover:text-red-400 transition-colors p-1">
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </Card>
      )}

      {/* ── ANALYTICS ────────────────────────────────────── */}
      {tab === 'analytics' && analytics && (
        <div className="space-y-4">
          {/* Summary */}
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
            {[
              { label:'Delays',     val: analytics.summary.total_delays,         color:'text-yellow-400' },
              { label:'Faults',     val: analytics.summary.total_faults,         color:'text-red-400'    },
              { label:'Incidents',  val: analytics.summary.total_incidents,      color:'text-orange-400' },
              { label:'Breakdowns', val: analytics.summary.total_breakdowns,     color:'text-purple-400' },
              { label:'Downtime',   val: `${analytics.summary.total_downtime_hours}h`, color:'text-rose-400' },
              { label:'Delay Mins', val: `${analytics.summary.total_delay_minutes}m`,  color:'text-amber-400' },
            ].map(({ label, val, color }) => (
              <div key={label} className="rounded-xl border border-[#334155] bg-[#1E293B] p-3 text-center">
                <div className={`text-2xl font-heading font-bold ${color}`}>{val}</div>
                <div className="text-[10px] text-slate-400 mt-1">{label}</div>
              </div>
            ))}
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {/* Breakdown by equipment */}
            {analytics.top_breakdown_equipment.length > 0 && (
              <Card className="p-4">
                <h3 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
                  <Wrench className="w-4 h-4 text-purple-400" /> Top Breakdown Equipment
                </h3>
                <ResponsiveContainer width="100%" height={200}>
                  <BarChart data={analytics.top_breakdown_equipment} layout="vertical" margin={{ left:10, right:20 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#1E293B" />
                    <XAxis type="number" tick={{ fontSize:9, fill:'#64748B' }} />
                    <YAxis dataKey="equipment" type="category" tick={{ fontSize:9, fill:'#94A3B8' }} width={100} />
                    <Tooltip contentStyle={{ background:'#1E293B', border:'1px solid #334155', fontSize:10 }} />
                    <Bar dataKey="count" fill="#8B5CF6" radius={[0,3,3,0]} />
                  </BarChart>
                </ResponsiveContainer>
              </Card>
            )}

            {/* Failure type frequency */}
            {analytics.failure_type_frequency.length > 0 && (
              <Card className="p-4">
                <h3 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
                  <AlertTriangle className="w-4 h-4 text-red-400" /> Failure Type Frequency
                </h3>
                <ResponsiveContainer width="100%" height={200}>
                  <PieChart>
                    <Pie data={analytics.failure_type_frequency} dataKey="count" nameKey="type" cx="50%" cy="50%" outerRadius={70} label={({ type, percent }) => `${type} ${(percent*100).toFixed(0)}%`} labelLine={false} fontSize={9}>
                      {analytics.failure_type_frequency.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                    </Pie>
                    <Tooltip contentStyle={{ background:'#1E293B', border:'1px solid #334155', fontSize:10 }} />
                  </PieChart>
                </ResponsiveContainer>
              </Card>
            )}

            {/* Fault severity */}
            {analytics.fault_severity_counts.length > 0 && (
              <Card className="p-4">
                <h3 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
                  <Zap className="w-4 h-4 text-yellow-400" /> Fault Severity Distribution
                </h3>
                <ResponsiveContainer width="100%" height={180}>
                  <BarChart data={analytics.fault_severity_counts}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#1E293B" />
                    <XAxis dataKey="severity" tick={{ fontSize:10, fill:'#64748B' }} />
                    <YAxis tick={{ fontSize:10, fill:'#64748B' }} width={30} />
                    <Tooltip contentStyle={{ background:'#1E293B', border:'1px solid #334155', fontSize:10 }} />
                    <Bar dataKey="count" radius={[4,4,0,0]}>
                      {analytics.fault_severity_counts.map((e, i) => (
                        <Cell key={i} fill={e.severity==='critical'?'#EF4444':e.severity==='high'?'#F97316':e.severity==='medium'?'#FBBF24':'#10B981'} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </Card>
            )}

            {/* Monthly trend */}
            {analytics.monthly_breakdown_trend.length > 0 && (
              <Card className="p-4">
                <h3 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
                  <TrendingUp className="w-4 h-4 text-blue-400" /> Monthly Breakdown Trend
                </h3>
                <ResponsiveContainer width="100%" height={180}>
                  <LineChart data={analytics.monthly_breakdown_trend}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#1E293B" />
                    <XAxis dataKey="month" tick={{ fontSize:9, fill:'#64748B' }} />
                    <YAxis tick={{ fontSize:9, fill:'#64748B' }} width={30} />
                    <Tooltip contentStyle={{ background:'#1E293B', border:'1px solid #334155', fontSize:10 }} />
                    <Line type="monotone" dataKey="count" stroke="#3B82F6" strokeWidth={2} dot={{ r:3 }} />
                  </LineChart>
                </ResponsiveContainer>
              </Card>
            )}
          </div>

          {/* AI Insights */}
          <Card className="p-5">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-semibold text-white flex items-center gap-2">
                <Brain className="w-4 h-4 text-orange-400" /> AI Insights
              </h3>
              <button onClick={loadInsights} disabled={insLoading}
                className="flex items-center gap-1.5 px-3 py-1.5 bg-orange-500 hover:bg-orange-600 text-white text-xs rounded-lg disabled:opacity-50 transition-colors">
                {insLoading ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Brain className="w-3.5 h-3.5" />}
                {insLoading ? 'Generating...' : 'Generate Insights'}
              </button>
            </div>
            {insights.length === 0 ? (
              <p className="text-slate-500 text-sm">Click "Generate Insights" to get AI analysis of your operational data patterns.</p>
            ) : (
              <div className="space-y-2">
                {insights.map((ins, i) => (
                  <div key={i} className="flex items-start gap-3 p-3 bg-[#0F1419] border border-[#334155] rounded-lg">
                    <div className="w-5 h-5 rounded-full bg-orange-500/20 border border-orange-500/30 flex items-center justify-center flex-shrink-0 mt-0.5">
                      <span className="text-[9px] text-orange-400 font-bold">{i+1}</span>
                    </div>
                    <p className="text-sm text-slate-300 leading-relaxed">{ins}</p>
                  </div>
                ))}
              </div>
            )}
          </Card>
        </div>
      )}

    </div>
  );
}
