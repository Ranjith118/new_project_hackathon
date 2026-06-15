import { useState, useEffect, useCallback, useRef } from 'react';
import {
  BarChart3, AlertTriangle, Shield, Clock, RefreshCw,
  ChevronLeft, Brain, Package, Activity,
  AlertCircle, Factory, Eye, Star, DollarSign,
  Wifi, WifiOff
} from 'lucide-react';
import {
  RadarChart, Radar, PolarGrid, PolarAngleAxis,
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  Cell
} from 'recharts';

const API  = 'http://localhost:8000/api/decision-support';
const PROC = 'http://localhost:8000/api/procurement';
const SENSOR_API = 'http://localhost:8000/api/sensor-data';
const get  = (u) => fetch(u).then(r => r.json()).catch(() => null);
const post = (u, b) => fetch(u, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(b) }).then(r => r.json()).catch(() => null);
const POLL_INTERVAL = 3000; // 3 seconds

/* ── helpers ─────────────────────────────────────────────── */
const priorityColor = (p) => ({ P1: '#EF4444', P2: '#F97316', P3: '#FBBF24', P4: '#10B981' })[p] || '#94A3B8';
const priorityBadge = (p) => ({
  P1: 'bg-red-500/20 text-red-400 border-red-500/40',
  P2: 'bg-orange-500/20 text-orange-400 border-orange-500/40',
  P3: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/40',
  P4: 'bg-green-500/20 text-green-400 border-green-500/40',
})[p] || 'bg-slate-500/20 text-slate-400';
const riskBadge = (r) => ({ critical: 'bg-red-500/20 text-red-400 border-red-500/40', high: 'bg-orange-500/20 text-orange-400 border-orange-500/40', medium: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/40', low: 'bg-green-500/20 text-green-400 border-green-500/40' })[r?.toLowerCase()] || 'bg-slate-500/20 text-slate-400';
const scoreColor = (s) => s >= 90 ? '#EF4444' : s >= 75 ? '#F97316' : s >= 50 ? '#FBBF24' : '#10B981';

const Card = ({ children, className = '' }) => (
  <div className={`bg-[#1E293B] border border-[#334155] rounded-xl ${className}`}>{children}</div>
);

/* ── Priority score gauge ───────────────────────────────── */
function ScoreGauge({ score, size = 64 }) {
  const c = scoreColor(score);
  const r = size * 0.42;
  const cx = size / 2, cy = size / 2;
  const start = Math.PI, sweep = Math.PI;
  const filled = sweep * (score / 100);
  const px = (a) => cx + r * Math.cos(a);
  const py = (a) => cy + r * Math.sin(a);
  const bgPath = `M ${px(start)} ${py(start)} A ${r} ${r} 0 0 1 ${px(2 * Math.PI)} ${py(2 * Math.PI)}`;
  const fgEnd  = start + filled;
  const fgPath = score > 0 ? `M ${px(start)} ${py(start)} A ${r} ${r} 0 ${filled > Math.PI ? 1 : 0} 1 ${px(fgEnd)} ${py(fgEnd)}` : '';
  return (
    <svg width={size} height={size * 0.65} viewBox={`0 0 ${size} ${size * 0.65}`}>
      <path d={bgPath} fill="none" stroke="#1E293B" strokeWidth={size * 0.1} strokeLinecap="round" />
      {fgPath && <path d={fgPath} fill="none" stroke={c} strokeWidth={size * 0.1} strokeLinecap="round" style={{ transition: 'all 0.8s ease' }} />}
      <text x={cx} y={cy * 0.85} textAnchor="middle" fill={c} fontSize={size * 0.2} fontWeight="bold" fontFamily="monospace">{score.toFixed(0)}</text>
    </svg>
  );
}

/* ── Equipment Detail Panel ─────────────────────────────── */
function EquipmentDetail({ equip, criticality, liveStatus, onBack }) {
  const [spares,    setSpares]    = useState([]);
  const [preds,     setPreds]     = useState(null);
  const [maintLogs, setMaintLogs] = useState([]);

  useEffect(() => {
    Promise.all([
      get(PROC + '/spares'),
      get(`http://localhost:8000/api/prediction/risk/${encodeURIComponent(equip.equipment_name)}`),
      get(`http://localhost:8000/api/maintenance-logs/?equipment_name=${encodeURIComponent(equip.equipment_name)}&limit=4`),
    ]).then(([sp, pr, ml]) => {
      setSpares(sp?.parts?.filter(p => p.equipment_type === 'motor' || p.status !== 'in_stock').slice(0, 5) || []);
      setPreds(pr);
      setMaintLogs(Array.isArray(ml) ? ml : []);
    });
  }, [equip.equipment_name]);

  const pc    = priorityColor(equip.priority_level);
  const score = equip.priority_score || 0;
  const live  = liveStatus[equip.equipment_name];

  // Radar chart data for this equipment
  const crit = criticality?.find(c => c.equipment_id === equip.equipment_id);
  const radarData = crit ? [
    { subject: 'Production', value: crit.production_dependency },
    { subject: 'Safety',     value: crit.safety_impact },
    { subject: 'Environ',    value: crit.environmental_impact },
    { subject: 'Downtime',   value: Math.min(100, crit.downtime_cost / 100) },
    { subject: 'Replacement',value: crit.replacement_difficulty },
  ] : [];

  return (
    <div className="space-y-5">
      <button onClick={onBack} className="flex items-center gap-1 text-slate-400 hover:text-white text-sm transition-colors">
        <ChevronLeft className="w-4 h-4" /> Plant Prioritization Center
      </button>

      {/* Header */}
      <Card className="p-5 border-l-4" style={{ borderLeftColor: pc }}>
        <div className="flex items-start justify-between flex-wrap gap-4">
          <div>
            <div className="flex items-center gap-2 flex-wrap mb-1">
              <span className="text-2xl font-heading font-bold text-white">{equip.equipment_name}</span>
              <span className={`text-xs px-2 py-0.5 rounded border font-bold ${priorityBadge(equip.priority_level)}`}>Rank #{equip.rank} · {equip.priority_level}</span>
            </div>
            <div className="text-slate-400 text-sm">Action: <span className="text-orange-300 font-medium">{equip.recommended_action}</span></div>
          </div>
          <ScoreGauge score={score} size={90} />
        </div>

        {/* Live sensor snapshot */}
        {live && live.sensors?.length > 0 && (
          <div className="mt-4 p-3 bg-blue-500/5 border border-blue-500/20 rounded-xl">
            <div className="text-xs text-blue-400 font-semibold mb-2 flex items-center gap-1">
              <Activity className="w-3 h-3 animate-pulse" /> Live Sensor Readings
              <span className="text-slate-500 font-normal ml-1">· Health {live.health_score}%</span>
            </div>
            <div className="flex flex-wrap gap-2">
              {live.sensors.map((s, i) => {
                const cls = s.status === 'critical' ? 'text-red-400 border-red-500/40 bg-red-500/10'
                          : s.status === 'warning'  ? 'text-yellow-400 border-yellow-500/40 bg-yellow-500/10'
                          : 'text-green-400 border-green-500/30 bg-green-500/5';
                return (
                  <div key={i} className={`flex flex-col items-center px-2 py-1 rounded border ${cls}`}>
                    <span className="text-[9px] text-slate-400 uppercase">{s.sensor_type}</span>
                    <span className="text-xs font-mono font-bold">{Number(s.value).toFixed(1)}</span>
                    <span className="text-[9px] opacity-70">{s.unit}</span>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Key metrics */}
        <div className="grid grid-cols-2 md:grid-cols-5 gap-3 mt-5 pt-5 border-t border-[#334155]">
          {[
            { label: 'Failure Prob',  val: (equip.failure_probability * 100).toFixed(0) + '%', color: '#EF4444' },
            { label: 'RUL Days',      val: equip.rul_days + 'd',                               color: equip.rul_days <= 14 ? '#EF4444' : '#F97316' },
            { label: 'Risk Score',    val: equip.risk_score?.toFixed(0),                        color: scoreColor(equip.risk_score) },
            { label: 'Criticality',   val: equip.criticality?.toFixed(0),                      color: scoreColor(equip.criticality) },
            { label: 'Priority Score',val: score.toFixed(0),                                   color: pc },
          ].map(({ label, val, color }) => (
            <div key={label} className="bg-[#0F1419] rounded-lg p-3 border border-[#334155] text-center">
              <div className="text-xl font-bold font-mono" style={{ color }}>{val}</div>
              <div className="text-[10px] text-slate-500 mt-0.5">{label}</div>
            </div>
          ))}
        </div>

        {/* Reasons */}
        {Array.isArray(equip.reason) && equip.reason.length > 0 && (
          <div className="mt-4 flex flex-wrap gap-2">
            {equip.reason.map((r, i) => (
              <span key={i} className="text-xs px-2.5 py-1 bg-orange-500/10 border border-orange-500/20 text-orange-300 rounded-lg">{r}</span>
            ))}
          </div>
        )}
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        {/* Criticality radar */}
        {radarData.length > 0 && (
          <Card className="p-4">
            <h3 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
              <Shield className="w-4 h-4 text-orange-400" /> Criticality Factors
            </h3>
            <ResponsiveContainer width="100%" height={200}>
              <RadarChart data={radarData} margin={{ top: 10, right: 20, bottom: 10, left: 20 }}>
                <PolarGrid stroke="#334155" />
                <PolarAngleAxis dataKey="subject" tick={{ fontSize: 10, fill: '#94A3B8' }} />
                <Radar dataKey="value" stroke="#F97316" fill="#F97316" fillOpacity={0.2} />
                <Tooltip contentStyle={{ background: '#1E293B', border: '1px solid #334155', fontSize: 11 }} />
              </RadarChart>
            </ResponsiveContainer>
            {crit && (
              <div className="grid grid-cols-2 gap-2 mt-3">
                {[
                  { label: 'Downtime Cost/hr', val: '₹' + crit.downtime_cost?.toLocaleString('en-IN'), color: 'text-red-400' },
                  { label: 'Criticality Level', val: crit.criticality_level?.toUpperCase(), color: 'text-orange-400' },
                ].map(({ label, val, color }) => (
                  <div key={label} className="bg-[#0F1419] rounded p-2 border border-[#334155] text-center">
                    <div className={`text-sm font-bold ${color}`}>{val}</div>
                    <div className="text-[10px] text-slate-500">{label}</div>
                  </div>
                ))}
              </div>
            )}
          </Card>
        )}

        {/* Risk prediction */}
        <Card className="p-4">
          <h3 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
            <Brain className="w-4 h-4 text-purple-400" /> Risk Assessment
          </h3>
          {preds ? (
            <div className="space-y-3">
              {[
                { label: 'Overall Risk',        val: preds.overall_risk,                             color: preds.overall_risk === 'critical' ? '#EF4444' : '#F97316' },
                { label: 'Risk Score',          val: preds.risk_score?.toFixed(0) + '/100',          color: scoreColor(preds.risk_score) },
                { label: 'Failure Probability', val: (preds.failure_probability * 100).toFixed(1) + '%', color: '#EF4444' },
                { label: 'RUL (days)',           val: preds.rul_days,                                 color: preds.rul_days <= 14 ? '#EF4444' : '#FBBF24' },
                { label: 'Health Score',        val: preds.health_score + '%',                       color: '#10B981' },
              ].map(({ label, val, color }) => (
                <div key={label} className="flex justify-between text-xs py-1.5 border-b border-[#334155] last:border-0">
                  <span className="text-slate-400">{label}</span>
                  <span className="font-mono font-bold" style={{ color }}>{val}</span>
                </div>
              ))}
              {preds.explanation && (
                <div className="p-2.5 bg-[#0F1419] rounded border border-[#334155] text-xs text-slate-300 leading-relaxed">{preds.explanation}</div>
              )}
            </div>
          ) : <div className="text-slate-500 text-sm">Loading risk data...</div>}
        </Card>

        {/* Spare parts impact */}
        <Card className="p-4">
          <h3 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
            <Package className="w-4 h-4 text-yellow-400" /> Spare Parts Impact
          </h3>
          {spares.length > 0 ? spares.map((s, i) => {
            const statusOk = s.stock_quantity >= s.minimum_stock;
            return (
              <div key={i} className="flex items-center justify-between text-xs py-2 border-b border-[#334155] last:border-0">
                <div>
                  <div className="text-white">{s.part_name}</div>
                  <div className="text-slate-500 text-[10px]">Lead: {s.lead_time_days}d</div>
                </div>
                <div className="text-right">
                  <div className={`font-mono font-bold ${statusOk ? 'text-green-400' : 'text-red-400'}`}>{s.stock_quantity}/{s.minimum_stock}</div>
                  <div className={`text-[10px] ${statusOk ? 'text-green-400' : 'text-red-400'}`}>{statusOk ? 'OK' : 'CRITICAL'}</div>
                </div>
              </div>
            );
          }) : <div className="text-slate-500 text-sm">No critical spare parts identified</div>}
        </Card>

        {/* Maintenance history */}
        <Card className="p-4">
          <h3 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
            <Clock className="w-4 h-4 text-cyan-400" /> Maintenance History
          </h3>
          {maintLogs.length > 0 ? (
            <div className="space-y-2">
              {maintLogs.map(log => (
                <div key={log.log_id} className="flex items-start gap-2 p-2.5 bg-[#0F1419] rounded border border-[#334155]">
                  <div className={`w-1.5 h-1.5 rounded-full mt-1.5 flex-shrink-0 ${log.severity === 'critical' ? 'bg-red-500' : log.severity === 'high' ? 'bg-orange-500' : 'bg-yellow-500'}`} />
                  <div className="flex-1">
                    <div className="text-xs text-white">{log.issue}</div>
                    <div className="text-[10px] text-slate-400">{log.maintenance_date} · {log.technician || '—'}</div>
                  </div>
                  {log.downtime_hours > 0 && <span className="text-[10px] text-red-400 flex-shrink-0">{log.downtime_hours}h</span>}
                </div>
              ))}
            </div>
          ) : <div className="text-slate-500 text-sm">No maintenance history</div>}
        </Card>
      </div>
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════
   MAIN PAGE
═══════════════════════════════════════════════════════════ */
export default function DecisionSupport() {
  const [rankings,    setRankings]    = useState([]);
  const [criticality, setCriticality] = useState([]);
  const [risks,       setRisks]       = useState([]);
  const [bottlenecks, setBottlenecks] = useState([]);
  const [prioSum,     setPrioSum]     = useState(null);
  const [critSum,     setCritSum]     = useState(null);
  const [plantHealth, setPlantHealth] = useState(null);
  const [liveStatus,  setLiveStatus]  = useState({});   // equipmentName → live row
  const [loading,     setLoading]     = useState(true);
  const [selected,    setSelected]    = useState(null);
  const [filterLevel, setFilterLevel] = useState('');
  const [lastUpdate,  setLastUpdate]  = useState(null);
  const [liveOnline,  setLiveOnline]  = useState(false);
  const [autoRefresh, setAutoRefresh] = useState(true);

  // ── Fetch live sensor status and trigger simulation ──────
  const fetchLiveStatus = useCallback(async () => {
    // Simulate new readings so backend has fresh data
    await post(SENSOR_API + '/simulate-all', {});
    const status = await get(SENSOR_API + '/live-status');
    if (status?.equipment) {
      const map = {};
      for (const row of status.equipment) map[row.equipment_name] = row;
      setLiveStatus(map);
      setLiveOnline(true);
    } else {
      setLiveOnline(false);
    }
  }, []);

  // ── Load all decision-support data (driven by live sensors on backend) ──
  const load = useCallback(async () => {
    const [rank, crit, risk, bn, ps, cs, ph] = await Promise.all([
      get(API + '/equipment-ranking'),
      get(API + '/criticality'),
      get(API + '/risk'),
      get(API + '/bottlenecks'),
      get(API + '/priorities/summary'),
      get(API + '/criticality/summary'),
      get(API + '/plant-health'),
    ]);
    setRankings(rank?.rankings || []);
    setCriticality(Array.isArray(crit) ? crit : []);
    setRisks(Array.isArray(risk) ? risk : []);
    setBottlenecks(Array.isArray(bn) ? bn : []);
    setPrioSum(ps);
    setCritSum(cs);
    setPlantHealth(ph);
    setLastUpdate(new Date());
    setLoading(false);
  }, []);

  // ── Combined poll: simulate sensors → refresh decisions ──
  const poll = useCallback(async () => {
    await fetchLiveStatus();   // step 1: write fresh sensor rows to DB
    await load();              // step 2: backend reads those rows → re-scores everything
  }, [fetchLiveStatus, load]);

  // ── 3-second polling interval ─────────────────────────────
  useEffect(() => {
    if (!autoRefresh) return;
    poll();                                      // run immediately
    const id = setInterval(poll, POLL_INTERVAL);
    return () => clearInterval(id);
  }, [autoRefresh, poll]);

  const filtered = rankings.filter(r => !filterLevel || r.priority_level === filterLevel);

  // Analytics data
  const riskDist  = ['critical','high','medium','low'].map(r => ({
    name: r.charAt(0).toUpperCase() + r.slice(1),
    count: risks.filter(x => x.risk_level?.toLowerCase() === r).length
  }));
  const critDist = criticality.slice(0, 8).map(c => ({
    name: c.equipment_name.split(' ').slice(-1)[0],
    score: Math.round(c.criticality_score)
  }));
  const COLORS = ['#EF4444','#F97316','#FBBF24','#10B981'];

  const plantScore = plantHealth?.plant_health_score || 0;
  const plantColor = plantScore >= 80 ? '#10B981' : plantScore >= 60 ? '#FBBF24' : plantScore >= 40 ? '#F97316' : '#EF4444';

  if (selected) return (
    <div className="p-6">
      <EquipmentDetail equip={selected} criticality={criticality} liveStatus={liveStatus} onBack={() => setSelected(null)} />
    </div>
  );

  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-2xl font-heading font-bold text-white flex items-center gap-2">
            <BarChart3 className="w-6 h-6 text-orange-500" /> Plant Prioritization Center
          </h1>
          <p className="text-slate-400 text-sm mt-0.5 flex items-center gap-2">
            AI-driven maintenance priority ranking · Live sensor-driven decisions
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
        <div className="flex items-center gap-2">
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
            {autoRefresh ? 'Auto ON' : 'Auto OFF'}
          </button>
          <button onClick={poll} className="p-2 bg-[#1E293B] border border-[#334155] hover:border-orange-500/40 text-slate-400 hover:text-white rounded-lg transition-all">
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Live sensor feed strip */}
      {Object.keys(liveStatus).length > 0 && (
        <Card className="p-4 border-blue-500/20 bg-blue-500/5">
          <div className="flex items-center gap-2 mb-3">
            <Activity className="w-4 h-4 text-blue-400 animate-pulse" />
            <span className="text-sm font-semibold text-blue-400">Live Sensor Feed — decisions update every 3s</span>
            <span className="text-xs text-slate-500 ml-auto">{Object.keys(liveStatus).length} machines online</span>
          </div>
          <div className="flex flex-wrap gap-2">
            {Object.values(liveStatus)
              .sort((a, b) => a.health_score - b.health_score)
              .map((row, i) => {
                const sc = row.health_score;
                const col = sc < 40 ? 'border-red-500/40 bg-red-500/5 text-red-400'
                          : sc < 60 ? 'border-orange-500/40 bg-orange-500/5 text-orange-400'
                          : sc < 80 ? 'border-yellow-500/40 bg-yellow-500/5 text-yellow-400'
                          : 'border-green-500/30 bg-green-500/5 text-green-400';
                return (
                  <div key={i} className={`flex items-center gap-2 px-3 py-1.5 rounded-lg border text-xs ${col}`}>
                    <span className="text-white font-medium">{row.equipment_name.split(' ').slice(-1)[0]}</span>
                    <span className="font-mono font-bold">{sc}%</span>
                    {row.sensors?.some(s => s.status !== 'normal') && (
                      <AlertTriangle className="w-3 h-3 flex-shrink-0" />
                    )}
                  </div>
                );
              })}
          </div>
        </Card>
      )}

      {/* KPI Cards */}
      <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-6 gap-3">
        {[
          { label: 'Total Equipment',   val: critSum?.total_equipment ?? 0, color: 'text-white',     bg: 'bg-slate-500/10 border-slate-500/20' },
          { label: 'Critical',          val: critSum?.critical_count  ?? 0, color: 'text-red-400',   bg: 'bg-red-500/10 border-red-500/20' },
          { label: 'High Risk',         val: critSum?.high_count      ?? 0, color: 'text-orange-400',bg: 'bg-orange-500/10 border-orange-500/20' },
          { label: 'P1 Actions',        val: prioSum?.p1_count        ?? 0, color: 'text-red-400',   bg: 'bg-red-500/10 border-red-500/20' },
          { label: 'Plant Health',      val: plantScore.toFixed(0) + '%',   color: '', bg: 'bg-green-500/10 border-green-500/20', customColor: plantColor },
          { label: 'Downtime Cost/hr',  val: '₹' + ((critSum?.total_downtime_cost_per_hour || 0) / 1000).toFixed(0) + 'K', color: 'text-yellow-400', bg: 'bg-yellow-500/10 border-yellow-500/20' },
        ].map(({ label, val, color, bg, customColor }) => (
          <div key={label} className={`rounded-xl border p-3 text-center ${bg}`}>
            <div className={`text-2xl font-heading font-bold ${color}`} style={customColor ? { color: customColor } : {}}>{val}</div>
            <div className="text-[10px] text-slate-400 mt-1">{label}</div>
          </div>
        ))}
      </div>

      {/* Critical bottlenecks */}
      {bottlenecks.filter(b => b.severity === 'critical').length > 0 && (
        <Card className="p-4 border-red-500/20 bg-red-500/5">
          <div className="flex items-center gap-2 mb-3">
            <AlertCircle className="w-4 h-4 text-red-400" />
            <span className="text-sm font-semibold text-red-400">Critical Bottlenecks — Single Points of Failure</span>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-2">
            {bottlenecks.filter(b => b.severity === 'critical').map((b, i) => (
              <div key={i} className="flex items-start gap-3 p-3 bg-red-500/5 border border-red-500/20 rounded-lg">
                <AlertTriangle className="w-4 h-4 text-red-400 flex-shrink-0 mt-0.5" />
                <div>
                  <div className="text-xs font-semibold text-white">{b.equipment_name}</div>
                  <div className="text-[10px] text-red-300 mt-0.5">{b.impact}</div>
                  <div className="text-[10px] text-slate-400 mt-0.5">{b.reason}</div>
                  {b.mitigation_options?.slice(0, 1).map((m, j) => (
                    <div key={j} className="text-[10px] text-green-400 mt-1">↗ {m}</div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        {/* Priority ranking table */}
        <div className="xl:col-span-2 space-y-4">
          {/* Filter tabs */}
          <div className="flex gap-1 bg-[#1E293B] p-1 rounded-xl border border-[#334155] w-fit flex-wrap">
            {[['', 'All'], ['P1', 'Critical'], ['P2', 'High'], ['P3', 'Medium'], ['P4', 'Low']].map(([val, label]) => (
              <button key={val} onClick={() => setFilterLevel(val)}
                className={`px-4 py-1.5 text-xs font-medium rounded-lg transition-all ${
                  filterLevel === val ? (val ? `${priorityBadge(val)} font-bold` : 'bg-orange-500 text-white') : 'text-slate-400 hover:text-white'
                }`}>{label}</button>
            ))}
            <span className="text-xs text-slate-500 self-center ml-2">{filtered.length} equipment</span>
          </div>

          {loading ? (
            <div className="flex items-center justify-center py-16">
              <div className="w-8 h-8 border-2 border-orange-500 border-t-transparent rounded-full animate-spin" />
            </div>
          ) : (
            <Card className="overflow-hidden">
              <table className="industrial-table">
                <thead>
                  <tr>
                    <th>Rank</th>
                    <th>Equipment</th>
                    <th>Priority Score</th>
                    <th>Failure Prob</th>
                    <th>RUL</th>
                    <th>Live Health</th>
                    <th>Risk</th>
                    <th>Action</th>
                    <th className="text-right">Detail</th>
                  </tr>
                </thead>
                <tbody>
                  {filtered.map((eq, i) => {
                    const pc   = priorityColor(eq.priority_level);
                    const live = liveStatus[eq.equipment_name];
                    return (
                      <tr key={i} className="cursor-pointer" onClick={() => setSelected(eq)}>
                        <td>
                          <div className={`w-7 h-7 rounded-lg flex items-center justify-center text-xs font-bold ${
                            eq.rank === 1 ? 'bg-red-500/20 text-red-400' :
                            eq.rank === 2 ? 'bg-orange-500/20 text-orange-400' :
                            eq.rank === 3 ? 'bg-yellow-500/20 text-yellow-400' :
                            'bg-slate-500/20 text-slate-400'
                          }`}>{eq.rank}</div>
                        </td>
                        <td>
                          <div className="flex items-center gap-2">
                            <div className="w-7 h-7 rounded-lg flex items-center justify-center flex-shrink-0" style={{ backgroundColor: pc + '20', border: `1px solid ${pc}40` }}>
                              <Factory className="w-3.5 h-3.5" style={{ color: pc }} />
                            </div>
                            <span className="font-medium">{eq.equipment_name}</span>
                          </div>
                        </td>
                        <td>
                          <div className="flex items-center gap-2">
                            <ScoreGauge score={eq.priority_score} size={44} />
                            <span className={`text-xs px-1.5 py-0.5 rounded border ${priorityBadge(eq.priority_level)}`}>{eq.priority_level}</span>
                          </div>
                        </td>
                        <td>
                          <div className="flex items-center gap-1.5">
                            <div className="w-12 bg-[#0F1419] rounded-full h-1.5">
                              <div className="h-1.5 rounded-full" style={{ width: `${eq.failure_probability * 100}%`, backgroundColor: scoreColor(eq.failure_probability * 100) }} />
                            </div>
                            <span className="text-xs font-mono" style={{ color: scoreColor(eq.failure_probability * 100) }}>
                              {(eq.failure_probability * 100).toFixed(0)}%
                            </span>
                          </div>
                        </td>
                        <td>
                          <span className={`font-mono text-sm ${eq.rul_days <= 7 ? 'text-red-400 font-bold' : eq.rul_days <= 14 ? 'text-orange-400' : 'text-slate-300'}`}>
                            {eq.rul_days}d
                          </span>
                        </td>
                        {/* Live health column */}
                        <td>
                          {live ? (
                            <div className="flex items-center gap-1">
                              <div className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${
                                live.health_score < 40 ? 'bg-red-500' : live.health_score < 70 ? 'bg-yellow-500' : 'bg-green-500'
                              }`} />
                              <span className={`text-xs font-mono ${
                                live.health_score < 40 ? 'text-red-400' : live.health_score < 70 ? 'text-yellow-400' : 'text-green-400'
                              }`}>{live.health_score}%</span>
                            </div>
                          ) : (
                            <span className="text-slate-600 text-xs">—</span>
                          )}
                        </td>
                        <td>
                          <span className={`text-xs px-1.5 py-0.5 rounded border ${riskBadge(eq.production_impact)}`}>
                            {eq.production_impact || '—'}
                          </span>
                        </td>
                        <td className="text-slate-300 text-xs max-w-[140px]">
                          <span className="truncate block">{eq.recommended_action?.split(' ').slice(0, 4).join(' ')}...</span>
                        </td>
                        <td className="text-right" onClick={e => e.stopPropagation()}>
                          <button onClick={() => setSelected(eq)} className="p-1.5 text-blue-400 hover:bg-blue-500/20 rounded transition-colors">
                            <Eye className="w-3.5 h-3.5" />
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </Card>
          )}
        </div>

        {/* Right: Analytics panels */}
        <div className="space-y-4">
          {/* Plant health score */}
          <Card className="p-4 text-center">
            <div className="text-xs text-orange-400 font-semibold uppercase tracking-wider mb-2">Plant Risk Score</div>
            <ScoreGauge score={100 - plantScore} size={100} />
            <div className="text-lg font-bold mt-1" style={{ color: plantColor }}>{plantScore.toFixed(1)}% Healthy</div>
            <div className="grid grid-cols-2 gap-2 mt-3">
              {[
                { label: 'P1 Critical',  val: prioSum?.p1_count ?? 0, color: 'text-red-400' },
                { label: 'P2 High',      val: prioSum?.p2_count ?? 0, color: 'text-orange-400' },
                { label: 'Est Downtime', val: (prioSum?.total_estimated_downtime ?? 0) + 'h', color: 'text-yellow-400' },
                { label: 'Est Cost',     val: '₹' + ((prioSum?.total_estimated_cost || 0) / 1000).toFixed(0) + 'K', color: 'text-blue-400' },
              ].map(({ label, val, color }) => (
                <div key={label} className="bg-[#0F1419] rounded p-2 border border-[#334155] text-center">
                  <div className={`text-sm font-bold ${color}`}>{val}</div>
                  <div className="text-[9px] text-slate-500">{label}</div>
                </div>
              ))}
            </div>
          </Card>

          {/* Risk distribution */}
          <Card className="p-4">
            <h3 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
              <Shield className="w-4 h-4 text-orange-400" /> Risk Distribution
            </h3>
            <ResponsiveContainer width="100%" height={140}>
              <BarChart data={riskDist} margin={{ left: -20 }}>
                <XAxis dataKey="name" tick={{ fontSize: 10, fill: '#94A3B8' }} />
                <YAxis tick={{ fontSize: 10, fill: '#64748B' }} />
                <Tooltip contentStyle={{ background: '#1E293B', border: '1px solid #334155', fontSize: 11 }} />
                <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                  {riskDist.map((_, i) => <Cell key={i} fill={COLORS[i]} />)}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </Card>

          {/* Criticality scores */}
          {critDist.length > 0 && (
            <Card className="p-4">
              <h3 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
                <Star className="w-4 h-4 text-yellow-400" /> Equipment Criticality
              </h3>
              <ResponsiveContainer width="100%" height={180}>
                <BarChart data={critDist} layout="vertical" margin={{ left: 5, right: 20 }}>
                  <XAxis type="number" tick={{ fontSize: 9, fill: '#64748B' }} domain={[0, 100]} />
                  <YAxis type="category" dataKey="name" tick={{ fontSize: 9, fill: '#94A3B8' }} width={60} />
                  <Tooltip contentStyle={{ background: '#1E293B', border: '1px solid #334155', fontSize: 10 }} formatter={v => [v, 'Criticality']} />
                  <Bar dataKey="score" radius={[0, 3, 3, 0]}>
                    {critDist.map((d, i) => <Cell key={i} fill={scoreColor(d.score)} />)}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </Card>
          )}

          {/* Summary stats */}
          <Card className="p-4">
            <h3 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
              <DollarSign className="w-4 h-4 text-green-400" /> Plant Impact Summary
            </h3>
            {critSum && [
              { label: 'Total Equipment',    val: critSum.total_equipment },
              { label: 'Critical (P1)',       val: critSum.critical_count, color: 'text-red-400' },
              { label: 'High (P2)',           val: critSum.high_count,     color: 'text-orange-400' },
              { label: 'Avg Criticality',     val: critSum.average_criticality?.toFixed(1) + '%' },
              { label: 'Downtime Cost/hr',    val: '₹' + critSum.total_downtime_cost_per_hour?.toLocaleString('en-IN'), color: 'text-yellow-400' },
            ].map(({ label, val, color = 'text-white' }) => (
              <div key={label} className="flex justify-between text-xs py-1.5 border-b border-[#334155] last:border-0">
                <span className="text-slate-400">{label}</span>
                <span className={`font-mono font-bold ${color}`}>{val}</span>
              </div>
            ))}
          </Card>
        </div>
      </div>
    </div>
  );
}
