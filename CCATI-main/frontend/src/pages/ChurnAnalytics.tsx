import React, { useState } from 'react';
import { BarChart3, Filter, PieChart, TrendingDown, Users, HelpCircle } from 'lucide-react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Cell,
  PieChart as RePieChart,
  Pie,
  AreaChart,
  Area,
} from 'recharts';

export const ChurnAnalytics: React.FC = () => {
  const [selectedRisk, setSelectedRisk] = useState('All');
  const [selectedContract, setSelectedContract] = useState('All');
  const [selectedSegment, setSelectedSegment] = useState('All');

  // Churn by Contract Type
  const contractChurnData = [
    { contract: 'Month-to-Month', churnRate: 42.7, customers: 2450 },
    { contract: 'One Year', churnRate: 11.2, customers: 1480 },
    { contract: 'Two Year', churnRate: 2.8, customers: 1002 },
  ];

  // Churn by Tenure Tier
  const tenureChurnData = [
    { tier: '< 6 mos', churnRate: 52.4, customers: 1210 },
    { tier: '6-12 mos', churnRate: 34.1, customers: 980 },
    { tier: '12-24 mos', churnRate: 18.5, customers: 1140 },
    { tier: '24-48 mos', churnRate: 8.2, customers: 920 },
    { tier: '48+ mos', churnRate: 2.1, customers: 682 },
  ];

  // Churn by Segment
  const segmentChurnData = [
    { name: 'High Value / High Risk', churnRate: 58.0, count: 890, color: '#ef4444' },
    { name: 'Proactive Support Needed', churnRate: 44.5, count: 1420, color: '#f97316' },
    { name: 'Onboarding Risk', churnRate: 31.2, count: 1180, color: '#f59e0b' },
    { name: 'Loyal Long-term', churnRate: 4.8, count: 1442, color: '#10b981' },
  ];

  return (
    <div className="p-8 space-y-8 max-w-7xl mx-auto">
      {/* Header & Filter Bar */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-extrabold tracking-tight text-white flex items-center space-x-2">
            <BarChart3 className="w-6 h-6 text-[#F5A623]" />
            <span>Subscriber Churn Analytics Workspace</span>
          </h1>
          <p className="text-xs text-gray-400 mt-1">Multi-dimensional churn risk drivers, contract vulnerability, and segment breakdown.</p>
        </div>

        {/* Global Filter Bar */}
        <div className="flex flex-wrap items-center gap-3 bg-[#151821] p-2 rounded-2xl border border-[#272B36] text-xs">
          <div className="flex items-center space-x-1.5 text-gray-400 px-2">
            <Filter className="w-3.5 h-3.5" />
            <span className="font-semibold">Filters:</span>
          </div>

          <select
            value={selectedRisk}
            onChange={(e) => setSelectedRisk(e.target.value)}
            className="bg-[#1A1D24] border border-[#272B36] text-gray-200 rounded-lg px-2.5 py-1 focus:outline-none focus:border-[#F5A623]"
          >
            <option value="All">All Risk Tiers</option>
            <option value="Critical">Critical Risk</option>
            <option value="High">High Risk</option>
            <option value="Medium">Medium Risk</option>
            <option value="Low">Low Risk</option>
          </select>

          <select
            value={selectedContract}
            onChange={(e) => setSelectedContract(e.target.value)}
            className="bg-[#1A1D24] border border-[#272B36] text-gray-200 rounded-lg px-2.5 py-1 focus:outline-none focus:border-[#F5A623]"
          >
            <option value="All">All Contracts</option>
            <option value="Month-to-Month">Month-to-Month</option>
            <option value="One Year">One Year</option>
            <option value="Two Year">Two Year</option>
          </select>

          <select
            value={selectedSegment}
            onChange={(e) => setSelectedSegment(e.target.value)}
            className="bg-[#1A1D24] border border-[#272B36] text-gray-200 rounded-lg px-2.5 py-1 focus:outline-none focus:border-[#F5A623]"
          >
            <option value="All">All Segments</option>
            <option value="High Value / High Risk">High Value Risk</option>
            <option value="Proactive Support">Proactive Support</option>
            <option value="Onboarding Risk">Onboarding Risk</option>
          </select>
        </div>
      </div>

      {/* Analytics Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Churn Rate by Contract Commitment */}
        <div className="dark-card p-6 space-y-4">
          <div>
            <h3 className="text-sm font-bold text-white uppercase tracking-wider">Churn Rate by Contract Commitment</h3>
            <p className="text-xs text-gray-400 mt-0.5">Vulnerability comparison across contract commitment terms.</p>
          </div>

          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={contractChurnData} margin={{ top: 10, right: 20, left: 0, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#272B36" />
                <XAxis dataKey="contract" stroke="#9ca3af" fontSize={11} />
                <YAxis stroke="#6b7280" fontSize={11} unit="%" />
                <Tooltip
                  contentStyle={{ backgroundColor: '#151821', borderColor: '#272B36', borderRadius: '8px', color: '#fff' }}
                  formatter={(val: any) => [`${val}% Churn Rate`, 'Vulnerability']}
                />
                <Bar dataKey="churnRate" fill="#F5A623" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Churn Rate by Customer Tenure */}
        <div className="dark-card p-6 space-y-4">
          <div>
            <h3 className="text-sm font-bold text-white uppercase tracking-wider">Churn Risk Trajectory by Tenure</h3>
            <p className="text-xs text-gray-400 mt-0.5">High early-life drop-off during initial 6 months.</p>
          </div>

          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={tenureChurnData} margin={{ top: 10, right: 20, left: 0, bottom: 5 }}>
                <defs>
                  <linearGradient id="tenureGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#ef4444" stopOpacity={0.4} />
                    <stop offset="95%" stopColor="#ef4444" stopOpacity={0.0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#272B36" />
                <XAxis dataKey="tier" stroke="#9ca3af" fontSize={11} />
                <YAxis stroke="#6b7280" fontSize={11} unit="%" />
                <Tooltip
                  contentStyle={{ backgroundColor: '#151821', borderColor: '#272B36', borderRadius: '8px', color: '#fff' }}
                  formatter={(val: any) => [`${val}% Churn Rate`, 'Tenure Risk']}
                />
                <Area type="monotone" dataKey="churnRate" stroke="#ef4444" strokeWidth={2.5} fillOpacity={1} fill="url(#tenureGrad)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Segment Churn Breakdown Table & Donut */}
      <div className="dark-card p-6 space-y-4">
        <h3 className="text-sm font-bold text-white uppercase tracking-wider">Segment Churn Risk Breakdown</h3>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {segmentChurnData.map((seg) => (
            <div key={seg.name} className="dark-card-secondary p-4 space-y-2 border-l-4" style={{ borderLeftColor: seg.color }}>
              <span className="text-xs font-bold text-white block">{seg.name}</span>
              <div className="flex items-baseline justify-between">
                <span className="text-xl font-extrabold text-white">{seg.churnRate}%</span>
                <span className="text-xs text-gray-400">{seg.count} subs</span>
              </div>
              <p className="text-[10px] text-gray-400">Churn Probability Index</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
