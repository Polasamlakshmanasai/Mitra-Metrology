from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean
from datetime import datetime, timezone

from app.database.connection import Base


class Scan(Base):
    __tablename__ = "scans"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(Integer, nullable=True, index=True)

    image_path = Column(String, nullable=True)

    # Workflow status:
    #   "ocr_pending"     — image uploaded, OCR not yet run
    #   "review_pending"  — OCR done, waiting for user to review extracted fields
    #   "confirmed"       — user confirmed fields, compliance evaluated
    #   "processing"      — pipeline running
    #   "COMPLIANT" | "NON-COMPLIANT" | "REVIEW REQUIRED" — final compliance verdict
    status = Column(String, default="processing")

    # Overall compliance score (0–100), set after confirmation
    score = Column(Float, nullable=True)

    # Has the user explicitly confirmed the OCR review?
    user_confirmed = Column(Boolean, default=False)

    # When the user clicked "Confirm & Generate Compliance Report"
    confirmed_at = Column(DateTime, nullable=True)

    # Whether this scan used the image quality fallback (Continue Anyway)
    quality_override = Column(Boolean, default=False)

    # Quality tier at time of scan: GOOD | POOR | VERY_POOR
    quality_tier = Column(String, nullable=True)

    # Was there an image quality warning added to the final report?
    has_quality_warning = Column(Boolean, default=False)

    # Is this product identified as a food product (triggers FSSAI checks)?
    is_food_product = Column(Boolean, default=False)

    # Number of rules checked
    rules_checked = Column(Integer, nullable=True)

    # Number of violations found
    violation_count = Column(Integer, nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)