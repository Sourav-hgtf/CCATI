from sqlalchemy import Column, Integer, String, Text
from backend.app.db.base import Base

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    timestamp = Column(String, index=True, nullable=False)
    actor_email = Column(String, nullable=False)
    actor_role = Column(String, nullable=False)
    action = Column(String, nullable=False)
    target_resource = Column(String, nullable=False)
    details = Column(Text, nullable=True)
    request_id = Column(String, nullable=True)
    model_version = Column(String, nullable=True)
    event_type = Column(String, index=True, nullable=True)
    status = Column(String, index=True, default="SUCCESS")
