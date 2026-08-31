from sqlalchemy.orm import Session
from backend.app.db.models.prediction import PredictionHistory
import json

class PredictionRepository:
    def __init__(self, db: Session):
        self.db = db

    def save_prediction(
        self,
        prediction_id: str,
        customer_id: str,
        churn_probability: float,
        prediction: int,
        risk_tier: str,
        confidence_score: float,
        threshold: float,
        model_name: str,
        model_version: str,
        prediction_timestamp: str,
        recommended_action: str = None,
        explanation_json: dict = None
    ) -> PredictionHistory:
        hist = PredictionHistory(
            prediction_id=prediction_id,
            customer_id=customer_id,
            churn_probability=churn_probability,
            prediction=prediction,
            risk_tier=risk_tier,
            confidence_score=confidence_score,
            threshold=threshold,
            model_name=model_name,
            model_version=model_version,
            prediction_timestamp=prediction_timestamp,
            recommended_action=recommended_action,
            explanation_json=json.dumps(explanation_json) if explanation_json else None
        )
        self.db.add(hist)
        self.db.commit()
        self.db.refresh(hist)
        return hist
        
    def get_recent_predictions(self, limit: int = 1000):
        return self.db.query(PredictionHistory).order_by(PredictionHistory.prediction_timestamp.desc()).limit(limit).all()
        
    def get_by_customer_id(self, customer_id: str):
        return self.db.query(PredictionHistory).filter(PredictionHistory.customer_id == customer_id).order_by(PredictionHistory.prediction_timestamp.desc()).all()
