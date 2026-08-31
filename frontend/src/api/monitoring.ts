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

export const getModelMetrics = async (): Promise<ModelMetricsResponse> => {
  return fetchApi<ModelMetricsResponse>(`/models/metrics`);
};

export const getActiveModelInfo = async (): Promise<ActiveModelInfo> => {
  return fetchApi<ActiveModelInfo>(`/model-info`);
};

export const promoteCandidateModel = async (version: string): Promise<{ status: string; promoted_version: string }> => {
  return fetchApi<{ status: string; promoted_version: string }>(`/models/promote/${version}`, {
    method: 'POST',
  });
};
