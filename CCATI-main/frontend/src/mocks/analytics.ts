import { OverviewMetrics, ChurnTrendPoint, RiskDistributionPoint } from '../types';

export const mockOverviewMetrics: OverviewMetrics = {
  active_customers: 4932,
  active_customers_change: +2.4,
  churn_rate: 18.4,
  churn_rate_change: -0.7,
  revenue_at_risk: 211937,
  revenue_at_risk_change: -4.1,
  high_risk_customers: 3183,
  high_risk_customers_change: +12,
  customers_saved: 428,
  customers_saved_change: +15.8,
  retention_roi: 3.8,
  retention_roi_change: +0.4,
};

export const mockChurnTrendData: ChurnTrendPoint[] = [
  { time_period: 'Jan', churn_rate: 24.2, customers_at_risk: 1120 },
  { time_period: 'Feb', churn_rate: 22.8, customers_at_risk: 1080 },
  { time_period: 'Mar', churn_rate: 21.5, customers_at_risk: 1010 },
  { time_period: 'Apr', churn_rate: 20.1, customers_at_risk: 950 },
  { time_period: 'May', churn_rate: 19.4, customers_at_risk: 920 },
  { time_period: 'Jun', churn_rate: 18.8, customers_at_risk: 890 },
  { time_period: 'Jul', churn_rate: 18.4, customers_at_risk: 870 },
];

export const mockRiskDistributionData: RiskDistributionPoint[] = [
  { tier: 'Low', count: 1749, percentage: 35.5, revenue_at_risk: 35000 },
  { tier: 'Medium', count: 1240, percentage: 25.1, revenue_at_risk: 62000 },
  { tier: 'High', count: 1250, percentage: 25.3, revenue_at_risk: 88000 },
  { tier: 'Critical', count: 693, percentage: 14.1, revenue_at_risk: 68937 },
];
