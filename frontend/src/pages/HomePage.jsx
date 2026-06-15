import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Brain, Activity, AlertTriangle, Wrench, Package,
  BarChart3, Shield, FileText, Zap, ChevronRight,
  Settings, Search, Database, TrendingUp, Bell,
  CheckCircle, Factory, Cpu, BookOpen, ArrowRight
} from 'lucide-react';

const API = 'http://localhost:8000';
const get = (url) => fetch(API + url).then(r => r.json()).catch(() => null);

const MODULES = [
  { icon: BarChart3,    label: 'Dashboard',         sub: 'Plant overview & KPIs',         href: '/dashboard',       color: 'from-orange-500 to-orange-700',   glow: 'shadow-orange-500/20'  },
  { icon: Cpu,          label: 'Equipment',          sub: 'Register & manage machines',    href: '/equipment',       color: 'from-blue-500 to-blue-700',       glow: 'shadow-blue-500/20'    },
  { icon: Activity,     label: 'Sensor Monitoring',  sub: 'Live readings & trends',        href: '/sensor-data',     color: 'from-green-500 to-green-700',     glow: 'shadow-green-500/20'   },
  { icon: AlertTriangle,label: 'Alert Center',       sub: 'Real-time fault alerts',        href: '/alerts',          color: 'from-red-500 to-red-700',         glow: 'shadow-red-500/20'     },
  { icon: Brain,        label: 'AI Assistant',       sub: 'Chat · analyze · diagnose',     href: '/assistant',       color: 'from-purple-500 to-purple-700',   glow: 'shadow-purple-500/20'  },
  { icon: TrendingUp,   label: 'Failure Prediction', sub: 'ML-powered RUL & risk',         href: '/predictive',      color: 'from-cyan-500 to-cyan-700',       glow: 'shadow-cyan-500/20'    },
  { icon: Search,       label: 'Root Cause Analysis',sub: 'Evidence-based diagnosis',      href: '/root-cause',      color: 'from-yellow-500 to-yellow-600',   glow: 'shadow-yellow-500/20'  },
  { icon: Wrench,       label: 'Maintenance Logs',   sub: 'Track all maintenance work',    href: '/maintenance-logs',color: 'from-amber-500 to-amber-700',     glow: 'shadow-amber-500/20'   },
  { icon: Package,      label: 'Spare Parts',        sub: 'Inventory & reorder alerts',    href: '/spare-parts',     color: 'from-pink-500 to-pink-700',       glow: 'shadow-pink-500/20'    },
  { icon: BookOpen,     label: 'Doc Intelligence',   sub: 'Upload & query manuals',        href: '/doc-intelligence',color: 'from-indigo-500 to-indigo-700',   glow: 'shadow-indigo-500/20'  },
  { icon: Database,     label: 'Intelligence Hub',   sub: 'Central data & quality',        href: '/intelligence-hub',color: 'from-teal-500 to-teal-700',       glow: 'shadow-teal-500/20'    },
  { icon: BarChart3,    label: 'Reports & Analytics',sub: 'KPIs · trends · insights',      href: '/learning',        color: 'from-rose-500 to-rose-700',       glow: 'shadow-rose-500/20'    },
];

const FEATURES = [
  { icon: Brain,        title: 'AI-Powered Analysis',   desc: 'LLaMA 70B via Groq for intelligent maintenance reasoning and fault diagnosis',      color: 'text-purple-400' },
  { icon: Activity,     title: 'Real-Time Monitoring',  desc: '11 sensor types including temperature, vibration, bearing temp, voltage & more',    color: 'text-green-400'  },
  { icon: TrendingUp,   title: 'Predictive Maintenance',desc: 'Random Forest & XGBoost models predict failure probability and remaining useful life', color: 'text-cyan-400'  },
  { icon: Search,       title: 'Root Cause Analysis',   desc: 'Pattern matching + historical case retrieval with multi-source confidence scoring',  color: 'text-yellow-400' },
  { icon: BookOpen,     title: 'Document Intelligence', desc: 'Upload manuals/SOPs — AI extracts knowledge and enables RAG-powered Q&A',           color: 'text-blue-400'   },
  { icon: Shield,       title: 'Feedback Learning',     desc: 'Engineer feedback loop with outcome tracking and continuous model improvement',       color: 'text-emerald-400'},
];

export default function HomePage() {
  const navigate = useNavigate();
  const [stats, setStats]     = useState({ equipment:0, alerts:0, health:0, parts:0 });
  const [loading, setLoading] = useState(true);
  const [time, setTime]       = useState(new Date());

  useEffect(() => {
    const t = setInterval(() => setTime(new Date()), 1000);
    return () => clearInterval(t);
  }, []);

  useEffect(() => {
    Promise.all([
      get('/api/equipment/count/total'),
      get('/api/anomaly/health-status'),
      get('/api/procurement/spares'),
      get('/api/anomaly/alerts'),
    ]).then(([eq, health, spares, alerts]) => {
      setStats({
        equipment: eq?.count || 0,
        health:    Math.round(health?.overall_health_percentage || 0),
        parts:     spares?.parts?.length || 0,
        alerts:    (alerts?.alerts || []).filter(a => a.status === 'active').length,
      });
      setLoading(false);
    });
  }, []);

  return (
    <div className="min-h-full bg-[#0A0F1A] -m-6 overflow-x-hidden">

      {/* ── HERO ──────────────────────────────────────────── */}
      <div className="relative overflow-hidden">
        {/* Background grid */}
        <div className="absolute inset-0 opacity-[0.03]"
          style={{ backgroundImage: 'linear-gradient(#fff 1px,transparent 1px),linear-gradient(90deg,#fff 1px,transparent 1px)', backgroundSize: '40px 40px' }} />
        {/* Glow orbs */}
        <div className="absolute top-10 left-1/4 w-96 h-96 bg-orange-500/10 rounded-full blur-3xl" />
        <div className="absolute top-20 right-1/4 w-80 h-80 bg-blue-500/8 rounded-full blur-3xl" />

        <div className="relative max-w-6xl mx-auto px-6 pt-14 pb-10">
          {/* Badge */}
          <div className="flex justify-center mb-5">
            <div className="flex items-center gap-2 px-4 py-1.5 bg-orange-500/10 border border-orange-500/20 rounded-full">
              <div className="w-1.5 h-1.5 rounded-full bg-orange-400 animate-pulse" />
              <span className="text-xs text-orange-400 font-medium">AI-Powered Industrial Maintenance Platform</span>
            </div>
          </div>

          {/* Title */}
          <div className="text-center mb-5">
            <div className="flex items-center justify-center gap-3 mb-3">
              <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-orange-500 to-orange-700 flex items-center justify-center shadow-lg shadow-orange-500/30">
                <Factory className="w-6 h-6 text-white" />
              </div>
            </div>
            <h1 className="text-4xl md:text-5xl font-heading font-black text-white leading-tight">
              Maintenance <span className="text-transparent bg-clip-text bg-gradient-to-r from-orange-400 to-orange-600">Wizard</span>
            </h1>
            <p className="text-lg text-slate-400 mt-2 max-w-2xl mx-auto">
              AI-Powered Maintenance Intelligence for Steel Manufacturing Plants
            </p>
            <p className="text-sm text-slate-500 mt-1">
              Powered by LLaMA 70B · ChromaDB RAG · Random Forest · XGBoost · Isolation Forest
            </p>
          </div>

          {/* Live clock */}
          <div className="flex justify-center mb-6">
            <div className="flex items-center gap-4 px-5 py-2 bg-[#1E293B]/80 border border-[#334155] rounded-full text-sm">
              <span className="text-slate-500">Steel Plant</span>
              <span className="w-px h-4 bg-[#334155]" />
              <span className="font-mono text-orange-400">{time.toLocaleTimeString()}</span>
              <span className="w-px h-4 bg-[#334155]" />
              <span className="text-slate-500">{time.toLocaleDateString('en-IN', { weekday:'short', day:'numeric', month:'short' })}</span>
            </div>
          </div>

          {/* Live stat cards */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 max-w-3xl mx-auto mb-6">
            {[
              { label:'Equipment',      val: loading ? '—' : stats.equipment, icon: Cpu,           color:'text-blue-400',   bg:'bg-blue-500/10 border-blue-500/20'    },
              { label:'Plant Health',   val: loading ? '—' : stats.health+'%', icon: Activity,     color:'text-green-400',  bg:'bg-green-500/10 border-green-500/20'  },
              { label:'Active Alerts',  val: loading ? '—' : stats.alerts,    icon: Bell,          color:'text-red-400',    bg:'bg-red-500/10 border-red-500/20'      },
              { label:'Spare Parts',    val: loading ? '—' : stats.parts,     icon: Package,       color:'text-pink-400',   bg:'bg-pink-500/10 border-pink-500/20'    },
            ].map(({ label, val, icon:Icon, color, bg }) => (
              <div key={label} className={`rounded-xl border p-3 text-center ${bg}`}>
                <Icon className={`w-4 h-4 ${color} mx-auto mb-1`} />
                <div className={`text-2xl font-heading font-bold ${color}`}>{val}</div>
                <div className="text-[10px] text-slate-500 mt-0.5">{label}</div>
              </div>
            ))}
          </div>

          {/* CTA buttons */}
          <div className="flex items-center justify-center gap-3 flex-wrap">
            <button onClick={() => navigate('/dashboard')}
              className="flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-orange-500 to-orange-600 hover:from-orange-600 hover:to-orange-700 text-white font-semibold rounded-xl shadow-lg shadow-orange-500/30 transition-all hover:scale-[1.02]">
              <BarChart3 className="w-4 h-4" /> Open Dashboard <ArrowRight className="w-4 h-4" />
            </button>
            <button onClick={() => navigate('/assistant')}
              className="flex items-center gap-2 px-6 py-3 bg-[#1E293B] border border-purple-500/30 hover:border-purple-500/60 text-purple-400 hover:text-purple-300 font-semibold rounded-xl transition-all hover:scale-[1.02]">
              <Brain className="w-4 h-4" /> AI Assistant
            </button>
            <button onClick={() => navigate('/intelligence-hub')}
              className="flex items-center gap-2 px-6 py-3 bg-[#1E293B] border border-[#334155] hover:border-teal-500/40 text-slate-300 hover:text-white font-semibold rounded-xl transition-all hover:scale-[1.02]">
              <Database className="w-4 h-4" /> Intelligence Hub
            </button>
          </div>
        </div>
      </div>

      {/* ── MODULES GRID ──────────────────────────────────── */}
      <div className="max-w-6xl mx-auto px-6 py-8">
        <div className="text-center mb-6">
          <h2 className="text-2xl font-heading font-bold text-white">Platform Modules</h2>
          <p className="text-slate-500 text-sm mt-1">12 integrated modules covering the complete maintenance lifecycle</p>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
          {MODULES.map(({ icon:Icon, label, sub, href, color, glow }) => (
            <button key={href} onClick={() => navigate(href)}
              className={`group relative p-4 bg-[#1E293B] border border-[#334155] hover:border-transparent rounded-xl text-left transition-all duration-200 hover:scale-[1.02] hover:shadow-lg ${glow}`}>
              {/* Gradient border on hover */}
              <div className={`absolute inset-0 rounded-xl bg-gradient-to-br ${color} opacity-0 group-hover:opacity-10 transition-opacity`} />
              <div className={`w-9 h-9 rounded-lg bg-gradient-to-br ${color} flex items-center justify-center mb-3 shadow-md`}>
                <Icon className="w-4.5 h-4.5 text-white w-5 h-5" />
              </div>
              <div className="text-sm font-semibold text-white group-hover:text-white leading-tight">{label}</div>
              <div className="text-[10px] text-slate-500 mt-0.5 leading-relaxed">{sub}</div>
              <ChevronRight className="absolute top-4 right-4 w-3.5 h-3.5 text-slate-600 group-hover:text-slate-400 transition-colors" />
            </button>
          ))}
        </div>
      </div>

      {/* ── FEATURES ──────────────────────────────────────── */}
      <div className="max-w-6xl mx-auto px-6 pb-8">
        <div className="text-center mb-6">
          <h2 className="text-2xl font-heading font-bold text-white">AI Capabilities</h2>
          <p className="text-slate-500 text-sm mt-1">Built on production-grade ML models and LLM integration</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {FEATURES.map(({ icon:Icon, title, desc, color }) => (
            <div key={title} className="p-4 bg-[#1E293B] border border-[#334155] rounded-xl hover:border-[#475569] transition-all">
              <Icon className={`w-5 h-5 ${color} mb-2`} />
              <div className="text-sm font-semibold text-white mb-1">{title}</div>
              <div className="text-[11px] text-slate-400 leading-relaxed">{desc}</div>
            </div>
          ))}
        </div>
      </div>

      {/* ── TECH STACK BANNER ─────────────────────────────── */}
      <div className="border-t border-[#1E293B] bg-[#0A0F1A]">
        <div className="max-w-6xl mx-auto px-6 py-5">
          <div className="flex items-center justify-between flex-wrap gap-3">
            <div className="flex items-center gap-2">
              <Factory className="w-4 h-4 text-orange-400" />
              <span className="text-xs font-semibold text-orange-400">Maintenance Wizard</span>
              <span className="text-[10px] text-slate-600">— Steel Manufacturing Plant · AI Maintenance Platform v2.0</span>
            </div>
            <div className="flex items-center gap-2 flex-wrap">
              {['FastAPI', 'React', 'SQLite', 'ChromaDB', 'Groq LLaMA 70B', 'scikit-learn', 'XGBoost'].map(t => (
                <span key={t} className="text-[10px] px-2 py-0.5 bg-[#1E293B] border border-[#334155] rounded text-slate-400">{t}</span>
              ))}
            </div>
          </div>
        </div>
      </div>

    </div>
  );
}
