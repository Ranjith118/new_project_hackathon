import { useState, useEffect, useCallback, useRef } from 'react';
import {
  Thermometer, Activity, Zap, Gauge, Radio,
  RefreshCw, Clock, TrendingUp, TrendingDown, Minus,
  Wifi, WifiOff, ChevronDown
} from 'lucide-react';
import {
  LineChart, Line, AreaChart, Area,
  XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Legend, ReferenceLine
} from 'recharts';

const API = 'http://localhost:8000';
const get  = (url) => fetch(API + url).then(r => r.json()).catch(() => null);
const post = (url, b) => fetch(API + url, {
  method: 'POST', headers: { 'Content-Type': 'application/json' },
  body: b ? JSON.stringify(b) : undefined,
}).then(r => r.json()).catch(() => null);

const POLL_MS = 3000;

/* ── Per-equipment sensor threshold profiles (mirrors backend) ─ */
const PROFILES = {
  'Rolling Mill Motor':   { temperature:[65,115,90,95,110], vibration:[0.5,5.0,1.8,2.8,4.0], current:[18,32,22,28,32],  pressure:[70,95,80,90,95],    rpm:[1400,2200,1500,2000,2200] },
  'Blast Furnace Fan':    { temperature:[50,95,72,85,93],   vibration:[0.5,4.5,1.5,3.0,4.5], current:[38,58,42,52,58],  pressure:[180,250,200,230,248],rpm:[940,1020,980,1010,1020] },
  'Cooling Pump A':       { temperature:[30,85,55,75,85],   vibration:[0.3,3.5,1.0,2.5,3.5], current:[20,35,27,30,35],  pressure:[30,55,42,50,54],    rpm:[1400,1800,1600,1750,1800] },
  'Main Compressor':      { temperature:[60,100,78,90,100], vibration:[0.5,4.0,1.6,2.8,4.0], current:[30,60,45,55,60],  pressure:[5,12,8,11,12],      rpm:[1450,1550,1500,1530,1550] },
  'Conveyor Belt System': { temperature:[20,60,35,50,60],   vibration:[0.2,2.5,0.8,2.0,2.5], current:[10,25,16,22,25],  pressure:[2,8,4,7,8],         rpm:[800,1200,1000,1150,1200]  },
};
const DEFAULT_PROFILE = {
  temperature:[40,100,70,90,100], vibration:[0.5,4.0,1.5,3.0,4.0],
  current:[15,35,22,30,35],       pressure:[2,10,6,9,10],
  rpm:[900,1800,1200,1700,1800],
};

/* ── Compute health score from sensor readings (same formula as backend live-status) ── */
function computeHealth(rdg, equipName) {
  const profile = PROFILES[equipName] || DEFAULT_PROFILE;
  const penalties = [];
  for (const [sensor, thresholds] of Object.entries(profile)) {
    const val = rdg[sensor];
    if (val == null) continue;
    const [,,, warn, crit] = thresholds;
    if (val >= crit)      penalties.push(40);
    else if (val >= warn) penalties.push(15);
    else                  penalties.push(0);
  }
  if (penalties.length === 0) return 100;
  return Math.max(0, Math.min(100, Math.round(100 - penalties.reduce((a, b) => a + b, 0) / penalties.length)));
}

/* ── Derive sensor status string ─────────────────────────── */
function sensorStatus(val, sensor, equipName) {
  if (val == null) return 'normal';
  const profile = PROFILES[equipName] || DEFAULT_PROFILE;
  const th = profile[sensor];
  if (!th) return 'normal';
  const [,,, warn, crit] = th;
  if (val >= crit) return 'critical';
  if (val >= warn) return 'warning';
  return 'normal';
}

/* ── Timestamp helpers ───────────────────────────────────── */
function fmtHM(ts) {
  if (!ts) return '';
  const d = new Date(ts);
  return isNaN(d.getTime()) ? '' : d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
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

/* ── Color helpers ───────────────────────────────────────── */
function statusColors(st) {
  if (st === 'critical') return { bg:'bg-red-500/20',    text:'text-red-400',    border:'border-red-500/30'    };
  if (st === 'warning')  return { bg:'bg-yellow-500/20', text:'text-yellow-400', border:'border-yellow-500/30' };
  return                        { bg:'bg-green-500/20',  text:'text-green-400',  border:'border-green-500/30'  };
}
function healthColors(score) {
  if (score >= 85) return '#22c55e';
  if (score >= 60) return '#eab308';
  if (score >= 40) return '#f97316';
  return '#ef4444';
}

/* ── Current reading card ────────────────────────────────── */
function SensorCard({ icon: Icon, label, value, unit, status, trend }) {
  const c = statusColors(status);
  const TI = trend === 'up' ? TrendingUp : trend === 'down' ? TrendingDown : Minus;
  const tColor = trend === 'up' ? 'text-red-400' : trend === 'down' ? 'text-green-400' : 'text-slate-500';
  return (
    <div className={`bg-[#1E293B] border rounded-xl p-4 ${c.border}`}>
      <div className="flex items-center gap-3 mb-3">
        <div className={`p-2 rounded-lg ${c.bg}`}>
          <Icon className={`w-5 h-5 ${c.text}`} />
        </div>
        <div>
          <p className="text-xs text-slate-400">{label}</p>
          <div className="flex items-center gap-2">
            <span className={`text-2xl font-bold font-mono ${c.text}`}>
              {value != null ? Number(value).toFixed(1) : '—'}
            </span>
            <span className="text-xs text-slate-500">{unit}</span>
            <TI className={`w-4 h-4 ${tColor}`} />
          </div>
        </div>
      </div>
      <span className={`text-[10px] px-2 py-0.5 rounded font-medium ${c.bg} ${c.text}`}>
        {status?.toUpperCase() || 'NORMAL'}
      </span>
    </div>
  );
}

/* ── Chart tooltip ───────────────────────────────────────── */
function ChartTip({ active, payload, label }) {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-[#0F1419] border border-[#334155] rounded-lg p-3 shadow-xl text-xs">
      <p className="text-slate-400 mb-2 font-mono">{label}</p>
      {payload.map((e, i) => (
        <div key={i} className="flex items-center gap-2">
          <span className="w-2.5 h-2.5 rounded-full flex-shrink-0" style={{ background: e.color }} />
          <span className="text-slate-300">{e.name}:</span>
          <span className="font-mono font-bold text-orange-400">{e.value != null ? Number(e.value).toFixed(2) : '—'}</span>
        </div>
      ))}
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════
   MAIN PAGE
═══════════════════════════════════════════════════════════ */
export default function SensorTrends() {
  const [liveEquip,    setLiveEquip]    = useState([]);    // from /api/sensor-data/live-status
  const [historyMap,   setHistoryMap]   = useState({});    // { equipName: [rows...] }
  const [loading,      setLoading]      = useState(true);
  const [selectedEq,   setSelectedEq]   = useState('');    // '' = first available
  const [lastUpdate,   setLastUpdate]   = useState(null);
  const [liveOnline,   setLiveOnline]   = useState(false);
  const [autoRefresh,  setAutoRefresh]  = useState(true);
  const [tick,         setTick]         = useState(0);

  // 1-second ticker for "X ago" labels
  useEffect(() => {
    const id = setInterval(() => setTick(t => t + 1), 1000);
    return () => clearInterval(id);
  }, []);

  // ── Poll: simulate → live-status → history for selected eq ──
  const poll = useCallback(async () => {
    // 1. Write fresh sensor data to DB
    await post('/api/sensor-data/simulate-all', {});

    // 2. Fetch live status (current readings for all equipment)
    const status = await get('/api/sensor-data/live-status');
    if (status?.equipment?.length > 0) {
      setLiveEquip(status.equipment);
      setLiveOnline(true);

      // Default to first (worst-health) equipment if none selected
      setSelectedEq(prev => prev || status.equipment[0]?.equipment_name || '');
    } else {
      setLiveOnline(false);
    }

    // 3. Fetch 1-hour history for selected equipment (or all)
    const eqList = status?.equipment?.map(e => e.equipment_name) || [];
    const histPromises = eqList.map(name =>
      get(`/api/sensor-data/history/${encodeURIComponent(name)}?hours=1`)
        .then(r => ({ name, readings: r?.readings || [] }))
    );
    const results = await Promise.all(histPromises);
    const map = {};
    for (const { name, readings } of results) {
      // Compute health_score for every history row client-side
      map[name] = readings.map(r => ({
        ...r,
        health_score: computeHealth(r, name),
      }));
    }
    setHistoryMap(map);
    setLastUpdate(new Date());
    setLoading(false);
  }, []);

  useEffect(() => {
    if (!autoRefresh) return;
    poll();
    const id = setInterval(poll, POLL_MS);
    return () => clearInterval(id);
  }, [autoRefresh, poll]);

  // ── Derive display data from selected equipment ──────────
  const liveRow    = liveEquip.find(e => e.equipment_name === selectedEq) || liveEquip[0];
  const eqName     = liveRow?.equipment_name || '';
  const liveSensors = liveRow?.sensors || [];

  // Helpers to get live value / status for a specific sensor key
  const lv = (key) => liveSensors.find(s => s.sensor_type === key)?.value ?? null;
  const ls = (key) => liveSensors.find(s => s.sensor_type === key)?.status ?? 'normal';

  // Trend from last 10 history rows
  const history = historyMap[eqName] || [];
  const calcTrend = (key) => {
    if (history.length < 10) return 'stable';
    const recent = history.slice(-5);
    const older  = history.slice(-10, -5);
    const avg = (arr) => arr.reduce((s, r) => s + (r[key] ?? 0), 0) / arr.length;
    const r = avg(recent), o = avg(older);
    if (r > o * 1.05) return 'up';
    if (r < o * 0.95) return 'down';
    return 'stable';
  };

  // Chart data — last 30 history points for selected equipment, formatted for recharts
  const chartData = history.slice(-60).map(r => ({
    time:         fmtHM(r.timestamp),
    temperature:  r.temperature,
    vibration:    r.vibration,
    current:      r.current,
    pressure:     r.pressure,
    rpm:          r.rpm != null ? r.rpm / 10 : null,   // scale so it fits in chart
    health_score: r.health_score,
  }));

  // Threshold reference lines for selected equipment
  const prof = PROFILES[eqName] || DEFAULT_PROFILE;

  const equipNames = liveEquip.map(e => e.equipment_name);

  // ── Chart config entries ─────────────────────────────────
  const charts = [
    {
      key: 'temperature', label: 'Temperature', unit: '°C',
      color: '#ef4444', gradId: 'gTemp',
      domain: [0, 150],
      warn: prof.temperature?.[3], crit: prof.temperature?.[4],
    },
    {
      key: 'vibration', label: 'Vibration', unit: 'mm/s',
      color: '#eab308', gradId: 'gVib',
      domain: [0, 6],
      warn: prof.vibration?.[3], crit: prof.vibration?.[4],
    },
    {
      key: 'current', label: 'Current', unit: 'A',
      color: '#3b82f6', gradId: 'gCurr',
      domain: [0, 70],
      warn: prof.current?.[3], crit: prof.current?.[4],
    },
    {
      key: 'pressure', label: 'Pressure', unit: 'bar/mbar',
      color: '#06b6d4', gradId: 'gPres',
      domain: [0, 300],
      warn: prof.pressure?.[3], crit: prof.pressure?.[4],
    },
  ];

  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-2xl font-heading font-bold text-white flex items-center gap-2">
            <Activity className="w-6 h-6 text-orange-500" /> Sensor Trends
          </h1>
          <p className="text-slate-400 text-sm mt-0.5 flex items-center gap-2">
            Real-time sensor monitoring &amp; historical trends
            {liveOnline ? (
              <span className="flex items-center gap-1 text-green-400 text-xs">
                <Wifi className="w-3 h-3" /> Live · {lastUpdate ? lastUpdate.toLocaleTimeString() : ''}
              </span>
            ) : (
              <span className="flex items-center gap-1 text-slate-500 text-xs">
                <WifiOff className="w-3 h-3" /> Connecting...
              </span>
            )}
          </p>
        </div>

        <div className="flex items-center gap-2 flex-wrap">
          {/* Equipment selector */}
          <select
            value={selectedEq}
            onChange={e => setSelectedEq(e.target.value)}
            className="bg-[#1E293B] border border-[#334155] text-white text-sm rounded-lg px-3 py-2 focus:outline-none focus:border-orange-500"
          >
            {equipNames.map(n => (
              <option key={n} value={n}>{n}</option>
            ))}
          </select>

          {/* Auto-refresh toggle */}
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

      {/* Current readings strip */}
      {loading ? (
        <div className="flex items-center justify-center py-16">
          <div className="w-8 h-8 border-2 border-orange-500 border-t-transparent rounded-full animate-spin" />
        </div>
      ) : (
        <>
          {eqName && (
            <div className="text-xs text-slate-500 flex items-center gap-2">
              <Clock className="w-3.5 h-3.5" />
              Showing: <span className="text-white font-medium">{eqName}</span>
              {liveRow?.last_updated && (
                <span>· {fmtHM(liveRow.last_updated)} ({fmtAgo(liveRow.last_updated)})</span>
              )}
            </div>
          )}

          <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
            <SensorCard icon={Thermometer} label="Temperature" value={lv('temperature')} unit="°C"     status={ls('temperature')} trend={calcTrend('temperature')} />
            <SensorCard icon={Activity}    label="Vibration"   value={lv('vibration')}   unit="mm/s"   status={ls('vibration')}   trend={calcTrend('vibration')}   />
            <SensorCard icon={Zap}         label="Current"     value={lv('current')}     unit="A"      status={ls('current')}     trend={calcTrend('current')}     />
            <SensorCard icon={Gauge}       label="Pressure"    value={lv('pressure')}    unit="bar"    status={ls('pressure')}    trend={calcTrend('pressure')}    />
            <SensorCard icon={Radio}       label="RPM"         value={lv('rpm')}         unit="rpm"    status={ls('rpm')}         trend={calcTrend('rpm')}         />
          </div>

          {/* Health score summary bar */}
          {liveRow && (
            <div className="bg-[#1E293B] border border-[#334155] rounded-xl p-4">
              <div className="flex items-center justify-between flex-wrap gap-3">
                <div className="flex items-center gap-3">
                  <div
                    className="w-14 h-14 rounded-xl flex flex-col items-center justify-center border"
                    style={{ borderColor: healthColors(liveRow.health_score) + '80', background: healthColors(liveRow.health_score) + '15' }}
                  >
                    <span className="text-xl font-bold font-mono" style={{ color: healthColors(liveRow.health_score) }}>{liveRow.health_score}</span>
                    <span className="text-[9px] text-slate-500">%</span>
                  </div>
                  <div>
                    <div className="text-white font-semibold">{liveRow.health_status}</div>
                    <div className="text-xs text-slate-400">{liveRow.risk_level} Risk · {liveRow.sensor_count} sensors monitored</div>
                  </div>
                </div>
                <div className="flex gap-2 flex-wrap">
                  {liveSensors.map((s, i) => (
                    <div key={i} className={`text-xs px-2 py-1 rounded border font-mono ${
                      s.status === 'critical' ? 'bg-red-500/10 border-red-500/30 text-red-400'
                      : s.status === 'warning' ? 'bg-yellow-500/10 border-yellow-500/30 text-yellow-400'
                      : 'bg-green-500/10 border-green-500/30 text-green-400'
                    }`}>
                      {s.sensor_type.slice(0,4).toUpperCase()} {Number(s.value).toFixed(1)}{s.unit}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* 4 sensor charts */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {charts.map(({ key, label, unit, color, gradId, domain, warn, crit }) => (
              <div key={key} className="bg-[#1E293B] border border-[#334155] rounded-xl p-4">
                <h3 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
                  <span className="w-3 h-3 rounded-full" style={{ background: color }} />
                  {label} Trend <span className="text-slate-500 text-xs font-normal ml-1">({unit})</span>
                  {chartData.length === 0 && <span className="text-slate-600 text-xs ml-auto">No data yet</span>}
                </h3>
                <div className="h-52">
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={chartData} margin={{ left: -10, right: 5 }}>
                      <defs>
                        <linearGradient id={gradId} x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%"  stopColor={color} stopOpacity={0.25} />
                          <stop offset="95%" stopColor={color} stopOpacity={0} />
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" stroke="#1E293B" />
                      <XAxis dataKey="time" stroke="#475569" fontSize={10} tick={{ fill: '#64748b' }} interval="preserveStartEnd" />
                      <YAxis stroke="#475569" fontSize={10} tick={{ fill: '#64748b' }} domain={domain} />
                      <Tooltip content={<ChartTip />} />
                      {warn != null && (
                        <ReferenceLine y={warn} stroke="#eab308" strokeDasharray="4 2" strokeOpacity={0.6}
                          label={{ value: 'WARN', position: 'insideTopRight', fill: '#eab308', fontSize: 9 }} />
                      )}
                      {crit != null && (
                        <ReferenceLine y={crit} stroke="#ef4444" strokeDasharray="4 2" strokeOpacity={0.6}
                          label={{ value: 'CRIT', position: 'insideTopRight', fill: '#ef4444', fontSize: 9 }} />
                      )}
                      <Area
                        type="monotone" dataKey={key}
                        stroke={color} fill={`url(#${gradId})`}
                        strokeWidth={2} dot={false}
                        name={`${label} (${unit})`}
                        connectNulls
                      />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              </div>
            ))}
          </div>

          {/* Health Score Trend — full width */}
          <div className="bg-[#1E293B] border border-[#334155] rounded-xl p-4">
            <h3 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
              <Activity className="w-4 h-4 text-green-400" />
              Health Score Trend
              <span className="text-slate-500 text-xs font-normal">(computed from sensor thresholds · last 1 hour)</span>
              {chartData.length === 0 && (
                <span className="text-slate-600 text-xs ml-auto">No history yet — will populate as sensors generate data</span>
              )}
            </h3>

            {chartData.length > 0 ? (
              <div className="h-56">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={chartData} margin={{ left: -10, right: 5 }}>
                    <defs>
                      <linearGradient id="gHealth" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%"  stopColor="#22c55e" stopOpacity={0.3} />
                        <stop offset="95%" stopColor="#22c55e" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="#1E293B" />
                    <XAxis dataKey="time" stroke="#475569" fontSize={10} tick={{ fill: '#64748b' }} interval="preserveStartEnd" />
                    <YAxis stroke="#475569" fontSize={10} tick={{ fill: '#64748b' }} domain={[0, 100]} />
                    <Tooltip content={<ChartTip />} />
                    {/* Threshold zones */}
                    <ReferenceLine y={85} stroke="#22c55e" strokeDasharray="4 2" strokeOpacity={0.4}
                      label={{ value: 'Healthy', position: 'insideTopLeft', fill: '#22c55e', fontSize: 9 }} />
                    <ReferenceLine y={60} stroke="#eab308" strokeDasharray="4 2" strokeOpacity={0.4}
                      label={{ value: 'Warning', position: 'insideTopLeft', fill: '#eab308', fontSize: 9 }} />
                    <ReferenceLine y={40} stroke="#f97316" strokeDasharray="4 2" strokeOpacity={0.4}
                      label={{ value: 'Poor', position: 'insideTopLeft', fill: '#f97316', fontSize: 9 }} />
                    <Area
                      type="monotone" dataKey="health_score"
                      stroke="#22c55e" fill="url(#gHealth)"
                      strokeWidth={2.5} dot={false}
                      name="Health Score (%)"
                      connectNulls
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            ) : (
              /* Empty state with a live "current health" display while history accumulates */
              <div className="h-56 flex flex-col items-center justify-center gap-4">
                <div className="text-center">
                  <div
                    className="text-5xl font-bold font-mono mb-1"
                    style={{ color: healthColors(liveRow?.health_score ?? 100) }}
                  >
                    {liveRow?.health_score ?? '—'}
                  </div>
                  <div className="text-sm text-slate-400">Current Health Score</div>
                  <div className="text-xs text-slate-600 mt-2">
                    Trend chart will populate as sensor history accumulates (≥2 readings)
                  </div>
                </div>
                <div className="flex gap-3 text-xs text-slate-600">
                  {[['#22c55e','Healthy 85–100'],['#eab308','Warning 60–84'],['#f97316','Poor 40–59'],['#ef4444','Critical 0–39']].map(([c,l]) => (
                    <span key={l} className="flex items-center gap-1"><span className="w-2 h-2 rounded-full" style={{background:c}} />{l}</span>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* RPM trend */}
          <div className="bg-[#1E293B] border border-[#334155] rounded-xl p-4">
            <h3 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
              <Radio className="w-4 h-4 text-purple-400" />
              RPM Trend
              <span className="text-slate-500 text-xs font-normal">(÷10 scaled)</span>
            </h3>
            <div className="h-40">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={chartData} margin={{ left: -10, right: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1E293B" />
                  <XAxis dataKey="time" stroke="#475569" fontSize={10} tick={{ fill: '#64748b' }} interval="preserveStartEnd" />
                  <YAxis stroke="#475569" fontSize={10} tick={{ fill: '#64748b' }} />
                  <Tooltip content={<ChartTip />} formatter={(v) => [v != null ? (v * 10).toFixed(0) + ' rpm' : '—', 'RPM']} />
                  <Line type="monotone" dataKey="rpm" stroke="#a855f7" strokeWidth={2} dot={false} name="RPM (÷10)" connectNulls />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* All-equipment health comparison */}
          {liveEquip.length > 1 && (
            <div className="bg-[#1E293B] border border-[#334155] rounded-xl p-4">
              <h3 className="text-sm font-semibold text-white mb-4">All Equipment Health Comparison</h3>
              <div className="space-y-3">
                {liveEquip.map((eq) => {
                  const c = healthColors(eq.health_score);
                  return (
                    <div key={eq.equipment_name} className="flex items-center gap-3">
                      <button
                        className="text-xs text-slate-300 hover:text-white w-44 text-left truncate flex-shrink-0 transition-colors"
                        onClick={() => setSelectedEq(eq.equipment_name)}
                      >
                        {eq.equipment_name === selectedEq ? '▶ ' : ''}{eq.equipment_name}
                      </button>
                      <div className="flex-1 h-4 bg-[#0F1419] rounded-full overflow-hidden">
                        <div
                          className="h-full rounded-full transition-all duration-700"
                          style={{ width: `${eq.health_score}%`, background: c }}
                        />
                      </div>
                      <span className="text-xs font-mono font-bold w-10 text-right flex-shrink-0" style={{ color: c }}>
                        {eq.health_score}%
                      </span>
                      <span className="text-[10px] text-slate-500 w-20 flex-shrink-0">{eq.health_status}</span>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
