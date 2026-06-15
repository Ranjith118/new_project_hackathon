import { useState, useEffect, useCallback, useRef } from 'react';
import {
  Wrench, AlertTriangle, CheckCircle, Clock, RefreshCw,
  ChevronRight, ChevronLeft, Brain, Package, Shield,
  Zap, Play, BarChart3, Activity, TrendingUp, FileText,
  Settings, AlertCircle, Eye, Check, Wifi, WifiOff
} from 'lucide-react';
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';

const API = 'http://localhost:8000';
const get  = (u) => fetch(API + u).then(r => r.json()).catch(() => null);
const post = (u, b) => fetch(API + u, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(b) }).then(r => r.json()).catch(() => null);

const POLL_INTERVAL = 3000; // 3 seconds

/* ── helpers ─────────────────────────────────────────────── */
const priorityColor = (p) => ({ P1: '#EF4444', P2: '#F97316', P3: '#FBBF24', P4: '#10B981' })[p] || '#94A3B8';
const priorityLabel = (p) => ({ P1: 'Critical', P2: 'High', P3: 'Medium', P4: 'Low' })[p] || p;
const priorityBg    = (p) => ({ P1: 'bg-red-500/10 border-red-500/30', P2: 'bg-orange-500/10 border-orange-500/30', P3: 'bg-yellow-500/10 border-yellow-500/30', P4: 'bg-green-500/10 border-green-500/30' })[p] || 'bg-slate-500/10 border-slate-500/30';
const priorityBadge = (p) => ({ P1: 'bg-red-500/20 text-red-400 border-red-500/40', P2: 'bg-orange-500/20 text-orange-400 border-orange-500/40', P3: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/40', P4: 'bg-green-500/20 text-green-400 border-green-500/40' })[p] || 'bg-slate-500/20 text-slate-400';
const riskToP      = (r) => ({ critical: 'P1', high: 'P2', medium: 'P3', low: 'P4' })[r?.toLowerCase()] || 'P3';

const Card = ({ children, className = '' }) => (
  <div className={`bg-[#1E293B] border border-[#334155] rounded-xl ${className}`}>{children}</div>
);

/* ── Sensor value display badge ─────────────────────────────── */
function SensorBadge({ label, value, unit, status }) {
  const color = status === 'critical' ? 'text-red-400 border-red-500/40 bg-red-500/10'
              : status === 'warning'  ? 'text-yellow-400 border-yellow-500/40 bg-yellow-500/10'
              : 'text-green-400 border-green-500/40 bg-green-500/10';
  return (
    <div className={`flex flex-col items-center px-2 py-1 rounded border text-center ${color}`}>
      <span className="text-[9px] text-slate-400 uppercase">{label}</span>
      <span className="text-xs font-mono font-bold">{value != null ? Number(value).toFixed(1) : '—'}{unit}</span>
    </div>
  );
}

/* ── Plan Detail ─────────────────────────────────────────── */
function PlanDetail({ plan, onBack }) {
  const pc = priorityColor(plan.priority);
  const steps = plan.repair_guide?.steps || [];
  const spares = plan.spare_parts?.parts || [];
  const schedule = plan.maintenance_schedule || {};

  return (
    <div className="space-y-5">
      <button onClick={onBack} className="flex items-center gap-1 text-slate-400 hover:text-white text-sm transition-colors">
        <ChevronLeft className="w-4 h-4" /> Maintenance Recommendations
      </button>

      {/* Header */}
      <Card className="p-5 border-l-4" style={{ borderLeftColor: pc }}>
        <div className="flex items-start justify-between flex-wrap gap-4">
          <div>
            <div className="flex items-center gap-2 flex-wrap mb-1">
              <h2 className="text-xl font-heading font-bold text-white">{plan.equipment_name}</h2>
              <span className={`text-xs px-2 py-0.5 rounded border font-bold ${priorityBadge(plan.priority)}`}>
                {plan.priority} — {priorityLabel(plan.priority)}
              </span>
              <span className="text-xs text-slate-400 font-mono">{plan.plan_id?.slice(0, 8).toUpperCase()}</span>
            </div>
            <div className="text-slate-300 text-sm">Root Cause: <span className="text-orange-300 font-medium">{plan.root_cause}</span></div>
          </div>
          <div className="grid grid-cols-3 gap-3 text-center">
            {[
              { label: 'Downtime',    val: plan.estimated_total_downtime + 'h', color: pc },
              { label: 'Est Cost',    val: plan.estimated_total_cost ? '₹'+plan.estimated_total_cost?.toLocaleString('en-IN') : '—', color: '#FBBF24' },
              { label: 'Repair Time', val: plan.repair_guide?.estimated_total_time_minutes ? Math.round(plan.repair_guide.estimated_total_time_minutes / 60) + 'h' : '—', color: '#3B82F6' },
            ].map(({ label, val, color }) => (
              <div key={label} className="bg-[#0F1419] rounded-lg p-3 border border-[#334155]">
                <div className="text-lg font-bold font-mono" style={{ color }}>{val}</div>
                <div className="text-[10px] text-slate-500 mt-0.5">{label}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Live sensor readings snapshot */}
        {plan._sensorSnapshot && Object.keys(plan._sensorSnapshot).length > 0 && (
          <div className="mt-4 p-3 bg-blue-500/5 border border-blue-500/20 rounded-xl">
            <div className="text-xs text-blue-400 font-semibold mb-2 uppercase tracking-wider flex items-center gap-1">
              <Activity className="w-3 h-3" /> Sensor Readings at Time of Analysis
            </div>
            <div className="flex flex-wrap gap-2">
              {plan._sensorSnapshot.temperature != null && <SensorBadge label="Temp" value={plan._sensorSnapshot.temperature} unit="°C" status={plan._sensorSnapshot._status?.temperature} />}
              {plan._sensorSnapshot.vibration   != null && <SensorBadge label="Vib"  value={plan._sensorSnapshot.vibration}   unit="mm/s" status={plan._sensorSnapshot._status?.vibration} />}
              {plan._sensorSnapshot.current     != null && <SensorBadge label="Curr" value={plan._sensorSnapshot.current}     unit="A" status={plan._sensorSnapshot._status?.current} />}
              {plan._sensorSnapshot.pressure    != null && <SensorBadge label="Press" value={plan._sensorSnapshot.pressure}   unit="bar" status={plan._sensorSnapshot._status?.pressure} />}
              {plan._sensorSnapshot.rpm         != null && <SensorBadge label="RPM"  value={plan._sensorSnapshot.rpm}         unit="" status={plan._sensorSnapshot._status?.rpm} />}
            </div>
            {plan._generatedAt && (
              <div className="text-[10px] text-slate-500 mt-2">Generated: {new Date(plan._generatedAt).toLocaleTimeString()}</div>
            )}
          </div>
        )}

        {/* Immediate actions */}
        {plan.immediate_actions?.length > 0 && (
          <div className="mt-4 p-3 bg-red-500/5 border border-red-500/20 rounded-xl">
            <div className="text-xs text-red-400 font-semibold mb-2 uppercase tracking-wider">⚠ Immediate Actions Required</div>
            <div className="flex flex-wrap gap-2">
              {plan.immediate_actions.map((a, i) => (
                <span key={i} className="text-xs px-2.5 py-1 bg-red-500/10 border border-red-500/20 text-red-300 rounded-lg">
                  {i+1}. {a}
                </span>
              ))}
            </div>
          </div>
        )}
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        {/* Step-by-step repair guide */}
        {steps.length > 0 && (
          <Card className="p-5">
            <h3 className="font-heading font-semibold text-white mb-4 flex items-center gap-2">
              <Wrench className="w-4 h-4 text-orange-400" /> Repair Procedure — {plan.repair_guide?.repair_type?.replace(/_/g,' ')}
              <span className="text-xs text-slate-500 ml-auto">{plan.repair_guide?.estimated_total_time_minutes} min</span>
            </h3>
            <div className="space-y-3 max-h-[500px] overflow-y-auto pr-1">
              {steps.map((step) => (
                <div key={step.step_number} className="p-3 bg-[#0F1419] rounded-lg border border-[#334155]">
                  <div className="flex items-start gap-3">
                    <div className="w-7 h-7 rounded-lg bg-orange-500/10 border border-orange-500/20 flex items-center justify-center flex-shrink-0 text-xs font-bold text-orange-400">
                      {step.step_number}
                    </div>
                    <div className="flex-1">
                      <div className="text-white text-sm font-medium">{step.action}</div>
                      {step.description && <div className="text-xs text-slate-400 mt-0.5">{step.description}</div>}
                      <div className="flex flex-wrap gap-2 mt-2">
                        {step.safety_requirements?.map((s, j) => (
                          <span key={j} className="text-[10px] px-1.5 py-0.5 bg-yellow-500/10 border border-yellow-500/20 text-yellow-400 rounded">{s}</span>
                        ))}
                        {step.tools_required?.map((t, j) => (
                          <span key={j} className="text-[10px] px-1.5 py-0.5 bg-blue-500/10 border border-blue-500/20 text-blue-400 rounded">{t}</span>
                        ))}
                      </div>
                      <div className="text-[10px] text-slate-500 mt-1">⏱ {step.estimated_time_minutes} min · Source: {step.source}</div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </Card>
        )}

        {/* Spare parts + next steps */}
        <div className="space-y-4">
          {spares.length > 0 && (
            <Card className="p-4">
              <h3 className="font-heading font-semibold text-white mb-3 flex items-center gap-2">
                <Package className="w-4 h-4 text-yellow-400" /> Required Spare Parts
              </h3>
              <div className="space-y-2">
                {spares.map((p, i) => {
                  const ok = (p.quantity_required || 1) <= (p.stock_available || 0);
                  return (
                    <div key={i} className="flex items-center justify-between p-2.5 bg-[#0F1419] rounded-lg border border-[#334155]">
                      <div>
                        <div className="text-white text-xs font-medium">{p.part_name}</div>
                        <div className="text-[10px] text-slate-400">P/N: {p.part_number} · {p.urgency} · Lead: {p.lead_time_days}d</div>
                        {p.reason && <div className="text-[10px] text-slate-500">{p.reason?.slice(0, 60)}</div>}
                      </div>
                      <div className="text-right ml-3 flex-shrink-0">
                        <div className="text-sm font-mono font-bold text-white">×{p.quantity_required || 1}</div>
                        {p.estimated_cost && <div className="text-[10px] text-slate-400">₹{p.estimated_cost.toLocaleString('en-IN')}</div>}
                        <div className={`text-[10px] px-1.5 py-0.5 rounded border mt-0.5 ${ok ? 'bg-green-500/15 text-green-400 border-green-500/30' : 'bg-red-500/15 text-red-400 border-red-500/30'}`}>
                          {ok ? 'Available' : 'Order Now'}
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </Card>
          )}

          {/* Next steps */}
          {plan.next_steps?.length > 0 && (
            <Card className="p-4">
              <h3 className="font-heading font-semibold text-white mb-3 flex items-center gap-2">
                <CheckCircle className="w-4 h-4 text-green-400" /> Next Steps
              </h3>
              {plan.next_steps.map((step, i) => (
                <div key={i} className="flex items-start gap-2 p-2 bg-green-500/5 border border-green-500/15 rounded-lg mb-1.5 last:mb-0">
                  <span className="text-green-400 font-mono text-xs mt-0.5 flex-shrink-0">{i+1}.</span>
                  <span className="text-xs text-slate-300">{step}</span>
                </div>
              ))}
            </Card>
          )}

          {/* Safety warnings */}
          {plan.repair_guide?.safety_warnings?.length > 0 && (
            <Card className="p-4">
              <h3 className="font-heading font-semibold text-white mb-3 flex items-center gap-2">
                <Shield className="w-4 h-4 text-yellow-400" /> Safety Requirements
              </h3>
              {plan.repair_guide.safety_warnings.map((w, i) => (
                <div key={i} className="flex items-start gap-2 p-2 bg-yellow-500/5 border border-yellow-500/15 rounded-lg mb-1.5 last:mb-0">
                  <AlertTriangle className="w-3.5 h-3.5 text-yellow-400 flex-shrink-0 mt-0.5" />
                  <span className="text-xs text-slate-300">{w}</span>
                </div>
              ))}
            </Card>
          )}

          {/* Post-repair checks */}
          {plan.repair_guide?.post_repair_checks?.length > 0 && (
            <Card className="p-4">
              <h3 className="font-heading font-semibold text-white mb-3 flex items-center gap-2">
                <Activity className="w-4 h-4 text-blue-400" /> Post-Repair Verification
              </h3>
              {plan.repair_guide.post_repair_checks.map((c, i) => (
                <div key={i} className="flex items-center gap-2 text-xs text-slate-300 py-1 border-b border-[#334155] last:border-0">
                  <CheckCircle className="w-3 h-3 text-blue-400 flex-shrink-0" />{c}
                </div>
              ))}
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════
   MAIN PAGE
═══════════════════════════════════════════════════════════ */
export default function MaintenanceRecommendations() {
  const [equipment,   setEquipment]   = useState([]);
  const [plans,       setPlans]       = useState([]);
  const [ranking,     setRanking]     = useState([]);
  const [schedule,    setSchedule]    = useState(null);
  const [liveStatus,  setLiveStatus]  = useState({});   // { equipmentName: sensorRow }
  const [loading,     setLoading]     = useState(true);
  const [generating,  setGenerating]  = useState({});
  const [selected,    setSelected]    = useState(null);
  const [filterPri,   setFilterPri]   = useState('');
  const [liveOnline,  setLiveOnline]  = useState(false);
  const [lastPoll,    setLastPoll]    = useState(null);
  const [autoRefresh, setAutoRefresh] = useState(true);

  // Refs so interval callbacks always see latest state
  const plansRef    = useRef(plans);
  const rankingRef  = useRef(ranking);
  const generatingRef = useRef(generating);
  useEffect(() => { plansRef.current = plans; },     [plans]);
  useEffect(() => { rankingRef.current = ranking; }, [ranking]);
  useEffect(() => { generatingRef.current = generating; }, [generating]);

  // ── Initial load (equipment list, ranking, schedule) ──────
  const load = useCallback(async () => {
    const [eq, rank, sched] = await Promise.all([
      get('/api/equipment/'),
      get('/api/decision-support/equipment-ranking'),
      get('/api/recommendation/schedule/latest'),
    ]);
    setEquipment(Array.isArray(eq) ? eq : []);
    setRanking(rank?.rankings || []);
    if (sched?.tasks) setSchedule(sched);
    setLoading(false);
  }, []);

  useEffect(() => { load(); }, [load]);

  // ── Derive root cause from sensor status ──────────────────
  const deriveRootCause = (sensorRow) => {
    if (!sensorRow?.sensors) return 'General Maintenance';
    const criticalSensors = sensorRow.sensors.filter(s => s.status === 'critical');
    const warningSensors  = sensorRow.sensors.filter(s => s.status === 'warning');
    const worst = criticalSensors[0] || warningSensors[0];
    if (!worst) return 'Preventive Maintenance';
    switch (worst.sensor_type) {
      case 'temperature': return 'Thermal Overload';
      case 'vibration':   return 'Bearing Wear / Imbalance';
      case 'current':     return 'Electrical Overload';
      case 'pressure':    return 'Pressure Deviation';
      case 'rpm':         return 'Speed Anomaly';
      default:            return 'Sensor Anomaly';
    }
  };

  // ── Map health score to a risk level string ───────────────
  const healthToRisk = (score) => {
    if (score < 40) return 'critical';
    if (score < 60) return 'high';
    if (score < 80) return 'medium';
    return 'low';
  };

  // ── Generate / refresh one plan from live sensor data ─────
  const generatePlanFromSensor = useCallback(async (sensorRow) => {
    const eqName = sensorRow.equipment_name;
    if (generatingRef.current[eqName]) return; // already in flight

    // Build sensor reading map from sensorRow.sensors array
    const rdg = {};
    const sensorStatus = {};
    if (Array.isArray(sensorRow.sensors)) {
      for (const s of sensorRow.sensors) {
        rdg[s.sensor_type] = s.value;
        sensorStatus[s.sensor_type] = s.status;
      }
    }

    const rootCause   = deriveRootCause(sensorRow);
    const healthScore = sensorRow.health_score ?? 70;
    const risk        = sensorRow.risk_level   ?? 'medium';

    // Find ranking data for this equipment
    const rankData = rankingRef.current.find(r => r.equipment_name === eqName);
    const failProb = rankData ? rankData.failure_probability : (100 - healthScore) / 100;
    const rulDays  = rankData?.rul_days ?? 30;

    setGenerating(g => ({ ...g, [eqName]: true }));

    const body = {
      equipment:           eqName,
      equipment_type:      'motor',
      root_cause:          rootCause,
      failure_probability: parseFloat(failProb),
      rul_days:            parseInt(rulDays),
      health_score:        parseInt(healthScore),
      risk_level:          healthToRisk(healthScore),
      anomaly_detected:    healthScore < 70,
      temperature:         rdg.temperature  ?? null,
      vibration:           rdg.vibration    ?? null,
      current:             rdg.current      ?? null,
      pressure:            rdg.pressure     ?? null,
      rpm:                 rdg.rpm          ?? null,
    };

    const plan = await post('/api/recommendation/complete-plan', body);

    if (plan) {
      const enriched = {
        ...plan,
        _sensorSnapshot: { ...rdg, _status: sensorStatus },
        _generatedAt: new Date().toISOString(),
        _healthScore: healthScore,
        _riskLevel:   risk,
      };
      setPlans(prev => [enriched, ...prev.filter(p => p.equipment_name !== eqName)]);
    }

    setGenerating(g => { const n = { ...g }; delete n[eqName]; return n; });
  }, []);

  // ── Poll: simulate new readings, fetch live-status, regenerate plans ──
  const pollSensors = useCallback(async () => {
    // 1. Trigger sensor simulation to generate fresh data
    await post('/api/sensor-data/simulate-all', {});

    // 2. Fetch latest live status for all equipment
    const status = await get('/api/sensor-data/live-status');
    if (!status?.equipment) {
      setLiveOnline(false);
      return;
    }

    setLiveOnline(true);
    setLastPoll(new Date());

    // Build map: name → row
    const statusMap = {};
    for (const row of status.equipment) {
      statusMap[row.equipment_name] = row;
    }
    setLiveStatus(statusMap);

    // 3. Auto-generate / refresh plans for equipment that need attention
    //    Priority: critical/high health score first, max 3 concurrent to avoid flooding
    const needsUpdate = status.equipment
      .filter(row => {
        const existing = plansRef.current.find(p => p.equipment_name === row.equipment_name);
        if (!existing) return true; // never generated
        // Refresh if plan is older than 15 seconds or health changed significantly
        const age = (Date.now() - new Date(existing._generatedAt || 0)) / 1000;
        const healthChanged = Math.abs((existing._healthScore ?? 100) - row.health_score) > 8;
        return age > 15 || healthChanged;
      })
      .sort((a, b) => a.health_score - b.health_score) // worst health first
      .slice(0, 3);

    for (const row of needsUpdate) {
      generatePlanFromSensor(row);
    }
  }, [generatePlanFromSensor]);

  // ── 3-second polling interval ─────────────────────────────
  useEffect(() => {
    if (!autoRefresh) return;

    // Run immediately on mount / when turned on
    pollSensors();

    const id = setInterval(pollSensors, POLL_INTERVAL);
    return () => clearInterval(id);
  }, [autoRefresh, pollSensors]);

  // ── Manual "generate all" ──────────────────────────────────
  const generateAll = async () => {
    const status = await get('/api/sensor-data/live-status');
    const rows = status?.equipment || [];
    if (rows.length === 0) {
      // Fallback: use ranking data without live sensors
      for (const eq of rankingRef.current.slice(0, 6)) {
        await generatePlanFromSensor({
          equipment_name: eq.equipment_name,
          health_score: 100 - (eq.failure_probability * 100),
          risk_level: eq.priority_level === 'P1' ? 'critical' : eq.priority_level === 'P2' ? 'high' : 'medium',
          sensors: [],
        });
      }
    } else {
      for (const row of rows) {
        generatePlanFromSensor(row);
      }
    }
  };

  // ── Manual generate for one equipment ─────────────────────
  const generatePlan = async (eqName) => {
    const row = liveStatus[eqName];
    if (row) {
      generatePlanFromSensor(row);
    } else {
      const rankData = rankingRef.current.find(r => r.equipment_name === eqName);
      generatePlanFromSensor({
        equipment_name: eqName,
        health_score: rankData ? Math.round(100 - rankData.failure_probability * 100) : 70,
        risk_level: 'medium',
        sensors: [],
      });
    }
  };

  const filtered = plans.filter(p => !filterPri || p.priority === filterPri);

  // Analytics
  const byPriority = ['P1','P2','P3','P4'].map(p => ({
    name: priorityLabel(p), count: plans.filter(r => r.priority === p).length
  }));
  const PIE_COLORS = ['#EF4444','#F97316','#FBBF24','#10B981'];

  if (selected) return <div className="p-6"><PlanDetail plan={selected} onBack={() => setSelected(null)} /></div>;

  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-2xl font-heading font-bold text-white flex items-center gap-2">
            <Wrench className="w-6 h-6 text-orange-500" /> Maintenance Recommendations
          </h1>
          <p className="text-slate-400 text-sm mt-0.5 flex items-center gap-2">
            AI-powered maintenance planning · Live sensor-driven recommendations
            {liveOnline ? (
              <span className="flex items-center gap-1 text-green-400 text-xs">
                <Wifi className="w-3 h-3" /> Live · {lastPoll ? lastPoll.toLocaleTimeString() : ''}
              </span>
            ) : (
              <span className="flex items-center gap-1 text-slate-500 text-xs">
                <WifiOff className="w-3 h-3" /> Connecting...
              </span>
            )}
          </p>
        </div>
        <div className="flex gap-2 flex-wrap items-center">
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
          <button onClick={generateAll}
            className="flex items-center gap-1.5 px-3 py-2 bg-orange-500 hover:bg-orange-600 text-white text-sm rounded-lg transition-colors">
            <Zap className="w-4 h-4" /> Generate All Plans
          </button>
          <button onClick={() => { load(); pollSensors(); }}
            className="p-2 bg-[#1E293B] border border-[#334155] hover:border-orange-500/40 text-slate-400 hover:text-white rounded-lg transition-all">
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Live Sensor Feed */}
      {Object.keys(liveStatus).length > 0 && (
        <Card className="p-4 border-blue-500/20 bg-blue-500/5">
          <div className="flex items-center gap-2 mb-3">
            <Activity className="w-4 h-4 text-blue-400 animate-pulse" />
            <span className="text-sm font-semibold text-blue-400">Live Sensor Feed — updating every 3s</span>
            <span className="text-xs text-slate-500 ml-auto">{Object.keys(liveStatus).length} machines</span>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-2">
            {Object.values(liveStatus)
              .sort((a, b) => a.health_score - b.health_score)
              .slice(0, 6)
              .map((row, i) => {
                const critSensors = row.sensors?.filter(s => s.status !== 'normal') || [];
                const statusColor = row.health_score < 40 ? 'border-red-500/30 bg-red-500/5'
                                  : row.health_score < 60 ? 'border-orange-500/30 bg-orange-500/5'
                                  : row.health_score < 80 ? 'border-yellow-500/30 bg-yellow-500/5'
                                  : 'border-green-500/20 bg-green-500/5';
                const scoreColor = row.health_score < 40 ? 'text-red-400'
                                 : row.health_score < 60 ? 'text-orange-400'
                                 : row.health_score < 80 ? 'text-yellow-400'
                                 : 'text-green-400';
                return (
                  <div key={i} className={`rounded-lg border p-3 ${statusColor}`}>
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-xs font-semibold text-white truncate">{row.equipment_name}</span>
                      <span className={`text-xs font-bold font-mono ${scoreColor}`}>{row.health_score}%</span>
                    </div>
                    <div className="flex flex-wrap gap-1">
                      {row.sensors?.map((s, j) => (
                        <span key={j} className={`text-[9px] px-1 py-0.5 rounded border font-mono ${
                          s.status === 'critical' ? 'bg-red-500/10 border-red-500/30 text-red-400'
                          : s.status === 'warning' ? 'bg-yellow-500/10 border-yellow-500/30 text-yellow-400'
                          : 'bg-slate-500/10 border-slate-500/20 text-slate-400'
                        }`}>
                          {s.sensor_type.slice(0,4).toUpperCase()} {Number(s.value).toFixed(1)}
                        </span>
                      ))}
                    </div>
                    {critSensors.length > 0 && (
                      <div className="text-[9px] text-red-400 mt-1">⚠ {critSensors.map(s => s.sensor_type).join(', ')} anomaly</div>
                    )}
                  </div>
                );
              })}
          </div>
        </Card>
      )}

      {/* KPIs */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
        {[
          { label: 'Total Plans',     val: plans.length,                                           color: 'text-white',      bg: 'bg-slate-500/10 border-slate-500/20' },
          { label: 'Critical (P1)',   val: plans.filter(p => p.priority === 'P1').length,          color: 'text-red-400',    bg: 'bg-red-500/10 border-red-500/20' },
          { label: 'High (P2)',       val: plans.filter(p => p.priority === 'P2').length,          color: 'text-orange-400', bg: 'bg-orange-500/10 border-orange-500/20' },
          { label: 'Total Downtime',  val: plans.reduce((a, p) => a + (p.estimated_total_downtime || 0), 0).toFixed(0) + 'h', color: 'text-yellow-400', bg: 'bg-yellow-500/10 border-yellow-500/20' },
          { label: 'Equipment Ranked',val: ranking.length,                                         color: 'text-green-400',  bg: 'bg-green-500/10 border-green-500/20' },
        ].map(({ label, val, color, bg }) => (
          <div key={label} className={`rounded-xl border p-3 text-center ${bg}`}>
            <div className={`text-2xl font-heading font-bold ${color}`}>{val}</div>
            <div className="text-[10px] text-slate-400 mt-1">{label}</div>
          </div>
        ))}
      </div>

      {/* Generating indicator */}
      {Object.keys(generating).length > 0 && (
        <Card className="p-3 border-orange-500/20 bg-orange-500/5">
          <div className="flex items-center gap-2">
            <Brain className="w-4 h-4 text-orange-400 animate-pulse" />
            <span className="text-sm text-orange-400">Generating plans for: {Object.keys(generating).join(', ')}...</span>
          </div>
        </Card>
      )}

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        {/* Left: Plans list */}
        <div className="xl:col-span-2 space-y-4">
          {/* Filters */}
          <div className="flex gap-2 flex-wrap">
            {['','P1','P2','P3','P4'].map(p => (
              <button key={p} onClick={() => setFilterPri(p)}
                className={`px-3 py-1.5 text-xs rounded-lg border transition-all ${
                  filterPri === p ? (p ? `${priorityBadge(p)} font-semibold` : 'bg-orange-500 text-white border-orange-500') : 'border-[#334155] text-slate-400 hover:text-white'
                }`}>
                {p ? priorityLabel(p) : 'All'}
              </button>
            ))}
            <span className="text-xs text-slate-500 self-center ml-auto">{filtered.length} plans</span>
          </div>

          {loading ? (
            <div className="flex items-center justify-center py-16">
              <div className="w-8 h-8 border-2 border-orange-500 border-t-transparent rounded-full animate-spin" />
            </div>
          ) : filtered.length === 0 ? (
            <Card className="p-10 text-center">
              <Wrench className="w-12 h-12 text-slate-600 mx-auto mb-3" />
              <p className="text-slate-400 mb-1">No maintenance plans yet</p>
              <p className="text-slate-500 text-xs mb-4">
                {autoRefresh ? 'Plans are being generated from live sensor data...' : 'Enable auto-refresh or click Generate All Plans'}
              </p>
              <button onClick={generateAll} className="px-4 py-2 bg-orange-500 hover:bg-orange-600 text-white text-sm rounded-lg transition-colors">
                Generate Plans Now
              </button>
            </Card>
          ) : (
            filtered.map((plan, i) => {
              const pc = priorityColor(plan.priority);
              const isStale = plan._generatedAt && (Date.now() - new Date(plan._generatedAt)) > 20000;
              return (
                <Card key={i} className={`p-4 border-l-4 cursor-pointer hover:border-orange-500/30 transition-all ${priorityBg(plan.priority)}`}
                  style={{ borderLeftColor: pc }} onClick={() => setSelected(plan)}>
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex items-center gap-3 flex-1 min-w-0">
                      <div className="w-11 h-11 rounded-xl flex items-center justify-center flex-shrink-0 border" style={{ backgroundColor: pc + '20', borderColor: pc + '40' }}>
                        <span className="text-sm font-bold" style={{ color: pc }}>{plan.priority}</span>
                      </div>
                      <div className="min-w-0 flex-1">
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className="text-white font-semibold text-sm">{plan.equipment_name}</span>
                          <span className={`text-xs px-2 py-0.5 rounded border ${priorityBadge(plan.priority)}`}>{priorityLabel(plan.priority)}</span>
                          {plan._healthScore != null && (
                            <span className={`text-[10px] px-1.5 py-0.5 rounded border ${
                              plan._healthScore < 40 ? 'text-red-400 border-red-500/30 bg-red-500/10'
                              : plan._healthScore < 70 ? 'text-yellow-400 border-yellow-500/30 bg-yellow-500/10'
                              : 'text-green-400 border-green-500/30 bg-green-500/10'
                            }`}>
                              Health: {plan._healthScore}%
                            </span>
                          )}
                        </div>
                        <div className="text-xs text-orange-300 mt-0.5">RC: {plan.root_cause}</div>
                        <div className="flex items-center gap-3 mt-1 text-[10px] text-slate-400">
                          <span>⏱ {plan.estimated_total_downtime}h downtime</span>
                          {plan.estimated_total_cost && <span>💰 ₹{plan.estimated_total_cost?.toLocaleString('en-IN')}</span>}
                          {plan.repair_guide?.steps?.length > 0 && <span>📋 {plan.repair_guide.steps.length} steps</span>}
                          {plan.spare_parts?.parts?.length > 0 && <span>📦 {plan.spare_parts.parts.length} parts</span>}
                        </div>
                      </div>
                    </div>
                    <div className="flex flex-col items-end gap-1 flex-shrink-0">
                      <ChevronRight className="w-4 h-4 text-slate-500" />
                      <span className={`text-[10px] ${isStale ? 'text-yellow-500' : 'text-slate-500'}`}>
                        {plan._generatedAt ? new Date(plan._generatedAt).toLocaleTimeString() : ''}
                      </span>
                    </div>
                  </div>

                  {/* Sensor snapshot badges */}
                  {plan._sensorSnapshot && Object.keys(plan._sensorSnapshot).filter(k => k !== '_status').length > 0 && (
                    <div className="mt-2 flex flex-wrap gap-1">
                      {['temperature','vibration','current','pressure','rpm'].map(key => {
                        const val = plan._sensorSnapshot[key];
                        const st  = plan._sensorSnapshot._status?.[key];
                        if (val == null) return null;
                        const cls = st === 'critical' ? 'text-red-400 border-red-500/30 bg-red-500/5'
                                  : st === 'warning'  ? 'text-yellow-400 border-yellow-500/30 bg-yellow-500/5'
                                  : 'text-slate-400 border-slate-500/20 bg-slate-500/5';
                        return (
                          <span key={key} className={`text-[9px] px-1.5 py-0.5 rounded border font-mono ${cls}`}>
                            {key.slice(0,4).toUpperCase()} {Number(val).toFixed(1)}
                          </span>
                        );
                      })}
                    </div>
                  )}

                  {/* Immediate actions preview */}
                  {plan.immediate_actions?.length > 0 && (
                    <div className="mt-2 flex flex-wrap gap-1.5">
                      {plan.immediate_actions.slice(0, 3).map((a, j) => (
                        <span key={j} className="text-[10px] px-2 py-0.5 bg-[#0F1419] border border-[#334155] text-slate-300 rounded">{a}</span>
                      ))}
                    </div>
                  )}
                </Card>
              );
            })
          )}

          {/* Quick generate from ranking */}
          {ranking.length > 0 && (
            <Card className="p-4">
              <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">Generate / Refresh Plan for Equipment</h3>
              <div className="flex flex-wrap gap-2">
                {ranking.slice(0, 8).map((eq, i) => {
                  const isGenerating = generating[eq.equipment_name];
                  const hasPlan = plans.some(p => p.equipment_name === eq.equipment_name);
                  return (
                    <button key={i} disabled={isGenerating}
                      onClick={() => generatePlan(eq.equipment_name)}
                      className={`flex items-center gap-1.5 px-3 py-1.5 text-xs rounded-lg border transition-all disabled:opacity-50 ${
                        hasPlan ? 'border-orange-500/30 text-orange-400 bg-orange-500/5' : 'border-[#334155] text-slate-300 hover:text-white hover:border-orange-500/40'
                      }`}>
                      {isGenerating ? <RefreshCw className="w-3 h-3 animate-spin" /> : <Play className="w-3 h-3 text-orange-400" />}
                      {eq.equipment_name} [{eq.priority_level}]
                    </button>
                  );
                })}
              </div>
            </Card>
          )}
        </div>

        {/* Right: Ranking + Analytics + Schedule */}
        <div className="space-y-4">
          {/* Plant Priority Ranking */}
          {ranking.length > 0 && (
            <Card className="p-4">
              <h3 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
                <TrendingUp className="w-4 h-4 text-orange-400" /> Plant Priority Ranking
              </h3>
              <div className="space-y-2">
                {ranking.slice(0, 8).map((eq, i) => {
                  const pc = priorityColor(eq.priority_level || 'P4');
                  const live = liveStatus[eq.equipment_name];
                  return (
                    <div key={i} className="flex items-center gap-2 py-1.5 border-b border-[#334155] last:border-0">
                      <div className={`w-6 h-6 rounded flex items-center justify-center text-xs font-bold flex-shrink-0 ${
                        i === 0 ? 'bg-red-500/20 text-red-400' : i === 1 ? 'bg-orange-500/20 text-orange-400' : i === 2 ? 'bg-yellow-500/20 text-yellow-400' : 'bg-slate-500/20 text-slate-400'
                      }`}>{eq.rank}</div>
                      <div className="flex-1 min-w-0">
                        <div className="text-xs text-white truncate">{eq.equipment_name}</div>
                        <div className="text-[10px] text-slate-500">
                          Fail: {(eq.failure_probability * 100).toFixed(0)}% · RUL: {eq.rul_days}d
                          {live && <span className={`ml-1 ${live.health_score < 60 ? 'text-red-400' : 'text-green-400'}`}>· Live: {live.health_score}%</span>}
                        </div>
                      </div>
                      <span className="text-xs px-1.5 py-0.5 rounded border font-mono flex-shrink-0" style={{ color: pc, borderColor: pc + '40', backgroundColor: pc + '15' }}>
                        {eq.priority_level}
                      </span>
                    </div>
                  );
                })}
              </div>
            </Card>
          )}

          {/* Plans by priority chart */}
          {plans.length > 0 && (
            <Card className="p-4">
              <h3 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
                <BarChart3 className="w-4 h-4 text-orange-400" /> Plans by Priority
              </h3>
              <ResponsiveContainer width="100%" height={140}>
                <BarChart data={byPriority} margin={{ left: -20 }}>
                  <XAxis dataKey="name" tick={{ fontSize: 10, fill: '#94A3B8' }} />
                  <YAxis tick={{ fontSize: 10, fill: '#64748B' }} />
                  <Tooltip contentStyle={{ background: '#1E293B', border: '1px solid #334155', fontSize: 11 }} />
                  <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                    {byPriority.map((_, i) => <Cell key={i} fill={PIE_COLORS[i]} />)}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </Card>
          )}

          {/* Maintenance schedule */}
          {schedule && (
            <Card className="p-4">
              <h3 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
                <Clock className="w-4 h-4 text-blue-400" /> Maintenance Schedule
              </h3>
              <div className="space-y-2 max-h-52 overflow-y-auto">
                {schedule.tasks?.slice(0, 6).map((t, i) => (
                  <div key={i} className="flex items-start gap-2 p-2 bg-[#0F1419] rounded border border-[#334155]">
                    <span className={`text-[10px] px-1.5 py-0.5 rounded border flex-shrink-0 ${priorityBadge(t.priority)}`}>{t.priority}</span>
                    <div className="min-w-0 flex-1">
                      <div className="text-xs text-white truncate">{t.equipment_name}</div>
                      <div className="text-[10px] text-slate-400">{t.maintenance_type} · {t.scheduled_date?.slice(0, 10)}</div>
                    </div>
                    <span className="text-[10px] text-slate-500 flex-shrink-0">{t.estimated_duration_hours}h</span>
                  </div>
                ))}
              </div>
              <div className="mt-3 pt-3 border-t border-[#334155] flex justify-between text-xs text-slate-400">
                <span>Total tasks: {schedule.total_tasks}</span>
                <span>Downtime: {schedule.total_downtime_hours}h</span>
              </div>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}
