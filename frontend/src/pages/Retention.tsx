import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { getRetentionStrategies } from '../api/retention';
import { StatusBadge } from '../components/common/StatusBadge';
import { Target, DollarSign, Award, ArrowRight, Zap, CheckCircle2 } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export const Retention: React.FC = () => {
  const navigate = useNavigate();
  const [selectedFilter, setSelectedFilter] = useState('All');
  const [actionedTiers, setActionedTiers] = useState<Record<string, boolean>>({});

  const { data: strategies, isLoading } = useQuery({
    queryKey: ['retention-strategies'],
    queryFn: () => getRetentionStrategies(),
  });

  const handleTriggerAction = (tier: string) => {
    setActionedTiers((prev) => ({ ...prev, [tier]: true }));
  };

  if (isLoading || !strategies) {
    return <div className="p-12 text-center text-gray-400">Loading Retention Strategy Action Center...</div>;
  }

  const filteredStrategies = strategies.filter((item) => selectedFilter === 'All' || item.risk_tier === selectedFilter);

  return (
    <div className="p-8 space-y-8 max-w-7xl mx-auto">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center space-x-2">
            <Target className="w-6 h-6 text-primary" />
            <span>Retention Strategy Action Center</span>
          </h1>
          <p className="text-xs text-gray-400 mt-1">Prescriptive retention recommendations and ROI-optimized offer deployment per risk tier.</p>
        </div>

        <div className="flex bg-surface p-1 rounded-lg border border-border text-xs font-medium">
          {['All', 'Critical', 'High', 'Medium', 'Low'].map((tier) => (
            <button
              key={tier}
              onClick={() => setSelectedFilter(tier)}
              className={`px-3 py-1.5 rounded-md transition ${
                selectedFilter === tier ? 'bg-primary text-white font-semibold shadow' : 'text-gray-400 hover:text-white'
              }`}
            >
              {tier}
            </button>
          ))}
        </div>
      </div>

      {/* Retention Action Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {filteredStrategies.map((strat) => {
          const isActioned = actionedTiers[strat.risk_tier];

          return (
            <div key={strat.risk_tier} className="dark-card p-6 border-border hover:border-primary/50 flex flex-col justify-between space-y-4">
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <StatusBadge status={strat.risk_tier} size="md" />
                  <span className="text-xs text-gray-400 font-mono font-bold">{strat.action_code}</span>
                </div>

                <div>
                  <h3 className="text-base font-bold text-white">{strat.recommended_action}</h3>
                  <p className="text-xs text-gray-400 mt-1">{strat.description}</p>
                </div>

                <div className="grid grid-cols-2 gap-3 pt-2 text-xs">
                  <div className="bg-surfaceElevated p-2.5 rounded-lg border border-border/80">
                    <span className="text-[10px] text-gray-400 block">Target Customers</span>
                    <span className="font-bold text-white text-sm">{strat.customer_count.toLocaleString()}</span>
                  </div>

                  <div className="bg-surfaceElevated p-2.5 rounded-lg border border-border/80">
                    <span className="text-[10px] text-gray-400 block">Revenue at Risk</span>
                    <span className="font-bold text-red-400 text-sm">${strat.revenue_at_risk.toLocaleString()}</span>
                  </div>

                  <div className="bg-surfaceElevated p-2.5 rounded-lg border border-border/80">
                    <span className="text-[10px] text-gray-400 block">Estimated Offer Cost</span>
                    <span className="font-bold text-amber-400 text-sm">${strat.estimated_cost.toLocaleString()}</span>
                  </div>

                  <div className="bg-surfaceElevated p-2.5 rounded-lg border border-border/80">
                    <span className="text-[10px] text-gray-400 block">Projected ROI</span>
                    <span className="font-bold text-emerald-400 text-sm">{strat.expected_roi}</span>
                  </div>
                </div>
              </div>

              <div className="pt-3 border-t border-border flex items-center justify-between">
                <button
                  onClick={() => navigate(`/customers?risk_tier=${strat.risk_tier}`)}
                  className="text-xs text-gray-400 hover:text-white font-medium flex items-center space-x-1"
                >
                  <span>View Customers</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </button>

                <button
                  onClick={() => handleTriggerAction(strat.risk_tier)}
                  disabled={isActioned}
                  className={`px-4 py-2 rounded-lg text-xs font-semibold flex items-center space-x-1.5 transition ${
                    isActioned
                      ? 'bg-emerald-950/60 border border-emerald-800/60 text-emerald-400 cursor-default'
                      : 'bg-primary hover:bg-primaryHover text-white shadow-md shadow-primary/20'
                  }`}
                >
                  {isActioned ? (
                    <>
                      <CheckCircle2 className="w-4 h-4" />
                      <span>Campaign Deployed</span>
                    </>
                  ) : (
                    <>
                      <Zap className="w-4 h-4" />
                      <span>Deploy Retention Campaign</span>
                    </>
                  )}
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
