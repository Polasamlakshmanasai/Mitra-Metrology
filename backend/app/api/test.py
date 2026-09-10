from fastapi import APIRouter, Depends

from app.core.dependencies import (
    get_current_user,
    require_officer
)


router = APIRouter(
    prefix="/test",
    tags=["Testing"]
)


@router.get("/user")
def user_test(
    current_user=Depends(get_current_user)
):
    return {
        "message": "Authenticated successfully",
        "user": current_user
    }


@router.get("/officer")
def officer_test(
    current_user=Depends(require_officer)
):
    return {
        "message": "Officer access granted",
        "officer": current_user
    }