import { DataOverviewMetrics } from '../types';

export const mockDataOverviewMetrics: DataOverviewMetrics = {
  total_rows: 1500,
  total_columns: 24,
  missing_values_count: 0,
  duplicate_rows_count: 0,
  data_quality_score: 98.5,
  last_ingested: '2026-08-31T13:47:26.452Z',
  features: [
    { feature_name: 'customer_id', data_type: 'string', missing_pct: 0.0, unique_values: 1500, status: 'Clean' },
    { feature_name: 'tenure_months', data_type: 'integer', missing_pct: 0.0, unique_values: 71, status: 'Clean' },
    { feature_name: 'monthly_charges', data_type: 'float', missing_pct: 0.0, unique_values: 1240, status: 'Clean' },
    { feature_name: 'total_charges', data_type: 'float', missing_pct: 0.0, unique_values: 1482, status: 'Clean' },
    { feature_name: 'call_minutes_m1', data_type: 'float', missing_pct: 0.0, unique_values: 890, status: 'Clean' },
    { feature_name: 'data_gb_m1', data_type: 'float', missing_pct: 0.0, unique_values: 620, status: 'Clean' },
    { feature_name: 'support_calls_m1', data_type: 'integer', missing_pct: 0.0, unique_values: 8, status: 'Clean' },
    { feature_name: 'usage_drop_call_pct', data_type: 'float', missing_pct: 0.0, unique_values: 412, status: 'Clean' },
    { feature_name: 'usage_drop_data_pct', data_type: 'float', missing_pct: 0.0, unique_values: 388, status: 'Clean' },
    { feature_name: 'contract_type', data_type: 'string', missing_pct: 0.0, unique_values: 3, status: 'Clean' },
    { feature_name: 'plan_tier', data_type: 'string', missing_pct: 0.0, unique_values: 4, status: 'Clean' },
    { feature_name: 'churn', data_type: 'integer (binary)', missing_pct: 0.0, unique_values: 2, status: 'Clean' },
  ],
};
