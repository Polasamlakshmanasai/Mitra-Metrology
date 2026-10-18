from sqlalchemy import Column, Integer, String, Float, DateTime, Text
from datetime import datetime, timezone

from app.database.connection import Base


class ExtractedField(Base):
    __tablename__ = "extracted_fields"

    id = Column(Integer, primary_key=True, index=True)

    scan_id = Column(Integer, nullable=False, index=True)

    field_name = Column(String, nullable=False)

    # The value used for compliance evaluation
    # (corrected value if corrected, otherwise original OCR value)
    field_value = Column(String, nullable=True)

    # Original OCR-extracted value — preserved for audit
    # Never overwritten once set
    original_ocr_value = Column(String, nullable=True)

    # If the user corrected this field, the new value goes here
    corrected_value = Column(String, nullable=True)

    # OCR confidence for this field (0.0 – 1.0)
    confidence = Column(Float, nullable=True)

    # Bounding box as JSON string: {"x":..,"y":..,"width":..,"height":..}
    bounding_box = Column(String, nullable=True)

    # Correction status: "ocr_original" | "user_corrected" | "user_marked_unreadable"
    correction_status = Column(String, default="ocr_original")

    # When the user corrected this field
    corrected_at = Column(DateTime, nullable=True)

    # User ID of the person who made the correction
    corrected_by_user_id = Column(Integer, nullable=True)

    # Which OCR preprocessing variant produced this value
    ocr_source_variant = Column(String, nullable=True)

    # Field status at time of extraction
    field_status = Column(String, nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))