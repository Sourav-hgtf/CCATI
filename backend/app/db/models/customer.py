from sqlalchemy import Column, Integer, String, Float, Text
from backend.app.db.base import Base

class Customer(Base):
    __tablename__ = "customers"

    customer_id = Column(String, primary_key=True)
    name = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    email = Column(String, nullable=True)
    region = Column(String, nullable=True)
    plan_tier = Column(String, nullable=True)
    contract_type = Column(String, nullable=True)
    payment_method = Column(String, nullable=True)
    
    tenure_months = Column(Integer, nullable=True)
    monthly_charges = Column(Float, nullable=True)
    total_charges = Column(Float, nullable=True)
    
    call_minutes_m1 = Column(Float, nullable=True)
    call_minutes_m2 = Column(Float, nullable=True)
    call_minutes_m3 = Column(Float, nullable=True)
    
    data_gb_m1 = Column(Float, nullable=True)
    data_gb_m2 = Column(Float, nullable=True)
    data_gb_m3 = Column(Float, nullable=True)
    
    recharge_count_m1 = Column(Integer, nullable=True)
    recharge_count_m2 = Column(Integer, nullable=True)
    recharge_count_m3 = Column(Integer, nullable=True)
    
    support_calls_m1 = Column(Integer, nullable=True)
    support_calls_m2 = Column(Integer, nullable=True)
    support_calls_m3 = Column(Integer, nullable=True)
    
    churn = Column(Integer, nullable=True)
    usage_drop_call_pct = Column(Float, nullable=True)
    usage_drop_data_pct = Column(Float, nullable=True)
    support_call_trend = Column(Integer, nullable=True)
    avg_monthly_recharges = Column(Float, nullable=True)
    tenure_bucket = Column(String, nullable=True)


class CallLog(Base):
    __tablename__ = "call_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(String, index=True, nullable=True)
    call_reason = Column(String, nullable=True)
    sentiment = Column(String, nullable=True)
    resolved = Column(Integer, nullable=True)
    duration_sec = Column(Integer, nullable=True)


class CustomerScore(Base):
    __tablename__ = "customer_scores"

    customer_id = Column(String, primary_key=True)
    name = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    email = Column(String, nullable=True)
    region = Column(String, nullable=True)
    plan_tier = Column(String, nullable=True)
    contract_type = Column(String, nullable=True)
    payment_method = Column(String, nullable=True)
    tenure_months = Column(Integer, nullable=True)
    monthly_charges = Column(Float, nullable=True)
    total_charges = Column(Float, nullable=True)
    
    churn_probability = Column(Float, nullable=True)
    risk_tier = Column(String, nullable=True)
    priority_score = Column(Float, nullable=True)
    clv = Column(Float, nullable=True)
    
    usage_drop_call_pct = Column(Float, nullable=True)
    usage_drop_data_pct = Column(Float, nullable=True)
    support_calls_m1 = Column(Integer, nullable=True)
    
    cluster_id = Column(Integer, nullable=True)
    pca_x = Column(Float, nullable=True)
    pca_y = Column(Float, nullable=True)
    
    shap_json = Column(Text, nullable=True)
    recommendation_json = Column(Text, nullable=True)
    
    actioned = Column(Integer, nullable=True)
    actioned_at = Column(String, nullable=True)
