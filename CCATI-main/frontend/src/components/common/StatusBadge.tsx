import React from 'react';

interface StatusBadgeProps {
  status: 'Low' | 'Medium' | 'High' | 'Critical' | 'STABLE' | 'DRIFTING' | 'Clean' | string;
  size?: 'sm' | 'md';
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status, size = 'md' }) => {
  const normalized = status.toUpperCase();

  let style = 'bg-gray-800/80 text-gray-300 border-gray-700';

  if (['LOW', 'STABLE', 'CLEAN', 'HEALTHY', 'COMPLETED'].includes(normalized)) {
    style = 'bg-emerald-950/60 text-emerald-400 border-emerald-800/60';
  } else if (['MEDIUM', 'AMBER', 'WARNING', 'IMPUTED'].includes(normalized)) {
    style = 'bg-amber-950/60 text-amber-400 border-amber-800/60';
  } else if (['HIGH', 'ORANGE'].includes(normalized)) {
    style = 'bg-orange-950/60 text-orange-400 border-orange-800/60';
  } else if (['CRITICAL', 'DRIFTING', 'RED', 'FAILED'].includes(normalized)) {
    style = 'bg-red-950/60 text-red-400 border-red-800/60';
  }

  const padding = size === 'sm' ? 'px-2 py-0.5 text-[10px]' : 'px-2.5 py-1 text-xs';

  return (
    <span className={`inline-flex items-center font-semibold rounded-full border ${padding} ${style}`}>
      <span className="w-1.5 h-1.5 rounded-full bg-current mr-1.5" />
      {status}
    </span>
  );
};
