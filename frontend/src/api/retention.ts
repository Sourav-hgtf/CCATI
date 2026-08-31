import { fetchApi } from './client';

export interface RetentionStrategyGroup {
  risk_tier: 'Critical' | 'High' | 'Medium' | 'Low';
  customer_count: number;
  revenue_at_risk: number;
  recommended_action: string;
  action_code: string;
  estimated_cost: number;
  expected_saves: number;
  expected_roi: string;
  description: string;
}

export const getRetentionStrategies = async (): Promise<RetentionStrategyGroup[]> => {
  return fetchApi<RetentionStrategyGroup[]>(`/retention/recommendations`);
};
