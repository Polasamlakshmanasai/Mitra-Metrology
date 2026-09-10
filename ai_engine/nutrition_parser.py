# nutrition_parser.py
"""
Nutrition Information Parser for Indian Pre-Packaged Food Labels.
Extracts mandatory FSSAI nutrients (Energy, Protein, Carbs, Total/Added Sugars,
Total/Saturated/Trans Fat, Sodium), preserves units, and checks nutritional consistency.
"""

import re


def extract_numeric_value_and_unit(text):
    """
    Parses numbers and units from strings like '450 kcal', '12.5 g', '280 mg', '< 0.1g'.
    """
    if not text:
        return None, None

    match = re.search(r"([<>]?\s*\d+(?:\.\d+)?)\s*(kcal|kj|g|mg|mcg|µg)?", text, re.IGNORECASE)
    if match:
        val_str = match.group(1).replace(" ", "")
        unit = match.group(2) or ""
        return val_str, unit
    return None, None


def parse_nutrition_table(ocr_lines):
    """
    Extracts structured nutritional declarations from OCR text lines.
    """
    full_text = "\n".join(line["text"] if isinstance(line, dict) else str(line) for line in ocr_lines)

    # Basis detection: Per 100g, Per 100ml, Per Serve
    basis = "per 100g"
    if re.search(r"\b(?:per\s*100\s*ml|100ml)\b", full_text, re.IGNORECASE):
        basis = "per 100ml"
    elif re.search(r"\bper\s*serve\b", full_text, re.IGNORECASE):
        basis = "per serve"

    serving_size = None
    serve_match = re.search(r"(?:serving\s*size|per\s*serve)\s*[:\-]?\s*([^\n,]+)", full_text, re.IGNORECASE)
    if serve_match:
        serving_size = serve_match.group(1).strip()

    # Nutrient regex map
    nutrient_patterns = {
        "energy": [r"\b(?:energy|calories)\b[^\d]*([<>]?\s*\d+(?:\.\d+)?)\s*(kcal|kj)?"],
        "protein": [r"\bprotein\b[^\d]*([<>]?\s*\d+(?:\.\d+)?)\s*(g|mg)?"],
        "carbohydrate": [r"\b(?:carbohydrate|carbs)\b[^\d]*([<>]?\s*\d+(?:\.\d+)?)\s*(g|mg)?"],
        "total_sugars": [r"\b(?:total\s*sugars?|sugars?)\b[^\d]*([<>]?\s*\d+(?:\.\d+)?)\s*(g|mg)?"],
        "added_sugars": [r"\b(?:added\s*sugars?)\b[^\d]*([<>]?\s*\d+(?:\.\d+)?)\s*(g|mg)?"],
        "total_fat": [r"\b(?:total\s*fat|fat)\b[^\d]*([<>]?\s*\d+(?:\.\d+)?)\s*(g|mg)?"],
        "saturated_fat": [r"\b(?:saturated\s*fat|saturated\s*fatty\s*acids?)\b[^\d]*([<>]?\s*\d+(?:\.\d+)?)\s*(g|mg)?"],
        "trans_fat": [r"\b(?:trans\s*fat|trans\s*fatty\s*acids?)\b[^\d]*([<>]?\s*\d+(?:\.\d+)?)\s*(g|mg)?"],
        "sodium": [r"\bsodium\b[^\d]*([<>]?\s*\d+(?:\.\d+)?)\s*(mg|g)?"]
    }

    nutrients = {}
    found_count = 0

    for nutrient_key, patterns in nutrient_patterns.items():
        val = None
        unit = "g" if nutrient_key != "energy" and nutrient_key != "sodium" else ("kcal" if nutrient_key == "energy" else "mg")
        raw_snippet = None

        for p in patterns:
            match = re.search(p, full_text, re.IGNORECASE)
            if match:
                raw_snippet = match.group(0).strip()
                val = match.group(1).replace(" ", "")
                if len(match.groups()) > 1 and match.group(2):
                    unit = match.group(2).lower()
                break

        if val is not None:
            found_count += 1
            nutrients[nutrient_key] = {
                "value": val,
                "unit": unit,
                "raw_text": raw_snippet,
                "is_uncertain": False
            }
        else:
            nutrients[nutrient_key] = {
                "value": None,
                "unit": unit,
                "raw_text": None,
                "is_uncertain": False
            }

    # Consistency checks
    consistency_warnings = []

    # Check Added Sugars <= Total Sugars
    try:
        if nutrients["added_sugars"]["value"] and nutrients["total_sugars"]["value"]:
            added_f = float(re.sub(r"[<>]", "", nutrients["added_sugars"]["value"]))
            total_f = float(re.sub(r"[<>]", "", nutrients["total_sugars"]["value"]))
            if added_f > total_f:
                consistency_warnings.append(f"Added sugars ({added_f}g) cannot exceed Total sugars ({total_f}g).")
                nutrients["added_sugars"]["is_uncertain"] = True
    except Exception:
        pass

    # Check Saturated Fat + Trans Fat <= Total Fat
    try:
        if nutrients["total_fat"]["value"] and nutrients["saturated_fat"]["value"]:
            tot_fat_f = float(re.sub(r"[<>]", "", nutrients["total_fat"]["value"]))
            sat_fat_f = float(re.sub(r"[<>]", "", nutrients["saturated_fat"]["value"]))
            trans_f = float(re.sub(r"[<>]", "", nutrients["trans_fat"]["value"])) if nutrients["trans_fat"]["value"] else 0.0
            if (sat_fat_f + trans_f) > (tot_fat_f + 0.2):  # slight floating tolerance
                consistency_warnings.append("Saturated and Trans fat sum exceeds Total Fat.")
                nutrients["saturated_fat"]["is_uncertain"] = True
    except Exception:
        pass

    has_nutrition_table = found_count >= 3

    return {
        "found": has_nutrition_table,
        "basis": basis,
        "serving_size": serving_size,
        "nutrients_extracted_count": found_count,
        "nutrients": nutrients,
        "consistency_warnings": consistency_warnings
    }
