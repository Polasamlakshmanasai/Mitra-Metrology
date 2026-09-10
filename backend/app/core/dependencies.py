from typing import Optional
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError

from app.core.security import SECRET_KEY, ALGORITHM


security = HTTPBearer()
security_optional = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    token = credentials.credentials

    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        user_id = payload.get("sub")
        role = payload.get("role")

        if not user_id or not role:
            raise HTTPException(
                status_code=401,
                detail="Invalid token"
            )

        return {
            "user_id": int(user_id),
            "role": role
        }

    except JWTError:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token"
        )


def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_optional)
):
    if not credentials:
        return {
            "user_id": 1,
            "role": "user"
        }

    try:
        return get_current_user(credentials)
    except HTTPException:
        return {
            "user_id": 1,
            "role": "user"
        }


def require_officer(
    current_user=Depends(get_current_user)
):
    if current_user["role"] != "officer":
        raise HTTPException(
            status_code=403,
            detail="Officer access required"
        )

    return current_user