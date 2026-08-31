import React, { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Shield, Lock, Mail, AlertCircle, Sparkles, CheckCircle2 } from 'lucide-react';

const PRESET_ACCOUNTS = [
  { role: 'Admin', email: 'admin@telecom.com', password: 'AdminPassword123!', desc: 'Full System Control & Audit' },
  { role: 'RetentionManager', email: 'manager@telecom.com', password: 'ManagerPassword123!', desc: 'Campaigns & PII Unmasking' },
  { role: 'Analyst', email: 'analyst@telecom.com', password: 'AnalystPassword123!', desc: 'Data Analytics & Models' },
  { role: 'ModelManager', email: 'modelmanager@telecom.com', password: 'ModelPassword123!', desc: 'Model Promotion & Rollback' },
  { role: 'Operations', email: 'operations@telecom.com', password: 'OpsPassword123!', desc: 'Predictions & Risk Tiers' },
  { role: 'Viewer', email: 'viewer@telecom.com', password: 'ViewerPassword123!', desc: 'Read-Only Dashboards' },
];

export const Login: React.FC = () => {
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const [email, setEmail] = useState('admin@telecom.com');
  const [password, setPassword] = useState('AdminPassword123!');
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const from = (location.state as any)?.from?.pathname || '/';

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSubmitting(true);

    try {
      await login(email, password);
      navigate(from, { replace: true });
    } catch (err: any) {
      setError(err.message || 'Authentication failed. Please verify your credentials.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleSelectPreset = (presetEmail: string, presetPw: string) => {
    setEmail(presetEmail);
    setPassword(presetPw);
    setError(null);
  };

  return (
    <div className="min-h-screen bg-[#0E0E12] flex flex-col justify-center items-center p-4 selection:bg-[#F5A623] selection:text-black">
      {/* Background glow aesthetics */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-[#F5A623]/10 rounded-full blur-3xl pointer-events-none" />

      <div className="w-full max-w-md relative z-10 space-y-6">
        {/* Header Branding */}
        <div className="text-center space-y-2">
          <div className="inline-flex items-center space-x-2 px-3 py-1 bg-[#1C1C24] border border-[#2E2E38] rounded-full text-xs text-gray-300 mb-2">
            <Shield className="w-3.5 h-3.5 text-[#F5A623]" />
            <span className="font-mono font-semibold tracking-wide">ENTERPRISE RBAC ARCHITECTURE</span>
          </div>
          <h1 className="text-2xl font-black tracking-tight text-white flex items-center justify-center space-x-2">
            <span>Telecom Churn Intelligence</span>
          </h1>
          <p className="text-xs text-gray-400">
            Sign in with your enterprise credentials to access prediction workspaces.
          </p>
        </div>

        {/* Login Form Card */}
        <div className="bg-[#18181E] border border-[#2A2A36] rounded-2xl p-6 shadow-2xl space-y-6">
          {error && (
            <div className="p-3.5 bg-red-500/10 border border-red-500/30 rounded-xl flex items-start space-x-3 text-xs text-red-400">
              <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-gray-300 flex items-center justify-between">
                <span>Email or Username</span>
              </label>
              <div className="relative">
                <Mail className="w-4 h-4 absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-500" />
                <input
                  type="text"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="name@telecom.com"
                  className="w-full bg-[#101014] border border-[#2E2E38] rounded-xl pl-10 pr-4 py-2.5 text-xs text-white placeholder-gray-600 focus:outline-none focus:border-[#F5A623] transition font-sans"
                />
              </div>
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-gray-300 flex items-center justify-between">
                <span>Password</span>
              </label>
              <div className="relative">
                <Lock className="w-4 h-4 absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-500" />
                <input
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••••••"
                  className="w-full bg-[#101014] border border-[#2E2E38] rounded-xl pl-10 pr-4 py-2.5 text-xs text-white placeholder-gray-600 focus:outline-none focus:border-[#F5A623] transition font-mono"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={submitting}
              className="w-full bg-[#F5A623] hover:bg-[#E09612] text-black font-bold py-2.5 px-4 rounded-xl text-xs transition duration-150 flex items-center justify-center space-x-2 shadow-lg shadow-[#F5A623]/20 disabled:opacity-50"
            >
              {submitting ? (
                <>
                  <div className="w-3.5 h-3.5 border-2 border-black border-t-transparent rounded-full animate-spin"></div>
                  <span>Authenticating...</span>
                </>
              ) : (
                <>
                  <Lock className="w-3.5 h-3.5" />
                  <span>Sign In to Platform</span>
                </>
              )}
            </button>
          </form>

          {/* Quick Demo Credentials Selector */}
          <div className="pt-4 border-t border-[#262632] space-y-3">
            <div className="flex items-center justify-between text-[11px] text-gray-400 font-medium">
              <span className="flex items-center space-x-1">
                <Sparkles className="w-3 h-3 text-[#F5A623]" />
                <span>Pre-configured Enterprise Role Test Accounts:</span>
              </span>
            </div>

            <div className="grid grid-cols-2 gap-2">
              {PRESET_ACCOUNTS.map((preset) => (
                <button
                  key={preset.role}
                  type="button"
                  onClick={() => handleSelectPreset(preset.email, preset.password)}
                  className={`p-2 rounded-xl text-left border text-[11px] transition ${
                    email === preset.email
                      ? 'bg-[#F5A623]/15 border-[#F5A623]/50 text-white'
                      : 'bg-[#101014] border-[#2E2E38] text-gray-400 hover:border-gray-600 hover:text-gray-200'
                  }`}
                >
                  <div className="flex items-center justify-between font-semibold">
                    <span className="truncate">{preset.role}</span>
                    {email === preset.email && <CheckCircle2 className="w-3 h-3 text-[#F5A623]" />}
                  </div>
                  <div className="text-[10px] text-gray-500 truncate mt-0.5">{preset.desc}</div>
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Security Footer Note */}
        <div className="text-center text-[11px] text-gray-500 font-mono">
          <span>Protected by AES-256 JWT & bcrypt 12-round salted encryption</span>
        </div>
      </div>
    </div>
  );
};
