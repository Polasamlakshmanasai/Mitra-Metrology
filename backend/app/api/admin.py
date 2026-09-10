from fastapi import APIRouter

router = APIRouter(
    prefix="/admin",
    tags=["Admin"]
)


@router.get("/")
def admin_root():
    return {"message": "Admin module ready"}
