import sys
import os
import logging
from contextlib import asynccontextmanager
from pathlib import Path

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

try:
    from dotenv import load_dotenv
    _env_path = Path(BACKEND_DIR) / ".env"
    if _env_path.exists():
        load_dotenv(_env_path)
    else:
        load_dotenv()
except ImportError:
    pass

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.database.connection import Base, engine
from app.database.mongo import connect_mongo, disconnect_mongo, is_mongo_enabled
from app.models import user, product, scan, extracted_field, violation, complaint

from app.api.auth import router as auth_router
from app.api.complaints import router as complaints_router
from app.api.inspections import router as inspections_router
from app.api.products import router as products_router
from app.api.scans import router as scans_router
from app.api.test import router as test_router
from app.api.predict import router as predict_router
from app.api.food_label import router as food_label_router
from app.api.review import router as review_router

from app.services.seed_service import seed_default_accounts

logger = logging.getLogger("mitra.startup")
logging.basicConfig(level=logging.INFO)

# Initialize relational DB schema (SQLite for local / migration period)
Base.metadata.create_all(bind=engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI lifespan context — handles startup and shutdown.
    Replaces the deprecated @app.on_event pattern.
    """
    # ── Startup ────────────────────────────────────────────────
    seed_default_accounts()

    # Tesseract diagnostics — server-side log only, NOT in API responses
    try:
        from ai_engine.ocr import get_tesseract_diagnostics
        diag = get_tesseract_diagnostics()
        if diag["available"]:
            logger.info(
                f"[Tesseract] Available — version={diag['version']}, "
                f"path={'(env var)' if diag['env_cmd_set'] else '(auto-detected)'}, "
                f"languages={diag['installed_languages']}"
            )
        else:
            logger.warning(
                "[Tesseract] NOT available. OCR will use demo fallback. "
                "Install tesseract-ocr or set TESSERACT_CMD env var."
            )
    except Exception as exc:
        logger.warning(f"[Tesseract] Diagnostics failed: {exc}")

    # MongoDB Atlas (graceful no-op if MONGODB_URI not set)
    await connect_mongo()
    if is_mongo_enabled():
        logger.info("[MongoDB] Atlas persistence layer active.")
    else:
        logger.info("[MongoDB] MONGODB_URI not set — using SQLite (SQLAlchemy).")

    yield  # ── Application runs ──────────────────────────────────

    # ── Shutdown ───────────────────────────────────────────────
    await disconnect_mongo()


# Static files directory for uploads
UPLOAD_DIR = Path(__file__).resolve().parent.parent / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(
    title="Mitra Metrology API",
    description="AI-Powered Packaged Commodity Legal Metrology & FSSAI Compliance Inspector",
    version="2.0.0",
    lifespan=lifespan,
)

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
# review_router must be before scans_router to prevent /scans/ocr-extract
# being matched by the /{scan_id} path parameter pattern.
app.include_router(review_router)
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
        "version": "2.0.0"
    }


@app.get("/health/database")
def database_health():
    """Database connectivity check."""
    try:
        from app.database.connection import SessionLocal
        import sqlalchemy
        db = SessionLocal()
        db.execute(sqlalchemy.text("SELECT 1"))
        db.close()
        return {
            "sqlite": "connected",
            "mongodb": "enabled" if is_mongo_enabled() else "not_configured",
        }
    except Exception:
        return {"sqlite": "error", "mongodb": "unknown"}


@app.get("/health/ocr")
def ocr_health():
    """
    OCR availability check.
    Returns only status — no internal paths or system details.
    """
    try:
        from ai_engine.ocr import is_tesseract_available
        available = is_tesseract_available()
        return {
            "ocr_engine": "tesseract",
            "available": available,
            "status": "ready" if available else "fallback_mode",
            "note": (
                "OCR engine is ready for production use."
                if available
                else "Tesseract not found. Install tesseract-ocr or set TESSERACT_CMD. "
                     "Demo fallback is active."
            )
        }
    except Exception:
        return {"ocr_engine": "tesseract", "available": False, "status": "error"}