# app/services/seed_service.py
"""
Automatic database seeding service for Mitra Metrology.
Guarantees that default officer and citizen accounts are provisioned
both on local machines and on cloud deployments (Render, Docker, etc.).
"""

import logging
from sqlalchemy import func
from app.database.connection import SessionLocal
from app.models.user import User
from app.core.security import hash_password, verify_password

logger = logging.getLogger("mitra.seed")

DEFAULT_ACCOUNTS = [
    {
        "name": "Legal Metrology Inspector",
        "email": "officer_22472@mitra.gov.in",
        "password": "Officer@123",
        "role": "officer"
    },
    {
        "name": "Citizen User",
        "email": "user@mitra.com",
        "password": "User@123",
        "role": "user"
    }
]


def seed_default_accounts():
    """
    Idempotently seeds or repairs the default accounts.
    If an account exists, verifies that its password and role are correct;
    if not or mismatched, updates them to ensure login works without failure.
    """
    db = SessionLocal()
    results = []
    try:
        for acc in DEFAULT_ACCOUNTS:
            email_lower = acc["email"].strip().lower()
            existing_user = db.query(User).filter(
                func.lower(User.email) == email_lower
            ).first()

            if not existing_user:
                new_user = User(
                    name=acc["name"],
                    email=acc["email"],
                    password=hash_password(acc["password"]),
                    role=acc["role"]
                )
                db.add(new_user)
                db.commit()
                db.refresh(new_user)
                results.append({"email": acc["email"], "role": acc["role"], "action": "created"})
                logger.info(f"Created default account: {acc['email']} ({acc['role']})")
            else:
                updated = False
                # Ensure correct role
                if existing_user.role != acc["role"]:
                    existing_user.role = acc["role"]
                    updated = True

                # Ensure password hash matches
                if not verify_password(acc["password"], existing_user.password):
                    existing_user.password = hash_password(acc["password"])
                    updated = True

                if updated:
                    db.commit()
                    results.append({"email": acc["email"], "role": acc["role"], "action": "repaired"})
                    logger.info(f"Repaired default account credentials: {acc['email']}")
                else:
                    results.append({"email": acc["email"], "role": acc["role"], "action": "already_valid"})

        return {"status": "success", "accounts": results}
    except Exception as e:
        db.rollback()
        logger.error(f"Error during default account seeding: {e}")
        return {"status": "error", "message": str(e)}
    finally:
        db.close()
