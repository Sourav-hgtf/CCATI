import { fetchApi } from './client';

export interface FeatureAttribution {
  feature_name: string;
  feature_value: string | number;
  contribution: number;
  impact: 'Increase' | 'Decrease';
}

export interface ChurnPredictionResult {
  prediction_id?: string;
  customer_id: string;
  churn_probability: number;
  risk_tier: 'Low' | 'Medium' | 'High' | 'Critical';
  confidence_score: number;
  model_name: string;
  model_version: string;
  prediction_timestamp: string;
  top_features: FeatureAttribution[];
  recommended_action?: string;
}

export interface PredictionHistoryItem extends ChurnPredictionResult {
  prediction_id: string;
  prediction: number;
  threshold: number;
}

export interface PredictionHistoryPaginatedResponse {
  items: PredictionHistoryItem[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export const predictCustomerChurn = async (customerId: string): Promise<ChurnPredictionResult> => {
  return fetchApi<ChurnPredictionResult>(`/predict`, {
    method: 'POST',
    body: JSON.stringify({ customer_id: customerId }),
  });
};

export const getPredictionHistory = async (
  page: number = 1,
  pageSize: number = 20,
  riskTier?: string,
  customerId?: string
): Promise<PredictionHistoryPaginatedResponse> => {
  let url = `/predictions/history?page=${page}&page_size=${pageSize}`;
  if (riskTier) url += `&risk_tier=${encodeURIComponent(riskTier)}`;
  if (customerId) url += `&customer_id=${encodeURIComponent(customerId)}`;
  return fetchApi<PredictionHistoryPaginatedResponse>(url);
};

export const getCustomerPredictionHistory = async (
  customerId: string
): Promise<PredictionHistoryItem[]> => {
  return fetchApi<PredictionHistoryItem[]>(`/customers/${encodeURIComponent(customerId)}/predictions`);
};
