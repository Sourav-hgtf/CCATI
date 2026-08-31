import { fetchApi } from './client';
import { ModelMetricsResponse } from '../types';

export const getModelMetrics = async (): Promise<ModelMetricsResponse> => {
  return fetchApi<ModelMetricsResponse>(`/models/metrics`);
};

export const promoteCandidateModel = async (version: string): Promise<{ status: string; promoted_version: string }> => {
  return fetchApi<{ status: string; promoted_version: string }>(`/models/promote/${version}`, {
    method: 'POST',
  });
};
