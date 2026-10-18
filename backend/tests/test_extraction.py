# backend/tests/test_extraction.py
"""
Automated unit tests for Field Extraction Engine (extraction.py).
Tests:
- MRP pattern recognition across standard Indian retail formats
- Net quantity parsing across weight, volume, and unit denominations
- Context-aware date extraction (Manufacturing vs Expiry vs Best Before)
- Manufacturer, Address, Consumer Care, and FSSAI license extraction
- Field status classification (VALID, LOW_CONFIDENCE, UNREADABLE, NOT_DETECTED)
- Multi-variant candidate selection scoring
"""

import pytest

from ai_engine.extraction import (
    normalize_mrp,
    extract_mrp,
    normalize_quantity,
    extract_net_quantity,
    extract_date,
    extract_manufacturing_date,
    extract_expiry,
    extract_dates_with_context,
    extract_manufacturer,
    extract_manufacturer_address,
    extract_consumer_care,
    extract_fssai,
    extract_fields,
    classify_field_status,
    select_best_field_candidate,
    FIELD_STATUS_VALID,
    FIELD_STATUS_LOW_CONFIDENCE,
    FIELD_STATUS_UNREADABLE,
    FIELD_STATUS_NOT_DETECTED,
)


# ── 1. MRP Extraction Tests ───────────────────────────────────────────────────
@pytest.mark.parametrize("raw_text, expected_mrp", [
    ("MRP Rs. 295.00", "₹295.00"),
    ("MRP ₹295/-", "₹295"),
    ("MAXIMUM RETAIL PRICE: Rs 450.00 (INCL. OF ALL TAXES)", "₹450.00"),
    ("M.R.P. RS. 120.00", "₹120.00"),
    ("MRP: Rs 150", "₹150"),
    ("MRP ₹ 1250.00", "₹1250.00"),
    ("M.R.P. ₹85.50", "₹85.50"),
    ("MRP: Rs 450,00 (Incl. of all taxes)", "₹450.00"),  # Common OCR comma-decimal
])
def test_normalize_mrp_formats(raw_text, expected_mrp):
    """Test MRP normalization handles diverse Indian currency prefixes, punctuation, and decimals."""
    result = normalize_mrp(raw_text)
    assert result == expected_mrp, f"Failed for '{raw_text}': expected '{expected_mrp}', got '{result}'"


def test_extract_mrp_from_lines():
    """Test extract_mrp scans OCR line records and returns structured match."""
    lines = [
        {"text": "WHOLE WHEAT FLOUR", "confidence": 0.95, "bbox": None},
        {"text": "NET QTY: 5 kg", "confidence": 0.90, "bbox": None},
        {"text": "MRP Rs 295.00 (INCL. OF ALL TAXES)", "confidence": 0.96, "bbox": {"x": 10, "y": 80, "w": 200, "h": 25}},
    ]
    res = extract_mrp(lines)
    assert res is not None
    assert res["value"] == "₹295.00"
    assert res["ocr_confidence"] == 0.96
    assert res["bbox"] is not None


# ── 2. Net Quantity Extraction Tests ──────────────────────────────────────────
@pytest.mark.parametrize("raw_text, expected_qty", [
    ("NET QUANTITY: 5 kg", "5 kg"),
    ("Net Wt. 500 g", "500 g"),
    ("Net Qty: 750 ml", "750 ml"),
    ("Net Volume: 1.5 L", "1.5 L"),
    ("Net Weight: 10 kg", "10 kg"),
    ("Contents: 100 gms", "100 g"),
    ("Net Quantity: 500 gm", "500 g"),
    ("Net: 10 pcs", "10 pcs"),
    ("NET WT: 5 Kilogram", "5 kg"),
])
def test_normalize_quantity_denominations(raw_text, expected_qty):
    """Test net quantity parsing across grams, kilograms, milliliters, liters, and pieces."""
    result = normalize_quantity(raw_text)
    assert result == expected_qty, f"Failed for '{raw_text}': expected '{expected_qty}', got '{result}'"


def test_extract_net_quantity_from_lines():
    """Test extract_net_quantity scans OCR line records."""
    lines = [
        {"text": "ORGANIC ROASTED NAMKEEN", "confidence": 0.90, "bbox": None},
        {"text": "NET QUANTITY: 200 g", "confidence": 0.92, "bbox": {"x": 20, "y": 60, "w": 150, "h": 20}},
        {"text": "MRP Rs 55.00", "confidence": 0.95, "bbox": None},
    ]
    res = extract_net_quantity(lines)
    assert res is not None
    assert res["value"] == "200 g"
    assert res["ocr_confidence"] == 0.92


# ── 3. Date Extraction Tests ──────────────────────────────────────────────────
@pytest.mark.parametrize("raw_text, expected_date", [
    ("MFD: 15/08/2024", "15/08/2024"),
    ("PKD ON: 12-01-2025", "12-01-2025"),
    ("Date of Pkg: 10.05.2024", "10.05.2024"),
    ("MFG: 01/2025", "01/2025"),
    ("Manufactured: 15 Aug 2024", "15 Aug 2024"),
])
def test_extract_date_patterns(raw_text, expected_date):
    """Test date parsing handles slashes, dashes, dots, two-digit months, and text months."""
    extracted = extract_date(raw_text)
    assert extracted == expected_date


def test_extract_dates_with_context_separation():
    """Test that context-aware extraction keeps mfg date, expiry date, and best before separate."""
    lines = [
        {"text": "MFD: 10/01/2025", "confidence": 0.92, "bbox": None},
        {"text": "EXPIRY DATE: 09/10/2025", "confidence": 0.88, "bbox": None},
        {"text": "BEST BEFORE 9 MONTHS FROM PACKAGING", "confidence": 0.95, "bbox": None},
    ]
    res = extract_dates_with_context(lines)

    assert res["manufacturing_date"] is not None
    assert res["manufacturing_date"]["value"] == "10/01/2025"

    assert res["expiry_date"] is not None
    assert res["expiry_date"]["value"] == "09/10/2025"

    assert res["best_before"] is not None
    assert "9 MONTHS" in res["best_before"]["value"].upper()


# ── 4. Manufacturer, Address, Consumer Care & FSSAI Tests ─────────────────────
def test_extract_manufacturer_from_lines():
    lines = [
        {"text": "BEST FLOUR CO.", "confidence": 0.90, "bbox": None},
        {"text": "MANUFACTURED BY: Mitra Agro Foods Pvt. Ltd.", "confidence": 0.93, "bbox": None},
        {"text": "ADDRESS: Plot 42, Industrial Area, New Delhi - 110020", "confidence": 0.89, "bbox": None},
    ]
    mfg = extract_manufacturer(lines)
    assert mfg is not None
    assert "Mitra Agro Foods Pvt. Ltd." in mfg["value"]

    addr = extract_manufacturer_address(lines)
    assert addr is not None
    assert "New Delhi - 110020" in addr["value"]


def test_extract_consumer_care_from_lines():
    lines = [
        {"text": "FOR CONSUMER COMPLAINTS / FEEDBACK:", "confidence": 0.90, "bbox": None},
        {"text": "CONSUMER CARE: 1800-123-4567 | care@mitra.com", "confidence": 0.94, "bbox": None},
    ]
    cc = extract_consumer_care(lines)
    assert cc is not None
    assert "1800-123-4567" in cc["value"]


def test_extract_fssai_from_lines():
    lines = [
        {"text": "100% VEGETARIAN", "confidence": 0.90, "bbox": None},
        {"text": "FSSAI LIC NO: 10019022009876", "confidence": 0.97, "bbox": None},
    ]
    fssai = extract_fssai(lines)
    assert fssai is not None
    assert fssai["value"] == "10019022009876"


# ── 5. Field Status Classification Tests ──────────────────────────────────────
def test_classify_field_status_matrix():
    """Verify field classification into VALID, LOW_CONFIDENCE, UNREADABLE, NOT_DETECTED."""
    # Extracted with high confidence
    assert classify_field_status("mrp", "₹295.00", ocr_confidence=0.92, quality_score=0.9, quality_tier="GOOD") == FIELD_STATUS_VALID

    # Extracted with borderline/low confidence
    assert classify_field_status("mrp", "₹295.00", ocr_confidence=0.55, quality_score=0.9, quality_tier="GOOD") == FIELD_STATUS_LOW_CONFIDENCE

    # Not extracted on acceptable quality image (absent or missed by OCR, but NOT unreadable)
    assert classify_field_status("mrp", None, ocr_confidence=0.0, quality_score=0.85, quality_tier="GOOD") == FIELD_STATUS_NOT_DETECTED

    # Not extracted on severely degraded image (unreadable due to physical blur/exposure)
    assert classify_field_status("mrp", None, ocr_confidence=0.0, quality_score=0.10, quality_tier="VERY_POOR") == FIELD_STATUS_UNREADABLE


# ── 6. Candidate Selection Across Multi-Variant OCR ───────────────────────────
def test_select_best_field_candidate():
    """Verify select_best_field_candidate prioritizes valid format and agreement across variants."""
    variant_results = {
        "clahe": {
            "lines": [{"text": "MRP Rs 295.00", "confidence": 0.91, "bbox": None}]
        },
        "otsu": {
            "lines": [{"text": "MRP Rs 295.00", "confidence": 0.93, "bbox": None}]
        },
        "sharp": {
            "lines": [{"text": "MRP Ps 295", "confidence": 0.70, "bbox": None}]
        },
        "inverted": {
            "lines": []
        }
    }

    best = select_best_field_candidate("mrp", variant_results, quality_tier="GOOD")
    assert best["value"] == "₹295.00"
    assert best["status"] == FIELD_STATUS_VALID
    assert len(best["candidates"]) >= 2
