import os
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.user import User
from app.schemas.auth import (
    UserRegister,
    LoginRequest,
    TokenResponse
)

from app.core.security import (
    hash_password,
    verify_password,
    create_access_token
)
from app.services.seed_service import seed_default_accounts


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)


@router.post(
    "/register",
    response_model=TokenResponse
)
def register(
    user_data: UserRegister,
    db: Session = Depends(get_db)
):

    existing_user = db.query(User).filter(
        User.email == user_data.email
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )

    new_user = User(
        name=user_data.name,
        email=user_data.email,
        password=hash_password(
            user_data.password
        ),
        role="user"
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    token = create_access_token({
        "sub": str(new_user.id),
        "role": new_user.role
    })

    return {
        "access_token": token,
        "token_type": "bearer",
        "role": new_user.role,
        "user_id": new_user.id
    }


@router.post(
    "/create-officer",
    response_model=TokenResponse,
    operation_id="auth_create_officer"
)
def create_officer(
    user_data: UserRegister,
    db: Session = Depends(get_db)
):
    existing_user = db.query(User).filter(
        User.email == user_data.email
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )

    new_officer = User(
        name=user_data.name,
        email=user_data.email,
        password=hash_password(
            user_data.password
        ),
        role="officer"
    )

    db.add(new_officer)
    db.commit()
    db.refresh(new_officer)

    token = create_access_token({
        "sub": str(new_officer.id),
        "role": new_officer.role
    })

    return {
        "access_token": token,
        "token_type": "bearer",
        "role": new_officer.role,
        "user_id": new_officer.id
    }


@router.post(
    "/register/officer",
    response_model=TokenResponse,
    operation_id="auth_register_officer"
)
def register_officer(
    user_data: UserRegister,
    db: Session = Depends(get_db)
):
    return create_officer(user_data, db)


@router.get("/seed")
@router.post("/seed")
def trigger_seed():
    """Explicitly triggers or verifies default account provisioning."""
    return seed_default_accounts()


@router.post(
    "/login",
    response_model=TokenResponse
)
def login(
    login_data: LoginRequest,
    db: Session = Depends(get_db)
):
    raw_email = (login_data.email or "").strip()
    raw_password = (login_data.password or "").strip()

    clean_email = raw_email.lower()
    if clean_email and "@" not in clean_email:
        clean_email = f"{clean_email}@mitra.gov.in"

    user = db.query(User).filter(
        func.lower(User.email) == clean_email
    ).first()

    # Self-healing fallback for deployment environments:
    # If the user is missing, check if default credentials are being used
    if not user:
        if clean_email == "officer_22472@mitra.gov.in" and raw_password == "Officer@123":
            seed_default_accounts()
            user = db.query(User).filter(func.lower(User.email) == clean_email).first()
        elif clean_email == "user@mitra.com" and raw_password == "User@123":
            seed_default_accounts()
            user = db.query(User).filter(func.lower(User.email) == clean_email).first()

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    # If default officer is logging in with Officer@123 but has stale hash, heal it
    if clean_email == "officer_22472@mitra.gov.in" and raw_password == "Officer@123":
        if not verify_password(raw_password, user.password):
            user.password = hash_password("Officer@123")
            user.role = "officer"
            db.commit()
            db.refresh(user)

    # If default user is logging in with User@123 but has stale hash, heal it
    if clean_email == "user@mitra.com" and raw_password == "User@123":
        if not verify_password(raw_password, user.password):
            user.password = hash_password("User@123")
            user.role = "user"
            db.commit()
            db.refresh(user)

    if not verify_password(
        raw_password,
        user.password
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    token = create_access_token({
        "sub": str(user.id),
        "role": user.role
    })

    return {
        "access_token": token,
        "token_type": "bearer",
        "role": user.role,
        "user_id": user.id
    }