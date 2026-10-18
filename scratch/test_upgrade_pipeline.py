import sys
import os

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

from ai_engine.preprocessing import generate_preprocessing_variants
from ai_engine.ocr import run_ocr_multi_variant
from ai_engine.extraction import (
    extract_dates_with_context, 
    classify_field_status, 
    select_best_field_candidate,
    FIELD_STATUS_VALID, FIELD_STATUS_LOW_CONFIDENCE,
    FIELD_STATUS_UNREADABLE, FIELD_STATUS_NOT_DETECTED,
    FIELD_STATUS_MISSING, FIELD_STATUS_NOT_APPLICABLE,
    FIELD_STATUS_REVIEW_REQUIRED
)
from rules.rule_engine import check_compliance, is_food_product
from backend.app.services.compliance_service import analyze_product
import numpy as np


def run_tests():
    print("RUNNING UPGRADE PIPELINE TESTS")
    failures = 0
    passed = 0

    def assert_eq(actual, expected, name):
        nonlocal failures, passed
        if actual == expected:
            passed += 1
            print(f"PASS: {name}")
        else:
            failures += 1
            print(f"FAIL: {name}")
            print(f"   Expected: {expected}")
            print(f"   Actual:   {actual}")

    def assert_contains(container, item, name):
        nonlocal failures, passed
        if item in container:
            passed += 1
            print(f"PASS: {name}")
        else:
            failures += 1
            print(f"FAIL: {name}")
            print(f"   Expected {container} to contain {item}")

    # 1. Date Context Tests
    lines_mfg1 = [{"text": "MFD: 15/08/2024", "confidence": 0.9}]
    lines_exp1 = [{"text": "EXP: 15/08/2025", "confidence": 0.9}]
    lines_bb1  = [{"text": "BEST BEFORE: 6 MONTHS FROM PACKAGING", "confidence": 0.9}]
    lines_mfg2 = [{"text": "MFG 08/2024", "confidence": 0.9}]
    lines_exp2 = [{"text": "EXP 08/2025", "confidence": 0.9}]
    lines_date1 = [{"text": "MFD", "confidence": 0.9}, {"text": "15.08.2024", "confidence": 0.9}]
    lines_date2 = [{"text": "MFD", "confidence": 0.9}, {"text": "15-08-24", "confidence": 0.9}]
    lines_date3 = [{"text": "MFD", "confidence": 0.9}, {"text": "15/08/24", "confidence": 0.9}]
    lines_text = [{"text": "MFD", "confidence": 0.9}, {"text": "15 AUG 2024", "confidence": 0.9}]
    
    # 1.1 "MFD: 15/08/2024"
    res = extract_dates_with_context(lines_mfg1)
    assert_eq(res["manufacturing_date"]["value"], "15/08/2024", "Date 1: MFD 1")
    assert_eq(res["expiry_date"], None, "Date 1: No EXP")
    
    # 1.2 "EXP: 15/08/2025"
    res = extract_dates_with_context(lines_exp1)
    assert_eq(res["expiry_date"]["value"], "15/08/2025", "Date 2: EXP 1")
    assert_eq(res["manufacturing_date"], None, "Date 2: No MFD")
    
    # 1.3 "BEST BEFORE: 6 MONTHS FROM PACKAGING"
    res = extract_dates_with_context(lines_bb1)
    assert_eq(res["best_before"]["value"], "6 MONTHS FROM PACKAGING", "Date 3: Best Before Text")
    
    # 1.4 "MFG 08/2024"
    res = extract_dates_with_context(lines_mfg2)
    assert_eq(res["manufacturing_date"]["value"], "08/2024", "Date 4: MFG MM/YYYY")
    
    # 1.5 "EXP 08/2025"
    res = extract_dates_with_context(lines_exp2)
    assert_eq(res["expiry_date"]["value"], "08/2025", "Date 5: EXP MM/YYYY")
    
    # 1.6 "15.08.2024" Context
    res = extract_dates_with_context(lines_date1)
    assert_eq(res["manufacturing_date"]["value"], "15.08.2024", "Date 6: dot format")
    
    # 1.7 "15-08-24" Context
    res = extract_dates_with_context(lines_date2)
    assert_eq(res["manufacturing_date"]["value"], "15-08-24", "Date 7: hyphen format YY")
    
    # 1.8 "15/08/24" Context
    res = extract_dates_with_context(lines_date3)
    assert_eq(res["manufacturing_date"]["value"], "15/08/24", "Date 8: slash format YY")
    
    # 1.9 Text-based month format
    res = extract_dates_with_context(lines_text)
    assert_eq(res["manufacturing_date"]["value"].upper(), "15 AUG 2024", "Date 9: Text format")
    
    # 1.10 Multiple dates
    lines_multi = [
        {"text": "MFD: 15/08/2024", "confidence": 0.9},
        {"text": "EXP: 15/08/2025", "confidence": 0.9}
    ]
    res = extract_dates_with_context(lines_multi)
    assert_eq(res["manufacturing_date"]["value"], "15/08/2024", "Date 10: Multi MFD")
    assert_eq(res["expiry_date"]["value"], "15/08/2025", "Date 10: Multi EXP")


    # 2. UNREADABLE ≠ MISSING (Compliance Engine logic)
    # Give the compliance engine a field marked as UNREADABLE
    fields = {"expiry_date": None}
    field_statuses = {"expiry_date": FIELD_STATUS_UNREADABLE}
    
    comp_res = check_compliance(fields, field_statuses=field_statuses, quality_tier="VERY_POOR")
    # Rule 4 is best_before / expiry.
    # It should yield a medium severity violation (REVIEW REQUIRED), not HIGH (MISSING)
    viol = [v for v in comp_res["violations"] if v["field"] == "best_before"][0]
    assert_eq(viol["severity"], "medium", "UNREADABLE != MISSING (Severity is medium)")
    assert_eq(viol["field_status"], FIELD_STATUS_UNREADABLE, "UNREADABLE status is preserved")


    # 3. Field Status Classification
    st = classify_field_status("mrp", None, 0.0, 0.0, "VERY_POOR")
    assert_eq(st, FIELD_STATUS_UNREADABLE, "Classify: UNREADABLE when VERY_POOR")
    
    st = classify_field_status("mrp", None, 0.0, 0.5, "GOOD")
    assert_eq(st, FIELD_STATUS_NOT_DETECTED, "Classify: NOT_DETECTED when GOOD but None")

    st = classify_field_status("mrp", "100", 0.45, 0.8, "GOOD")
    assert_eq(st, FIELD_STATUS_LOW_CONFIDENCE, "Classify: LOW_CONFIDENCE when conf < 0.5")


    # 4. Field-level candidate selection across variants
    # Mock variant_results
    variant_results = {
        "clahe": {
            "lines": [
                {"text": "MRP: 50.00", "confidence": 0.9, "bbox": None},
                {"text": "EXP 01/2024", "confidence": 0.3, "bbox": None}
            ]
        },
        "otsu": {
            "lines": [
                {"text": "MAP: 50.00", "confidence": 0.4, "bbox": None},
                {"text": "EXP 01/2025", "confidence": 0.95, "bbox": None}
            ]
        }
    }
    
    best_mrp = select_best_field_candidate("mrp", variant_results)
    assert_eq(best_mrp["value"], "₹50.00", "Field-level: MRP from CLAHE (best)")
    assert_eq(best_mrp["source_variant"], "clahe", "Field-level: MRP source is clahe")
    
    best_exp = select_best_field_candidate("expiry_date", variant_results)
    assert_eq(best_exp["value"], "01/2025", "Field-level: EXP from OTSU (best)")
    assert_eq(best_exp["source_variant"], "otsu", "Field-level: EXP source is otsu")


    # 5. Food Product Detection
    assert_eq(is_food_product({"fssai": "12345678901234"}), True, "Food detection: FSSAI implies food")
    assert_eq(is_food_product({}, "INGREDIENTS: Water, Sugar"), True, "Food detection: ingredients in text")
    assert_eq(is_food_product({}, "SHAMPOO 500ml"), False, "Food detection: no food keywords")

    print("\n-------------------------")
    print(f"Total passed: {passed}")
    print(f"Total failed: {failures}")
    print("-------------------------")
    
    if failures > 0:
        sys.exit(1)


if __name__ == "__main__":
    run_tests()
