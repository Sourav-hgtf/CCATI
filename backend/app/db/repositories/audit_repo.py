from sqlalchemy.orm import Session
from backend.app.db.models.audit import AuditLog
import datetime

class AuditRepository:
    def __init__(self, db: Session):
        self.db = db
        
    def create_log(
        self,
        actor_email: str,
        actor_role: str,
        action: str,
        target_resource: str,
        details: str = None,
        request_id: str = None,
        model_version: str = None,
        event_type: str = "SYSTEM_EVENT",
        status: str = "SUCCESS",
    ) -> AuditLog:
        log = AuditLog(
            timestamp=datetime.datetime.utcnow().isoformat() + "Z",
            actor_email=actor_email,
            actor_role=actor_role,
            action=action,
            target_resource=target_resource,
            details=details,
            request_id=request_id,
            model_version=model_version,
            event_type=event_type,
            status=status,
        )
        self.db.add(log)
        self.db.commit()
        self.db.refresh(log)
        return log
        
    def get_logs(self, limit: int = 100):
        return self.db.query(AuditLog).order_by(AuditLog.timestamp.desc()).limit(limit).all()
        
    def delete_old_logs(self, retention_days: int) -> int:
        cutoff = (datetime.datetime.utcnow() - datetime.timedelta(days=retention_days)).isoformat()
        deleted = self.db.query(AuditLog).filter(AuditLog.timestamp < cutoff).delete()
        self.db.commit()
        return deleted
