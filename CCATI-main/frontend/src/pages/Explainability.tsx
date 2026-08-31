import React from 'react';
import { BarChart3, TrendingUp, TrendingDown, HelpCircle, Info, Scale, ShieldCheck } from 'lucide-react';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid, Cell, ReferenceLine } from 'recharts';

export const Explainability: React.FC = () => {
  const globalRiskDrivers = [
    { feature: 'Voice Usage Drop (%)', impact: +0.42, category: 'Usage & Engagement', raw: 'usage_drop_call_pct' },
    { feature: 'Customer Service Calls', impact: +0.38, category: 'Customer Support', raw: 'support_calls_m1' },
    { feature: 'Contract: Month-to-Month', impact: +0.31, category: 'Contract & Plan', raw: 'contract_type_Month-to-Month' },
    { feature: 'High Monthly Charges', impact: +0.22, category: 'Billing & Pricing', raw: 'monthly_charges' },
    { feature: 'Data Usage Drop (%)', impact: +0.18, category: 'Usage & Engagement', raw: 'usage_drop_data_pct' },
    { feature: 'Customer Tenure (>24m)', impact: -0.28, category: 'Tenure & Loyalty', raw: 'tenure_months' },
    { feature: 'Payment: Auto-Debit', impact: -0.21, category: 'Billing & Pricing', raw: 'payment_method_Auto-Debit' },
    { feature: 'Plan: Postpaid Premium', impact: -0.15, category: 'Contract & Plan', raw: 'plan_tier_Postpaid Premium' },
  ];

  return (
    <div className="p-8 space-y-8 max-w-7xl mx-auto">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-white flex items-center space-x-2">
          <BarChart3 className="w-6 h-6 text-[#F5A623]" />
          <span>SHAP Explainable AI & Decision Intelligence</span>
        </h1>
        <p className="text-xs text-gray-400 mt-1">
          Population-wide feature importance and tree-based SHAP (SHapley Additive exPlanations) attributions explaining churn risk.
        </p>
      </div>

      {/* Summary Explanation Card */}
      <div className="dark-card p-6 bg-gradient-to-r from-surface to-surfaceElevated border-[#F5A623]/30">
        <div className="flex items-center space-x-2 text-[#F5A623] font-bold text-sm mb-2">
          <HelpCircle className="w-4 h-4" />
          <span>AI Explanation Summary & Decision Transparency</span>
        </div>
        <p className="text-xs text-gray-200 leading-relaxed">
          Across the entire subscriber population, high churn risk is primarily driven by <strong>declining call usage (-32% avg drop)</strong>,{' '}
          <strong>frequent support contacts (3+ calls in recent month)</strong>, and <strong>month-to-month contract commitments</strong>.{' '}
          Conversely, <strong>long customer tenure (&gt;24 months)</strong>, <strong>multi-month contract commitments</strong>, and <strong>automatic billing</strong> act as key protective factors.
        </p>
      </div>

      {/* SHAP Horizontal Bar Chart */}
      <div className="dark-card p-6 space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <h2 className="text-sm font-bold text-white uppercase tracking-wider flex items-center space-x-2">
            <Scale className="w-4 h-4 text-[#F5A623]" />
            <span>Global SHAP Feature Importance & Directionality</span>
          </h2>
          <div className="flex items-center space-x-4 text-xs">
            <span className="flex items-center space-x-1.5">
              <span className="w-3 h-3 rounded bg-red-500"></span>
              <span className="text-gray-300">Increases Churn Risk (+)</span>
            </span>
            <span className="flex items-center space-x-1.5">
              <span className="w-3 h-3 rounded bg-emerald-500"></span>
              <span className="text-gray-300">Reduces Churn Risk (-)</span>
            </span>
          </div>
        </div>

        <div className="h-80">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart layout="vertical" data={globalRiskDrivers} margin={{ top: 10, right: 30, left: 160, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1f2d47" />
              <XAxis type="number" stroke="#6b7280" fontSize={11} tickFormatter={(val) => `${(val * 100).toFixed(0)}%`} />
              <YAxis dataKey="feature" type="category" stroke="#9ca3af" fontSize={11} tickLine={false} width={150} />
              <Tooltip
                contentStyle={{ backgroundColor: '#111726', borderColor: '#1f2d47', borderRadius: '8px', color: '#fff' }}
                formatter={(val: any) => [`${(Number(val) * 100).toFixed(1)}% SHAP Contribution`, 'Impact']}
              />
              <ReferenceLine x={0} stroke="#4b5563" />
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
            <span>Top Factors Increasing Churn Risk (Risk Escalators)</span>
          </div>

          <div className="space-y-2 text-xs">
            <div className="bg-surfaceElevated p-3 rounded-lg border border-border/80 flex justify-between">
              <span className="text-gray-300 font-medium">Voice Usage Drop-off (&gt;30%)</span>
              <span className="font-bold text-red-400">+42% Risk Impact</span>
            </div>
            <div className="bg-surfaceElevated p-3 rounded-lg border border-border/80 flex justify-between">
              <span className="text-gray-300 font-medium">Support Contacts (&gt;3 calls)</span>
              <span className="font-bold text-red-400">+38% Risk Impact</span>
            </div>
            <div className="bg-surfaceElevated p-3 rounded-lg border border-border/80 flex justify-between">
              <span className="text-gray-300 font-medium">Month-to-Month Contract</span>
              <span className="font-bold text-red-400">+31% Risk Impact</span>
            </div>
            <div className="bg-surfaceElevated p-3 rounded-lg border border-border/80 flex justify-between">
              <span className="text-gray-300 font-medium">High Monthly Charges (&gt;₹899)</span>
              <span className="font-bold text-red-400">+22% Risk Impact</span>
            </div>
          </div>
        </div>

        {/* Top Factors Reducing Churn */}
        <div className="dark-card p-6 border-emerald-500/30 space-y-3">
          <div className="flex items-center space-x-2 text-emerald-400 font-bold text-sm">
            <TrendingDown className="w-4 h-4" />
            <span>Top Factors Reducing Churn Risk (Protective Anchors)</span>
          </div>

          <div className="space-y-2 text-xs">
            <div className="bg-surfaceElevated p-3 rounded-lg border border-border/80 flex justify-between">
              <span className="text-gray-300 font-medium">Long Customer Tenure (&gt;24 months)</span>
              <span className="font-bold text-emerald-400">-28% Risk Impact</span>
            </div>
            <div className="bg-surfaceElevated p-3 rounded-lg border border-border/80 flex justify-between">
              <span className="text-gray-300 font-medium">Automatic Credit Card / UPI Billing</span>
              <span className="font-bold text-emerald-400">-21% Risk Impact</span>
            </div>
            <div className="bg-surfaceElevated p-3 rounded-lg border border-border/80 flex justify-between">
              <span className="text-gray-300 font-medium">Postpaid Premium / Family Plan</span>
              <span className="font-bold text-emerald-400">-15% Risk Impact</span>
            </div>
            <div className="bg-surfaceElevated p-3 rounded-lg border border-border/80 flex justify-between">
              <span className="text-gray-300 font-medium">One / Two Year Contract Commitment</span>
              <span className="font-bold text-emerald-400">-12% Risk Impact</span>
            </div>
          </div>
        </div>
      </div>

      {/* Decision Transparency & Methodology Card */}
      <div className="dark-card p-6 space-y-3 border-border">
        <div className="flex items-center space-x-2 text-white font-bold text-sm">
          <ShieldCheck className="w-4 h-4 text-emerald-400" />
          <span>Decision Transparency & Business Rules Integration</span>
        </div>
        <p className="text-xs text-gray-300 leading-relaxed">
          The explainability pipeline connects directly with the business decision engine. Churn probability predictions are evaluated against the authoritative 50% intervention threshold. High and Critical risk tiers trigger automated retention interventions configured in the rules matrix, ensuring complete operational traceability from raw data to business action.
        </p>
        <div className="p-3 bg-[#151821] rounded-lg border border-[#272B36] flex items-center space-x-2 text-xs text-gray-400">
          <Info className="w-4 h-4 text-gray-500 shrink-0" />
          <span><strong>Methodology Note:</strong> Feature contributions explain the model's mathematical prediction; they do not prove causation.</span>
        </div>
      </div>
    </div>
  );
};

