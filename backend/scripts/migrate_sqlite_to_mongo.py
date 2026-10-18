#!/usr/bin/env python3
"""
migrate_sqlite_to_mongo.py — SQLite → MongoDB Atlas migration script.

Usage:
    # Dry run (check counts, no writes):
    python backend/scripts/migrate_sqlite_to_mongo.py --dry-run

    # Migrate to dev database:
    MONGODB_URI="mongodb+srv://..." DATABASE_NAME=mitra_dev python backend/scripts/migrate_sqlite_to_mongo.py

    # Full migration:
    MONGODB_URI="mongodb+srv://..." DATABASE_NAME=mitra_metrology python backend/scripts/migrate_sqlite_to_mongo.py

Safety:
    - Does NOT delete the SQLite database.
    - Uses upsert (update_one with upsert=True) — safe to re-run.
    - Prints a summary before any writes.
    - Verify record counts match before marking migration successful.

Prerequisites:
    pip install motor pymongo sqlalchemy
    MONGODB_URI environment variable must be set.
"""

import asyncio
import os
import sys
import argparse
import json
from pathlib import Path
from datetime import datetime, timezone

# Add project root to path
SCRIPT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = SCRIPT_DIR.parent
PROJECT_ROOT = BACKEND_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(BACKEND_DIR))

MONGODB_URI = os.environ.get("MONGODB_URI", "").strip()
DATABASE_NAME = os.environ.get("DATABASE_NAME", "mitra_metrology").strip()


def _get_sqlite_session():
    """Returns a SQLAlchemy session connected to the existing SQLite DB."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    db_path = BACKEND_DIR / "mitra.db"
    if not db_path.exists():
        raise FileNotFoundError(f"SQLite database not found: {db_path}")

    engine = create_engine(f"sqlite:///{db_path.as_posix()}", connect_args={"check_same_thread": False})
    Session = sessionmaker(bind=engine)
    return Session()


def _to_iso(dt):
    if dt is None:
        return None
    if isinstance(dt, datetime):
        return dt.isoformat()
    return str(dt)


def _migrate_users(db_session, mongo_col, dry_run: bool) -> tuple[int, int]:
    from app.models.user import User

    rows = db_session.query(User).all()
    migrated = skipped = 0

    for u in rows:
        doc = {
            "_sqlite_id": u.id,
            "name": u.name,
            "email": u.email,
            "password": u.password,
            "role": u.role,
            "created_at": _to_iso(u.created_at),
        }
        if not dry_run:
            mongo_col.update_one(
                {"email": u.email},
                {"$set": doc},
                upsert=True,
            )
            migrated += 1
        else:
            migrated += 1

    return migrated, skipped


def _migrate_scans(db_session, mongo_col, dry_run: bool) -> tuple[int, int]:
    from app.models.scan import Scan

    rows = db_session.query(Scan).all()
    migrated = 0

    for s in rows:
        doc = {
            "_sqlite_id": s.id,
            "user_id": s.user_id,
            "image_path": s.image_path,
            "status": s.status,
            "score": s.score,
            "user_confirmed": getattr(s, "user_confirmed", False),
            "confirmed_at": _to_iso(getattr(s, "confirmed_at", None)),
            "quality_override": getattr(s, "quality_override", False),
            "quality_tier": getattr(s, "quality_tier", None),
            "has_quality_warning": getattr(s, "has_quality_warning", False),
            "is_food_product": getattr(s, "is_food_product", False),
            "rules_checked": getattr(s, "rules_checked", None),
            "violation_count": getattr(s, "violation_count", None),
            "created_at": _to_iso(s.created_at),
        }
        if not dry_run:
            mongo_col.update_one(
                {"_sqlite_id": s.id},
                {"$set": doc},
                upsert=True,
            )
        migrated += 1

    return migrated, 0


def _migrate_extracted_fields(db_session, mongo_col, dry_run: bool) -> tuple[int, int]:
    from app.models.extracted_field import ExtractedField

    rows = db_session.query(ExtractedField).all()
    migrated = 0

    for f in rows:
        doc = {
            "_sqlite_id": f.id,
            "scan_id": f.scan_id,
            "field_name": f.field_name,
            "field_value": f.field_value,
            "original_ocr_value": getattr(f, "original_ocr_value", f.field_value),
            "corrected_value": getattr(f, "corrected_value", None),
            "confidence": f.confidence,
            "bounding_box": f.bounding_box,
            "correction_status": getattr(f, "correction_status", "ocr_original"),
            "corrected_at": _to_iso(getattr(f, "corrected_at", None)),
            "corrected_by_user_id": getattr(f, "corrected_by_user_id", None),
            "ocr_source_variant": getattr(f, "ocr_source_variant", None),
            "field_status": getattr(f, "field_status", None),
            "created_at": _to_iso(getattr(f, "created_at", None)),
        }
        if not dry_run:
            mongo_col.update_one(
                {"_sqlite_id": f.id},
                {"$set": doc},
                upsert=True,
            )
        migrated += 1

    return migrated, 0


def _migrate_violations(db_session, mongo_col, dry_run: bool) -> tuple[int, int]:
    from app.models.violation import Violation

    rows = db_session.query(Violation).all()
    migrated = 0

    for v in rows:
        doc = {
            "_sqlite_id": v.id,
            "scan_id": v.scan_id,
            "field": v.field,
            "description": v.description,
            "severity": v.severity,
            "evidence_path": v.evidence_path,
        }
        if not dry_run:
            mongo_col.update_one(
                {"_sqlite_id": v.id},
                {"$set": doc},
                upsert=True,
            )
        migrated += 1

    return migrated, 0


def _migrate_complaints(db_session, mongo_col, dry_run: bool) -> tuple[int, int]:
    from app.models.complaint import Complaint

    rows = db_session.query(Complaint).all()
    migrated = 0

    for c in rows:
        doc = {
            "_sqlite_id": c.id,
            "scan_id": c.scan_id,
            "user_id": c.user_id,
            "product_name": c.product_name,
            "manufacturer": c.manufacturer,
            "violation_type": c.violation_type,
            "description": c.description,
            "status": c.status,
            "created_at": _to_iso(c.created_at),
        }
        if not dry_run:
            mongo_col.update_one(
                {"_sqlite_id": c.id},
                {"$set": doc},
                upsert=True,
            )
        migrated += 1

    return migrated, 0


async def run_migration(dry_run: bool):
    if not MONGODB_URI:
        print("ERROR: MONGODB_URI environment variable is not set.")
        print("       Export it before running this script.")
        sys.exit(1)

    print(f"\n{'='*60}")
    print(f"  Mitra Metrology — SQLite → MongoDB Migration")
    print(f"  Database: {DATABASE_NAME}")
    print(f"  Mode: {'DRY RUN (no writes)' if dry_run else 'LIVE MIGRATION'}")
    print(f"{'='*60}\n")

    # Connect to MongoDB
    try:
        import motor.motor_asyncio as motor_async
        client = motor_async.AsyncIOMotorClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
        await client.admin.command("ping")
        db_mongo = client[DATABASE_NAME]
        print(f"[OK] MongoDB Atlas connected — database: {DATABASE_NAME}")
    except Exception as exc:
        print(f"[FAIL] MongoDB connection failed: {exc}")
        sys.exit(1)

    # Connect to SQLite
    try:
        db_sqlite = _get_sqlite_session()
        print("[OK] SQLite connected")
    except Exception as exc:
        print(f"[FAIL] SQLite connection failed: {exc}")
        sys.exit(1)

    # Run each collection migration synchronously using run_in_executor
    # (SQLAlchemy is synchronous, Motor is async — we bridge them here)
    import asyncio

    loop = asyncio.get_event_loop()

    collections = [
        ("users",            _migrate_users),
        ("scans",            _migrate_scans),
        ("extracted_fields", _migrate_extracted_fields),
        ("violations",       _migrate_violations),
        ("complaints",       _migrate_complaints),
    ]

    results = {}
    for col_name, fn in collections:
        # Get sync collection from pymongo for upserts in sync code
        if not dry_run:
            sync_col = client.get_io_loop()  # not used directly
            # Use pymongo sync client for sync upserts
            import pymongo
            sync_client = pymongo.MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
            sync_col = sync_client[DATABASE_NAME][col_name]
        else:
            sync_col = None

        try:
            migrated, skipped = await loop.run_in_executor(
                None, fn, db_sqlite, sync_col, dry_run
            )
            results[col_name] = {"migrated": migrated, "skipped": skipped}
            status = "DRY" if dry_run else "OK"
            print(f"  [{status}] {col_name}: {migrated} records {'would be ' if dry_run else ''}migrated")
        except Exception as exc:
            print(f"  [ERROR] {col_name}: {exc}")
            results[col_name] = {"error": str(exc)}

    # Verify record counts in MongoDB (only in live mode)
    if not dry_run:
        print(f"\n{'='*60}")
        print("  Post-migration count verification:")
        print(f"{'='*60}")
        all_match = True
        for col_name in [c[0] for c in collections]:
            expected = results.get(col_name, {}).get("migrated", 0)
            actual = await db_mongo[col_name].count_documents({})
            match = actual >= expected
            if not match:
                all_match = False
            icon = "[OK]" if match else "[WARN]"
            print(f"  {icon} {col_name}: expected>={expected}, found={actual}")

        if all_match:
            print("\n  ✓ All record counts verified. Migration successful.")
        else:
            print("\n  ⚠ Count mismatch detected. Review before switching to MongoDB.")

    db_sqlite.close()
    client.close()
    print("\nMigration script complete.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Migrate Mitra Metrology SQLite data to MongoDB Atlas")
    parser.add_argument("--dry-run", action="store_true", help="Count records without writing to MongoDB")
    args = parser.parse_args()

    asyncio.run(run_migration(dry_run=args.dry_run))
