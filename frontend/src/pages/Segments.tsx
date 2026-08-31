import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { fetchApi } from '../lib/apiClient';
import { SegmentOverviewResponse, SegmentProfile } from '../types/api';
import ReactECharts from 'echarts-for-react';
import { PieChart, Users, AlertTriangle, ArrowRight } from 'lucide-react';
import { Link } from 'react-router-dom';

export const Segments: React.FC = () => {
  const [selectedCluster, setSelectedCluster] = useState<number | null>(null);

  const { data, isLoading } = useQuery<SegmentOverviewResponse>({
    queryKey: ['segments-overview'],
    queryFn: () => fetchApi<SegmentOverviewResponse>('/segments'),
  });

  if (isLoading || !data) {
    return <div className="p-12 text-center text-gray-400">Loading K-Means cluster analysis...</div>;
  }

  // ECharts cluster scatter plot configuration (TICKET-801)
  const clusterColors = ['#ef4444', '#f59e0b', '#3b82f6', '#10b981'];

  const series = data.segments.map((seg, idx) => {
    const points = data.scatter_points
      .filter((p) => p.cluster_id === seg.cluster_id)
      .map((p) => [p.x, p.y, p.customer_id, (p.churn_probability * 100).toFixed(1)]);

    return {
      name: seg.cluster_name,
      type: 'scatter',
      symbolSize: selectedCluster === null || selectedCluster === seg.cluster_id ? 10 : 5,
      itemStyle: {
        color: clusterColors[idx % clusterColors.length],
        opacity: selectedCluster === null || selectedCluster === seg.cluster_id ? 0.85 : 0.2,
      },
      data: points,
    };
  });

  const getOption = () => ({
    backgroundColor: 'transparent',
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
    tooltip: {
      backgroundColor: '#111827',
      borderColor: '#374151',
      textStyle: { color: '#f3f4f6' },
      formatter: (params: any) => {
        return `
          <div style="font-weight:bold; color:#60a5fa;">${params.seriesName}</div>
          <div>Customer: ${params.value[2]}</div>
          <div>Churn Probability: <span style="color:#f87171; font-weight:bold;">${params.value[3]}%</span></div>
        `;
      },
    },
    xAxis: { type: 'value', splitLine: { lineStyle: { color: '#1f2937' } } },
    yAxis: { type: 'value', splitLine: { lineStyle: { color: '#1f2937' } } },
    series: series,
  });

  return (
    <div className="p-8 space-y-8">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-white">Subscriber Behavioral Segments (K-Means)</h1>
        <p className="text-sm text-gray-400 mt-1">2D PCA projection of subscriber cluster distributions and segment profiles.</p>
      </div>

      {/* Cluster Scatter Plot Card */}
      <div className="bg-surface border border-border rounded-xl p-6 shadow-lg">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-lg font-bold text-white">Cluster Scatter Plot (2D Projection)</h2>
            <p className="text-xs text-gray-400">Click a segment card below to highlight its cluster distribution.</p>
          </div>
          {selectedCluster !== null && (
            <button
              onClick={() => setSelectedCluster(null)}
              className="text-xs text-blue-400 hover:text-blue-300 font-semibold"
            >
              Reset Scatter Highlight
            </button>
          )}
        </div>
        <div className="h-96">
          <ReactECharts option={getOption()} style={{ height: '100%', width: '100%' }} />
        </div>
      </div>

      {/* Segment Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {data.segments.map((seg, idx) => (
          <div
            key={seg.cluster_id}
            onClick={() => setSelectedCluster(seg.cluster_id)}
            className={`bg-surface border rounded-xl p-6 shadow-lg cursor-pointer transition flex flex-col justify-between ${
              selectedCluster === seg.cluster_id ? 'border-blue-500 ring-2 ring-blue-500/20' : 'border-border hover:border-gray-700'
            }`}
          >
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm font-bold text-white">{seg.cluster_name}</span>
                <span className="w-3 h-3 rounded-full" style={{ backgroundColor: clusterColors[idx % clusterColors.length] }}></span>
              </div>

              <div className="text-xs text-gray-400">{seg.size} Subscribers ({seg.percentage}%)</div>

              <div className="space-y-1.5 pt-2 text-xs border-t border-border">
                <div className="flex justify-between">
                  <span className="text-gray-400">Avg Tenure:</span>
                  <span className="font-semibold text-gray-200">{seg.avg_tenure_months} mos</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Avg Monthly Fee:</span>
                  <span className="font-semibold text-gray-200">₹{seg.avg_monthly_charges}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Avg Call Drop:</span>
                  <span className="font-semibold text-red-400">{(seg.avg_usage_drop_call_pct * 100).toFixed(0)}%</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Avg Support Calls:</span>
                  <span className="font-semibold text-amber-400">{seg.avg_support_calls_m1}</span>
                </div>
              </div>
            </div>

            <div className="mt-4 pt-3 border-t border-border">
              <div className="text-xs font-semibold text-blue-400">{seg.recommended_strategy}</div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
