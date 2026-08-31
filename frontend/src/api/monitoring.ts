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
  affected_features: string[];
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

export const promoteCandidateModel = async (version: string): Promise<{ status: string; promoted_version: string }> => {
  return fetchApi<{ status: string; promoted_version: string }>(`/models/promote/${version}`, {
    method: 'POST',
  });
};
