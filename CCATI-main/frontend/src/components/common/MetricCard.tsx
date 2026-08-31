import React from 'react';
import { LucideIcon, TrendingUp, TrendingDown } from 'lucide-react';

interface MetricCardProps {
  label: string;
  value: string | number;
  change?: number;
  changeLabel?: string;
  description?: string;
  icon: LucideIcon;
  variant?: 'primary' | 'secondary' | 'success' | 'warning' | 'danger';
}

export const MetricCard: React.FC<MetricCardProps> = ({
  label,
  value,
  change,
  changeLabel = 'vs prev month',
  description,
  icon: Icon,
  variant = 'secondary',
}) => {
  let accentColor = 'border-border hover:border-blue-500/40';
  let iconBg = 'bg-blue-500/10 text-blue-400';

  if (variant === 'primary') {
    accentColor = 'border-primary/40 hover:border-primary/70';
    iconBg = 'bg-primary/10 text-primary';
  } else if (variant === 'success') {
    accentColor = 'border-emerald-500/30 hover:border-emerald-500/60';
    iconBg = 'bg-emerald-500/10 text-emerald-400';
  } else if (variant === 'warning') {
    accentColor = 'border-amber-500/30 hover:border-amber-500/60';
    iconBg = 'bg-amber-500/10 text-amber-400';
  } else if (variant === 'danger') {
    accentColor = 'border-red-500/30 hover:border-red-500/60';
    iconBg = 'bg-red-500/10 text-red-400';
  }

  const isPositive = change !== undefined && change >= 0;

  return (
    <div className={`dark-card dark-card-hover p-5 border ${accentColor}`}>
      <div className="flex items-center justify-between">
        <span className="text-xs font-semibold text-gray-400 uppercase tracking-wider">{label}</span>
        <div className={`w-9 h-9 rounded-lg flex items-center justify-center ${iconBg}`}>
          <Icon className="w-4 h-4" />
        </div>
      </div>

      <div className="mt-3">
        <div className="text-2xl font-extrabold text-white tracking-tight">{value}</div>

        <div className="mt-2 flex items-center justify-between text-xs">
          {change !== undefined ? (
            <div className={`flex items-center font-semibold ${isPositive ? 'text-emerald-400' : 'text-red-400'}`}>
              {isPositive ? <TrendingUp className="w-3.5 h-3.5 mr-1" /> : <TrendingDown className="w-3.5 h-3.5 mr-1" />}
              <span>{change > 0 ? `+${change}%` : `${change}%`}</span>
              <span className="text-gray-500 ml-1.5 font-normal">{changeLabel}</span>
            </div>
          ) : (
            description && <span className="text-gray-400 text-[11px]">{description}</span>
          )}
        </div>
      </div>
    </div>
  );
};
