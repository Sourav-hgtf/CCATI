import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { CustomerListItem } from '../../types';
import { StatusBadge } from '../common/StatusBadge';
import { Search, Download, ChevronLeft, ChevronRight, Eye } from 'lucide-react';

interface HighRiskTableProps {
  customers: CustomerListItem[];
  total: number;
  page: number;
  pageSize: number;
  onPageChange: (newPage: number) => void;
  onSearchChange: (search: string) => void;
  onRiskFilterChange: (tier: string) => void;
  selectedRisk: string;
}

export const HighRiskTable: React.FC<HighRiskTableProps> = ({
  customers,
  total,
  page,
  pageSize,
  onPageChange,
  onSearchChange,
  onRiskFilterChange,
  selectedRisk,
}) => {
  const navigate = useNavigate();
  const [searchTerm, setSearchTerm] = useState('');

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSearchChange(searchTerm);
  };

  const totalPages = Math.ceil(total / pageSize) || 1;

  return (
    <div className="dark-card p-6 space-y-4">
      {/* Header & Controls */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-base font-bold text-white tracking-tight">High-Risk Customer Target Roster</h2>
          <p className="text-xs text-gray-400 mt-0.5">Subscribers prioritized by ML churn probability and financial impact.</p>
        </div>

        <div className="flex flex-wrap items-center gap-3 w-full sm:w-auto">
          {/* Search Input */}
          <form onSubmit={handleSearchSubmit} className="relative flex-1 sm:w-64">
            <Search className="w-3.5 h-3.5 absolute left-3 top-2.5 text-gray-500" />
            <input
              type="text"
              placeholder="Search Customer ID..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full bg-surfaceElevated border border-border rounded-lg pl-9 pr-3 py-1.5 text-xs text-white placeholder-gray-500 focus:outline-none focus:border-primary transition"
            />
          </form>

          {/* Risk Tier Filter */}
          <select
            value={selectedRisk}
            onChange={(e) => onRiskFilterChange(e.target.value)}
            className="bg-surfaceElevated border border-border text-xs text-gray-300 rounded-lg px-3 py-1.5 focus:outline-none focus:border-primary transition"
          >
            <option value="All">All Risk Tiers</option>
            <option value="Critical">Critical Risk</option>
            <option value="High">High Risk</option>
            <option value="Medium">Medium Risk</option>
            <option value="Low">Low Risk</option>
          </select>

          {/* Export CSV Button */}
          <a
            href="/api/v1/export/customers"
            download
            className="bg-surfaceElevated hover:bg-surfaceHover border border-border text-xs font-semibold text-gray-300 hover:text-white px-3 py-1.5 rounded-lg flex items-center space-x-1.5 transition"
          >
            <Download className="w-3.5 h-3.5" />
            <span className="hidden md:inline">Export CSV</span>
          </a>
        </div>
      </div>

      {/* Table Container */}
      <div className="table-responsive border border-border/80 rounded-lg overflow-hidden">
        <table className="w-full text-left text-xs text-gray-300">
          <thead className="bg-[#0e1422] text-gray-400 font-semibold border-b border-border uppercase tracking-wider text-[10px]">
            <tr>
              <th className="py-3 px-4">Customer ID</th>
              <th className="py-3 px-4">Churn Prob</th>
              <th className="py-3 px-4">Risk Tier</th>
              <th className="py-3 px-4">Monthly Fee</th>
              <th className="py-3 px-4">Tenure</th>
              <th className="py-3 px-4">Usage Drop</th>
              <th className="py-3 px-4">Support Calls</th>
              <th className="py-3 px-4">Priority Score</th>
              <th className="py-3 px-4">Action Strategy</th>
              <th className="py-3 px-4 text-right">View</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border/60 bg-surface">
            {customers.map((cust) => {
              const churnPct = (cust.churn_probability * 100).toFixed(1);
              const dropPct = (cust.usage_drop_call_pct * 100).toFixed(0);

              return (
                <tr
                  key={cust.customer_id}
                  onClick={() => navigate(`/customers/${cust.customer_id}`)}
                  className="hover:bg-surfaceHover cursor-pointer transition"
                >
                  <td className="py-3 px-4 font-mono font-bold text-white">{cust.customer_id}</td>
                  <td className="py-3 px-4 font-semibold text-red-400">{churnPct}%</td>
                  <td className="py-3 px-4">
                    <StatusBadge status={cust.risk_tier} size="sm" />
                  </td>
                  <td className="py-3 px-4 font-medium text-gray-200">₹{cust.monthly_charges}</td>
                  <td className="py-3 px-4">{cust.tenure_months} mos</td>
                  <td className="py-3 px-4 font-semibold text-amber-400">-{dropPct}%</td>
                  <td className="py-3 px-4">{cust.support_calls_m1} calls</td>
                  <td className="py-3 px-4 font-bold text-primary">{cust.priority_score.toFixed(0)}</td>
                  <td className="py-3 px-4 text-gray-300 truncate max-w-xs">{cust.recommended_action}</td>
                  <td className="py-3 px-4 text-right">
                    <button className="p-1 text-gray-400 hover:text-white rounded hover:bg-surfaceElevated transition">
                      <Eye className="w-4 h-4" />
                    </button>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Pagination Footer */}
      <div className="flex items-center justify-between pt-2 text-xs text-gray-400">
        <div>
          Showing page <strong className="text-white">{page}</strong> of <strong className="text-white">{totalPages}</strong> ({total} total subscribers)
        </div>

        <div className="flex items-center space-x-2">
          <button
            disabled={page <= 1}
            onClick={() => onPageChange(page - 1)}
            className="p-1.5 rounded-lg border border-border bg-surfaceElevated hover:bg-surfaceHover text-gray-300 disabled:opacity-40 disabled:cursor-not-allowed transition"
          >
            <ChevronLeft className="w-4 h-4" />
          </button>
          <button
            disabled={page >= totalPages}
            onClick={() => onPageChange(page + 1)}
            className="p-1.5 rounded-lg border border-border bg-surfaceElevated hover:bg-surfaceHover text-gray-300 disabled:opacity-40 disabled:cursor-not-allowed transition"
          >
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
};
