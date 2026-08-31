import { fetchApi } from './client';
import { OverviewMetrics, ChurnTrendPoint, RiskDistributionPoint } from '../types';

export const getOverviewMetrics = async (dateRange: string = '30d'): Promise<OverviewMetrics> => {
  return fetchApi<OverviewMetrics>(`/analytics/overview?range=${dateRange}`);
};

export const getChurnTrend = async (period: string = 'monthly'): Promise<ChurnTrendPoint[]> => {
  return fetchApi<ChurnTrendPoint[]>(`/analytics/trend?period=${period}`);
};

export const getRiskDistribution = async (): Promise<RiskDistributionPoint[]> => {
  return fetchApi<RiskDistributionPoint[]>(`/analytics/distribution`);
};
