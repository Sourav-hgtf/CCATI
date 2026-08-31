import React, { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import {
  getMonitoringStatus,
  getMonitoringHistory,
  runMonitoringScan,
  getPerformanceMonitoring,
  getPerformanceHistory,
  runPerformanceScan,
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
  BarChart2,
  X,
  Clock,
  ShieldCheck,
  Award,
  Layers,
  HelpCircle,
  TrendingDown,
  TrendingUp,
} from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, Legend } from 'recharts';

interface ModelMonitoringProps {
  currentRole: string;
}

export const ModelMonitoring: React.FC<ModelMonitoringProps> = ({ currentRole }) => {
  const [activeTab, setActiveTab] = useState<'performance' | 'drift'>('performance');
  const [selectedFeature, setSelectedFeature] = useState<FeatureDriftDetail | null>(null);

  // Task 9 Performance Monitoring Queries
  const { data: perfData, isLoading: loadingPerf, refetch: refetchPerf } = useQuery({
    queryKey: ['monitoring-performance'],
    queryFn: getPerformanceMonitoring,
  });

  const { data: perfHistoryData, refetch: refetchPerfHistory } = useQuery({
    queryKey: ['monitoring-performance-history'],
    queryFn: getPerformanceHistory,
  });

  const perfMutation = useMutation({
    mutationFn: runPerformanceScan,
    onSuccess: () => {
      refetchPerf();
      refetchPerfHistory();
    },
  });

  // Task 8 Data Drift Queries
  const { data: driftData, isLoading: loadingDrift, refetch: refetchDrift } = useQuery({
    queryKey: ['monitoring-status'],
    queryFn: getMonitoringStatus,
  });

  const { data: driftHistoryData, refetch: refetchDriftHistory } = useQuery({
    queryKey: ['monitoring-history'],
    queryFn: getMonitoringHistory,
  });

  const driftMutation = useMutation({
    mutationFn: runMonitoringScan,
    onSuccess: () => {
      refetchDrift();
      refetchDriftHistory();
    },
  });

  const { data: metricsData } = useQuery({
    queryKey: ['model-metrics'],
    queryFn: getModelMetrics,
  });

  if (loadingPerf || loadingDrift || !perfData || !driftData) {
    return (
      <div className="p-16 text-center text-gray-400 flex flex-col items-center justify-center space-y-4">
        <RefreshCw className="w-8 h-8 text-[#F5A623] animate-spin" />
        <span className="text-sm font-semibold text-gray-300">Evaluating production model performance and statistical data drift...</span>
      </div>
    );
  }

  const canTrigger = ['Admin', 'Analyst'].includes(currentRole);
  const m = perfData.metrics;
  const b = perfData.baseline;
  const cm = perfData.confusion_matrix;
  const d = perfData.deltas;

  const chartData = (metricsData?.history || []).map((h, i) => ({
    run: `Run ${metricsData!.history.length - i}`,
    Precision: h.precision,
    Recall: h.recall,
    F1: h.f1,
    'PR-AUC': h.pr_auc,
  }));

  return (
    <div className="p-8 space-y-8 max-w-7xl mx-auto">
      {/* Header & Sub-Navigation Tabs */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center space-x-2">
            <Activity className="w-6 h-6 text-[#F5A623]" />
            <span>Model Health & Performance Monitoring</span>
          </h1>
          <p className="text-xs text-gray-400 mt-1">
            Production classification performance metrics, baseline evaluation deltas, and statistical feature drift.
          </p>
        </div>

        {/* Tab Switcher */}
        <div className="flex items-center space-x-3">
          <div className="flex bg-[#151821] p-1 rounded-xl border border-[#272B36] text-xs font-semibold">
            <button
              onClick={() => setActiveTab('performance')}
              className={`px-4 py-2 rounded-lg transition ${
                activeTab === 'performance' ? 'bg-[#F5A623] text-black font-bold shadow' : 'text-gray-400 hover:text-white'
              }`}
            >
              Model Performance & Quality
            </button>
            <button
              onClick={() => setActiveTab('drift')}
              className={`px-4 py-2 rounded-lg transition ${
                activeTab === 'drift' ? 'bg-[#F5A623] text-black font-bold shadow' : 'text-gray-400 hover:text-white'
              }`}
            >
              Data Drift Intelligence
            </button>
          </div>

          {canTrigger && (
            <button
              onClick={() => (activeTab === 'performance' ? perfMutation.mutate() : driftMutation.mutate())}
              disabled={perfMutation.isPending || driftMutation.isPending}
              className="px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs flex items-center space-x-2 shadow-lg shadow-emerald-600/20 transition disabled:opacity-50"
            >
              {perfMutation.isPending || driftMutation.isPending ? (
                <RefreshCw className="w-4 h-4 animate-spin" />
              ) : (
                <Play className="w-4 h-4 fill-current" />
              )}
              <span>{activeTab === 'performance' ? 'Run Performance Evaluation' : 'Run Drift Scan'}</span>
            </button>
          )}
        </div>
      </div>

      {/* TAB 1: MODEL PERFORMANCE & QUALITY (TASK 9) */}
      {activeTab === 'performance' && (
        <div className="space-y-8">
          {/* Health Status & 6 KPI Cards Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-6 gap-4">
            <div className="dark-card p-5 space-y-2 border-[#272B36]">
              <span className="text-xs font-semibold text-gray-400">Model Health</span>
              <div className="pt-1">
                <StatusBadge status={perfData.status} size="md" />
              </div>
            </div>

            <div className="dark-card p-5 space-y-2 border-[#272B36]">
              <span className="text-xs font-semibold text-gray-400">Precision Score</span>
              <div className="text-2xl font-extrabold text-white">{m ? (m.precision * 100).toFixed(1) + '%' : 'N/A'}</div>
              <span className="text-[10px] text-gray-500">Baseline: {(b.precision * 100).toFixed(1)}%</span>
            </div>

            <div className="dark-card p-5 space-y-2 border-[#272B36]">
              <span className="text-xs font-semibold text-gray-400">Recall Score</span>
              <div className="text-2xl font-extrabold text-emerald-400">{m ? (m.recall * 100).toFixed(1) + '%' : 'N/A'}</div>
              <span className="text-[10px] text-gray-500">Baseline: {(b.recall * 100).toFixed(1)}%</span>
            </div>

            <div className="dark-card p-5 space-y-2 border-[#272B36]">
              <span className="text-xs font-semibold text-gray-400">F1 Score</span>
              <div className="text-2xl font-extrabold text-[#F5A623]">{m ? (m.f1 * 100).toFixed(1) + '%' : 'N/A'}</div>
              <span className="text-[10px] text-gray-500">Baseline: {(b.f1 * 100).toFixed(1)}%</span>
            </div>

            <div className="dark-card p-5 space-y-2 border-[#272B36]">
              <span className="text-xs font-semibold text-gray-400">ROC-AUC Score</span>
              <div className="text-2xl font-extrabold text-blue-400">{m ? (m.roc_auc * 100).toFixed(1) + '%' : 'N/A'}</div>
              <span className="text-[10px] text-gray-500">Baseline: {(b.roc_auc * 100).toFixed(1)}%</span>
            </div>

            <div className="dark-card p-5 space-y-2 border-[#272B36]">
              <span className="text-xs font-semibold text-gray-400">Decision Threshold</span>
              <div className="text-2xl font-extrabold text-white">{(perfData.threshold * 100).toFixed(0)}%</div>
              <span className="text-[10px] text-gray-500">Configured Cutoff</span>
            </div>
          </div>

          {/* Actionable Performance Alert Banner */}
          <div className="dark-card p-6 border-[#F5A623]/30 bg-[#151821] space-y-3">
            <div className="flex items-center space-x-2">
              <AlertTriangle className={`w-5 h-5 ${perfData.status === 'CRITICAL' ? 'text-red-400' : perfData.status === 'WARNING' ? 'text-amber-400' : 'text-emerald-400'}`} />
              <h3 className="text-sm font-bold text-white uppercase tracking-wider">Performance Recommendation</h3>
            </div>
            <p className="text-xs text-gray-300 font-medium">{perfData.recommended_action}</p>
            <div className="text-[11px] text-gray-500 pt-2 border-t border-[#272B36] flex items-center justify-between">
              <span>Evaluated Record Sample: <strong className="font-mono text-gray-300">{perfData.sample_count} subscribers</strong></span>
              <span>{new Date(perfData.timestamp).toLocaleString()}</span>
            </div>
          </div>

          {/* Grid: Confusion Matrix & Baseline Comparison */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            {/* Confusion Matrix Card */}
            <div className="dark-card p-6 space-y-4">
              <div>
                <h3 className="text-sm font-bold text-white uppercase tracking-wider">Production Confusion Matrix</h3>
                <p className="text-xs text-gray-400 mt-0.5">Real classification outcomes against ground-truth customer records.</p>
              </div>

              {cm ? (
                <div className="grid grid-cols-2 gap-4 pt-2">
                  <div className="bg-[#1A1D24] p-4 rounded-xl border border-[#272B36] text-center space-y-1">
                    <span className="text-xs text-gray-400 font-semibold">True Negatives (TN)</span>
                    <div className="text-2xl font-extrabold text-gray-200">{cm.tn}</div>
                    <p className="text-[10px] text-gray-500">Correct Non-Churn Predictions</p>
                  </div>
                  <div className="bg-[#1A1D24] p-4 rounded-xl border border-[#272B36] text-center space-y-1">
                    <span className="text-xs text-gray-400 font-semibold">False Positives (FP)</span>
                    <div className="text-2xl font-extrabold text-amber-400">{cm.fp}</div>
                    <p className="text-[10px] text-gray-500">False Alarm / Over-retention</p>
                  </div>
                  <div className="bg-[#1A1D24] p-4 rounded-xl border border-[#272B36] text-center space-y-1">
                    <span className="text-xs text-gray-400 font-semibold">False Negatives (FN)</span>
                    <div className="text-2xl font-extrabold text-red-400">{cm.fn}</div>
                    <p className="text-[10px] text-gray-500">Missed Churn Risk Subscriber</p>
                  </div>
                  <div className="bg-[#1A1D24] p-4 rounded-xl border border-[#272B36] text-center space-y-1">
                    <span className="text-xs text-gray-400 font-semibold">True Positives (TP)</span>
                    <div className="text-2xl font-extrabold text-emerald-400">{cm.tp}</div>
                    <p className="text-[10px] text-gray-500">Saved At-Risk Subscriber</p>
                  </div>
                </div>
              ) : (
                <div className="p-8 text-center text-gray-500 text-xs">
                  Ground-truth labels unavailable for confusion matrix computation.
                </div>
              )}
            </div>

            {/* Baseline vs Current Metrics Comparison Table */}
            <div className="dark-card p-6 space-y-4">
              <div>
                <h3 className="text-sm font-bold text-white uppercase tracking-wider">Baseline vs Production Metrics</h3>
                <p className="text-xs text-gray-400 mt-0.5">Model Registry baseline evaluation comparison.</p>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="bg-[#1A1D24] text-gray-400 uppercase text-[10px]">
                    <tr>
                      <th className="p-3">Metric</th>
                      <th className="p-3">Baseline</th>
                      <th className="p-3">Production</th>
                      <th className="p-3">Delta</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[#272B36]">
                    {[
                      { name: 'Precision', base: b.precision, curr: m?.precision, delta: d?.precision_delta },
                      { name: 'Recall', base: b.recall, curr: m?.recall, delta: d?.recall_delta },
                      { name: 'F1 Score', base: b.f1, curr: m?.f1, delta: d?.f1_delta },
                      { name: 'ROC-AUC', base: b.roc_auc, curr: m?.roc_auc, delta: d?.roc_auc_delta },
                      { name: 'PR-AUC', base: b.pr_auc, curr: m?.pr_auc, delta: d?.pr_auc_delta },
                    ].map((row) => (
                      <tr key={row.name}>
                        <td className="p-3 font-semibold text-white">{row.name}</td>
                        <td className="p-3 font-mono text-gray-400">{(row.base * 100).toFixed(2)}%</td>
                        <td className="p-3 font-mono text-white">{row.curr ? (row.curr * 100).toFixed(2) + '%' : 'N/A'}</td>
                        <td className="p-3 font-mono font-bold">
                          {row.delta !== undefined ? (
                            <span className={row.delta >= 0 ? 'text-emerald-400' : 'text-red-400'}>
                              {row.delta >= 0 ? `+${(row.delta * 100).toFixed(2)}%` : `${(row.delta * 100).toFixed(2)}%`}
                            </span>
                          ) : (
                            'N/A'
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>

          {/* Performance Audit History */}
          <div className="dark-card p-6 space-y-4">
            <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center space-x-2">
              <Clock className="w-4 h-4 text-[#F5A623]" />
              <span>Performance Evaluation Audit Log</span>
            </h3>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-[#1A1D24] text-gray-400 uppercase text-[10px]">
                  <tr>
                    <th className="p-3">Run ID</th>
                    <th className="p-3">Timestamp</th>
                    <th className="p-3">Model Version</th>
                    <th className="p-3">Health Status</th>
                    <th className="p-3">Precision</th>
                    <th className="p-3">Recall</th>
                    <th className="p-3">F1 Score</th>
                    <th className="p-3">ROC-AUC</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#272B36]">
                  {(perfHistoryData || []).map((h) => (
                    <tr key={h.performance_id} className="hover:bg-[#1A1D24]/50 transition">
                      <td className="p-3 font-mono font-bold text-white">{h.performance_id}</td>
                      <td className="p-3 text-gray-400">{new Date(h.timestamp).toLocaleString()}</td>
                      <td className="p-3 font-mono text-[#F5A623]">{h.model_version}</td>
                      <td className="p-3">
                        <StatusBadge status={h.status} size="sm" />
                      </td>
                      <td className="p-3 font-mono text-gray-300">{(h.precision * 100).toFixed(1)}%</td>
                      <td className="p-3 font-mono text-gray-300">{(h.recall * 100).toFixed(1)}%</td>
                      <td className="p-3 font-mono font-bold text-white">{(h.f1 * 100).toFixed(1)}%</td>
                      <td className="p-3 font-mono text-blue-400">{(h.roc_auc * 100).toFixed(1)}%</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* TAB 2: DATA DRIFT INTELLIGENCE (TASK 8) */}
      {activeTab === 'drift' && (
        <div className="space-y-8">
          {/* 5 KPI Cards Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
            <div className="dark-card p-5 space-y-2 border-[#272B36]">
              <span className="text-xs font-semibold text-gray-400">Drift Status</span>
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
        </div>
      )}

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
