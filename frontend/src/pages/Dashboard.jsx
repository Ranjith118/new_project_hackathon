import { useState, useEffect, useRef, useCallback } from 'react';
import {
  Activity, AlertTriangle, Brain, Zap, Clock,
  Package, CheckCircle, AlertCircle,
  RefreshCw, Factory, Settings, ChevronRight
} from 'lucide-react';
import {
  AreaChart, Area, Tooltip, ResponsiveContainer
} from 'recharts';
import { dashboardAPI, equipmentAPI } from '../services/api';

const API = 'http://localhost:8000';
const get = (url) => fetch(API + url).then(r => r.json()).catch(() => null);

const healthColor = (s) =>
  s >= 80 ? '#10B981' : s >= 60 ? '#FBBF24' : s >= 40 ? '#F97316' : '#EF4444';
const healthLabel = (s) =>
  s >= 80 ? 'Healthy' : s >= 60 ? 'Fair' : s >= 40 ? 'Poor' : 'Critical';
const severityColor = (t) => ({
  critical: 'border-red-500/40 bg-red-500/5',
  high:     'border-orange-500/40 bg-orange-500/5',
  medium:   'border-yellow-500/40 bg-yellow-500/5',
  low:      'border-blue-500/40 bg-blue-500/5',
})[t] || 'border-slate-500/40 bg-slate-500/5';
const severityBadge = (t) => ({
  critical: 'bg-red-500/20 text-red-400 border border-red-500/40',
  high:     'bg-orange-500/20 text-orange-400 border border-orange-500/40',
  medium:   'bg-yellow-500/20 text-yellow-400 border border-yellow-500/40',
  low:      'bg-blue-500/20 text-blue-400 border border-blue-500/40',
})[t] || 'bg-slate-500/20 text-slate-400';

const Card = ({ children, className = '' }) => (
  <div className={`bg-[#1E293B] border border-[#334155] rounded-xl ${className}`}>{children}</div>
);
const SectionHead = ({ icon: Icon, title, sub, action }) => (
  <div className="flex items-center justify-between mb-4">
    <div className="flex items-center gap-2">
      <Icon className="w-4 h-4 text-orange-400" />
      <span className="font-heading font-semibold text-white">{title}</span>
      {sub && <span className="text-xs text-slate-500 ml-1">{sub}</span>}
    </div>
    {action && (
      <button onClick={action.fn} className="text-xs text-orange-400 hover:text-orange-300 flex items-center gap-1">
        {action.label}<ChevronRight className="w-3 h-3" />
      </button>
    )}
  </div>
);
const Pulse = ({ color = 'bg-green-500' }) => (
  <span className={`inline-block w-2 h-2 rounded-full ${color} animate-pulse`} />
);

/* ── Semicircle Health Gauge ─────────────────────────────── */
function HealthGauge({ score }) {
  const c = healthColor(score);
  const r = 54, cx = 80, cy = 85;
  const startAngle = Math.PI, sweepAngle = Math.PI;
  const filledAngle = sweepAngle * (score / 100);
  const px = (a) => cx + r * Math.cos(a);
  const py = (a) => cy + r * Math.sin(a);
  const bgPath = `M ${px(startAngle)} ${py(startAngle)} A ${r} ${r} 0 0 1 ${px(2 * Math.PI)} ${py(2 * Math.PI)}`;
  const fgEnd = startAngle + filledAngle;
  const fgPath = score > 0
    ? `M ${px(startAngle)} ${py(startAngle)} A ${r} ${r} 0 ${filledAngle > Math.PI ? 1 : 0} 1 ${px(fgEnd)} ${py(fgEnd)}`
    : '';
  return (
    <div style={{ width: 160, height: 110 }}>
      <svg width="160" height="110" viewBox="0 0 160 110">
        <path d={bgPath} fill="none" stroke="#1E293B" strokeWidth="14" strokeLinecap="round" />
        {fgPath && <path d={fgPath} fill="none" stroke={c} strokeWidth="14" strokeLinecap="round" style={{ transition: 'all 1s ease' }} />}
        <text x={cx} y={cy - 8} textAnchor="middle" fill={c} fontSize="22" fontWeight="bold" fontFamily="monospace">{score}%</text>
        <text x={cx} y={cy + 8} textAnchor="middle" fill="#64748B" fontSize="9" fontFamily="sans-serif" letterSpacing="2">PLANT HEALTH</text>
      </svg>
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════
   DASHBOARD
═══════════════════════════════════════════════════════════ */
export default function Dashboard() {
  const [data, setData]         = useState({});
  const [loading, setLoading]   = useState(true);
  const [lastRefresh, setLastRefresh] = useState(new Date());
  const [time, setTime]         = useState(new Date());

  useEffect(() => {
    const t = setInterval(() => setTime(new Date()), 1000);
    return () => clearInterval(t);
  }, []);

  const load = useCallback(async () => {
    const [stats, health, alertSum, alerts, inventory, spares, sensorData] = await Promise.all([
      get('/api/dashboard/stats'),
      get('/api/anomaly/health-status'),
      get('/api/alerts/summary'),
      get('/api/alerts'),
      get('/api/procurement/inventory-summary'),
      get('/api/procurement/spares'),
      get('/api/sensor-data/?limit=100'),
    ]);
    setData({ stats, health, alertSum, alerts, inventory, spares, sensorData });
    setLastRefresh(new Date());
    setLoading(false);
  }, []);

  useEffect(() => { load(); }, [load]);

  const healthPct    = data.health?.overall_health_percentage ?? 0;
  const equipList    = data.health?.equipment ?? [];
  const activeAlerts = (data.alerts?.alerts ?? []).filter(a => a.status === 'active');
  const sparesList   = data.spares?.parts ?? [];
  const stats        = data.stats ?? {};

  // Real sensor data — sorted by timestamp ascending for trend charts
  const rawSensor = Array.isArray(data.sensorData) ? data.sensorData : [];
  const trendData = rawSensor
    .filter(s => s.timestamp)
    .sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp))
    .map(s => ({
      t:         new Date(s.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      equipment: s.equipment_name,
      temp:      s.temperature ?? null,
      vibration: s.vibration   ?? null,
      current:   s.current     ?? null,
      pressure:  s.pressure    ?? null,
      rpm:       s.rpm         ?? null,
    }));

  const hasSensorData = trendData.length > 0;

  if (loading) return (
    <div className="min-h-screen bg-[#0F1419] flex items-center justify-center">
      <div className="text-center space-y-4">
        <div className="w-10 h-10 border-2 border-orange-500 border-t-transparent rounded-full animate-spin mx-auto" />
        <p className="text-slate-400 text-sm">Loading Plant Intelligence...</p>
      </div>
    </div>
  );

  return (
    <div className="space-y-6 p-6">

      {/* ── HEADER ───────────────────────────────────────── */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-heading font-bold text-white flex items-center gap-2">
            <Factory className="w-6 h-6 text-orange-500" />
            Plant Dashboard
          </h1>
          <p className="text-slate-400 text-sm mt-0.5">Steel Manufacturing Plant · Live Monitoring</p>
        </div>
        <div className="flex items-center gap-4">
          <div className="hidden md:flex items-center gap-1 text-xs text-slate-400">
            <Pulse color={healthPct >= 80 ? 'bg-green-500' : healthPct >= 60 ? 'bg-yellow-500' : 'bg-red-500'} />
            LIVE · {time.toLocaleTimeString()}
          </div>
          <button onClick={load}
            className="p-2 rounded-lg bg-[#1E293B] border border-[#334155] hover:border-orange-500/50 transition-colors">
            <RefreshCw className="w-4 h-4 text-slate-400" />
          </button>
        </div>
      </div>

      {/* ── ROW 1: PLANT HEALTH + KPI CARDS ──────────────── */}
      <div className="grid grid-cols-2 md:grid-cols-4 xl:grid-cols-6 gap-4">

        {/* Health Gauge Card */}
        <Card className="col-span-2 p-4 flex items-center gap-6">
          <HealthGauge score={Math.round(healthPct)} />
          <div className="space-y-3">
            {[
              { label: 'Total Equipment',  val: stats.total_equipment ?? 0,      color: 'text-white' },
              { label: 'Operational',      val: stats.operational_equipment ?? 0, color: 'text-green-400' },
              { label: 'Maintenance',      val: stats.maintenance_equipment ?? 0, color: 'text-yellow-400' },
              { label: 'Failed',           val: stats.failed_equipment ?? 0,      color: 'text-red-400' },
            ].map(({ label, val, color }) => (
              <div key={label} className="flex items-center justify-between gap-8">
                <span className="text-xs text-slate-400">{label}</span>
                <span className={`text-sm font-mono font-bold ${color}`}>{val}</span>
              </div>
            ))}
          </div>
        </Card>

        {/* Active Alerts KPI */}
        <Card className="p-4 flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <AlertTriangle className="w-5 h-5 text-red-400" />
            <span className="text-[10px] text-slate-500 uppercase tracking-wide">Alerts</span>
          </div>
          <div>
            <div className="text-3xl font-heading font-bold text-red-400">{data.alertSum?.active ?? 0}</div>
            <div className="text-xs text-slate-400">Active · {data.alertSum?.critical_count ?? 0} Critical</div>
          </div>
        </Card>

        {/* Maintenance Logs KPI */}
        <Card className="p-4 flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <Activity className="w-5 h-5 text-blue-400" />
            <span className="text-[10px] text-slate-500 uppercase tracking-wide">Logs</span>
          </div>
          <div>
            <div className="text-3xl font-heading font-bold text-blue-400">{stats.total_maintenance_logs ?? 0}</div>
            <div className="text-xs text-slate-400">Maintenance Logs</div>
          </div>
        </Card>

        {/* Failure Reports KPI */}
        <Card className="p-4 flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <Zap className="w-5 h-5 text-orange-400" />
            <span className="text-[10px] text-slate-500 uppercase tracking-wide">Failures</span>
          </div>
          <div>
            <div className="text-3xl font-heading font-bold text-orange-400">{stats.total_failure_reports ?? 0}</div>
            <div className="text-xs text-slate-400">Failure Reports</div>
          </div>
        </Card>

        {/* Inventory KPI */}
        <Card className="p-4 flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <Package className="w-5 h-5 text-yellow-400" />
            <span className="text-[10px] text-slate-500 uppercase tracking-wide">Inventory</span>
          </div>
          <div>
            <div className="text-3xl font-heading font-bold text-yellow-400">{data.inventory?.out_of_stock ?? 0}</div>
            <div className="text-xs text-slate-400">Out of Stock · {data.inventory?.low_stock ?? 0} Low</div>
          </div>
        </Card>
      </div>

      {/* ── ROW 2: ACTIVE ALERTS + EQUIPMENT HEALTH ──────── */}
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">

        {/* Active Alerts */}
        <Card className="p-4">
          <SectionHead icon={AlertTriangle} title="Active Alerts"
            sub={`${activeAlerts.length} active`}
            action={{ label: 'View All', fn: () => window.location.href = '/alerts' }} />
          <div className="space-y-2 max-h-72 overflow-y-auto pr-1">
            {activeAlerts.length === 0 ? (
              <div className="text-center py-8">
                <CheckCircle className="w-8 h-8 text-green-400 mx-auto mb-2" />
                <p className="text-sm text-slate-400">No active alerts</p>
              </div>
            ) : activeAlerts.slice(0, 8).map((a, i) => (
              <div key={i} className={`flex items-start gap-3 p-3 rounded-lg border ${severityColor(a.alert_type)}`}>
                <AlertCircle className="w-4 h-4 mt-0.5 flex-shrink-0 text-red-400" />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="text-xs font-semibold text-white truncate">{a.equipment_name}</span>
                    <span className={`text-[10px] px-1.5 py-0.5 rounded font-medium ${severityBadge(a.alert_type)}`}>
                      {a.alert_type?.toUpperCase()}
                    </span>
                  </div>
                  <p className="text-xs text-slate-400 mt-0.5 line-clamp-1">{a.message}</p>
                  <p className="text-[10px] text-slate-500 mt-0.5">{new Date(a.timestamp).toLocaleTimeString()}</p>
                </div>
              </div>
            ))}
          </div>
        </Card>

        {/* Equipment Health */}
        <Card className="p-4">
          <SectionHead icon={Activity} title="Equipment Health Status"
            action={{ label: 'Details', fn: () => window.location.href = '/equipment-health' }} />
          <div className="space-y-3 max-h-72 overflow-y-auto pr-1">
            {equipList.length === 0 ? (
              <p className="text-slate-400 text-sm text-center py-8">No equipment data</p>
            ) : equipList.map((eq, i) => {
              const hc = healthColor(eq.health_score);
              return (
                <div key={i} className="flex items-center gap-3">
                  <div className="w-2 h-2 rounded-full flex-shrink-0" style={{ backgroundColor: hc }} />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-xs text-white truncate max-w-[160px]">{eq.equipment_name}</span>
                      <span className="text-xs font-mono font-bold ml-2" style={{ color: hc }}>{eq.health_score}</span>
                    </div>
                    <div className="w-full bg-[#0F1419] rounded-full h-1.5">
                      <div className="h-1.5 rounded-full transition-all duration-500"
                        style={{ width: `${eq.health_score}%`, backgroundColor: hc }} />
                    </div>
                  </div>
                  <span className="text-[10px] px-1.5 py-0.5 rounded border flex-shrink-0"
                    style={{ color: hc, borderColor: hc + '50', backgroundColor: hc + '15' }}>
                    {healthLabel(eq.health_score)}
                  </span>
                </div>
              );
            })}
          </div>
        </Card>
      </div>

      {/* ── ROW 3: SENSOR TRENDS + SPARE PARTS ───────────── */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">

        {/* Sensor Trends */}
        <Card className="xl:col-span-2 p-4">
          <SectionHead icon={Activity} title="Sensor Trend Monitoring"
            sub={hasSensorData ? `${trendData.length} readings` : 'No sensor data yet'}
            action={{ label: 'Sensor Trends', fn: () => window.location.href = '/sensor-trends' }} />

          {!hasSensorData ? (
            <div className="text-center py-12">
              <Activity className="w-10 h-10 text-slate-600 mx-auto mb-3" />
              <p className="text-slate-400 text-sm">No sensor data available</p>
              <p className="text-slate-500 text-xs mt-1">Add sensor readings via Sensor Data page</p>
            </div>
          ) : (
            <div className="space-y-4">
              {[
                { label: 'Temperature (°C)', color: '#EF4444', key: 'temp' },
                { label: 'Vibration (mm/s)',  color: '#F97316', key: 'vibration' },
                { label: 'Current (A)',        color: '#3B82F6', key: 'current' },
              ].map(({ label, color, key }) => {
                const latest = trendData.filter(d => d[key] !== null).slice(-1)[0];
                const hasKey = trendData.some(d => d[key] !== null);
                return (
                  <div key={key}>
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-xs text-slate-400">{label}</span>
                      <span className="text-xs font-mono" style={{ color }}>
                        {latest ? latest[key]?.toFixed(1) : '—'}
                      </span>
                    </div>
                    {hasKey ? (
                      <ResponsiveContainer width="100%" height={44}>
                        <AreaChart data={trendData.filter(d => d[key] !== null)}
                          margin={{ top: 0, right: 0, bottom: 0, left: 0 }}>
                          <defs>
                            <linearGradient id={`g-${key}`} x1="0" y1="0" x2="0" y2="1">
                              <stop offset="5%"  stopColor={color} stopOpacity={0.3} />
                              <stop offset="95%" stopColor={color} stopOpacity={0} />
                            </linearGradient>
                          </defs>
                          <Area type="monotone" dataKey={key} stroke={color} strokeWidth={1.5}
                            fill={`url(#g-${key})`} dot={{ r: 3, fill: color }} />
                          <Tooltip
                            contentStyle={{ background: '#1E293B', border: '1px solid #334155', fontSize: 10 }}
                            formatter={v => [v?.toFixed(2), label]}
                            labelFormatter={l => `Time: ${l}`} />
                        </AreaChart>
                      </ResponsiveContainer>
                    ) : (
                      <div className="h-11 flex items-center">
                        <span className="text-xs text-slate-600">No {label.toLowerCase()} readings</span>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </Card>

        {/* Spare Parts */}
        <Card className="p-4">
          <SectionHead icon={Package} title="Spare Parts Status"
            action={{ label: 'Procurement', fn: () => window.location.href = '/procurement' }} />

          {/* Summary counts */}
          <div className="grid grid-cols-3 gap-2 mb-4 text-center">
            {[
              { label: 'In Stock', val: data.inventory?.in_stock ?? 0,    color: 'text-green-400' },
              { label: 'Low',      val: data.inventory?.low_stock ?? 0,    color: 'text-yellow-400' },
              { label: 'Out',      val: data.inventory?.out_of_stock ?? 0, color: 'text-red-400' },
            ].map(({ label, val, color }) => (
              <div key={label} className="bg-[#0F1419] rounded-lg p-2 border border-[#334155]">
                <div className={`text-xl font-bold font-mono ${color}`}>{val}</div>
                <div className="text-[10px] text-slate-500">{label}</div>
              </div>
            ))}
          </div>

          {/* Parts list */}
          <div className="space-y-2 max-h-52 overflow-y-auto pr-1">
            {sparesList.slice(0, 8).map((p, i) => {
              const sc = p.status === 'in_stock' ? 'text-green-400'
                : p.status === 'out_of_stock'   ? 'text-red-400' : 'text-yellow-400';
              const sl = p.status === 'in_stock' ? 'OK'
                : p.status === 'out_of_stock'   ? 'OUT' : 'LOW';
              return (
                <div key={i} className="flex items-center justify-between text-xs py-1.5 border-b border-[#334155] last:border-0">
                  <div>
                    <div className="text-white truncate max-w-[130px]">{p.part_name}</div>
                    <div className="text-slate-500 text-[10px]">P/N: {p.part_number}</div>
                  </div>
                  <div className="text-right">
                    <div className={`font-mono font-bold ${sc}`}>{sl}</div>
                    <div className="text-[10px] text-slate-500">{p.stock_quantity}/{p.minimum_stock}</div>
                  </div>
                </div>
              );
            })}
          </div>
        </Card>
      </div>

      {/* ── FOOTER ───────────────────────────────────────── */}
      <div className="flex items-center justify-between text-xs text-slate-600 pt-2 border-t border-[#334155]">
        <div className="flex items-center gap-2">
          <Pulse color="bg-green-500" />
          All systems connected
        </div>
        <span>Last refreshed: {lastRefresh.toLocaleTimeString()}</span>
      </div>

    </div>
  );
}
