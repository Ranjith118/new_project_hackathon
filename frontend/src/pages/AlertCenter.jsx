import { useState, useEffect, useCallback, useRef } from 'react';
import {
  AlertTriangle, AlertCircle, CheckCircle, Bell, XCircle,
  RefreshCw, Filter, Clock, Activity, Search, ChevronRight,
  ChevronLeft, Eye, Check, X, Wrench, Brain, Package,
  ThermometerSun, Gauge, Zap, Wind, Cpu, Info, Shield
} from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';

const API = 'http://localhost:8000';
const get  = (url) => fetch(API + url).then(r => r.json()).catch(() => null);
const post = (url, body) => fetch(API + url, {
  method: 'POST', headers: { 'Content-Type': 'application/json' },
  body: body ? JSON.stringify(body) : undefined
}).then(r => r.json()).catch(() => null);

/* ── timestamp helpers ──────────────────────────────────── */
function safeDate(ts) {
  if (!ts) return null;
  const d = new Date(ts);
  return isNaN(d.getTime()) ? null : d;
}

function fmtTime(ts) {
  const d = safeDate(ts);
  if (!d) return '—';
  return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
}

function fmtDateTime(ts) {
  const d = safeDate(ts);
  if (!d) return '—';
  return d.toLocaleString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit', second: '2-digit' });
}

function fmtAgo(ts) {
  const d = safeDate(ts);
  if (!d) return '';
  const secs = Math.floor((Date.now() - d.getTime()) / 1000);
  if (secs < 5)   return 'just now';
  if (secs < 60)  return `${secs}s ago`;
  if (secs < 3600) return `${Math.floor(secs / 60)}m ago`;
  if (secs < 86400) return `${Math.floor(secs / 3600)}h ago`;
  return `${Math.floor(secs / 86400)}d ago`;
}

/* ── colour helpers ─────────────────────────────────────── */
const SC = {
  critical: { bg: 'bg-red-500/10',    border: 'border-red-500/40',    text: 'text-red-400',    badge: 'bg-red-500/20 border-red-500/40 text-red-400',    dot: 'bg-red-500' },
  high:     { bg: 'bg-orange-500/10', border: 'border-orange-500/40', text: 'text-orange-400', badge: 'bg-orange-500/20 border-orange-500/40 text-orange-400', dot: 'bg-orange-500' },
  medium:   { bg: 'bg-yellow-500/10', border: 'border-yellow-500/40', text: 'text-yellow-400', badge: 'bg-yellow-500/20 border-yellow-500/40 text-yellow-400', dot: 'bg-yellow-500' },
  low:      { bg: 'bg-blue-500/10',   border: 'border-blue-500/40',   text: 'text-blue-400',   badge: 'bg-blue-500/20 border-blue-500/40 text-blue-400',   dot: 'bg-blue-500'  },
};
const getSC = (t) => SC[t] || SC.low;

const statusBadge = (s) => ({
  active:       'bg-red-500/15 border-red-500/30 text-red-400',
  acknowledged: 'bg-yellow-500/15 border-yellow-500/30 text-yellow-400',
  resolved:     'bg-green-500/15 border-green-500/30 text-green-400',
})[s] || 'bg-slate-500/15 border-slate-500/30 text-slate-400';

const SeverityIcon = ({ type, size = 'w-4 h-4' }) => {
  const c = getSC(type);
  if (type === 'critical') return <XCircle   className={`${size} ${c.text}`} />;
  if (type === 'high')     return <AlertTriangle className={`${size} ${c.text}`} />;
  if (type === 'medium')   return <AlertCircle  className={`${size} ${c.text}`} />;
  return <Info className={`${size} ${c.text}`} />;
};

const Card = ({ children, className = '' }) => (
  <div className={`bg-[#1E293B] border border-[#334155] rounded-xl ${className}`}>{children}</div>
);

const SENSOR_ICONS = { temperature: ThermometerSun, vibration: Activity, current: Zap, pressure: Wind, rpm: Cpu };

/* ── Alert Detail Panel ──────────────────────────────────── */
function AlertDetail({ alert, onBack, onAcknowledge, onResolve }) {
  const [rca,    setRca]    = useState(null);
  const [preds,  setPreds]  = useState(null);
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const sc = getSC(alert.alert_type);

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      const [r, p, h] = await Promise.all([
        post(`/api/rca/analyze`, {
          equipment: alert.equipment_name,
          issue: alert.message,
          severity: alert.alert_type,
          temperature: alert.sensor_readings?.temperature,
          vibration:   alert.sensor_readings?.vibration,
          current:     alert.sensor_readings?.current,
          pressure:    alert.sensor_readings?.pressure,
        }),
        get(`/api/prediction/risk/${encodeURIComponent(alert.equipment_name)}`),
        get(`/api/maintenance-logs/?equipment_name=${encodeURIComponent(alert.equipment_name)}&limit=5`),
      ]);
      setRca(r);
      setPreds(p);
      setHistory(Array.isArray(h) ? h : []);
      setLoading(false);
    };
    load();
  }, [alert]);

  return (
    <div className="space-y-5">
      <div className="flex items-center gap-3">
        <button onClick={onBack} className="flex items-center gap-1 text-slate-400 hover:text-white text-sm transition-colors">
          <ChevronLeft className="w-4 h-4" /> All Alerts
        </button>
        <span className="text-slate-600">/</span>
        <span className="text-white font-medium">{alert.equipment_name}</span>
      </div>

      {/* Alert header */}
      <Card className={`p-5 border-l-4 ${sc.border.replace('border-', 'border-l-')}`}>
        <div className="flex items-start justify-between flex-wrap gap-4">
          <div className="flex items-center gap-3">
            <div className={`w-12 h-12 rounded-xl ${sc.bg} border ${sc.border} flex items-center justify-center flex-shrink-0`}>
              <SeverityIcon type={alert.alert_type} size="w-6 h-6" />
            </div>
            <div>
              <h2 className="text-xl font-heading font-bold text-white">{alert.message}</h2>
              <div className="flex items-center gap-3 mt-1 flex-wrap text-sm">
                <span className={`font-semibold ${sc.text}`}>{alert.equipment_name}</span>
                <span className="text-slate-600">·</span>
                <span className={`px-2 py-0.5 rounded border text-xs font-medium ${sc.badge}`}>{alert.alert_type?.toUpperCase()}</span>
                <span className={`px-2 py-0.5 rounded border text-xs ${statusBadge(alert.status)}`}>{alert.status}</span>
                <span className="text-slate-400 text-xs">{fmtDateTime(alert.timestamp)}</span>
              </div>
            </div>
          </div>
          <div className="flex gap-2">
            {alert.status === 'active' && (
              <button onClick={() => onAcknowledge(alert.alert_id)}
                className="flex items-center gap-1.5 px-3 py-2 bg-yellow-500/10 border border-yellow-500/30 text-yellow-400 hover:bg-yellow-500/20 rounded-lg text-sm transition-colors">
                <Check className="w-4 h-4" /> Acknowledge
              </button>
            )}
            {alert.status !== 'resolved' && (
              <button onClick={() => onResolve(alert.alert_id)}
                className="flex items-center gap-1.5 px-3 py-2 bg-green-500/10 border border-green-500/30 text-green-400 hover:bg-green-500/20 rounded-lg text-sm transition-colors">
                <CheckCircle className="w-4 h-4" /> Resolve
              </button>
            )}
          </div>
        </div>

        {/* Sensor readings */}
        {alert.sensor_readings && Object.keys(alert.sensor_readings).length > 0 && (
          <div className="grid grid-cols-2 md:grid-cols-5 gap-3 mt-5 pt-5 border-t border-[#334155]">
            {Object.entries(alert.sensor_readings).map(([key, val]) => {
              if (val == null) return null;
              const Icon = SENSOR_ICONS[key] || Gauge;
              return (
                <div key={key} className="bg-[#0F1419] rounded-lg p-3 border border-[#334155]">
                  <div className="flex items-center gap-1.5 mb-1">
                    <Icon className={`w-3.5 h-3.5 ${sc.text}`} />
                    <span className="text-[10px] text-slate-400 capitalize">{key}</span>
                  </div>
                  <div className={`text-lg font-mono font-bold ${sc.text}`}>{val}</div>
                </div>
              );
            })}
          </div>
        )}
      </Card>

      {loading ? (
        <div className="flex items-center justify-center py-12">
          <div className="w-8 h-8 border-2 border-orange-500 border-t-transparent rounded-full animate-spin" />
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
          {/* Root Cause Analysis */}
          {rca && (
            <Card className="p-5">
              <h3 className="font-heading font-semibold text-white mb-4 flex items-center gap-2">
                <Brain className="w-4 h-4 text-orange-400" /> AI Root Cause Analysis
              </h3>
              <div className="space-y-3">
                <div className="p-3 bg-[#0F1419] rounded-lg border border-red-500/20">
                  <div className="text-xs text-slate-400 mb-1">Primary Cause</div>
                  <div className="text-white font-semibold">{rca.primary_cause?.cause || '—'}</div>
                  <div className="text-xs text-orange-400 mt-1">
                    Confidence: {rca.primary_cause?.confidence?.toFixed(0)}% · {rca.primary_cause?.confidence_level}
                  </div>
                </div>
                {rca.contributing_factors?.length > 0 && (
                  <div>
                    <div className="text-xs text-slate-400 mb-2">Contributing Factors</div>
                    {rca.contributing_factors.map((f, i) => (
                      <div key={i} className="flex items-center gap-2 text-xs text-slate-300 py-1">
                        <span className="w-1.5 h-1.5 rounded-full bg-orange-400 flex-shrink-0" /> {f}
                      </div>
                    ))}
                  </div>
                )}
                {rca.investigation_steps?.length > 0 && (
                  <div>
                    <div className="text-xs text-slate-400 mb-2">Investigation Steps</div>
                    {rca.investigation_steps.slice(0, 4).map((s, i) => (
                      <div key={i} className="text-xs text-slate-300 py-1 border-b border-[#334155] last:border-0">{s}</div>
                    ))}
                  </div>
                )}
              </div>
            </Card>
          )}

          {/* AI Recommendations */}
          {rca?.recommended_actions && (
            <Card className="p-5">
              <h3 className="font-heading font-semibold text-white mb-4 flex items-center gap-2">
                <Wrench className="w-4 h-4 text-green-400" /> Recommended Actions
              </h3>
              <div className="space-y-2">
                {rca.recommended_actions.map((action, i) => (
                  <div key={i} className="flex items-start gap-2 p-2.5 bg-green-500/5 border border-green-500/20 rounded-lg">
                    <span className="text-green-400 font-mono text-xs mt-0.5 flex-shrink-0">{i + 1}.</span>
                    <span className="text-xs text-slate-300">{action}</span>
                  </div>
                ))}
              </div>
              {preds && (
                <div className="mt-4 pt-4 border-t border-[#334155] space-y-2">
                  <div className="text-xs text-slate-400 mb-2">Risk Assessment</div>
                  <div className="grid grid-cols-3 gap-2">
                    {[
                      { label: 'Risk Score',   val: preds.risk_score || '—',         color: 'text-orange-400' },
                      { label: 'Fail Prob',    val: preds.failure_probability ? (preds.failure_probability * 100).toFixed(0) + '%' : '—', color: 'text-red-400' },
                      { label: 'RUL (days)',   val: preds.rul_days || '—',            color: 'text-blue-400' },
                    ].map(({ label, val, color }) => (
                      <div key={label} className="bg-[#0F1419] rounded-lg p-2 border border-[#334155] text-center">
                        <div className={`text-sm font-bold font-mono ${color}`}>{val}</div>
                        <div className="text-[10px] text-slate-500 mt-0.5">{label}</div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </Card>
          )}

          {/* Maintenance History */}
          <Card className="p-5 lg:col-span-2">
            <h3 className="font-heading font-semibold text-white mb-4 flex items-center gap-2">
              <Clock className="w-4 h-4 text-blue-400" /> Recent Maintenance History
            </h3>
            {history.length === 0 ? (
              <p className="text-slate-500 text-sm">No maintenance records found</p>
            ) : (
              <div className="space-y-2">
                {history.map(log => (
                  <div key={log.log_id} className="flex items-start gap-3 p-3 bg-[#0F1419] rounded-lg border border-[#334155]">
                    <div className={`w-2 h-2 rounded-full mt-1.5 flex-shrink-0 ${
                      log.severity === 'critical' ? 'bg-red-500' :
                      log.severity === 'high'     ? 'bg-orange-500' :
                      log.severity === 'medium'   ? 'bg-yellow-500' : 'bg-blue-500'
                    }`} />
                    <div className="flex-1">
                      <div className="text-xs text-white font-medium">{log.issue}</div>
                      {log.action_taken && <div className="text-[11px] text-slate-400 mt-0.5">Action: {log.action_taken}</div>}
                    </div>
                    <div className="text-right text-xs text-slate-500 flex-shrink-0">
                      <div>{log.maintenance_date}</div>
                      {log.technician && <div>{log.technician}</div>}
                    </div>
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

/* ═══════════════════════════════════════════════════════════
   MAIN ALERT CENTER PAGE
═══════════════════════════════════════════════════════════ */
export default function AlertCenter() {
  const [alerts,      setAlerts]      = useState([]);
  const [summary,     setSummary]     = useState(null);
  const [loading,     setLoading]     = useState(true);
  const [selectedAlert, setSelectedAlert] = useState(null);
  const [filterSev,   setFilterSev]   = useState('');
  const [filterStatus,setFilterStatus]= useState('');
  const [filterEq,    setFilterEq]    = useState('');
  const [search,      setSearch]      = useState('');
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [lastUpdate,  setLastUpdate]  = useState(null);
  const [tick,        setTick]        = useState(0);  // forces re-render for "X ago" labels
  const timerRef = useRef(null);
  const tickRef  = useRef(null);

  // 1-second ticker to keep relative timestamps fresh
  useEffect(() => {
    tickRef.current = setInterval(() => setTick(t => t + 1), 1000);
    return () => clearInterval(tickRef.current);
  }, []);

  const load = useCallback(async () => {
    // Trigger fresh sensor simulation so new threshold alerts get created
    await post('/api/sensor-data/simulate-all', {});
    const [al, sum] = await Promise.all([
      get('/api/alerts?limit=200'),
      get('/api/alerts/summary'),
    ]);
    if (al?.alerts) setAlerts(al.alerts);
    if (sum)        setSummary(sum);
    setLastUpdate(new Date());
    setLoading(false);
  }, []);

  useEffect(() => {
    load();
    if (autoRefresh) { timerRef.current = setInterval(load, 3000); }   // 3 seconds
    return () => clearInterval(timerRef.current);
  }, [load, autoRefresh]);

  const acknowledge = async (id) => {
    await post(`/api/alerts/${id}/acknowledge`, {});
    load();
  };
  const resolve = async (id) => {
    await post(`/api/alerts/${id}/resolve`, {});
    load();
  };

  // Filtered alerts
  const filtered = alerts.filter(a => {
    if (filterSev    && a.alert_type !== filterSev)           return false;
    if (filterStatus && a.status     !== filterStatus)        return false;
    if (filterEq     && !a.equipment_name.toLowerCase().includes(filterEq.toLowerCase())) return false;
    if (search       && !a.message.toLowerCase().includes(search.toLowerCase()) &&
                        !a.equipment_name.toLowerCase().includes(search.toLowerCase())) return false;
    return true;
  });

  const criticals = alerts.filter(a => a.alert_type === 'critical' && a.status === 'active');

  // Analytics data
  const bySeverity = ['critical','high','medium','low'].map(s => ({
    name: s, count: alerts.filter(a => a.alert_type === s).length
  }));
  const byEquipment = Object.entries(
    alerts.reduce((acc, a) => { acc[a.equipment_name] = (acc[a.equipment_name] || 0) + 1; return acc; }, {})
  ).map(([name, count]) => ({ name: name.split(' ').slice(-1)[0], count })).slice(0, 5);
  const PIE_COLORS = ['#EF4444','#F97316','#FBBF24','#3B82F6'];

  if (selectedAlert) {
    return (
      <div className="p-6">
        <AlertDetail
          alert={selectedAlert}
          onBack={() => setSelectedAlert(null)}
          onAcknowledge={async (id) => { await acknowledge(id); setSelectedAlert(prev => ({ ...prev, status: 'acknowledged' })); }}
          onResolve={async (id)      => { await resolve(id);     setSelectedAlert(prev => ({ ...prev, status: 'resolved'     })); }}
        />
      </div>
    );
  }

  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-2xl font-heading font-bold text-white flex items-center gap-2">
            <Bell className="w-6 h-6 text-orange-500" /> Alert Center
          </h1>
          <p className="text-slate-400 text-sm mt-0.5 flex items-center gap-2">
            Industrial incident monitoring
            {lastUpdate && (
              <span className="flex items-center gap-1 text-green-400 text-xs">
                <span className="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse inline-block" />
                Live · {lastUpdate.toLocaleTimeString()}
              </span>
            )}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button onClick={() => setAutoRefresh(a => !a)}
            className={`flex items-center gap-1.5 px-3 py-2 border text-sm rounded-lg transition-all ${
              autoRefresh ? 'bg-green-500/10 border-green-500/30 text-green-400' : 'bg-[#1E293B] border-[#334155] text-slate-400'
            }`}>
            <Activity className="w-4 h-4" /> {autoRefresh ? 'Live' : 'Paused'}
          </button>
          <button onClick={load} className="p-2 bg-[#1E293B] border border-[#334155] hover:border-orange-500/40 text-slate-400 hover:text-white rounded-lg transition-all">
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-6 gap-3">
        {[
          { label: 'Total Alerts',   val: summary?.total    ?? 0, color: 'text-white',     bg: 'bg-slate-500/10 border-slate-500/20' },
          { label: 'Critical',       val: summary?.by_type?.critical ?? 0, color: 'text-red-400',  bg: 'bg-red-500/10 border-red-500/20' },
          { label: 'High',           val: summary?.by_type?.high     ?? 0, color: 'text-orange-400',bg: 'bg-orange-500/10 border-orange-500/20' },
          { label: 'Medium',         val: summary?.by_type?.medium   ?? 0, color: 'text-yellow-400',bg: 'bg-yellow-500/10 border-yellow-500/20' },
          { label: 'Low',            val: summary?.by_type?.low      ?? 0, color: 'text-blue-400', bg: 'bg-blue-500/10 border-blue-500/20' },
          { label: 'Active',         val: summary?.active   ?? 0, color: 'text-green-400', bg: 'bg-green-500/10 border-green-500/20' },
        ].map(({ label, val, color, bg }) => (
          <div key={label} className={`rounded-xl border p-3 text-center ${bg}`}>
            <div className={`text-2xl font-heading font-bold ${color}`}>{val}</div>
            <div className="text-[10px] text-slate-400 mt-1">{label}</div>
          </div>
        ))}
      </div>

      {/* Critical alerts banner */}
      {criticals.length > 0 && (
        <Card className="p-4 border-red-500/30 bg-red-500/5">
          <div className="flex items-center gap-2 mb-3">
            <XCircle className="w-5 h-5 text-red-400" />
            <span className="font-heading font-semibold text-red-400">
              CRITICAL ALERTS — Immediate Action Required ({criticals.length})
            </span>
            <span className="ml-auto w-2 h-2 rounded-full bg-red-500 animate-pulse" />
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-2">
            {criticals.map((a, i) => (
              <button key={i} onClick={() => setSelectedAlert(a)}
                className="flex items-center gap-3 p-3 bg-red-500/10 border border-red-500/30 rounded-lg hover:bg-red-500/20 transition-all text-left">
                <XCircle className="w-4 h-4 text-red-400 flex-shrink-0" />
                <div className="min-w-0">
                  <div className="text-xs font-semibold text-white truncate">{a.equipment_name}</div>
                  <div className="text-[10px] text-red-300 truncate">{a.message}</div>
                  <div className="text-[10px] text-slate-500 mt-0.5">{fmtTime(a.timestamp)} · {fmtAgo(a.timestamp)}</div>
                </div>
                <ChevronRight className="w-3 h-3 text-red-400 flex-shrink-0 ml-auto" />
              </button>
            ))}
          </div>
        </Card>
      )}

      {/* Filters */}
      <div className="flex flex-wrap gap-3">
        <div className="relative flex-1 min-w-[180px] max-w-xs">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
          <input value={search} onChange={e => setSearch(e.target.value)}
            placeholder="Search alerts..."
            className="input-industrial pl-9 text-sm" />
        </div>
        <select value={filterSev} onChange={e => setFilterSev(e.target.value)} className="select-industrial text-sm w-32">
          <option value="">All Severity</option>
          {['critical','high','medium','low'].map(s => <option key={s} value={s}>{s.charAt(0).toUpperCase()+s.slice(1)}</option>)}
        </select>
        <select value={filterStatus} onChange={e => setFilterStatus(e.target.value)} className="select-industrial text-sm w-36">
          <option value="">All Status</option>
          {['active','acknowledged','resolved'].map(s => <option key={s} value={s}>{s.charAt(0).toUpperCase()+s.slice(1)}</option>)}
        </select>
        <input value={filterEq} onChange={e => setFilterEq(e.target.value)}
          placeholder="Filter equipment..."
          className="input-industrial text-sm w-44" />
        {(filterSev || filterStatus || filterEq || search) && (
          <button onClick={() => { setFilterSev(''); setFilterStatus(''); setFilterEq(''); setSearch(''); }}
            className="px-3 py-2 bg-[#1E293B] border border-[#334155] hover:border-red-500/40 text-slate-400 hover:text-red-400 rounded-lg text-sm transition-colors flex items-center gap-1">
            <X className="w-3.5 h-3.5" /> Clear
          </button>
        )}
        <span className="text-xs text-slate-500 self-center ml-auto">{filtered.length} alerts</span>
      </div>

      {/* Alert Table */}
      <Card className="overflow-hidden">
        {loading ? (
          <div className="flex items-center justify-center py-16">
            <div className="w-8 h-8 border-2 border-orange-500 border-t-transparent rounded-full animate-spin" />
          </div>
        ) : filtered.length === 0 ? (
          <div className="text-center py-16">
            <CheckCircle className="w-12 h-12 text-green-400 mx-auto mb-3" />
            <p className="text-slate-400">No alerts found</p>
          </div>
        ) : (
          <table className="industrial-table">
            <thead>
              <tr>
                <th>Severity</th>
                <th>Equipment</th>
                <th>Alert</th>
                <th>Source</th>
                <th>Status</th>
                <th>Time</th>
                <th className="text-right">Actions</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((a, i) => {
                const sc = getSC(a.alert_type);
                return (
                  <tr key={a.alert_id || i} className={`cursor-pointer ${a.alert_type === 'critical' ? 'bg-red-500/3' : ''}`}
                    onClick={() => setSelectedAlert(a)}>
                    <td>
                      <div className="flex items-center gap-2">
                        <span className={`w-2 h-2 rounded-full flex-shrink-0 ${sc.dot} ${a.status === 'active' ? 'animate-pulse' : ''}`} />
                        <span className={`text-xs px-2 py-0.5 rounded border font-medium ${sc.badge}`}>
                          {a.alert_type?.toUpperCase()}
                        </span>
                      </div>
                    </td>
                    <td className="font-medium">{a.equipment_name}</td>
                    <td className="text-slate-300 max-w-[220px]">
                      <span className="truncate block">{a.message}</span>
                    </td>
                    <td className="text-slate-400 text-xs capitalize">{a.source || 'threshold'}</td>
                    <td>
                      <span className={`text-xs px-2 py-0.5 rounded border ${statusBadge(a.status)}`}>
                        {a.status}
                      </span>
                    </td>
                    <td className="text-slate-400 text-xs font-mono whitespace-nowrap">
                      <div>{fmtTime(a.timestamp)}</div>
                      <div className="text-slate-600 text-[10px]">{fmtAgo(a.timestamp)}</div>
                    </td>
                    <td className="text-right" onClick={e => e.stopPropagation()}>
                      <div className="flex items-center justify-end gap-1">
                        <button onClick={() => setSelectedAlert(a)}
                          className="p-1.5 text-blue-400 hover:bg-blue-500/20 rounded transition-colors" title="View">
                          <Eye className="w-3.5 h-3.5" />
                        </button>
                        {a.status === 'active' && (
                          <button onClick={() => acknowledge(a.alert_id)}
                            className="p-1.5 text-yellow-400 hover:bg-yellow-500/20 rounded transition-colors" title="Acknowledge">
                            <Check className="w-3.5 h-3.5" />
                          </button>
                        )}
                        {a.status !== 'resolved' && (
                          <button onClick={() => resolve(a.alert_id)}
                            className="p-1.5 text-green-400 hover:bg-green-500/20 rounded transition-colors" title="Resolve">
                            <CheckCircle className="w-3.5 h-3.5" />
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </Card>

      {/* Analytics */}
      {alerts.length > 0 && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card className="p-4">
            <h3 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
              <Shield className="w-4 h-4 text-orange-400" /> Alerts by Severity
            </h3>
            <ResponsiveContainer width="100%" height={180}>
              <BarChart data={bySeverity} margin={{ left: -10 }}>
                <XAxis dataKey="name" tick={{ fontSize: 11, fill: '#94A3B8' }} />
                <YAxis tick={{ fontSize: 11, fill: '#64748B' }} />
                <Tooltip contentStyle={{ background: '#1E293B', border: '1px solid #334155', fontSize: 11 }} />
                <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                  {bySeverity.map((_, i) => (
                    <Cell key={i} fill={['#EF4444','#F97316','#FBBF24','#3B82F6'][i]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </Card>

          <Card className="p-4">
            <h3 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
              <Activity className="w-4 h-4 text-orange-400" /> Most Affected Equipment
            </h3>
            <ResponsiveContainer width="100%" height={180}>
              <BarChart data={byEquipment} layout="vertical" margin={{ left: 10, right: 20 }}>
                <XAxis type="number" tick={{ fontSize: 10, fill: '#64748B' }} />
                <YAxis type="category" dataKey="name" tick={{ fontSize: 10, fill: '#94A3B8' }} width={80} />
                <Tooltip contentStyle={{ background: '#1E293B', border: '1px solid #334155', fontSize: 11 }} />
                <Bar dataKey="count" fill="#F97316" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </Card>
        </div>
      )}
    </div>
  );
}
