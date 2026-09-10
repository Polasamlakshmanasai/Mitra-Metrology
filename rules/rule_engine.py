# rule_engine.py
"""
Legal Metrology & FSSAI Compliance Rule Engine.
Evaluates OCR-extracted packaged commodity declarations against statutory rules.
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Any

RULES_PATH = Path(__file__).parent / "rules.json"


def check_compliance(fields: Dict[str, Any], confidences: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Evaluates extracted fields across 8 statutory categories:
    1. MRP
    2. Net quantity
    3. Manufacturing date
    4. Best before / expiry
    5. Manufacturer
    6. Address
    7. Consumer care
    8. FSSAI for food products

    Decision hierarchy:
    - High-severity violation -> NON-COMPLIANT
    - Medium-severity violation OR low confidence -> REVIEW REQUIRED
    - All valid -> COMPLIANT
    """
    violations: List[Dict[str, Any]] = []
    rules_checked = 8

    # Helper to extract actual value if nested in dict
    def get_val(key):
        v = fields.get(key)
        if isinstance(v, dict):
            return v.get("value")
        return v

    # 1. MRP check
    mrp_val = get_val("mrp")
    if mrp_val is None or str(mrp_val).strip() == "":
        violations.append({
            "field": "mrp",
            "rule": "Rule 6(1)(e)",
            "description": "MRP is missing or unreadable",
            "severity": "high"
        })

    # 2. Net quantity check
    net_val = fields.get("net_quantity")
    if not net_val:
        violations.append({
            "field": "net_quantity",
            "rule": "Rule 6(1)(c)",
            "description": "Net quantity is missing",
            "severity": "high"
        })

    # 3. Manufacturing date check
    mfd_val = get_val("manufacturing_date")
    if not mfd_val or str(mfd_val).strip() == "":
        violations.append({
            "field": "manufacturing_date",
            "rule": "Rule 6(1)(d)",
            "description": "Manufacturing date is missing",
            "severity": "medium"
        })

    # 4. Best before / expiry date check
    bb_val = get_val("best_before") or get_val("expiry_best_before")
    if not bb_val or str(bb_val).strip() == "":
        violations.append({
            "field": "best_before",
            "rule": "Rule 6(1)(d)",
            "description": "Best before / expiry date is missing",
            "severity": "medium"
        })

    # 5. Manufacturer name check
    mfr_val = get_val("manufacturer")
    if not mfr_val or str(mfr_val).strip() == "":
        violations.append({
            "field": "manufacturer",
            "rule": "Rule 6(1)(a)",
            "description": "Manufacturer name is missing",
            "severity": "high"
        })

    # 6. Manufacturer address check
    addr_val = get_val("address") or get_val("manufacturer_address")
    if not addr_val or str(addr_val).strip() == "":
        violations.append({
            "field": "address",
            "rule": "Rule 6(1)(a)",
            "description": "Manufacturer address is missing",
            "severity": "medium"
        })

    # 7. Consumer care details check
    care_val = get_val("consumer_care")
    if not care_val or str(care_val).strip() == "":
        violations.append({
            "field": "consumer_care",
            "rule": "Rule 6(1)(n)",
            "description": "Consumer care contact information is missing",
            "severity": "medium"
        })

    # 8. FSSAI license check
    fssai_val = get_val("fssai")
    if not fssai_val or str(fssai_val).strip() == "":
        violations.append({
            "field": "fssai",
            "rule": "FSSAI Reg 5(7)",
            "description": "FSSAI license number is missing",
            "severity": "high"
        })
    elif len(str(fssai_val).strip()) != 14:
        violations.append({
            "field": "fssai",
            "rule": "FSSAI Reg 5(7)",
            "description": f"FSSAI license number must be exactly 14 digits (found {len(str(fssai_val).strip())} digits)",
            "severity": "medium"
        })

    # Check for low confidence flags if provided
    has_low_confidence = False
    if confidences:
        for f_name, conf_data in confidences.items():
            conf_val = conf_data.get("confidence", 1.0) if isinstance(conf_data, dict) else conf_data
            if conf_val < 0.70 and f_name in ["mrp", "net_quantity", "manufacturer", "fssai"]:
                has_low_confidence = True
                violations.append({
                    "field": f_name,
                    "rule": "Confidence Gate",
                    "description": f"Low OCR confidence ({int(conf_val*100)}%) on critical declaration: {f_name}",
                    "severity": "medium"
                })

    # Determine status
    has_high = any(v["severity"] == "high" for v in violations)
    has_medium = any(v["severity"] == "medium" for v in violations)

    if has_high:
        status = "NON-COMPLIANT"
    elif has_medium or has_low_confidence or len(violations) > 0:
        status = "REVIEW REQUIRED"
    else:
        status = "COMPLIANT"

    return {
        "status": status,
        "violations": violations,
        "rules_checked": rules_checked,
        "violation_count": len(violations)
    }


def load_rules():
    if os.path.exists(RULES_PATH):
        with open(RULES_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def evaluate_compliance(extracted_fields: Dict[str, Any]) -> Dict[str, Any]:
    """
    Backwards-compatible evaluator with scoring percentage for analytical views.
    """
    comp = check_compliance(extracted_fields)
    total_rules = comp["rules_checked"]
    passed_count = max(0, total_rules - comp["violation_count"])
    compliance_score = round((passed_count / total_rules) * 100, 1)

    return {
        "compliance_score": compliance_score,
        "status": comp["status"],
        "rules_checked": total_rules,
        "violations_count": comp["violation_count"],
        "passed_count": passed_count,
        "violations": comp["violations"]
    }
