// Auto-generated TypeScript definitions from FastAPI OpenAPI Schema (TICKET-903)
// DO NOT EDIT MANUALLY - Generated via `python scripts/generate_types.py`

export interface ConfusionMatrixData {
  tn: number;
  fp: number;
  fn: number;
  tp: number;
}

export interface CustomerDetailResponse {
  customer_id: string;
  name: string;
  phone: string;
  email: string;
  is_pii_revealed?: boolean;
  plan_tier: string;
  contract_type: string;
  payment_method: string;
  tenure_months: number;
  monthly_charges: number;
  total_charges: number;
  churn_probability: number;
  risk_tier: string;
  priority_score: number;
  clv: number;
  usage_history: Record<string, any>[];
  top_shap_features: any[];
  recommendation: RecommendationPayload;
  call_log_history: Record<string, any>[];
  segment_id?: number;
}

export interface CustomerListItem {
  customer_id: string;
  name: string;
  phone: string;
  plan_tier: string;
  tenure_months: number;
  monthly_charges: number;
  churn_probability: number;
  risk_tier: string;
  priority_score: number;
  usage_drop_call_pct: number;
  support_calls_m1: number;
  last_call_reason?: any;
  recommended_action: string;
  segment_id?: number;
}

export interface CustomerPaginatedResponse {
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
  items: any[];
}

export interface FeatureAttribution {
  feature: string;
  importance: number;
  direction: string;
}

export interface FeatureDriftItem {
  feature_name: string;
  baseline_mean: number;
  current_mean: number;
  drift_score: number;
  status: string;
}

export interface HTTPValidationError {
  detail?: any[];
}

export interface LoginRequest {
  email: string;
  password?: string;
}

export interface MetricRun {
  version: string;
  model_name: string;
  registered_at: string;
  status: string;
  precision: number;
  recall: number;
  f1: number;
  roc_auc: number;
  pr_auc: number;
  confusion_matrix: ConfusionMatrixData;
}

export interface ModelMetricsResponse {
  current_model_version: string;
  promoted_model_name: string;
  history: any[];
  drift_report: any[];
}

export interface ROIDetails {
  action_cost: number;
  expected_saved_revenue: number;
  net_saved_revenue: number;
  roi_pct: number;
}

export interface RecommendationPayload {
  action_code: string;
  action_name: string;
  description: string;
  roi_details: ROIDetails;
  actioned?: boolean;
  actioned_at?: any;
}

export interface ScatterPoint {
  customer_id: string;
  x: number;
  y: number;
  cluster_id: number;
  churn_probability: number;
  risk_tier: string;
}

export interface ScoringJobResponse {
  job_id: string;
  job_type: string;
  status: string;
  started_at: string;
  completed_at?: any;
  records_processed?: number;
  message?: string;
}

export interface ScoringJobTriggerRequest {
  job_type?: string;
  force_ingestion?: boolean;
}

export interface SegmentQualityMetrics {
  silhouette_score: number;
  davies_bouldin_index: number;
  calinski_harabasz_index: number;
  n_clusters: number;
  evaluated_subscribers: number;
  interpretation: string;
}

export interface SegmentRiskMatrixRow {
  cluster_id: number;
  cluster_name: string;
  low_risk_count: number;
  medium_risk_count: number;
  high_risk_count: number;
  critical_risk_count: number;
  total_count: number;
  high_critical_ratio: number;
}

export interface SegmentMacroInsights {
  highest_risk_segment: string;
  highest_risk_churn_prob: number;
  largest_segment: string;
  largest_segment_size: number;
  highest_churn_volume_segment: string;
  highest_churn_volume_count: number;
  lowest_risk_segment: string;
  lowest_risk_churn_prob: number;
}

export interface SegmentROI {
  eligible_customers: number;
  avg_clv: number;
  estimated_campaign_cost: number;
  estimated_retention_opportunity: number;
  estimated_roi_pct: number;
}

export interface SegmentDetailResponse {
  profile: SegmentProfile;
  feature_distributions: Record<string, any>;
  total_customers: number;
  roi_projection?: SegmentROI;
  risk_breakdown: Record<string, number>;
}

export interface SegmentOverviewResponse {
  segments: SegmentProfile[];
  scatter_points: ScatterPoint[];
  quality_metrics?: SegmentQualityMetrics;
  risk_matrix: SegmentRiskMatrixRow[];
  macro_insights?: SegmentMacroInsights;
}

export interface SegmentProfile {
  cluster_id: number;
  cluster_name: string;
  size: number;
  percentage: number;
  avg_tenure_months: number;
  avg_monthly_charges: number;
  avg_total_charges: number;
  avg_usage_drop_call_pct: number;
  avg_usage_drop_data_pct: number;
  avg_support_calls_m1: number;
  avg_churn_probability: number;
  actual_churn_rate: number;
  avg_clv: number;
  avg_priority_score: number;
  high_risk_count: number;
  critical_risk_count: number;
  health_score: number;
  health_status: 'HEALTHY' | 'MODERATE_RISK' | 'CRITICAL_RISK';
  recommended_strategy: string;
  risk_category: string;
  eligible_customers: number;
  estimated_campaign_cost: number;
  estimated_retention_opportunity: number;
  estimated_roi_pct: number;
}

export interface SegmentCustomerItem {
  customer_id: string;
  name: string;
  plan_tier: string;
  contract_type: string;
  tenure_months: number;
  monthly_charges: number;
  churn_probability: number;
  risk_tier: string;
  priority_score: number;
  clv: number;
  support_calls_m1: number;
  usage_drop_call_pct: number;
  cluster_id: number;
}

export interface SegmentCustomerListResponse {
  cluster_id: number;
  cluster_name: string;
  total_customers: number;
  page: number;
  page_size: number;
  total_pages: number;
  customers: SegmentCustomerItem[];
}

export interface SegmentSummaryResponse {
  total_segments: number;
  total_subscribers: number;
  macro_insights: SegmentMacroInsights;
  quality_metrics: SegmentQualityMetrics;
  segments_summary: SegmentProfile[];
}

export interface TokenResponse {
  access_token: string;
  token_type?: string;
  user_id: string;
  email: string;
  role: string;
}

export interface UserProfileResponse {
  user_id: string;
  email: string;
  name: string;
  role: string;
}

export interface ValidationError {
  loc: any[];
  msg: string;
  type: string;
  input?: any;
  ctx?: Record<string, any>;
}

