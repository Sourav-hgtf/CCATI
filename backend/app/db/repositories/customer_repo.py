from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.app.db.models.customer import Customer, CustomerScore, CallLog

class CustomerRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_customer(self, customer_id: str) -> Customer:
        return self.db.query(Customer).filter(Customer.customer_id == customer_id).first()

    def get_customer_score(self, customer_id: str) -> CustomerScore:
        return self.db.query(CustomerScore).filter(CustomerScore.customer_id == customer_id).first()

    def get_all_customers(self, limit: int = 1000):
        return self.db.query(Customer).limit(limit).all()
        
    def get_all_customer_scores(self, limit: int = 1000, offset: int = 0):
        return self.db.query(CustomerScore).limit(limit).offset(offset).all()

    def get_customer_call_logs(self, customer_id: str):
        return self.db.query(CallLog).filter(CallLog.customer_id == customer_id).all()

    def search_customer_scores(self, search: str, risk_tier: str, limit: int = 100, offset: int = 0):
        query = self.db.query(CustomerScore)
        if search:
            query = query.filter(
                (CustomerScore.customer_id.ilike(f"%{search}%")) |
                (CustomerScore.name.ilike(f"%{search}%")) |
                (CustomerScore.email.ilike(f"%{search}%"))
            )
        if risk_tier and risk_tier.lower() != "all":
            query = query.filter(CustomerScore.risk_tier == risk_tier)
            
        return query.limit(limit).offset(offset).all()

    def get_customer_scores_count(self, search: str = None, risk_tier: str = None) -> int:
        query = self.db.query(func.count(CustomerScore.customer_id))
        if search:
            query = query.filter(
                (CustomerScore.customer_id.ilike(f"%{search}%")) |
                (CustomerScore.name.ilike(f"%{search}%")) |
                (CustomerScore.email.ilike(f"%{search}%"))
            )
        if risk_tier and risk_tier.lower() != "all":
            query = query.filter(CustomerScore.risk_tier == risk_tier)
            
        return query.scalar() or 0

    def get_risk_tier_distribution(self):
        result = self.db.query(CustomerScore.risk_tier, func.count(CustomerScore.customer_id)).group_by(CustomerScore.risk_tier).all()
        return {r[0]: r[1] for r in result if r[0] is not None}
        
    def get_average_churn_probability(self):
        return self.db.query(func.avg(CustomerScore.churn_probability)).scalar() or 0.0

    def update_customer_score(self, score: CustomerScore):
        # We assume the object is already attached to the session if fetched via get_customer_score
        self.db.add(score)
        self.db.commit()
        self.db.refresh(score)
        return score
        
    def execute_raw(self, stmt, params=None):
        return self.db.execute(stmt, params or {})
