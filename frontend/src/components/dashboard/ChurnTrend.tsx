import React, { useState } from 'react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { ChurnTrendPoint } from '../../types';

interface ChurnTrendProps {
  data: ChurnTrendPoint[];
}

export const ChurnTrend: React.FC<ChurnTrendProps> = ({ data }) => {
  const [period, setPeriod] = useState<'Weekly' | 'Monthly' | 'Quarterly'>('Monthly');

  return (
    <div className="dark-card p-6 flex flex-col justify-between h-full">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-sm font-bold text-white uppercase tracking-wider">Churn Risk Trend</h2>
          <p className="text-xs text-gray-400 mt-0.5">Historical trajectory of subscriber churn probability over time.</p>
        </div>
        <div className="flex bg-surfaceElevated p-1 rounded-lg border border-border text-[11px] font-semibold">
          {(['Weekly', 'Monthly', 'Quarterly'] as const).map((p) => (
            <button
              key={p}
              onClick={() => setPeriod(p)}
              className={`px-2.5 py-1 rounded-md transition ${
                period === p ? 'bg-primary text-white shadow-sm' : 'text-gray-400 hover:text-gray-200'
              }`}
            >
              {p}
            </button>
          ))}
        </div>
      </div>

      <div className="h-64 my-2">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
            <defs>
              <linearGradient id="churnGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#f97316" stopOpacity={0.4} />
                <stop offset="95%" stopColor="#f97316" stopOpacity={0.0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#1f2d47" />
            <XAxis dataKey="time_period" stroke="#6b7280" fontSize={11} tickLine={false} />
            <YAxis stroke="#6b7280" fontSize={11} tickLine={false} unit="%" />
            <Tooltip
              contentStyle={{ backgroundColor: '#111726', borderColor: '#1f2d47', borderRadius: '8px', color: '#fff' }}
              formatter={(value: any) => [`${value}% Churn Rate`, 'Predicted Churn']}
            />
            <Area type="monotone" dataKey="churn_rate" stroke="#f97316" strokeWidth={2.5} fillOpacity={1} fill="url(#churnGradient)" />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      <div className="flex items-center justify-between text-xs text-gray-400 pt-3 border-t border-border/80">
        <span>Current Period Avg: <strong className="text-white">18.4%</strong></span>
        <span className="text-emerald-400 font-semibold">&darr; 0.7% lower than previous period</span>
      </div>
    </div>
  );
};
