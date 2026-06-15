import { useState, useEffect, useCallback, useRef } from 'react';
import {
  Activity, AlertTriangle, CheckCircle, XCircle,
  TrendingUp, TrendingDown, Minus, RefreshCw, Clock,
  ThermometerSun, Gauge, Zap, Wind, Cpu, Wifi, WifiOff,
  ChevronDown, ChevronUp
} from 'lucide-react';

const API = 'http://localhost:8000';

/* ── fetch helpers ──────────────────────────────────────── */
const get  = (url) => fetch(API + url).then(r => r.json()).catch(() => null);
const post = (url, b) => fetch(API + url, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: b ? JSON.stringify(b) : undefined,
}).then(r => r.json()).catch(() => null);

/* ── timestamp helpers ──────────────────────────────────── */
function fmtTime(ts) {
  if (!ts) return '—';
  const d = new Date(ts);
  return isNaN(d.getTime()) ? '—' : d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
}
function fmtAgo(ts) {
  if (!ts) return '';
  const d = new Date(ts);
  if (isNaN(d.getTime())) return '';
  const s = Math.floor((Date.now() - d.getTime()) / 1000);
  if (s < 5)    return 'just now';
  if (s < 60)   return `${s}s ago`;
  if (s < 3600) return `${Math.floor(s / 60)}m ago`;
  return `${Math.floor(s / 3600)}h ago`;
}

/* ── color helpers ──────────────────────────────────────── */
function healthColor(score) {
  if (score >= 85) return { text: 'text-green-400',  bg: 'bg-green-500/15',  border: 'border-green-500/40',  bar: 'bg-green-500',  ring: 'ring-green-500/30'  };
  if (score >= 60) return { text: 'text-yellow-400', bg: 'bg-yellow-500/15', border: 'border-yellow-500/40', bar: 'bg-yellow-500', ring: 'ring-yellow-500/30' };
  if (score >= 40) return { text: 'text-orange-400', bg: 'bg-orange-500/15', border: 'border-orange-500/40', bar: 'bg-orange-500', ring: 'ring-orange-500/30' };
  return             { text: 'text-red-400',    bg: 'bg-red-500/15',    border: 'border-red-500/40',    bar: 'bg-red-500',    ring: 'ring-red-500/30'    };
}
function sensorColor(status) {
  if (status === 'critical') return 'text-red-400 border-red-500/40 bg-red-500/10';
  if (status === 'warning')  return 'text-yellow-400 border-yellow-500/40 bg-yellow-500/10';
  return 'text-green-400 border-green-500/30 bg-green-500/5';
}
const SENSOR_ICONS = {
  temperature: ThermometerSun, vibration: Activity,
  current: Zap, pressure: Wind, rpm: Cpu,
};

/* ── Summary KPI card ───────────────────────────────────── */
function KpiCard({ label, value, color, bg, border, icon: Icon }) {
  return (
    <div className={`rounded-xl border p-4 ${bg} ${border}`}>
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs text-slate-400">{label}</span>
        {Icon && <Icon className={`w-4 h-4 ${color}`} />}
      </div>
      <div className={`text-3xl font-bold font-mono ${color}`}>{value}</div>
    </div>
  );
}

/* ── Health bar gauge ────────────────────────────────────── */
function HealthBar({ score }) {
  const c = healthColor(score);
  return (
    <div className="w-full">
      <div className="flex justify-between text-[10px] mb-1">
        <span className={c.text + ' font-bold font-mono'}>{score}%</span>
      </div>
      <div className="h-2 bg-[#0F1419] rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-700 ${c.bar}`}
          style={{ width: `${score}%` }}
        />
      </div>
    </div>
  );
}

/* ── Equipment card (expanded view) ─────────────────────── */
function EquipmentCard({ eq, expanded, onToggle }) {
  const c    = healthColor(eq.health_score);
  const crit = (eq.sensors || []).filter(s => s.status === 'critical');
  const warn = (eq.sensors || []).filter(s => s.status === 'warning');

  return (
    <div className={`rounded-xl border transition-all duration-300 ${c.border} ${c.bg}`}>
      {/* Header row */}
      <button
        className="w-full flex items-center gap-3 p-4 text-left"
        onClick={onToggle}
      >
        {/* Health ring badge */}
        <div className={`w-12 h-12 rounded-xl flex flex-col items-center justify-center flex-shrink-0 border ring-2 ${c.border} ${c.ring} bg-[#0F1419]`}>
          <span className={`text-sm font-bold font-mono leading-none ${c.text}`}>{eq.health_score}</span>
          <span className="text-[8px] text-slate-500 mt-0.5">%</span>
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-white font-semibold text-sm">{eq.equipment_name}</span>
            <span className={`text-[10px] px-2 py-0.5 rounded border font-medium ${c.bg} ${c.border} ${c.text}`}>
              {eq.health_status}
            </span>
            <span className={`text-[10px] px-2 py-0.5 rounded border ${
              eq.risk_level === 'Critical' ? 'bg-red-500/10 border-red-500/30 text-red-400'
              : eq.risk_level === 'High'   ? 'bg-orange-500/10 border-orange-500/30 text-orange-400'
              : eq.risk_level === 'Medium' ? 'bg-yellow-500/10 border-yellow-500/30 text-yellow-400'
              : 'bg-green-500/10 border-green-500/30 text-green-400'
            }`}>
              {eq.risk_level} Risk
            </span>
            {crit.length > 0 && (
              <span className="text-[10px] px-2 py-0.5 rounded bg-red-500/20 border border-red-500/40 text-red-400 animate-pulse">
                ⚠ {crit.length} critical
              </span>
            )}
            {warn.length > 0 && crit.length === 0 && (
              <span className="text-[10px] px-2 py-0.5 rounded bg-yellow-500/20 border border-yellow-500/40 text-yellow-400">
                ⚡ {warn.length} warning
              </span>
            )}
          </div>
          <HealthBar score={eq.health_score} />
        </div>

        <div className="flex flex-col items-end gap-1 flex-shrink-0 ml-2">
          <span className="text-[10px] text-slate-500 font-mono">{fmtTime(eq.last_updated)}</span>
          <span className="text-[9px] text-slate-600">{fmtAgo(eq.last_updated)}</span>
          {expanded
            ? <ChevronUp className="w-4 h-4 text-slate-500 mt-1" />
            : <ChevronDown className="w-4 h-4 text-slate-500 mt-1" />}
        </div>
      </button>

      {/* Expanded sensor detail */}
      {expanded && (
        <div className="px-4 pb-4 border-t border-[#334155] pt-3">
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-2">
            {(eq.sensors || []).map((s, i) => {
              const Icon = SENSOR_ICONS[s.sensor_type] || Gauge;
              const cls  = sensorColor(s.status);
              return (
                <div key={i} className={`rounded-lg border p-2.5 ${cls}`}>
                  <div className="flex items-center gap-1.5 mb-1">
                    <Icon className="w-3 h-3 flex-shrink-0" />
                    <span className="text-[10px] uppercase font-medium">{s.sensor_type}</span>
                  </div>
                  <div className="text-base font-bold font-mono">{Number(s.value).toFixed(1)}</div>
                  <div className="text-[9px] opacity-70">{s.unit}</div>
                  <div className="flex items-center justify-between mt-1">
                    <span className="text-[9px] opacity-60">norm: {s.normal_range}</span>
                    <span className={`text-[9px] px-1 rounded ${
                      s.status === 'critical' ? 'bg-red-500/20' : s.status === 'warning' ? 'bg-yellow-500/20' : 'bg-green-500/20'
                    }`}>{s.status}</span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════
   MAIN PAGE
═══════════════════════════════════════════════════════════ */
export default function EquipmentHealth() {
  const [equipment,   setEquipment]   = useState([]);   // live-status rows
  const [loading,     setLoading]     = useState(true);
  const [lastUpdate,  setLastUpdate]  = useState(null);
  const [liveOnline,  setLiveOnline]  = useState(false);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [expanded,    setExpanded]    = useState({});   // { equipmentName: bool }
  const [filterRisk,  setFilterRisk]  = useState('');
  const [tick,        setTick]        = useState(0);    // 1-second ticker for "X ago"

  // 1-second ticker keeps relative timestamps fresh without re-fetching
  useEffect(() => {
    const id = setInterval(() => setTick(t => t + 1), 1000);
    return () => clearInterval(id);
  }, []);

  // ── Main poll: simulate → fetch live-status ──────────────
  const poll = useCallback(async () => {
    // 1. Generate fresh sensor readings
    await post('/api/sensor-data/simulate-all', {});
    // 2. Fetch health status computed from those fresh readings
    const data = await get('/api/sensor-data/live-status');
    if (data?.equipment) {
      setEquipment(data.equipment);
      setLiveOnline(true);
    } else {
      setLiveOnline(false);
    }
    setLastUpdate(new Date());
    setLoading(false);
  }, []);

  useEffect(() => {
    if (!autoRefresh) return;
    poll();
    const id = setInterval(poll, 3000);
    return () => clearInterval(id);
  }, [autoRefresh, poll]);

  const toggleExpand = (name) =>
    setExpanded(prev => ({ ...prev, [name]: !prev[name] }));

  // ── Filtered list ─────────────────────────────────────────
  const filtered = equipment.filter(eq => {
    if (!filterRisk) return true;
    return eq.risk_level?.toLowerCase() === filterRisk.toLowerCase();
  });

  // ── Aggregate KPIs ────────────────────────────────────────
  const total    = equipment.length;
  const healthy  = equipment.filter(e => e.health_score >= 85).length;
  const warning  = equipment.filter(e => e.health_score >= 60 && e.health_score < 85).length;
  const poor     = equipment.filter(e => e.health_score >= 40 && e.health_score < 60).length;
  const critical = equipment.filter(e => e.health_score < 40).length;
  const avgScore = total > 0 ? Math.round(equipment.reduce((s, e) => s + e.health_score, 0) / total) : 0;
  const critSensors = equipment.flatMap(e => (e.sensors || []).filter(s => s.status === 'critical'));

  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-2xl font-heading font-bold text-white flex items-center gap-2">
            <Activity className="w-6 h-6 text-orange-500" /> Equipment Health
          </h1>
          <p className="text-slate-400 text-sm mt-0.5 flex items-center gap-2">
            Real-time sensor health monitoring
            {liveOnline ? (
              <span className="flex items-center gap-1 text-green-400 text-xs">
                <Wifi className="w-3 h-3" />
                Live · {lastUpdate ? lastUpdate.toLocaleTimeString() : ''}
              </span>
            ) : (
              <span className="flex items-center gap-1 text-slate-500 text-xs">
                <WifiOff className="w-3 h-3" /> Connecting...
              </span>
            )}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setAutoRefresh(v => !v)}
            className={`flex items-center gap-1.5 px-3 py-2 text-sm rounded-lg border transition-colors ${
              autoRefresh
                ? 'bg-green-500/10 border-green-500/30 text-green-400'
                : 'bg-[#1E293B] border-[#334155] text-slate-400'
            }`}
          >
            <Activity className="w-4 h-4" />
            {autoRefresh ? 'Live ON' : 'Live OFF'}
          </button>
          <button
            onClick={poll}
            className="p-2 bg-[#1E293B] border border-[#334155] hover:border-orange-500/40 text-slate-400 hover:text-white rounded-lg transition-all"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* KPI cards */}
      <div className="grid grid-cols-2 sm:grid-cols-3 xl:grid-cols-6 gap-3">
        <KpiCard label="Avg Health"    value={avgScore + '%'} color="text-white"      bg="bg-slate-500/10"  border="border-slate-500/20" />
        <KpiCard label="Total"         value={total}          color="text-white"      bg="bg-slate-500/10"  border="border-slate-500/20" icon={Activity} />
        <KpiCard label="Healthy"       value={healthy}        color="text-green-400"  bg="bg-green-500/10"  border="border-green-500/20"  icon={CheckCircle} />
        <KpiCard label="Warning"       value={warning}        color="text-yellow-400" bg="bg-yellow-500/10" border="border-yellow-500/20" icon={AlertTriangle} />
        <KpiCard label="Poor"          value={poor}           color="text-orange-400" bg="bg-orange-500/10" border="border-orange-500/20" icon={AlertTriangle} />
        <KpiCard label="Critical"      value={critical}       color="text-red-400"    bg="bg-red-500/10"    border="border-red-500/20"    icon={XCircle} />
      </div>

      {/* Critical sensor alerts strip */}
      {critSensors.length > 0 && (
        <div className="p-4 rounded-xl border border-red-500/30 bg-red-500/5">
          <div className="flex items-center gap-2 mb-3">
            <XCircle className="w-4 h-4 text-red-400" />
            <span className="text-sm font-semibold text-red-400">
              Critical Sensors — {critSensors.length} readings above threshold
            </span>
            <span className="ml-auto w-2 h-2 rounded-full bg-red-500 animate-pulse" />
          </div>
          <div className="flex flex-wrap gap-2">
            {critSensors.map((s, i) => {
              const Icon = SENSOR_ICONS[s.sensor_type] || Gauge;
              // Find parent equipment
              const eqName = equipment.find(e =>
                (e.sensors || []).some(x => x === s)
              )?.equipment_name || '';
              return (
                <div key={i} className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg border bg-red-500/10 border-red-500/30 text-red-400 text-xs">
                  <Icon className="w-3 h-3 flex-shrink-0" />
                  <span className="font-medium">{s.sensor_type}</span>
                  <span className="font-mono font-bold">{Number(s.value).toFixed(1)}{s.unit}</span>
                  {eqName && <span className="text-red-300/60 text-[10px]">({eqName.split(' ').slice(-1)[0]})</span>}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Filter bar */}
      <div className="flex items-center gap-2 flex-wrap">
        <span className="text-xs text-slate-400">Filter:</span>
        {[['', 'All'], ['Low', 'Healthy'], ['Medium', 'Warning'], ['High', 'Poor'], ['Critical', 'Critical']].map(([val, label]) => (
          <button
            key={val}
            onClick={() => setFilterRisk(val)}
            className={`px-3 py-1.5 text-xs rounded-lg border transition-all ${
              filterRisk === val
                ? val === ''        ? 'bg-orange-500 text-white border-orange-500'
                  : val === 'Low'   ? 'bg-green-500/20 border-green-500/40 text-green-400'
                  : val === 'Medium'? 'bg-yellow-500/20 border-yellow-500/40 text-yellow-400'
                  : val === 'High'  ? 'bg-orange-500/20 border-orange-500/40 text-orange-400'
                  : 'bg-red-500/20 border-red-500/40 text-red-400'
                : 'border-[#334155] text-slate-400 hover:text-white'
            }`}
          >
            {label}
          </button>
        ))}
        <span className="text-xs text-slate-500 ml-auto">{filtered.length} machines</span>
      </div>

      {/* Equipment cards */}
      {loading ? (
        <div className="flex items-center justify-center py-20">
          <div className="w-8 h-8 border-2 border-orange-500 border-t-transparent rounded-full animate-spin" />
        </div>
      ) : filtered.length === 0 ? (
        <div className="text-center py-20">
          <Activity className="w-12 h-12 text-slate-600 mx-auto mb-3" />
          <p className="text-slate-400">No equipment found. Add equipment and sensor data to see health status.</p>
        </div>
      ) : (
        <div className="space-y-2">
          {filtered.map((eq) => (
            <EquipmentCard
              key={eq.equipment_name}
              eq={eq}
              expanded={!!expanded[eq.equipment_name]}
              onToggle={() => toggleExpand(eq.equipment_name)}
            />
          ))}
        </div>
      )}

      {/* Legend */}
      <div className="flex items-center justify-center gap-6 text-xs text-slate-500 flex-wrap">
        {[
          { color: 'bg-green-500',  label: 'Healthy (85–100)' },
          { color: 'bg-yellow-500', label: 'Warning (60–84)' },
          { color: 'bg-orange-500', label: 'Poor (40–59)' },
          { color: 'bg-red-500',    label: 'Critical (0–39)' },
        ].map(({ color, label }) => (
          <div key={label} className="flex items-center gap-1.5">
            <span className={`w-2.5 h-2.5 rounded-full ${color}`} />
            {label}
          </div>
        ))}
        <span className="text-slate-600">· Updates every 3s</span>
      </div>
    </div>
  );
}
