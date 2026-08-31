from sqlalchemy.orm import Session
from backend.app.db.models.segment import SegmentProfile

class SegmentRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_all_segments(self):
        return self.db.query(SegmentProfile).order_by(SegmentProfile.cluster_id).all()
        
    def get_segment(self, cluster_id: int):
        return self.db.query(SegmentProfile).filter(SegmentProfile.cluster_id == cluster_id).first()
        
    def save_segment(
        self,
        cluster_id: int,
        cluster_name: str,
        size: int,
        percentage: float,
        avg_tenure_months: float,
        avg_monthly_charges: float,
        avg_total_charges: float,
        avg_usage_drop_call_pct: float,
        avg_usage_drop_data_pct: float,
        avg_support_calls_m1: float,
        avg_churn_probability: float,
        actual_churn_rate: float,
        avg_clv: float,
        avg_priority_score: float,
        high_risk_count: int,
        critical_risk_count: int,
        health_score: float,
        health_status: str,
        risk_category: str,
        recommended_strategy: str,
        eligible_customers: int,
        estimated_campaign_cost: float,
        estimated_retention_opportunity: float,
        estimated_roi_pct: float
    ) -> SegmentProfile:
        segment = self.get_segment(cluster_id)
        if not segment:
            segment = SegmentProfile(cluster_id=cluster_id)
            self.db.add(segment)
            
        segment.cluster_name = cluster_name
        segment.size = size
        segment.percentage = percentage
        segment.avg_tenure_months = avg_tenure_months
        segment.avg_monthly_charges = avg_monthly_charges
        segment.avg_total_charges = avg_total_charges
        segment.avg_usage_drop_call_pct = avg_usage_drop_call_pct
        segment.avg_usage_drop_data_pct = avg_usage_drop_data_pct
        segment.avg_support_calls_m1 = avg_support_calls_m1
        segment.avg_churn_probability = avg_churn_probability
        segment.actual_churn_rate = actual_churn_rate
        segment.avg_clv = avg_clv
        segment.avg_priority_score = avg_priority_score
        segment.high_risk_count = high_risk_count
        segment.critical_risk_count = critical_risk_count
        segment.health_score = health_score
        segment.health_status = health_status
        segment.risk_category = risk_category
        segment.recommended_strategy = recommended_strategy
        segment.eligible_customers = eligible_customers
        segment.estimated_campaign_cost = estimated_campaign_cost
        segment.estimated_retention_opportunity = estimated_retention_opportunity
        segment.estimated_roi_pct = estimated_roi_pct
        
        self.db.commit()
        self.db.refresh(segment)
        return segment
