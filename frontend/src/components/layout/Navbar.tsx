import React, { useState } from 'react';
import { Shield, User, ChevronDown } from 'lucide-react';

interface NavbarProps {
  currentRole: string;
  onRoleChange: (role: string) => void;
}

export const Navbar: React.FC<NavbarProps> = ({ currentRole, onRoleChange }) => {
  const [dropdownOpen, setDropdownOpen] = useState(false);

  const roles = [
    { id: 'RetentionManager', label: 'Retention Manager', email: 'manager@telecom.com' },
    { id: 'Executive', label: 'Executive / Viewer', email: 'executive@telecom.com' },
    { id: 'Analyst', label: 'Data / ML Analyst', email: 'analyst@telecom.com' },
    { id: 'Admin', label: 'System Admin', email: 'samalsouravranjan@gmail.com' },
  ];

  return (
    <header className="h-16 bg-surface border-b border-border px-6 flex items-center justify-between sticky top-0 z-40">
      <div className="flex items-center space-x-3">
        <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-blue-600 to-indigo-500 flex items-center justify-center font-bold text-white shadow-md shadow-blue-500/20">
          TC
        </div>
        <span className="font-semibold text-lg tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-gray-100 to-gray-400">
          Telecom Churn & Segmentation Engine
        </span>
      </div>

      <div className="flex items-center space-x-4">
        <div className="relative">
          <button
            onClick={() => setDropdownOpen(!dropdownOpen)}
            className="flex items-center space-x-2 bg-background border border-border px-3 py-1.5 rounded-lg text-sm font-medium hover:bg-gray-800 transition"
          >
            <Shield className="w-4 h-4 text-blue-400" />
            <span>Role: <strong className="text-blue-400">{currentRole}</strong></span>
            <ChevronDown className="w-4 h-4 text-gray-400" />
          </button>

          {dropdownOpen && (
            <div className="absolute right-0 mt-2 w-56 bg-surface border border-border rounded-xl shadow-xl py-2 z-50">
              <div className="px-3 py-1.5 text-xs font-semibold text-gray-400 uppercase tracking-wider">
                Switch Role Context (RBAC)
              </div>
              {roles.map((r) => (
                <button
                  key={r.id}
                  onClick={() => {
                    onRoleChange(r.id);
                    setDropdownOpen(false);
                  }}
                  className={`w-full text-left px-3 py-2 text-sm flex flex-col hover:bg-gray-800 transition ${
                    currentRole === r.id ? 'bg-blue-600/10 text-blue-400 border-l-2 border-blue-500' : 'text-gray-300'
                  }`}
                >
                  <span className="font-medium">{r.label}</span>
                  <span className="text-xs text-gray-500">{r.email}</span>
                </button>
              ))}
            </div>
          )}
        </div>

        <div className="w-8 h-8 rounded-full bg-gray-800 flex items-center justify-center text-gray-300 border border-border">
          <User className="w-4 h-4" />
        </div>
      </div>
    </header>
  );
};
