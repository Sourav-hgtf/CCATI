import React from 'react';
import { BarChart3, TrendingUp, TrendingDown, HelpCircle } from 'lucide-react';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid, Cell } from 'recharts';

export const Explainability: React.FC = () => {
  const globalRiskDrivers = [
    { feature: 'usage_drop_call_pct', impact: +0.42, category: 'Usage Decline' },
    { feature: 'support_calls_m1', impact: +0.38, category: 'Service Issues' },
    { feature: 'contract_type (Month-to-Month)', impact: +0.31, category: 'Contract Status' },
    { feature: 'monthly_charges (High Tier)', impact: +0.22, category: 'Pricing' },
    { feature: 'data_usage_m3 (Decline)', impact: +0.18, category: 'Usage Decline' },
    { feature: 'tenure_months (Long Tenure)', impact: -0.28, category: 'Loyalty' },
    { feature: 'payment_method (Auto-Pay)', impact: -0.21, category: 'Contract Status' },
    { feature: 'plan_tier (Family Premium)', impact: -0.15, category: 'Product Fit' },
  ];

  return (
    <div className="p-8 space-y-8 max-w-7xl mx-auto">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-white flex items-center space-x-2">
          <BarChart3 className="w-6 h-6 text-primary" />
          <span>SHAP Explainable AI Intelligence</span>
        </h1>
        <p className="text-xs text-gray-400 mt-1">Global feature importance and local SHAP attributions explaining subscriber churn predictors.</p>
      </div>

      {/* Summary Explanation Card */}
      <div className="dark-card p-6 bg-gradient-to-r from-surface to-surfaceElevated border-primary/30">
        <div className="flex items-center space-x-2 text-primary font-bold text-sm mb-2">
          <HelpCircle className="w-4 h-4" />
          <span>AI Explanation Summary</span>
        </div>
        <p className="text-xs text-gray-200 leading-relaxed">
          Across the entire subscriber population, high churn risk is primarily driven by <strong>declining call usage (-32% avg drop)</strong>, 
          <strong>frequent support contacts (6+ calls)</strong>, and <strong>month-to-month contract commitments</strong>. 
          Conversely, <strong>long customer tenure (&gt;24 months)</strong> and <strong>automatic credit card billing</strong> act as key protective factors.
        </p>
      </div>

      {/* SHAP Horizontal Bar Chart */}
      <div className="dark-card p-6 space-y-4">
        <h2 className="text-sm font-bold text-white uppercase tracking-wider">Global SHAP Feature Importance</h2>
        
        <div className="h-80">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart layout="vertical" data={globalRiskDrivers} margin={{ top: 10, right: 30, left: 140, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1f2d47" />
              <XAxis type="number" stroke="#6b7280" fontSize={11} tickFormatter={(val) => `${(val * 100).toFixed(0)}%`} />
              <YAxis type="category" dataKey="feature" stroke="#9ca3af" fontSize={11} tickLine={false} width={130} />
              <Tooltip
                contentStyle={{ backgroundColor: '#111726', borderColor: '#1f2d47', borderRadius: '8px', color: '#fff' }}
                formatter={(val: any) => [`${(Number(val) * 100).toFixed(1)}% SHAP Impact`, 'Feature Value']}
              />
              <Bar dataKey="impact" radius={[0, 4, 4, 0]}>
                {globalRiskDrivers.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.impact > 0 ? '#ef4444' : '#10b981'} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Factors Comparison Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Top Factors Increasing Churn */}
        <div className="dark-card p-6 border-red-500/30 space-y-3">
          <div className="flex items-center space-x-2 text-red-400 font-bold text-sm">
            <TrendingUp className="w-4 h-4" />
            <span>Top Factors Increasing Churn Risk</span>
          </div>

          <div className="space-y-2 text-xs">
            <div className="bg-surfaceElevated p-3 rounded-lg border border-border/80 flex justify-between">
              <span className="text-gray-300 font-medium">Call Usage Drop-off (&gt;30%)</span>
              <span className="font-bold text-red-400">+42% Risk</span>
            </div>
            <div className="bg-surfaceElevated p-3 rounded-lg border border-border/80 flex justify-between">
              <span className="text-gray-300 font-medium">Support Contacts (&gt;5 calls)</span>
              <span className="font-bold text-red-400">+38% Risk</span>
            </div>
            <div className="bg-surfaceElevated p-3 rounded-lg border border-border/80 flex justify-between">
              <span className="text-gray-300 font-medium">Month-to-Month Contract</span>
              <span className="font-bold text-red-400">+31% Risk</span>
            </div>
            <div className="bg-surfaceElevated p-3 rounded-lg border border-border/80 flex justify-between">
              <span className="text-gray-300 font-medium">High Monthly Charges (&gt;₹899)</span>
              <span className="font-bold text-red-400">+22% Risk</span>
            </div>
          </div>
        </div>

        {/* Top Factors Reducing Churn */}
        <div className="dark-card p-6 border-emerald-500/30 space-y-3">
          <div className="flex items-center space-x-2 text-emerald-400 font-bold text-sm">
            <TrendingDown className="w-4 h-4" />
            <span>Top Factors Reducing Churn Risk</span>
          </div>

          <div className="space-y-2 text-xs">
            <div className="bg-surfaceElevated p-3 rounded-lg border border-border/80 flex justify-between">
              <span className="text-gray-300 font-medium">Long Tenure (&gt;24 months)</span>
              <span className="font-bold text-emerald-400">-28% Risk</span>
            </div>
            <div className="bg-surfaceElevated p-3 rounded-lg border border-border/80 flex justify-between">
              <span className="text-gray-300 font-medium">Automatic Credit Card Billing</span>
              <span className="font-bold text-emerald-400">-21% Risk</span>
            </div>
            <div className="bg-surfaceElevated p-3 rounded-lg border border-border/80 flex justify-between">
              <span className="text-gray-300 font-medium">Family Multi-line Plan</span>
              <span className="font-bold text-emerald-400">-15% Risk</span>
            </div>
            <div className="bg-surfaceElevated p-3 rounded-lg border border-border/80 flex justify-between">
              <span className="text-gray-300 font-medium">Fiber Optic Data Add-on</span>
              <span className="font-bold text-emerald-400">-12% Risk</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
