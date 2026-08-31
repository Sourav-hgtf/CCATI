import React, { useState } from 'react';
import { Settings as SettingsIcon, Shield, Sliders, Bell, Cpu, Palette, CheckCircle2 } from 'lucide-react';

export const Settings: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'General' | 'Business Rules' | 'Model Config' | 'Notifications' | 'Appearance'>('General');
  const [saved, setSaved] = useState(false);

  // Business Rules state loaded dynamically
  const [rules, setRules] = useState({
    clv_tenure_multiplier: 12,
    high_risk_threshold: 0.50,
    critical_risk_threshold: 0.75,
    auto_trigger_campaigns: true,
    data_retention_months: 24,
  });

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    setSaved(true);
    setTimeout(() => setSaved(false), 3000);
  };

  return (
    <div className="p-8 space-y-8 max-w-6xl mx-auto">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-white flex items-center space-x-2">
          <SettingsIcon className="w-6 h-6 text-primary" />
          <span>System Settings & Business Rules Configuration</span>
        </h1>
        <p className="text-xs text-gray-400 mt-1">Platform parameters, risk thresholds, data retention policies, and API configuration.</p>
      </div>

      {/* Tabs Header */}
      <div className="flex border-b border-border space-x-6 text-xs font-semibold text-gray-400">
        {(['General', 'Business Rules', 'Model Config', 'Notifications', 'Appearance'] as const).map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`pb-3 transition border-b-2 ${
              activeTab === tab ? 'border-primary text-primary font-bold' : 'border-transparent hover:text-white'
            }`}
          >
            {tab}
          </button>
        ))}
      </div>

      {saved && (
        <div className="bg-emerald-950/60 border border-emerald-800/80 p-4 rounded-xl text-xs text-emerald-300 flex items-center space-x-2">
          <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
          <span>Settings saved successfully. Config changes applied.</span>
        </div>
      )}

      {/* Tab Content */}
      <form onSubmit={handleSave} className="dark-card p-6 space-y-6">
        {activeTab === 'Business Rules' && (
          <div className="space-y-4 text-xs">
            <h2 className="text-sm font-bold text-white uppercase tracking-wider">Decoupled Business Rules Configuration</h2>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="bg-surfaceElevated p-4 rounded-lg border border-border/80 space-y-1.5">
                <label className="font-semibold text-gray-300 block">High Risk Probability Threshold</label>
                <input
                  type="number"
                  step="0.05"
                  value={rules.high_risk_threshold}
                  onChange={(e) => setRules({ ...rules, high_risk_threshold: Number(e.target.value) })}
                  className="w-full bg-surface border border-border rounded px-3 py-1.5 text-white font-mono"
                />
                <span className="text-[10px] text-gray-500 block">Subscribers with churn prob &ge; threshold are fed to K-Means clustering.</span>
              </div>

              <div className="bg-surfaceElevated p-4 rounded-lg border border-border/80 space-y-1.5">
                <label className="font-semibold text-gray-300 block">Critical Risk Probability Threshold</label>
                <input
                  type="number"
                  step="0.05"
                  value={rules.critical_risk_threshold}
                  onChange={(e) => setRules({ ...rules, critical_risk_threshold: Number(e.target.value) })}
                  className="w-full bg-surface border border-border rounded px-3 py-1.5 text-white font-mono"
                />
                <span className="text-[10px] text-gray-500 block">Triggers instant call center priority outreach escalation.</span>
              </div>

              <div className="bg-surfaceElevated p-4 rounded-lg border border-border/80 space-y-1.5">
                <label className="font-semibold text-gray-300 block">CLV Expected Remaining Tenure (Months)</label>
                <input
                  type="number"
                  value={rules.clv_tenure_multiplier}
                  onChange={(e) => setRules({ ...rules, clv_tenure_multiplier: Number(e.target.value) })}
                  className="w-full bg-surface border border-border rounded px-3 py-1.5 text-white font-mono"
                />
                <span className="text-[10px] text-gray-500 block">CLV = avg monthly revenue &times; expected remaining tenure in months.</span>
              </div>

              <div className="bg-surfaceElevated p-4 rounded-lg border border-border/80 space-y-1.5">
                <label className="font-semibold text-gray-300 block">Raw Data Retention Window (Months)</label>
                <input
                  type="number"
                  value={rules.data_retention_months}
                  onChange={(e) => setRules({ ...rules, data_retention_months: Number(e.target.value) })}
                  className="w-full bg-surface border border-border rounded px-3 py-1.5 text-white font-mono"
                />
                <span className="text-[10px] text-gray-500 block">Keep raw logs 24 months, then automatically anonymize PII.</span>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'General' && (
          <div className="space-y-4 text-xs">
            <h2 className="text-sm font-bold text-white uppercase tracking-wider">General Platform Settings</h2>
            <div className="space-y-3">
              <div>
                <label className="font-semibold text-gray-300 block mb-1">Platform Name</label>
                <input type="text" defaultValue="Telecom Customer Churn Analysis Platform" className="w-full bg-surfaceElevated border border-border rounded px-3 py-2 text-white" />
              </div>
              <div>
                <label className="font-semibold text-gray-300 block mb-1">Default Currency</label>
                <input type="text" defaultValue="INR (₹) / USD ($)" className="w-full bg-surfaceElevated border border-border rounded px-3 py-2 text-white" />
              </div>
            </div>
          </div>
        )}

        {activeTab === 'Model Config' && (
          <div className="space-y-4 text-xs">
            <h2 className="text-sm font-bold text-white uppercase tracking-wider">Production Model Configuration</h2>
            <div className="bg-surfaceElevated p-4 rounded-lg border border-border space-y-2">
              <span className="text-gray-400 font-semibold block">Active Promoted Classifier</span>
              <p className="font-mono text-primary font-bold text-sm">Candidate_RandomForest (v1788203728)</p>
              <p className="text-gray-400 text-[11px]">Validation Target Recall: 1.0000 | ROC-AUC: 0.9432</p>
            </div>
          </div>
        )}

        {activeTab === 'Notifications' && (
          <div className="space-y-4 text-xs">
            <h2 className="text-sm font-bold text-white uppercase tracking-wider">Alerts & Email Notifications</h2>
            <label className="flex items-center space-x-2 cursor-pointer">
              <input type="checkbox" defaultChecked className="rounded accent-primary" />
              <span className="text-gray-300 font-medium">Send high-risk subscriber alert emails to Retention Managers</span>
            </label>
          </div>
        )}

        {activeTab === 'Appearance' && (
          <div className="space-y-4 text-xs">
            <h2 className="text-sm font-bold text-white uppercase tracking-wider">Appearance & Theme</h2>
            <p className="text-gray-400">Enterprise Dark Mode is active by default.</p>
          </div>
        )}

        <div className="pt-4 border-t border-border flex justify-end">
          <button
            type="submit"
            className="px-6 py-2.5 rounded-lg bg-primary hover:bg-primaryHover text-white text-xs font-semibold shadow-md shadow-primary/20 transition"
          >
            Save Settings
          </button>
        </div>
      </form>
    </div>
  );
};
