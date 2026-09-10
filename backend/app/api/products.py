from fastapi import APIRouter

router = APIRouter(
    prefix="/products",
    tags=["Products"]
)


@router.get("/")
def products_root():
    return {"message": "Products module ready"}
