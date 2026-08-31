from sqlalchemy import Column, Integer, String, Float, Text
from backend.app.db.base import Base

class PredictionHistory(Base):
    __tablename__ = "prediction_history"

    prediction_id = Column(String, primary_key=True)
    customer_id = Column(String, index=True, nullable=False)
    churn_probability = Column(Float, nullable=False)
    prediction = Column(Integer, nullable=False)
    risk_tier = Column(String, index=True, nullable=False)
    confidence_score = Column(Float, nullable=False)
    threshold = Column(Float, nullable=False, default=0.50)
    model_name = Column(String, nullable=False)
    model_version = Column(String, nullable=False)
    prediction_timestamp = Column(String, index=True, nullable=False)
    recommended_action = Column(String, nullable=True)
    explanation_json = Column(Text, nullable=True)
