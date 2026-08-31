import React, { useState, useEffect } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { predictCustomerChurn, ChurnPredictionResult } from '../api/predictions';
import { StatusBadge } from '../components/common/StatusBadge';
import { Search, BrainCircuit, Sparkles, CheckCircle2, TrendingUp, TrendingDown, ArrowRight, RefreshCw, AlertTriangle } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export const Predictions: React.FC = () => {
  const navigate = useNavigate();
  const [selectedCustomerId, setSelectedCustomerId] = useState('CUST-10000');
  const [activeSearchId, setActiveSearchId] = useState('CUST-10000');
  const [result, setResult] = useState<ChurnPredictionResult | null>(null);

  const queryClient = useQueryClient();

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
    return '#10b981';                   // Green (Low)
  };

  const isMatchingCustomer = result && result.customer_id.toLowerCase() === activeSearchId.toLowerCase();

  return (
    <div className="p-8 space-y-8 max-w-6xl mx-auto">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-white flex items-center space-x-2">
          <BrainCircuit className="w-6 h-6 text-[#F5A623]" />
          <span>Real-time Churn Prediction Workspace</span>
        </h1>
        <p className="text-xs text-gray-400 mt-1">Run production ML inference to compute instant subscriber churn risk probabilities and feature explanations.</p>
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
                placeholder="Enter Customer ID e.g. CUST-10000"
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

        {/* Quick Sample Selector Shortcuts */}
        <div className="flex flex-wrap items-center gap-2 pt-2 border-t border-[#272B36] text-xs">
          <span className="text-gray-400 font-semibold text-[11px]">Quick Sample Profiles:</span>

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
      </div>

      {/* Loading State */}
      {mutation.isPending && (
        <div className="dark-card p-12 text-center text-gray-400 flex flex-col items-center justify-center space-y-3 border-[#272B36]">
          <RefreshCw className="w-6 h-6 text-[#F5A623] animate-spin" />
          <span className="text-xs font-semibold">Executing production ML inference for <strong className="text-white font-mono">{activeSearchId}</strong>...</span>
        </div>
      )}

      {/* Error State */}
      {mutation.isError && !mutation.isPending && (
        <div className="dark-card p-8 text-center flex flex-col items-center justify-center space-y-4 border-red-500/40 bg-red-950/20">
          <AlertTriangle className="w-8 h-8 text-red-400" />
          <div className="space-y-1">
            <h3 className="text-sm font-bold text-red-300">Prediction Service Unavailable</h3>
            <p className="text-xs text-gray-400 max-w-md">
              Production ML inference could not be obtained for subscriber <strong className="text-white font-mono">{activeSearchId}</strong>.
              Please verify the subscriber ID or ensure batch scoring has ingested this record.
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

      {/* Synchronized Production ML Prediction Output Card */}
      {result && isMatchingCustomer && !mutation.isPending && (
        <div className="space-y-6">
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
                    strokeDashoffset={440 - (440 * result.churn_probability)}
                    strokeLinecap="round"
                    className="transition-all duration-1000 ease-out"
                  />
                </svg>
                <div className="absolute flex flex-col items-center">
                  <span className="text-3xl font-extrabold text-white">{(result.churn_probability * 100).toFixed(0)}%</span>
                  <span className="text-[10px] text-gray-400 font-medium mt-0.5">Risk Score</span>
                </div>
              </div>

              <StatusBadge status={result.risk_tier} size="md" />

              <div className="text-[11px] text-gray-400 pt-2 border-t border-[#272B36] w-full flex justify-between">
                <span>Model Confidence:</span>
                <span className="font-semibold text-emerald-400">{(result.confidence_score * 100).toFixed(0)}%</span>
              </div>
            </div>

            {/* Model Metadata Card */}
            <div className="dark-card p-6 space-y-4 lg:col-span-2 flex flex-col justify-between">
              <div>
                <h3 className="text-sm font-bold text-white uppercase tracking-wider">Inference Model Metadata</h3>
                <p className="text-xs text-gray-400 mt-1">
                  Versioned production classifier attributions for <strong className="text-white font-mono">{result.customer_id}</strong>.
                </p>
              </div>

              <div className="grid grid-cols-2 gap-4 text-xs">
                <div className="bg-[#1A1D24] p-3 rounded-lg border border-[#272B36] space-y-1">
                  <span className="text-gray-400 text-[10px]">Model Name</span>
                  <p className="font-semibold text-white truncate">{result.model_name}</p>
                </div>
                <div className="bg-[#1A1D24] p-3 rounded-lg border border-[#272B36] space-y-1">
                  <span className="text-gray-400 text-[10px]">Version Hash</span>
                  <p className="font-mono font-semibold text-[#F5A623]">{result.model_version}</p>
                </div>
                <div className="bg-[#1A1D24] p-3 rounded-lg border border-[#272B36] space-y-1">
                  <span className="text-gray-400 text-[10px]">Prediction Timestamp</span>
                  <p className="text-gray-300 text-[11px]">{new Date(result.prediction_timestamp).toLocaleTimeString()}</p>
                </div>
                <div className="bg-[#1A1D24] p-3 rounded-lg border border-[#272B36] space-y-1">
                  <span className="text-gray-400 text-[10px]">Inference Status</span>
                  <p className="font-semibold text-emerald-400 flex items-center">
                    <CheckCircle2 className="w-3.5 h-3.5 mr-1" /> Real ML Inference (200 OK)
                  </p>
                </div>
              </div>

              {result.recommended_action && (
                <div className="bg-[#1A1D24] p-3 rounded-lg border border-[#272B36] flex items-center justify-between text-xs">
                  <span className="text-gray-400 font-medium">Recommended Action:</span>
                  <span className="font-bold text-[#F5A623]">{result.recommended_action}</span>
                </div>
              )}

              <div className="pt-3 border-t border-[#272B36] flex justify-end">
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

          {/* "Why this prediction?" Feature Contributions */}
          <div className="dark-card p-6 space-y-4">
            <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center space-x-2">
              <Sparkles className="w-4 h-4 text-[#F5A623]" />
              <span>Why this prediction? (Top Feature Contributions)</span>
            </h3>

            <div className="space-y-3">
              {result.top_features.map((feat) => {
                const isIncrease = feat.impact === 'Increase';
                return (
                  <div key={feat.feature_name} className="bg-[#1A1D24] p-3.5 rounded-lg border border-[#272B36] flex items-center justify-between">
                    <div className="space-y-0.5">
                      <div className="flex items-center space-x-2">
                        <span className="text-xs font-semibold text-white font-mono">{feat.feature_name}</span>
                        <span className="text-[10px] px-2 py-0.5 rounded bg-[#151821] text-gray-300">{feat.feature_value}</span>
                      </div>
                      <p className="text-[11px] text-gray-400">
                        {isIncrease ? 'Increases churn risk' : 'Reduces churn risk'}
                      </p>
                    </div>

                    <div className="flex items-center space-x-2">
                      <span className={`text-xs font-bold ${isIncrease ? 'text-red-400' : 'text-emerald-400'}`}>
                        {isIncrease ? `+${(feat.contribution * 100).toFixed(0)}%` : `-${(Math.abs(feat.contribution) * 100).toFixed(0)}%`}
                      </span>
                      {isIncrease ? <TrendingUp className="w-4 h-4 text-red-400" /> : <TrendingDown className="w-4 h-4 text-emerald-400" />}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
