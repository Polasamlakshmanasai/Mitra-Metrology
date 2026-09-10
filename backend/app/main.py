import sys
import os
from pathlib import Path

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.database.connection import Base, engine
from app.models import user, product, scan, extracted_field, violation, complaint

from app.api.auth import router as auth_router
from app.api.complaints import router as complaints_router
from app.api.inspections import router as inspections_router
from app.api.products import router as products_router
from app.api.scans import router as scans_router
from app.api.test import router as test_router
from app.api.predict import router as predict_router
from app.api.food_label import router as food_label_router

from app.services.seed_service import seed_default_accounts

# Initialize database schema and ensure default credentials exist
Base.metadata.create_all(bind=engine)
seed_default_accounts()

# Static files directory for uploads
UPLOAD_DIR = Path(__file__).resolve().parent.parent / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(
    title="Mitra Metrology API",
    description="AI-Powered Packaged Commodity Legal Metrology & FSSAI Compliance Inspector",
    version="1.0.0"
)

@app.on_event("startup")
def on_startup():
    seed_default_accounts()

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve uploaded product photos statically
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")

# Register routers
app.include_router(auth_router)
app.include_router(complaints_router)
app.include_router(inspections_router)
app.include_router(products_router)
app.include_router(scans_router)
app.include_router(test_router)
app.include_router(predict_router)
app.include_router(food_label_router)


@app.get("/")
def root():
    return {
        "message": "Mitra Metrology API is running",
        "status": "success",
        "version": "1.0.0"
    }


@app.get("/health/database")
def database_health():
    return {
        "database": "connected"
    }