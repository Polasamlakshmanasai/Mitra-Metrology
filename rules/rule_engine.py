# rule_engine.py
"""
Legal Metrology (Packaged Commodities) Rules 2011 — Primary Compliance Engine.
FSSAI labelling rules applied ONLY when product is identified as a food product.

v2 changes:
  - check_compliance() uses field_statuses: UNREADABLE != MISSING.
  - is_food_product() — food-product detection heuristic.
  - violations include field_status and action.
  - 7 field-status constants imported from extraction.py.
  - All v1 function signatures backward-compatible.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

RULES_PATH = Path(__file__).parent / "rules.json"

# Import field status constants
try:
    from ai_engine.extraction import (
        FIELD_STATUS_VALID, FIELD_STATUS_DETECTED, FIELD_STATUS_LOW_CONFIDENCE,
        FIELD_STATUS_UNREADABLE, FIELD_STATUS_NOT_DETECTED,
        FIELD_STATUS_MISSING, FIELD_STATUS_VERIFIED_ABSENT,
        FIELD_STATUS_NOT_APPLICABLE, FIELD_STATUS_USER_CORRECTED,
        FIELD_STATUS_CONFIRMED, FIELD_STATUS_REVIEW_REQUIRED,
    )
except ImportError:
    # Fallback string literals if ai_engine not on path
    FIELD_STATUS_VALID           = "VALID"
    FIELD_STATUS_DETECTED        = "DETECTED"
    FIELD_STATUS_LOW_CONFIDENCE  = "LOW_CONFIDENCE"
    FIELD_STATUS_UNREADABLE      = "UNREADABLE"
    FIELD_STATUS_NOT_DETECTED    = "NOT_DETECTED"
    FIELD_STATUS_MISSING         = "MISSING"
    FIELD_STATUS_VERIFIED_ABSENT = "VERIFIED_ABSENT"
    FIELD_STATUS_NOT_APPLICABLE  = "NOT_APPLICABLE"
    FIELD_STATUS_USER_CORRECTED  = "USER_CORRECTED"
    FIELD_STATUS_CONFIRMED       = "CONFIRMED"
    FIELD_STATUS_REVIEW_REQUIRED = "REVIEW_REQUIRED"


def is_food_product(fields: Dict[str, Any], ocr_text: str = "") -> bool:
    """
    Heuristic: returns True if this appears to be a food product,
    so that FSSAI labelling rules should be applied in addition to Legal Metrology.

    Signals:
    - FSSAI license present → very strong signal (food products must have FSSAI)
    - ingredients declared
    - nutrition facts in OCR text
    - best_before / expiry present (most non-food commodities don't carry these)
    """
    def _get(key):
        v = fields.get(key)
        if isinstance(v, dict):
            return v.get("value")
        return v

    if _get("fssai"):
        return True

    text_lower = (ocr_text or "").lower()
    food_keywords = [
        "ingredient", "nutrition", "serving size", "calories",
        "protein", "carbohydrate", "fat", "energy", "per 100",
        "contains", "allergen", "vegetarian", "vegan",
        "best before", "expiry", "use by", "consume before",
    ]
    return any(kw in text_lower for kw in food_keywords)


def check_compliance(
    fields: Dict[str, Any],
    confidences: Dict[str, Any] = None,
    field_statuses: Dict[str, str] = None,
    ocr_text: str = "",
    quality_tier: str = "GOOD",
) -> Dict[str, Any]:
    """
    Evaluates extracted fields against 8 Legal Metrology statutory rules.
    FSSAI license check is only applied when is_food_product() returns True.

    Key v2 rule:
      - UNREADABLE or LOW_CONFIDENCE → "REVIEW REQUIRED" (never "NON-COMPLIANT" on its own)
      - NOT_DETECTED + required field → high/medium severity as before
      - MISSING is set BY THIS FUNCTION (not by OCR) and means "deterministically absent"

    Returns:
    {
        "status":          "COMPLIANT" | "REVIEW REQUIRED" | "NON-COMPLIANT",
        "violations":      list[dict],
        "rules_checked":   int,
        "violation_count": int,
        "is_food_product": bool,
    }
    """
    violations: List[Dict[str, Any]] = []

    # Helper to safely extract value
    def get_val(key):
        v = fields.get(key)
        if isinstance(v, dict):
            return v.get("value")
        return v

    # Helper to get precomputed field status
    def get_status(key) -> str:
        if field_statuses and key in field_statuses:
            return field_statuses[key]
        val = get_val(key)
        if val is None or str(val).strip() == "":
            return FIELD_STATUS_NOT_DETECTED
        return FIELD_STATUS_VALID

    def add_violation(field, rule, description, severity, fs, action="Verify declaration on physical package", regime="LEGAL_METROLOGY"):
        violations.append({
            "field":        field,
            "field_status": fs,
            "rule":         rule,
            "description":  description,
            "severity":     severity,
            "action":       action,
            "regime":       regime,
        })

    food_product = is_food_product(fields, ocr_text)
    rules_checked = 8 if food_product else 7

    # ── Rule 1: MRP [Rule 6(1)(e) LM(PC)R 2011] — HIGH ─────────────────
    mrp_val = get_val("mrp")
    mrp_status = get_status("mrp")
    if mrp_status == FIELD_STATUS_UNREADABLE:
        add_violation("mrp", "Rule 6(1)(e) LM(PC)R 2011",
                      "MRP could not be read from image — manual verification required",
                      "medium", mrp_status, "Manually check MRP declaration on package")
    elif mrp_status == FIELD_STATUS_LOW_CONFIDENCE:
        add_violation("mrp", "Rule 6(1)(e) LM(PC)R 2011",
                      f"MRP extracted with low OCR confidence — value '{mrp_val}' may be inaccurate",
                      "medium", mrp_status, "Verify MRP value against physical package")
    elif mrp_val is None or str(mrp_val).strip() == "":
        add_violation("mrp", "Rule 6(1)(e) LM(PC)R 2011",
                      "MRP declaration is absent from label",
                      "high", FIELD_STATUS_MISSING)

    # ── Rule 2: Net Quantity [Rule 6(1)(c)] — HIGH ──────────────────────
    net_val = get_val("net_quantity")
    net_status = get_status("net_quantity")
    if net_status == FIELD_STATUS_UNREADABLE:
        add_violation("net_quantity", "Rule 6(1)(c) LM(PC)R 2011",
                      "Net quantity could not be read — manual verification required",
                      "medium", net_status)
    elif net_status == FIELD_STATUS_LOW_CONFIDENCE:
        add_violation("net_quantity", "Rule 6(1)(c) LM(PC)R 2011",
                      f"Net quantity low OCR confidence — value '{net_val}' may be inaccurate",
                      "medium", net_status)
    elif not net_val:
        add_violation("net_quantity", "Rule 6(1)(c) LM(PC)R 2011",
                      "Net quantity declaration is absent from label",
                      "high", FIELD_STATUS_MISSING)

    # ── Rule 3: Manufacturing Date [Rule 6(1)(d)] — MEDIUM ──────────────
    mfd_val = get_val("manufacturing_date")
    mfd_status = get_status("manufacturing_date")
    if mfd_status == FIELD_STATUS_UNREADABLE:
        add_violation("manufacturing_date", "Rule 6(1)(d) LM(PC)R 2011",
                      "Manufacturing date could not be read — manual check required",
                      "medium", mfd_status)
    elif mfd_status == FIELD_STATUS_LOW_CONFIDENCE:
        add_violation("manufacturing_date", "Rule 6(1)(d) LM(PC)R 2011",
                      f"Manufacturing date low confidence — value '{mfd_val}' may be inaccurate",
                      "medium", mfd_status)
    elif not mfd_val or str(mfd_val).strip() == "":
        add_violation("manufacturing_date", "Rule 6(1)(d) LM(PC)R 2011",
                      "Manufacturing/packing date is absent from label",
                      "medium", FIELD_STATUS_MISSING)

    # ── Rule 4: Best Before / Expiry [Rule 6(1)(da)] — MEDIUM ────────────
    bb_val = (get_val("best_before") or get_val("expiry_date")
              or get_val("expiry_best_before"))
    bb_status = (get_status("best_before") if get_val("best_before")
                 else get_status("expiry_date"))
    if bb_status == FIELD_STATUS_UNREADABLE:
        add_violation("best_before", "Rule 6(1)(da) LM(PC)R 2011",
                      "Best before / expiry date could not be read — manual verification required",
                      "medium", bb_status)
    elif bb_status == FIELD_STATUS_LOW_CONFIDENCE:
        add_violation("best_before", "Rule 6(1)(da) LM(PC)R 2011",
                      f"Best before / expiry date low confidence — value '{bb_val}' may be inaccurate",
                      "medium", bb_status)
    elif not bb_val or str(bb_val).strip() == "":
        add_violation("best_before", "Rule 6(1)(da) LM(PC)R 2011",
                      "Best before / expiry information is absent from label",
                      "medium", FIELD_STATUS_MISSING)

    # ── Rule 5: Manufacturer Name [Rule 6(1)(a)] — HIGH ─────────────────
    mfr_val = get_val("manufacturer")
    mfr_status = get_status("manufacturer")
    if mfr_status == FIELD_STATUS_UNREADABLE:
        add_violation("manufacturer", "Rule 6(1)(a) LM(PC)R 2011",
                      "Manufacturer name could not be read — manual check required",
                      "medium", mfr_status)
    elif mfr_status == FIELD_STATUS_LOW_CONFIDENCE:
        add_violation("manufacturer", "Rule 6(1)(a) LM(PC)R 2011",
                      "Manufacturer name low confidence",
                      "medium", mfr_status)
    elif not mfr_val or str(mfr_val).strip() == "":
        add_violation("manufacturer", "Rule 6(1)(a) LM(PC)R 2011",
                      "Manufacturer / Packer name is absent from label",
                      "high", FIELD_STATUS_MISSING)

    # ── Rule 6: Manufacturer Address [Rule 6(1)(a)] — MEDIUM ────────────
    addr_val = get_val("address") or get_val("manufacturer_address")
    addr_status = get_status("address") if get_val("address") else get_status("manufacturer_address")
    if addr_status == FIELD_STATUS_UNREADABLE:
        add_violation("address", "Rule 6(1)(a) LM(PC)R 2011",
                      "Manufacturer address could not be read",
                      "medium", addr_status)
    elif not addr_val or str(addr_val).strip() == "":
        add_violation("address", "Rule 6(1)(a) LM(PC)R 2011",
                      "Manufacturer / Packer address is absent from label",
                      "medium", FIELD_STATUS_MISSING)

    # ── Rule 7: Consumer Care [Rule 6(1)(f)] — MEDIUM ───────────────────
    care_val = get_val("consumer_care")
    care_status = get_status("consumer_care")
    if care_status == FIELD_STATUS_UNREADABLE:
        add_violation("consumer_care", "Rule 6(1)(f) LM(PC)R 2011",
                      "Consumer care contact could not be read",
                      "medium", care_status)
    elif not care_val or str(care_val).strip() == "":
        add_violation("consumer_care", "Rule 6(1)(f) LM(PC)R 2011",
                      "Consumer care contact information is absent from label",
                      "medium", FIELD_STATUS_MISSING)

    # ── Rule 8: FSSAI [Reg 5(7)] — only for food products ───────────────
    if food_product:
        fssai_val = get_val("fssai")
        fssai_status = get_status("fssai")
        if fssai_status == FIELD_STATUS_UNREADABLE:
            add_violation("fssai", "FSSAI Reg 5(7) — FSS (L&D) Regulations 2020",
                          "FSSAI license number could not be read — manual check required",
                          "medium", fssai_status, "Verify FSSAI logo and 14-digit license number on food package",
                          regime="FSSAI")
        elif fssai_status == FIELD_STATUS_LOW_CONFIDENCE:
            add_violation("fssai", "FSSAI Reg 5(7) — FSS (L&D) Regulations 2020",
                          f"FSSAI license number low confidence — value '{fssai_val}' may contain OCR errors",
                          "medium", fssai_status, "Verify 14-digit license number against package",
                          regime="FSSAI")
        elif fssai_status == FIELD_STATUS_NOT_DETECTED or (not fssai_val and fssai_status != FIELD_STATUS_MISSING):
            add_violation("fssai", "FSSAI Reg 5(7) — FSS (L&D) Regulations 2020",
                          "FSSAI license number was not detected by OCR on this panel — manual verification recommended on food package",
                          "medium", FIELD_STATUS_NOT_DETECTED, "Check physical food package for 14-digit FSSAI license or registration",
                          regime="FSSAI")
        elif not fssai_val or str(fssai_val).strip() == "":
            add_violation("fssai", "FSSAI Reg 5(7) — FSS (L&D) Regulations 2020",
                          "FSSAI license number is confirmed absent from food label",
                          "high", FIELD_STATUS_MISSING, "Packaged food commodity must bear 14-digit FSSAI license",
                          regime="FSSAI")
        elif len(str(fssai_val).strip()) != 14:
            add_violation("fssai", "FSSAI Reg 5(7) — FSS (L&D) Regulations 2020",
                          f"FSSAI license number must be exactly 14 digits (found {len(str(fssai_val).strip())} digits)",
                          "medium", FIELD_STATUS_LOW_CONFIDENCE, "Verify and correct the 14-digit FSSAI license number",
                          regime="FSSAI")

    # ── Low confidence gate on critical fields ───────────────────────────
    if confidences:
        critical_fields = ["mrp", "net_quantity", "manufacturer", "fssai"]
        for f_name, conf_data in confidences.items():
            if f_name not in critical_fields:
                continue
            conf_val = conf_data.get("confidence", 1.0) if isinstance(conf_data, dict) else conf_data
            fs = conf_data.get("status", FIELD_STATUS_VALID) if isinstance(conf_data, dict) else FIELD_STATUS_VALID
            # Only add low-confidence violation if not already captured above
            already_flagged = any(v["field"] == f_name for v in violations)
            if conf_val < 0.65 and not already_flagged and fs not in (FIELD_STATUS_UNREADABLE, FIELD_STATUS_NOT_DETECTED):
                add_violation(f_name, "Confidence Gate",
                              f"Low OCR confidence ({int(conf_val*100)}%) on critical declaration: {f_name}",
                              "medium", FIELD_STATUS_LOW_CONFIDENCE,
                              "Manual verification of this field is recommended")

    # ── Final verdict ────────────────────────────────────────────────────
    has_high   = any(v["severity"] == "high" for v in violations)
    has_medium = any(v["severity"] == "medium" for v in violations)

    if has_high:
        status = "NON-COMPLIANT"
    elif has_medium or len(violations) > 0:
        status = "REVIEW REQUIRED"
    else:
        status = "COMPLIANT"

    return {
        "status":          status,
        "violations":      violations,
        "rules_checked":   rules_checked,
        "violation_count": len(violations),
        "is_food_product": food_product,
    }


def load_rules():
    if os.path.exists(RULES_PATH):
        with open(RULES_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def evaluate_compliance(extracted_fields: Dict[str, Any]) -> Dict[str, Any]:
    """
    Backward-compatible evaluator with scoring percentage.
    """
    comp = check_compliance(extracted_fields)
    total_rules = comp["rules_checked"]
    passed_count = max(0, total_rules - comp["violation_count"])
    compliance_score = round((passed_count / total_rules) * 100, 1)

    return {
        "compliance_score": compliance_score,
        "status":           comp["status"],
        "rules_checked":    total_rules,
        "violations_count": comp["violation_count"],
        "passed_count":     passed_count,
        "violations":       comp["violations"],
    }
