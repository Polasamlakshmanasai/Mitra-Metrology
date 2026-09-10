# app/services/extraction_service.py
"""
Extraction Service for packaged commodity statutory declarations.
"""

import sys
from pathlib import Path

for root in [
    Path(__file__).resolve().parent.parent.parent.parent,
    Path(__file__).resolve().parent.parent.parent,
    Path("/app")
]:
    ai_dir = root / "ai_engine"
    if ai_dir.is_dir():
        if str(ai_dir) not in sys.path:
            sys.path.insert(0, str(ai_dir))
        if str(root) not in sys.path:
            sys.path.insert(0, str(root))

from extraction import extract_fields
from confidence import add_confidence_to_fields


def extract_and_score_fields(ocr_lines: list, image_quality_score: float):
    """
    Extracts structured fields from OCR lines and calculates extraction confidence.
    """
    raw_fields = extract_fields(ocr_lines)
    fields_with_confidence = add_confidence_to_fields(raw_fields, image_quality_score)
    return fields_with_confidence
