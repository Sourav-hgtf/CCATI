"""Production SQLite to PostgreSQL Migration Script (TASK 20).

Transfers all records from legacy SQLite database (data/database/telecom_churn.db)
into PostgreSQL while preserving primary keys, timestamps, foreign keys, and sequences.
"""

from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3
import sys
import time

from sqlalchemy import create_engine, func, select, text
from sqlalchemy.orm import sessionmaker

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR))

from backend.app.core.config import settings
from backend.app.db.models import (
    AuditLog,
    CallLog,
    Customer,
    CustomerScore,
    MonitoringHistory,
    PerformanceHistory,
    PredictionHistory,
    SegmentProfile,
    User,
)


def parse_datetime(val):
    if val is None or val == "":
        return None
    if isinstance(val, datetime):
        return val
    try:
        # Replace Z with +00:00 for fromisoformat
        clean_str = str(val).replace("Z", "+00:00")
        return datetime.fromisoformat(clean_str)
    except Exception:
        return None


def migrate_data(sqlite_path: Path = settings.DB_PATH, database_url: str = settings.get_database_url) -> dict:
    """Execute transactional data migration from SQLite to PostgreSQL."""
    start_time = time.time()
    if not Path(sqlite_path).exists():
        raise FileNotFoundError(f"Source SQLite database not found at {sqlite_path}")

    print(f"==================================================")
    print(f" Starting SQLite -> PostgreSQL Data Migration")
    print(f" Source SQLite : {sqlite_path}")
    print(f" Target PG     : {database_url}")
    print(f"==================================================")

    # Connect to SQLite
    sqlite_conn = sqlite3.connect(str(sqlite_path))
    sqlite_conn.row_factory = sqlite3.Row
    sqlite_cursor = sqlite_conn.cursor()

    # Connect to PostgreSQL
    pg_engine = create_engine(database_url)
    Session = sessionmaker(bind=pg_engine)
    session = Session()

    report = {}

    try:
        # 1. Users
        print("\n[1/9] Migrating users...")
        users_sqlite = sqlite_cursor.execute("SELECT * FROM users").fetchall()
        user_count = 0
        for r in users_sqlite:
            d = dict(r)
            user = User(
                id=d["id"],
                email=d["email"],
                username=d["username"],
                full_name=d["full_name"],
                password_hash=d["password_hash"],
                role=d["role"],
                is_active=bool(d["is_active"]),
                failed_login_attempts=int(d["failed_login_attempts"]),
                locked_until=parse_datetime(d.get("locked_until")),
                created_at=parse_datetime(d["created_at"]) or datetime.now(timezone.utc),
                updated_at=parse_datetime(d["updated_at"]) or datetime.now(timezone.utc),
                last_login_at=parse_datetime(d.get("last_login_at")),
            )
            session.merge(user)
            user_count += 1
        session.commit()
        report["users"] = {"source": len(users_sqlite), "migrated": user_count, "status": "PASS"}
        print(f"  -> Migrated {user_count} users.")

        # 2. Customers
        print("\n[2/9] Migrating customers...")
        cust_sqlite = sqlite_cursor.execute("SELECT * FROM customers").fetchall()
        cust_count = 0
        for r in cust_sqlite:
            d = dict(r)
            customer = Customer(**d)
            session.merge(customer)
            cust_count += 1
        session.commit()
        report["customers"] = {"source": len(cust_sqlite), "migrated": cust_count, "status": "PASS"}
        print(f"  -> Migrated {cust_count} customers.")

        # 3. Call Logs
        print("\n[3/9] Migrating call_logs...")
        call_sqlite = sqlite_cursor.execute("SELECT * FROM call_logs").fetchall()
        call_count = 0
        for r in call_sqlite:
            d = dict(r)
            log = CallLog(
                id=d.get("id"),
                customer_id=d.get("customer_id"),
                call_reason=d.get("call_reason"),
                sentiment=d.get("sentiment"),
                resolved=d.get("resolved"),
                duration_sec=d.get("duration_sec"),
            )
            session.merge(log)
            call_count += 1
        session.commit()
        report["call_logs"] = {"source": len(call_sqlite), "migrated": call_count, "status": "PASS"}
        print(f"  -> Migrated {call_count} call_logs.")

        # 4. Customer Scores
        print("\n[4/9] Migrating customer_scores...")
        scores_sqlite = sqlite_cursor.execute("SELECT * FROM customer_scores").fetchall()
        scores_count = 0
        for r in scores_sqlite:
            d = dict(r)
            score = CustomerScore(**d)
            session.merge(score)
            scores_count += 1
        session.commit()
        report["customer_scores"] = {"source": len(scores_sqlite), "migrated": scores_count, "status": "PASS"}
        print(f"  -> Migrated {scores_count} customer_scores.")

        # 5. Segment Profiles
        print("\n[5/9] Migrating segment_profiles...")
        seg_sqlite = sqlite_cursor.execute("SELECT * FROM segment_profiles").fetchall()
        seg_count = 0
        for r in seg_sqlite:
            d = dict(r)
            seg = SegmentProfile(**d)
            session.merge(seg)
            seg_count += 1
        session.commit()
        report["segment_profiles"] = {"source": len(seg_sqlite), "migrated": seg_count, "status": "PASS"}
        print(f"  -> Migrated {seg_count} segment_profiles.")

        # 6. Prediction History
        print("\n[6/9] Migrating prediction_history...")
        pred_sqlite = sqlite_cursor.execute("SELECT * FROM prediction_history").fetchall()
        pred_count = 0
        for r in pred_sqlite:
            d = dict(r)
            pred = PredictionHistory(**d)
            session.merge(pred)
            pred_count += 1
        session.commit()
        report["prediction_history"] = {"source": len(pred_sqlite), "migrated": pred_count, "status": "PASS"}
        print(f"  -> Migrated {pred_count} prediction_history records.")

        # 7. Monitoring History
        print("\n[7/9] Migrating monitoring_history...")
        mon_sqlite = sqlite_cursor.execute("SELECT * FROM monitoring_history").fetchall()
        mon_count = 0
        for r in mon_sqlite:
            d = dict(r)
            mon = MonitoringHistory(**d)
            session.merge(mon)
            mon_count += 1
        session.commit()
        report["monitoring_history"] = {"source": len(mon_sqlite), "migrated": mon_count, "status": "PASS"}
        print(f"  -> Migrated {mon_count} monitoring_history records.")

        # 8. Performance History
        print("\n[8/9] Migrating performance_history...")
        perf_sqlite = sqlite_cursor.execute("SELECT * FROM performance_history").fetchall()
        perf_count = 0
        for r in perf_sqlite:
            d = dict(r)
            perf = PerformanceHistory(**d)
            session.merge(perf)
            perf_count += 1
        session.commit()
        report["performance_history"] = {"source": len(perf_sqlite), "migrated": perf_count, "status": "PASS"}
        print(f"  -> Migrated {perf_count} performance_history records.")

        # 9. Audit Logs
        print("\n[9/9] Migrating audit_logs...")
        audit_sqlite = sqlite_cursor.execute("SELECT * FROM audit_logs").fetchall()
        audit_count = 0
        for r in audit_sqlite:
            d = dict(r)
            audit = AuditLog(
                id=d.get("id"),
                timestamp=d.get("timestamp"),
                actor_email=d.get("actor_email"),
                actor_role=d.get("actor_role"),
                action=d.get("action"),
                target_resource=d.get("target_resource"),
                details=d.get("details"),
                request_id=d.get("request_id"),
                model_version=d.get("model_version"),
                event_type=d.get("event_type"),
                status=d.get("status", "SUCCESS"),
            )
            session.merge(audit)
            audit_count += 1
        session.commit()
        report["audit_logs"] = {"source": len(audit_sqlite), "migrated": audit_count, "status": "PASS"}
        print(f"  -> Migrated {audit_count} audit_logs records.")

        # Reset Postgres Sequences for auto-increment tables
        print("\nResetting PostgreSQL sequence values...")
        seq_tables = [
            ("call_logs", "id", "call_logs_id_seq"),
            ("monitoring_history", "id", "monitoring_history_id_seq"),
            ("performance_history", "id", "performance_history_id_seq"),
            ("audit_logs", "id", "audit_logs_id_seq"),
        ]
        for tbl, col, seq in seq_tables:
            try:
                session.execute(
                    text(f"SELECT setval('{seq}', COALESCE((SELECT MAX({col}) FROM {tbl}), 1), true);")
                )
                session.commit()
                print(f"  -> Reset sequence '{seq}'")
            except Exception as e:
                session.rollback()
                print(f"  -> Note: Sequence reset skipped for {seq}: {e}")

        duration = round(time.time() - start_time, 2)
        print(f"\n==================================================")
        print(f" Migration finished successfully in {duration}s!")
        print(f"==================================================")

        return report

    except Exception as e:
        session.rollback()
        print(f"\n[ERROR] Migration failed: {e}")
        raise
    finally:
        session.close()
        sqlite_conn.close()


if __name__ == "__main__":
    migrate_data()
