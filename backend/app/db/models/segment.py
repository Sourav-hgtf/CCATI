from sqlalchemy import Column, Integer, String, Float
from backend.app.db.base import Base

class SegmentProfile(Base):
    __tablename__ = "segment_profiles"

    cluster_id = Column(Integer, primary_key=True)
    cluster_name = Column(String, nullable=True)
    size = Column(Integer, nullable=True)
    percentage = Column(Float, nullable=True)
    avg_tenure_months = Column(Float, nullable=True)
    avg_monthly_charges = Column(Float, nullable=True)
    avg_total_charges = Column(Float, nullable=True)
    avg_usage_drop_call_pct = Column(Float, nullable=True)
    avg_usage_drop_data_pct = Column(Float, nullable=True)
    avg_support_calls_m1 = Column(Float, nullable=True)
    avg_churn_probability = Column(Float, nullable=True)
    actual_churn_rate = Column(Float, nullable=True)
    avg_clv = Column(Float, nullable=True)
    avg_priority_score = Column(Float, nullable=True)
    high_risk_count = Column(Integer, nullable=True)
    critical_risk_count = Column(Integer, nullable=True)
    health_score = Column(Float, nullable=True)
    health_status = Column(String, nullable=True)
    risk_category = Column(String, nullable=True)
    recommended_strategy = Column(String, nullable=True)
    eligible_customers = Column(Integer, nullable=True)
    estimated_campaign_cost = Column(Float, nullable=True)
    estimated_retention_opportunity = Column(Float, nullable=True)
    estimated_roi_pct = Column(Float, nullable=True)
