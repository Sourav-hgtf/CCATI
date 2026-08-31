from backend.app.db.base import Base
from backend.app.db.models.audit import AuditLog
from backend.app.db.models.prediction import PredictionHistory
from backend.app.db.models.monitoring import MonitoringHistory, PerformanceHistory
from backend.app.db.models.customer import Customer, CallLog, CustomerScore
from backend.app.db.models.segment import SegmentProfile
from backend.app.db.models.user import User

# Export all models so Alembic can discover them
__all__ = [
    "Base",
    "AuditLog",
    "PredictionHistory",
    "MonitoringHistory",
    "PerformanceHistory",
    "Customer",
    "CallLog",
    "CustomerScore",
    "SegmentProfile",
    "User",
]
