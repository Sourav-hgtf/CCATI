import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { fetchApi } from '../lib/apiClient';
import { CustomerPaginatedResponse } from '../types/api';
import { Search, Download, Filter, ChevronLeft, ChevronRight } from 'lucide-react';
import { Link } from 'react-router-dom';

interface CustomersPageProps {
  currentRole: string;
}

export const Customers: React.FC<CustomersPageProps> = ({ currentRole }) => {
  const [page, setPage] = useState(1);
  const [riskFilter, setRiskFilter] = useState<string>('');
  const [planFilter, setPlanFilter] = useState<string>('');
  const [search, setSearch] = useState<string>('');

  const { data, isLoading, refetch } = useQuery<CustomerPaginatedResponse>({
    queryKey: ['customers', page, riskFilter, planFilter, search],
    queryFn: () => {
      const params = new URLSearchParams({
        page: page.toString(),
        page_size: '15',
        ...(riskFilter ? { risk_tier: riskFilter } : {}),
        ...(planFilter ? { plan_tier: planFilter } : {}),
        ...(search ? { search } : {}),
      });
      return fetchApi<CustomerPaginatedResponse>(`/customers?${params.toString()}`);
    },
  });

  const handleExport = () => {
    const params = new URLSearchParams({
      ...(riskFilter ? { risk_tier: riskFilter } : {}),
      ...(planFilter ? { plan_tier: planFilter } : {}),
    });
    const token = localStorage.getItem('auth_token') || '';
    window.open(`/api/v1/export/customers?${params.toString()}`, '_blank');
  };

  const canExport = ['RetentionManager', 'Admin'].includes(currentRole);

  return (
    <div className="p-8 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white">At-Risk Subscriber Management</h1>
          <p className="text-sm text-gray-400 mt-1">Sortable, filterable subscriber list ranked by composite priority score.</p>
        </div>

        {canExport ? (
          <button
            onClick={handleExport}
            className="flex items-center space-x-2 bg-blue-600 hover:bg-blue-500 text-white font-semibold text-sm px-4 py-2 rounded-lg shadow-lg shadow-blue-600/20 transition"
          >
            <Download className="w-4 h-4" />
            <span>Export CSV</span>
          </button>
        ) : (
          <div className="text-xs text-gray-500 italic">Export CSV restricted to Retention Managers/Admins</div>
        )}
      </div>

      {/* Filter and Search Bar */}
      <div className="bg-surface border border-border rounded-xl p-4 flex flex-col md:flex-row items-center justify-between gap-4">
        <div className="relative w-full md:w-80">
          <Search className="w-4 h-4 absolute left-3 top-3 text-gray-400" />
          <input
            type="text"
            placeholder="Search Customer ID..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full bg-background border border-border rounded-lg pl-9 pr-4 py-2 text-sm text-white focus:outline-none focus:border-blue-500"
          />
        </div>

        <div className="flex items-center space-x-4 w-full md:w-auto">
          <div className="flex items-center space-x-2">
            <Filter className="w-4 h-4 text-gray-400" />
            <select
              value={riskFilter}
              onChange={(e) => { setRiskFilter(e.target.value); setPage(1); }}
              className="bg-background border border-border text-sm text-gray-200 rounded-lg px-3 py-2 focus:outline-none"
            >
              <option value="">All Risk Tiers</option>
              <option value="High">High Risk (&ge;70%)</option>
              <option value="Medium">Medium Risk (35-70%)</option>
              <option value="Low">Low Risk (&lt;35%)</option>
            </select>
          </div>

          <select
            value={planFilter}
            onChange={(e) => { setPlanFilter(e.target.value); setPage(1); }}
            className="bg-background border border-border text-sm text-gray-200 rounded-lg px-3 py-2 focus:outline-none"
          >
            <option value="">All Plan Tiers</option>
            <option value="Prepaid Basic">Prepaid Basic</option>
            <option value="Prepaid Unlimited">Prepaid Unlimited</option>
            <option value="Postpaid Standard">Postpaid Standard</option>
            <option value="Postpaid Premium">Postpaid Premium</option>
          </select>
        </div>
      </div>

      {/* Main Customer Table */}
      <div className="bg-surface border border-border rounded-xl shadow-lg overflow-hidden">
        {isLoading ? (
          <div className="p-12 text-center text-gray-400">Loading subscribers...</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-gray-300">
              <thead className="bg-background text-gray-400 uppercase text-xs">
                <tr>
                  <th className="p-4">Customer ID</th>
                  <th className="p-4">Plan Tier</th>
                  <th className="p-4">Tenure</th>
                  <th className="p-4">Monthly Fee</th>
                  <th className="p-4">Risk Tier</th>
                  <th className="p-4">Churn Prob</th>
                  <th className="p-4">Priority Score</th>
                  <th className="p-4">Call Drop %</th>
                  <th className="p-4">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {data?.items.map((item) => (
                  <tr key={item.customer_id} className="hover:bg-gray-800/50 transition">
                    <td className="p-4 font-mono font-medium text-blue-400">
                      <Link to={`/customers/${item.customer_id}`} className="hover:underline">
                        {item.customer_id}
                      </Link>
                    </td>
                    <td className="p-4">{item.plan_tier}</td>
                    <td className="p-4">{item.tenure_months} mos</td>
                    <td className="p-4">₹{item.monthly_charges}</td>
                    <td className="p-4">
                      <span
                        className={`px-2.5 py-1 rounded-full text-xs font-bold ${
                          item.risk_tier === 'High'
                            ? 'bg-red-500/20 text-red-400 border border-red-500/30'
                            : item.risk_tier === 'Medium'
                            ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                            : 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                        }`}
                      >
                        {item.risk_tier}
                      </span>
                    </td>
                    <td className="p-4 font-semibold text-gray-200">{(item.churn_probability * 100).toFixed(1)}%</td>
                    <td className="p-4 font-bold text-white">{item.priority_score}</td>
                    <td className="p-4 font-mono text-gray-400">{(item.usage_drop_call_pct * 100).toFixed(0)}%</td>
                    <td className="p-4">
                      <Link
                        to={`/customers/${item.customer_id}`}
                        className="text-xs bg-gray-800 hover:bg-gray-700 text-gray-200 px-3 py-1.5 rounded-md border border-border font-medium"
                      >
                        Inspect
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination Footer */}
        <div className="p-4 bg-background border-t border-border flex items-center justify-between text-sm text-gray-400">
          <div>
            Showing Page <strong className="text-white">{data?.page || 1}</strong> of <strong className="text-white">{data?.total_pages || 1}</strong> ({data?.total || 0} total records)
          </div>
          <div className="flex items-center space-x-2">
            <button
              disabled={page <= 1}
              onClick={() => setPage(page - 1)}
              className="p-2 bg-surface border border-border rounded-lg disabled:opacity-40 hover:bg-gray-800"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <button
              disabled={page >= (data?.total_pages || 1)}
              onClick={() => setPage(page + 1)}
              className="p-2 bg-surface border border-border rounded-lg disabled:opacity-40 hover:bg-gray-800"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
