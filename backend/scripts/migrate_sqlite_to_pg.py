import sqlite3
import json
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.core.config import settings
from backend.app.db.models.audit import AuditLog
from backend.app.db.models.prediction import PredictionHistory
from backend.app.db.models.monitoring import MonitoringHistory, PerformanceHistory
from backend.app.db.models.customer import Customer, CallLog, CustomerScore
from backend.app.db.models.segment import SegmentProfile

# Ensure we're connecting to PG
pg_engine = create_engine("postgresql+psycopg2://postgres:postgres@localhost:5432/telecom_churn")
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=pg_engine)

def migrate():
    sqlite_conn = sqlite3.connect("data/database/telecom_churn.db")
    sqlite_conn.row_factory = sqlite3.Row
    cursor = sqlite_conn.cursor()
    
    db = SessionLocal()
    
    try:
        # Migrate Customers
        print("Migrating customers...")
        rows = cursor.execute("SELECT * FROM customers").fetchall()
        for r in rows:
            c = Customer(**dict(r))
            db.merge(c)
            
        # Migrate Customer Scores
        print("Migrating customer_scores...")
        rows = cursor.execute("SELECT * FROM customer_scores").fetchall()
        for r in rows:
            c = CustomerScore(**dict(r))
            db.merge(c)
            
        # Migrate Call Logs
        print("Migrating call_logs...")
        rows = cursor.execute("SELECT * FROM call_logs").fetchall()
        for r in rows:
            c = CallLog(**dict(r))
            db.merge(c)
            
        # Migrate Segment Profiles
        print("Migrating segment_profiles...")
        rows = cursor.execute("SELECT * FROM segment_profiles").fetchall()
        for r in rows:
            c = SegmentProfile(**dict(r))
            db.merge(c)
            
        # Migrate Prediction History
        print("Migrating prediction_history...")
        rows = cursor.execute("SELECT * FROM prediction_history").fetchall()
        for r in rows:
            c = PredictionHistory(**dict(r))
            db.merge(c)
            
        # Migrate Audit Logs
        print("Migrating audit_logs...")
        rows = cursor.execute("SELECT * FROM audit_logs").fetchall()
        for r in rows:
            c = AuditLog(**dict(r))
            db.merge(c)
            
        db.commit()
        print("Migration complete!")
    except Exception as e:
        db.rollback()
        print(f"Migration failed: {e}")
    finally:
        db.close()
        sqlite_conn.close()

if __name__ == "__main__":
    migrate()
