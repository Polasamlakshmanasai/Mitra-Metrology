# backend/tests/test_compliance.py
"""
Automated unit tests for Legal Metrology & FSSAI Compliance Rule Engine (rule_engine.py).
Tests:
- Deterministic statutory rule evaluation across 8 Legal Metrology declarations
- Full compliance evaluation (COMPLIANT)
- Missing mandatory field detection (NON-COMPLIANT)
- Unreadable and low-confidence field classification (REVIEW REQUIRED)
- Conditional FSSAI food product detection
- Impact of human-corrected fields on final compliance decision
"""

import pytest

from rules.rule_engine import (
    check_compliance,
    is_food_product,
    FIELD_STATUS_VALID,
    FIELD_STATUS_LOW_CONFIDENCE,
    FIELD_STATUS_UNREADABLE,
    FIELD_STATUS_NOT_DETECTED,
    FIELD_STATUS_MISSING,
)


def test_fully_compliant_packaged_commodity():
    """Verify that a package with all 8 valid Legal Metrology declarations receives COMPLIANT status."""
    fields = {
        "product_name": "Premium Whole Wheat Atta",
        "mrp": "₹295.00",
        "net_quantity": "5 kg",
        "manufacturing_date": "15/08/2026",
        "manufacturer": "Mitra Agro Foods Pvt. Ltd.",
        "manufacturer_address": "Plot 42, Industrial Area, New Delhi - 110020",
        "consumer_care": "1800-123-4567 | care@mitraagro.in",
        "country_of_origin": "India",
        "best_before": "6 MONTHS FROM PACKAGING",
        "fssai": "10019022009876",
    }
    field_statuses = {k: FIELD_STATUS_VALID for k in fields}

    res = check_compliance(fields, field_statuses=field_statuses, ocr_text="Made in India")
    assert res["status"] == "COMPLIANT"
    assert res["violation_count"] == 0
    assert res["rules_checked"] >= 8


def test_missing_mandatory_declarations_triggers_non_compliant():
    """Verify that missing critical statutory declarations (MRP, Net Qty) triggers NON-COMPLIANT."""
    fields = {
        "product_name": "Generic Flour",
        "mrp": None,  # Missing MRP
        "net_quantity": None,  # Missing Net Quantity
        "manufacturing_date": "15/08/2024",
        "manufacturer": "ABC Foods",
        "manufacturer_address": "New Delhi",
        "consumer_care": "1800-111-222",
    }
    field_statuses = {
        "mrp": FIELD_STATUS_NOT_DETECTED,
        "net_quantity": FIELD_STATUS_NOT_DETECTED,
        "manufacturing_date": FIELD_STATUS_VALID,
        "manufacturer": FIELD_STATUS_VALID,
        "manufacturer_address": FIELD_STATUS_VALID,
        "consumer_care": FIELD_STATUS_VALID,
    }

    res = check_compliance(fields, field_statuses=field_statuses)
    assert res["status"] == "NON-COMPLIANT"
    assert res["violation_count"] >= 2
    viol_fields = [v["field"] for v in res["violations"]]
    assert "mrp" in viol_fields
    assert "net_quantity" in viol_fields


def test_unreadable_field_triggers_review_required():
    """Unreadable or low-confidence fields must trigger REVIEW REQUIRED, never direct non-compliant."""
    fields = {
        "product_name": "Organic Atta",
        "mrp": "₹120.00",
        "net_quantity": "500 g",
        "manufacturing_date": None,  # Unreadable due to blur
        "manufacturer": "ABC Foods Ltd",
        "manufacturer_address": "Delhi",
        "consumer_care": "1800-000-000",
    }
    field_statuses = {
        "product_name": FIELD_STATUS_VALID,
        "mrp": FIELD_STATUS_VALID,
        "net_quantity": FIELD_STATUS_VALID,
        "manufacturing_date": FIELD_STATUS_UNREADABLE,
        "manufacturer": FIELD_STATUS_VALID,
        "manufacturer_address": FIELD_STATUS_VALID,
        "consumer_care": FIELD_STATUS_VALID,
    }

    res = check_compliance(fields, field_statuses=field_statuses)
    assert res["status"] == "REVIEW REQUIRED"
    unreadable_viols = [v for v in res["violations"] if v.get("field_status") == FIELD_STATUS_UNREADABLE]
    assert len(unreadable_viols) > 0


def test_is_food_product_detection():
    """Test heuristic differentiation of food products from general non-food commodities."""
    # Food product with FSSAI license
    assert is_food_product({"fssai": "10012021000456"}) is True

    # Food product with ingredients and nutrition in text
    food_text = "Ingredients: Refined wheat flour, sugar, edible vegetable oil. Nutritional facts per 100g."
    assert is_food_product({}, ocr_text=food_text) is True

    # Non-food commodity (e.g. electrical appliances or clothing)
    non_food_text = "Cotton Formal Shirt. Size: 42 cm (L). Color: Blue. Made in India. Wash in cold water."
    assert is_food_product({}, ocr_text=non_food_text) is False


def test_human_correction_resolves_violation():
    """Verify that replacing a missing value with a human-corrected value resolves the violation."""
    # Before correction: missing MRP
    fields_before = {"mrp": None, "net_quantity": "1 kg", "manufacturer": "Co Ltd", "manufacturer_address": "Delhi"}
    res_before = check_compliance(fields_before)
    assert any(v["field"] == "mrp" for v in res_before["violations"])

    # After correction: user provided ₹150.00
    fields_after = {"mrp": "₹150.00", "net_quantity": "1 kg", "manufacturer": "Co Ltd", "manufacturer_address": "Delhi"}
    field_statuses_after = {"mrp": FIELD_STATUS_VALID, "net_quantity": FIELD_STATUS_VALID, "manufacturer": FIELD_STATUS_VALID, "manufacturer_address": FIELD_STATUS_VALID}
    res_after = check_compliance(fields_after, field_statuses=field_statuses_after)
    assert not any(v["field"] == "mrp" for v in res_after["violations"])
