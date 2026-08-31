from sqlalchemy import Column, Integer, String, Float, Text
from backend.app.db.base import Base

class MonitoringHistory(Base):
    __tablename__ = "monitoring_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    monitoring_id = Column(String, unique=True, nullable=False)
    timestamp = Column(String, nullable=False)
    model_name = Column(String, nullable=False)
    model_version = Column(String, nullable=False)
    overall_status = Column(String, nullable=False)
    overall_score = Column(Float, nullable=False)
    features_checked = Column(Integer, nullable=False)
    features_drifted = Column(Integer, nullable=False)
    report_json = Column(Text, nullable=False)

class PerformanceHistory(Base):
    __tablename__ = "performance_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    performance_id = Column(String, unique=True, nullable=False)
    timestamp = Column(String, nullable=False)
    model_name = Column(String, nullable=False)
    model_version = Column(String, nullable=False)
    status = Column(String, nullable=False)
    precision = Column(Float, nullable=False)
    recall = Column(Float, nullable=False)
    f1 = Column(Float, nullable=False)
    roc_auc = Column(Float, nullable=False)
    pr_auc = Column(Float, nullable=False)
    report_json = Column(Text, nullable=False)
