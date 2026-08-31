import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { getOverviewMetrics, getChurnTrend, getRiskDistribution } from '../api/analytics';
import { getCustomers } from '../api/customers';
import { MetricCard } from '../components/common/MetricCard';
import { InsightCard } from '../components/common/InsightCard';
import { RiskDistribution } from '../components/dashboard/RiskDistribution';
import { ChurnTrend } from '../components/dashboard/ChurnTrend';
import { HighRiskTable } from '../components/dashboard/HighRiskTable';
import { Users, TrendingDown, DollarSign, AlertTriangle, ShieldCheck, Award } from 'lucide-react';

export const Overview: React.FC = () => {
  const [dateRange, setDateRange] = useState('30d');
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [riskTier, setRiskTier] = useState('All');

  const { data: metrics, isLoading: loadingMetrics } = useQuery({
    queryKey: ['overview-metrics', dateRange],
    queryFn: () => getOverviewMetrics(dateRange),
  });

  const { data: trendData } = useQuery({
    queryKey: ['churn-trend'],
    queryFn: () => getChurnTrend(),
  });

  const { data: distData } = useQuery({
    queryKey: ['risk-dist'],
    queryFn: () => getRiskDistribution(),
  });

  const { data: customersData, isLoading: loadingCustomers } = useQuery({
    queryKey: ['customers-list', page, search, riskTier],
    queryFn: () => getCustomers({ page, page_size: 10, search, risk_tier: riskTier }),
  });

  if (loadingMetrics || !metrics) {
    return (
      <div className="p-12 text-center text-gray-400 animate-pulse">
        Loading Executive Churn Intelligence Overview...
      </div>
    );
  }

  return (
    <div className="p-8 space-y-8">
      {/* Date Range Selector Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white">Executive Retention Overview</h1>
          <p className="text-xs text-gray-400 mt-1">AI-powered customer churn intelligence and retention optimization command center.</p>
        </div>

        <div className="flex bg-surface p-1 rounded-lg border border-border text-xs font-medium">
          {['Today', '7 Days', '30 Days', '90 Days'].map((range) => {
            const key = range.toLowerCase().replace(' ', '');
            return (
              <button
                key={range}
                onClick={() => setDateRange(key)}
                className={`px-3 py-1.5 rounded-md transition ${
                  dateRange === key ? 'bg-primary text-white font-semibold shadow' : 'text-gray-400 hover:text-white'
                }`}
              >
                {range}
              </button>
            );
          })}
        </div>
      </div>

      {/* 6 KPI Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
        <MetricCard
          label="Active Customers"
          value={metrics.active_customers.toLocaleString()}
          change={metrics.active_customers_change}
          icon={Users}
          variant="secondary"
        />
        <MetricCard
          label="Churn Rate"
          value={`${metrics.churn_rate}%`}
          change={metrics.churn_rate_change}
          icon={TrendingDown}
          variant="danger"
        />
        <MetricCard
          label="Revenue at Risk"
          value={`$${metrics.revenue_at_risk.toLocaleString()}`}
          change={metrics.revenue_at_risk_change}
          icon={DollarSign}
          variant="warning"
        />
        <MetricCard
          label="High-Risk Customers"
          value={metrics.high_risk_customers.toLocaleString()}
          change={metrics.high_risk_customers_change}
          icon={AlertTriangle}
          variant="danger"
        />
        <MetricCard
          label="Customers Saved"
          value={metrics.customers_saved.toLocaleString()}
          change={metrics.customers_saved_change}
          icon={ShieldCheck}
          variant="success"
        />
        <MetricCard
          label="Retention ROI"
          value={`${metrics.retention_roi}x`}
          change={metrics.retention_roi_change}
          icon={Award}
          variant="primary"
        />
      </div>

      {/* AI Executive Insight Card */}
      <InsightCard />

      {/* Analytics Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <RiskDistribution data={distData || []} />
        <ChurnTrend data={trendData || []} />
      </div>

      {/* High-Risk Customer Table */}
      <HighRiskTable
        customers={customersData?.items || []}
        total={customersData?.total || 0}
        page={page}
        pageSize={10}
        onPageChange={setPage}
        onSearchChange={setSearch}
        onRiskFilterChange={setRiskTier}
        selectedRisk={riskTier}
      />
    </div>
  );
};
