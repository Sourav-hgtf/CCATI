import React, { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { fetchApi } from '../lib/apiClient';
import { ModelMetricsResponse } from '../types/api';
import { Play, Activity, CheckCircle2, AlertTriangle, RefreshCw } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, Legend } from 'recharts';

interface ModelMonitoringProps {
  currentRole: string;
}

export const ModelMonitoring: React.FC<ModelMonitoringProps> = ({ currentRole }) => {
  const [jobTriggered, setJobTriggered] = useState(false);

  const { data, isLoading, refetch } = useQuery<ModelMetricsResponse>({
    queryKey: ['model-metrics'],
    queryFn: () => fetchApi<ModelMetricsResponse>('/models/metrics'),
  });

  const triggerJobMutation = useMutation({
    mutationFn: () => fetchApi('/scoring-jobs', { method: 'POST', body: JSON.stringify({ job_type: 'BATCH_SCORING', force_ingestion: true }) }),
    onSuccess: () => {
      setJobTriggered(true);
      setTimeout(() => {
        setJobTriggered(false);
        refetch();
      }, 3000);
    },
  });

  if (isLoading || !data) {
    return <div className="p-12 text-center text-gray-400">Loading model performance metrics...</div>;
  }

  const latestRun = data.history[0] || {
    precision: 0.76,
    recall: 0.80,
    f1: 0.78,
    roc_auc: 0.85,
    pr_auc: 0.68,
    confusion_matrix: { tn: 850, fp: 50, fn: 40, tp: 160 },
  };

  const chartData = data.history.map((h, i) => ({
    run: `Run ${data.history.length - i}`,
    Precision: h.precision,
    Recall: h.recall,
    F1: h.f1,
    'PR-AUC': h.pr_auc,
  }));

  const canTrigger = ['Admin', 'Analyst'].includes(currentRole);

  return (
    <div className="p-8 space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white">Model Health & Drift Monitoring</h1>
          <p className="text-sm text-gray-400 mt-1">Classification performance over time, confusion matrix, and feature drift indicators.</p>
        </div>

        {canTrigger && (
          <button
            onClick={() => triggerJobMutation.mutate()}
            disabled={triggerJobMutation.isPending || jobTriggered}
            className="flex items-center space-x-2 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white font-bold px-4 py-2 rounded-lg shadow-lg shadow-emerald-600/20 transition"
          >
            <Play className="w-4 h-4 fill-current" />
            <span>{jobTriggered ? 'Scoring Job Triggered...' : 'Trigger Batch Scoring Job'}</span>
          </button>
        )}
      </div>

      {jobTriggered && (
        <div className="p-4 bg-emerald-500/10 border border-emerald-500/30 rounded-xl text-emerald-400 text-sm flex items-center space-x-2">
          <RefreshCw className="w-4 h-4 animate-spin" />
          <span>Batch scoring job queued in background. Updating model predictions...</span>
        </div>
      )}

      {/* Metrics Over Time Chart */}
      <div className="bg-surface border border-border rounded-xl p-6 shadow-lg">
        <h2 className="text-lg font-bold text-white mb-4">Performance Metrics History (Precision, Recall, PR-AUC)</h2>
        <div className="h-72">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartData}>
              <XAxis dataKey="run" stroke="#9ca3af" fontSize={12} />
              <YAxis stroke="#9ca3af" fontSize={12} domain={[0.4, 1.0]} />
              <Tooltip contentStyle={{ backgroundColor: '#111827', borderColor: '#374151' }} />
              <Legend />
              <Line type="monotone" dataKey="Precision" stroke="#3b82f6" strokeWidth={2.5} />
              <Line type="monotone" dataKey="Recall" stroke="#10b981" strokeWidth={2.5} />
              <Line type="monotone" dataKey="PR-AUC" stroke="#f59e0b" strokeWidth={2.5} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Grid: Confusion Matrix & Drift Table */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Confusion Matrix Card */}
        <div className="bg-surface border border-border rounded-xl p-6 shadow-lg space-y-4">
          <h2 className="text-lg font-bold text-white">Active Model Confusion Matrix</h2>
          <p className="text-xs text-gray-400">Promoted Model: {data.promoted_model_name} ({data.current_model_version})</p>

          <div className="grid grid-cols-2 gap-4 pt-2">
            <div className="bg-background border border-border p-4 rounded-xl text-center">
              <div className="text-xs text-gray-400 font-semibold">True Negatives (TN)</div>
              <div className="text-2xl font-extrabold text-gray-200 mt-1">{latestRun.confusion_matrix.tn}</div>
            </div>
            <div className="bg-background border border-border p-4 rounded-xl text-center">
              <div className="text-xs text-gray-400 font-semibold">False Positives (FP)</div>
              <div className="text-2xl font-extrabold text-amber-400 mt-1">{latestRun.confusion_matrix.fp}</div>
            </div>
            <div className="bg-background border border-border p-4 rounded-xl text-center">
              <div className="text-xs text-gray-400 font-semibold">False Negatives (FN)</div>
              <div className="text-2xl font-extrabold text-red-400 mt-1">{latestRun.confusion_matrix.fn}</div>
            </div>
            <div className="bg-background border border-border p-4 rounded-xl text-center">
              <div className="text-xs text-gray-400 font-semibold">True Positives (TP)</div>
              <div className="text-2xl font-extrabold text-emerald-400 mt-1">{latestRun.confusion_matrix.tp}</div>
            </div>
          </div>
        </div>

        {/* Feature Drift Indicators Card */}
        <div className="bg-surface border border-border rounded-xl p-6 shadow-lg space-y-4">
          <h2 className="text-lg font-bold text-white">Data & Feature Drift Indicators</h2>
          <p className="text-xs text-gray-400">Comparing current scoring population distribution against training baseline.</p>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-gray-300">
              <thead className="bg-background text-gray-400 uppercase text-xs">
                <tr>
                  <th className="p-3">Feature</th>
                  <th className="p-3">Baseline</th>
                  <th className="p-3">Current</th>
                  <th className="p-3">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {data.drift_report.map((item) => (
                  <tr key={item.feature_name}>
                    <td className="p-3 font-mono text-xs text-blue-400">{item.feature_name}</td>
                    <td className="p-3 font-mono">{item.baseline_mean}</td>
                    <td className="p-3 font-mono">{item.current_mean}</td>
                    <td className="p-3">
                      <span
                        className={`px-2 py-0.5 rounded-full text-xs font-bold ${
                          item.status === 'DRIFTING'
                            ? 'bg-red-500/20 text-red-400 border border-red-500/30'
                            : 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                        }`}
                      >
                        {item.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
};
