import { useState, useEffect } from 'react';
import { Outlet, NavLink, useLocation } from 'react-router-dom';
import {
  LayoutDashboard, Settings, Package, FileText, Upload,
  Activity, AlertTriangle, Wrench, MessageSquare, Library,
  Bot, Bell, TrendingUp, Brain, Search, Lightbulb,
  ShoppingCart, BarChart3, BookOpen, ClipboardList, Database, Cpu,
  Menu, X, ChevronRight
} from 'lucide-react';

const NAV_GROUPS = [
  {
    label: 'Core',
    items: [
      { name: 'Dashboard',          href: '/dashboard',        icon: LayoutDashboard },
      { name: 'Intelligence Hub',   href: '/intelligence-hub', icon: Database        },
      { name: 'AI Assistant',       href: '/assistant',        icon: Bot             },
    ]
  },
  {
    label: 'Equipment & Sensors',
    items: [
      { name: 'Equipment',          href: '/equipment',        icon: Settings        },
      { name: 'Sensor Data',        href: '/sensor-data',      icon: Activity        },
      { name: 'Equipment Health',   href: '/equipment-health', icon: Cpu             },
      { name: 'Alert Center',       href: '/alerts',           icon: Bell            },
    ]
  },
  {
    label: 'Maintenance',
    items: [
      { name: 'Maintenance Logs',   href: '/maintenance-logs', icon: Wrench          },
      { name: 'Failure Reports',    href: '/failure-reports',  icon: AlertTriangle   },
      { name: 'Operational Data',   href: '/operational',      icon: ClipboardList   },
      { name: 'Recommendations',    href: '/recommendations',  icon: Lightbulb       },
    ]
  },
  {
    label: 'AI & Analytics',
    items: [
      { name: 'Predictive',         href: '/predictive',       icon: Brain           },
      { name: 'Root Cause',         href: '/root-cause',       icon: Search          },
      { name: 'Decision Support',   href: '/decision-support', icon: BarChart3       },
      { name: 'Reports & Analytics',href: '/learning',         icon: TrendingUp      },
    ]
  },
  {
    label: 'Documents & Inventory',
    items: [
      { name: 'Doc Intelligence',   href: '/doc-intelligence', icon: BookOpen        },
      { name: 'Document Library',   href: '/documents',        icon: Library         },
      { name: 'Spare Parts',        href: '/spare-parts',      icon: Package         },
      { name: 'Procurement',        href: '/procurement',      icon: ShoppingCart    },
    ]
  },
];

/* ── Sidebar nav content (shared between desktop and mobile) ── */
function SidebarContent({ onNavClick }) {
  return (
    <div className="flex flex-col h-full">
      {/* Logo */}
      <div
        className="p-5 border-b border-industrial-border cursor-pointer flex-shrink-0"
        onClick={() => { window.location.href = '/'; }}
      >
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-orange-500 to-orange-700 flex items-center justify-center shadow-md shadow-orange-500/30 flex-shrink-0">
            <Wrench className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="font-heading font-bold text-base text-white leading-tight">Maintenance</h1>
            <p className="font-heading text-xs text-orange-500">Wizard · Steel Plant</p>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-3 overflow-y-auto space-y-4">
        {NAV_GROUPS.map(group => (
          <div key={group.label}>
            <p className="text-[9px] font-semibold text-slate-600 uppercase tracking-widest px-3 mb-1">
              {group.label}
            </p>
            <ul className="space-y-0.5">
              {group.items.map(item => (
                <li key={item.name}>
                  <NavLink
                    to={item.href}
                    end={item.href === '/'}
                    onClick={onNavClick}
                    className={({ isActive }) =>
                      `flex items-center gap-2.5 px-3 py-2.5 rounded-lg transition-all text-sm ${
                        isActive
                          ? 'bg-orange-500/10 text-orange-400 border border-orange-500/20'
                          : 'text-slate-400 hover:text-white hover:bg-[#1E293B]'
                      }`
                    }
                  >
                    <item.icon className="w-4 h-4 flex-shrink-0" />
                    <span className="font-medium">{item.name}</span>
                  </NavLink>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </nav>

      {/* Footer */}
      <div className="p-4 border-t border-industrial-border flex-shrink-0">
        <div className="text-[10px] text-slate-600 leading-relaxed">
          <p className="text-slate-500">Steel Manufacturing Plant</p>
          <p>AI Maintenance Wizard v2.0</p>
        </div>
      </div>
    </div>
  );
}

export default function Layout() {
  const location = useLocation();
  const [mobileOpen, setMobileOpen] = useState(false);

  // Close mobile menu on route change
  useEffect(() => {
    setMobileOpen(false);
  }, [location.pathname]);

  // Prevent body scroll when mobile menu is open
  useEffect(() => {
    if (mobileOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }
    return () => { document.body.style.overflow = ''; };
  }, [mobileOpen]);

  const isAssistant = location.pathname === '/assistant';

  // Get current page name for mobile header
  const currentPage = NAV_GROUPS
    .flatMap(g => g.items)
    .find(i => i.href === location.pathname)?.name || 'Maintenance Wizard';

  return (
    <div className={`flex bg-industrial-bg ${isAssistant ? 'h-screen overflow-hidden' : 'min-h-screen'}`}>

      {/* ── DESKTOP SIDEBAR (hidden on mobile) ── */}
      <aside className="hidden lg:flex w-64 bg-industrial-bg-secondary border-r border-industrial-border flex-col flex-shrink-0">
        <SidebarContent onNavClick={() => {}} />
      </aside>

      {/* ── MOBILE OVERLAY ── */}
      {mobileOpen && (
        <div
          className="fixed inset-0 bg-black/60 z-40 lg:hidden"
          onClick={() => setMobileOpen(false)}
        />
      )}

      {/* ── MOBILE DRAWER (slides in from left) ── */}
      <aside
        className={`
          fixed top-0 left-0 h-full w-72 max-w-[85vw] z-50
          bg-[#0F1419] border-r border-industrial-border
          transform transition-transform duration-300 ease-in-out
          lg:hidden
          ${mobileOpen ? 'translate-x-0' : '-translate-x-full'}
        `}
      >
        {/* Close button inside drawer */}
        <button
          onClick={() => setMobileOpen(false)}
          className="absolute top-4 right-4 w-8 h-8 flex items-center justify-center rounded-lg bg-[#1E293B] text-slate-400 hover:text-white transition-colors z-10"
        >
          <X className="w-4 h-4" />
        </button>
        <SidebarContent onNavClick={() => setMobileOpen(false)} />
      </aside>

      {/* ── MAIN CONTENT AREA ── */}
      <div className={`flex flex-col min-w-0 overflow-hidden ${isAssistant ? 'flex-1 h-full' : 'flex-1'}`}>

        {/* ── MOBILE TOP BAR ── */}
        <header className="lg:hidden flex items-center justify-between px-4 py-3 bg-[#0F1419] border-b border-industrial-border flex-shrink-0 sticky top-0 z-30">
          <button
            onClick={() => setMobileOpen(true)}
            className="flex items-center justify-center w-9 h-9 rounded-lg bg-[#1E293B] border border-[#334155] text-slate-400 hover:text-white transition-colors"
            aria-label="Open menu"
          >
            <Menu className="w-5 h-5" />
          </button>

          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded bg-gradient-to-br from-orange-500 to-orange-700 flex items-center justify-center">
              <Wrench className="w-3.5 h-3.5 text-white" />
            </div>
            <span className="text-white text-sm font-semibold truncate max-w-[160px]">
              {currentPage}
            </span>
          </div>

          {/* Right side — home button */}
          <button
            onClick={() => window.location.href = '/'}
            className="flex items-center justify-center w-9 h-9 rounded-lg bg-[#1E293B] border border-[#334155] text-orange-400 hover:text-orange-300 transition-colors"
            aria-label="Home"
          >
            <span className="text-xs font-bold">MW</span>
          </button>
        </header>

        {/* ── PAGE CONTENT ── */}
        <main className={`flex-1 min-w-0 ${isAssistant ? 'overflow-hidden flex flex-col h-full' : 'overflow-auto'}`}>
          <div className={isAssistant ? 'flex-1 flex flex-col overflow-hidden h-full' : 'p-4 lg:p-6'}>
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
}
