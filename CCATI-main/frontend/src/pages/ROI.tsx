import React, { useState } from 'react';
import { DollarSign, Award, ShieldCheck, Sliders, TrendingUp } from 'lucide-react';
import { calculateROISimulation } from '../mocks/roi';
import { MetricCard } from '../components/common/MetricCard';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid, Cell } from 'recharts';

export const ROI: React.FC = () => {
  const [inputs, setInputs] = useState({
    target_customers: 2000,
    offer_cost_per_customer: 75,
    campaign_cost: 50000,
    expected_success_rate: 0.35,
    avg_customer_clv: 1200,
  });

  const results = calculateROISimulation(inputs);

  const waterfallData = [
    { stage: 'Campaign Cost', amount: -inputs.campaign_cost },
    { stage: 'Retention Offers', amount: -(inputs.target_customers * inputs.offer_cost_per_customer) },
    { stage: 'Gross Revenue Saved', amount: results.expected_revenue_saved },
    { stage: 'Net Retained Value', amount: results.net_benefit },
  ];

  return (
    <div className="p-8 space-y-8 max-w-7xl mx-auto">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-white flex items-center space-x-2">
          <DollarSign className="w-6 h-6 text-emerald-400" />
          <span>Executive ROI Intelligence & What-If Simulator</span>
        </h1>
        <p className="text-xs text-gray-400 mt-1">Financial impact modeling for customer retention campaigns and net CLV saved returns.</p>
      </div>

      {/* Top ROI Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          label="Retention Investment"
          value={`$${results.total_investment.toLocaleString()}`}
          description="Campaign + Offer Outlay"
          icon={DollarSign}
          variant="warning"
        />
        <MetricCard
          label="Expected Revenue Saved"
          value={`$${results.expected_revenue_saved.toLocaleString()}`}
          change={+14.2}
          changeLabel="vs unmitigated churn"
          icon={ShieldCheck}
          variant="success"
        />
        <MetricCard
          label="Expected Customers Saved"
          value={results.expected_saves.toLocaleString()}
          description={`${(inputs.expected_success_rate * 100).toFixed(0)}% save rate`}
          icon={Award}
          variant="secondary"
        />
        <MetricCard
          label="Projected ROI"
          value={`${results.roi_pct}%`}
          change={+4.8}
          changeLabel="Net Efficiency Ratio"
          icon={TrendingUp}
          variant="primary"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Interactive "What-if Simulator" Slider Form */}
        <div className="dark-card p-6 space-y-5 border-primary/30">
          <div className="flex items-center space-x-2 text-primary font-bold text-sm">
            <Sliders className="w-4 h-4" />
            <span>Interactive What-if Simulator</span>
          </div>

          <div className="space-y-4 text-xs">
            <div>
              <div className="flex justify-between text-gray-300 font-semibold mb-1">
                <span>Targeted Customers</span>
                <span className="text-primary font-bold">{inputs.target_customers.toLocaleString()}</span>
              </div>
              <input
                type="range"
                min="500"
                max="5000"
                step="100"
                value={inputs.target_customers}
                onChange={(e) => setInputs({ ...inputs, target_customers: Number(e.target.value) })}
                className="w-full accent-primary"
              />
            </div>

            <div>
              <div className="flex justify-between text-gray-300 font-semibold mb-1">
                <span>Offer Cost / Customer</span>
                <span className="text-primary font-bold">${inputs.offer_cost_per_customer}</span>
              </div>
              <input
                type="range"
                min="20"
                max="200"
                step="5"
                value={inputs.offer_cost_per_customer}
                onChange={(e) => setInputs({ ...inputs, offer_cost_per_customer: Number(e.target.value) })}
                className="w-full accent-primary"
              />
            </div>

            <div>
              <div className="flex justify-between text-gray-300 font-semibold mb-1">
                <span>Fixed Campaign Overhead</span>
                <span className="text-primary font-bold">${inputs.campaign_cost.toLocaleString()}</span>
              </div>
              <input
                type="range"
                min="10000"
                max="150000"
                step="5000"
                value={inputs.campaign_cost}
                onChange={(e) => setInputs({ ...inputs, campaign_cost: Number(e.target.value) })}
                className="w-full accent-primary"
              />
            </div>

            <div>
              <div className="flex justify-between text-gray-300 font-semibold mb-1">
                <span>Expected Success Rate</span>
                <span className="text-emerald-400 font-bold">{(inputs.expected_success_rate * 100).toFixed(0)}%</span>
              </div>
              <input
                type="range"
                min="0.10"
                max="0.70"
                step="0.05"
                value={inputs.expected_success_rate}
                onChange={(e) => setInputs({ ...inputs, expected_success_rate: Number(e.target.value) })}
                className="w-full accent-emerald-400"
              />
            </div>
          </div>

          <div className="pt-3 border-t border-border bg-surfaceElevated p-3 rounded-lg space-y-1">
            <span className="text-[10px] text-gray-400 block">Simulated Net Financial Benefit</span>
            <div className="text-lg font-extrabold text-emerald-400">${results.net_benefit.toLocaleString()}</div>
          </div>
        </div>

        {/* ROI Financial Waterfall Chart */}
        <div className="dark-card p-6 space-y-4 lg:col-span-2">
          <h2 className="text-sm font-bold text-white uppercase tracking-wider">Campaign Financial Waterfall Breakdown</h2>

          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={waterfallData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1f2d47" />
                <XAxis dataKey="stage" stroke="#9ca3af" fontSize={11} />
                <YAxis stroke="#6b7280" fontSize={11} tickFormatter={(val) => `$${(val / 1000).toFixed(0)}k`} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#111726', borderColor: '#1f2d47', borderRadius: '8px', color: '#fff' }}
                  formatter={(val: any) => [`$${Number(val).toLocaleString()}`, 'Amount']}
                />
                <Bar dataKey="amount" radius={[4, 4, 0, 0]}>
                  {waterfallData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.amount >= 0 ? '#10b981' : '#ef4444'} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
};
