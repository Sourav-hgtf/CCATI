import React, { useState } from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import {
  Cpu,
  Search,
  Bell,
  Settings,
  LayoutDashboard,
  Users,
  BarChart3,
  BrainCircuit,
  Target,
  PieChart,
  DollarSign,
  Activity,
  FileSpreadsheet,
  CheckCircle2,
  History,
  Menu,
  X,
  LogOut,
  Shield,
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

export const HeaderNav: React.FC = () => {
  const navigate = useNavigate();
  const { user, role, logout, isAuthenticated, hasRole } = useAuth();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const navItems = [
    { label: 'Overview', path: '/', icon: LayoutDashboard },
    { label: 'Customers', path: '/customers', icon: Users },
    { label: 'Churn Analytics', path: '/churn-analytics', icon: BarChart3 },
    { label: 'Predictions', path: '/predictions', icon: BrainCircuit },
    { label: 'History', path: '/history', icon: History },
    { label: 'Retention', path: '/retention', icon: Target },
    { label: 'Segments', path: '/segmentation', icon: PieChart },
    { label: 'ROI Intelligence', path: '/roi', icon: DollarSign },
    { label: 'Model Monitor', path: '/monitoring', icon: Activity },
    { label: 'Reports', path: '/reports', icon: FileSpreadsheet },
  ];

  if (hasRole(['Admin'])) {
    navItems.push({ label: 'Admin', path: '/admin', icon: Shield });
  }

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  const getInitials = (name?: string, email?: string) => {
    if (name) {
      const parts = name.split(' ');
      if (parts.length >= 2) return `${parts[0][0]}${parts[1][0]}`.toUpperCase();
      return name.substring(0, 2).toUpperCase();
    }
    if (email) return email.substring(0, 2).toUpperCase();
    return 'US';
  };

  if (!isAuthenticated) {
    return null;
  }

  return (
    <header className="sticky top-0 z-40 bg-[#0B0D12]/95 backdrop-blur-md border-b border-[#272B36] px-6 py-3.5 flex items-center justify-between">
      {/* LEFT: Logo & Platform Subtitle */}
      <div className="flex items-center space-x-3 shrink-0">
        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-[#F5A623] to-amber-600 flex items-center justify-center shadow-lg shadow-[#F5A623]/20">
          <Cpu className="w-5 h-5 text-black stroke-[2.5]" />
        </div>
        <div>
          <div className="flex items-center space-x-2">
            <h1 className="text-base font-extrabold text-white tracking-tight leading-none">
              Telecom <span className="text-[#F5A623]">Intelligence</span>
            </h1>
          </div>
          <p className="text-[11px] text-gray-400 font-medium mt-0.5">AI Customer Retention Platform</p>
        </div>
      </div>

      {/* CENTER: Compact Rounded Pill Navigation Container */}
      <nav className="hidden lg:flex items-center bg-[#151821] border border-[#272B36] p-1.5 rounded-full shadow-inner space-x-1">
        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) =>
                `flex items-center space-x-1.5 px-3.5 py-1.5 rounded-full text-xs font-semibold transition-all duration-150 ${
                  isActive
                    ? 'bg-[#F5A623] text-black shadow-md font-bold'
                    : 'text-gray-400 hover:text-white hover:bg-white/5'
                }`
              }
            >
              <Icon className="w-3.5 h-3.5 shrink-0" />
              <span>{item.label}</span>
            </NavLink>
          );
        })}
      </nav>

      {/* RIGHT: Search, Notifications, Health Indicators, Profile & Logout */}
      <div className="flex items-center space-x-3 shrink-0">
        {/* Compact System Health Indicators */}
        <div className="hidden xl:flex items-center space-x-2.5 text-[11px] bg-[#151821] px-3 py-1.5 rounded-full border border-[#272B36]">
          <span className="flex items-center text-emerald-400 font-semibold">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse mr-1.5" />
            API Online
          </span>
          <span className="text-gray-600">|</span>
          <span className="flex items-center text-emerald-400 font-semibold">
            <CheckCircle2 className="w-3 h-3 mr-1" />
            Model Active
          </span>
        </div>

        {/* Search Action */}
        <button
          onClick={() => navigate('/customers')}
          className="p-2 text-gray-400 hover:text-white bg-[#151821] hover:bg-[#1A1D24] rounded-full border border-[#272B36] transition"
          title="Search Subscribers"
        >
          <Search className="w-4 h-4" />
        </button>

        {/* Notifications Icon */}
        <button className="relative p-2 text-gray-400 hover:text-white bg-[#151821] hover:bg-[#1A1D24] rounded-full border border-[#272B36] transition">
          <Bell className="w-4 h-4" />
          <span className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-[#F5A623]" />
        </button>

        {/* Settings Button */}
        <button
          onClick={() => navigate('/settings')}
          className="p-2 text-gray-400 hover:text-white bg-[#151821] hover:bg-[#1A1D24] rounded-full border border-[#272B36] transition"
          title="Settings"
        >
          <Settings className="w-4 h-4" />
        </button>

        {/* User Profile & Role Pill */}
        <div className="flex items-center space-x-2 pl-2 border-l border-[#272B36]">
          <div className="w-8 h-8 rounded-full bg-[#F5A623] text-black font-bold text-xs flex items-center justify-center shadow-md">
            {getInitials(user?.name, user?.email)}
          </div>
          <div className="hidden sm:flex flex-col text-left">
            <span className="text-xs font-semibold text-gray-200 leading-tight">
              {user?.name || user?.email?.split('@')[0]}
            </span>
            <span className="text-[10px] font-mono text-[#F5A623] font-medium leading-tight">
              {role}
            </span>
          </div>
        </div>

        {/* Logout Action */}
        <button
          onClick={handleLogout}
          className="p-2 text-gray-400 hover:text-red-400 bg-[#151821] hover:bg-red-500/10 rounded-full border border-[#272B36] hover:border-red-500/30 transition"
          title="Sign Out"
        >
          <LogOut className="w-4 h-4" />
        </button>

        {/* Mobile Menu Button */}
        <button
          onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          className="p-2 text-gray-400 hover:text-white rounded-lg lg:hidden"
        >
          {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
        </button>
      </div>

      {/* Mobile Drawer Navigation */}
      {mobileMenuOpen && (
        <div className="absolute top-full left-0 right-0 bg-[#151821] border-b border-[#272B36] p-4 space-y-2 lg:hidden shadow-2xl">
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.path}
                to={item.path}
                onClick={() => setMobileMenuOpen(false)}
                className={({ isActive }) =>
                  `flex items-center space-x-3 px-4 py-2.5 rounded-lg text-xs font-semibold ${
                    isActive ? 'bg-[#F5A623] text-black font-bold' : 'text-gray-300 hover:bg-[#1A1D24]'
                  }`
                }
              >
                <Icon className="w-4 h-4" />
                <span>{item.label}</span>
              </NavLink>
            );
          })}
          <div className="pt-2 border-t border-[#272B36]">
            <button
              onClick={handleLogout}
              className="w-full flex items-center space-x-3 px-4 py-2.5 rounded-lg text-xs font-semibold text-red-400 hover:bg-red-500/10"
            >
              <LogOut className="w-4 h-4" />
              <span>Sign Out ({user?.email})</span>
            </button>
          </div>
        </div>
      )}
    </header>
  );
};
