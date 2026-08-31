import React from 'react';
import { Sparkles, AlertTriangle, ArrowRight, ShieldAlert, Zap } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

interface InsightCardProps {
  riskSummary?: string;
  revenueExposure?: string;
  primaryRiskDriver?: string;
  recommendedAction?: string;
}

export const InsightCard: React.FC<InsightCardProps> = ({
  riskSummary = '3,183 customers are currently classified as high-risk.',
  revenueExposure = '$211,937 monthly revenue is exposed to potential churn.',
  primaryRiskDriver = 'Declining usage (-32%) and increased customer service contacts (6+ calls).',
  recommendedAction = 'Prioritize retention outreach for high-value customers with churn probability > 70%.',
}) => {
  const navigate = useNavigate();

  return (
    <div className="dark-card bg-gradient-to-r from-surfaceElevated via-surface to-surface border border-primary/30 p-6 shadow-xl relative overflow-hidden">
      <div className="absolute -top-12 -right-12 w-48 h-48 bg-primary/10 rounded-full blur-3xl pointer-events-none" />

      <div className="flex items-center space-x-2 text-primary font-bold text-sm mb-4">
        <div className="w-7 h-7 rounded-lg bg-primary/20 flex items-center justify-center border border-primary/40">
          <Sparkles className="w-4 h-4 text-primary" />
        </div>
        <span>AI Executive Insights</span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-surface/80 border border-border/80 rounded-lg p-3.5 space-y-1">
          <div className="flex items-center text-xs font-semibold text-red-400">
            <ShieldAlert className="w-3.5 h-3.5 mr-1.5 shrink-0" /> Risk Summary
          </div>
          <p className="text-xs text-gray-200 leading-snug">{riskSummary}</p>
        </div>

        <div className="bg-surface/80 border border-border/80 rounded-lg p-3.5 space-y-1">
          <div className="flex items-center text-xs font-semibold text-amber-400">
            <AlertTriangle className="w-3.5 h-3.5 mr-1.5 shrink-0" /> Revenue Exposure
          </div>
          <p className="text-xs text-gray-200 leading-snug">{revenueExposure}</p>
        </div>

        <div className="bg-surface/80 border border-border/80 rounded-lg p-3.5 space-y-1">
          <div className="flex items-center text-xs font-semibold text-blue-400">
            <Zap className="w-3.5 h-3.5 mr-1.5 shrink-0" /> Primary Risk Driver
          </div>
          <p className="text-xs text-gray-200 leading-snug">{primaryRiskDriver}</p>
        </div>

        <div className="bg-surface/80 border border-primary/30 rounded-lg p-3.5 space-y-1">
          <div className="flex items-center text-xs font-semibold text-primary">
            <Sparkles className="w-3.5 h-3.5 mr-1.5 shrink-0" /> Recommended Action
          </div>
          <p className="text-xs text-gray-200 leading-snug">{recommendedAction}</p>
        </div>
      </div>

      <div className="mt-5 flex items-center justify-end space-x-3 pt-3 border-t border-border/60">
        <button
          onClick={() => navigate('/explainability')}
          className="px-3.5 py-1.5 rounded-lg text-xs font-semibold text-gray-300 hover:text-white bg-surfaceElevated hover:bg-surfaceHover border border-border transition"
        >
          View Explanation
        </button>
        <button
          onClick={() => navigate('/customers?risk_tier=High')}
          className="px-3.5 py-1.5 rounded-lg text-xs font-semibold text-white bg-primary hover:bg-primaryHover transition flex items-center space-x-1.5 shadow-md shadow-primary/20"
        >
          <span>View High-Risk Customers</span>
          <ArrowRight className="w-3.5 h-3.5" />
        </button>
      </div>
    </div>
  );
};
