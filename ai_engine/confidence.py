# confidence.py
"""
Confidence Scoring Engine for Mitra Metrology.
Computes field-level confidence scores and classifies into HIGH, MEDIUM, and LOW confidence tiers.
"""

from typing import Dict, Any


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
    ocr_text: str = ""
) -> Dict[str, Any]:
    """
    Assigns confidence scores to each extracted field.
    
    Logic:
    - 90–100% -> HIGH CONFIDENCE
    - 70–89%  -> MEDIUM CONFIDENCE
    - <70%    -> LOW CONFIDENCE
    
    Returns:
    {
      "mrp": {"value": 295, "confidence": 0.96, "level": "HIGH"},
      "fssai": {"value": "10019022009876", "confidence": 0.98, "level": "HIGH"},
      ...
    }
    """
    scored = {}

    # Field-specific heuristic baseline confidence when detected by regex
    base_scores = {
        "fssai": 0.96,
        "mrp": 0.94,
        "net_quantity": 0.92,
        "consumer_care": 0.90,
        "manufacturing_date": 0.89,
        "best_before": 0.85,
        "manufacturer": 0.79,
        "address": 0.72,
        "product_name": 0.88,
        "ingredients": 0.85
    }

    quality_factor = clamp(quality_score, 0.5, 1.0)

    for field_name, raw_val in fields.items():
        if raw_val is None:
            scored[field_name] = {
                "value": None,
                "confidence": 0.0,
                "level": "LOW"
            }
            continue

        # Extract value if raw_val is dict (e.g. net_quantity or already structured)
        val = raw_val
        if isinstance(raw_val, dict) and "value" in raw_val:
            val = raw_val["value"]

        # Base confidence
        base = base_scores.get(field_name, 0.80)

        # Field-specific fine-tuning
        if field_name == "fssai":
            f_str = str(val).strip()
            if len(f_str) == 14 and f_str.isdigit():
                base = 0.98
            else:
                base = 0.65

        elif field_name == "mrp":
            try:
                num = float(str(val).replace("₹", "").replace("Rs", "").replace(".", "", 1).strip())
                base = 0.96 if num > 0 else 0.70
            except ValueError:
                base = 0.70

        elif field_name == "net_quantity":
            if isinstance(raw_val, dict) and raw_val.get("unit"):
                base = 0.94
            else:
                base = 0.82

        elif field_name == "consumer_care":
            c_str = str(val).lower()
            if "@" in c_str or "1800" in c_str or "+" in c_str:
                base = 0.93
            else:
                base = 0.80

        # Adjust with image quality (80% pattern match + 20% visual quality)
        final_score = round(clamp(base * 0.85 + quality_factor * 0.15, 0.0, 1.0), 2)
        tier = get_confidence_tier(final_score)

        scored[field_name] = {
            "value": raw_val,
            "confidence": final_score,
            "level": tier
        }

    return scored


# Backwards compatibility helpers
def calculate_field_confidence(field, image_quality_score=0.9):
    if not field:
        return 0.0
    ocr_confidence = field.get("ocr_confidence", 0.0) if isinstance(field, dict) else 0.85
    score = ocr_confidence * 0.80 + image_quality_score * 0.20
    return round(clamp(score), 3)


def add_confidence_to_fields(fields, image_quality_score=0.9):
    return calculate_field_confidences(fields, image_quality_score)