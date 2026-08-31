export * from './api';

export interface OverviewMetrics {
  active_customers: number;
  active_customers_change: number;
  churn_rate: number;
  churn_rate_change: number;
  revenue_at_risk: number;
  revenue_at_risk_change: number;
  high_risk_customers: number;
  high_risk_customers_change: number;
  customers_saved: number;
  customers_saved_change: number;
  retention_roi: number;
  retention_roi_change: number;
}

export interface ChurnTrendPoint {
  time_period: string;
  churn_rate: number;
  customers_at_risk: number;
}

export interface RiskDistributionPoint {
  tier: 'Low' | 'Medium' | 'High' | 'Critical';
  count: number;
  percentage: number;
  revenue_at_risk: number;
}

export interface ROISimulationInputs {
  target_customers: number;
  offer_cost_per_customer: number;
  campaign_cost: number;
  expected_success_rate: number; // e.g. 0.35 (35%)
  avg_customer_clv: number;
}

export interface ROISimulationResults {
  total_investment: number;
  expected_saves: number;
  expected_revenue_saved: number;
  net_benefit: number;
  roi_ratio: number;
  roi_pct: number;
}

export interface DatasetFeatureItem {
  feature_name: string;
  data_type: string;
  missing_pct: number;
  unique_values: number;
  status: 'Clean' | 'Imputed' | 'Warning';
}

export interface DataOverviewMetrics {
  total_rows: number;
  total_columns: number;
  missing_values_count: number;
  duplicate_rows_count: number;
  data_quality_score: number;
  last_ingested: string;
  features: DatasetFeatureItem[];
}

export interface ReportItem {
  id: string;
  title: string;
  category: 'Executive' | 'Retention' | 'Model' | 'ROI' | 'Risk';
  description: string;
  last_generated: string;
  file_format: 'PDF' | 'CSV' | 'XLSX';
  size: string;
}

export interface SystemSettingsConfig {
  general: {
    platform_name: string;
    organization: string;
    default_currency: string;
    timezone: string;
  };
  business_rules: {
    clv_tenure_multiplier: number;
    high_risk_threshold: number;
    critical_risk_threshold: number;
    auto_trigger_campaigns: boolean;
  };
  model: {
    active_model_version: string;
    auto_retrain_frequency: string;
    min_recall_threshold: number;
  };
  notifications: {
    email_alerts: boolean;
    slack_webhook_enabled: boolean;
    high_risk_threshold_alert: number;
  };
}
