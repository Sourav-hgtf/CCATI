from sqlalchemy.orm import Session
from backend.app.db.models.monitoring import MonitoringHistory, PerformanceHistory
import json

class MonitoringRepository:
    def __init__(self, db: Session):
        self.db = db

    def save_drift_report(
        self,
        monitoring_id: str,
        timestamp: str,
        model_name: str,
        model_version: str,
        overall_status: str,
        overall_score: float,
        features_checked: int,
        features_drifted: int,
        report_json: dict
    ) -> MonitoringHistory:
        hist = MonitoringHistory(
            monitoring_id=monitoring_id,
            timestamp=timestamp,
            model_name=model_name,
            model_version=model_version,
            overall_status=overall_status,
            overall_score=overall_score,
            features_checked=features_checked,
            features_drifted=features_drifted,
            report_json=json.dumps(report_json)
        )
        self.db.add(hist)
        self.db.commit()
        self.db.refresh(hist)
        return hist
        
    def get_recent_drift_reports(self, limit: int = 10):
        return self.db.query(MonitoringHistory).order_by(MonitoringHistory.timestamp.desc()).limit(limit).all()

class PerformanceRepository:
    def __init__(self, db: Session):
        self.db = db

    def save_performance_report(
        self,
        performance_id: str,
        timestamp: str,
        model_name: str,
        model_version: str,
        status: str,
        precision: float,
        recall: float,
        f1: float,
        roc_auc: float,
        pr_auc: float,
        report_json: dict
    ) -> PerformanceHistory:
        hist = PerformanceHistory(
            performance_id=performance_id,
            timestamp=timestamp,
            model_name=model_name,
            model_version=model_version,
            status=status,
            precision=precision,
            recall=recall,
            f1=f1,
            roc_auc=roc_auc,
            pr_auc=pr_auc,
            report_json=json.dumps(report_json)
        )
        self.db.add(hist)
        self.db.commit()
        self.db.refresh(hist)
        return hist
        
    def get_recent_performance_reports(self, limit: int = 10):
        return self.db.query(PerformanceHistory).order_by(PerformanceHistory.timestamp.desc()).limit(limit).all()
