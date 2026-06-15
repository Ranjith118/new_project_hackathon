import { useState, useEffect, useCallback, useRef } from 'react';
import {
  Activity, ThermometerSun, Gauge, Zap, Wind, Cpu,
  RefreshCw, AlertTriangle, CheckCircle, AlertCircle,
  Clock, ChevronLeft, Siren
} from 'lucide-react';
import {
  AreaChart, Area, XAxis, YAxis,
  CartesianGrid, Tooltip, ResponsiveContainer
} from 'recharts';

const API = 'http://localhost:8000/api/sensor-data';

const statusColor = (s) => ({ normal:'#10B981', warning:'#FBBF24', critical:'#EF4444' })[s] || '#94A3B8';
const statusBg    = (s) => ({
  normal:   'border-green-500/30 bg-green-500/5',
  warning:  'border-yellow-500/30 bg-yellow-500/5',
  critical: 'border-red-500/30 bg-red-500/5 animate-pulse',
})[s] || 'border-slate-500/30 bg-slate-500/5';
const healthColor = (s) => s >= 85 ? '#10B981' : s >= 60 ? '#FBBF24' : s >= 40 ? '#F97316' : '#EF4444';
const sensorIcon  = (t) => ({ temperature: ThermometerSun, vibration: Activity, current: Zap, pressure: Wind, rpm: Cpu })[t] || Gauge;

const CHART_COLORS = { temperature:'#EF4444', vibration:'#F97316', current:'#3B82F6', pressure:'#8B5CF6', rpm:'#10B981' };
const Card = ({ children, className='' }) => <div className={`bg-[#1E293B] border border-[#334155] rounded-xl ${className}`}>{children}</div>;
const TIME_OPTIONS = [{ label:'1h', hours:1 }, { label:'6h', hours:6 }, { label:'24h', hours:24 }, { label:'7d', hours:168 }];

function safeTime(ts) {
  if (!ts) return '—';
  const d = new Date(ts);
  return isNaN(d.getTime()) ? '—' : d.toLocaleTimeString();
}

/* ── Health Gauge ─────────────────────────────────────────── */
function HealthGauge({ score, size=80 }) {
  const c = healthColor(score);
  const r = size*0.38, cx = size/2, cy = size/2;
  const start = Math.PI, filled = Math.PI*(score/100);
  const px = a => cx+r*Math.cos(a), py = a => cy+r*Math.sin(a);
  const bgPath = `M ${px(start)} ${py(start)} A ${r} ${r} 0 0 1 ${px(2*Math.PI)} ${py(2*Math.PI)}`;
  const fgEnd  = start+filled;
  const fgPath = score>0 ? `M ${px(start)} ${py(start)} A ${r} ${r} 0 ${filled>Math.PI?1:0} 1 ${px(fgEnd)} ${py(fgEnd)}` : '';
  return (
    <svg width={size} height={size*0.65} viewBox={`0 0 ${size} ${size*0.65}`}>
      <path d={bgPath} fill="none" stroke="#1E293B" strokeWidth={size*0.1} strokeLinecap="round" />
      {fgPath && <path d={fgPath} fill="none" stroke={c} strokeWidth={size*0.1} strokeLinecap="round" style={{transition:'all 0.8s ease'}} />}
      <text x={cx} y={cy*0.88} textAnchor="middle" fill={c} fontSize={size*0.2} fontWeight="bold" fontFamily="monospace">{score}%</text>
    </svg>
  );
}

/* ── Sensor Card ──────────────────────────────────────────── */
function SensorCard({ sensor, onClick }) {
  const Icon = sensorIcon(sensor.sensor_type);
  const c = statusColor(sensor.status);
  return (
    <div onClick={onClick} className={`p-3 rounded-xl border cursor-pointer transition-all hover:scale-[1.02] ${statusBg(sensor.status)}`}>
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-1.5">
          <Icon className="w-3.5 h-3.5" style={{color:c}} />
          <span className="text-xs text-slate-300 capitalize">{sensor.sensor_type}</span>
        </div>
        <span className="text-[10px] px-1.5 py-0.5 rounded border" style={{color:c,borderColor:c+'50',backgroundColor:c+'15'}}>{sensor.status}</span>
      </div>
      <div className="text-2xl font-mono font-bold" style={{color:c}}>
        {sensor.value}<span className="text-xs text-slate-400 ml-1">{sensor.unit}</span>
      </div>
      <div className="text-[10px] text-slate-500 mt-1">Normal: {sensor.normal_range} {sensor.unit}</div>
    </div>
  );
}

/* ── Equipment Detail ─────────────────────────────────────── */
function EquipmentDetail({ equipment, onBack, timeHours, onTimeChange }) {
  const [history, setHistory]           = useState([]);
  const [loading, setLoading]           = useState(true);
  const [activeSensor, setActiveSensor] = useState('temperature');

  const loadHistory = useCallback(async () => {
    setLoading(true);
    try {
      const r = await fetch(`${API}/history/${encodeURIComponent(equipment.equipment_name)}?hours=${timeHours}`);
      const d = await r.json();
      setHistory(d.readings.map(row => ({
        time: new Date(row.timestamp).toLocaleTimeString([], {hour:'2-digit',minute:'2-digit'}),
        temperature:row.temperature, vibration:row.vibration,
        current:row.current, pressure:row.pressure, rpm:row.rpm,
      })));
    } catch {}
    setLoading(false);
  }, [equipment.equipment_name, timeHours]);

  useEffect(() => { loadHistory(); }, [loadHistory]);

  const hc = healthColor(equipment.health_score);
  const sensors = ['temperature','vibration','current','pressure','rpm'];
  const stats = {};
  sensors.forEach(s => {
    const vals = history.map(h => h[s]).filter(v => v != null);
    if (vals.length > 0) stats[s] = {
      min: Math.min(...vals).toFixed(2), max: Math.max(...vals).toFixed(2),
      avg: (vals.reduce((a,b)=>a+b,0)/vals.length).toFixed(2),
      last: vals[vals.length-1]?.toFixed(2),
    };
  });

  return (
    <div className="space-y-5">
      <div className="flex items-center gap-3 flex-wrap">
        <button onClick={onBack} className="flex items-center gap-1 text-slate-400 hover:text-white text-sm transition-colors">
          <ChevronLeft className="w-4 h-4" /> All Equipment
        </button>
        <span className="text-slate-600">/</span>
        <span className="text-white font-medium">{equipment.equipment_name}</span>
        <div className="flex gap-1 ml-auto">
          {TIME_OPTIONS.map(t => (
            <button key={t.label} onClick={() => onTimeChange(t.hours)}
              className={`px-3 py-1 text-xs rounded-lg border transition-all ${timeHours===t.hours?'bg-orange-500 border-orange-500 text-white':'border-[#334155] text-slate-400 hover:text-white'}`}>
              {t.label}
            </button>
          ))}
        </div>
      </div>

      <Card className="p-4">
        <div className="flex items-center gap-5 flex-wrap">
          <HealthGauge score={equipment.health_score} size={100} />
          <div className="flex-1">
            <h2 className="text-xl font-heading font-bold text-white">{equipment.equipment_name}</h2>
            <div className="flex items-center gap-3 mt-1 flex-wrap">
              <span className="text-sm font-semibold" style={{color:hc}}>{equipment.health_status}</span>
              <span className="text-slate-600">·</span>
              <span className="text-sm text-slate-400">Risk: {equipment.risk_level}</span>
              <span className="text-slate-600">·</span>
              <span className="text-xs text-slate-500">Updated: {safeTime(equipment.last_updated)}</span>
            </div>
          </div>
          <div className="grid grid-cols-5 gap-2">
            {equipment.sensors.map(s => {
              const Icon = sensorIcon(s.sensor_type);
              const c = statusColor(s.status);
              return (
                <div key={s.sensor_type} onClick={() => setActiveSensor(s.sensor_type)}
                  className={`p-2.5 rounded-lg border cursor-pointer transition-all text-center ${activeSensor===s.sensor_type?'border-orange-500 bg-orange-500/10':statusBg(s.status)}`}>
                  <Icon className="w-4 h-4 mx-auto mb-1" style={{color:c}} />
                  <div className="text-sm font-mono font-bold" style={{color:c}}>{s.value}</div>
                  <div className="text-[9px] text-slate-500">{s.unit}</div>
                </div>
              );
            })}
          </div>
        </div>
      </Card>

      <Card className="p-4">
        <div className="flex items-center justify-between mb-4 flex-wrap gap-2">
          <div className="flex gap-1 flex-wrap">
            {sensors.map(s => history.some(h => h[s]!=null) && (
              <button key={s} onClick={() => setActiveSensor(s)}
                className={`px-3 py-1 text-xs rounded-lg border capitalize transition-all ${activeSensor===s?'text-white border-transparent':'border-[#334155] text-slate-400 hover:text-white'}`}
                style={activeSensor===s ? {backgroundColor:CHART_COLORS[s]} : {}}>
                {s}
              </button>
            ))}
          </div>
          <span className="text-xs text-slate-500">{history.length} readings · last {timeHours}h</span>
        </div>
        {loading ? (
          <div className="flex items-center justify-center h-48"><div className="w-8 h-8 border-2 border-orange-500 border-t-transparent rounded-full animate-spin" /></div>
        ) : history.length === 0 ? (
          <div className="flex items-center justify-center h-48 text-slate-500 text-sm">No data in this time range</div>
        ) : (
          <ResponsiveContainer width="100%" height={200}>
            <AreaChart data={history} margin={{top:5,right:10,bottom:0,left:0}}>
              <defs>
                <linearGradient id={`grad-${activeSensor}`} x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%"  stopColor={CHART_COLORS[activeSensor]} stopOpacity={0.3} />
                  <stop offset="95%" stopColor={CHART_COLORS[activeSensor]} stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#1E293B" />
              <XAxis dataKey="time" tick={{fontSize:10,fill:'#64748B'}} interval="preserveStartEnd" />
              <YAxis tick={{fontSize:10,fill:'#64748B'}} width={45} />
              <Tooltip contentStyle={{background:'#1E293B',border:'1px solid #334155',fontSize:11}} />
              <Area type="monotone" dataKey={activeSensor} stroke={CHART_COLORS[activeSensor]} strokeWidth={2} fill={`url(#grad-${activeSensor})`} dot={false} />
            </AreaChart>
          </ResponsiveContainer>
        )}
      </Card>

      {Object.keys(stats).length > 0 && (
        <Card className="overflow-hidden">
          <table className="industrial-table">
            <thead><tr><th>Sensor</th><th>Latest</th><th>Min</th><th>Max</th><th>Average</th></tr></thead>
            <tbody>
              {Object.entries(stats).map(([sensor, v]) => {
                const s = equipment.sensors.find(x => x.sensor_type === sensor);
                const c = statusColor(s?.status || 'normal');
                return (
                  <tr key={sensor}>
                    <td className="capitalize font-medium">{sensor}</td>
                    <td className="font-mono font-bold" style={{color:c}}>{v.last} {s?.unit}</td>
                    <td className="font-mono text-slate-400">{v.min}</td>
                    <td className="font-mono text-slate-400">{v.max}</td>
                    <td className="font-mono text-slate-400">{v.avg}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </Card>
      )}
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════
   MAIN PAGE — Simulation always ON, Anomaly toggle only
═══════════════════════════════════════════════════════════ */
export default function SensorMonitoring() {
  const [liveData,        setLiveData]        = useState({ equipment:[], total:0 });
  const [loading,         setLoading]         = useState(true);
  const [selectedEq,      setSelectedEq]      = useState(null);
  const [timeHours,       setTimeHours]       = useState(24);
  const [lastUpdate,      setLastUpdate]      = useState(null);
  const [anomalyTarget,   setAnomalyTarget]   = useState('');
  const [injecting,       setInjecting]       = useState(false);
  const [injectMsg,       setInjectMsg]       = useState('');
  const [pinnedAnomalies, setPinnedAnomalies] = useState([]);
  // No countdown — anomaly persists until user clicks Resolve

  const simTimer = useRef(null);

  /* ── load helpers ─────────────────────────────────────── */
  const loadLive = useCallback(async () => {
    try {
      const d = await fetch(`${API}/live-status`).then(r => r.json());
      setLiveData(d);
      setLastUpdate(new Date());
      setLoading(false);
    } catch {}
  }, []);

  const loadPins = useCallback(async () => {
    try {
      const d = await fetch(`${API}/anomaly-pins`).then(r => r.json());
      setPinnedAnomalies(d.pinned || []);
    } catch {}
  }, []);

  /* ── simulation tick (skips pinned machines) ──────────── */
  const simTick = useCallback(async () => {
    try {
      await fetch(`${API}/simulate-all`, { method:'POST' });
      await loadLive();
      await loadPins();
    } catch {}
  }, [loadLive, loadPins]);

  const simTickRef = useRef(simTick);
  useEffect(() => { simTickRef.current = simTick; }, [simTick]);

  /* ── auto-start simulation on mount, survive refresh ──── */
  useEffect(() => {
    let active = true;
    (async () => {
      // On mount, keep existing pins — do NOT auto-clear them.
      // Only the Resolve button clears pins.
      try {
        await loadPins();
      } catch {}
      if (active) {
        simTickRef.current();
        simTimer.current = setInterval(() => simTickRef.current(), 3000);
      }
    })();
    return () => {
      active = false;
      if (simTimer.current) clearInterval(simTimer.current);
    };
  }, []); // empty — runs once on mount

  /* ── Resolve: force machine back to normal simulation ───── */
  const resolveWarning = useCallback(async (eqName) => {
    try {
      // 1. Always unpin — whether it was an injected anomaly or a simulation warning
      await fetch(`${API}/clear-anomaly?equipment_name=${encodeURIComponent(eqName)}`, { method:'POST' });

      // 2. Write exact normal values + add 15-second grace period on backend
      //    so simulate-all cannot immediately overwrite with a new warning reading
      await fetch(`${API}/simulate-normal?equipment_name=${encodeURIComponent(eqName)}`, { method:'POST' });

      // 3. Refresh
      await loadPins();
      await loadLive();
    } catch {}
  }, [loadLive, loadPins]);

  /* ── inject anomaly — stays until user clicks Resolve ─── */
  const injectAnomaly = async () => {
    if (!anomalyTarget) return;
    setInjecting(true);
    setInjectMsg('');
    try {
      const r = await fetch(
        `${API}/inject-anomaly?equipment_name=${encodeURIComponent(anomalyTarget)}`,
        { method:'POST' }
      );
      const d = await r.json();
      if (r.ok) {
        await loadLive();
        await loadPins();
        setInjectMsg(`✅ Anomaly active on "${anomalyTarget}" — click Resolve to restore`);
        setTimeout(() => setInjectMsg(''), 6000);
      } else {
        setInjectMsg(`❌ ${d.detail || 'Failed'}`);
      }
    } catch (e) {
      setInjectMsg(`❌ ${e.message}`);
    } finally {
      setInjecting(false);
    }
  };

  /* ── derived ─────────────────────────────────────────── */
  const eqList    = liveData.equipment || [];
  const healthy   = eqList.filter(e => e.health_score >= 85).length;
  const warning   = eqList.filter(e => e.health_score >= 60 && e.health_score < 85).length;
  const highRisk  = eqList.filter(e => e.health_score >= 40 && e.health_score < 60).length;
  const critical  = eqList.filter(e => e.health_score < 40).length;
  const allAlerts = eqList.flatMap(e =>
    e.sensors.filter(s => s.status !== 'normal').map(s => ({equipment:e.equipment_name,...s}))
  );

  useEffect(() => {
    if (eqList.length > 0 && !anomalyTarget) setAnomalyTarget(eqList[0].equipment_name);
  }, [eqList, anomalyTarget]);

  if (selectedEq) {
    return (
      <div className="p-6">
        <EquipmentDetail equipment={selectedEq} onBack={() => setSelectedEq(null)}
          timeHours={timeHours} onTimeChange={setTimeHours} />
      </div>
    );
  }

  return (
    <div className="space-y-6 p-6">

      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-2xl font-heading font-bold text-white flex items-center gap-2">
            <Activity className="w-6 h-6 text-orange-500" /> Sensor Monitoring
          </h1>
          <p className="text-slate-400 text-sm mt-0.5 flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse inline-block" />
            Simulation running · auto-updates every 3s
            {pinnedAnomalies.length > 0 && (
              <span className="flex items-center gap-1 text-red-400 text-xs">
                · <span className="w-1.5 h-1.5 rounded-full bg-red-500 animate-pulse inline-block" />
                Anomaly: {pinnedAnomalies.join(', ')}
              </span>
            )}
            {lastUpdate && <span className="text-slate-600">· {lastUpdate.toLocaleTimeString()}</span>}
          </p>
        </div>
        <button onClick={loadLive}
          className="p-2 bg-[#1E293B] border border-[#334155] hover:border-orange-500/40 text-slate-400 hover:text-white rounded-lg transition-all">
          <RefreshCw className="w-4 h-4" />
        </button>
      </div>

      {/* Status banner */}
      {pinnedAnomalies.length === 0 ? (
        <div className="flex items-center gap-3 px-4 py-3 rounded-xl border bg-green-500/10 border-green-500/30 text-green-300 text-sm">
          <div className="w-2 h-2 rounded-full flex-shrink-0 bg-green-400 animate-pulse" />
          All machines running in simulation — sensor readings update every 3 seconds.
        </div>
      ) : (
        <div className="flex items-center gap-3 px-4 py-3 rounded-xl border bg-orange-500/10 border-orange-500/30 text-orange-300 text-sm">
          <div className="w-2 h-2 rounded-full flex-shrink-0 bg-orange-400 animate-pulse" />
          Simulation running for all machines except{' '}
          <strong className="text-white">{pinnedAnomalies.join(', ')}</strong>
          {' '}— anomaly active, auto-restores when countdown ends.
        </div>
      )}

      {/* Anomaly panel */}
      <Card className="p-4 border-orange-500/30 bg-orange-500/5">
        <div className="flex items-center gap-2 mb-4">
          <Siren className="w-4 h-4 text-orange-400" />
          <span className="text-sm font-semibold text-orange-400">Anomaly Injection</span>
          <span className="text-xs text-slate-500 ml-1">— simulation keeps running for all other machines</span>
        </div>

        <div className="flex items-center gap-3 flex-wrap">
          {/* Machine selector */}
          <div className="flex flex-col gap-1">
            <label className="text-[10px] text-slate-400 uppercase tracking-wider">Select Machine</label>
            <select value={anomalyTarget} onChange={e => setAnomalyTarget(e.target.value)}
              className="bg-[#0F1419] border border-[#334155] text-white text-sm rounded-lg px-3 py-2 focus:outline-none focus:border-orange-500 min-w-[220px]">
              {eqList.length === 0
                ? <option value="">Loading...</option>
                : eqList.map(eq => (
                    <option key={eq.equipment_name} value={eq.equipment_name}>
                      {pinnedAnomalies.includes(eq.equipment_name) ? '⚠ ' : ''}{eq.equipment_name}
                    </option>
                  ))
              }
            </select>
          </div>

          {/* Start Anomaly button — disabled while already active on this machine */}
          <div className="flex flex-col gap-1">
            <label className="text-[10px] text-slate-400 uppercase tracking-wider invisible">action</label>
            <button onClick={injectAnomaly}
              disabled={!anomalyTarget || injecting || pinnedAnomalies.includes(anomalyTarget)}
              className="flex items-center gap-2 px-5 py-2 bg-red-600 hover:bg-red-700 disabled:opacity-40 disabled:cursor-not-allowed text-white text-sm font-semibold rounded-lg transition-colors">
              {injecting ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Siren className="w-4 h-4" />}
              {injecting ? 'Injecting...' : 'Start Anomaly'}
            </button>
          </div>

          {injectMsg && (
            <span className={`text-sm font-medium self-end pb-0.5 ${injectMsg.startsWith('✅') ? 'text-green-400' : 'text-red-400'}`}>
              {injectMsg}
            </span>
          )}
        </div>

        {/* Active anomalies — no countdown, only Resolve button */}
        {pinnedAnomalies.length > 0 && (
          <div className="mt-4 pt-3 border-t border-orange-500/20">
            <div className="text-[10px] text-slate-400 uppercase tracking-wider mb-2">
              Active Anomalies — click Resolve to restore to simulation
            </div>
            <div className="flex flex-wrap gap-2">
              {pinnedAnomalies.map(name => (
                <div key={name} className="flex items-center gap-3 px-3 py-2 bg-red-500/10 border border-red-500/30 rounded-xl">
                  <span className="flex items-center gap-1.5 text-red-400 text-xs font-semibold">
                    <span className="w-1.5 h-1.5 rounded-full bg-red-500 animate-pulse" />
                    {name}
                  </span>
                  <button
                    onClick={() => resolveWarning(name)}
                    className="flex items-center gap-1.5 px-3 py-1 bg-green-500/15 border border-green-500/30 text-green-400 hover:bg-green-500/25 text-xs font-semibold rounded-lg transition-colors"
                  >
                    <CheckCircle className="w-3.5 h-3.5" /> Resolve
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        <p className="mt-3 text-[11px] text-slate-500">
          <strong className="text-slate-400">Start Anomaly</strong> — pushes all sensors above critical threshold. Stays active until you click Resolve.{' '}
          <strong className="text-slate-400">Resolve</strong> — immediately restores the machine to normal simulation values.
        </p>
      </Card>

      {/* KPI cards */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
        {[
          {label:'Total Monitored',val:eqList.length, color:'text-white',      bg:'bg-slate-500/10 border-slate-500/20'},
          {label:'Healthy',        val:healthy,       color:'text-green-400',  bg:'bg-green-500/10 border-green-500/20'},
          {label:'Warning',        val:warning,       color:'text-yellow-400', bg:'bg-yellow-500/10 border-yellow-500/20'},
          {label:'High Risk',      val:highRisk,      color:'text-orange-400', bg:'bg-orange-500/10 border-orange-500/20'},
          {label:'Critical',       val:critical,      color:'text-red-400',    bg:'bg-red-500/10 border-red-500/20'},
        ].map(({label,val,color,bg}) => (
          <div key={label} className={`rounded-xl border p-3 text-center ${bg}`}>
            <div className={`text-2xl font-heading font-bold ${color}`}>{val}</div>
            <div className="text-[10px] text-slate-400 mt-1">{label}</div>
          </div>
        ))}
      </div>

      {/* Active alerts */}
      {allAlerts.length > 0 && (
        <Card className="p-4">
          <div className="flex items-center gap-2 mb-3">
            <AlertTriangle className="w-4 h-4 text-red-400" />
            <span className="text-sm font-semibold text-white">Active Sensor Alerts ({allAlerts.length})</span>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-2">
            {allAlerts.map((a,i) => {
              const c = statusColor(a.status);
              return (
                <div key={i} className={`flex items-center gap-3 p-2.5 rounded-lg border ${statusBg(a.status)}`}>
                  <AlertCircle className="w-4 h-4 flex-shrink-0" style={{color:c}} />
                  <div className="flex-1 min-w-0">
                    <div className="text-xs font-semibold text-white truncate">{a.equipment}</div>
                    <div className="text-[10px] text-slate-400 capitalize">{a.sensor_type}: {a.value} {a.unit}</div>
                    <div className="text-[10px]" style={{color:c}}>
                      {a.status==='critical'?'CRITICAL':'WARNING'} · Threshold: {a.warn_threshold} {a.unit}
                    </div>
                  </div>
                  {/* Resolve button — only shown if not a pinned anomaly */}
                  {!pinnedAnomalies.includes(a.equipment) && (
                    <button
                      onClick={() => resolveWarning(a.equipment)}
                      className="flex-shrink-0 flex items-center gap-1 px-2.5 py-1.5 bg-green-500/10 border border-green-500/30 text-green-400 hover:bg-green-500/20 text-[10px] font-semibold rounded-lg transition-colors"
                      title="Resolve — write a fresh normal reading"
                    >
                      <CheckCircle className="w-3 h-3" /> Resolve
                    </button>
                  )}
                </div>
              );
            })}
          </div>
        </Card>
      )}

      {/* Equipment grid */}
      {loading ? (
        <div className="flex items-center justify-center py-20">
          <div className="w-10 h-10 border-2 border-orange-500 border-t-transparent rounded-full animate-spin" />
        </div>
      ) : eqList.length === 0 ? (
        <Card className="p-12 text-center">
          <Activity className="w-12 h-12 text-slate-600 mx-auto mb-3" />
          <p className="text-slate-400">No sensor data yet — simulation starting...</p>
        </Card>
      ) : (
        <div className="space-y-4">
          {eqList.map(eq => {
            const hc = healthColor(eq.health_score);
            const isAnomaly = pinnedAnomalies.includes(eq.equipment_name);
            const hasWarning = eq.sensors?.some(s => s.status !== 'normal');
            return (
              <Card key={eq.equipment_name} className={`p-4 ${isAnomaly ? 'border-red-500/40 bg-red-500/5' : hasWarning ? 'border-yellow-500/30' : ''}`}>
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-3 cursor-pointer flex-1 min-w-0" onClick={() => setSelectedEq(eq)}>
                    <HealthGauge score={eq.health_score} size={72} />
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2 flex-wrap">
                        <h3 className="text-white font-heading font-semibold">{eq.equipment_name}</h3>
                        {isAnomaly && (
                          <span className="text-[10px] px-2 py-0.5 rounded bg-red-500/20 border border-red-500/40 text-red-400 animate-pulse font-medium">
                            ⚠ ANOMALY
                          </span>
                        )}
                        {!isAnomaly && hasWarning && (
                          <span className="text-[10px] px-2 py-0.5 rounded bg-yellow-500/20 border border-yellow-500/40 text-yellow-400 font-medium">
                            ⚡ WARNING
                          </span>
                        )}
                      </div>
                      <div className="flex items-center gap-2 mt-0.5 flex-wrap">
                        <span className="text-sm font-medium" style={{color:hc}}>{eq.health_status}</span>
                        <span className="text-slate-600">·</span>
                        <span className="text-xs text-slate-400">Risk: {eq.risk_level}</span>
                        <span className="text-slate-600">·</span>
                        <span className="text-xs text-slate-500">
                          <Clock className="w-3 h-3 inline mr-0.5" />{safeTime(eq.last_updated)}
                        </span>
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center gap-2 flex-shrink-0 ml-2">
                    {/* Resolve button — visible when machine has any warning/critical sensors and is NOT pinned */}
                    {hasWarning && !isAnomaly && (
                      <button
                        onClick={e => { e.stopPropagation(); resolveWarning(eq.equipment_name); }}
                        className="flex items-center gap-1.5 px-3 py-1.5 bg-green-500/10 border border-green-500/30 text-green-400 hover:bg-green-500/20 text-xs font-semibold rounded-lg transition-colors"
                        title="Resolve — write a fresh normal reading and return to simulation"
                      >
                        <CheckCircle className="w-3.5 h-3.5" /> Resolve
                      </button>
                    )}
                    <button className="text-xs text-orange-400 hover:text-orange-300 flex items-center gap-1 transition-colors" onClick={() => setSelectedEq(eq)}>
                      View Details <ChevronLeft className="w-3 h-3 rotate-180" />
                    </button>
                  </div>
                </div>
                <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-5 gap-2">
                  {eq.sensors.map(s => <SensorCard key={s.sensor_type} sensor={s} onClick={() => setSelectedEq(eq)} />)}
                </div>
              </Card>
            );
          })}
        </div>
      )}

      {/* Readings table */}
      {eqList.length > 0 && (
        <Card className="overflow-hidden">
          <div className="p-4 border-b border-[#334155]">
            <h2 className="text-sm font-semibold text-white flex items-center gap-2">
              <Gauge className="w-4 h-4 text-orange-400" /> All Sensor Readings
            </h2>
          </div>
          <table className="industrial-table">
            <thead>
              <tr><th>Equipment</th><th>Sensor</th><th>Value</th><th>Normal Range</th><th>Status</th><th>Last Updated</th><th>Action</th></tr>
            </thead>
            <tbody>
              {eqList.flatMap(eq =>
                (eq.sensors||[]).map(s => (
                  <tr key={`${eq.equipment_name}-${s.sensor_type}`} className="cursor-pointer" onClick={() => setSelectedEq(eq)}>
                    <td className="font-medium">{eq.equipment_name}</td>
                    <td className="capitalize text-slate-300">{s.sensor_type}</td>
                    <td className="font-mono font-bold" style={{color:statusColor(s.status)}}>{s.value} {s.unit}</td>
                    <td className="text-slate-400 text-xs">{s.normal_range} {s.unit}</td>
                    <td>
                      <span className="flex items-center gap-1 w-fit px-2 py-0.5 rounded border text-xs capitalize"
                        style={{color:statusColor(s.status),borderColor:statusColor(s.status)+'40',backgroundColor:statusColor(s.status)+'10'}}>
                        {s.status==='critical' && <AlertCircle className="w-3 h-3" />}
                        {s.status==='warning'  && <AlertTriangle className="w-3 h-3" />}
                        {s.status==='normal'   && <CheckCircle className="w-3 h-3" />}
                        {s.status}
                      </span>
                    </td>
                    <td className="text-slate-500 text-xs font-mono">{safeTime(s.last_updated)}</td>
                    <td onClick={e => e.stopPropagation()}>
                      {s.status !== 'normal' && !pinnedAnomalies.includes(eq.equipment_name) && (
                        <button
                          onClick={() => resolveWarning(eq.equipment_name)}
                          className="flex items-center gap-1 px-2 py-1 bg-green-500/10 border border-green-500/30 text-green-400 hover:bg-green-500/20 text-[10px] font-semibold rounded-lg transition-colors"
                        >
                          <CheckCircle className="w-3 h-3" /> Resolve
                        </button>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </Card>
      )}
    </div>
  );
}
