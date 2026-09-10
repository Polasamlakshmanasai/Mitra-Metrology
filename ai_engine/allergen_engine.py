# allergen_engine.py
"""
Allergen Detection Engine for FSSAI Labelling & Display Regulations.
Detects mandatory food allergens from explicit declarations, ingredients list, and synonyms.
Enforces safety safeguards: NEVER claims 'Allergen Free'.
"""

import re
import json
from pathlib import Path

RULES_DIR = Path(__file__).resolve().parent.parent / "rules"
ALLERGEN_DB_PATH = RULES_DIR / "allergen_db.json"

_ALLERGEN_DB = None

def get_allergen_db():
    global _ALLERGEN_DB
    if _ALLERGEN_DB is None:
        try:
            with open(ALLERGEN_DB_PATH, "r", encoding="utf-8") as f:
                _ALLERGEN_DB = json.load(f)
        except Exception:
            _ALLERGEN_DB = {"allergens": []}
    return _ALLERGEN_DB


def evaluate_allergens(ingredients_text, explicit_allergen_text="", is_label_readable=True):
    """
    Evaluates allergens across explicit declarations and ingredient list.
    
    Status values per allergen:
    - 'CONTAINS': Definitively identified in ingredients or declared as 'Contains'
    - 'POSSIBLE_SOURCE': Cross-contamination warning ('May contain...', 'Processed on equipment...')
    - 'NOT_DETECTED': Not observed in visible text (explicitly NOT 'Allergen Free')
    - 'UNABLE_TO_DETERMINE': Label text unreadable or OCR confidence insufficient
    """
    db = get_allergen_db()
    all_allergens = db.get("allergens", [])

    if not is_label_readable or (not ingredients_text and not explicit_allergen_text):
        return {
            "overall_status": "UNABLE_TO_DETERMINE",
            "summary": "Label text quality or coverage insufficient to reliably assess allergen declarations.",
            "explicit_declaration_found": False,
            "detected_allergens": [],
            "allergen_breakdown": [
                {
                    "allergen_id": a["id"],
                    "name": a["name"],
                    "status": "UNABLE_TO_DETERMINE",
                    "evidence": None
                }
                for a in all_allergens
            ],
            "safeguard_disclaimer": "Lack of detection does not guarantee the product is allergen-free."
        }

    combined_text = f"{ingredients_text} {explicit_allergen_text}".lower()

    # Check for precautionary cross-contact statements
    precautionary_patterns = [
        r"may\s+contain(?:\s+traces\s+of)?\s*[:\-]?\s*([^.]+)",
        r"processed\s+(?:in\s+a\s+facility|on\s+equipment)\s+that\s+(?:also\s+)?(?:handles|processes)\s*[:\-]?\s*([^.]+)",
        r"manufactured\s+in\s+a\s+facility\s+that\s+handles\s*[:\-]?\s*([^.]+)"
    ]

    precautionary_snippets = []
    for pattern in precautionary_patterns:
        match = re.search(pattern, combined_text, re.IGNORECASE)
        if match:
            precautionary_snippets.append(match.group(0))

    allergen_results = []
    detected_list = []
    has_explicit = bool(explicit_allergen_text and explicit_allergen_text.strip())

    for item in all_allergens:
        a_id = item["id"]
        a_name = item["name"]
        sources = item.get("sources", [])

        status = "NOT_DETECTED"
        evidence = None

        # Check explicit contains statement first
        for src in sources:
            word_pattern = r"\b" + re.escape(src) + r"\b"
            if re.search(word_pattern, combined_text):
                # Is it in a precautionary "may contain" section?
                in_precautionary = any(re.search(word_pattern, snippet) for snippet in precautionary_snippets)
                if in_precautionary:
                    status = "POSSIBLE_SOURCE"
                    evidence = f"Cross-contamination advisory: '{src}' mentioned in precautionary statement."
                else:
                    status = "CONTAINS"
                    evidence = f"Identified '{src}' in product ingredients/declarations."
                    break

        if status in ["CONTAINS", "POSSIBLE_SOURCE"]:
            detected_list.append({
                "allergen_id": a_id,
                "name": a_name,
                "status": status,
                "evidence": evidence
            })

        allergen_results.append({
            "allergen_id": a_id,
            "name": a_name,
            "status": status,
            "evidence": evidence
        })

    contains_count = sum(1 for a in allergen_results if a["status"] == "CONTAINS")
    possible_count = sum(1 for a in allergen_results if a["status"] == "POSSIBLE_SOURCE")

    if contains_count > 0:
        overall = "ALLERGENS_PRESENT"
        summary = f"Product contains {contains_count} mandatory FSSAI allergen source(s)."
    elif possible_count > 0:
        overall = "POTENTIAL_ALLERGEN_TRACES"
        summary = f"Product contains precautionary warnings for {possible_count} potential allergen(s)."
    else:
        overall = "NOT_DETECTED_ON_LABEL"
        summary = "No mandatory allergens were detected in readable label text. (Not a laboratory allergen-free certificate)."

    return {
        "overall_status": overall,
        "summary": summary,
        "explicit_declaration_found": has_explicit,
        "detected_allergens": detected_list,
        "allergen_breakdown": allergen_results,
        "safeguard_disclaimer": "Results are based strictly on readable text from the submitted packaging. This is NOT a guarantee that the food is allergen-free."
    }
