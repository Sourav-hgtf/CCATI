import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  Users,
  BrainCircuit,
  BarChart3,
  PieChart,
  Target,
  DollarSign,
  FileSpreadsheet,
  Database,
  Activity,
  Settings,
  ShieldCheck,
  CheckCircle2,
  Cpu,
} from 'lucide-react';

interface SidebarProps {
  isOpen: boolean;
  onCloseMobile?: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ isOpen, onCloseMobile }) => {
  const navGroups = [
    {
      group: 'COMMAND CENTER',
      items: [
        { label: 'Overview', path: '/', icon: LayoutDashboard },
        { label: 'Customers', path: '/customers', icon: Users },
      ],
    },
    {
      group: 'INTELLIGENCE',
      items: [
        { label: 'Churn Predictions', path: '/predictions', icon: BrainCircuit },
        { label: 'Explainability', path: '/explainability', icon: BarChart3 },
        { label: 'Segmentation', path: '/segmentation', icon: PieChart },
        { label: 'Retention Strategy', path: '/retention', icon: Target },
      ],
    },
    {
      group: 'BUSINESS',
      items: [
        { label: 'ROI Intelligence', path: '/roi', icon: DollarSign },
        { label: 'Reports', path: '/reports', icon: FileSpreadsheet },
      ],
    },
    {
      group: 'MODEL & DATA',
      items: [
        { label: 'Data Management', path: '/data', icon: Database },
        { label: 'Model Monitor', path: '/monitoring', icon: Activity },
      ],
    },
    {
      group: 'SYSTEM',
      items: [
        { label: 'Settings', path: '/settings', icon: Settings },
        { label: 'Admin Panel', path: '/admin', icon: ShieldCheck },
      ],
    },
  ];

  return (
    <>
      {/* Mobile Backdrop */}
      {isOpen && (
        <div
          onClick={onCloseMobile}
          className="fixed inset-0 z-40 bg-black/60 backdrop-blur-sm lg:hidden"
        />
      )}

      <aside
        className={`fixed top-0 bottom-0 left-0 z-50 w-64 bg-[#0b111e] border-r border-border flex flex-col justify-between transition-transform duration-300 ease-in-out lg:translate-x-0 ${
          isOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        <div className="flex flex-col h-full overflow-y-auto custom-scrollbar">
          {/* Logo & Header */}
          <div className="p-6 border-b border-border">
            <div className="flex items-center space-x-3">
              <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-primary to-orange-600 flex items-center justify-center shadow-lg shadow-primary/20">
                <Cpu className="w-5 h-5 text-white" />
              </div>
              <div>
                <h1 className="text-base font-bold text-white tracking-wide leading-none">
                  Telecom Retention <span className="text-primary">AI</span>
                </h1>
                <p className="text-[11px] text-gray-400 mt-1 font-medium">Customer Intelligence Platform</p>
              </div>
            </div>
          </div>

          {/* Navigation Groups */}
          <div className="p-4 space-y-6 flex-1">
            {navGroups.map((group) => (
              <div key={group.group} className="space-y-1.5">
                <div className="px-3 text-[10px] font-bold text-gray-500 tracking-wider uppercase">
                  {group.group}
                </div>
                {group.items.map((item) => {
                  const Icon = item.icon;
                  return (
                    <NavLink
                      key={item.path}
                      to={item.path}
                      onClick={onCloseMobile}
                      className={({ isActive }) =>
                        `flex items-center space-x-3 px-3 py-2 rounded-lg text-xs font-medium transition-colors ${
                          isActive
                            ? 'bg-primary/15 text-primary border-l-2 border-primary font-semibold'
                            : 'text-gray-400 hover:text-gray-200 hover:bg-surfaceElevated'
                        }`
                      }
                    >
                      <Icon className="w-4 h-4 shrink-0" />
                      <span>{item.label}</span>
                    </NavLink>
                  );
                })}
              </div>
            ))}
          </div>

          {/* System Status & User Footer */}
          <div className="p-4 border-t border-border bg-[#090d16]/80 space-y-3">
            <div className="bg-surface border border-border/80 rounded-lg p-2.5 space-y-1.5">
              <div className="flex items-center justify-between text-[11px]">
                <span className="text-gray-400">API Status</span>
                <span className="flex items-center text-emerald-400 font-medium">
                  <CheckCircle2 className="w-3 h-3 mr-1" /> Online
                </span>
              </div>
              <div className="flex items-center justify-between text-[11px]">
                <span className="text-gray-400">Model Status</span>
                <span className="flex items-center text-emerald-400 font-medium">
                  <CheckCircle2 className="w-3 h-3 mr-1" /> Active (v1.0)
                </span>
              </div>
              <div className="flex items-center justify-between text-[11px]">
                <span className="text-gray-400">Dataset</span>
                <span className="flex items-center text-emerald-400 font-medium">
                  <CheckCircle2 className="w-3 h-3 mr-1" /> Healthy (1.5k)
                </span>
              </div>
            </div>

            <div className="flex items-center space-x-3 px-2 pt-1">
              <div className="w-8 h-8 rounded-full bg-primary/20 border border-primary/40 text-primary font-bold text-xs flex items-center justify-center">
                DA
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-xs font-semibold text-white truncate">Dev Admin</p>
                <p className="text-[10px] text-gray-400 truncate">samalsouravranjan@gmail.com</p>
              </div>
            </div>
          </div>
        </div>
      </aside>
    </>
  );
};
