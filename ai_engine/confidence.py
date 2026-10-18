# confidence.py
"""
Confidence Scoring Engine for Mitra Metrology.

v2 changes:
  - calculate_field_confidences() now also returns "status" per field using 7-state enum.
  - Fixed hardcoded 0.92 fallback bug — uses actual OCR confidence when available.
  - All v1 functions (add_confidence_to_fields, calculate_field_confidence) unchanged.
"""

from typing import Any, Dict

from ai_engine.extraction import (
    FIELD_STATUS_VALID, FIELD_STATUS_LOW_CONFIDENCE,
    FIELD_STATUS_UNREADABLE, FIELD_STATUS_NOT_DETECTED,
    FIELD_STATUS_MISSING, FIELD_STATUS_NOT_APPLICABLE,
    FIELD_STATUS_REVIEW_REQUIRED,
    classify_field_status,
)


def clamp(value: float, minimum: float = 0.0, maximum: float = 1.0) -> float:
    return max(minimum, min(maximum, value))


def get_confidence_tier(score: float) -> str:
    if score >= 0.90:
        return "HIGH"
    elif score >= 0.70:
        return "MEDIUM"
    else:
        return "LOW"


def calculate_field_confidences(
    fields: Dict[str, Any],
    quality_score: float = 0.92,
    ocr_text: str = "",
    quality_tier: str = "GOOD",
    field_level_results: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Assigns confidence scores and field status to each extracted field.

    v2: accepts optional field_level_results dict (from extract_best_fields_from_variants)
    which provides actual per-field OCR confidence instead of heuristic base scores.

    Returns per-field:
    {
        "value":      Any,
        "confidence": float (0–1),
        "level":      "HIGH" | "MEDIUM" | "LOW",
        "status":     "VALID" | "LOW_CONFIDENCE" | "UNREADABLE" | "NOT_DETECTED" | ...
    }
    """
    scored = {}

    # Field-specific heuristic baseline confidence (used when real OCR confidence is unavailable)
    base_scores = {
        "fssai":               0.96,
        "mrp":                 0.94,
        "net_quantity":        0.92,
        "consumer_care":       0.90,
        "manufacturing_date":  0.89,
        "best_before":         0.85,
        "manufacturer":        0.79,
        "address":             0.72,
        "product_name":        0.88,
        "ingredients":         0.85,
    }

    quality_factor = clamp(quality_score, 0.5, 1.0)

    for field_name, raw_val in fields.items():
        if raw_val is None:
            status = (FIELD_STATUS_UNREADABLE if quality_tier == "VERY_POOR"
                      else FIELD_STATUS_NOT_DETECTED)
            scored[field_name] = {
                "value":      None,
                "confidence": 0.0,
                "level":      "LOW",
                "status":     status,
            }
            continue

        # Extract scalar value if nested
        val = raw_val
        if isinstance(raw_val, dict) and "value" in raw_val:
            val = raw_val["value"]

        # ── Use real OCR confidence from field-level results if available ────
        real_ocr_conf = None
        if field_level_results and field_name in field_level_results:
            flr = field_level_results[field_name]
            if isinstance(flr, dict):
                real_ocr_conf = flr.get("ocr_confidence")

        if real_ocr_conf is not None:
            # Blend real OCR conf (80%) + image quality (20%)
            base = clamp(real_ocr_conf, 0.0, 1.0)
        else:
            # Fall back to heuristic base scores (v1 behaviour)
            base = base_scores.get(field_name, 0.80)

            # Field-specific fine-tuning on value
            if field_name == "fssai":
                f_str = str(val).strip()
                base = 0.98 if (len(f_str) == 14 and f_str.isdigit()) else 0.65
            elif field_name == "mrp":
                try:
                    num = float(re.sub(r"[^\d.]", "", str(val).replace("₹", "").replace("Rs", "")).strip())
                    base = 0.96 if num > 0 else 0.70
                except (ValueError, AttributeError):
                    base = 0.70
            elif field_name == "net_quantity":
                base = 0.94 if (isinstance(raw_val, dict) and raw_val.get("unit")) else 0.82
            elif field_name == "consumer_care":
                c_str = str(val).lower()
                base = 0.93 if ("@" in c_str or "1800" in c_str or "+" in c_str) else 0.80

        final_score = round(clamp(base * 0.85 + quality_factor * 0.15, 0.0, 1.0), 2)
        tier = get_confidence_tier(final_score)

        # Determine field status using real OCR confidence or heuristic
        ocr_conf_for_status = real_ocr_conf if real_ocr_conf is not None else base
        status = classify_field_status(
            field_name, val, ocr_conf_for_status, quality_score, quality_tier
        )

        scored[field_name] = {
            "value":      raw_val,
            "confidence": final_score,
            "level":      tier,
            "status":     status,
        }

    return scored


# ── v1 backward-compat helpers ─────────────────────────────────────────────

def calculate_field_confidence(field, image_quality_score=0.9):
    if not field:
        return 0.0
    ocr_confidence = field.get("ocr_confidence", 0.0) if isinstance(field, dict) else 0.85
    score = ocr_confidence * 0.80 + image_quality_score * 0.20
    return round(clamp(score), 3)


def add_confidence_to_fields(fields, image_quality_score=0.9):
    return calculate_field_confidences(fields, image_quality_score)


# Avoid circular-import issues with re module
import re