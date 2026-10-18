# backend/tests/conftest.py
"""
Pytest configuration and isolated fixtures for Mitra Metrology test suite.

Ensures:
- Dedicated isolated SQLite database (backend/tests/test_metrology_isolated.db)
- Developer's primary database (mitra.db) is never touched
- Automatic cleanup of test database on teardown
- Authentication tokens for Citizen and Officer roles
- Reusable test image fixtures and synthetic packaging generators
"""

import os
import sys
import tempfile
from pathlib import Path
import pytest
from PIL import Image, ImageDraw, ImageFilter
from fastapi.testclient import TestClient

# ── 1. Configure isolated test environment variables ──────────────────────────
TESTS_DIR = Path(__file__).resolve().parent
BACKEND_DIR = TESTS_DIR.parent
PROJECT_ROOT = BACKEND_DIR.parent

TEST_DB_PATH = TESTS_DIR / "test_metrology_isolated.db"
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB_PATH.as_posix()}"
os.environ["MONGODB_URI"] = ""  # Force SQLite fallback for all tests
os.environ["TESSERACT_CMD"] = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# Ensure proper Python path resolution
for p in [str(PROJECT_ROOT), str(BACKEND_DIR)]:
    if p not in sys.path:
        sys.path.insert(0, p)

from app.database.connection import Base, engine, SessionLocal
from app.services.seed_service import seed_default_accounts
from app.main import app


# ── 2. Database isolation session fixture ─────────────────────────────────────
@pytest.fixture(scope="session", autouse=True)
def setup_isolated_test_database():
    """Initializes schema and default accounts in isolated test database, tears down at end."""
    # Ensure fresh test DB
    if TEST_DB_PATH.exists():
        try:
            TEST_DB_PATH.unlink()
        except Exception:
            pass

    Base.metadata.create_all(bind=engine)
    seed_default_accounts()

    yield

    # Clean up test database
    try:
        Base.metadata.drop_all(bind=engine)
        engine.dispose()
        if TEST_DB_PATH.exists():
            TEST_DB_PATH.unlink()
    except Exception as e:
        print(f"Warning: could not cleanly remove test DB: {e}")


# ── 3. Test client and auth fixtures ──────────────────────────────────────────
@pytest.fixture(scope="session")
def client():
    """FastAPI TestClient instance connected to isolated test environment."""
    return TestClient(app)


@pytest.fixture(scope="session")
def citizen_token(client):
    """Access token for standard citizen user (user@mitra.com)."""
    res = client.post("/auth/login", json={"email": "user@mitra.com", "password": "User@123"})
    assert res.status_code == 200, f"Citizen login failed: {res.text}"
    return res.json()["access_token"]


@pytest.fixture(scope="session")
def citizen_headers(citizen_token):
    return {"Authorization": f"Bearer {citizen_token}"}


@pytest.fixture(scope="session")
def officer_token(client):
    """Access token for legal metrology officer (officer_22472@mitra.gov.in)."""
    res = client.post("/auth/login", json={"email": "officer_22472@mitra.gov.in", "password": "Officer@123"})
    assert res.status_code == 200, f"Officer login failed: {res.text}"
    return res.json()["access_token"]


@pytest.fixture(scope="session")
def officer_headers(officer_token):
    return {"Authorization": f"Bearer {officer_token}"}


# ── 4. Image fixture helpers ──────────────────────────────────────────────────
@pytest.fixture
def fixtures_dir():
    return TESTS_DIR / "fixtures"


@pytest.fixture
def sample_product_label_path(fixtures_dir):
    p = fixtures_dir / "sample_product_label.jpg"
    assert p.exists(), f"Missing test fixture: {p}"
    return p


@pytest.fixture
def compliant_package_path(fixtures_dir):
    p = fixtures_dir / "test_compliant_package.jpg"
    assert p.exists(), f"Missing test fixture: {p}"
    return p


@pytest.fixture
def blurry_package_path(fixtures_dir):
    p = fixtures_dir / "test_blurry_atta.jpg"
    assert p.exists(), f"Missing test fixture: {p}"
    return p


@pytest.fixture
def create_synthetic_image(tmp_path):
    """Helper to generate customizable synthetic package label images."""
    def _create(
        lines=None,
        width=800,
        height=800,
        bg_color=(255, 255, 255),
        text_color=(0, 0, 0),
        blur_radius=0,
        filename="synthetic_package.jpg"
    ):
        img = Image.new("RGB", (width, height), color=bg_color)
        draw = ImageDraw.Draw(img)
        
        # Border
        draw.rectangle([15, 15, width - 15, height - 15], outline=(30, 60, 120), width=3)
        
        y = 40
        if lines:
            for line in lines:
                draw.text((40, y), line, fill=text_color)
                y += 36
                
        if blur_radius > 0:
            img = img.filter(ImageFilter.GaussianBlur(blur_radius))
            
        out_path = tmp_path / filename
        img.save(out_path, format="JPEG", quality=95)
        return out_path

    return _create
