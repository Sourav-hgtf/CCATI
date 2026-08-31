import React, { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { fetchApi } from '../lib/apiClient';
import { CustomerDetailResponse } from '../types/api';
import { Eye, CheckCircle, ArrowLeft, AlertCircle, Phone, Mail, Award, DollarSign } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts';

interface CustomerDetailProps {
  currentRole: string;
}

export const CustomerDetail: React.FC<CustomerDetailProps> = ({ currentRole }) => {
  const { id } = useParams<{ id: string }>();
  const [revealPII, setRevealPII] = useState(false);
  const queryClient = useQueryClient();

  const { data, isLoading } = useQuery<CustomerDetailResponse>({
    queryKey: ['customer-detail', id, revealPII],
    queryFn: () => fetchApi<CustomerDetailResponse>(`/customers/${id}?reveal_pii=${revealPII}`),
  });

  const actionMutation = useMutation({
    mutationFn: () => fetchApi(`/customers/${id}/action`, { method: 'POST' }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['customer-detail', id] });
    },
  });

  if (isLoading || !data) {
    return <div className="p-12 text-center text-gray-400">Loading customer profile...</div>;
  }

  const canReveal = ['RetentionManager', 'Admin'].includes(currentRole);

  const shapChartData = data.top_shap_features.map((f) => ({
    feature: f.feature,
    importance: f.importance,
    color: f.importance > 0 ? '#ef4444' : '#10b981',
  }));

  return (
    <div className="p-8 space-y-8 max-w-7xl mx-auto">
      <Link to="/customers" className="inline-flex items-center space-x-2 text-sm text-gray-400 hover:text-white mb-2">
        <ArrowLeft className="w-4 h-4" />
        <span>Back to Customer List</span>
      </Link>

      {/* Profile Header */}
      <div className="bg-surface border border-border rounded-xl p-6 shadow-lg flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
        <div className="space-y-2">
          <div className="flex items-center space-x-3">
            <h1 className="text-2xl font-bold font-mono text-blue-400">{data.customer_id}</h1>
            <span
              className={`px-3 py-1 rounded-full text-xs font-bold ${
                data.risk_tier === 'High'
                  ? 'bg-red-500/20 text-red-400 border border-red-500/30'
                  : 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
              }`}
            >
              {data.risk_tier} Risk ({ (data.churn_probability * 100).toFixed(1) }%)
            </span>
          </div>

          <div className="flex flex-wrap items-center gap-4 text-sm text-gray-300">
            <div className="flex items-center space-x-1.5">
              <span className="font-semibold text-white">{data.name}</span>
            </div>
            <span>•</span>
            <div className="flex items-center space-x-1 text-gray-400">
              <Phone className="w-3.5 h-3.5" />
              <span>{data.phone}</span>
            </div>
            <span>•</span>
            <div className="flex items-center space-x-1 text-gray-400">
              <Mail className="w-3.5 h-3.5" />
              <span>{data.email}</span>
            </div>
          </div>
        </div>

        <div className="flex items-center space-x-4">
          {!data.is_pii_revealed && canReveal && (
            <button
              onClick={() => setRevealPII(true)}
              className="flex items-center space-x-2 bg-gray-800 hover:bg-gray-700 text-gray-200 text-sm font-semibold px-4 py-2 rounded-lg border border-border shadow-md transition"
            >
              <Eye className="w-4 h-4 text-blue-400" />
              <span>Reveal Unmasked PII</span>
            </button>
          )}

          <div className="bg-background border border-border px-4 py-2 rounded-lg text-right">
            <div className="text-xs text-gray-400 font-semibold uppercase">Composite Priority</div>
            <div className="text-2xl font-extrabold text-white">{data.priority_score}</div>
          </div>
        </div>
      </div>

      {/* Grid Specs */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* SHAP Explanation Card */}
        <div className="bg-surface border border-border rounded-xl p-6 shadow-lg space-y-4">
          <div>
            <h2 className="text-lg font-bold text-white">Model Prediction Explanation (SHAP)</h2>
            <p className="text-xs text-gray-400">Top feature attributions driving churn prediction for this subscriber.</p>
          </div>

          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart layout="vertical" data={shapChartData} margin={{ left: 40, right: 20 }}>
                <XAxis type="number" stroke="#9ca3af" fontSize={11} />
                <YAxis dataKey="feature" type="category" stroke="#9ca3af" fontSize={11} width={130} />
                <Tooltip contentStyle={{ backgroundColor: '#111827', borderColor: '#374151' }} />
                <Bar dataKey="importance" radius={[0, 4, 4, 0]}>
                  {shapChartData.map((entry, idx) => (
                    <Cell key={idx} fill={entry.color} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
          <div className="flex items-center space-x-4 text-xs text-gray-400 pt-2">
            <span className="flex items-center space-x-1">
              <span className="w-3 h-3 rounded-full bg-red-500"></span>
              <span>Pushes toward Churn</span>
            </span>
            <span className="flex items-center space-x-1">
              <span className="w-3 h-3 rounded-full bg-emerald-500"></span>
              <span>Pushes toward Retention</span>
            </span>
          </div>
        </div>

        {/* Recommendation & ROI Action Card */}
        <div className="bg-surface border border-border rounded-xl p-6 shadow-lg flex flex-col justify-between space-y-6">
          <div>
            <div className="flex items-center space-x-2 mb-2">
              <Award className="w-5 h-5 text-amber-400" />
              <h2 className="text-lg font-bold text-white">Recommended Retention Strategy</h2>
            </div>
            <p className="text-xs text-gray-400">Generated by Business Decision Engine based on risk & CLV profile.</p>

            <div className="mt-4 p-4 bg-background border border-border rounded-xl space-y-3">
              <div className="text-base font-bold text-blue-400">{data.recommendation.action_name}</div>
              <p className="text-sm text-gray-300">{data.recommendation.description}</p>
            </div>

            <div className="grid grid-cols-3 gap-3 mt-4 text-center">
              <div className="p-3 bg-background border border-border rounded-lg">
                <div className="text-xs text-gray-400 font-medium">Action Cost</div>
                <div className="text-sm font-bold text-gray-200 mt-1">₹{data.recommendation.roi_details.action_cost}</div>
              </div>
              <div className="p-3 bg-background border border-border rounded-lg">
                <div className="text-xs text-gray-400 font-medium">Exp. Saved Revenue</div>
                <div className="text-sm font-bold text-emerald-400 mt-1">₹{data.recommendation.roi_details.expected_saved_revenue}</div>
              </div>
              <div className="p-3 bg-background border border-border rounded-lg">
                <div className="text-xs text-gray-400 font-medium">Est. Net ROI</div>
                <div className="text-sm font-bold text-amber-400 mt-1">{data.recommendation.roi_details.roi_pct}%</div>
              </div>
            </div>
          </div>

          <div>
            {data.recommendation.actioned ? (
              <div className="flex items-center justify-center space-x-2 p-3 bg-emerald-500/10 border border-emerald-500/30 rounded-xl text-emerald-400 font-semibold text-sm">
                <CheckCircle className="w-5 h-5" />
                <span>Retention Action Marked as Executed ({new Date(data.recommendation.actioned_at || '').toLocaleDateString()})</span>
              </div>
            ) : (
              <button
                onClick={() => actionMutation.mutate()}
                disabled={actionMutation.isPending || !['RetentionManager', 'Admin'].includes(currentRole)}
                className="w-full bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white font-bold py-3 rounded-xl shadow-lg shadow-emerald-600/20 transition flex items-center justify-center space-x-2"
              >
                <CheckCircle className="w-5 h-5" />
                <span>Mark Action as Taken</span>
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
