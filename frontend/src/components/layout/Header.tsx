import React from 'react';
import { Search, Bell, Settings, Menu, ShieldCheck } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

interface HeaderProps {
  title: string;
  subtitle: string;
  onToggleSidebar?: () => void;
}

export const Header: React.FC<HeaderProps> = ({ title, subtitle, onToggleSidebar }) => {
  const navigate = useNavigate();

  return (
    <header className="sticky top-0 z-30 bg-[#080c14]/90 backdrop-blur-md border-b border-border px-6 py-4 flex items-center justify-between">
      {/* Title & Description */}
      <div className="flex items-center space-x-4">
        <button
          onClick={onToggleSidebar}
          className="p-2 text-gray-400 hover:text-white rounded-lg lg:hidden"
        >
          <Menu className="w-5 h-5" />
        </button>
        <div>
          <h1 className="text-xl font-bold text-white tracking-tight">{title}</h1>
          <p className="text-xs text-gray-400 mt-0.5">{subtitle}</p>
        </div>
      </div>

      {/* Header Actions & Indicators */}
      <div className="flex items-center space-x-4">
        {/* Compact Status Indicators */}
        <div className="hidden md:flex items-center space-x-3 text-xs bg-surface px-3 py-1.5 rounded-full border border-border">
          <span className="flex items-center text-emerald-400 font-medium">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse mr-1.5" />
            API Online
          </span>
          <span className="text-gray-600">|</span>
          <span className="flex items-center text-emerald-400 font-medium">
            <span className="w-2 h-2 rounded-full bg-emerald-400 mr-1.5" />
            Model Online
          </span>
          <span className="text-gray-600">|</span>
          <span className="flex items-center text-emerald-400 font-medium">
            <span className="w-2 h-2 rounded-full bg-emerald-400 mr-1.5" />
            Data Healthy
          </span>
        </div>

        {/* Global Search Button */}
        <button className="flex items-center space-x-2 bg-surface hover:bg-surfaceHover text-gray-400 px-3 py-1.5 rounded-lg border border-border text-xs transition">
          <Search className="w-3.5 h-3.5" />
          <span className="hidden sm:inline">Search subscribers...</span>
        </button>

        {/* Notifications Icon */}
        <button className="relative p-2 text-gray-400 hover:text-white bg-surface hover:bg-surfaceHover rounded-lg border border-border transition">
          <Bell className="w-4 h-4" />
          <span className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-primary" />
        </button>

        {/* Settings Shortcut */}
        <button
          onClick={() => navigate('/settings')}
          className="p-2 text-gray-400 hover:text-white bg-surface hover:bg-surfaceHover rounded-lg border border-border transition"
        >
          <Settings className="w-4 h-4" />
        </button>

        {/* User Avatar */}
        <div className="flex items-center space-x-2 pl-2 border-l border-border">
          <div className="w-8 h-8 rounded-full bg-gradient-to-br from-primary to-amber-500 text-white font-bold text-xs flex items-center justify-center shadow-md">
            DA
          </div>
        </div>
      </div>
    </header>
  );
};
