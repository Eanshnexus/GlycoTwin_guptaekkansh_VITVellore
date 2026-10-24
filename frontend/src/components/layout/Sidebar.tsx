import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  Users,
  Activity,
  Sparkles,
  BarChart3,
  Info,
  ShieldCheck,
  Stethoscope
} from 'lucide-react';

const navItems = [
  { name: 'Overview', to: '/', icon: LayoutDashboard },
  { name: 'Patient Digital Twin', to: '/patients', icon: Users },
  { name: 'Glucose Predictions', to: '/predictions', icon: Activity },
  { name: 'Personalisation Lab', to: '/personalisation', icon: Sparkles, badge: 'Key Result' },
  { name: 'Model Evaluation', to: '/evaluation', icon: BarChart3 },
  { name: 'About & Clinical Data', to: '/about', icon: Info },
];

export const Sidebar: React.FC = () => {
  return (
    <aside className="w-64 bg-[#0a0f1d] text-slate-300 flex flex-col justify-between shrink-0 border-r border-slate-800/80 min-h-screen">
      <div>
        {/* Brand Header */}
        <div className="h-16 flex items-center px-6 border-b border-slate-800/60 gap-3">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-teal-500 to-sky-400 flex items-center justify-center text-slate-950 font-black shadow-md shadow-teal-500/20">
            <Stethoscope className="w-5 h-5 text-slate-950" />
          </div>
          <div>
            <div className="text-base font-bold text-white tracking-tight flex items-center gap-1.5">
              GlycoTwin
              <span className="text-[10px] font-semibold uppercase px-1.5 py-0.5 rounded bg-teal-900/60 text-teal-300 border border-teal-500/30">
                v1.0
              </span>
            </div>
            <div className="text-[11px] font-medium text-slate-400">
              Glucose Intelligence
            </div>
          </div>
        </div>

        {/* Navigation Menu */}
        <nav className="p-3 space-y-1 mt-2">
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) =>
                  `flex items-center justify-between px-3.5 py-2.5 rounded-lg text-xs font-medium transition-colors ${
                    isActive
                      ? 'bg-teal-500/15 text-teal-300 font-semibold border border-teal-500/30 shadow-xs'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
                  }`
                }
              >
                <div className="flex items-center gap-3">
                  <Icon className="w-4 h-4 shrink-0" />
                  <span>{item.name}</span>
                </div>
                {item.badge && (
                  <span className="text-[9px] font-bold px-1.5 py-0.5 rounded bg-teal-950 text-teal-400 border border-teal-600/40">
                    {item.badge}
                  </span>
                )}
              </NavLink>
            );
          })}
        </nav>
      </div>

      {/* Footer Info & Regulatory Notice */}
      <div className="p-4 border-t border-slate-800/60 text-slate-400 space-y-2">
        <div className="flex items-center gap-2 text-[11px] font-medium text-slate-300">
          <ShieldCheck className="w-3.5 h-3.5 text-teal-400" />
          <span>Research Prototype</span>
        </div>
        <p className="text-[10px] text-slate-500 leading-relaxed">
          Retrospective diabetes management twin built using the HUPA-UCM Clinical Cohort (25 T1D participants).
        </p>
        <div className="text-[10px] text-slate-600 pt-1">
          Non-clinical diagnostic device.
        </div>
      </div>
    </aside>
  );
};
