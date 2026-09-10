import sys
import os
from pathlib import Path

ROOT_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../..")
)

if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

RULES_DIR = os.path.join(ROOT_DIR, "rules")
if RULES_DIR not in sys.path:
    sys.path.append(RULES_DIR)

from ai_engine.image_quality import check_image_quality
from ai_engine.ocr import extract_text
from ai_engine.extraction import extract_fields
from ai_engine.confidence import calculate_field_confidences
from rules.rule_engine import check_compliance, evaluate_compliance
from app.services.ocr_service import analyze_image_ocr
from app.services.extraction_service import extract_and_score_fields


def analyze_product(image_path: str):
    """
    Executes the comprehensive Mitra Metrology inspection pipeline:
    1. Image Quality Assessment (blur, resolution)
    2. Packaging OCR extraction
    3. Field extraction (MRP, Net Qty, Dates, Mfr, FSSAI, Consumer Care)
    4. Confidence Scoring (HIGH, MEDIUM, LOW tiers)
    5. Legal Metrology + FSSAI 8-Rule Compliance Engine
    """
    # 1. Image quality
    quality = check_image_quality(image_path)

    if not quality.get("valid", True):
        return {
            "status": "REVIEW REQUIRED",
            "stage": "image_quality",
            "quality": quality,
            "ocr_text": "",
            "fields": {},
            "confidences": {},
            "violations": [{
                "field": "image_quality",
                "description": quality.get("reason", "Image quality validation failed"),
                "severity": "medium"
            }],
            "violation_count": 1,
            "rules_checked": 8
        }

    # 2. OCR
    text = extract_text(image_path)

    if not text or not text.strip():
        return {
            "status": "REVIEW REQUIRED",
            "stage": "ocr",
            "message": "No readable text detected",
            "quality": quality,
            "ocr_text": "",
            "fields": {},
            "confidences": {},
            "violations": [{
                "field": "ocr",
                "description": "No readable text detected on package",
                "severity": "medium"
            }],
            "violation_count": 1,
            "rules_checked": 8
        }

    # 3. Field extraction
    fields = extract_fields(text)

    # 4. Confidence scoring
    quality_score = 0.95 if quality.get("valid") else 0.60
    confidences = calculate_field_confidences(fields, quality_score=quality_score, ocr_text=text)

    # 5. Deterministic compliance
    compliance = check_compliance(fields, confidences)

    return {
        "status": compliance["status"],
        "quality": quality,
        "ocr_text": text,
        "fields": fields,
        "confidences": confidences,
        "violations": compliance["violations"],
        "violation_count": compliance["violation_count"],
        "rules_checked": compliance["rules_checked"]
    }


def run_full_pipeline(image_path: str):
    """
    Legacy wrapper for CV + compliance analysis.
    """
    return analyze_product(image_path)
