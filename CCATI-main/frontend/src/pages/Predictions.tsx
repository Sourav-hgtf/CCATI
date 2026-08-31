import React, { useState, useEffect } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { predictCustomerChurn, ChurnPredictionResult } from '../api/predictions';
import { getCustomerDataQuality } from '../api/monitoring';
import { StatusBadge } from '../components/common/StatusBadge';
import {
  Search,
  BrainCircuit,
  Sparkles,
  CheckCircle2,
  TrendingUp,
  TrendingDown,
  ArrowRight,
  RefreshCw,
  AlertTriangle,
  ShieldCheck,
  AlertCircle,
  ShieldAlert,
  Info,
  Scale,
  Award,
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Cell,
  ReferenceLine,
} from 'recharts';

export const Predictions: React.FC = () => {
  const navigate = useNavigate();
  const [selectedCustomerId, setSelectedCustomerId] = useState('CUST-10164');
  const [activeSearchId, setActiveSearchId] = useState('CUST-10164');
  const [result, setResult] = useState<ChurnPredictionResult | null>(null);

  const queryClient = useQueryClient();

  // Task 11 Customer Data Quality Query
  const { data: dqData } = useQuery({
    queryKey: ['customer-data-quality', activeSearchId],
    queryFn: () => getCustomerDataQuality(activeSearchId),
    enabled: !!activeSearchId,
    retry: false,
  });

  const mutation = useMutation({
    mutationFn: (id: string) => predictCustomerChurn(id),
    onSuccess: (data, variables) => {
      // Defensive Validation: Only set result if returned payload customer_id matches active request ID
      if (data && data.customer_id.toLowerCase() === variables.toLowerCase()) {
        setResult(data);
        queryClient.invalidateQueries({ queryKey: ['prediction-history'] });
      }
    },
    onError: () => {
      setResult(null); // Clear stale prediction state on API/Model failure
    },
  });

  // Run initial prediction on mount
  useEffect(() => {
    mutation.mutate(selectedCustomerId);
  }, []);

  const handlePredict = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    const cleanId = selectedCustomerId.trim();
    if (cleanId) {
      setActiveSearchId(cleanId);
      setResult(null); // Immediately clear previous prediction state
      mutation.mutate(cleanId);
    }
  };

  const handleSelectQuickCustomer = (id: string) => {
    setSelectedCustomerId(id);
    setActiveSearchId(id);
    setResult(null); // Immediately clear previous prediction state
    mutation.mutate(id);
  };

  const getDialColor = (prob: number) => {
    if (prob >= 0.75) return '#ef4444'; // Red (Critical)
    if (prob >= 0.50) return '#f97316'; // Orange (High)
    if (prob >= 0.25) return '#f59e0b'; // Amber (Medium)
    return '#10b981'; // Green (Low)
  };

  const isMatchingCustomer = result && result.customer_id.toLowerCase() === activeSearchId.toLowerCase();

  // Prepare chart data from explanation attributions
  const chartData = React.useMemo(() => {
    if (!result) return [];
    const sourceDrivers = result.explanation?.all_drivers?.length
      ? result.explanation.all_drivers
      : result.top_features || [];

    return sourceDrivers.slice(0, 8).map((d) => ({
      name: d.display_name || d.feature_name.replace(/_/g, ' '),
      rawName: d.feature_name,
      value: d.feature_value,
      contribution: d.contribution,
      impact: d.impact,
      effect: d.effect || (d.contribution > 0 ? 'Increases churn risk' : 'Reduces churn risk'),
    }));
  }, [result]);

  const posDrivers = result?.explanation?.top_positive_drivers || [];
  const negDrivers = result?.explanation?.top_negative_drivers || [];

  return (
    <div className="p-8 space-y-8 max-w-6xl mx-auto">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-white flex items-center space-x-2">
          <BrainCircuit className="w-6 h-6 text-[#F5A623]" />
          <span>Real-time Churn Prediction & Decision Transparency</span>
        </h1>
        <p className="text-xs text-gray-400 mt-1">
          Production ML inference with transparent risk thresholds, SHAP feature attributions, and prescriptive retention actions.
        </p>
      </div>

      {/* Customer Selector Form */}
      <div className="dark-card p-6 border-[#F5A623]/30 space-y-4">
        <form onSubmit={handlePredict} className="flex flex-col sm:flex-row items-end gap-4">
          <div className="flex-1 space-y-2 w-full">
            <label className="text-xs font-semibold text-gray-300 flex justify-between">
              <span>Target Subscriber ID</span>
              <span className="text-[10px] text-gray-500">Case-insensitive ID lookup</span>
            </label>
            <div className="relative">
              <Search className="w-4 h-4 absolute left-3 top-3 text-gray-500" />
              <input
                type="text"
                value={selectedCustomerId}
                onChange={(e) => setSelectedCustomerId(e.target.value)}
                placeholder="Enter Customer ID e.g. CUST-10164"
                className="w-full bg-[#1A1D24] border border-[#272B36] rounded-lg pl-9 pr-4 py-2 text-sm text-white focus:outline-none focus:border-[#F5A623] font-mono transition"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={mutation.isPending}
            className="w-full sm:w-auto px-6 py-2.5 rounded-lg bg-[#F5A623] hover:bg-[#E0951C] text-black font-bold text-xs flex items-center justify-center space-x-2 shadow-lg shadow-[#F5A623]/20 transition disabled:opacity-50"
          >
            <Sparkles className="w-4 h-4 text-black" />
            <span>{mutation.isPending ? 'Computing ML Risk...' : 'Run Churn Prediction'}</span>
          </button>
        </form>

        {/* Quick Sample Selector Shortcuts & Data Quality Tag */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pt-2 border-t border-[#272B36] text-xs">
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-gray-400 font-semibold text-[11px]">Quick Profiles:</span>

            <span className="text-red-400 font-medium text-[11px] ml-1">High Risk:</span>
            {['CUST-10164', 'CUST-10628', 'CUST-11267'].map((id) => (
              <button
                key={id}
                onClick={() => handleSelectQuickCustomer(id)}
                className={`px-2.5 py-1 rounded-md border font-mono text-[11px] transition ${
                  selectedCustomerId.toUpperCase() === id
                    ? 'bg-red-950/80 border-red-500 text-red-300 font-bold'
                    : 'bg-[#1A1D24] border-[#272B36] text-gray-400 hover:text-white'
                }`}
              >
                {id}
              </button>
            ))}

            <span className="text-emerald-400 font-medium text-[11px] ml-2">Low Risk:</span>
            {['CUST-10006', 'CUST-10008', 'CUST-10009'].map((id) => (
              <button
                key={id}
                onClick={() => handleSelectQuickCustomer(id)}
                className={`px-2.5 py-1 rounded-md border font-mono text-[11px] transition ${
                  selectedCustomerId.toUpperCase() === id
                    ? 'bg-emerald-950/80 border-emerald-500 text-emerald-300 font-bold'
                    : 'bg-[#1A1D24] border-[#272B36] text-gray-400 hover:text-white'
                }`}
              >
                {id}
              </button>
            ))}
          </div>

          {/* TASK 11: Compact Data Quality Indicator */}
          {dqData && (
            <div className="flex items-center space-x-2 bg-[#151821] px-3 py-1.5 rounded-lg border border-[#272B36]">
              <span className="text-[10px] text-gray-400 font-semibold uppercase tracking-wider">Data Quality:</span>
              <span
                className={`text-[11px] font-bold flex items-center ${
                  dqData.has_critical_errors
                    ? 'text-red-400'
                    : dqData.quality_status === 'WARNING'
                    ? 'text-amber-400'
                    : 'text-emerald-400'
                }`}
              >
                {dqData.has_critical_errors ? (
                  <AlertCircle className="w-3.5 h-3.5 mr-1 text-red-400" />
                ) : (
                  <ShieldCheck className="w-3.5 h-3.5 mr-1 text-emerald-400" />
                )}
                {dqData.quality_score.toFixed(0)}/100 — {dqData.quality_status}
              </span>
            </div>
          )}
        </div>
      </div>

      {/* Loading State */}
      {mutation.isPending && (
        <div className="dark-card p-12 text-center text-gray-400 flex flex-col items-center justify-center space-y-3 border-[#272B36]">
          <RefreshCw className="w-6 h-6 text-[#F5A623] animate-spin" />
          <span className="text-xs font-semibold">
            Executing production ML inference & SHAP explainability for <strong className="text-white font-mono">{activeSearchId}</strong>...
          </span>
        </div>
      )}

      {/* Error State */}
      {mutation.isError && !mutation.isPending && (
        <div className="dark-card p-8 text-center flex flex-col items-center justify-center space-y-4 border-red-500/40 bg-red-950/20">
          <AlertTriangle className="w-8 h-8 text-red-400" />
          <div className="space-y-1">
            <h3 className="text-sm font-bold text-red-300">Prediction Blocked / Unavailable</h3>
            <p className="text-xs text-gray-400 max-w-md">
              Production ML inference could not be completed for subscriber <strong className="text-white font-mono">{activeSearchId}</strong>.
              This may be due to missing records or critical pre-inference data quality validation failures.
            </p>
          </div>
          <button
            onClick={() => handlePredict()}
            className="px-4 py-2 rounded-lg bg-red-900/60 hover:bg-red-900 border border-red-500/50 text-xs font-semibold text-white flex items-center space-x-2 transition"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>Retry Prediction</span>
          </button>
        </div>
      )}

      {/* Synchronized Production ML Prediction Output */}
      {result && isMatchingCustomer && !mutation.isPending && (
        <div className="space-y-6">
          {/* SECTION 1: CUSTOMER RISK PROFILE & METADATA */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Probability Meter Card */}
            <div className="dark-card p-6 flex flex-col items-center justify-center text-center space-y-4 border-[#272B36]">
              <span className="text-xs font-bold uppercase tracking-wider text-gray-400">Predicted Churn Probability</span>

              <div className="relative w-40 h-40 flex items-center justify-center">
                <svg className="w-full h-full transform -rotate-90">
                  <circle cx="80" cy="80" r="70" stroke="#1f2d47" strokeWidth="12" fill="transparent" />
                  <circle
                    cx="80"
                    cy="80"
                    r="70"
                    stroke={getDialColor(result.churn_probability)}
                    strokeWidth="12"
                    fill="transparent"
                    strokeDasharray={440}
                    strokeDashoffset={440 - 440 * result.churn_probability}
                    strokeLinecap="round"
                    className="transition-all duration-1000 ease-out"
                  />
                </svg>
                <div className="absolute flex flex-col items-center">
                  <span className="text-3xl font-extrabold text-white">{(result.churn_probability * 100).toFixed(1)}%</span>
                  <span className="text-[10px] text-gray-400 font-medium mt-0.5">Churn Probability</span>
                </div>
              </div>

              <StatusBadge status={result.risk_tier} size="md" />

              <div className="text-[11px] text-gray-400 pt-2 border-t border-[#272B36] w-full flex justify-between">
                <span>Classification Confidence:</span>
                <span className="font-semibold text-emerald-400">{(result.confidence_score * 100).toFixed(1)}%</span>
              </div>
            </div>

            {/* Model Metadata Card */}
            <div className="dark-card p-6 space-y-4 lg:col-span-2 flex flex-col justify-between">
              <div>
                <h3 className="text-sm font-bold text-white uppercase tracking-wider">Customer Risk Profile</h3>
                <p className="text-xs text-gray-400 mt-1">
                  Active production model attributions for subscriber <strong className="text-white font-mono">{result.customer_id}</strong>.
                </p>
              </div>

              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
                <div className="bg-[#1A1D24] p-3 rounded-lg border border-[#272B36] space-y-1">
                  <span className="text-gray-400 text-[10px]">Customer ID</span>
                  <p className="font-mono font-bold text-white truncate">{result.customer_id}</p>
                </div>
                <div className="bg-[#1A1D24] p-3 rounded-lg border border-[#272B36] space-y-1">
                  <span className="text-gray-400 text-[10px]">Model Version</span>
                  <p className="font-mono font-semibold text-[#F5A623]">{result.model_version}</p>
                </div>
                <div className="bg-[#1A1D24] p-3 rounded-lg border border-[#272B36] space-y-1">
                  <span className="text-gray-400 text-[10px]">Model Architecture</span>
                  <p className="font-semibold text-gray-200 truncate">{result.model_name}</p>
                </div>
                <div className="bg-[#1A1D24] p-3 rounded-lg border border-[#272B36] space-y-1">
                  <span className="text-gray-400 text-[10px]">Prediction Time</span>
                  <p className="text-gray-300 text-[11px]">{new Date(result.prediction_timestamp).toLocaleTimeString()}</p>
                </div>
              </div>

              {/* SECTION 2: RISK DECISION TRANSPARENCY BANNER */}
              <div
                className={`p-4 rounded-xl border flex items-start space-x-3 ${
                  result.churn_probability >= (result.threshold ?? 0.5)
                    ? 'bg-red-950/30 border-red-500/40 text-red-300'
                    : 'bg-emerald-950/30 border-emerald-500/40 text-emerald-300'
                }`}
              >
                {result.churn_probability >= (result.threshold ?? 0.5) ? (
                  <ShieldAlert className="w-5 h-5 text-red-400 shrink-0 mt-0.5" />
                ) : (
                  <ShieldCheck className="w-5 h-5 text-emerald-400 shrink-0 mt-0.5" />
                )}
                <div className="space-y-1 text-xs">
                  <div className="flex items-center space-x-2">
                    <span className="font-bold uppercase tracking-wide">
                      {result.decision || (result.churn_probability >= 0.5 ? 'RETENTION INTERVENTION RECOMMENDED' : 'STANDARD MONITORING')}
                    </span>
                    <span className="text-[10px] px-2 py-0.5 rounded bg-black/40 border border-white/10 font-mono">
                      Threshold: {((result.threshold ?? 0.5) * 100).toFixed(0)}%
                    </span>
                  </div>
                  <p className="text-gray-300 text-[11px] leading-relaxed">
                    {result.decision_reason ||
                      `Predicted churn probability (${(result.churn_probability * 100).toFixed(1)}%) ${
                        result.churn_probability >= (result.threshold ?? 0.5) ? 'exceeds' : 'is below'
                      } the retention intervention threshold (${((result.threshold ?? 0.5) * 100).toFixed(0)}%).`}
                  </p>
                </div>
              </div>

              <div className="pt-2 border-t border-[#272B36] flex items-center justify-between">
                <span className="text-[11px] text-gray-400">
                  Explanation Status:{' '}
                  <strong className="text-emerald-400">{result.explanation?.explanation_status || 'AVAILABLE'}</strong>
                </span>
                <button
                  onClick={() => navigate(`/customers/${result.customer_id}`)}
                  className="px-4 py-2 rounded-lg bg-[#1A1D24] hover:bg-[#272B36] text-xs font-semibold text-white flex items-center space-x-1.5 transition"
                >
                  <span>Open Customer 360 Profile</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          </div>

          {/* SECTION 3: VISUAL EXPLANATION (HORIZONTAL SHAP ATTRIBUTION CHART) */}
          <div className="dark-card p-6 space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
              <div>
                <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center space-x-2">
                  <Scale className="w-4 h-4 text-[#F5A623]" />
                  <span>SHAP Feature Attribution Waterfall / Contribution</span>
                </h3>
                <p className="text-xs text-gray-400 mt-0.5">
                  Positive impact increases churn risk (Red). Negative impact reduces churn risk / protective factor (Emerald).
                </p>
              </div>
              <div className="flex items-center space-x-4 text-xs">
                <span className="flex items-center space-x-1.5">
                  <span className="w-3 h-3 rounded bg-red-500"></span>
                  <span className="text-gray-300">Increases Churn Risk</span>
                </span>
                <span className="flex items-center space-x-1.5">
                  <span className="w-3 h-3 rounded bg-emerald-500"></span>
                  <span className="text-gray-300">Protective Factor</span>
                </span>
              </div>
            </div>

            {chartData.length > 0 ? (
              <div className="h-72">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart layout="vertical" data={chartData} margin={{ top: 10, right: 30, left: 160, bottom: 5 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#1f2d47" />
                    <XAxis
                      type="number"
                      stroke="#6b7280"
                      fontSize={11}
                      tickFormatter={(val) => `${(val * 100).toFixed(0)}%`}
                    />
                    <YAxis dataKey="name" type="category" stroke="#9ca3af" fontSize={11} tickLine={false} width={150} />
                    <Tooltip
                      contentStyle={{ backgroundColor: '#111726', borderColor: '#1f2d47', borderRadius: '8px', color: '#fff' }}
                      formatter={(val: any, _name: any, item: any) => [
                        `${(Number(val) * 100).toFixed(1)}% SHAP Impact (${item.payload.effect})`,
                        `Value: ${item.payload.value}`,
                      ]}
                    />
                    <ReferenceLine x={0} stroke="#4b5563" />
                    <Bar dataKey="contribution" radius={[0, 4, 4, 0]}>
                      {chartData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.contribution > 0 ? '#ef4444' : '#10b981'} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            ) : (
              <div className="p-8 text-center text-gray-500 text-xs">No feature contribution data available.</div>
            )}
          </div>

          {/* SECTION 4: WHY THIS CUSTOMER IS AT RISK & PROTECTIVE FACTORS */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Top Churn Drivers */}
            <div className="dark-card p-6 border-red-500/30 space-y-4">
              <div className="flex items-center space-x-2 text-red-400 font-bold text-sm">
                <TrendingUp className="w-4 h-4" />
                <span>Top Churn Drivers (Risk Escalators)</span>
              </div>
              <p className="text-xs text-gray-400">Primary behavioral and contract metrics elevating predicted churn risk.</p>

              <div className="space-y-2.5">
                {posDrivers.length > 0 ? (
                  posDrivers.map((feat, idx) => (
                    <div
                      key={feat.feature_name + idx}
                      className="bg-[#1A1D24] p-3 rounded-lg border border-[#272B36] flex items-center justify-between"
                    >
                      <div className="space-y-0.5">
                        <div className="flex items-center space-x-2">
                          <span className="text-xs font-semibold text-white">
                            {feat.display_name || feat.feature_name.replace(/_/g, ' ')}
                          </span>
                          <span className="text-[10px] px-1.5 py-0.5 rounded bg-[#151821] text-gray-300 font-mono">
                            {feat.feature_value}
                          </span>
                        </div>
                        <p className="text-[10px] text-red-400/80">{feat.effect || 'Increases churn risk'}</p>
                      </div>
                      <span className="text-xs font-bold text-red-400">+{((feat.contribution || 0) * 100).toFixed(1)}%</span>
                    </div>
                  ))
                ) : (
                  <div className="p-4 text-center text-gray-500 text-xs">No dominant risk elevating factors detected.</div>
                )}
              </div>
            </div>

            {/* Protective Factors */}
            <div className="dark-card p-6 border-emerald-500/30 space-y-4">
              <div className="flex items-center space-x-2 text-emerald-400 font-bold text-sm">
                <TrendingDown className="w-4 h-4" />
                <span>Protective Factors (Retention Anchors)</span>
              </div>
              <p className="text-xs text-gray-400">Subscribers loyalty and usage traits lowering predicted churn probability.</p>

              <div className="space-y-2.5">
                {negDrivers.length > 0 ? (
                  negDrivers.map((feat, idx) => (
                    <div
                      key={feat.feature_name + idx}
                      className="bg-[#1A1D24] p-3 rounded-lg border border-[#272B36] flex items-center justify-between"
                    >
                      <div className="space-y-0.5">
                        <div className="flex items-center space-x-2">
                          <span className="text-xs font-semibold text-white">
                            {feat.display_name || feat.feature_name.replace(/_/g, ' ')}
                          </span>
                          <span className="text-[10px] px-1.5 py-0.5 rounded bg-[#151821] text-gray-300 font-mono">
                            {feat.feature_value}
                          </span>
                        </div>
                        <p className="text-[10px] text-emerald-400/80">{feat.effect || 'Reduces churn risk'}</p>
                      </div>
                      <span className="text-xs font-bold text-emerald-400">
                        {((feat.contribution || 0) * 100).toFixed(1)}%
                      </span>
                    </div>
                  ))
                ) : (
                  <div className="p-4 text-center text-gray-500 text-xs">No significant protective factors detected.</div>
                )}
              </div>
            </div>
          </div>

          {/* SECTION 5: BUSINESS DECISION & RECOMMENDED ACTION */}
          {result.recommended_action && (
            <div className="dark-card p-6 border-[#F5A623]/30 space-y-3 bg-gradient-to-r from-surface to-surfaceElevated">
              <div className="flex items-center space-x-2 text-[#F5A623] font-bold text-sm">
                <Award className="w-4 h-4" />
                <span>Prescriptive Retention Intervention (Business Decision Engine)</span>
              </div>
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pt-1">
                <div>
                  <h4 className="text-base font-bold text-white">{result.recommended_action}</h4>
                  <p className="text-xs text-gray-400 mt-0.5">
                    Triggered automatically based on risk tier, CLV projection, and primary behavioral driver attributions.
                  </p>
                </div>
                <button
                  onClick={() => navigate(`/customers/${result.customer_id}`)}
                  className="px-4 py-2 rounded-lg bg-[#F5A623] hover:bg-[#E0951C] text-black font-bold text-xs flex items-center justify-center space-x-1.5 transition shrink-0"
                >
                  <span>Execute Intervention</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          )}

          {/* SECTION 6: SCIENTIFIC EXPLAINABILITY DISCLAIMER */}
          <div className="p-4 rounded-lg bg-[#151821] border border-[#272B36] flex items-start space-x-3 text-xs text-gray-400">
            <Info className="w-4 h-4 text-gray-500 shrink-0 mt-0.5" />
            <div>
              <span className="font-semibold text-gray-300">Model Interpretability Disclaimer:</span>{' '}
              {result.explanation?.disclaimer ||
                'Feature contribution explains the model’s prediction; it does not prove causation.'}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

