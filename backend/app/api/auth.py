from fastapi import APIRouter, Depends, HTTPException
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


@router.post(
    "/login",
    response_model=TokenResponse
)
def login(
    login_data: LoginRequest,
    db: Session = Depends(get_db)
):

    user = db.query(User).filter(
        User.email == login_data.email
    ).first()

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    if not verify_password(
        login_data.password,
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