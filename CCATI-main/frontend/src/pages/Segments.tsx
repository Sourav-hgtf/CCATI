import React, { useState, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { fetchApi } from '../lib/apiClient';
import {
  SegmentOverviewResponse,
  SegmentProfile,
  SegmentDetailResponse,
  SegmentCustomerListResponse,
  SegmentQualityMetrics,
  SegmentRiskMatrixRow,
} from '../types/api';
import ReactECharts from 'echarts-for-react';
import {
  Users,
  TrendingDown,
  ShieldAlert,
  Heart,
  ChevronRight,
  ChevronLeft,
  BarChart3,
  Target,
  Zap,
  AlertTriangle,
  CheckCircle,
  Info,
  Search,
  Filter,
  X,
} from 'lucide-react';
import { Link } from 'react-router-dom';

// ─── Color System ───────────────────────────────────────────────────────────
const CLUSTER_COLORS = ['#ef4444', '#f59e0b', '#3b82f6', '#10b981'];
const RISK_COLORS: Record<string, string> = {
  Low: '#10b981',
  Medium: '#f59e0b',
  High: '#ef4444',
  Critical: '#dc2626',
};

function healthColor(status: string) {
  if (status === 'HEALTHY') return 'text-emerald-400';
  if (status === 'MODERATE_RISK') return 'text-amber-400';
  return 'text-red-400';
}
function healthBg(status: string) {
  if (status === 'HEALTHY') return 'bg-emerald-500/10 border-emerald-500/30';
  if (status === 'MODERATE_RISK') return 'bg-amber-500/10 border-amber-500/30';
  return 'bg-red-500/10 border-red-500/30';
}
function healthLabel(status: string) {
  if (status === 'HEALTHY') return 'Healthy';
  if (status === 'MODERATE_RISK') return 'Moderate Risk';
  return 'Critical Risk';
}

// ─── Sub-components ─────────────────────────────────────────────────────────

/** Stat tile used in segment detail */
function StatTile({ label, value, sub }: { label: string; value: string; sub?: string }) {
  return (
    <div className="bg-gray-800/50 rounded-lg px-4 py-3">
      <div className="text-xs text-gray-400 mb-1">{label}</div>
      <div className="text-lg font-bold text-white">{value}</div>
      {sub && <div className="text-xs text-gray-500 mt-0.5">{sub}</div>}
    </div>
  );
}

/** Inline health badge */
function HealthBadge({ status, score }: { status: string; score: number }) {
  return (
    <span className={`inline-flex items-center gap-1.5 text-xs font-semibold px-2.5 py-1 rounded-full border ${healthBg(status)}`}>
      {status === 'HEALTHY' ? (
        <CheckCircle className={`w-3 h-3 ${healthColor(status)}`} />
      ) : (
        <AlertTriangle className={`w-3 h-3 ${healthColor(status)}`} />
      )}
      <span className={healthColor(status)}>{healthLabel(status)}</span>
      <span className="text-gray-400">({score})</span>
    </span>
  );
}

/** Quality metrics panel */
function QualityPanel({ qm }: { qm: SegmentQualityMetrics }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="bg-surface border border-border rounded-xl p-5">
      <div
        className="flex items-center justify-between cursor-pointer"
        onClick={() => setOpen((o) => !o)}
      >
        <div className="flex items-center gap-2">
          <BarChart3 className="w-4 h-4 text-blue-400" />
          <span className="text-sm font-semibold text-white">Clustering Quality Metrics</span>
          <span className="text-xs text-gray-500">({qm.n_clusters} clusters · {qm.evaluated_subscribers.toLocaleString()} subscribers)</span>
        </div>
        <div className="flex items-center gap-4 text-xs">
          <span className="text-gray-400">Silhouette <span className="font-bold text-blue-300">{qm.silhouette_score.toFixed(3)}</span></span>
          <span className="text-gray-400">D-B <span className="font-bold text-purple-300">{qm.davies_bouldin_index.toFixed(3)}</span></span>
          <span className="text-gray-400">C-H <span className="font-bold text-emerald-300">{qm.calinski_harabasz_index.toFixed(0)}</span></span>
          <ChevronRight className={`w-4 h-4 text-gray-500 transition-transform ${open ? 'rotate-90' : ''}`} />
        </div>
      </div>
      {open && (
        <div className="mt-4 pt-4 border-t border-border space-y-3">
          <div className="grid grid-cols-3 gap-3">
            <div className="bg-blue-500/5 border border-blue-500/20 rounded-lg p-3">
              <div className="text-xs text-gray-400 mb-1">Silhouette Score</div>
              <div className="text-xl font-bold text-blue-300">{qm.silhouette_score.toFixed(3)}</div>
              <div className="text-xs text-gray-500 mt-1">Cluster cohesion vs separation. Higher is better. &gt;0.25 = solid for behavioral data.</div>
            </div>
            <div className="bg-purple-500/5 border border-purple-500/20 rounded-lg p-3">
              <div className="text-xs text-gray-400 mb-1">Davies-Bouldin Index</div>
              <div className="text-xl font-bold text-purple-300">{qm.davies_bouldin_index.toFixed(3)}</div>
              <div className="text-xs text-gray-500 mt-1">Inter-cluster similarity. Lower is better. Measures cluster separation.</div>
            </div>
            <div className="bg-emerald-500/5 border border-emerald-500/20 rounded-lg p-3">
              <div className="text-xs text-gray-400 mb-1">Calinski-Harabasz</div>
              <div className="text-xl font-bold text-emerald-300">{qm.calinski_harabasz_index.toFixed(0)}</div>
              <div className="text-xs text-gray-500 mt-1">Variance ratio score. Higher indicates denser, well-separated clusters.</div>
            </div>
          </div>
          <p className="text-xs text-gray-500 italic">{qm.interpretation}</p>
          <p className="text-xs text-amber-500/80">
            ⚠️ Customer segments describe <strong>behavioral similarity</strong> and should not be interpreted as causal groups.
          </p>
        </div>
      )}
    </div>
  );
}

/** Segment × Risk matrix table */
function RiskMatrix({ matrix }: { matrix: SegmentRiskMatrixRow[] }) {
  return (
    <div className="bg-surface border border-border rounded-xl p-5">
      <div className="flex items-center gap-2 mb-4">
        <ShieldAlert className="w-4 h-4 text-red-400" />
        <h3 className="text-sm font-semibold text-white">Segment × Risk Distribution Matrix</h3>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-xs">
          <thead>
            <tr className="border-b border-border">
              <th className="text-left text-gray-400 pb-2 pr-4 font-medium">Segment</th>
              <th className="text-right text-emerald-400 pb-2 px-3 font-medium">Low Risk</th>
              <th className="text-right text-amber-400 pb-2 px-3 font-medium">Medium Risk</th>
              <th className="text-right text-red-400 pb-2 px-3 font-medium">High Risk</th>
              <th className="text-right text-red-600 pb-2 px-3 font-medium">Critical</th>
              <th className="text-right text-gray-400 pb-2 pl-3 font-medium">Total</th>
              <th className="text-right text-gray-400 pb-2 pl-3 font-medium">High+Critical%</th>
            </tr>
          </thead>
          <tbody>
            {matrix.map((row) => (
              <tr key={row.cluster_id} className="border-b border-border/50 hover:bg-white/[0.02]">
                <td className="py-2.5 pr-4 font-medium text-white">{row.cluster_name}</td>
                <td className="text-right py-2.5 px-3 text-emerald-300">{row.low_risk_count.toLocaleString()}</td>
                <td className="text-right py-2.5 px-3 text-amber-300">{row.medium_risk_count.toLocaleString()}</td>
                <td className="text-right py-2.5 px-3 text-red-300">{row.high_risk_count.toLocaleString()}</td>
                <td className="text-right py-2.5 px-3 text-red-500">{row.critical_risk_count.toLocaleString()}</td>
                <td className="text-right py-2.5 pl-3 text-gray-300">{row.total_count.toLocaleString()}</td>
                <td className="text-right py-2.5 pl-3">
                  <span className={`font-bold ${row.high_critical_ratio > 0.5 ? 'text-red-400' : row.high_critical_ratio > 0.2 ? 'text-amber-400' : 'text-emerald-400'}`}>
                    {(row.high_critical_ratio * 100).toFixed(1)}%
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

/** Segment detail drawer panel */
function SegmentDetailPanel({
  seg,
  segIdx,
  onClose,
}: {
  seg: SegmentProfile;
  segIdx: number;
  onClose: () => void;
}) {
  const [custPage, setCustPage] = useState(1);
  const [riskFilter, setRiskFilter] = useState('');
  const [search, setSearch] = useState('');
  const color = CLUSTER_COLORS[segIdx % CLUSTER_COLORS.length];

  const { data: detail } = useQuery<SegmentDetailResponse>({
    queryKey: ['segment-detail', seg.cluster_id],
    queryFn: () => fetchApi<SegmentDetailResponse>(`/segments/${seg.cluster_id}`),
  });

  const { data: custData, isLoading: custLoading } = useQuery<SegmentCustomerListResponse>({
    queryKey: ['segment-customers', seg.cluster_id, custPage, riskFilter, search],
    queryFn: () => {
      let url = `/segments/${seg.cluster_id}/customers?page=${custPage}&page_size=10`;
      if (riskFilter) url += `&risk_tier=${riskFilter}`;
      if (search) url += `&search=${encodeURIComponent(search)}`;
      return fetchApi<SegmentCustomerListResponse>(url);
    },
  });

  return (
    <div className="fixed inset-0 z-50 flex">
      {/* Backdrop */}
      <div className="flex-1 bg-black/60 backdrop-blur-sm" onClick={onClose} />
      {/* Panel */}
      <div className="w-full max-w-2xl bg-gray-900 border-l border-border overflow-y-auto">
        {/* Header */}
        <div className="sticky top-0 bg-gray-900 border-b border-border px-6 py-4 flex items-center justify-between z-10">
          <div className="flex items-center gap-3">
            <span className="w-3 h-3 rounded-full flex-shrink-0" style={{ backgroundColor: color }} />
            <div>
              <h2 className="text-base font-bold text-white">{seg.cluster_name}</h2>
              <p className="text-xs text-gray-400">Cluster {seg.cluster_id} · {seg.size.toLocaleString()} subscribers ({seg.percentage}%)</p>
            </div>
          </div>
          <button onClick={onClose} className="p-2 rounded-lg hover:bg-white/5 text-gray-400 hover:text-white">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-6 space-y-6">
          {/* Health & Risk */}
          <div className="flex items-center justify-between">
            <HealthBadge status={seg.health_status} score={seg.health_score} />
            <span className="text-xs text-gray-400 font-medium px-3 py-1 bg-gray-800 rounded-full">{seg.risk_category}</span>
          </div>

          {/* Profile Metrics */}
          <div>
            <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">Customer Characteristics</h3>
            <div className="grid grid-cols-2 gap-2">
              <StatTile label="Avg Tenure" value={`${seg.avg_tenure_months} months`} />
              <StatTile label="Avg Monthly Charges" value={`₹${seg.avg_monthly_charges.toLocaleString()}`} />
              <StatTile label="Avg Total Charges" value={`₹${seg.avg_total_charges.toLocaleString()}`} />
              <StatTile label="Avg Support Calls" value={`${seg.avg_support_calls_m1}`} sub="calls per month" />
              <StatTile label="Avg Call Drop" value={`${(seg.avg_usage_drop_call_pct * 100).toFixed(1)}%`} />
              <StatTile label="Avg Data Drop" value={`${(seg.avg_usage_drop_data_pct * 100).toFixed(1)}%`} />
            </div>
          </div>

          {/* Churn Analysis */}
          <div>
            <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">Churn Analysis</h3>
            <div className="grid grid-cols-3 gap-2">
              <StatTile
                label="Actual Churn Rate"
                value={`${seg.actual_churn_rate.toFixed(1)}%`}
                sub="Ground truth"
              />
              <StatTile
                label="Avg Churn Probability"
                value={`${(seg.avg_churn_probability * 100).toFixed(1)}%`}
                sub="Model prediction"
              />
              <StatTile
                label="High-Risk Customers"
                value={seg.high_risk_count.toLocaleString()}
                sub={`+ ${seg.critical_risk_count} Critical`}
              />
            </div>
          </div>

          {/* Feature Distributions (from detail query) */}
          {detail?.feature_distributions && Object.keys(detail.feature_distributions).length > 0 && (
            <div>
              <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">Feature Distributions (Q25 / Median / Q75)</h3>
              <div className="space-y-2">
                {Object.entries(detail.feature_distributions).map(([feat, dist]: [string, any]) => (
                  <div key={feat} className="flex items-center justify-between text-xs bg-gray-800/50 rounded-lg px-3 py-2">
                    <span className="text-gray-400 capitalize">{feat.replace(/_/g, ' ')}</span>
                    <span className="text-gray-300 font-mono">
                      {dist.q25} / <span className="text-white font-bold">{dist.q50}</span> / {dist.q75}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Risk Breakdown */}
          {detail?.risk_breakdown && Object.keys(detail.risk_breakdown).length > 0 && (
            <div>
              <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">Risk Tier Breakdown</h3>
              <div className="flex gap-2 flex-wrap">
                {Object.entries(detail.risk_breakdown).map(([tier, count]) => (
                  <div key={tier} className="flex items-center gap-2 bg-gray-800/50 rounded-full px-3 py-1.5">
                    <span className="w-2 h-2 rounded-full" style={{ backgroundColor: RISK_COLORS[tier] || '#6b7280' }} />
                    <span className="text-xs text-gray-300">{tier}: <span className="font-bold text-white">{count}</span></span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Business Opportunity */}
          <div>
            <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">Business Opportunity</h3>
            <div className="bg-blue-500/5 border border-blue-500/20 rounded-xl p-4 space-y-2.5">
              <div className="flex justify-between text-sm">
                <span className="text-gray-400">Eligible for Intervention</span>
                <span className="font-bold text-white">{seg.eligible_customers.toLocaleString()} customers</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-400">Estimated Campaign Cost</span>
                <span className="font-bold text-amber-300">₹{seg.estimated_campaign_cost.toLocaleString()}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-400">Retention Opportunity</span>
                <span className="font-bold text-emerald-300">₹{seg.estimated_retention_opportunity.toLocaleString()}</span>
              </div>
              <div className="flex justify-between text-sm border-t border-blue-500/20 pt-2.5">
                <span className="text-gray-400 font-medium">Estimated ROI</span>
                <span className={`font-bold text-lg ${seg.estimated_roi_pct > 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                  {seg.estimated_roi_pct.toFixed(0)}%
                </span>
              </div>
            </div>
          </div>

          {/* Recommended Strategy */}
          <div>
            <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">Recommended Strategy</h3>
            <div className="bg-gray-800/50 border border-border rounded-xl p-4">
              <div className="flex items-start gap-3">
                <Zap className="w-4 h-4 text-amber-400 mt-0.5 flex-shrink-0" />
                <p className="text-sm text-gray-200">{seg.recommended_strategy}</p>
              </div>
            </div>
          </div>

          {/* Customer List */}
          <div>
            <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">
              Customers in Segment
              {custData && <span className="ml-2 text-gray-500 font-normal">({custData.total_customers.toLocaleString()} total)</span>}
            </h3>

            {/* Filters */}
            <div className="flex gap-2 mb-3">
              <div className="relative flex-1">
                <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-gray-500" />
                <input
                  type="text"
                  placeholder="Search ID or name..."
                  value={search}
                  onChange={(e) => { setSearch(e.target.value); setCustPage(1); }}
                  className="w-full bg-gray-800 border border-border rounded-lg text-xs text-white pl-8 pr-3 py-2 placeholder-gray-500 focus:outline-none focus:border-blue-500"
                />
              </div>
              <select
                value={riskFilter}
                onChange={(e) => { setRiskFilter(e.target.value); setCustPage(1); }}
                className="bg-gray-800 border border-border rounded-lg text-xs text-white px-3 py-2 focus:outline-none focus:border-blue-500"
              >
                <option value="">All Risk Tiers</option>
                <option value="Low">Low</option>
                <option value="Medium">Medium</option>
                <option value="High">High</option>
                <option value="Critical">Critical</option>
              </select>
            </div>

            {custLoading ? (
              <div className="text-center text-gray-500 text-xs py-6">Loading customers...</div>
            ) : custData && custData.customers.length > 0 ? (
              <>
                <div className="space-y-1.5">
                  {custData.customers.map((c) => (
                    <Link
                      key={c.customer_id}
                      to={`/customers/${c.customer_id}`}
                      className="flex items-center justify-between bg-gray-800/50 rounded-lg px-3 py-2.5 hover:bg-gray-800 transition group"
                    >
                      <div>
                        <span className="text-xs font-medium text-white group-hover:text-blue-300">{c.name}</span>
                        <span className="text-xs text-gray-500 ml-2">{c.customer_id}</span>
                      </div>
                      <div className="flex items-center gap-3 text-xs">
                        <span className="text-gray-400">₹{c.monthly_charges.toLocaleString()}/mo</span>
                        <span
                          className="font-bold"
                          style={{ color: RISK_COLORS[c.risk_tier] || '#9ca3af' }}
                        >
                          {(c.churn_probability * 100).toFixed(0)}%
                        </span>
                        <ChevronRight className="w-3.5 h-3.5 text-gray-600 group-hover:text-blue-400" />
                      </div>
                    </Link>
                  ))}
                </div>
                {/* Pagination */}
                {custData.total_pages > 1 && (
                  <div className="flex items-center justify-between mt-3 pt-3 border-t border-border">
                    <button
                      disabled={custPage <= 1}
                      onClick={() => setCustPage((p) => p - 1)}
                      className="flex items-center gap-1 text-xs text-gray-400 hover:text-white disabled:opacity-40 disabled:cursor-not-allowed"
                    >
                      <ChevronLeft className="w-3.5 h-3.5" /> Prev
                    </button>
                    <span className="text-xs text-gray-500">Page {custPage}/{custData.total_pages}</span>
                    <button
                      disabled={custPage >= custData.total_pages}
                      onClick={() => setCustPage((p) => p + 1)}
                      className="flex items-center gap-1 text-xs text-gray-400 hover:text-white disabled:opacity-40 disabled:cursor-not-allowed"
                    >
                      Next <ChevronRight className="w-3.5 h-3.5" />
                    </button>
                  </div>
                )}
              </>
            ) : (
              <div className="text-center text-gray-500 text-xs py-6">No customers found with current filters.</div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

// ─── Main Component ──────────────────────────────────────────────────────────
export const Segments: React.FC = () => {
  const [selectedCluster, setSelectedCluster] = useState<number | null>(null);
  const [detailSeg, setDetailSeg] = useState<{ seg: SegmentProfile; idx: number } | null>(null);

  const { data, isLoading, isError } = useQuery<SegmentOverviewResponse>({
    queryKey: ['segments-overview'],
    queryFn: () => fetchApi<SegmentOverviewResponse>('/segments'),
    staleTime: 2 * 60 * 1000,
  });

  // ── Charts ──────────────────────────────────────────────────────────────

  const scatterOption = useMemo(() => {
    if (!data) return {};
    const series = data.segments.map((seg, idx) => ({
      name: seg.cluster_name,
      type: 'scatter',
      symbolSize: selectedCluster === null || selectedCluster === seg.cluster_id ? 9 : 4,
      itemStyle: {
        color: CLUSTER_COLORS[idx % CLUSTER_COLORS.length],
        opacity: selectedCluster === null || selectedCluster === seg.cluster_id ? 0.85 : 0.15,
      },
      data: data.scatter_points
        .filter((p) => p.cluster_id === seg.cluster_id)
        .map((p) => [p.x, p.y, p.customer_id, (p.churn_probability * 100).toFixed(1), p.risk_tier]),
    }));
    return {
      backgroundColor: 'transparent',
      legend: { textStyle: { color: '#9ca3af' }, top: 0, right: 0, itemWidth: 12, itemHeight: 12 },
      grid: { left: '3%', right: '4%', bottom: '3%', top: 32, containLabel: true },
      tooltip: {
        backgroundColor: '#111827',
        borderColor: '#374151',
        textStyle: { color: '#f3f4f6', fontSize: 12 },
        formatter: (params: any) =>
          `<div style="font-weight:700;color:${CLUSTER_COLORS[params.seriesIndex % CLUSTER_COLORS.length]}">${params.seriesName}</div>
           <div>ID: ${params.value[2]}</div>
           <div>Churn: <b style="color:#f87171">${params.value[3]}%</b></div>
           <div>Risk: ${params.value[4]}</div>`,
      },
      xAxis: { type: 'value', splitLine: { lineStyle: { color: '#1f2937' } }, axisLabel: { color: '#6b7280', fontSize: 10 } },
      yAxis: { type: 'value', splitLine: { lineStyle: { color: '#1f2937' } }, axisLabel: { color: '#6b7280', fontSize: 10 } },
      series,
    };
  }, [data, selectedCluster]);

  const churnBarOption = useMemo(() => {
    if (!data) return {};
    return {
      backgroundColor: 'transparent',
      tooltip: { trigger: 'axis', backgroundColor: '#111827', borderColor: '#374151', textStyle: { color: '#f3f4f6' } },
      grid: { left: 16, right: 16, bottom: 48, top: 16, containLabel: true },
      xAxis: {
        type: 'category',
        data: data.segments.map((s) => s.cluster_name),
        axisLabel: { color: '#9ca3af', fontSize: 10, rotate: 20, interval: 0 },
        axisLine: { lineStyle: { color: '#374151' } },
      },
      yAxis: { type: 'value', axisLabel: { color: '#6b7280', fontSize: 10, formatter: '{value}%' }, splitLine: { lineStyle: { color: '#1f2937' } } },
      series: [
        {
          name: 'Actual Churn Rate',
          type: 'bar',
          data: data.segments.map((s, i) => ({ value: s.actual_churn_rate, itemStyle: { color: CLUSTER_COLORS[i % CLUSTER_COLORS.length] } })),
          barMaxWidth: 48,
          label: { show: true, position: 'top', color: '#d1d5db', fontSize: 10, formatter: '{c}%' },
        },
        {
          name: 'Avg Churn Probability',
          type: 'line',
          data: data.segments.map((s) => parseFloat((s.avg_churn_probability * 100).toFixed(1))),
          lineStyle: { color: '#f59e0b', width: 2 },
          itemStyle: { color: '#f59e0b' },
          symbol: 'circle',
          symbolSize: 6,
        },
      ],
    };
  }, [data]);

  const sizeBarOption = useMemo(() => {
    if (!data) return {};
    return {
      backgroundColor: 'transparent',
      tooltip: { trigger: 'axis', backgroundColor: '#111827', borderColor: '#374151', textStyle: { color: '#f3f4f6' } },
      grid: { left: 16, right: 16, bottom: 48, top: 16, containLabel: true },
      xAxis: {
        type: 'category',
        data: data.segments.map((s) => s.cluster_name),
        axisLabel: { color: '#9ca3af', fontSize: 10, rotate: 20, interval: 0 },
        axisLine: { lineStyle: { color: '#374151' } },
      },
      yAxis: { type: 'value', axisLabel: { color: '#6b7280', fontSize: 10 }, splitLine: { lineStyle: { color: '#1f2937' } } },
      series: [
        {
          name: 'Total Customers',
          type: 'bar',
          data: data.segments.map((s, i) => ({ value: s.size, itemStyle: { color: CLUSTER_COLORS[i % CLUSTER_COLORS.length] } })),
          barMaxWidth: 48,
          label: { show: true, position: 'top', color: '#d1d5db', fontSize: 10 },
        },
        {
          name: 'High-Risk Customers',
          type: 'bar',
          data: data.segments.map((s) => ({ value: s.high_risk_count, itemStyle: { color: '#ef444480' } })),
          barMaxWidth: 48,
        },
      ],
    };
  }, [data]);

  // ── Render ───────────────────────────────────────────────────────────────

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center p-20 gap-4">
        <div className="w-10 h-10 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
        <p className="text-gray-400 text-sm">Running K-Means cluster analysis…</p>
      </div>
    );
  }

  if (isError || !data) {
    return (
      <div className="p-12 text-center">
        <AlertTriangle className="w-10 h-10 text-red-400 mx-auto mb-3" />
        <p className="text-gray-400 text-sm">Segment assignment unavailable. Please retry after scoring.</p>
      </div>
    );
  }

  return (
    <div className="p-6 lg:p-8 space-y-6">
      {/* Page Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight">Customer Segment Explorer</h1>
          <p className="text-sm text-gray-400 mt-1">
            K-Means behavioral segmentation · {data.segments.length} segments · {data.segments.reduce((a, s) => a + s.size, 0).toLocaleString()} subscribers
          </p>
        </div>
        {selectedCluster !== null && (
          <button
            onClick={() => setSelectedCluster(null)}
            className="flex items-center gap-1.5 text-xs text-blue-400 hover:text-blue-300 font-medium bg-blue-500/10 border border-blue-500/20 rounded-lg px-3 py-2"
          >
            <Filter className="w-3.5 h-3.5" /> Clear Filter
          </button>
        )}
      </div>

      {/* Macro Insights Banner */}
      {data.macro_insights && (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
          {[
            { icon: ShieldAlert, label: 'Highest Risk Segment', value: data.macro_insights.highest_risk_segment, sub: `${(data.macro_insights.highest_risk_churn_prob * 100).toFixed(0)}% avg churn`, color: 'text-red-400', bg: 'bg-red-500/5 border-red-500/20' },
            { icon: Users, label: 'Largest Segment', value: data.macro_insights.largest_segment, sub: `${data.macro_insights.largest_segment_size.toLocaleString()} subscribers`, color: 'text-blue-400', bg: 'bg-blue-500/5 border-blue-500/20' },
            { icon: TrendingDown, label: 'Highest Churn Volume', value: data.macro_insights.highest_churn_volume_segment, sub: `${data.macro_insights.highest_churn_volume_count.toLocaleString()} high-risk`, color: 'text-amber-400', bg: 'bg-amber-500/5 border-amber-500/20' },
            { icon: Heart, label: 'Safest Segment', value: data.macro_insights.lowest_risk_segment, sub: `${(data.macro_insights.lowest_risk_churn_prob * 100).toFixed(0)}% avg churn`, color: 'text-emerald-400', bg: 'bg-emerald-500/5 border-emerald-500/20' },
          ].map(({ icon: Icon, label, value, sub, color, bg }) => (
            <div key={label} className={`border rounded-xl p-4 ${bg}`}>
              <div className="flex items-center gap-2 mb-2">
                <Icon className={`w-4 h-4 ${color}`} />
                <span className="text-xs text-gray-400">{label}</span>
              </div>
              <div className="text-sm font-bold text-white leading-tight">{value}</div>
              <div className="text-xs text-gray-500 mt-0.5">{sub}</div>
            </div>
          ))}
        </div>
      )}

      {/* Segment Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {data.segments.map((seg, idx) => {
          const color = CLUSTER_COLORS[idx % CLUSTER_COLORS.length];
          const isActive = selectedCluster === seg.cluster_id;
          return (
            <div
              key={seg.cluster_id}
              onClick={() => {
                setSelectedCluster(isActive ? null : seg.cluster_id);
              }}
              className={`bg-surface border rounded-xl p-5 cursor-pointer transition-all duration-200 ${
                isActive ? 'border-blue-500 ring-2 ring-blue-500/20 shadow-blue-500/10 shadow-lg' : 'border-border hover:border-gray-600'
              }`}
            >
              {/* Card Header */}
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-2">
                  <span className="w-3 h-3 rounded-full flex-shrink-0" style={{ backgroundColor: color }} />
                  <span className="text-sm font-bold text-white leading-snug">{seg.cluster_name}</span>
                </div>
                <HealthBadge status={seg.health_status} score={seg.health_score} />
              </div>

              {/* Subscriber Count */}
              <div className="text-2xl font-bold text-white mb-0.5">{seg.size.toLocaleString()}</div>
              <div className="text-xs text-gray-400 mb-4">{seg.percentage}% of subscribers</div>

              {/* Key Stats */}
              <div className="space-y-2 text-xs border-t border-border pt-3">
                <div className="flex justify-between">
                  <span className="text-gray-400">Avg Churn Prob</span>
                  <span className="font-bold text-red-400">{(seg.avg_churn_probability * 100).toFixed(1)}%</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Churn Rate</span>
                  <span className="font-bold text-amber-300">{seg.actual_churn_rate.toFixed(1)}%</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">High-Risk Customers</span>
                  <span className="font-bold text-orange-400">{seg.high_risk_count.toLocaleString()}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Avg Monthly Fee</span>
                  <span className="font-bold text-gray-200">₹{seg.avg_monthly_charges.toLocaleString()}</span>
                </div>
              </div>

              {/* Strategy + Detail Button */}
              <div className="mt-4 pt-3 border-t border-border space-y-2">
                <p className="text-xs text-blue-400 leading-snug">{seg.recommended_strategy}</p>
                <button
                  onClick={(e) => { e.stopPropagation(); setDetailSeg({ seg, idx }); }}
                  className="w-full flex items-center justify-center gap-1.5 text-xs font-medium text-gray-300 hover:text-white bg-white/[0.04] hover:bg-white/[0.08] border border-border hover:border-gray-500 rounded-lg py-2 transition"
                >
                  View Detail <ChevronRight className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          );
        })}
      </div>

      {/* Scatter Plot */}
      <div className="bg-surface border border-border rounded-xl p-5 shadow-lg">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-sm font-semibold text-white">Cluster Scatter Plot — PCA 2D Projection</h2>
            <p className="text-xs text-gray-500 mt-0.5">Click a segment card to highlight its cluster. Each point = one subscriber.</p>
          </div>
          <div className="flex items-center gap-1.5 text-xs text-gray-500">
            <Info className="w-3.5 h-3.5" />
            <span>PCA axes are abstract behavioral dimensions</span>
          </div>
        </div>
        <div className="h-80">
          <ReactECharts option={scatterOption} style={{ height: '100%', width: '100%' }} />
        </div>
      </div>

      {/* Analytics Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="bg-surface border border-border rounded-xl p-5">
          <h3 className="text-sm font-semibold text-white mb-1">Churn Rate vs Avg Churn Probability by Segment</h3>
          <p className="text-xs text-gray-500 mb-3">Bars = actual churn rate · Line = model-predicted probability</p>
          <div className="h-52">
            <ReactECharts option={churnBarOption} style={{ height: '100%', width: '100%' }} />
          </div>
        </div>
        <div className="bg-surface border border-border rounded-xl p-5">
          <h3 className="text-sm font-semibold text-white mb-1">Segment Size & High-Risk Distribution</h3>
          <p className="text-xs text-gray-500 mb-3">Total subscribers vs high-risk customers per segment</p>
          <div className="h-52">
            <ReactECharts option={sizeBarOption} style={{ height: '100%', width: '100%' }} />
          </div>
        </div>
      </div>

      {/* Segment × Risk Matrix */}
      {data.risk_matrix && data.risk_matrix.length > 0 && (
        <RiskMatrix matrix={data.risk_matrix} />
      )}

      {/* Clustering Quality */}
      {data.quality_metrics && <QualityPanel qm={data.quality_metrics} />}

      {/* Segment Detail Drawer */}
      {detailSeg && (
        <SegmentDetailPanel
          seg={detailSeg.seg}
          segIdx={detailSeg.idx}
          onClose={() => setDetailSeg(null)}
        />
      )}
    </div>
  );
};
