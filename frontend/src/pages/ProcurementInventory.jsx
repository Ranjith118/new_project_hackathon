import { useState, useEffect, useCallback } from 'react';
import {
  Package, AlertTriangle, CheckCircle, RefreshCw, Search,
  ChevronRight, ChevronLeft, TrendingUp, Truck, Star,
  AlertCircle, Zap, BarChart3, ShoppingCart, Eye,
  Clock, DollarSign, MapPin, Phone, Mail, X, Filter
} from 'lucide-react';
import {
  BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, Tooltip, ResponsiveContainer
} from 'recharts';

const API = 'http://localhost:8000/api/procurement';
const get = (u) => fetch(API + u).then(r => r.json()).catch(() => null);

/* ── helpers ─────────────────────────────────────────────── */
const statusColor = (s) => ({
  in_stock:         '#10B981',
  low_stock:        '#FBBF24',
  reorder_required: '#F97316',
  out_of_stock:     '#EF4444',
})[s] || '#94A3B8';

const statusLabel = (s) => ({
  in_stock:         'In Stock',
  low_stock:        'Low Stock',
  reorder_required: 'Reorder Required',
  out_of_stock:     'Out of Stock',
})[s] || s;

const statusBg = (s) => ({
  in_stock:         'bg-green-500/10 border-green-500/30 text-green-400',
  low_stock:        'bg-yellow-500/10 border-yellow-500/30 text-yellow-400',
  reorder_required: 'bg-orange-500/10 border-orange-500/30 text-orange-400',
  out_of_stock:     'bg-red-500/10 border-red-500/30 text-red-400',
})[s] || 'bg-slate-500/10 border-slate-500/30 text-slate-400';

const urgencyBadge = (u) => ({
  critical: 'bg-red-500/20 text-red-400 border-red-500/40',
  high:     'bg-orange-500/20 text-orange-400 border-orange-500/40',
  medium:   'bg-yellow-500/20 text-yellow-400 border-yellow-500/40',
  low:      'bg-green-500/20 text-green-400 border-green-500/40',
})[u] || 'bg-slate-500/20 text-slate-400';

const Card = ({ children, className = '' }) => (
  <div className={`bg-[#1E293B] border border-[#334155] rounded-xl ${className}`}>{children}</div>
);

/* ── Stock bar ───────────────────────────────────────────── */
function StockBar({ current, minimum, maximum }) {
  const max   = maximum || minimum * 2 || 20;
  const pct   = Math.min(100, (current / max) * 100);
  const color = current === 0 ? '#EF4444' : current < minimum ? '#F97316' : current <= minimum * 1.3 ? '#FBBF24' : '#10B981';
  return (
    <div className="w-full">
      <div className="w-full bg-[#0F1419] rounded-full h-2">
        <div className="h-2 rounded-full transition-all" style={{ width: `${pct}%`, backgroundColor: color }} />
      </div>
      <div className="flex justify-between text-[10px] text-slate-500 mt-0.5">
        <span>Min: {minimum}</span>
        <span className="font-mono font-bold" style={{ color }}>{current}</span>
        <span>Max: {max}</span>
      </div>
    </div>
  );
}

/* ── Part Detail Panel ───────────────────────────────────── */
function PartDetail({ part, reorderRec, onBack }) {
  const [suppliers, setSuppliers] = useState([]);
  useEffect(() => {
    get('/suppliers').then(d => setSuppliers(d?.suppliers || []));
  }, []);

  const supplier = suppliers.find(s => s.supplier_name === part.supplier);
  const sc = statusColor(part.status);

  return (
    <div className="space-y-5">
      <button onClick={onBack} className="flex items-center gap-1 text-slate-400 hover:text-white text-sm transition-colors">
        <ChevronLeft className="w-4 h-4" /> Inventory Management
      </button>

      {/* Header */}
      <Card className="p-5 border-l-4" style={{ borderLeftColor: sc }}>
        <div className="flex items-start justify-between flex-wrap gap-4">
          <div className="flex items-center gap-4">
            <div className="w-14 h-14 rounded-xl bg-orange-500/10 border border-orange-500/20 flex items-center justify-center flex-shrink-0">
              <Package className="w-7 h-7 text-orange-400" />
            </div>
            <div>
              <h2 className="text-xl font-heading font-bold text-white">{part.part_name}</h2>
              <div className="flex items-center gap-3 mt-1 flex-wrap text-sm">
                <span className="font-mono text-orange-400">{part.part_number}</span>
                <span className="text-slate-600">·</span>
                <span className="text-slate-400">{part.category}</span>
                <span className="text-slate-600">·</span>
                <span className={`px-2 py-0.5 rounded border text-xs font-medium ${statusBg(part.status)}`}>{statusLabel(part.status)}</span>
              </div>
            </div>
          </div>
          <div className="text-right">
            <div className="text-4xl font-bold font-mono" style={{ color: sc }}>{part.stock_quantity}</div>
            <div className="text-xs text-slate-400">Current Stock</div>
          </div>
        </div>

        {/* Stock bar */}
        <div className="mt-5">
          <StockBar current={part.stock_quantity} minimum={part.minimum_stock} maximum={part.minimum_stock * 3} />
        </div>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        {/* Part info */}
        <Card className="p-4">
          <h3 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
            <Package className="w-4 h-4 text-orange-400" /> Part Information
          </h3>
          <div className="space-y-2">
            {[
              { label: 'Part Number',     val: part.part_number },
              { label: 'Category',        val: part.category },
              { label: 'Unit Cost',       val: part.unit_cost ? '₹' + part.unit_cost.toLocaleString('en-IN') : '—' },
              { label: 'Min Stock',       val: part.minimum_stock },
              { label: 'Reorder Level',   val: part.reorder_level },
              { label: 'Lead Time',       val: part.lead_time_days + ' days' },
              { label: 'Location',        val: part.location || '—' },
              { label: 'Equipment Type',  val: part.equipment_type || '—' },
              { label: 'Last Updated',    val: new Date(part.last_updated).toLocaleDateString() },
            ].map(({ label, val }) => (
              <div key={label} className="flex justify-between text-xs py-1.5 border-b border-[#334155] last:border-0">
                <span className="text-slate-400">{label}</span>
                <span className="text-white font-medium">{String(val)}</span>
              </div>
            ))}
          </div>
        </Card>

        {/* Supplier info */}
        <Card className="p-4">
          <h3 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
            <Truck className="w-4 h-4 text-blue-400" /> Supplier Information
          </h3>
          {supplier ? (
            <div className="space-y-2">
              <div className="flex items-center gap-2 mb-3">
                <span className="text-white font-semibold">{supplier.supplier_name}</span>
                {supplier.preferred_supplier && <Star className="w-3.5 h-3.5 text-yellow-400 fill-yellow-400" />}
              </div>
              {[
                { icon: Phone, val: supplier.phone },
                { icon: Mail,  val: supplier.email },
                { icon: MapPin,val: supplier.address?.split(',')[0] },
              ].map(({ icon: Icon, val }, i) => val && (
                <div key={i} className="flex items-center gap-2 text-xs text-slate-300">
                  <Icon className="w-3 h-3 text-slate-500 flex-shrink-0" />{val}
                </div>
              ))}
              <div className="grid grid-cols-3 gap-2 mt-4">
                {[
                  { label: 'Reliability',   val: supplier.reliability_score + '%',       color: 'text-green-400' },
                  { label: 'On-Time',       val: supplier.on_time_delivery_rate + '%',   color: 'text-blue-400' },
                  { label: 'Quality',       val: supplier.quality_score + '%',           color: 'text-purple-400' },
                ].map(({ label, val, color }) => (
                  <div key={label} className="bg-[#0F1419] rounded-lg p-2 border border-[#334155] text-center">
                    <div className={`text-sm font-bold ${color}`}>{val}</div>
                    <div className="text-[10px] text-slate-500">{label}</div>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div className="space-y-2">
              {[
                { label: 'Supplier Name', val: part.supplier },
                { label: 'Lead Time',     val: part.lead_time_days + ' days' },
              ].map(({ label, val }) => (
                <div key={label} className="flex justify-between text-xs py-1.5 border-b border-[#334155] last:border-0">
                  <span className="text-slate-400">{label}</span>
                  <span className="text-white">{val}</span>
                </div>
              ))}
            </div>
          )}
        </Card>

        {/* Reorder recommendation */}
        {reorderRec && (
          <Card className="p-4 lg:col-span-2">
            <h3 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
              <Zap className="w-4 h-4 text-red-400" /> AI Procurement Recommendation
            </h3>
            <div className="p-4 bg-red-500/5 border border-red-500/20 rounded-xl">
              <div className="flex items-start justify-between flex-wrap gap-3">
                <div>
                  <div className={`text-xs px-2 py-0.5 rounded border font-medium w-fit mb-2 ${urgencyBadge(reorderRec.urgency)}`}>
                    {reorderRec.urgency?.toUpperCase()} PRIORITY
                  </div>
                  <div className="text-white font-semibold">Order {reorderRec.recommended_quantity} units immediately</div>
                  <p className="text-xs text-slate-400 mt-1 leading-relaxed max-w-lg">{reorderRec.reason}</p>
                </div>
                <div className="text-right">
                  <div className="text-2xl font-bold text-orange-400">{reorderRec.recommended_quantity}</div>
                  <div className="text-xs text-slate-400">Recommended Qty</div>
                  <div className="text-sm font-semibold text-white mt-1">₹{reorderRec.estimated_cost?.toLocaleString('en-IN')}</div>
                  <div className="text-xs text-slate-400">Est. Cost</div>
                </div>
              </div>
              <div className="grid grid-cols-3 gap-3 mt-3">
                {[
                  { label: 'Current Stock', val: reorderRec.current_stock, color: 'text-red-400' },
                  { label: 'Minimum Stock', val: reorderRec.minimum_stock, color: 'text-yellow-400' },
                  { label: 'Lead Time',     val: reorderRec.lead_time_days + 'd', color: 'text-blue-400' },
                ].map(({ label, val, color }) => (
                  <div key={label} className="bg-[#0F1419] rounded-lg p-2 border border-[#334155] text-center">
                    <div className={`text-lg font-bold font-mono ${color}`}>{val}</div>
                    <div className="text-[10px] text-slate-500">{label}</div>
                  </div>
                ))}
              </div>
            </div>
          </Card>
        )}
      </div>
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════
   MAIN PAGE
═══════════════════════════════════════════════════════════ */
export default function ProcurementInventory() {
  const [parts,      setParts]      = useState([]);
  const [invSum,     setInvSum]     = useState(null);
  const [alerts,     setAlerts]     = useState([]);
  const [reorders,   setReorders]   = useState([]);
  const [suppliers,  setSuppliers]  = useState([]);
  const [dashboard,  setDashboard]  = useState(null);
  const [loading,    setLoading]    = useState(true);
  const [selected,   setSelected]   = useState(null);
  const [search,     setSearch]     = useState('');
  const [filterCat,  setFilterCat]  = useState('');
  const [filterStat, setFilterStat] = useState('');
  const [activeTab,  setActiveTab]  = useState(0);
  const [lastUpdate, setLastUpdate] = useState(null);

  const load = useCallback(async () => {
    const [p, inv, al, ro, sup, dash] = await Promise.all([
      get('/spares'),
      get('/inventory-summary'),
      get('/alerts'),
      get('/reorder'),
      get('/suppliers'),
      get('/dashboard'),
    ]);
    setParts(p?.parts || []);
    setInvSum(inv);
    setAlerts(al?.alerts || []);
    setReorders(ro?.recommendations || []);
    setSuppliers(sup?.suppliers || []);
    setDashboard(dash);
    setLastUpdate(new Date());
    setLoading(false);
  }, []);

  useEffect(() => { load(); }, [load]);

  // Filtered parts
  const categories = [...new Set(parts.map(p => p.category))];
  const filtered = parts.filter(p => {
    if (search && !p.part_name.toLowerCase().includes(search.toLowerCase()) && !p.part_number.toLowerCase().includes(search.toLowerCase())) return false;
    if (filterCat  && p.category !== filterCat)    return false;
    if (filterStat && p.status   !== filterStat)   return false;
    return true;
  });

  // Analytics data
  const byCat = Object.entries(
    parts.reduce((acc, p) => { acc[p.category] = (acc[p.category] || 0) + 1; return acc; }, {})
  ).map(([name, count]) => ({ name, count }));

  const byStatus = [
    { name: 'In Stock',  count: parts.filter(p => p.status === 'in_stock').length,         color: '#10B981' },
    { name: 'Low Stock', count: parts.filter(p => p.status === 'low_stock').length,         color: '#FBBF24' },
    { name: 'Reorder',   count: parts.filter(p => p.status === 'reorder_required').length,  color: '#F97316' },
    { name: 'Out',       count: parts.filter(p => p.status === 'out_of_stock').length,       color: '#EF4444' },
  ].filter(s => s.count > 0);

  const totalValue = parts.reduce((a, p) => a + (p.stock_quantity * (p.unit_cost || 0)), 0);
  const criticalCount = parts.filter(p => p.status === 'out_of_stock' || p.status === 'reorder_required').length;

  const TABS = ['Inventory', 'Low Stock Alerts', 'Procurement', 'Suppliers'];

  if (selected) {
    const rec = reorders.find(r => r.part_id === selected.part_id);
    return <div className="p-6"><PartDetail part={selected} reorderRec={rec} onBack={() => setSelected(null)} /></div>;
  }

  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-2xl font-heading font-bold text-white flex items-center gap-2">
            <Package className="w-6 h-6 text-orange-500" /> Inventory Management Center
          </h1>
          <p className="text-slate-400 text-sm mt-0.5">
            Spare parts · Procurement · Supply chain · {lastUpdate ? `Updated ${lastUpdate.toLocaleTimeString()}` : ''}
          </p>
        </div>
        <button onClick={load} className="p-2 bg-[#1E293B] border border-[#334155] hover:border-orange-500/40 text-slate-400 hover:text-white rounded-lg transition-all">
          <RefreshCw className="w-4 h-4" />
        </button>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-6 gap-3">
        {[
          { label: 'Total Parts',     val: invSum?.total_parts     ?? 0, color: 'text-white',     bg: 'bg-slate-500/10 border-slate-500/20' },
          { label: 'In Stock',        val: invSum?.in_stock        ?? 0, color: 'text-green-400', bg: 'bg-green-500/10 border-green-500/20' },
          { label: 'Low Stock',       val: invSum?.low_stock       ?? 0, color: 'text-yellow-400',bg: 'bg-yellow-500/10 border-yellow-500/20' },
          { label: 'Out of Stock',    val: invSum?.out_of_stock    ?? 0, color: 'text-red-400',   bg: 'bg-red-500/10 border-red-500/20' },
          { label: 'Reorder Needed',  val: reorders.length,              color: 'text-orange-400',bg: 'bg-orange-500/10 border-orange-500/20' },
          { label: 'Inventory Value', val: '₹'+totalValue.toLocaleString('en-IN'), color: 'text-blue-400', bg: 'bg-blue-500/10 border-blue-500/20' },
        ].map(({ label, val, color, bg }) => (
          <div key={label} className={`rounded-xl border p-3 text-center ${bg}`}>
            <div className={`text-2xl font-heading font-bold ${color}`}>{val}</div>
            <div className="text-[10px] text-slate-400 mt-1">{label}</div>
          </div>
        ))}
      </div>

      {/* Critical alert banner */}
      {criticalCount > 0 && (
        <Card className="p-4 border-red-500/20 bg-red-500/5">
          <div className="flex items-center gap-2 mb-2">
            <AlertCircle className="w-4 h-4 text-red-400" />
            <span className="text-sm font-semibold text-red-400">{criticalCount} Parts Require Immediate Procurement</span>
          </div>
          <div className="flex flex-wrap gap-2">
            {parts.filter(p => p.status === 'out_of_stock' || p.status === 'reorder_required').map(p => (
              <button key={p.part_id} onClick={() => setSelected(p)}
                className={`text-xs px-2.5 py-1 rounded-lg border transition-colors ${statusBg(p.status)} hover:opacity-80`}>
                {p.part_name} ({p.stock_quantity}/{p.minimum_stock})
              </button>
            ))}
          </div>
        </Card>
      )}

      {/* Tabs */}
      <div className="flex gap-1 bg-[#1E293B] p-1 rounded-xl border border-[#334155] w-fit flex-wrap">
        {TABS.map((t, i) => (
          <button key={t} onClick={() => setActiveTab(i)}
            className={`px-4 py-2 text-sm font-medium rounded-lg transition-all ${activeTab === i ? 'bg-orange-500 text-white' : 'text-slate-400 hover:text-white'}`}>
            {t}
            {i === 1 && alerts.length > 0 && <span className="ml-1.5 text-[10px] bg-red-500/30 text-red-400 px-1.5 rounded-full">{alerts.length}</span>}
            {i === 2 && reorders.length > 0 && <span className="ml-1.5 text-[10px] bg-orange-500/30 text-orange-400 px-1.5 rounded-full">{reorders.length}</span>}
          </button>
        ))}
      </div>

      {/* ── TAB 0: INVENTORY ──────────────────────────────── */}
      {activeTab === 0 && (
        <div className="space-y-4">
          {/* Filters */}
          <div className="flex flex-wrap gap-3">
            <div className="relative flex-1 min-w-[180px] max-w-sm">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
              <input value={search} onChange={e => setSearch(e.target.value)} placeholder="Search parts..." className="input-industrial pl-9 text-sm" />
            </div>
            <select value={filterCat} onChange={e => setFilterCat(e.target.value)} className="select-industrial text-sm w-36">
              <option value="">All Categories</option>
              {categories.map(c => <option key={c} value={c}>{c}</option>)}
            </select>
            <select value={filterStat} onChange={e => setFilterStat(e.target.value)} className="select-industrial text-sm w-40">
              <option value="">All Status</option>
              {['in_stock','low_stock','reorder_required','out_of_stock'].map(s => <option key={s} value={s}>{statusLabel(s)}</option>)}
            </select>
            {(search || filterCat || filterStat) && (
              <button onClick={() => { setSearch(''); setFilterCat(''); setFilterStat(''); }}
                className="px-3 py-2 bg-[#1E293B] border border-[#334155] hover:border-red-500/40 text-slate-400 hover:text-red-400 rounded-lg text-sm transition-colors flex items-center gap-1">
                <X className="w-3.5 h-3.5" /> Clear
              </button>
            )}
            <span className="text-xs text-slate-500 self-center ml-auto">{filtered.length} parts</span>
          </div>

          {/* Parts table */}
          <Card className="overflow-hidden">
            {loading ? (
              <div className="flex items-center justify-center py-12">
                <div className="w-8 h-8 border-2 border-orange-500 border-t-transparent rounded-full animate-spin" />
              </div>
            ) : (
              <table className="industrial-table">
                <thead>
                  <tr>
                    <th>Part</th>
                    <th>Category</th>
                    <th>Stock Level</th>
                    <th>Lead Time</th>
                    <th>Unit Cost</th>
                    <th>Location</th>
                    <th>Status</th>
                    <th className="text-right">Action</th>
                  </tr>
                </thead>
                <tbody>
                  {filtered.map(p => (
                    <tr key={p.part_id} className="cursor-pointer" onClick={() => setSelected(p)}>
                      <td>
                        <div>
                          <div className="font-medium">{p.part_name}</div>
                          <div className="text-xs text-orange-400 font-mono">{p.part_number}</div>
                        </div>
                      </td>
                      <td className="text-slate-400 text-xs">{p.category}</td>
                      <td>
                        <div className="w-32">
                          <StockBar current={p.stock_quantity} minimum={p.minimum_stock} maximum={p.minimum_stock * 3} />
                        </div>
                      </td>
                      <td className="text-slate-300 font-mono text-xs">{p.lead_time_days}d</td>
                      <td className="text-slate-300 font-mono text-xs">{p.unit_cost ? '₹'+p.unit_cost.toLocaleString('en-IN') : '—'}</td>
                      <td className="text-slate-400 text-xs">{p.location?.split(',')[0] || '—'}</td>
                      <td>
                        <span className={`text-xs px-2 py-0.5 rounded border ${statusBg(p.status)}`}>{statusLabel(p.status)}</span>
                      </td>
                      <td className="text-right" onClick={e => e.stopPropagation()}>
                        <button onClick={() => setSelected(p)} className="p-1.5 text-blue-400 hover:bg-blue-500/20 rounded transition-colors">
                          <Eye className="w-3.5 h-3.5" />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </Card>

          {/* Analytics */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <Card className="p-4">
              <h3 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
                <BarChart3 className="w-4 h-4 text-orange-400" /> Parts by Category
              </h3>
              <ResponsiveContainer width="100%" height={160}>
                <BarChart data={byCat} margin={{ left: -10 }}>
                  <XAxis dataKey="name" tick={{ fontSize: 9, fill: '#94A3B8' }} />
                  <YAxis tick={{ fontSize: 9, fill: '#64748B' }} />
                  <Tooltip contentStyle={{ background: '#1E293B', border: '1px solid #334155', fontSize: 10 }} />
                  <Bar dataKey="count" fill="#F97316" radius={[3, 3, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </Card>
            <Card className="p-4">
              <h3 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
                <Package className="w-4 h-4 text-orange-400" /> Stock Status Distribution
              </h3>
              <div className="flex items-center gap-4">
                <ResponsiveContainer width={140} height={140}>
                  <PieChart>
                    <Pie data={byStatus} cx={65} cy={65} innerRadius={35} outerRadius={60} dataKey="count" strokeWidth={0}>
                      {byStatus.map((s, i) => <Cell key={i} fill={s.color} />)}
                    </Pie>
                    <Tooltip contentStyle={{ background: '#1E293B', border: '1px solid #334155', fontSize: 11 }} />
                  </PieChart>
                </ResponsiveContainer>
                <div className="flex-1 space-y-2">
                  {byStatus.map(s => (
                    <div key={s.name} className="flex items-center gap-2 text-xs">
                      <div className="w-2.5 h-2.5 rounded-full flex-shrink-0" style={{ backgroundColor: s.color }} />
                      <span className="text-slate-300 flex-1">{s.name}</span>
                      <span className="font-mono font-bold text-white">{s.count}</span>
                    </div>
                  ))}
                </div>
              </div>
            </Card>
          </div>
        </div>
      )}

      {/* ── TAB 1: LOW STOCK ALERTS ───────────────────────── */}
      {activeTab === 1 && (
        <div className="space-y-3">
          {alerts.length === 0 ? (
            <Card className="p-10 text-center">
              <CheckCircle className="w-10 h-10 text-green-400 mx-auto mb-3" />
              <p className="text-slate-400">No stock alerts — inventory is healthy</p>
            </Card>
          ) : alerts.map((a, i) => {
            const part = parts.find(p => p.part_id === a.part_id);
            const sevColor = a.alert_type === 'out_of_stock' ? '#EF4444' : a.alert_type === 'reorder_required' ? '#F97316' : '#FBBF24';
            return (
              <Card key={i} className="p-4 border-l-4 cursor-pointer hover:border-orange-500/30 transition-all" style={{ borderLeftColor: sevColor }} onClick={() => part && setSelected(part)}>
                <div className="flex items-start justify-between gap-3">
                  <div className="flex items-center gap-3">
                    <AlertTriangle className="w-5 h-5 flex-shrink-0" style={{ color: sevColor }} />
                    <div>
                      <div className="text-white font-semibold text-sm">{a.part_name}</div>
                      <div className="text-xs text-slate-400 mt-0.5">{a.message}</div>
                    </div>
                  </div>
                  <div className="text-right flex-shrink-0">
                    <div className="text-2xl font-bold font-mono" style={{ color: sevColor }}>{a.current_stock}</div>
                    <div className="text-[10px] text-slate-500">/ {a.minimum_stock} min</div>
                    <div className="text-xs font-semibold mt-1" style={{ color: sevColor }}>
                      Order {a.recommended_order} units
                    </div>
                  </div>
                </div>
              </Card>
            );
          })}
        </div>
      )}

      {/* ── TAB 2: PROCUREMENT RECOMMENDATIONS ───────────── */}
      {activeTab === 2 && (
        <div className="space-y-3">
          {reorders.length === 0 ? (
            <Card className="p-10 text-center">
              <CheckCircle className="w-10 h-10 text-green-400 mx-auto mb-3" />
              <p className="text-slate-400">No procurement recommendations</p>
            </Card>
          ) : reorders.map((r, i) => {
            const part = parts.find(p => p.part_id === r.part_id);
            return (
              <Card key={i} className="p-4 cursor-pointer hover:border-orange-500/30 transition-all" onClick={() => part && setSelected(part)}>
                <div className="flex items-start justify-between gap-3 flex-wrap">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 flex-wrap mb-1">
                      <span className="text-white font-semibold">{r.part_name}</span>
                      <span className="font-mono text-xs text-orange-400">{r.part_number}</span>
                      <span className={`text-xs px-2 py-0.5 rounded border font-medium ${urgencyBadge(r.urgency)}`}>{r.urgency?.toUpperCase()}</span>
                    </div>
                    <p className="text-xs text-slate-400 leading-relaxed max-w-lg">{r.reason}</p>
                    <div className="flex items-center gap-4 mt-2 text-xs text-slate-500">
                      <span>Supplier: {r.supplier}</span>
                      <span>Lead: {r.lead_time_days}d</span>
                      <span>Est cost: ₹{r.estimated_cost?.toLocaleString('en-IN')}</span>
                    </div>
                  </div>
                  <div className="text-right flex-shrink-0">
                    <div className="text-2xl font-bold font-mono text-orange-400">{r.recommended_quantity}</div>
                    <div className="text-[10px] text-slate-500">units to order</div>
                    <div className="mt-2 grid grid-cols-2 gap-1 text-center">
                      <div className="bg-[#0F1419] rounded p-1 border border-[#334155]">
                        <div className="text-xs font-mono text-red-400">{r.current_stock}</div>
                        <div className="text-[9px] text-slate-600">have</div>
                      </div>
                      <div className="bg-[#0F1419] rounded p-1 border border-[#334155]">
                        <div className="text-xs font-mono text-yellow-400">{r.minimum_stock}</div>
                        <div className="text-[9px] text-slate-600">need</div>
                      </div>
                    </div>
                  </div>
                </div>
              </Card>
            );
          })}
        </div>
      )}

      {/* ── TAB 3: SUPPLIERS ─────────────────────────────── */}
      {activeTab === 3 && (
        <Card className="overflow-hidden">
          <table className="industrial-table">
            <thead>
              <tr>
                <th>Supplier</th>
                <th>Categories</th>
                <th>Reliability</th>
                <th>On-Time</th>
                <th>Quality</th>
                <th>Lead Time</th>
                <th>Preferred</th>
              </tr>
            </thead>
            <tbody>
              {suppliers.map(s => (
                <tr key={s.supplier_id}>
                  <td>
                    <div className="flex items-center gap-2">
                      {s.preferred_supplier && <Star className="w-3.5 h-3.5 text-yellow-400 fill-yellow-400 flex-shrink-0" />}
                      <div>
                        <div className="font-medium">{s.supplier_name}</div>
                        <div className="text-[10px] text-slate-400">{s.contact_person}</div>
                      </div>
                    </div>
                  </td>
                  <td>
                    <div className="flex flex-wrap gap-1">
                      {(s.categories || []).slice(0, 2).map(c => (
                        <span key={c} className="text-[10px] px-1.5 py-0.5 bg-[#0F1419] border border-[#334155] text-slate-300 rounded">{c}</span>
                      ))}
                    </div>
                  </td>
                  <td>
                    <div className="flex items-center gap-1.5">
                      <div className="w-12 bg-[#0F1419] rounded-full h-1.5">
                        <div className="h-1.5 rounded-full bg-green-500" style={{ width: `${s.reliability_score}%` }} />
                      </div>
                      <span className="text-xs font-mono text-green-400">{s.reliability_score}%</span>
                    </div>
                  </td>
                  <td><span className="font-mono text-xs text-blue-400">{s.on_time_delivery_rate}%</span></td>
                  <td><span className="font-mono text-xs text-purple-400">{s.quality_score}%</span></td>
                  <td><span className="font-mono text-xs text-slate-300">{s.lead_time_days}d</span></td>
                  <td>
                    {s.preferred_supplier
                      ? <span className="text-xs px-2 py-0.5 rounded border bg-yellow-500/10 border-yellow-500/30 text-yellow-400">Preferred</span>
                      : <span className="text-xs text-slate-500">—</span>}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      )}
    </div>
  );
}
