import { useState, useEffect, useCallback, useRef } from 'react';
import {
  Activity, AlertTriangle, CheckCircle, XCircle, Clock,
  TrendingUp, TrendingDown, RefreshCw, AlertCircle,
  Wrench, Calendar, Zap, Wifi, WifiOff
} from 'lucide-react';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, AreaChart, Area, Cell, BarChart, Bar
} from 'recharts';
import {
  getPredictiveDashboard, getEquipmentPredictions,
  getWarnings, trainFailureModel, trainRULModel
} from '../../services/predictionApi';

const API = 'http://localhost:8000';
const get  = (url) => fetch(API + url).then(r => r.json()).catch(() => null);
const post = (url) => fetch(API + url, { method:'POST' }).then(r => r.json()).catch(() => null);

/* ── helpers ───────────────────────────────────────────── */
const riskColors = {
  Critical: { bg:'bg-red-500/20',    text:'text-red-400',    border:'border-red-500/50'    },
  High:     { bg:'bg-orange-500/20', text:'text-orange-400', border:'border-orange-500/50' },
  Medium:   { bg:'bg-yellow-500/20', text:'text-yellow-400', border:'border-yellow-500/50' },
  Low:      { bg:'bg-green-500/20',  text:'text-green-400',  border:'border-green-500/50'  },
};

const RiskBadge = ({ level }) => {
  const s = riskColors[level] || riskColors.Low;
  return (
    <span className={`px-2 py-1 rounded text-xs font-medium ${s.bg} ${s.text} border ${s.border}`}>
      {level}
    </span>
  );
};

const PredictionCard = ({ equipment }) => {
  const fColor = equipment.failure_probability >= 70 ? 'text-red-400'
               : equipment.failure_probability >= 50 ? 'text-orange-400'
               : 'text-green-400';
  return (
    <div className="bg-[#1E293B] border border-[#334155] rounded-xl p-4 hover:border-orange-500/30 transition-all">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <Activity className="w-4 h-4 text-orange-500" />
          <span className="font-medium text-white text-sm">{equipment.equipment_name}</span>
        </div>
        <RiskBadge level={equipment.risk_level} />
      </div>
      <div className="grid grid-cols-3 gap-3">
        <div>
          <p className="text-[10px] text-slate-400 mb-1">Failure Prob</p>
          <p className={`text-xl font-bold font-mono ${fColor}`}>{equipment.failure_probability}%</p>
        </div>
        <div>
          <p className="text-[10px] text-slate-400 mb-1">RUL</p>
          <p className={`text-xl font-bold font-mono ${equipment.rul_days < 15 ? 'text-red-400' : equipment.rul_days < 30 ? 'text-orange-400' : 'text-white'}`}>
            {equipment.rul_days}<span className="text-xs"> d</span>
          </p>
        </div>
        <div>
          <p className="text-[10px] text-slate-400 mb-1">Health</p>
          <p className={`text-xl font-bold font-mono ${equipment.health_score >= 80 ? 'text-green-400' : equipment.health_score >= 60 ? 'text-yellow-400' : 'text-red-400'}`}>
            {equipment.health_score}%
          </p>
        </div>
      </div>
      <div className="mt-3 pt-3 border-t border-[#334155] flex items-center justify-between text-xs">
        <span className={`px-2 py-0.5 rounded capitalize ${
          equipment.degradation_level === 'healthy'              ? 'bg-green-500/20 text-green-400'  :
          equipment.degradation_level === 'slightly_degraded'   ? 'bg-yellow-500/20 text-yellow-400' :
          equipment.degradation_level === 'moderately_degraded' ? 'bg-orange-500/20 text-orange-400' :
          'bg-red-500/20 text-red-400'
        }`}>
          {equipment.degradation_level?.replace(/_/g,' ')}
        </span>
        <span className="text-slate-500 font-mono">{new Date(equipment.last_updated).toLocaleTimeString()}</span>
      </div>
    </div>
  );
};

const WarningCard = ({ warning }) => {
  const Icon = warning.level === 'critical' ? XCircle
             : warning.level === 'high'     ? AlertTriangle
             : warning.level === 'medium'   ? AlertCircle
             : Activity;
  const color = warning.level === 'critical' ? 'text-red-400'
              : warning.level === 'high'     ? 'text-orange-400'
              : warning.level === 'medium'   ? 'text-yellow-400'
              : 'text-blue-400';
  return (
    <div className="bg-[#1E293B] border border-[#334155] rounded-xl p-3">
      <div className="flex items-start gap-3">
        <Icon className={`w-4 h-4 flex-shrink-0 mt-0.5 ${color}`} />
        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between mb-1">
            <span className="font-medium text-white text-xs">{warning.equipment_name}</span>
            <span className={`text-[10px] font-semibold uppercase ${color}`}>{warning.level}</span>
          </div>
          <p className="text-xs text-slate-400">{warning.reason}</p>
          <div className="flex items-center gap-3 mt-1.5 text-[10px] text-slate-500">
            {warning.failure_probability != null && (
              <span>Fail: {(warning.failure_probability * 100).toFixed(0)}%</span>
            )}
            {warning.rul_days != null && <span>RUL: {warning.rul_days}d</span>}
          </div>
        </div>
      </div>
    </div>
  );
};

/* ── chart tooltip ─────────────────────────────────────── */
const ChartTip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-[#0F1419] border border-[#334155] rounded-lg p-2.5 text-xs shadow-xl">
      <p className="text-slate-400 mb-1">{label}</p>
      {payload.map((e, i) => (
        <div key={i} className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full" style={{ background:e.color }} />
          <span className="text-slate-300">{e.name}:</span>
          <span className="font-mono text-orange-400">{Number(e.value).toFixed(1)}</span>
        </div>
      ))}
    </div>
  );
};

/* ═══════════════════════════════════════════════════════ */
export default function PredictiveDashboard() {
  const [dashboard,   setDashboard]   = useState(null);
  const [predictions, setPredictions] = useState([]);
  const [warnings,    setWarnings]    = useState([]);
  const [trendData,   setTrendData]   = useState([]);  // real sensor history
  const [loading,     setLoading]     = useState(true);
  const [training,    setTraining]    = useState(false);
  const [lastUpdate,  setLastUpdate]  = useState(null);
  const [liveOnline,  setLiveOnline]  = useState(false);

  /* ── fetch all predictive data ──────────────────────── */
  const fetchAll = useCallback(async () => {
    try {
      // 1. Trigger fresh sensor readings
      await post('/api/sensor-data/simulate-all');

      // 2. Fetch all prediction endpoints in parallel
      const [dash, preds, warns] = await Promise.all([
        getPredictiveDashboard(),
        getEquipmentPredictions(),
        getWarnings({ limit: 20 }),
      ]);

      if (dash)  setDashboard(dash);
      if (preds) setPredictions(preds.predictions || []);
      if (warns) setWarnings(warns.warnings || []);

      // 3. Build real trend data from live-status
      const live = await get('/api/sensor-data/live-status');
      if (live?.equipment?.length > 0) {
        setLiveOnline(true);
        // Create a time-series point per equipment using current prediction data
        const predsMap = {};
        (preds?.predictions || []).forEach(p => { predsMap[p.equipment_name] = p; });

        const point = { time: new Date().toLocaleTimeString([], {hour:'2-digit', minute:'2-digit'}) };
        live.equipment.forEach(eq => {
          const pred = predsMap[eq.equipment_name];
          if (pred) {
            point[`${eq.equipment_name}_fail`] = pred.failure_probability;
            point[`${eq.equipment_name}_rul`]  = Math.min(pred.rul_days, 100);
          }
        });
        setTrendData(prev => {
          const next = [...prev, point].slice(-20); // keep last 20 ticks
          return next;
        });
      } else {
        setLiveOnline(false);
      }

      setLastUpdate(new Date());
      setLoading(false);
    } catch (err) {
      console.error('Predictive fetch failed:', err);
      setLoading(false);
    }
  }, []);

  /* ── 3-second polling ───────────────────────────────── */
  useEffect(() => {
    fetchAll();
    const id = setInterval(fetchAll, 3000);
    return () => clearInterval(id);
  }, [fetchAll]);

  /* ── train models ───────────────────────────────────── */
  const handleTrain = async () => {
    setTraining(true);
    try {
      await Promise.all([trainFailureModel(), trainRULModel()]);
      await fetchAll();
    } catch (e) {
      console.error('Training failed:', e);
    } finally {
      setTraining(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="w-8 h-8 border-2 border-orange-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  const stats = dashboard || {};
  const RISK_COLORS = ['#EF4444','#F97316','#FBBF24','#10B981'];

  // Build risk distribution for bar chart
  const riskDist = [
    { name:'Critical', count: stats.critical_risk_count  || 0 },
    { name:'High',     count: stats.high_risk_count      || 0 },
    { name:'Medium',   count: stats.medium_risk_count    || 0 },
    { name:'Low',      count: stats.low_risk_count       || 0 },
  ];

  // Top-2 most critical machines for trend chart
  const top2 = predictions.slice(0, 2);

  return (
    <div className="space-y-6 p-6">

      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-2xl font-heading font-bold text-white flex items-center gap-2">
            <TrendingUp className="w-6 h-6 text-orange-500" /> Predictive Maintenance
          </h1>
          <p className="text-slate-400 text-sm mt-0.5 flex items-center gap-2">
            AI-powered failure prediction · live sensor data
            {liveOnline ? (
              <span className="flex items-center gap-1 text-green-400 text-xs">
                <Wifi className="w-3 h-3" /> Live · {lastUpdate?.toLocaleTimeString()}
              </span>
            ) : (
              <span className="flex items-center gap-1 text-slate-500 text-xs">
                <WifiOff className="w-3 h-3" /> Connecting...
              </span>
            )}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button onClick={handleTrain} disabled={training}
            className="flex items-center gap-1.5 px-3 py-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white text-sm rounded-lg transition-colors">
            {training ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Zap className="w-4 h-4" />}
            {training ? 'Training...' : 'Re-train Models'}
          </button>
          <button onClick={fetchAll}
            className="p-2 bg-[#1E293B] border border-[#334155] hover:border-orange-500/40 text-slate-400 hover:text-white rounded-lg transition-all">
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* KPI cards */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
        {[
          { label:'Critical Risk', val: stats.critical_risk_count  || 0, color:'text-red-400',    bg:'bg-red-500/10 border-red-500/20',    icon:XCircle       },
          { label:'High Risk',     val: stats.high_risk_count      || 0, color:'text-orange-400', bg:'bg-orange-500/10 border-orange-500/20',icon:AlertTriangle },
          { label:'Medium Risk',   val: stats.medium_risk_count    || 0, color:'text-yellow-400', bg:'bg-yellow-500/10 border-yellow-500/20',icon:AlertCircle   },
          { label:'Low Risk',      val: stats.low_risk_count       || 0, color:'text-green-400',  bg:'bg-green-500/10 border-green-500/20',  icon:CheckCircle   },
          { label:'Avg RUL (days)',val: stats.average_rul_days != null ? stats.average_rul_days.toFixed(0) : '—', color:'text-blue-400', bg:'bg-blue-500/10 border-blue-500/20', icon:Calendar },
        ].map(({ label, val, color, bg, icon: Icon }) => (
          <div key={label} className={`rounded-xl border p-3 text-center ${bg}`}>
            <Icon className={`w-5 h-5 mx-auto mb-1 ${color}`} />
            <div className={`text-2xl font-bold font-mono ${color}`}>{val}</div>
            <div className="text-[10px] text-slate-400 mt-1">{label}</div>
          </div>
        ))}
      </div>

      {/* Charts row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

        {/* Live failure probability trend (real data) */}
        <div className="lg:col-span-2 bg-[#1E293B] border border-[#334155] rounded-xl p-4">
          <h3 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
            <TrendingUp className="w-4 h-4 text-red-400" />
            Live Failure Probability Trend
            <span className="text-[10px] text-slate-500 ml-1">— top 2 highest-risk machines</span>
          </h3>
          {trendData.length < 2 ? (
            <div className="h-52 flex items-center justify-center text-slate-500 text-sm">
              Accumulating live data...
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={200}>
              <LineChart data={trendData} margin={{ left:-10, right:5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1E293B" />
                <XAxis dataKey="time" tick={{ fontSize:10, fill:'#64748B' }} interval="preserveStartEnd" />
                <YAxis tick={{ fontSize:10, fill:'#64748B' }} domain={[0, 100]} unit="%" />
                <Tooltip content={<ChartTip />} />
                {top2.map((p, i) => (
                  <Line key={p.equipment_name} type="monotone"
                    dataKey={`${p.equipment_name}_fail`}
                    stroke={i === 0 ? '#EF4444' : '#F97316'}
                    strokeWidth={2} dot={false}
                    name={`${p.equipment_name.split(' ').slice(-1)[0]} fail%`}
                    connectNulls />
                ))}
              </LineChart>
            </ResponsiveContainer>
          )}
        </div>

        {/* Risk distribution bar chart */}
        <div className="bg-[#1E293B] border border-[#334155] rounded-xl p-4">
          <h3 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
            <Activity className="w-4 h-4 text-orange-400" /> Risk Distribution
          </h3>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={riskDist} margin={{ left:-20 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1E293B" />
              <XAxis dataKey="name" tick={{ fontSize:10, fill:'#94A3B8' }} />
              <YAxis tick={{ fontSize:10, fill:'#64748B' }} />
              <Tooltip content={<ChartTip />} />
              <Bar dataKey="count" radius={[4,4,0,0]}>
                {riskDist.map((_, i) => <Cell key={i} fill={RISK_COLORS[i]} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Active warnings */}
      {warnings.length > 0 && (
        <div className="bg-[#1E293B] border border-[#334155] rounded-xl p-4">
          <h3 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-orange-400" />
            Active Warnings ({warnings.length})
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-2">
            {warnings.slice(0, 9).map(w => (
              <WarningCard key={w.warning_id} warning={w} />
            ))}
          </div>
        </div>
      )}

      {/* Equipment predictions grid */}
      <div className="bg-[#1E293B] border border-[#334155] rounded-xl p-4">
        <h3 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
          <Activity className="w-4 h-4 text-orange-500" />
          Equipment Risk Assessment ({predictions.length})
          <span className="text-[10px] text-slate-500 ml-1">— from live sensor readings</span>
        </h3>
        {predictions.length === 0 ? (
          <div className="text-center py-12">
            <Wrench className="w-12 h-12 mx-auto text-slate-600 mb-3" />
            <p className="text-slate-400">No predictions yet — waiting for sensor data</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {predictions.map(pred => (
              <PredictionCard key={pred.equipment_name} equipment={pred} />
            ))}
          </div>
        )}
      </div>

      {/* Model status */}
      <div className="bg-[#1E293B] border border-[#334155] rounded-xl p-4">
        <h3 className="text-sm font-semibold text-white mb-3">ML Model Status</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          {[
            { title:'Failure Model',      desc:'Random Forest Classifier — trained on sensor threshold patterns' },
            { title:'RUL Model',          desc:'Random Forest Regressor — estimates remaining useful life in days' },
            { title:'Degradation Engine', desc:'Combines health score, failure prob and RUL for degradation state' },
          ].map(({ title, desc }) => (
            <div key={title} className="p-3 bg-[#0F1419] rounded-lg border border-[#334155]">
              <div className="flex items-center gap-2 mb-1.5">
                <CheckCircle className="w-4 h-4 text-green-400" />
                <span className="font-medium text-white text-xs">{title}</span>
              </div>
              <p className="text-[10px] text-slate-400 leading-relaxed">{desc}</p>
            </div>
          ))}
        </div>
        <p className="text-[10px] text-slate-600 mt-3">
          Click "Re-train Models" to retrain with the latest synthetic + sensor data.
          Models auto-train on server startup if not already trained.
        </p>
      </div>
    </div>
  );
}
