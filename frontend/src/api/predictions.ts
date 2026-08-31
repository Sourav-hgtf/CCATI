import { fetchApi } from './client';

export interface ChurnPredictionResult {
  customer_id: string;
  churn_probability: number;
  risk_tier: 'Low' | 'Medium' | 'High' | 'Critical';
  confidence_score: number;
  model_name: string;
  model_version: string;
  prediction_timestamp: string;
  top_features: {
    feature_name: string;
    feature_value: string | number;
    contribution: number;
    impact: 'Increase' | 'Decrease';
  }[];
  recommended_action?: string;
}

export const predictCustomerChurn = async (customerId: string): Promise<ChurnPredictionResult> => {
  return fetchApi<ChurnPredictionResult>(`/predict`, {
    method: 'POST',
    body: JSON.stringify({ customer_id: customerId }),
  });
};
