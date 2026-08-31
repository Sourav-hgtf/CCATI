import React, { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import {
  getMonitoringStatus,
  getMonitoringHistory,
  runMonitoringScan,
  getModelMetrics,
  FeatureDriftDetail,
} from '../api/monitoring';
import { StatusBadge } from '../components/common/StatusBadge';
import {
  Activity,
  Play,
  CheckCircle2,
  AlertTriangle,
  RefreshCw,
  Sliders,
  Database,
  BarChart2,
  X,
  FileText,
  Clock,
  ShieldCheck,
  TrendingUp,
} from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, Legend } from 'recharts';

interface ModelMonitoringProps {
  currentRole: string;
}

export const ModelMonitoring: React.FC<ModelMonitoringProps> = ({ currentRole }) => {
  const [selectedFeature, setSelectedFeature] = useState<FeatureDriftDetail | null>(null);

  const { data: driftData, isLoading: loadingDrift, refetch: refetchDrift } = useQuery({
    queryKey: ['monitoring-status'],
    queryFn: getMonitoringStatus,
  });

  const { data: historyData, refetch: refetchHistory } = useQuery({
    queryKey: ['monitoring-history'],
    queryFn: getMonitoringHistory,
  });

  const { data: metricsData } = useQuery({
    queryKey: ['model-metrics'],
    queryFn: getModelMetrics,
  });

  const scanMutation = useMutation({
    mutationFn: runMonitoringScan,
    onSuccess: () => {
      refetchDrift();
      refetchHistory();
    },
  });

  if (loadingDrift || !driftData) {
    return (
      <div className="p-16 text-center text-gray-400 flex flex-col items-center justify-center space-y-4">
        <RefreshCw className="w-8 h-8 text-[#F5A623] animate-spin" />
        <span className="text-sm font-semibold text-gray-300">Computing statistical data drift analysis against production inference records...</span>
      </div>
    );
  }

  const getStatusVariant = (status: string) => {
    switch (status) {
      case 'CRITICAL':
        return 'danger';
      case 'WARNING':
        return 'warning';
      case 'STABLE':
        return 'success';
      default:
        return 'secondary';
    }
  };

  const canTrigger = ['Admin', 'Analyst'].includes(currentRole);

  const chartData = (metricsData?.history || []).map((h, i) => ({
    run: `Run ${metricsData!.history.length - i}`,
    Precision: h.precision,
    Recall: h.recall,
    F1: h.f1,
    'PR-AUC': h.pr_auc,
  }));

  return (
    <div className="p-8 space-y-8 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center space-x-2">
            <Activity className="w-6 h-6 text-[#F5A623]" />
            <span>Model Health & Data Drift Intelligence Console</span>
          </h1>
          <p className="text-xs text-gray-400 mt-1">
            Statistical PSI drift metrics, feature distribution shifts, and production classifier health monitoring.
          </p>
        </div>

        {canTrigger && (
          <button
            onClick={() => scanMutation.mutate()}
            disabled={scanMutation.isPending}
            className="px-5 py-2.5 rounded-lg bg-[#F5A623] hover:bg-[#E0951C] text-black font-bold text-xs flex items-center space-x-2 shadow-lg shadow-[#F5A623]/20 transition disabled:opacity-50"
          >
            {scanMutation.isPending ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4 fill-current" />}
            <span>{scanMutation.isPending ? 'Running Statistical Scan...' : 'Run Monitoring Scan'}</span>
          </button>
        )}
      </div>

      {/* 5 KPI Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
        <div className="dark-card p-5 space-y-2 border-[#272B36]">
          <span className="text-xs font-semibold text-gray-400">Monitoring Status</span>
          <div className="pt-1">
            <StatusBadge status={driftData.status} size="md" />
          </div>
        </div>

        <div className="dark-card p-5 space-y-2 border-[#272B36]">
          <span className="text-xs font-semibold text-gray-400">Features Monitored</span>
          <div className="text-2xl font-extrabold text-white">{driftData.features_checked}</div>
          <span className="text-[10px] text-gray-500">Numerical & Categorical</span>
        </div>

        <div className="dark-card p-5 space-y-2 border-[#272B36]">
          <span className="text-xs font-semibold text-gray-400">Features Drifted</span>
          <div className={`text-2xl font-extrabold ${driftData.features_drifted > 0 ? 'text-red-400' : 'text-emerald-400'}`}>
            {driftData.features_drifted}
          </div>
          <span className="text-[10px] text-gray-500">PSI Threshold ≥ 0.10</span>
        </div>

        <div className="dark-card p-5 space-y-2 border-[#272B36]">
          <span className="text-xs font-semibold text-gray-400">Overall Drift Score</span>
          <div className="text-2xl font-extrabold text-[#F5A623]">{driftData.overall_score.toFixed(4)}</div>
          <span className="text-[10px] text-gray-500">Population Stability Index</span>
        </div>

        <div className="dark-card p-5 space-y-2 border-[#272B36]">
          <span className="text-xs font-semibold text-gray-400">Active Model Version</span>
          <div className="text-sm font-mono font-bold text-white truncate">{driftData.model_version}</div>
          <span className="text-[10px] text-emerald-400 flex items-center mt-1">
            <ShieldCheck className="w-3 h-3 mr-1" /> Verified SHA-256
          </span>
        </div>
      </div>

      {/* AI Recommendation & Alert Card */}
      <div className="dark-card p-6 border-[#F5A623]/30 bg-[#151821] space-y-3">
        <div className="flex items-center space-x-2">
          <AlertTriangle className={`w-5 h-5 ${driftData.status === 'CRITICAL' ? 'text-red-400' : driftData.status === 'WARNING' ? 'text-amber-400' : 'text-emerald-400'}`} />
          <h3 className="text-sm font-bold text-white uppercase tracking-wider">Actionable Recommendation</h3>
        </div>
        <p className="text-xs text-gray-300 font-medium">{driftData.recommended_action}</p>
        <div className="text-[11px] text-gray-500 pt-2 border-t border-[#272B36] flex items-center justify-between">
          <span>Last Statistical Run ID: <strong className="font-mono text-gray-300">{driftData.monitoring_id}</strong></span>
          <span>{new Date(driftData.timestamp).toLocaleString()}</span>
        </div>
      </div>

      {/* Feature Drift Analysis Table */}
      <div className="dark-card p-6 space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-sm font-bold text-white uppercase tracking-wider">Feature Drift Statistical Analysis</h2>
            <p className="text-xs text-gray-400 mt-0.5">Real-time baseline vs production inference population distribution metrics.</p>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-[#1A1D24] text-gray-400 uppercase text-[10px]">
              <tr>
                <th className="p-3">Feature Name</th>
                <th className="p-3">Type</th>
                <th className="p-3">Baseline Mean</th>
                <th className="p-3">Current Mean</th>
                <th className="p-3">PSI Score</th>
                <th className="p-3">Severity</th>
                <th className="p-3">Status</th>
                <th className="p-3 text-right">Inspect</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#272B36]">
              {driftData.features.map((feat) => (
                <tr key={feat.name} className="hover:bg-[#1A1D24]/50 transition">
                  <td className="p-3 font-mono font-bold text-white">{feat.name}</td>
                  <td className="p-3 text-gray-400 capitalize">{feat.type}</td>
                  <td className="p-3 font-mono text-gray-300">{feat.baseline_stats.mean ?? 'N/A'}</td>
                  <td className="p-3 font-mono text-gray-300">{feat.current_stats.mean ?? 'N/A'}</td>
                  <td className="p-3 font-mono font-bold text-[#F5A623]">{feat.drift_score.toFixed(4)}</td>
                  <td className="p-3">
                    <span
                      className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                        feat.severity === 'CRITICAL'
                          ? 'bg-red-950 text-red-400 border border-red-500/40'
                          : feat.severity === 'WARNING'
                          ? 'bg-amber-950 text-amber-400 border border-amber-500/40'
                          : 'bg-emerald-950 text-emerald-400 border border-emerald-500/40'
                      }`}
                    >
                      {feat.severity}
                    </span>
                  </td>
                  <td className="p-3">
                    <StatusBadge status={feat.status === 'DRIFTING' ? 'High' : 'Low'} size="sm" />
                  </td>
                  <td className="p-3 text-right">
                    <button
                      onClick={() => setSelectedFeature(feat)}
                      className="px-3 py-1 bg-[#1A1D24] hover:bg-[#272B36] text-gray-300 hover:text-white rounded border border-[#272B36] text-[11px] font-semibold transition"
                    >
                      Inspect Details
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Model Performance History Chart */}
      {chartData.length > 0 && (
        <div className="dark-card p-6 space-y-4">
          <h2 className="text-sm font-bold text-white uppercase tracking-wider">Classification Performance History</h2>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData}>
                <XAxis dataKey="run" stroke="#9ca3af" fontSize={11} />
                <YAxis stroke="#9ca3af" fontSize={11} domain={[0.4, 1.0]} />
                <Tooltip contentStyle={{ backgroundColor: '#151821', borderColor: '#272B36', borderRadius: '8px', color: '#fff' }} />
                <Legend />
                <Line type="monotone" dataKey="Precision" stroke="#3b82f6" strokeWidth={2} />
                <Line type="monotone" dataKey="Recall" stroke="#10b981" strokeWidth={2} />
                <Line type="monotone" dataKey="PR-AUC" stroke="#F5A623" strokeWidth={2} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* Monitoring Run History Log */}
      <div className="dark-card p-6 space-y-4">
        <h2 className="text-sm font-bold text-white uppercase tracking-wider flex items-center space-x-2">
          <Clock className="w-4 h-4 text-[#F5A623]" />
          <span>Monitoring Execution Audit History</span>
        </h2>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-[#1A1D24] text-gray-400 uppercase text-[10px]">
              <tr>
                <th className="p-3">Run ID</th>
                <th className="p-3">Timestamp</th>
                <th className="p-3">Model Version</th>
                <th className="p-3">Overall Status</th>
                <th className="p-3">Drift Score</th>
                <th className="p-3">Drifted / Checked</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#272B36]">
              {(historyData || []).map((h) => (
                <tr key={h.monitoring_id} className="hover:bg-[#1A1D24]/50 transition">
                  <td className="p-3 font-mono font-bold text-white">{h.monitoring_id}</td>
                  <td className="p-3 text-gray-400">{new Date(h.timestamp).toLocaleString()}</td>
                  <td className="p-3 font-mono text-[#F5A623]">{h.model_version}</td>
                  <td className="p-3">
                    <StatusBadge status={h.overall_status === 'CRITICAL' ? 'Critical' : h.overall_status === 'WARNING' ? 'High' : 'Low'} size="sm" />
                  </td>
                  <td className="p-3 font-mono font-bold text-white">{h.overall_score.toFixed(4)}</td>
                  <td className="p-3 text-gray-300">
                    {h.features_drifted} / {h.features_checked}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Feature Inspection Modal Drawer */}
      {selectedFeature && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="dark-card max-w-lg w-full p-6 space-y-5 border-[#F5A623]/40 shadow-2xl relative animate-in fade-in zoom-in duration-200">
            <button
              onClick={() => setSelectedFeature(null)}
              className="absolute top-4 right-4 text-gray-400 hover:text-white p-1 rounded-lg hover:bg-[#1A1D24] transition"
            >
              <X className="w-5 h-5" />
            </button>

            <div>
              <div className="flex items-center space-x-2">
                <Sliders className="w-5 h-5 text-[#F5A623]" />
                <h3 className="text-base font-bold text-white font-mono">{selectedFeature.name}</h3>
              </div>
              <p className="text-xs text-gray-400 mt-1">Detailed statistical drift distribution comparison.</p>
            </div>

            <div className="grid grid-cols-2 gap-3 text-xs">
              <div className="bg-[#1A1D24] p-3 rounded-lg border border-[#272B36] space-y-1">
                <span className="text-gray-400 text-[10px]">Feature Type</span>
                <p className="font-semibold text-white capitalize">{selectedFeature.type}</p>
              </div>
              <div className="bg-[#1A1D24] p-3 rounded-lg border border-[#272B36] space-y-1">
                <span className="text-gray-400 text-[10px]">PSI Drift Score</span>
                <p className="font-mono font-bold text-[#F5A623]">{selectedFeature.drift_score.toFixed(4)}</p>
              </div>
              <div className="bg-[#1A1D24] p-3 rounded-lg border border-[#272B36] space-y-1">
                <span className="text-gray-400 text-[10px]">Statistical P-Value</span>
                <p className="font-mono font-semibold text-gray-200">{selectedFeature.p_value.toFixed(4)}</p>
              </div>
              <div className="bg-[#1A1D24] p-3 rounded-lg border border-[#272B36] space-y-1">
                <span className="text-gray-400 text-[10px]">Severity Classification</span>
                <p className="font-bold text-amber-400">{selectedFeature.severity}</p>
              </div>
            </div>

            {selectedFeature.type === 'numerical' && (
              <div className="bg-[#1A1D24] p-4 rounded-xl border border-[#272B36] space-y-3">
                <h4 className="text-xs font-bold text-white uppercase tracking-wider">Baseline vs Production Statistics</h4>
                <div className="grid grid-cols-2 gap-4 text-xs">
                  <div>
                    <span className="text-gray-400 text-[10px] block font-semibold">Baseline Distribution</span>
                    <p className="text-gray-300">Mean: <strong className="text-white font-mono">{selectedFeature.baseline_stats.mean}</strong></p>
                    <p className="text-gray-300">Std: <strong className="text-white font-mono">{selectedFeature.baseline_stats.std}</strong></p>
                    <p className="text-gray-300">Min: <strong className="text-white font-mono">{selectedFeature.baseline_stats.min}</strong></p>
                    <p className="text-gray-300">Max: <strong className="text-white font-mono">{selectedFeature.baseline_stats.max}</strong></p>
                  </div>

                  <div>
                    <span className="text-gray-400 text-[10px] block font-semibold">Production Distribution</span>
                    <p className="text-gray-300">Mean: <strong className="text-[#F5A623] font-mono">{selectedFeature.current_stats.mean}</strong></p>
                    <p className="text-gray-300">Std: <strong className="text-white font-mono">{selectedFeature.current_stats.std}</strong></p>
                    <p className="text-gray-300">Min: <strong className="text-white font-mono">{selectedFeature.current_stats.min}</strong></p>
                    <p className="text-gray-300">Max: <strong className="text-white font-mono">{selectedFeature.current_stats.max}</strong></p>
                  </div>
                </div>
              </div>
            )}

            <div className="pt-2 flex justify-end">
              <button
                onClick={() => setSelectedFeature(null)}
                className="px-4 py-2 bg-[#F5A623] hover:bg-[#E0951C] text-black font-bold text-xs rounded-lg transition"
              >
                Close Inspection
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
