import React, { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { getDataOverview, triggerDataRefresh } from '../api/data';
import { StatusBadge } from '../components/common/StatusBadge';
import { Database, RefreshCw, Upload, CheckCircle2, ShieldCheck, FileSpreadsheet } from 'lucide-react';

export const DataManagement: React.FC = () => {
  const [refreshMessage, setRefreshMessage] = useState<string | null>(null);

  const { data: overview, isLoading, refetch } = useQuery({
    queryKey: ['data-overview'],
    queryFn: () => getDataOverview(),
  });

  const mutation = useMutation({
    mutationFn: () => triggerDataRefresh(),
    onSuccess: (res) => {
      setRefreshMessage(res.message);
      refetch();
    },
  });

  if (isLoading || !overview) {
    return <div className="p-12 text-center text-gray-400">Loading Data Management Metrics...</div>;
  }

  return (
    <div className="p-8 space-y-8 max-w-7xl mx-auto">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center space-x-2">
            <Database className="w-6 h-6 text-primary" />
            <span>Telemetry Data Management & Schema Health</span>
          </h1>
          <p className="text-xs text-gray-400 mt-1">Parquet ingestion pipeline status, data quality scores, and feature schema definitions.</p>
        </div>

        <div className="flex items-center space-x-3">
          <button
            onClick={() => mutation.mutate()}
            disabled={mutation.isPending}
            className="px-4 py-2 rounded-lg bg-surfaceHover hover:bg-border text-xs font-semibold text-white flex items-center space-x-1.5 transition disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${mutation.isPending ? 'animate-spin' : ''}`} />
            <span>{mutation.isPending ? 'Ingesting Data...' : 'Refresh Ingestion'}</span>
          </button>
          <button className="px-4 py-2 rounded-lg bg-primary hover:bg-primaryHover text-white text-xs font-semibold flex items-center space-x-1.5 shadow-md shadow-primary/20 transition">
            <Upload className="w-3.5 h-3.5" />
            <span>Upload New Parquet</span>
          </button>
        </div>
      </div>

      {refreshMessage && (
        <div className="bg-emerald-950/60 border border-emerald-800/80 p-4 rounded-xl text-xs text-emerald-300 flex items-center space-x-2">
          <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
          <span>{refreshMessage}</span>
        </div>
      )}

      {/* Dataset Health Summary Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
        <div className="dark-card p-4 space-y-1">
          <span className="text-[10px] uppercase font-bold text-gray-400">Total Rows</span>
          <p className="text-xl font-extrabold text-white">{overview.total_rows.toLocaleString()}</p>
        </div>
        <div className="dark-card p-4 space-y-1">
          <span className="text-[10px] uppercase font-bold text-gray-400">Total Columns</span>
          <p className="text-xl font-extrabold text-white">{overview.total_columns}</p>
        </div>
        <div className="dark-card p-4 space-y-1">
          <span className="text-[10px] uppercase font-bold text-gray-400">Missing Values</span>
          <p className="text-xl font-extrabold text-emerald-400">{overview.missing_values_count}</p>
        </div>
        <div className="dark-card p-4 space-y-1">
          <span className="text-[10px] uppercase font-bold text-gray-400">Duplicate Rows</span>
          <p className="text-xl font-extrabold text-emerald-400">{overview.duplicate_rows_count}</p>
        </div>
        <div className="dark-card p-4 space-y-1 border-emerald-500/30">
          <span className="text-[10px] uppercase font-bold text-gray-400">Data Quality Score</span>
          <p className="text-xl font-extrabold text-emerald-400">{overview.data_quality_score}/100</p>
        </div>
      </div>

      {/* Feature Schema Table */}
      <div className="dark-card p-6 space-y-4">
        <h2 className="text-sm font-bold text-white uppercase tracking-wider">Feature Data Schema & Quality Status</h2>

        <div className="table-responsive border border-border/80 rounded-lg overflow-hidden">
          <table className="w-full text-left text-xs text-gray-300">
            <thead className="bg-[#0e1422] text-gray-400 font-semibold border-b border-border uppercase tracking-wider text-[10px]">
              <tr>
                <th className="py-3 px-4">Feature Name</th>
                <th className="py-3 px-4">Data Type</th>
                <th className="py-3 px-4">Missing %</th>
                <th className="py-3 px-4">Unique Values</th>
                <th className="py-3 px-4">Quality Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border/60 bg-surface">
              {overview.features.map((feat) => (
                <tr key={feat.feature_name} className="hover:bg-surfaceHover transition">
                  <td className="py-3 px-4 font-mono font-bold text-white">{feat.feature_name}</td>
                  <td className="py-3 px-4 text-gray-400 font-mono">{feat.data_type}</td>
                  <td className="py-3 px-4 font-semibold text-emerald-400">{feat.missing_pct.toFixed(1)}%</td>
                  <td className="py-3 px-4">{feat.unique_values.toLocaleString()}</td>
                  <td className="py-3 px-4">
                    <StatusBadge status={feat.status} size="sm" />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
