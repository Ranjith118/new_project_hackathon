import { useState, useEffect, useCallback } from 'react';
import {
  FileText, BarChart3, AlertTriangle, Package, Brain,
  Shield, Wrench, RefreshCw, Download, Printer,
  CheckCircle, AlertCircle, Activity, Zap, Target
} from 'lucide-react';
import {
  BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, Tooltip, ResponsiveContainer, Legend
} from 'recharts';

const API = 'http://localhost:8000';
const get = (u) => fetch(API + u).then(r => r.json()).catch(() => null);
const CHART_COLORS = ['#EF4444','#F97316','#FBBF24','#10B981','#3B82F6','#8B5CF6'];

const Card = ({ children, className = '' }) => (
  <div className={`bg-[#1E293B] border border-[#334155] rounded-xl ${className}`}>{children}</div>
);
const TabBtn = ({ label, active, onClick, badge }) => (
  <button onClick={onClick}
    className={`flex items-center gap-1.5 px-3 py-2 text-xs font-medium rounded-lg transition-all ${active ? 'bg-orange-500 text-white' : 'text-slate-400 hover:text-white hover:bg-[#334155]'}`}>
    {label}
    {badge != null && <span className={`text-[10px] px-1.5 py-0.5 rounded-full ${active ? 'bg-white/20' : 'bg-[#334155] text-slate-400'}`}>{badge}</span>}
  </button>
);

function exportCSV(rows, filename) {
  if (!rows || !rows.length) return;
  const keys = Object.keys(rows[0]);
  const csv  = [keys.join(','), ...rows.map(r => keys.map(k => JSON.stringify(r[k] ?? '')).join(','))].join('\n');
  const blob = new Blob([csv], { type: 'text/csv' });
  const a    = Object.assign(document.createElement('a'), { href: URL.createObjectURL(blob), download: filename + '.csv' });
  a.click(); URL.revokeObjectURL(a.href);
}

export default function ReportsAnalytics() {
  const [tab,        setTab]        = useState(0);
  const [data,       setData]       = useState({});
  const [loading,    setLoading]    = useState(true);
  const [lastUpdate, setLastUpdate] = useState(null);

  const load = useCallback(async () => {
    const [
      stats, health, alertSum, alerts, preds, rank, inv,
      spares, rcaDash, patterns, learn, prioSum, critSum, reorders, maintLogs
    ] = await Promise.all([
      get('/api/dashboard/stats'),
      get('/api/anomaly/health-status'),
      get('/api/anomaly/alerts/summary'),
      get('/api/anomaly/alerts?limit=50'),
      get('/api/prediction/equipment-predictions'),
      get('/api/decision-support/equipment-ranking'),
      get('/api/procurement/inventory-summary'),
      get('/api/procurement/spares'),
      get('/api/rca/dashboard'),
      get('/api/rca/patterns'),
      get('/api/learning/summary/quick'),
      get('/api/decision-support/priorities/summary'),
      get('/api/decision-support/criticality/summary'),
      get('/api/procurement/reorder'),
      get('/api/maintenance-logs/?limit=20'),
    ]);
    setData({ stats, health, alertSum, alerts, preds, rank, inv, spares, rcaDash, patterns, learn, prioSum, critSum, reorders, maintLogs });
    setLastUpdate(new Date());
    setLoading(false);
  }, []);

  useEffect(() => { load(); }, [load]);

  const d         = data;
  const healthPct = d.health?.overall_health_percentage ?? 0;
  const invHealth = d.inv ? Math.round((d.inv.in_stock / Math.max(d.inv.total_parts, 1)) * 100) : 0;
  const parts     = d.spares?.parts || [];
  const rankings  = d.rank?.rankings || [];
  const alerts    = d.alerts?.alerts || [];
  const preds     = (d.preds?.predictions || []).filter((p, i, a) => a.findIndex(x => x.equipment_name === p.equipment_name) === i);
  const logs      = Array.isArray(d.maintLogs) ? d.maintLogs : [];
  const reorders  = d.reorders?.recommendations || [];

  const healthChart   = (d.health?.equipment || []).map(e => ({ name: e.equipment_name.split(' ').slice(-1)[0], score: e.health_score }));
  const alertsByType  = [
    { name: 'Critical', count: d.alertSum?.by_type?.critical || 0 },
    { name: 'High',     count: d.alertSum?.by_type?.high     || 0 },
    { name: 'Medium',   count: d.alertSum?.by_type?.medium   || 0 },
  ].filter(a => a.count > 0);
  const causePie = (d.rcaDash?.common_causes || []).map(c => ({ name: c.cause, value: c.percentage }));

  const aiInsights = [];
  if (d.alertSum?.critical_count > 0)
    aiInsights.push({ icon: AlertTriangle, color: 'text-red-400', text: d.alertSum.critical_count + ' critical alerts require immediate attention.' });
  if (rankings.length > 0 && rankings[0]?.rul_days <= 14)
    aiInsights.push({ icon: Brain, color: 'text-orange-400', text: rankings.filter(r => r.rul_days <= 14).length + ' equipment may fail within 14 days. Immediate action required.' });
  if ((d.inv?.out_of_stock || 0) > 0)
    aiInsights.push({ icon: Package, color: 'text-red-400', text: d.inv.out_of_stock + ' spare parts are out of stock. Procurement risk is high.' });
  if ((d.inv?.low_stock || 0) > 0)
    aiInsights.push({ icon: Package, color: 'text-yellow-400', text: d.inv.low_stock + ' parts below minimum stock. Order before next maintenance cycle.' });
  if (d.rcaDash?.common_causes?.length > 0)
    aiInsights.push({ icon: Shield, color: 'text-blue-400', text: d.rcaDash.common_causes[0].cause + ' is the most common failure cause (' + d.rcaDash.common_causes[0].percentage + '% of cases).' });
  if ((d.prioSum?.p1_count || 0) > 0)
    aiInsights.push({ icon: Zap, color: 'text-red-400', text: d.prioSum.p1_count + ' equipment classified as P1 Critical requiring immediate maintenance.' });

  const TABS = [
    { label: 'Executive Summary' },
    { label: 'Equipment Health',    badge: d.health?.total_equipment },
    { label: 'Failure Predictions', badge: preds.length },
    { label: 'Alerts Report',       badge: d.alertSum?.active },
    { label: 'Maintenance Logs',    badge: logs.length },
    { label: 'Inventory Report',    badge: d.inv?.total_parts },
    { label: 'Priority Ranking',    badge: rankings.length },
    { label: 'AI Insights' },
  ];

  if (loading) return (
    <div className="flex items-center justify-center h-64">
      <div className="w-8 h-8 border-2 border-orange-500 border-t-transparent rounded-full animate-spin" />
    </div>
  );

  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-2xl font-heading font-bold text-white flex items-center gap-2">
            <FileText className="w-6 h-6 text-orange-500" /> Reports & Analytics Center
          </h1>
          <p className="text-slate-400 text-sm mt-0.5">
            Executive reporting · KPIs · Trend analysis · {lastUpdate ? 'Updated ' + lastUpdate.toLocaleTimeString() : ''}
          </p>
        </div>
        <div className="flex gap-2">
          <button onClick={() => window.print()}
            className="flex items-center gap-1.5 px-3 py-2 bg-[#1E293B] border border-[#334155] hover:border-orange-500/40 text-slate-300 text-sm rounded-lg transition-all">
            <Printer className="w-4 h-4 text-orange-400" /> Print
          </button>
          <button onClick={load}
            className="p-2 bg-[#1E293B] border border-[#334155] hover:border-orange-500/40 text-slate-400 hover:text-white rounded-lg transition-all">
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Global KPIs */}
      <div className="grid grid-cols-2 md:grid-cols-4 xl:grid-cols-7 gap-3">
        {[
          { label: 'Equipment',     val: d.stats?.total_equipment ?? 0,      color: 'text-white',     bg: 'bg-slate-500/10 border-slate-500/20' },
          { label: 'Active Alerts', val: d.alertSum?.active ?? 0,            color: 'text-red-400',   bg: 'bg-red-500/10 border-red-500/20' },
          { label: 'Critical',      val: d.alertSum?.critical_count ?? 0,    color: 'text-red-400',   bg: 'bg-red-500/10 border-red-500/20' },
          { label: 'Plant Health',  val: healthPct.toFixed(0) + '%',         color: healthPct >= 80 ? 'text-green-400' : 'text-yellow-400', bg: 'bg-green-500/10 border-green-500/20' },
          { label: 'Fail Predicted',val: preds.filter(p => p.failure_probability > 50).length, color: 'text-orange-400', bg: 'bg-orange-500/10 border-orange-500/20' },
          { label: 'Inv Health',    val: invHealth + '%',                    color: invHealth >= 70 ? 'text-green-400' : 'text-yellow-400', bg: 'bg-yellow-500/10 border-yellow-500/20' },
          { label: 'Maint Logs',    val: d.stats?.total_maintenance_logs ?? 0, color: 'text-blue-400', bg: 'bg-blue-500/10 border-blue-500/20' },
        ].map(({ label, val, color, bg }) => (
          <div key={label} className={`rounded-xl border p-3 text-center ${bg}`}>
            <div className={`text-xl font-heading font-bold ${color}`}>{val}</div>
            <div className="text-[9px] text-slate-400 mt-1">{label}</div>
          </div>
        ))}
      </div>

      {/* Tabs */}
      <div className="flex gap-1 flex-wrap bg-[#1E293B] p-1 rounded-xl border border-[#334155]">
        {TABS.map((t, i) => <TabBtn key={t.label} label={t.label} badge={t.badge} active={tab === i} onClick={() => setTab(i)} />)}
      </div>

      {/* TAB 0: Executive Summary */}
      {tab === 0 && (
        <div className="space-y-5">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-heading font-semibold text-white">Executive Summary Report</h2>
            <button onClick={() => exportCSV([
              { metric: 'Plant Health',          value: healthPct.toFixed(1) + '%' },
              { metric: 'Total Equipment',        value: d.stats?.total_equipment },
              { metric: 'Operational',            value: d.stats?.operational_equipment },
              { metric: 'Active Alerts',          value: d.alertSum?.active },
              { metric: 'Critical Alerts',        value: d.alertSum?.critical_count },
              { metric: 'Inventory Health',       value: invHealth + '%' },
              { metric: 'P1 Critical Equipment',  value: d.prioSum?.p1_count },
              { metric: 'Total Downtime Est (hr)',value: d.prioSum?.total_estimated_downtime },
              { metric: 'Maintenance Logs',       value: d.stats?.total_maintenance_logs },
              { metric: 'Failure Reports',        value: d.stats?.total_failure_reports },
              { metric: 'RCA Analyses',           value: d.rcaDash?.total_analyses },
              { metric: 'Avg RCA Confidence',     value: d.rcaDash?.average_confidence + '%' },
            ], 'executive-summary')}
              className="flex items-center gap-1.5 px-3 py-1.5 bg-green-500/10 border border-green-500/30 text-green-400 text-xs rounded-lg hover:bg-green-500/20 transition-colors">
              <Download className="w-3.5 h-3.5" /> Export CSV
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {[
              { title: 'Plant Health',        val: healthPct.toFixed(1) + '%', sub: (d.health?.healthy_count || 0) + ' healthy equipment', icon: Activity, color: '#10B981' },
              { title: 'Active Alerts',       val: d.alertSum?.active ?? 0,    sub: (d.alertSum?.critical_count || 0) + ' critical',       icon: AlertTriangle, color: '#EF4444' },
              { title: 'Inventory Status',    val: invHealth + '%',            sub: (d.inv?.out_of_stock || 0) + ' parts out of stock',    icon: Package,       color: invHealth >= 70 ? '#10B981' : '#FBBF24' },
              { title: 'P1+P2 Priority',      val: (d.prioSum?.p1_count || 0) + (d.prioSum?.p2_count || 0), sub: 'critical/high items pending', icon: Wrench, color: '#F97316' },
            ].map(({ title, val, sub, icon: Icon, color }) => (
              <Card key={title} className="p-5" style={{ borderLeft: `4px solid ${color}` }}>
                <div className="flex items-start justify-between">
                  <div>
                    <div className="text-xs text-slate-400 mb-1">{title}</div>
                    <div className="text-3xl font-heading font-bold" style={{ color }}>{val}</div>
                    <div className="text-xs text-slate-500 mt-1">{sub}</div>
                  </div>
                  <Icon className="w-6 h-6" style={{ color }} />
                </div>
              </Card>
            ))}
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
            <Card className="p-4">
              <h3 className="text-sm font-semibold text-white mb-3">Equipment Health Scores</h3>
              <ResponsiveContainer width="100%" height={180}>
                <BarChart data={healthChart} margin={{ left: -20 }}>
                  <XAxis dataKey="name" tick={{ fontSize: 9, fill: '#94A3B8' }} />
                  <YAxis tick={{ fontSize: 9, fill: '#64748B' }} domain={[0, 100]} />
                  <Tooltip contentStyle={{ background: '#1E293B', border: '1px solid #334155', fontSize: 10 }} />
                  <Bar dataKey="score" radius={[3, 3, 0, 0]}>
                    {healthChart.map((d, i) => <Cell key={i} fill={d.score >= 80 ? '#10B981' : d.score >= 60 ? '#FBBF24' : '#EF4444'} />)}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </Card>
            <Card className="p-4">
              <h3 className="text-sm font-semibold text-white mb-3">Alert Distribution</h3>
              <ResponsiveContainer width="100%" height={180}>
                <PieChart>
                  <Pie data={alertsByType} cx="50%" cy="50%" innerRadius={40} outerRadius={70} dataKey="count" nameKey="name" strokeWidth={0}>
                    {alertsByType.map((_, i) => <Cell key={i} fill={CHART_COLORS[i]} />)}
                  </Pie>
                  <Tooltip contentStyle={{ background: '#1E293B', border: '1px solid #334155', fontSize: 11 }} />
                  <Legend wrapperStyle={{ fontSize: 10, color: '#94A3B8' }} />
                </PieChart>
              </ResponsiveContainer>
            </Card>
            <Card className="p-4">
              <h3 className="text-sm font-semibold text-white mb-3">Root Cause Distribution</h3>
              {causePie.slice(0, 5).map((c, i) => (
                <div key={i} className="flex items-center gap-2 mb-2">
                  <div className="w-2.5 h-2.5 rounded-full flex-shrink-0" style={{ backgroundColor: CHART_COLORS[i] }} />
                  <span className="text-xs text-slate-300 flex-1 truncate">{c.name}</span>
                  <div className="w-20 bg-[#0F1419] rounded-full h-1.5 flex-shrink-0">
                    <div className="h-1.5 rounded-full" style={{ width: c.value + '%', backgroundColor: CHART_COLORS[i] }} />
                  </div>
                  <span className="text-[10px] font-mono text-slate-400 w-8">{c.value}%</span>
                </div>
              ))}
            </Card>
          </div>

          <Card className="p-5">
            <h3 className="text-sm font-semibold text-white mb-4">Key Metrics Summary</h3>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
              {[
                { label: 'Total Equipment',         val: d.stats?.total_equipment,            color: 'text-white' },
                { label: 'Operational',             val: d.stats?.operational_equipment,      color: 'text-green-400' },
                { label: 'Under Maintenance',       val: d.stats?.maintenance_equipment,      color: 'text-yellow-400' },
                { label: 'Failed Equipment',        val: d.stats?.failed_equipment,           color: 'text-red-400' },
                { label: 'Maintenance Logs Total',  val: d.stats?.total_maintenance_logs,     color: 'text-blue-400' },
                { label: 'Failure Reports Total',   val: d.stats?.total_failure_reports,      color: 'text-orange-400' },
                { label: 'P1 Critical Priority',    val: d.prioSum?.p1_count,                 color: 'text-red-400' },
                { label: 'Est. Total Downtime (hr)',val: d.prioSum?.total_estimated_downtime, color: 'text-yellow-400' },
                { label: 'Est. Maintenance Cost',   val: '₹' + (d.prioSum?.total_estimated_cost || 0).toLocaleString('en-IN'), color: 'text-blue-400' },
                { label: 'RCA Analyses Run',        val: d.rcaDash?.total_analyses,           color: 'text-purple-400' },
                { label: 'Avg RCA Confidence',      val: (d.rcaDash?.average_confidence || 0) + '%', color: 'text-green-400' },
                { label: 'AI Model Accuracy',       val: Math.round((d.learn?.average_accuracy || 0) * 100) + '%', color: 'text-cyan-400' },
              ].map(({ label, val }) => (
                <div key={label} className="flex justify-between text-xs py-1.5 border-b border-[#334155] last:border-0">
                  <span className="text-slate-400">{label}</span>
                  <span className="font-mono font-bold text-white">{val}</span>
                </div>
              ))}
            </div>
          </Card>
        </div>
      )}

      {/* TAB 1: Equipment Health */}
      {tab === 1 && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-heading font-semibold text-white">Equipment Health Report</h2>
            <button onClick={() => exportCSV((d.health?.equipment || []).map(e => ({ Equipment: e.equipment_name, HealthScore: e.health_score, Status: e.health_status, RiskLevel: e.risk_level, Trend: e.trend, Anomalies: e.anomaly_count })), 'equipment-health')}
              className="flex items-center gap-1.5 px-3 py-1.5 bg-green-500/10 border border-green-500/30 text-green-400 text-xs rounded-lg hover:bg-green-500/20 transition-colors">
              <Download className="w-3.5 h-3.5" /> Export CSV
            </button>
          </div>
          <Card className="overflow-hidden">
            <table className="industrial-table">
              <thead><tr><th>Equipment</th><th>Health Score</th><th>Status</th><th>Risk Level</th><th>Trend</th><th>Anomalies</th></tr></thead>
              <tbody>
                {(d.health?.equipment || []).map((e, i) => {
                  const hc = e.health_score >= 80 ? '#10B981' : e.health_score >= 60 ? '#FBBF24' : '#EF4444';
                  return (
                    <tr key={i}>
                      <td className="font-medium">{e.equipment_name}</td>
                      <td>
                        <div className="flex items-center gap-2">
                          <div className="w-20 bg-[#0F1419] rounded-full h-1.5">
                            <div className="h-1.5 rounded-full" style={{ width: e.health_score + '%', backgroundColor: hc }} />
                          </div>
                          <span className="font-mono text-sm font-bold" style={{ color: hc }}>{e.health_score}%</span>
                        </div>
                      </td>
                      <td><span className="text-xs px-2 py-0.5 rounded" style={{ backgroundColor: hc + '20', color: hc }}>{e.health_status}</span></td>
                      <td className="text-slate-300 text-xs">{e.risk_level}</td>
                      <td><span className={`text-xs ${e.trend === 'improving' ? 'text-green-400' : e.trend === 'declining' ? 'text-red-400' : 'text-slate-400'}`}>{e.trend}</span></td>
                      <td className="font-mono text-slate-400 text-sm">{e.anomaly_count || 0}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </Card>
        </div>
      )}

      {/* TAB 2: Failure Predictions */}
      {tab === 2 && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-heading font-semibold text-white">Failure Prediction Report</h2>
            <button onClick={() => exportCSV(preds.map(p => ({ Equipment: p.equipment_name, FailureProb: p.failure_probability + '%', RUL: p.rul_days + 'd', RiskLevel: p.risk_level, Degradation: p.degradation_level })), 'failure-predictions')}
              className="flex items-center gap-1.5 px-3 py-1.5 bg-green-500/10 border border-green-500/30 text-green-400 text-xs rounded-lg hover:bg-green-500/20 transition-colors">
              <Download className="w-3.5 h-3.5" /> Export CSV
            </button>
          </div>
          <Card className="overflow-hidden">
            <table className="industrial-table">
              <thead><tr><th>Equipment</th><th>Failure Probability</th><th>RUL (days)</th><th>Health Score</th><th>Risk Level</th><th>Degradation</th></tr></thead>
              <tbody>
                {preds.map((p, i) => {
                  const fc = p.failure_probability > 70 ? '#EF4444' : p.failure_probability > 40 ? '#F97316' : '#10B981';
                  return (
                    <tr key={i}>
                      <td className="font-medium">{p.equipment_name}</td>
                      <td>
                        <div className="flex items-center gap-2">
                          <div className="w-16 bg-[#0F1419] rounded-full h-1.5">
                            <div className="h-1.5 rounded-full" style={{ width: p.failure_probability + '%', backgroundColor: fc }} />
                          </div>
                          <span className="font-mono text-sm font-bold" style={{ color: fc }}>{p.failure_probability?.toFixed(1)}%</span>
                        </div>
                      </td>
                      <td><span className={`font-mono ${p.rul_days <= 14 ? 'text-red-400 font-bold' : 'text-slate-300'}`}>{p.rul_days}d</span></td>
                      <td><span className="font-mono text-slate-300">{p.health_score}%</span></td>
                      <td className="text-slate-300 text-xs">{p.risk_level}</td>
                      <td className="text-slate-400 text-xs capitalize">{p.degradation_level?.replace(/_/g,' ')}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </Card>
        </div>
      )}

      {/* TAB 3: Alerts Report */}
      {tab === 3 && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-heading font-semibold text-white">Alert Report</h2>
            <button onClick={() => exportCSV(alerts.map(a => ({ Equipment: a.equipment_name, Type: a.alert_type, Message: a.message, Status: a.status, Source: a.source, Time: a.timestamp })), 'alerts')}
              className="flex items-center gap-1.5 px-3 py-1.5 bg-green-500/10 border border-green-500/30 text-green-400 text-xs rounded-lg hover:bg-green-500/20 transition-colors">
              <Download className="w-3.5 h-3.5" /> Export CSV
            </button>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {[
              { label: 'Total', val: d.alertSum?.total ?? 0, color: 'text-white' },
              { label: 'Active', val: d.alertSum?.active ?? 0, color: 'text-red-400' },
              { label: 'Critical', val: d.alertSum?.critical_count ?? 0, color: 'text-red-400' },
              { label: 'Resolved', val: d.alertSum?.resolved ?? 0, color: 'text-green-400' },
            ].map(({ label, val, color }) => (
              <div key={label} className="bg-[#0F1419] rounded-xl border border-[#334155] p-3 text-center">
                <div className={`text-2xl font-bold ${color}`}>{val}</div>
                <div className="text-[10px] text-slate-500">{label}</div>
              </div>
            ))}
          </div>
          <Card className="overflow-hidden">
            <table className="industrial-table">
              <thead><tr><th>Equipment</th><th>Severity</th><th>Message</th><th>Source</th><th>Status</th><th>Time</th></tr></thead>
              <tbody>
                {alerts.map((a, i) => {
                  const c = { critical: '#EF4444', high: '#F97316', medium: '#FBBF24', low: '#10B981' }[a.alert_type] || '#94A3B8';
                  return (
                    <tr key={i}>
                      <td className="font-medium">{a.equipment_name}</td>
                      <td><span className="text-xs px-2 py-0.5 rounded font-bold" style={{ backgroundColor: c + '20', color: c }}>{a.alert_type?.toUpperCase()}</span></td>
                      <td className="text-slate-300 text-xs max-w-[200px]"><span className="truncate block">{a.message}</span></td>
                      <td className="text-slate-400 text-xs capitalize">{a.source}</td>
                      <td><span className={`text-xs ${a.status === 'active' ? 'text-red-400' : a.status === 'resolved' ? 'text-green-400' : 'text-yellow-400'}`}>{a.status}</span></td>
                      <td className="text-slate-500 text-xs font-mono">{new Date(a.timestamp).toLocaleTimeString()}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </Card>
        </div>
      )}

      {/* TAB 4: Maintenance Logs */}
      {tab === 4 && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-heading font-semibold text-white">Maintenance History Report</h2>
            <button onClick={() => exportCSV(logs.map(l => ({ Equipment: l.equipment_name, Issue: l.issue, Action: l.action_taken, Severity: l.severity, Technician: l.technician, Downtime: l.downtime_hours, Date: l.maintenance_date })), 'maintenance-logs')}
              className="flex items-center gap-1.5 px-3 py-1.5 bg-green-500/10 border border-green-500/30 text-green-400 text-xs rounded-lg hover:bg-green-500/20 transition-colors">
              <Download className="w-3.5 h-3.5" /> Export CSV
            </button>
          </div>
          <Card className="overflow-hidden">
            <table className="industrial-table">
              <thead><tr><th>Date</th><th>Equipment</th><th>Issue</th><th>Action Taken</th><th>Severity</th><th>Technician</th><th>Downtime</th></tr></thead>
              <tbody>
                {logs.map((l, i) => {
                  const sc = { critical: '#EF4444', high: '#F97316', medium: '#FBBF24', low: '#10B981' }[l.severity] || '#94A3B8';
                  return (
                    <tr key={i}>
                      <td className="font-mono text-xs">{l.maintenance_date}</td>
                      <td className="font-medium">{l.equipment_name}</td>
                      <td className="text-slate-300 text-xs max-w-[150px]"><span className="truncate block">{l.issue}</span></td>
                      <td className="text-slate-300 text-xs max-w-[150px]"><span className="truncate block">{l.action_taken || '—'}</span></td>
                      <td><span className="text-xs px-1.5 py-0.5 rounded font-bold" style={{ backgroundColor: sc + '20', color: sc }}>{l.severity}</span></td>
                      <td className="text-slate-400 text-xs">{l.technician || '—'}</td>
                      <td className="font-mono text-xs text-slate-300">{l.downtime_hours}h</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </Card>
        </div>
      )}

      {/* TAB 5: Inventory Report */}
      {tab === 5 && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-heading font-semibold text-white">Inventory & Procurement Report</h2>
            <button onClick={() => exportCSV(parts.map(p => ({ PartName: p.part_name, PartNo: p.part_number, Category: p.category, Stock: p.stock_quantity, MinStock: p.minimum_stock, Status: p.status, Supplier: p.supplier, LeadTime: p.lead_time_days })), 'inventory')}
              className="flex items-center gap-1.5 px-3 py-1.5 bg-green-500/10 border border-green-500/30 text-green-400 text-xs rounded-lg hover:bg-green-500/20 transition-colors">
              <Download className="w-3.5 h-3.5" /> Export CSV
            </button>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {[
              { label: 'Total Parts',  val: d.inv?.total_parts ?? 0,     color: 'text-white' },
              { label: 'In Stock',     val: d.inv?.in_stock ?? 0,        color: 'text-green-400' },
              { label: 'Low Stock',    val: d.inv?.low_stock ?? 0,       color: 'text-yellow-400' },
              { label: 'Out of Stock', val: d.inv?.out_of_stock ?? 0,    color: 'text-red-400' },
            ].map(({ label, val, color }) => (
              <div key={label} className="bg-[#0F1419] rounded-xl border border-[#334155] p-3 text-center">
                <div className={`text-2xl font-bold ${color}`}>{val}</div>
                <div className="text-[10px] text-slate-500">{label}</div>
              </div>
            ))}
          </div>
          <Card className="overflow-hidden">
            <table className="industrial-table">
              <thead><tr><th>Part Name</th><th>Part No</th><th>Category</th><th>Stock</th><th>Min Stock</th><th>Status</th><th>Lead Time</th><th>Cost</th></tr></thead>
              <tbody>
                {parts.map((p, i) => {
                  const sc = { in_stock: '#10B981', low_stock: '#FBBF24', reorder_required: '#F97316', out_of_stock: '#EF4444' }[p.status] || '#94A3B8';
                  return (
                    <tr key={i}>
                      <td className="font-medium">{p.part_name}</td>
                      <td className="font-mono text-xs text-orange-400">{p.part_number}</td>
                      <td className="text-slate-400 text-xs">{p.category}</td>
                      <td className="font-mono font-bold" style={{ color: sc }}>{p.stock_quantity}</td>
                      <td className="font-mono text-slate-400">{p.minimum_stock}</td>
                      <td><span className="text-xs px-1.5 py-0.5 rounded" style={{ backgroundColor: sc + '20', color: sc }}>{p.status?.replace(/_/g,' ')}</span></td>
                      <td className="font-mono text-slate-300 text-xs">{p.lead_time_days}d</td>
                      <td className="font-mono text-slate-300 text-xs">{p.unit_cost ? '₹' + p.unit_cost.toLocaleString('en-IN') : '—'}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </Card>
        </div>
      )}

      {/* TAB 6: Priority Ranking */}
      {tab === 6 && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-heading font-semibold text-white">Plant Priority Ranking Report</h2>
            <button onClick={() => exportCSV(rankings.map(r => ({ Rank: r.rank, Equipment: r.equipment_name, PriorityScore: r.priority_score?.toFixed(1), FailureProb: (r.failure_probability * 100).toFixed(0) + '%', RUL: r.rul_days + 'd', Priority: r.priority_level, Action: r.recommended_action })), 'priority-ranking')}
              className="flex items-center gap-1.5 px-3 py-1.5 bg-green-500/10 border border-green-500/30 text-green-400 text-xs rounded-lg hover:bg-green-500/20 transition-colors">
              <Download className="w-3.5 h-3.5" /> Export CSV
            </button>
          </div>
          <Card className="overflow-hidden">
            <table className="industrial-table">
              <thead><tr><th>Rank</th><th>Equipment</th><th>Priority Score</th><th>Failure Prob</th><th>RUL</th><th>Priority</th><th>Action</th></tr></thead>
              <tbody>
                {rankings.map((r, i) => {
                  const pc = { P1: '#EF4444', P2: '#F97316', P3: '#FBBF24', P4: '#10B981' }[r.priority_level] || '#94A3B8';
                  return (
                    <tr key={i}>
                      <td><div className="w-7 h-7 rounded flex items-center justify-center text-xs font-bold" style={{ backgroundColor: pc + '20', color: pc }}>{r.rank}</div></td>
                      <td className="font-medium">{r.equipment_name}</td>
                      <td><span className="font-mono font-bold" style={{ color: pc }}>{r.priority_score?.toFixed(1)}</span></td>
                      <td><span className="font-mono text-sm" style={{ color: pc }}>{(r.failure_probability * 100).toFixed(0)}%</span></td>
                      <td><span className={`font-mono ${r.rul_days <= 14 ? 'text-red-400 font-bold' : 'text-slate-300'}`}>{r.rul_days}d</span></td>
                      <td><span className="text-xs px-2 py-0.5 rounded border font-bold" style={{ backgroundColor: pc + '20', borderColor: pc + '40', color: pc }}>{r.priority_level}</span></td>
                      <td className="text-slate-300 text-xs max-w-[200px]"><span className="truncate block">{r.recommended_action}</span></td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </Card>
        </div>
      )}

      {/* TAB 7: AI Insights */}
      {tab === 7 && (
        <div className="space-y-5">
          <h2 className="text-lg font-heading font-semibold text-white">AI-Generated Insights & Analytics</h2>
          <Card className="p-5">
            <h3 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
              <Brain className="w-4 h-4 text-orange-400" /> AI Observations
            </h3>
            {aiInsights.length === 0 ? (
              <p className="text-slate-500 text-sm">No critical insights at this time.</p>
            ) : aiInsights.map((ins, i) => (
              <div key={i} className="flex items-start gap-3 p-3 bg-[#0F1419] rounded-lg border border-[#334155] mb-2 last:mb-0">
                <ins.icon className={`w-4 h-4 flex-shrink-0 mt-0.5 ${ins.color}`} />
                <span className="text-sm text-slate-300">{ins.text}</span>
              </div>
            ))}
          </Card>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
            <Card className="p-4">
              <h3 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
                <Target className="w-4 h-4 text-purple-400" /> AI Learning System
              </h3>
              {[
                { label: 'Total Feedback',     val: d.learn?.feedback_count },
                { label: 'Acceptance Rate',    val: Math.round((d.learn?.acceptance_rate || 0) * 100) + '%' },
                { label: 'Success Rate',       val: Math.round((d.learn?.success_rate || 0) * 100) + '%' },
                { label: 'Model Accuracy',     val: Math.round((d.learn?.average_accuracy || 0) * 100) + '%' },
                { label: 'Retraining Jobs',    val: d.learn?.retraining_jobs },
                { label: 'Recent Improvement', val: '+' + Math.round((d.learn?.recent_improvement || 0) * 100) + '%' },
              ].map(({ label, val }) => (
                <div key={label} className="flex justify-between text-xs py-1.5 border-b border-[#334155] last:border-0">
                  <span className="text-slate-400">{label}</span>
                  <span className="font-mono font-bold text-white">{val}</span>
                </div>
              ))}
            </Card>
            <Card className="p-4">
              <h3 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
                <Shield className="w-4 h-4 text-blue-400" /> RCA Engine Performance
              </h3>
              {[
                { label: 'Total Analyses',   val: d.rcaDash?.total_analyses },
                { label: 'Avg Confidence',   val: d.rcaDash?.average_confidence + '%' },
                { label: 'Top Root Cause',   val: d.rcaDash?.common_causes?.[0]?.cause },
                { label: 'Top Cause %',      val: d.rcaDash?.common_causes?.[0]?.percentage + '%' },
              ].map(({ label, val }) => (
                <div key={label} className="flex justify-between text-xs py-1.5 border-b border-[#334155] last:border-0">
                  <span className="text-slate-400">{label}</span>
                  <span className="font-mono font-bold text-white">{val}</span>
                </div>
              ))}
              <div className="mt-3 space-y-1.5">
                {(d.rcaDash?.common_causes || []).map((c, i) => (
                  <div key={i} className="flex items-center gap-2">
                    <span className="text-[10px] text-slate-400 w-28 truncate">{c.cause}</span>
                    <div className="flex-1 bg-[#0F1419] rounded-full h-1.5">
                      <div className="h-1.5 rounded-full" style={{ width: c.percentage + '%', backgroundColor: CHART_COLORS[i] }} />
                    </div>
                    <span className="text-[10px] font-mono text-slate-400 w-8">{c.percentage}%</span>
                  </div>
                ))}
              </div>
            </Card>
          </div>
        </div>
      )}
    </div>
  );
}
