import { useState, useEffect } from 'react';
import {
  Plus, Search, Edit2, Trash2, X, Settings, Eye,
  Activity, AlertTriangle, CheckCircle, Clock, ChevronRight,
  ThermometerSun, Gauge, Zap, Wind, Cpu, FileText,
  Wrench, Package, Brain, ChevronLeft, Filter
} from 'lucide-react';
import {
  AreaChart, Area, Tooltip, ResponsiveContainer
} from 'recharts';

const API = 'http://localhost:8000';
const get  = (url) => fetch(API + url).then(r => r.json()).catch(() => null);
const post = (url, body) => fetch(API + url, {
  method: 'POST', headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(body)
}).then(r => r.json()).catch(() => null);

/* ── helpers ─────────────────────────────────────────────── */
const statusColor = (s) => ({
  operational: 'bg-green-500/15 text-green-400 border-green-500/30',
  maintenance:  'bg-yellow-500/15 text-yellow-400 border-yellow-500/30',
  failed:       'bg-red-500/15 text-red-400 border-red-500/30',
})[s] || 'bg-slate-500/15 text-slate-400 border-slate-500/30';

const statusDot = (s) => ({
  operational: 'bg-green-500', maintenance: 'bg-yellow-500', failed: 'bg-red-500'
})[s] || 'bg-slate-500';

const healthColor = (s) =>
  s >= 80 ? '#10B981' : s >= 60 ? '#FBBF24' : s >= 40 ? '#F97316' : '#EF4444';
const healthLabel = (s) =>
  s >= 80 ? 'Healthy' : s >= 60 ? 'Fair' : s >= 40 ? 'Poor' : 'Critical';
const riskColor = (r) => ({
  Low: 'text-green-400', Medium: 'text-yellow-400', High: 'text-orange-400', Critical: 'text-red-400'
})[r] || 'text-slate-400';

const Card = ({ children, className = '' }) => (
  <div className={`bg-[#1E293B] border border-[#334155] rounded-xl ${className}`}>{children}</div>
);
const Tab = ({ label, active, onClick }) => (
  <button onClick={onClick}
    className={`px-4 py-2 text-sm font-medium rounded-lg transition-all ${
      active ? 'bg-orange-500 text-white' : 'text-slate-400 hover:text-white'
    }`}>{label}</button>
);

const EQUIPMENT_TYPES = [
  'Motor', 'Pump', 'Compressor', 'Furnace', 'Conveyor', 'Fan', 'Crane',
  'Roller Mill', 'Hydraulic System', 'Generator', 'Transformer', 'Other'
];
const STATUS_OPTIONS = ['operational', 'maintenance', 'failed'];

/* ══════════════════════════════════════════════════════════
   EQUIPMENT DETAIL PAGE
══════════════════════════════════════════════════════════ */
function EquipmentDetail({ equipment, onBack }) {
  const [tab, setTab] = useState(0);
  const [sensorData, setSensorData] = useState([]);
  const [maintLogs, setMaintLogs]   = useState([]);
  const [failReports, setFailReports] = useState([]);
  const [health, setHealth]         = useState(null);
  const [aiData, setAiData]         = useState(null);
  const [loading, setLoading]       = useState(true);

  const name = equipment.equipment_name;

  useEffect(() => {
    (async () => {
      setLoading(true);
      const [sd, ml, fr, hs] = await Promise.all([
        get(`/api/sensor-data/?equipment_name=${encodeURIComponent(name)}&limit=20`),
        get(`/api/maintenance-logs/?equipment_name=${encodeURIComponent(name)}&limit=20`),
        get(`/api/failure-reports/?equipment_name=${encodeURIComponent(name)}&limit=20`),
        get(`/api/anomaly/equipment-health/${encodeURIComponent(name)}`),
      ]);
      setSensorData(Array.isArray(sd) ? sd : []);
      setMaintLogs(Array.isArray(ml) ? ml : []);
      setFailReports(Array.isArray(fr) ? fr : []);
      setHealth(hs);

      // AI predictions if sensor data exists
      if (sd && sd.length > 0) {
        const latest = sd[0];
        const ai = await get(
          `/api/prediction/degradation/${encodeURIComponent(name)}`
        );
        setAiData(ai);
      }
      setLoading(false);
    })();
  }, [name]);

  const latestSensor = sensorData[0] || null;
  const healthScore  = health?.health_score ?? 100;
  const hc           = healthColor(healthScore);

  // Build trend arrays from sensor data (sorted asc)
  const trendBase = [...sensorData].reverse();

  const TABS = ['Overview', 'Sensor Data', 'Maintenance History', 'Failure History', 'AI Insights'];

  return (
    <div className="space-y-6">
      {/* Back header */}
      <div className="flex items-center gap-3">
        <button onClick={onBack}
          className="flex items-center gap-1 text-slate-400 hover:text-white text-sm transition-colors">
          <ChevronLeft className="w-4 h-4" /> Equipment List
        </button>
        <span className="text-slate-600">/</span>
        <span className="text-white font-medium">{name}</span>
      </div>

      {/* Equipment header card */}
      <Card className="p-6">
        <div className="flex items-start justify-between flex-wrap gap-4">
          <div className="flex items-center gap-4">
            <div className="w-14 h-14 rounded-xl bg-orange-500/10 border border-orange-500/20 flex items-center justify-center flex-shrink-0">
              <Settings className="w-7 h-7 text-orange-400" />
            </div>
            <div>
              <h1 className="text-2xl font-heading font-bold text-white">{name}</h1>
              <div className="flex items-center gap-3 mt-1 flex-wrap">
                <span className="text-slate-400 text-sm">{equipment.equipment_type}</span>
                <span className="text-slate-600">·</span>
                <span className="text-slate-400 text-sm">{equipment.manufacturer || 'Unknown'}</span>
                {equipment.installation_date && <>
                  <span className="text-slate-600">·</span>
                  <span className="text-slate-400 text-sm">Installed: {equipment.installation_date}</span>
                </>}
              </div>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <span className={`flex items-center gap-2 px-3 py-1.5 rounded-lg border text-sm font-medium ${statusColor(equipment.status)}`}>
              <span className={`w-2 h-2 rounded-full animate-pulse ${statusDot(equipment.status)}`} />
              {equipment.status?.charAt(0).toUpperCase() + equipment.status?.slice(1)}
            </span>
          </div>
        </div>

        {/* Quick stats row */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6 pt-6 border-t border-[#334155]">
          <div>
            <div className="text-xs text-slate-500 mb-1">Health Score</div>
            <div className="flex items-center gap-2">
              <div className="flex-1 bg-[#0F1419] rounded-full h-2">
                <div className="h-2 rounded-full" style={{ width: `${healthScore}%`, backgroundColor: hc }} />
              </div>
              <span className="text-sm font-mono font-bold" style={{ color: hc }}>{healthScore}%</span>
            </div>
          </div>
          <div>
            <div className="text-xs text-slate-500 mb-1">Risk Level</div>
            <span className={`text-sm font-semibold ${riskColor(health?.risk_level)}`}>
              {health?.risk_level || 'Low'}
            </span>
          </div>
          <div>
            <div className="text-xs text-slate-500 mb-1">Maintenance Logs</div>
            <span className="text-sm font-mono font-bold text-white">{maintLogs.length}</span>
          </div>
          <div>
            <div className="text-xs text-slate-500 mb-1">Failure Reports</div>
            <span className="text-sm font-mono font-bold text-white">{failReports.length}</span>
          </div>
        </div>
      </Card>

      {/* Tabs */}
      <div className="flex gap-1 bg-[#1E293B] p-1 rounded-xl border border-[#334155] w-fit flex-wrap">
        {TABS.map((t, i) => <Tab key={t} label={t} active={tab === i} onClick={() => setTab(i)} />)}
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-20">
          <div className="w-8 h-8 border-2 border-orange-500 border-t-transparent rounded-full animate-spin" />
        </div>
      ) : (
        <>
          {/* ── TAB 0: OVERVIEW ──────────────────────────── */}
          {tab === 0 && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Equipment Info */}
              <Card className="p-5">
                <h3 className="font-heading font-semibold text-white mb-4 flex items-center gap-2">
                  <Settings className="w-4 h-4 text-orange-400" /> Equipment Information
                </h3>
                <div className="space-y-3">
                  {[
                    { label: 'Equipment ID',    val: equipment.equipment_id?.slice(0, 8).toUpperCase() },
                    { label: 'Name',            val: equipment.equipment_name },
                    { label: 'Type',            val: equipment.equipment_type },
                    { label: 'Manufacturer',    val: equipment.manufacturer || '—' },
                    { label: 'Installation',    val: equipment.installation_date || '—' },
                    { label: 'Status',          val: equipment.status },
                    { label: 'Registered',      val: new Date(equipment.created_at).toLocaleDateString() },
                  ].map(({ label, val }) => (
                    <div key={label} className="flex justify-between py-1.5 border-b border-[#334155] last:border-0">
                      <span className="text-xs text-slate-400">{label}</span>
                      <span className="text-xs text-white font-medium">{val}</span>
                    </div>
                  ))}
                </div>
              </Card>

              {/* Health Status */}
              <Card className="p-5">
                <h3 className="font-heading font-semibold text-white mb-4 flex items-center gap-2">
                  <Activity className="w-4 h-4 text-orange-400" /> Health Status
                </h3>
                <div className="flex items-center justify-center py-4">
                  <div className="relative w-32 h-32">
                    <svg width="128" height="128" viewBox="0 0 128 128">
                      <circle cx="64" cy="64" r="52" fill="none" stroke="#1E293B" strokeWidth="12" />
                      <circle cx="64" cy="64" r="52" fill="none" stroke={hc} strokeWidth="12"
                        strokeDasharray={`${(healthScore / 100) * 326.7} 326.7`}
                        strokeLinecap="round" transform="rotate(-90 64 64)"
                        style={{ transition: 'stroke-dasharray 1s ease' }} />
                    </svg>
                    <div className="absolute inset-0 flex flex-col items-center justify-center">
                      <span className="text-2xl font-bold" style={{ color: hc }}>{healthScore}%</span>
                      <span className="text-[10px] text-slate-400">{healthLabel(healthScore)}</span>
                    </div>
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-3 mt-2">
                  {[
                    { label: 'Status',     val: healthLabel(healthScore),    color: hc },
                    { label: 'Risk Level', val: health?.risk_level || 'Low', color: hc },
                    { label: 'Trend',      val: health?.trend || 'Stable',   color: '#94A3B8' },
                    { label: 'Anomalies',  val: health?.anomaly_count || 0,  color: '#94A3B8' },
                  ].map(({ label, val, color }) => (
                    <div key={label} className="bg-[#0F1419] rounded-lg p-3 border border-[#334155]">
                      <div className="text-[10px] text-slate-500 mb-1">{label}</div>
                      <div className="text-sm font-semibold" style={{ color }}>{String(val)}</div>
                    </div>
                  ))}
                </div>
              </Card>

              {/* Latest Sensor Snapshot */}
              {latestSensor && (
                <Card className="p-5 lg:col-span-2">
                  <h3 className="font-heading font-semibold text-white mb-4 flex items-center gap-2">
                    <Gauge className="w-4 h-4 text-orange-400" /> Latest Sensor Reading
                    <span className="text-[10px] text-slate-500 ml-2">
                      {new Date(latestSensor.timestamp).toLocaleString()}
                    </span>
                  </h3>
                  <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
                    {[
                      { icon: ThermometerSun, label: 'Temperature', val: latestSensor.temperature, unit: '°C', warn: 95, crit: 110 },
                      { icon: Activity,       label: 'Vibration',   val: latestSensor.vibration,   unit: 'mm/s', warn: 2.8, crit: 4.0 },
                      { icon: Zap,            label: 'Current',     val: latestSensor.current,     unit: 'A',    warn: 28, crit: 32 },
                      { icon: Wind,           label: 'Pressure',    val: latestSensor.pressure,    unit: 'bar',  warn: 90, crit: 98 },
                      { icon: Cpu,            label: 'RPM',         val: latestSensor.rpm,         unit: 'rpm',  warn: 2200, crit: 2400 },
                    ].map(({ icon: Icon, label, val, unit, warn, crit }) => {
                      if (val == null) return null;
                      const c = val >= crit ? '#EF4444' : val >= warn ? '#F97316' : '#10B981';
                      return (
                        <div key={label} className="bg-[#0F1419] rounded-lg p-3 border border-[#334155]">
                          <div className="flex items-center gap-1.5 mb-2">
                            <Icon className="w-3.5 h-3.5" style={{ color: c }} />
                            <span className="text-[10px] text-slate-400">{label}</span>
                          </div>
                          <div className="text-xl font-mono font-bold" style={{ color: c }}>{val}</div>
                          <div className="text-[10px] text-slate-500">{unit}</div>
                        </div>
                      );
                    })}
                  </div>
                </Card>
              )}
            </div>
          )}

          {/* ── TAB 1: SENSOR DATA ───────────────────────── */}
          {tab === 1 && (
            <div className="space-y-4">
              {sensorData.length === 0 ? (
                <Card className="p-10 text-center">
                  <Gauge className="w-10 h-10 text-slate-600 mx-auto mb-3" />
                  <p className="text-slate-400">No sensor data for this equipment</p>
                  <p className="text-slate-500 text-xs mt-1">Add sensor readings via Sensor Data page</p>
                </Card>
              ) : (
                <>
                  {[
                    { key: 'temperature', label: 'Temperature (°C)',  color: '#EF4444' },
                    { key: 'vibration',   label: 'Vibration (mm/s)',  color: '#F97316' },
                    { key: 'current',     label: 'Current (A)',       color: '#3B82F6' },
                    { key: 'pressure',    label: 'Pressure (bar)',    color: '#8B5CF6' },
                    { key: 'rpm',         label: 'RPM',               color: '#10B981' },
                  ].map(({ key, label, color }) => {
                    const data = trendBase.filter(s => s[key] != null);
                    if (data.length === 0) return null;
                    const latest = data[data.length - 1]?.[key];
                    return (
                      <Card key={key} className="p-4">
                        <div className="flex items-center justify-between mb-3">
                          <span className="text-sm font-medium text-white">{label}</span>
                          <span className="text-sm font-mono font-bold" style={{ color }}>
                            {latest?.toFixed(1)} {key === 'rpm' ? 'rpm' : ''}
                          </span>
                        </div>
                        <ResponsiveContainer width="100%" height={60}>
                          <AreaChart data={data} margin={{ top: 0, right: 0, bottom: 0, left: 0 }}>
                            <defs>
                              <linearGradient id={`g${key}`} x1="0" y1="0" x2="0" y2="1">
                                <stop offset="5%" stopColor={color} stopOpacity={0.3} />
                                <stop offset="95%" stopColor={color} stopOpacity={0} />
                              </linearGradient>
                            </defs>
                            <Area type="monotone" dataKey={key} stroke={color} strokeWidth={1.5}
                              fill={`url(#g${key})`} dot={{ r: 3, fill: color }} />
                            <Tooltip contentStyle={{ background: '#1E293B', border: '1px solid #334155', fontSize: 10 }}
                              formatter={v => [v?.toFixed(2), label]}
                              labelFormatter={() => ''} />
                          </AreaChart>
                        </ResponsiveContainer>
                      </Card>
                    );
                  })}

                  {/* Raw data table */}
                  <Card className="p-4">
                    <h3 className="text-sm font-semibold text-white mb-3">All Readings ({sensorData.length})</h3>
                    <div className="overflow-x-auto">
                      <table className="industrial-table">
                        <thead><tr>
                          <th>Timestamp</th><th>Temp (°C)</th><th>Vibration</th>
                          <th>Current (A)</th><th>Pressure</th><th>RPM</th>
                        </tr></thead>
                        <tbody>
                          {sensorData.map(s => (
                            <tr key={s.sensor_id}>
                              <td className="font-mono text-xs">{new Date(s.timestamp).toLocaleString()}</td>
                              <td className="font-mono">{s.temperature ?? '—'}</td>
                              <td className="font-mono">{s.vibration ?? '—'}</td>
                              <td className="font-mono">{s.current ?? '—'}</td>
                              <td className="font-mono">{s.pressure ?? '—'}</td>
                              <td className="font-mono">{s.rpm ?? '—'}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </Card>
                </>
              )}
            </div>
          )}

          {/* ── TAB 2: MAINTENANCE HISTORY ───────────────── */}
          {tab === 2 && (
            <Card className="p-4">
              <h3 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
                <Wrench className="w-4 h-4 text-orange-400" />
                Maintenance History ({maintLogs.length})
              </h3>
              {maintLogs.length === 0 ? (
                <div className="text-center py-10">
                  <Wrench className="w-10 h-10 text-slate-600 mx-auto mb-3" />
                  <p className="text-slate-400 text-sm">No maintenance records</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {maintLogs.map(log => (
                    <div key={log.log_id} className="p-4 bg-[#0F1419] rounded-lg border border-[#334155]">
                      <div className="flex items-start justify-between flex-wrap gap-2">
                        <div>
                          <div className="flex items-center gap-2 flex-wrap">
                            <span className="text-white text-sm font-medium">{log.issue}</span>
                            <span className={`text-[10px] px-2 py-0.5 rounded border font-medium ${
                              log.severity === 'critical' ? 'bg-red-500/15 text-red-400 border-red-500/30'
                              : log.severity === 'high'   ? 'bg-orange-500/15 text-orange-400 border-orange-500/30'
                              : log.severity === 'medium' ? 'bg-yellow-500/15 text-yellow-400 border-yellow-500/30'
                              : 'bg-blue-500/15 text-blue-400 border-blue-500/30'
                            }`}>{log.severity?.toUpperCase()}</span>
                          </div>
                          {log.action_taken && (
                            <p className="text-xs text-slate-400 mt-1">Action: {log.action_taken}</p>
                          )}
                        </div>
                        <div className="text-right text-xs text-slate-500">
                          <div>{log.maintenance_date}</div>
                          {log.technician && <div>By: {log.technician}</div>}
                          {log.downtime_hours > 0 && <div>Downtime: {log.downtime_hours}h</div>}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </Card>
          )}

          {/* ── TAB 3: FAILURE HISTORY ───────────────────── */}
          {tab === 3 && (
            <Card className="p-4">
              <h3 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 text-red-400" />
                Failure History ({failReports.length})
              </h3>
              {failReports.length === 0 ? (
                <div className="text-center py-10">
                  <CheckCircle className="w-10 h-10 text-green-500 mx-auto mb-3" />
                  <p className="text-slate-400 text-sm">No failure reports — good record!</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {failReports.map(rep => (
                    <div key={rep.report_id} className="p-4 bg-[#0F1419] rounded-lg border border-red-500/20">
                      <div className="flex items-start justify-between flex-wrap gap-2">
                        <div>
                          <span className="text-white text-sm font-medium">{rep.failure_type}</span>
                          {rep.root_cause && (
                            <p className="text-xs text-slate-400 mt-1">Root Cause: {rep.root_cause}</p>
                          )}
                        </div>
                        <div className="text-right text-xs text-slate-500">
                          <div>{rep.report_date}</div>
                          {rep.downtime_hours > 0 && (
                            <div className="text-red-400">{rep.downtime_hours}h downtime</div>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </Card>
          )}

          {/* ── TAB 4: AI INSIGHTS ───────────────────────── */}
          {tab === 4 && (
            <div className="space-y-4">
              {!aiData && !latestSensor ? (
                <Card className="p-10 text-center">
                  <Brain className="w-10 h-10 text-slate-600 mx-auto mb-3" />
                  <p className="text-slate-400 text-sm">No sensor data — AI insights require sensor readings</p>
                </Card>
              ) : (
                <>
                  {aiData && (
                    <Card className="p-5">
                      <h3 className="font-heading font-semibold text-white mb-4 flex items-center gap-2">
                        <Brain className="w-4 h-4 text-orange-400" /> AI Degradation Analysis
                      </h3>
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        {[
                          { label: 'Degradation Level', val: aiData.level?.replace(/_/g,' ').replace(/\b\w/g, c => c.toUpperCase()), color: aiData.score >= 60 ? '#10B981' : '#EF4444' },
                          { label: 'Degradation Score', val: aiData.score + '/100', color: healthColor(aiData.score) },
                          { label: 'Failure Probability', val: aiData.factors?.failure_probability?.toFixed(1) + '%' || '—', color: '#F97316' },
                          { label: 'RUL (days)', val: aiData.factors?.rul_score?.toFixed(0) + 'd' || '—', color: '#3B82F6' },
                        ].map(({ label, val, color }) => (
                          <div key={label} className="bg-[#0F1419] rounded-lg p-4 border border-[#334155]">
                            <div className="text-[10px] text-slate-500 mb-2">{label}</div>
                            <div className="text-lg font-bold font-mono" style={{ color }}>{val}</div>
                          </div>
                        ))}
                      </div>
                      {aiData.explanation && (
                        <div className="mt-4 p-3 bg-[#0F1419] rounded-lg border border-[#334155]">
                          <p className="text-xs text-slate-300 leading-relaxed">{aiData.explanation}</p>
                        </div>
                      )}
                    </Card>
                  )}
                  {/* Run RCA button */}
                  {latestSensor && (
                    <Card className="p-5">
                      <h3 className="font-heading font-semibold text-white mb-3 flex items-center gap-2">
                        <Activity className="w-4 h-4 text-orange-400" /> Run AI Analysis
                      </h3>
                      <div className="flex flex-wrap gap-2">
                        <a href={`/predictive`}
                          className="px-4 py-2 bg-orange-500/10 border border-orange-500/30 text-orange-400 rounded-lg text-sm hover:bg-orange-500/20 transition-colors">
                          Failure Prediction →
                        </a>
                        <a href={`/root-cause`}
                          className="px-4 py-2 bg-blue-500/10 border border-blue-500/30 text-blue-400 rounded-lg text-sm hover:bg-blue-500/20 transition-colors">
                          Root Cause Analysis →
                        </a>
                        <a href={`/recommendations`}
                          className="px-4 py-2 bg-green-500/10 border border-green-500/30 text-green-400 rounded-lg text-sm hover:bg-green-500/20 transition-colors">
                          Maintenance Recommendations →
                        </a>
                      </div>
                    </Card>
                  )}
                </>
              )}
            </div>
          )}
        </>
      )}
    </div>
  );
}

/* ══════════════════════════════════════════════════════════
   EQUIPMENT LIST PAGE
══════════════════════════════════════════════════════════ */
export default function Equipment() {
  const [equipment, setEquipment]       = useState([]);
  const [loading, setLoading]           = useState(true);
  const [searchTerm, setSearchTerm]     = useState('');
  const [filterStatus, setFilterStatus] = useState('');
  const [filterType, setFilterType]     = useState('');
  const [showModal, setShowModal]       = useState(false);
  const [modalMode, setModalMode]       = useState('add');
  const [currentEq, setCurrentEq]       = useState(null);
  const [selectedEq, setSelectedEq]     = useState(null);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [deleteId, setDeleteId]         = useState(null);
  const [healthMap, setHealthMap]       = useState({});

  const [formData, setFormData] = useState({
    equipment_name: '', equipment_type: '', manufacturer: '',
    installation_date: '', status: 'operational'
  });

  useEffect(() => { fetchEquipment(); }, [searchTerm, filterStatus, filterType]);

  const fetchEquipment = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (searchTerm)   params.set('search', searchTerm);
      if (filterStatus) params.set('status', filterStatus);
      const url = `/api/equipment/?${params}`;
      const data = await get(url);
      const list = Array.isArray(data) ? data : [];
      const filtered = filterType
        ? list.filter(e => e.equipment_type?.toLowerCase() === filterType.toLowerCase())
        : list;
      setEquipment(filtered);

      // Fetch health for each equipment
      const healthData = {};
      await Promise.all(filtered.map(async (eq) => {
        const h = await get(`/api/anomaly/equipment-health/${encodeURIComponent(eq.equipment_name)}`);
        if (h) healthData[eq.equipment_id] = h;
      }));
      setHealthMap(healthData);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  // Summary counts
  const summary = {
    total:       equipment.length,
    operational: equipment.filter(e => e.status === 'operational').length,
    maintenance: equipment.filter(e => e.status === 'maintenance').length,
    failed:      equipment.filter(e => e.status === 'failed').length,
    critical:    Object.values(healthMap).filter(h => h.health_score < 40).length,
  };

  const resetForm = () => setFormData({
    equipment_name: '', equipment_type: '', manufacturer: '',
    installation_date: '', status: 'operational'
  });

  const openModal = (mode, item = null) => {
    setModalMode(mode);
    if (mode === 'edit' && item) {
      setCurrentEq(item);
      setFormData({
        equipment_name: item.equipment_name, equipment_type: item.equipment_type,
        manufacturer: item.manufacturer || '', installation_date: item.installation_date || '',
        status: item.status
      });
    } else { setCurrentEq(null); resetForm(); }
    setShowModal(true);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (modalMode === 'add') {
        await fetch(`${API}/api/equipment/`, {
          method: 'POST', headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(formData)
        });
      } else {
        await fetch(`${API}/api/equipment/${currentEq.equipment_id}`, {
          method: 'PUT', headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(formData)
        });
      }
      setShowModal(false); resetForm(); fetchEquipment();
    } catch (e) { console.error(e); }
  };

  const handleDelete = async () => {
    await fetch(`${API}/api/equipment/${deleteId}`, { method: 'DELETE' });
    setShowDeleteModal(false); setDeleteId(null); fetchEquipment();
  };

  if (selectedEq) return <EquipmentDetail equipment={selectedEq} onBack={() => setSelectedEq(null)} />;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-2xl font-heading font-bold text-white flex items-center gap-2">
            <Settings className="w-6 h-6 text-orange-500" /> Equipment Management
          </h1>
          <p className="text-slate-400 text-sm mt-0.5">Central asset registry · Steel Manufacturing Plant</p>
        </div>
        <button onClick={() => openModal('add')}
          className="flex items-center gap-2 px-4 py-2 bg-orange-500 hover:bg-orange-600 text-white rounded-lg font-medium text-sm transition-colors">
          <Plus className="w-4 h-4" /> Add Equipment
        </button>
      </div>

      {/* Summary KPI cards */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
        {[
          { label: 'Total',       val: summary.total,       color: 'text-white',    bg: 'bg-slate-500/10 border-slate-500/20' },
          { label: 'Operational', val: summary.operational, color: 'text-green-400', bg: 'bg-green-500/10 border-green-500/20' },
          { label: 'Maintenance', val: summary.maintenance, color: 'text-yellow-400',bg: 'bg-yellow-500/10 border-yellow-500/20' },
          { label: 'Failed',      val: summary.failed,      color: 'text-red-400',   bg: 'bg-red-500/10 border-red-500/20' },
          { label: 'Critical Health', val: summary.critical, color: 'text-orange-400',bg: 'bg-orange-500/10 border-orange-500/20' },
        ].map(({ label, val, color, bg }) => (
          <div key={label} className={`rounded-xl border p-4 text-center ${bg}`}>
            <div className={`text-2xl font-heading font-bold ${color}`}>{val}</div>
            <div className="text-xs text-slate-400 mt-1">{label}</div>
          </div>
        ))}
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-3">
        <div className="relative flex-1 min-w-[200px] max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
          <input value={searchTerm} onChange={e => setSearchTerm(e.target.value)}
            placeholder="Search equipment name..."
            className="input-industrial pl-9 text-sm" />
        </div>
        <select value={filterStatus} onChange={e => setFilterStatus(e.target.value)} className="select-industrial text-sm w-36">
          <option value="">All Status</option>
          {STATUS_OPTIONS.map(s => <option key={s} value={s}>{s.charAt(0).toUpperCase()+s.slice(1)}</option>)}
        </select>
        <select value={filterType} onChange={e => setFilterType(e.target.value)} className="select-industrial text-sm w-36">
          <option value="">All Types</option>
          {EQUIPMENT_TYPES.map(t => <option key={t} value={t}>{t}</option>)}
        </select>
      </div>

      {/* Equipment Table */}
      <Card className="overflow-hidden">
        {loading ? (
          <div className="flex items-center justify-center py-16">
            <div className="w-8 h-8 border-2 border-orange-500 border-t-transparent rounded-full animate-spin" />
          </div>
        ) : equipment.length === 0 ? (
          <div className="text-center py-16">
            <Settings className="w-12 h-12 text-slate-600 mx-auto mb-3" />
            <p className="text-slate-400">No equipment found</p>
            <button onClick={() => openModal('add')}
              className="mt-4 px-4 py-2 bg-orange-500 hover:bg-orange-600 text-white rounded-lg text-sm">
              Add Equipment
            </button>
          </div>
        ) : (
          <table className="industrial-table">
            <thead>
              <tr>
                <th>Equipment Name</th>
                <th>Type</th>
                <th>Manufacturer</th>
                <th>Installed</th>
                <th>Health</th>
                <th>Status</th>
                <th className="text-right">Actions</th>
              </tr>
            </thead>
            <tbody>
              {equipment.map(eq => {
                const h = healthMap[eq.equipment_id];
                const hs = h?.health_score ?? 100;
                const hc = healthColor(hs);
                return (
                  <tr key={eq.equipment_id} className="cursor-pointer" onClick={() => setSelectedEq(eq)}>
                    <td>
                      <div className="flex items-center gap-2">
                        <div className="w-7 h-7 rounded-lg bg-orange-500/10 border border-orange-500/20 flex items-center justify-center flex-shrink-0">
                          <Settings className="w-3.5 h-3.5 text-orange-400" />
                        </div>
                        <span className="font-medium">{eq.equipment_name}</span>
                      </div>
                    </td>
                    <td className="text-slate-400">{eq.equipment_type}</td>
                    <td className="text-slate-400">{eq.manufacturer || '—'}</td>
                    <td className="text-slate-400 font-mono text-xs">{eq.installation_date || '—'}</td>
                    <td>
                      <div className="flex items-center gap-2">
                        <div className="w-16 bg-[#0F1419] rounded-full h-1.5">
                          <div className="h-1.5 rounded-full" style={{ width: `${hs}%`, backgroundColor: hc }} />
                        </div>
                        <span className="text-xs font-mono" style={{ color: hc }}>{hs}%</span>
                      </div>
                    </td>
                    <td onClick={e => e.stopPropagation()}>
                      <span className={`flex items-center gap-1.5 w-fit px-2 py-1 rounded border text-xs font-medium ${statusColor(eq.status)}`}>
                        <span className={`w-1.5 h-1.5 rounded-full ${statusDot(eq.status)}`} />
                        {eq.status?.charAt(0).toUpperCase() + eq.status?.slice(1)}
                      </span>
                    </td>
                    <td className="text-right" onClick={e => e.stopPropagation()}>
                      <div className="flex items-center justify-end gap-1">
                        <button onClick={() => setSelectedEq(eq)}
                          className="p-1.5 text-blue-400 hover:bg-blue-500/20 rounded transition-colors" title="View">
                          <Eye className="w-4 h-4" />
                        </button>
                        <button onClick={() => openModal('edit', eq)}
                          className="p-1.5 text-slate-400 hover:bg-slate-500/20 rounded transition-colors" title="Edit">
                          <Edit2 className="w-4 h-4" />
                        </button>
                        <button onClick={() => { setDeleteId(eq.equipment_id); setShowDeleteModal(true); }}
                          className="p-1.5 text-red-400 hover:bg-red-500/20 rounded transition-colors" title="Delete">
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </Card>

      {/* Add / Edit Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
          <Card className="w-full max-w-lg">
            <div className="flex items-center justify-between p-5 border-b border-[#334155]">
              <h2 className="text-lg font-heading font-semibold text-white">
                {modalMode === 'add' ? 'Add New Equipment' : 'Edit Equipment'}
              </h2>
              <button onClick={() => setShowModal(false)} className="text-slate-400 hover:text-white">
                <X className="w-5 h-5" />
              </button>
            </div>
            <form onSubmit={handleSubmit} className="p-5 space-y-4">
              <div>
                <label className="block text-xs text-slate-400 mb-1">Equipment Name *</label>
                <input name="equipment_name" value={formData.equipment_name} required
                  onChange={e => setFormData({...formData, equipment_name: e.target.value})}
                  className="input-industrial" />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs text-slate-400 mb-1">Type *</label>
                  <select name="equipment_type" value={formData.equipment_type} required
                    onChange={e => setFormData({...formData, equipment_type: e.target.value})}
                    className="select-industrial">
                    <option value="">Select...</option>
                    {EQUIPMENT_TYPES.map(t => <option key={t} value={t}>{t}</option>)}
                  </select>
                </div>
                <div>
                  <label className="block text-xs text-slate-400 mb-1">Status</label>
                  <select value={formData.status}
                    onChange={e => setFormData({...formData, status: e.target.value})}
                    className="select-industrial">
                    {STATUS_OPTIONS.map(s => <option key={s} value={s}>{s.charAt(0).toUpperCase()+s.slice(1)}</option>)}
                  </select>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs text-slate-400 mb-1">Manufacturer</label>
                  <input value={formData.manufacturer}
                    onChange={e => setFormData({...formData, manufacturer: e.target.value})}
                    className="input-industrial" />
                </div>
                <div>
                  <label className="block text-xs text-slate-400 mb-1">Installation Date</label>
                  <input type="date" value={formData.installation_date}
                    onChange={e => setFormData({...formData, installation_date: e.target.value})}
                    className="input-industrial" />
                </div>
              </div>
              <div className="flex gap-3 pt-2">
                <button type="submit" className="flex-1 py-2 bg-orange-500 hover:bg-orange-600 text-white rounded-lg font-medium text-sm transition-colors">
                  {modalMode === 'add' ? 'Add Equipment' : 'Save Changes'}
                </button>
                <button type="button" onClick={() => setShowModal(false)}
                  className="flex-1 py-2 bg-[#334155] hover:bg-[#475569] text-white rounded-lg font-medium text-sm transition-colors">
                  Cancel
                </button>
              </div>
            </form>
          </Card>
        </div>
      )}

      {/* Delete Modal */}
      {showDeleteModal && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
          <Card className="w-full max-w-sm p-6 text-center">
            <div className="w-12 h-12 bg-red-500/20 rounded-full flex items-center justify-center mx-auto mb-4">
              <Trash2 className="w-6 h-6 text-red-400" />
            </div>
            <h3 className="text-lg font-heading font-semibold text-white mb-2">Delete Equipment</h3>
            <p className="text-slate-400 text-sm mb-6">This action cannot be undone.</p>
            <div className="flex gap-3">
              <button onClick={handleDelete}
                className="flex-1 py-2 bg-red-600 hover:bg-red-500 text-white rounded-lg text-sm font-medium transition-colors">Delete</button>
              <button onClick={() => setShowDeleteModal(false)}
                className="flex-1 py-2 bg-[#334155] hover:bg-[#475569] text-white rounded-lg text-sm font-medium transition-colors">Cancel</button>
            </div>
          </Card>
        </div>
      )}
    </div>
  );
}
