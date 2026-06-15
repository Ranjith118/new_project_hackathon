import { Outlet, NavLink, useLocation } from 'react-router-dom';
import {
  LayoutDashboard, Settings, Package, FileText, Upload,
  Activity, AlertTriangle, Wrench, MessageSquare, Library,
  Bot, Bell, TrendingUp, Brain, Search, Lightbulb,
  ShoppingCart, BarChart3, BookOpen, ClipboardList, Database, Cpu
} from 'lucide-react';

const NAV_GROUPS = [
  {
    label: 'Core',
    items: [
      { name: 'Dashboard',          href: '/dashboard',       icon: LayoutDashboard },
      { name: 'Intelligence Hub',   href: '/intelligence-hub',icon: Database        },
      { name: 'AI Assistant',       href: '/assistant',       icon: Bot             },
    ]
  },
  {
    label: 'Equipment & Sensors',
    items: [
      { name: 'Equipment',          href: '/equipment',       icon: Settings        },
      { name: 'Sensor Data',        href: '/sensor-data',     icon: Activity        },
      { name: 'Equipment Health',   href: '/equipment-health',icon: Cpu             },
      { name: 'Alert Center',       href: '/alerts',          icon: Bell            },
    ]
  },
  {
    label: 'Maintenance',
    items: [
      { name: 'Maintenance Logs',   href: '/maintenance-logs',icon: Wrench          },
      { name: 'Failure Reports',    href: '/failure-reports', icon: AlertTriangle   },
      { name: 'Operational Data',   href: '/operational',     icon: ClipboardList   },
      { name: 'Recommendations',    href: '/recommendations', icon: Lightbulb       },
    ]
  },
  {
    label: 'AI & Analytics',
    items: [
      { name: 'Predictive',         href: '/predictive',      icon: Brain           },
      { name: 'Root Cause',         href: '/root-cause',      icon: Search          },
      { name: 'Decision Support',   href: '/decision-support',icon: BarChart3       },
      { name: 'Reports & Analytics',href: '/learning',        icon: TrendingUp      },
    ]
  },
  {
    label: 'Documents & Inventory',
    items: [
      { name: 'Doc Intelligence',   href: '/doc-intelligence',icon: BookOpen        },
      { name: 'Document Library',   href: '/documents',       icon: Library         },
      { name: 'Spare Parts',        href: '/spare-parts',     icon: Package         },
      { name: 'Procurement',        href: '/procurement',     icon: ShoppingCart    },
    ]
  },
];

export default function Layout() {
  const location = useLocation();
  const isAssistant = location.pathname === '/assistant';
  const isFullPage  = location.pathname === '/assistant' || location.pathname === '/';

  return (
    <div className="min-h-screen flex bg-industrial-bg">
      {/* Sidebar */}
      <aside className="w-64 bg-industrial-bg-secondary border-r border-industrial-border flex flex-col flex-shrink-0">
        {/* Logo — click to go home */}
        <div className="p-5 border-b border-industrial-border cursor-pointer" onClick={() => window.location.href='/'}>
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-orange-500 to-orange-700 flex items-center justify-center shadow-md shadow-orange-500/30">
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
              <p className="text-[9px] font-semibold text-slate-600 uppercase tracking-widest px-3 mb-1">{group.label}</p>
              <ul className="space-y-0.5">
                {group.items.map(item => (
                  <li key={item.name}>
                    <NavLink
                      to={item.href}
                      end={item.href === '/'}
                      className={({ isActive }) =>
                        `flex items-center gap-2.5 px-3 py-2 rounded-lg transition-all text-sm ${
                          isActive
                            ? 'bg-orange-500/10 text-orange-400 border border-orange-500/20'
                            : 'text-slate-400 hover:text-white hover:bg-[#1E293B]'
                        }`
                      }
                    >
                      <item.icon className="w-4 h-4 flex-shrink-0" />
                      <span className="font-medium truncate">{item.name}</span>
                    </NavLink>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </nav>

        {/* Footer */}
        <div className="p-4 border-t border-industrial-border">
          <div className="text-[10px] text-slate-600 leading-relaxed">
            <p className="text-slate-500">Steel Manufacturing Plant</p>
            <p>AI Maintenance Wizard v2.0</p>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-hidden min-w-0 flex flex-col">
        <div className={isAssistant ? 'flex-1 overflow-hidden' : 'flex-1 overflow-auto p-6'}>
          <Outlet />
        </div>
      </main>
    </div>
  );
}
