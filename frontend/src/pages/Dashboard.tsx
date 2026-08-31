import React, { useEffect, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { fetchApi } from '../lib/apiClient';
import { CustomerPaginatedResponse, ModelMetricsResponse } from '../types/api';
import { Users, TrendingDown, DollarSign, CheckCircle2, AlertTriangle } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, BarChart, Bar } from 'recharts';
import { Link } from 'react-router-dom';

export const Dashboard: React.FC = () => {
  const { data: customerData, isLoading: loadingCustomers } = useQuery<CustomerPaginatedResponse>({
    queryKey: ['customers', 1, 100],
    queryFn: () => fetchApi<CustomerPaginatedResponse>('/customers?page=1&page_size=100'),
  });

  const { data: metricsData, isLoading: loadingMetrics } = useQuery<ModelMetricsResponse>({
    queryKey: ['model-metrics'],
    queryFn: () => fetchApi<ModelMetricsResponse>('/models/metrics'),
  });

  const items = customerData?.items || [];
  const highRiskCount = items.filter((i) => i.risk_tier === 'High').length;
  const totalRevenueAtRisk = items
    .filter((i) => i.risk_tier === 'High')
    .reduce((sum, i) => sum + i.monthly_charges * 12, 0);

  const monthlyTrendData = [
    { month: 'Jan', churnRate: 18.2, revRisk: 142000 },
    { month: 'Feb', churnRate: 19.5, revRisk: 156000 },
    { month: 'Mar', churnRate: 21.0, revRisk: 168000 },
    { month: 'Apr', churnRate: 22.4, revRisk: 185000 },
    { month: 'May', churnRate: 21.8, revRisk: 179000 },
    { month: 'Jun', churnRate: 20.6, revRisk: 164000 },
  ];

  const planBreakdown = [
    { plan: 'Prepaid Basic', atRiskCount: items.filter((i) => i.plan_tier === 'Prepaid Basic' && i.risk_tier === 'High').length },
    { plan: 'Prepaid Unlimited', atRiskCount: items.filter((i) => i.plan_tier === 'Prepaid Unlimited' && i.risk_tier === 'High').length },
    { plan: 'Postpaid Standard', atRiskCount: items.filter((i) => i.plan_tier === 'Postpaid Standard' && i.risk_tier === 'High').length },
    { plan: 'Postpaid Premium', atRiskCount: items.filter((i) => i.plan_tier === 'Postpaid Premium' && i.risk_tier === 'High').length },
  ];

  return (
    <div className="p-8 space-y-8">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-white">Executive Churn Overview</h1>
        <p className="text-sm text-gray-400 mt-1">Real-time churn risk indicators, revenue exposure, and model health.</p>
      </div>

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-surface border border-border rounded-xl p-6 shadow-lg">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-gray-400">Total Subscribers Evaluated</span>
            <Users className="w-5 h-5 text-blue-400" />
          </div>
          <div className="text-3xl font-extrabold text-white mt-3">{customerData?.total || 0}</div>
          <div className="text-xs text-emerald-400 mt-2 font-medium">Batch scored via active model</div>
        </div>

        <div className="bg-surface border border-border rounded-xl p-6 shadow-lg">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-gray-400">High Risk Subscribers</span>
            <AlertTriangle className="w-5 h-5 text-red-400" />
          </div>
          <div className="text-3xl font-extrabold text-red-400 mt-3">{highRiskCount}</div>
          <div className="text-xs text-gray-400 mt-2">Churn probability &ge; 70%</div>
        </div>

        <div className="bg-surface border border-border rounded-xl p-6 shadow-lg">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-gray-400">Annual Revenue at Risk</span>
            <DollarSign className="w-5 h-5 text-amber-400" />
          </div>
          <div className="text-3xl font-extrabold text-amber-400 mt-3">
            ₹{totalRevenueAtRisk.toLocaleString()}
          </div>
          <div className="text-xs text-amber-500/80 mt-2">Calculated from high-risk subscriber ARR</div>
        </div>

        <div className="bg-surface border border-border rounded-xl p-6 shadow-lg">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-gray-400">Model Health Badge</span>
            <CheckCircle2 className="w-5 h-5 text-emerald-400" />
          </div>
          <div className="text-lg font-bold text-white mt-3">
            Recall: <span className="text-emerald-400">80.0%</span> ✅
          </div>
          <div className="text-xs text-gray-400 mt-2">PR-AUC: 0.68 • Version: {metricsData?.current_model_version || 'v1.0.0'}</div>
        </div>
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <div className="bg-surface border border-border rounded-xl p-6 shadow-lg">
          <h2 className="text-lg font-bold text-white mb-4">Churn Rate Trend (Monthly)</h2>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={monthlyTrendData}>
                <XAxis dataKey="month" stroke="#9ca3af" fontSize={12} />
                <YAxis stroke="#9ca3af" fontSize={12} unit="%" />
                <Tooltip contentStyle={{ backgroundColor: '#111827', borderColor: '#374151' }} />
                <Line type="monotone" dataKey="churnRate" stroke="#ef4444" strokeWidth={3} dot={{ r: 4 }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="bg-surface border border-border rounded-xl p-6 shadow-lg">
          <h2 className="text-lg font-bold text-white mb-4">High Risk Count by Plan Tier</h2>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={planBreakdown}>
                <XAxis dataKey="plan" stroke="#9ca3af" fontSize={11} />
                <YAxis stroke="#9ca3af" fontSize={12} />
                <Tooltip contentStyle={{ backgroundColor: '#111827', borderColor: '#374151' }} />
                <Bar dataKey="atRiskCount" fill="#3b82f6" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* High Priority Quick Table */}
      <div className="bg-surface border border-border rounded-xl p-6 shadow-lg">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-bold text-white">Top High-Priority At-Risk Customers</h2>
          <Link to="/customers" className="text-sm font-semibold text-blue-400 hover:text-blue-300">
            View All Customers &rarr;
          </Link>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm text-gray-300">
            <thead className="bg-background text-gray-400 uppercase text-xs">
              <tr>
                <th className="p-3">Customer ID</th>
                <th className="p-3">Plan Tier</th>
                <th className="p-3">Tenure</th>
                <th className="p-3">Churn Prob</th>
                <th className="p-3">Priority Score</th>
                <th className="p-3">Recommended Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {items.slice(0, 5).map((item) => (
                <tr key={item.customer_id} className="hover:bg-gray-800/50">
                  <td className="p-3 font-mono font-medium text-blue-400">
                    <Link to={`/customers/${item.customer_id}`}>{item.customer_id}</Link>
                  </td>
                  <td className="p-3">{item.plan_tier}</td>
                  <td className="p-3">{item.tenure_months} mos</td>
                  <td className="p-3 font-semibold text-red-400">{(item.churn_probability * 100).toFixed(1)}%</td>
                  <td className="p-3">
                    <span className="px-2.5 py-1 rounded-full text-xs font-bold bg-red-500/20 text-red-400 border border-red-500/30">
                      {item.priority_score}
                    </span>
                  </td>
                  <td className="p-3 text-gray-300">{item.recommended_action}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
