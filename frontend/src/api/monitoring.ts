import { fetchApi } from './client';
import { ModelMetricsResponse } from '../types';

export interface ActiveModelInfo {
  status: string;
  model_name: string;
  model_version: string;
  registered_at: string;
  model_status: string;
  metrics: {
    precision: number;
    recall: number;
    f1: number;
    roc_auc: number;
    pr_auc: number;
  };
  feature_count: number;
  hyperparameters: Record<string, any>;
  sha256: string;
  integrity_verified: boolean;
  threshold: number;
}

export interface FeatureDriftDetail {
  name: string;
  type: string;
  drift_score: number;
  p_value: number;
  drift_detected: boolean;
  severity: 'STABLE' | 'WARNING' | 'CRITICAL';
  status: 'STABLE' | 'DRIFTING';
  baseline_stats: {
    mean?: number;
    std?: number;
    min?: number;
    max?: number;
    sample_count?: number;
  };
  current_stats: {
    mean?: number;
    std?: number;
    min?: number;
    max?: number;
    sample_count?: number;
  };
}

export interface MonitoringAlert {
  severity: string;
  title: string;
  message: string;
  affected_features?: string[];
  timestamp: string;
}

export interface DriftStatusResponse {
  monitoring_id: string;
  status: 'STABLE' | 'WARNING' | 'CRITICAL' | 'INSUFFICIENT_DATA';
  overall_score: number;
  features_checked: number;
  features_drifted: number;
  model_name: string;
  model_version: string;
  timestamp: string;
  recommended_action: string;
  alerts: MonitoringAlert[];
  features: FeatureDriftDetail[];
}

export interface MonitoringHistoryItem {
  monitoring_id: string;
  timestamp: string;
  model_name: string;
  model_version: string;
  overall_status: string;
  overall_score: number;
  features_checked: number;
  features_drifted: number;
}

export interface PerformanceMetrics {
  accuracy: number;
  precision: number;
  recall: number;
  f1: number;
  roc_auc: number;
  pr_auc: number;
  confusion_matrix: {
    tn: number;
    fp: number;
    fn: number;
    tp: number;
  };
}

export interface PerformanceMonitoringResponse {
  performance_id: string;
  status: 'HEALTHY' | 'WARNING' | 'CRITICAL' | 'UNAVAILABLE';
  model_name: string;
  model_version: string;
  threshold: number;
  timestamp: string;
  ground_truth_available: boolean;
  sample_count: number;
  metrics: PerformanceMetrics | null;
  baseline: {
    precision: number;
    recall: number;
    f1: number;
    roc_auc: number;
    pr_auc: number;
  };
  deltas?: {
    precision_delta: number;
    recall_delta: number;
    f1_delta: number;
    roc_auc_delta: number;
    pr_auc_delta: number;
  };
  confusion_matrix?: {
    tn: number;
    fp: number;
    fn: number;
    tp: number;
  };
  churn_rate_analysis?: {
    actual_churn_rate_pct: number;
    predicted_churn_rate_pct: number;
    churn_rate_diff_pct: number;
  };
  probability_distribution?: {
    min: number;
    max: number;
    mean: number;
    median: number;
    std: number;
  };
  alerts: MonitoringAlert[];
  recommended_action: string;
}

export interface PerformanceHistoryItem {
  performance_id: string;
  timestamp: string;
  model_name: string;
  model_version: string;
  status: string;
  precision: number;
  recall: number;
  f1: number;
  roc_auc: number;
  pr_auc: number;
}

export const getModelMetrics = async (): Promise<ModelMetricsResponse> => {
  return fetchApi<ModelMetricsResponse>(`/models/metrics`);
};

export const getActiveModelInfo = async (): Promise<ActiveModelInfo> => {
  return fetchApi<ActiveModelInfo>(`/model-info`);
};

export const getMonitoringStatus = async (): Promise<DriftStatusResponse> => {
  return fetchApi<DriftStatusResponse>(`/monitoring/status`);
};

export const getMonitoringHistory = async (): Promise<MonitoringHistoryItem[]> => {
  return fetchApi<MonitoringHistoryItem[]>(`/monitoring/history`);
};

export const runMonitoringScan = async (): Promise<{ status: string; run: DriftStatusResponse }> => {
  return fetchApi<{ status: string; run: DriftStatusResponse }>(`/monitoring/run`, {
    method: 'POST',
  });
};

export const getPerformanceMonitoring = async (): Promise<PerformanceMonitoringResponse> => {
  return fetchApi<PerformanceMonitoringResponse>(`/monitoring/performance`);
};

export const getPerformanceHistory = async (): Promise<PerformanceHistoryItem[]> => {
  return fetchApi<PerformanceHistoryItem[]>(`/monitoring/performance/history`);
};

export const runPerformanceScan = async (): Promise<{ status: string; run: PerformanceMonitoringResponse }> => {
  return fetchApi<{ status: string; run: PerformanceMonitoringResponse }>(`/monitoring/performance/run`, {
    method: 'POST',
  });
};

export const promoteCandidateModel = async (version: string): Promise<{ status: string; promoted_version: string }> => {
  return fetchApi<{ status: string; promoted_version: string }>(`/models/promote/${version}`, {
    method: 'POST',
  });
};
