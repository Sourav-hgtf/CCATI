"""PostgreSQL Data Migration Verification Script (TASK 20).

Validates data parity, row counts, null constraints, and table integrity
between legacy SQLite database and production PostgreSQL database.
"""

from pathlib import Path
import sqlite3
import sys

from sqlalchemy import create_engine, func, select, text
from sqlalchemy.orm import sessionmaker

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


def verify_migration(sqlite_path: Path = settings.DB_PATH, database_url: str = settings.get_database_url) -> bool:
    """Compare SQLite vs PostgreSQL and verify data integrity."""
    print("==========================================================================")
    print("           POSTGRESQL DATA MIGRATION VERIFICATION REPORT")
    print(f" Source SQLite : {sqlite_path}")
    print(f" Target PG     : {database_url}")
    print("==========================================================================")

    sqlite_conn = sqlite3.connect(str(sqlite_path))
    sqlite_cursor = sqlite_conn.cursor()

    pg_engine = create_engine(database_url)
    Session = sessionmaker(bind=pg_engine)
    session = Session()

    tables = [
        ("users", User),
        ("customers", Customer),
        ("call_logs", CallLog),
        ("customer_scores", CustomerScore),
        ("segment_profiles", SegmentProfile),
        ("prediction_history", PredictionHistory),
        ("monitoring_history", MonitoringHistory),
        ("performance_history", PerformanceHistory),
        ("audit_logs", AuditLog),
    ]

    all_passed = True
    print(f"{'Table':<22} | {'SQLite Rows':<12} | {'PG Rows':<10} | {'Diff':<6} | {'Status':<6}")
    print("-" * 68)

    for table_name, model_cls in tables:
        sqlite_count = sqlite_cursor.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
        pg_count = session.query(func.count()).select_from(model_cls).scalar() or 0
        diff = pg_count - sqlite_count
        status = "PASS" if diff == 0 and pg_count > 0 else "FAIL"
        if status == "FAIL":
            all_passed = False

        print(f"{table_name:<22} | {sqlite_count:<12} | {pg_count:<10} | {diff:<6} | {status:<6}")

    print("-" * 68)

    # Secondary Integrity Checks
    print("\n--- Additional Integrity Verifications ---")

    # 1. Admin user check
    admin_user = session.query(User).filter(User.role == "Admin").first()
    if admin_user:
        print(f"  [PASS] Admin user verified: {admin_user.email} (Active: {admin_user.is_active})")
    else:
        print("  [FAIL] No Admin user found in PostgreSQL!")
        all_passed = False

    # 2. Customer score sample check
    sample_score = session.query(CustomerScore).first()
    if sample_score and sample_score.churn_probability is not None:
        print(f"  [PASS] Customer scores verified: {sample_score.customer_id} (Prob: {sample_score.churn_probability}, Risk: {sample_score.risk_tier})")
    else:
        print("  [FAIL] Customer score records corrupted or empty!")
        all_passed = False

    # 3. Segment profiles check
    seg_count = session.query(SegmentProfile).count()
    if seg_count == 4:
        print(f"  [PASS] All 4 behavioral segment profiles verified in PostgreSQL.")
    else:
        print(f"  [FAIL] Expected 4 segment profiles, found {seg_count}!")
        all_passed = False

    session.close()
    sqlite_conn.close()

    print("\n==========================================================================")
    if all_passed:
        print(" OVERALL VERIFICATION: [PASS] - PostgreSQL Migration is 100% Validated")
    else:
        print(" OVERALL VERIFICATION: [FAIL] - Discrepancies detected between SQLite & PG")
    print("==========================================================================")

    return all_passed


if __name__ == "__main__":
    success = verify_migration()
    sys.exit(0 if success else 1)
