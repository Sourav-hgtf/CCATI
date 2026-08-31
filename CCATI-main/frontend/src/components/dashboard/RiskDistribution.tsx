import React, { useState } from 'react';
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer } from 'recharts';
import { RiskDistributionPoint } from '../../types';

interface RiskDistributionProps {
  data: RiskDistributionPoint[];
}

export const RiskDistribution: React.FC<RiskDistributionProps> = ({ data }) => {
  const [activeTab, setActiveTab] = useState<'Distribution' | 'Risk Tier' | 'Revenue at Risk'>('Distribution');

  const COLORS = {
    Low: '#10b981',
    Medium: '#f59e0b',
    High: '#f97316',
    Critical: '#ef4444',
  };

  const chartData = data.map((item) => ({
    name: `${item.tier} Risk`,
    value: activeTab === 'Revenue at Risk' ? item.revenue_at_risk : item.count,
    tier: item.tier,
    revenue: item.revenue_at_risk,
    percentage: item.percentage,
  }));

  return (
    <div className="dark-card p-6 flex flex-col justify-between h-full">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-sm font-bold text-white uppercase tracking-wider">Customer Churn Risk Distribution</h2>
          <p className="text-xs text-gray-400 mt-0.5">Distribution of predicted churn probabilities across subscribers.</p>
        </div>
        <div className="flex bg-surfaceElevated p-1 rounded-lg border border-border text-[11px] font-semibold">
          {(['Distribution', 'Risk Tier', 'Revenue at Risk'] as const).map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-2.5 py-1 rounded-md transition ${
                activeTab === tab ? 'bg-primary text-white shadow-sm' : 'text-gray-400 hover:text-gray-200'
              }`}
            >
              {tab}
            </button>
          ))}
        </div>
      </div>

      <div className="h-64 my-2">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={chartData}
              cx="50%"
              cy="50%"
              innerRadius={60}
              outerRadius={95}
              paddingAngle={4}
              dataKey="value"
            >
              {chartData.map((entry) => (
                <Cell key={entry.tier} fill={COLORS[entry.tier as keyof typeof COLORS] || '#3b82f6'} />
              ))}
            </Pie>
            <Tooltip
              contentStyle={{ backgroundColor: '#111726', borderColor: '#1f2d47', borderRadius: '8px', color: '#fff' }}
              formatter={(value: any, name: any, props: any) => {
                const payload = props.payload;
                if (activeTab === 'Revenue at Risk') {
                  return [`$${value.toLocaleString()}`, `${name}`];
                }
                return [`${value.toLocaleString()} subscribers (${payload.percentage}%)`, name];
              }}
            />
          </PieChart>
        </ResponsiveContainer>
      </div>

      <div className="grid grid-cols-4 gap-2 pt-3 border-t border-border/80 text-center">
        {data.map((item) => (
          <div key={item.tier} className="bg-surfaceElevated p-2 rounded-lg border border-border/60">
            <span className="text-[10px] uppercase font-bold text-gray-400 block">{item.tier}</span>
            <span className="text-xs font-extrabold text-white mt-0.5 block">{item.count.toLocaleString()}</span>
            <span className="text-[10px] text-gray-400">${(item.revenue_at_risk / 1000).toFixed(0)}k</span>
          </div>
        ))}
      </div>
    </div>
  );
};
