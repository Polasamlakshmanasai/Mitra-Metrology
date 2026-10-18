# app/database/mongo.py
"""
MongoDB Atlas Persistence Layer — Mitra Metrology 2.0.

Uses Motor (async MongoDB driver) with a shared client lifecycle
managed by FastAPI startup/shutdown events.

Usage:
    from app.database.mongo import get_mongo_db, is_mongo_enabled

    async def my_endpoint(mongo=Depends(get_mongo_db)):
        if mongo is not None:
            await mongo["scans"].insert_one({...})

Configuration:
    Set MONGODB_URI environment variable to a valid MongoDB connection string.
    Set DATABASE_NAME environment variable (default: mitra_metrology).

If MONGODB_URI is not set, all mongo functions return None gracefully
and the application falls back to SQLite/SQLAlchemy.
"""

import os
import logging
from typing import Optional

logger = logging.getLogger("mitra.mongo")

MONGODB_URI: Optional[str] = os.environ.get("MONGODB_URI", "").strip() or None
DATABASE_NAME: str = os.environ.get("DATABASE_NAME", "mitra_metrology").strip()

# Module-level client — shared across requests (Motor is thread-safe)
_mongo_client = None
_mongo_db = None


def is_mongo_enabled() -> bool:
    """Returns True if MONGODB_URI is configured."""
    return bool(MONGODB_URI)


async def connect_mongo() -> None:
    """
    Initialize the Motor client. Call this from FastAPI startup event.
    Safe to call even if MONGODB_URI is not set (no-op in that case).
    """
    global _mongo_client, _mongo_db

    if not MONGODB_URI:
        logger.info("[MongoDB] MONGODB_URI not set — MongoDB persistence disabled. Using SQLite.")
        return

    try:
        import motor.motor_asyncio as motor_async
        _mongo_client = motor_async.AsyncIOMotorClient(
            MONGODB_URI,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=5000,
            maxPoolSize=20,
            minPoolSize=2,
        )
        _mongo_db = _mongo_client[DATABASE_NAME]

        # Verify connection
        await _mongo_client.admin.command("ping")
        logger.info(f"[MongoDB] Connected to Atlas — database: {DATABASE_NAME}")

        # Ensure indexes
        await _ensure_indexes(_mongo_db)

    except ImportError:
        logger.warning("[MongoDB] motor package not installed. Run: pip install motor")
        _mongo_client = None
        _mongo_db = None
    except Exception as exc:
        logger.error(f"[MongoDB] Connection failed: {exc}. Falling back to SQLite.")
        _mongo_client = None
        _mongo_db = None


async def disconnect_mongo() -> None:
    """Close the Motor client. Call from FastAPI shutdown event."""
    global _mongo_client, _mongo_db
    if _mongo_client:
        _mongo_client.close()
        logger.info("[MongoDB] Connection closed.")
    _mongo_client = None
    _mongo_db = None


def get_mongo_db():
    """
    FastAPI dependency — yields the Motor database instance or None.

    Always check the returned value before using:
        if mongo is not None:
            await mongo["collection"].find_one(...)
    """
    return _mongo_db


async def _ensure_indexes(db) -> None:
    """
    Create required indexes on all collections.
    Uses create_index with background=True — safe to call repeatedly.
    """
    try:
        from pymongo import ASCENDING, DESCENDING

        # users — unique email
        await db["users"].create_index(
            [("email", ASCENDING)], unique=True, background=True
        )

        # scans — query by user, sort by date
        await db["scans"].create_index(
            [("user_id", ASCENDING), ("created_at", DESCENDING)], background=True
        )
        await db["scans"].create_index(
            [("created_at", DESCENDING)], background=True
        )

        # extracted_fields — lookup by scan
        await db["extracted_fields"].create_index(
            [("scan_id", ASCENDING)], background=True
        )
        await db["extracted_fields"].create_index(
            [("scan_id", ASCENDING), ("field_name", ASCENDING)], background=True
        )

        # violations — lookup by scan
        await db["violations"].create_index(
            [("scan_id", ASCENDING)], background=True
        )

        # complaints — query by user and status
        await db["complaints"].create_index(
            [("user_id", ASCENDING), ("created_at", DESCENDING)], background=True
        )
        await db["complaints"].create_index(
            [("status", ASCENDING)], background=True
        )

        # inspections — query by officer
        await db["inspections"].create_index(
            [("officer_id", ASCENDING), ("created_at", DESCENDING)], background=True
        )

        logger.info("[MongoDB] Indexes verified/created.")
    except Exception as exc:
        logger.warning(f"[MongoDB] Index creation warning: {exc}")
