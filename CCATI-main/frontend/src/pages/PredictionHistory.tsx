import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { getPredictionHistory } from '../api/predictions';
import { History, Search, Filter, Calendar, ShieldCheck, Cpu, ArrowLeftRight } from 'lucide-react';

interface PredictionHistoryProps {
  currentRole: string;
}

export const PredictionHistoryPage: React.FC<PredictionHistoryProps> = ({ currentRole }) => {
  const [page, setPage] = useState(1);
  const [pageSize] = useState(15);
  const [riskTier, setRiskTier] = useState<string>('');
  const [searchId, setSearchId] = useState<string>('');

  const { data, isLoading, refetch } = useQuery({
    queryKey: ['prediction-history', page, pageSize, riskTier, searchId],
    queryFn: () => getPredictionHistory(page, pageSize, riskTier || undefined, searchId || undefined),
  });

  return (
    <div className="p-8 space-y-8 max-w-7xl mx-auto">
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center space-x-2">
            <History className="w-6 h-6 text-amber-400" />
            <span>Persistent Prediction History Log</span>
          </h1>
          <p className="text-sm text-gray-400 mt-1">
            Auditable, immutable snapshots of production inference predictions, probabilities, and model versions.
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <div className="relative">
            <Search className="w-4 h-4 text-gray-400 absolute left-3 top-3" />
            <input
              type="text"
              placeholder="Search Customer ID..."
              value={searchId}
              onChange={(e) => {
                setSearchId(e.target.value);
                setPage(1);
              }}
              className="bg-surface border border-border rounded-xl pl-9 pr-4 py-2 text-sm text-white focus:outline-none focus:border-blue-500 w-64"
            />
          </div>

          <div className="relative">
            <Filter className="w-4 h-4 text-gray-400 absolute left-3 top-3" />
            <select
              value={riskTier}
              onChange={(e) => {
                setRiskTier(e.target.value);
                setPage(1);
              }}
              className="bg-surface border border-border rounded-xl pl-9 pr-4 py-2 text-sm text-white focus:outline-none focus:border-blue-500 appearance-none"
            >
              <option value="">All Risk Tiers</option>
              <option value="Critical">Critical Risk</option>
              <option value="High">High Risk</option>
              <option value="Medium">Medium Risk</option>
              <option value="Low">Low Risk</option>
            </select>
          </div>
        </div>
      </div>

      {/* History Table */}
      <div className="bg-surface border border-border rounded-xl shadow-lg overflow-hidden">
        {isLoading ? (
          <div className="p-12 text-center text-gray-400">Loading prediction history records...</div>
        ) : !data || data.items.length === 0 ? (
          <div className="p-12 text-center space-y-3">
            <History className="w-10 h-10 text-gray-600 mx-auto" />
            <p className="text-gray-300 font-semibold">No persistent prediction history records found.</p>
            <p className="text-xs text-gray-500">Generate a prediction in the Real-time Workspace to create persistent audit logs.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-gray-300">
              <thead className="bg-background text-gray-400 uppercase text-xs">
                <tr>
                  <th className="p-4">Prediction ID</th>
                  <th className="p-4">Customer ID</th>
                  <th className="p-4">Timestamp</th>
                  <th className="p-4">Probability</th>
                  <th className="p-4">Risk Tier</th>
                  <th className="p-4">Certainty</th>
                  <th className="p-4">Model & Version</th>
                  <th className="p-4">Recommendation</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border font-mono text-xs">
                {data.items.map((item) => (
                  <tr key={item.prediction_id} className="hover:bg-gray-800/40 transition">
                    <td className="p-4 font-bold text-blue-400">{item.prediction_id}</td>
                    <td className="p-4 font-bold text-white">{item.customer_id}</td>
                    <td className="p-4 text-gray-400">
                      {new Date(item.prediction_timestamp).toLocaleString()}
                    </td>
                    <td className="p-4 font-extrabold text-white">
                      {(item.churn_probability * 100).toFixed(1)}%
                    </td>
                    <td className="p-4">
                      <span
                        className={`px-2.5 py-1 rounded-full text-xs font-bold font-sans ${
                          item.risk_tier === 'Critical' || item.risk_tier === 'High'
                            ? 'bg-red-500/20 text-red-400 border border-red-500/30'
                            : item.risk_tier === 'Medium'
                            ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                            : 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                        }`}
                      >
                        {item.risk_tier}
                      </span>
                    </td>
                    <td className="p-4 font-bold text-gray-200 font-sans">
                      {(item.confidence_score * 100).toFixed(0)}%
                    </td>
                    <td className="p-4 text-gray-400 font-sans flex items-center space-x-1 mt-1">
                      <Cpu className="w-3.5 h-3.5 text-amber-400" />
                      <span>{item.model_name} ({item.model_version})</span>
                    </td>
                    <td className="p-4 text-gray-300 font-sans">
                      {item.recommended_action || 'Standard Retention'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>

            {/* Pagination Controls */}
            <div className="p-4 bg-background border-t border-border flex items-center justify-between text-xs text-gray-400 font-sans">
              <div>
                Showing page <span className="font-bold text-white">{data.page}</span> of{' '}
                <span className="font-bold text-white">{data.total_pages}</span> ({data.total} total records)
              </div>

              <div className="flex items-center space-x-2">
                <button
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={data.page <= 1}
                  className="px-3 py-1.5 bg-surface border border-border rounded-lg hover:bg-gray-800 disabled:opacity-40 transition font-semibold"
                >
                  Previous
                </button>
                <button
                  onClick={() => setPage((p) => Math.min(data.total_pages, p + 1))}
                  disabled={data.page >= data.total_pages}
                  className="px-3 py-1.5 bg-surface border border-border rounded-lg hover:bg-gray-800 disabled:opacity-40 transition font-semibold"
                >
                  Next
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
