import { useNavigate } from 'react-router-dom';
import {
  Brain, Activity, AlertTriangle, Wrench, Package,
  BarChart3, Shield, Zap, ChevronRight, Factory,
  Cpu, BookOpen, ArrowRight, CheckCircle, Search,
  TrendingUp, Database, Bell, Settings
} from 'lucide-react';

const FEATURES = [
  {
    icon: Brain,
    title: 'AI Maintenance Assistant',
    desc: 'Chat with LLaMA 70B to diagnose failures, get repair procedures, analyze equipment images, and manage data through natural conversation.',
    color: 'from-purple-500 to-purple-700',
    glow: 'shadow-purple-500/20',
    tag: 'LLaMA 70B · Groq'
  },
  {
    icon: TrendingUp,
    title: 'Failure Prediction',
    desc: 'Random Forest & XGBoost models predict equipment failure probability and Remaining Useful Life (RUL) from real-time sensor data.',
    color: 'from-cyan-500 to-cyan-700',
    glow: 'shadow-cyan-500/20',
    tag: 'ML · XGBoost · RUL'
  },
  {
    icon: Activity,
    title: 'Real-Time Sensor Monitoring',
    desc: '11 sensor types — temperature, vibration, current, pressure, RPM, voltage, bearing temp and more. Live health scoring and anomaly detection.',
    color: 'from-green-500 to-green-700',
    glow: 'shadow-green-500/20',
    tag: 'Isolation Forest'
  },
  {
    icon: Search,
    title: 'Root Cause Analysis',
    desc: 'Pattern matching + historical case retrieval with multi-source confidence scoring. Evidence-based diagnosis with full reasoning path.',
    color: 'from-yellow-500 to-yellow-600',
    glow: 'shadow-yellow-500/20',
    tag: 'RAG · Confidence Engine'
  },
  {
    icon: BookOpen,
    title: 'Document Intelligence',
    desc: 'Upload equipment manuals, SOPs, and reports. AI extracts knowledge, chunks and indexes into ChromaDB for instant Q&A retrieval.',
    color: 'from-indigo-500 to-indigo-700',
    glow: 'shadow-indigo-500/20',
    tag: 'ChromaDB · RAG Pipeline'
  },
  {
    icon: Bell,
    title: 'Real-Time Alert Center',
    desc: 'Threshold, anomaly, and health-score alerts with 4 severity levels. Acknowledge, resolve, and track alert history across the plant.',
    color: 'from-red-500 to-red-700',
    glow: 'shadow-red-500/20',
    tag: 'Auto-Detection · Dedup'
  },
];

const MODULES = [
  { icon: BarChart3,    label: 'Dashboard',          href: '/dashboard'        },
  { icon: Cpu,          label: 'Equipment',           href: '/equipment'        },
  { icon: Activity,     label: 'Sensor Data',         href: '/sensor-data'      },
  { icon: Brain,        label: 'AI Assistant',        href: '/assistant'        },
  { icon: TrendingUp,   label: 'Predictive',          href: '/predictive'       },
  { icon: Search,       label: 'Root Cause',          href: '/root-cause'       },
  { icon: Wrench,       label: 'Maintenance',         href: '/maintenance-logs' },
  { icon: Bell,         label: 'Alerts',              href: '/alerts'           },
  { icon: Package,      label: 'Spare Parts',         href: '/spare-parts'      },
  { icon: BookOpen,     label: 'Doc Intelligence',    href: '/doc-intelligence' },
  { icon: Database,     label: 'Intelligence Hub',    href: '/intelligence-hub' },
  { icon: Shield,       label: 'Decision Support',    href: '/decision-support' },
];

const STATS = [
  { val: '12',    label: 'Integrated Modules'    },
  { val: '11',    label: 'Sensor Types'          },
  { val: '3',     label: 'ML Models'             },
  { val: '100%',  label: 'AI-Powered'            },
];

export default function LandingPage() {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-[#060B14] text-white overflow-x-hidden">

      {/* ── NAV ─────────────────────────────────────────── */}
      <nav className="fixed top-0 left-0 right-0 z-50 flex items-center justify-between px-8 py-4 bg-[#060B14]/80 backdrop-blur-md border-b border-white/5">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-orange-500 to-orange-700 flex items-center justify-center shadow-lg shadow-orange-500/30">
            <Factory className="w-4 h-4 text-white" />
          </div>
          <div>
            <span className="font-heading font-black text-white text-base">Maintenance Wizard</span>
            <span className="text-orange-500 text-xs ml-1.5">by Steel Plant AI</span>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <button onClick={() => navigate('/dashboard')}
            className="text-sm text-slate-400 hover:text-white transition-colors px-4 py-2">
            Dashboard
          </button>
          <button onClick={() => navigate('/assistant')}
            className="text-sm text-slate-400 hover:text-white transition-colors px-4 py-2">
            AI Assistant
          </button>
          <button onClick={() => navigate('/dashboard')}
            className="flex items-center gap-2 px-5 py-2 bg-orange-500 hover:bg-orange-600 text-white text-sm font-semibold rounded-lg shadow-lg shadow-orange-500/30 transition-all hover:scale-[1.02]">
            Enter App <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </nav>

      {/* ── HERO ────────────────────────────────────────── */}
      <section className="relative min-h-screen flex items-center justify-center overflow-hidden pt-20">
        {/* Background */}
        <div className="absolute inset-0">
          <div className="absolute inset-0 bg-gradient-to-b from-[#060B14] via-[#0A0F1E] to-[#060B14]" />
          {/* Grid */}
          <div className="absolute inset-0 opacity-[0.04]"
            style={{ backgroundImage:'linear-gradient(#fff 1px,transparent 1px),linear-gradient(90deg,#fff 1px,transparent 1px)', backgroundSize:'50px 50px' }} />
          {/* Glow orbs */}
          <div className="absolute top-1/4 left-1/3 w-[600px] h-[600px] bg-orange-500/8 rounded-full blur-[120px]" />
          <div className="absolute bottom-1/4 right-1/4 w-[400px] h-[400px] bg-blue-500/6 rounded-full blur-[100px]" />
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] bg-purple-500/4 rounded-full blur-[150px]" />
        </div>

        <div className="relative z-10 max-w-5xl mx-auto px-8 text-center">
          {/* Badge */}
          <div className="inline-flex items-center gap-2 px-4 py-1.5 bg-orange-500/10 border border-orange-500/20 rounded-full mb-8">
            <div className="w-2 h-2 rounded-full bg-orange-400 animate-pulse" />
            <span className="text-xs text-orange-400 font-medium tracking-wide">AI-Powered Industrial Maintenance Platform</span>
          </div>

          {/* Main heading */}
          <h1 className="text-5xl md:text-7xl font-heading font-black leading-tight mb-6">
            <span className="text-white">Smart Maintenance</span><br />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-orange-400 via-orange-500 to-orange-600">
              for Steel Plants
            </span>
          </h1>

          <p className="text-lg md:text-xl text-slate-400 max-w-2xl mx-auto mb-4 leading-relaxed">
            An AI-powered platform that predicts failures, diagnoses faults, analyzes equipment, and guides maintenance decisions — all through intelligent conversation.
          </p>
          <p className="text-sm text-slate-600 mb-10">
            Powered by LLaMA 70B · ChromaDB · Random Forest · XGBoost · Isolation Forest · FastAPI · React
          </p>

          {/* CTA buttons */}
          <div className="flex items-center justify-center gap-4 mb-16 flex-wrap">
            <button onClick={() => navigate('/dashboard')}
              className="flex items-center gap-2.5 px-8 py-4 bg-gradient-to-r from-orange-500 to-orange-600 hover:from-orange-600 hover:to-orange-700 text-white font-bold text-base rounded-xl shadow-2xl shadow-orange-500/30 transition-all hover:scale-[1.02] hover:shadow-orange-500/40">
              <BarChart3 className="w-5 h-5" />
              Open Dashboard
              <ArrowRight className="w-5 h-5" />
            </button>
            <button onClick={() => navigate('/assistant')}
              className="flex items-center gap-2.5 px-8 py-4 bg-white/5 border border-white/10 hover:border-purple-500/40 hover:bg-purple-500/5 text-white font-semibold text-base rounded-xl transition-all hover:scale-[1.02]">
              <Brain className="w-5 h-5 text-purple-400" />
              AI Assistant
            </button>
          </div>

          {/* Stats row */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 max-w-2xl mx-auto">
            {STATS.map(({ val, label }) => (
              <div key={label} className="p-4 bg-white/3 border border-white/8 rounded-2xl backdrop-blur-sm">
                <div className="text-3xl font-heading font-black text-orange-400">{val}</div>
                <div className="text-xs text-slate-500 mt-1">{label}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── FEATURES ────────────────────────────────────── */}
      <section className="py-24 px-8 max-w-6xl mx-auto">
        <div className="text-center mb-16">
          <div className="inline-flex items-center gap-2 px-3 py-1 bg-blue-500/10 border border-blue-500/20 rounded-full mb-4">
            <Zap className="w-3.5 h-3.5 text-blue-400" />
            <span className="text-xs text-blue-400 font-medium">Core Capabilities</span>
          </div>
          <h2 className="text-3xl md:text-4xl font-heading font-black text-white mb-4">
            Everything You Need for<br />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-cyan-400">Intelligent Maintenance</span>
          </h2>
          <p className="text-slate-400 max-w-xl mx-auto">
            12 integrated modules covering the complete maintenance lifecycle from sensor monitoring to AI-powered decision support.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {FEATURES.map(({ icon:Icon, title, desc, color, glow, tag }) => (
            <div key={title}
              className={`group relative p-6 bg-[#0D1421] border border-white/5 rounded-2xl hover:border-white/15 transition-all duration-300 hover:shadow-xl ${glow} cursor-default`}>
              {/* Gradient top bar */}
              <div className={`absolute top-0 left-0 right-0 h-px bg-gradient-to-r ${color} opacity-0 group-hover:opacity-100 transition-opacity rounded-t-2xl`} />
              <div className={`w-11 h-11 rounded-xl bg-gradient-to-br ${color} flex items-center justify-center mb-4 shadow-lg`}>
                <Icon className="w-5 h-5 text-white" />
              </div>
              <div className="flex items-start justify-between mb-2">
                <h3 className="text-base font-semibold text-white">{title}</h3>
              </div>
              <p className="text-sm text-slate-400 leading-relaxed mb-3">{desc}</p>
              <span className="text-[10px] px-2 py-0.5 bg-white/5 border border-white/10 rounded-full text-slate-500">{tag}</span>
            </div>
          ))}
        </div>
      </section>

      {/* ── MODULE GRID ─────────────────────────────────── */}
      <section className="py-16 px-8 bg-[#0A0F1A]">
        <div className="max-w-5xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-2xl md:text-3xl font-heading font-black text-white mb-2">
              All Modules — One Platform
            </h2>
            <p className="text-slate-500 text-sm">Click any module to jump directly into the app</p>
          </div>
          <div className="grid grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-3">
            {MODULES.map(({ icon:Icon, label, href }) => (
              <button key={href} onClick={() => navigate(href)}
                className="group flex flex-col items-center gap-2 p-4 bg-[#0D1421] border border-white/5 hover:border-orange-500/30 hover:bg-orange-500/5 rounded-xl transition-all hover:scale-[1.04]">
                <Icon className="w-5 h-5 text-slate-400 group-hover:text-orange-400 transition-colors" />
                <span className="text-[11px] text-slate-500 group-hover:text-slate-300 font-medium text-center transition-colors">{label}</span>
              </button>
            ))}
          </div>
        </div>
      </section>

      {/* ── HOW IT WORKS ────────────────────────────────── */}
      <section className="py-24 px-8 max-w-5xl mx-auto">
        <div className="text-center mb-14">
          <h2 className="text-2xl md:text-3xl font-heading font-black text-white mb-2">How It Works</h2>
          <p className="text-slate-500 text-sm">From sensor data to actionable maintenance decisions</p>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 relative">
          {/* Connector line */}
          <div className="hidden md:block absolute top-10 left-[12%] right-[12%] h-px bg-gradient-to-r from-transparent via-orange-500/30 to-transparent" />
          {[
            { step:'01', icon:Activity,   title:'Collect Data',    desc:'Sensor readings, maintenance logs, failure reports, manuals uploaded' },
            { step:'02', icon:Brain,      title:'AI Analyzes',     desc:'LLM + ML models process data, detect anomalies, predict failures'     },
            { step:'03', icon:AlertTriangle,title:'Alerts & RCA', desc:'Auto-alerts generated, root cause identified with confidence scores'   },
            { step:'04', icon:CheckCircle,title:'Take Action',     desc:'Guided maintenance procedures, spare parts ordered, decisions logged'  },
          ].map(({ step, icon:Icon, title, desc }) => (
            <div key={step} className="relative flex flex-col items-center text-center p-5 bg-[#0D1421] border border-white/5 rounded-2xl">
              <div className="w-12 h-12 rounded-full bg-orange-500/10 border border-orange-500/20 flex items-center justify-center mb-3">
                <Icon className="w-5 h-5 text-orange-400" />
              </div>
              <div className="text-[10px] text-orange-500 font-bold mb-1 tracking-widest">STEP {step}</div>
              <div className="text-sm font-semibold text-white mb-1">{title}</div>
              <div className="text-[11px] text-slate-500 leading-relaxed">{desc}</div>
            </div>
          ))}
        </div>
      </section>

      {/* ── FINAL CTA ───────────────────────────────────── */}
      <section className="py-20 px-8 relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-r from-orange-500/5 via-orange-500/10 to-orange-500/5" />
        <div className="absolute inset-0 border-y border-orange-500/10" />
        <div className="relative max-w-3xl mx-auto text-center">
          <Factory className="w-10 h-10 text-orange-400 mx-auto mb-4" />
          <h2 className="text-3xl font-heading font-black text-white mb-4">
            Ready to Transform Your<br />Maintenance Operations?
          </h2>
          <p className="text-slate-400 mb-8">
            Enter the platform and start with the AI Assistant — add your equipment, enter sensor readings, upload manuals, and let AI guide every maintenance decision.
          </p>
          <div className="flex items-center justify-center gap-4 flex-wrap">
            <button onClick={() => navigate('/dashboard')}
              className="flex items-center gap-2 px-8 py-4 bg-orange-500 hover:bg-orange-600 text-white font-bold rounded-xl shadow-xl shadow-orange-500/30 transition-all hover:scale-[1.02]">
              <BarChart3 className="w-5 h-5" /> Open Dashboard <ArrowRight className="w-5 h-5" />
            </button>
            <button onClick={() => navigate('/assistant')}
              className="flex items-center gap-2 px-8 py-4 bg-white/5 border border-white/10 hover:border-white/20 text-white font-semibold rounded-xl transition-all hover:scale-[1.02]">
              <Brain className="w-5 h-5 text-purple-400" /> Try AI Assistant
            </button>
          </div>
        </div>
      </section>

      {/* ── FOOTER ──────────────────────────────────────── */}
      <footer className="py-8 px-8 border-t border-white/5 bg-[#060B14]">
        <div className="max-w-5xl mx-auto flex items-center justify-between flex-wrap gap-4">
          <div className="flex items-center gap-2">
            <Factory className="w-4 h-4 text-orange-400" />
            <span className="text-sm font-semibold text-white">Maintenance Wizard</span>
            <span className="text-xs text-slate-600">· Steel Manufacturing Plant · v2.0</span>
          </div>
          <div className="flex items-center gap-2 flex-wrap">
            {['FastAPI','React','SQLite','ChromaDB','Groq LLaMA 70B','scikit-learn','XGBoost'].map(t => (
              <span key={t} className="text-[10px] px-2 py-0.5 bg-white/4 border border-white/8 rounded text-slate-500">{t}</span>
            ))}
          </div>
        </div>
      </footer>

    </div>
  );
}
