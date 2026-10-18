# backend/tests/test_regression.py
"""
Automated Regression Test Suite for Known Failure Cases.
Tests:
1. MRP extraction: Comma decimal and spaced decimal handling (preventing ₹45000 when ₹450.00 expected)
2. Net quantity extraction: Unit normalization across gm, gms, ml, L, kg
3. Manufacturing vs Expiry date confusion: Disambiguating dates when both appear on single/adjacent lines
4. Expiry vs Best-before separation: Preventing merged/overwritten duration vs calendar date
5. Unreadable field fallback prevention: Unreadable field must remain null, never reverting to raw OCR
6. Premature compliance evaluation: Ensuring compliance is evaluated only upon user confirmation
7. Human correction persistence in final report: Ensuring corrected values are preserved in output
8. Image quality warning communication: Communicating blur/overexposure issues to user
"""

import pytest
from app.database.connection import SessionLocal
from app.models.scan import Scan
from app.models.extracted_field import ExtractedField
from ai_engine.extraction import (
    normalize_mrp,
    extract_mrp,
    normalize_quantity,
    extract_net_quantity,
    extract_dates_with_context,
)
from ai_engine.image_quality import check_image_quality
from app.services.compliance_service import analyze_product


# ── Regression 1: MRP Extraction Decimal Accuracy ─────────────────────────────
def test_regression_mrp_comma_decimal():
    """
    Regression: On Indian retail packages and OCR misreads, decimal points frequently appear as commas (e.g. 450,00).
    The extractor must extract ₹450.00, NOT ₹450 and NOT ₹45000.
    """
    raw_ocr = "MRP. Ps 450,00 (Incl ofall taxes)"
    val = normalize_mrp(raw_ocr)
    assert val == "₹450.00", f"Expected '₹450.00', got: {val}"


def test_regression_mrp_spaced_decimal():
    """
    Regression: OCR spacing around decimal (e.g. 'MRP Rs. 450 . 00') must not truncate at 450.
    """
    raw_ocr = "MRP: Rs. 450 . 00"
    val = normalize_mrp(raw_ocr)
    assert val == "₹450.00", f"Expected '₹450.00', got: {val}"


def test_regression_mrp_no_excessive_zeros():
    """
    Regression: ₹45000 must never be extracted when the package clearly specifies ₹450.00.
    """
    line = {"text": "MRP: Rs 450.00 (INCL. OF ALL TAXES)", "confidence": 0.95, "bbox": None}
    res = extract_mrp([line])
    assert res is not None
    assert res["value"] == "₹450.00"
    assert res["value"] != "₹45000"


# ── Regression 2: Net Quantity Extraction ─────────────────────────────────────
@pytest.mark.parametrize("line_text, expected_qty", [
    ("Net Wt.: 500 gm", "500 g"),
    ("Net Quantity: 500 gms", "500 g"),
    ("NET WT: 1000g", "1000 g"),
    ("Net Content: 750 ml", "750 ml"),
    ("Net Vol: 1.5 L", "1.5 L"),
    ("NET QUANTITY: 10 kg", "10 kg"),
])
def test_regression_net_quantity_abbreviations(line_text, expected_qty):
    """
    Regression: Net quantity must accurately resolve 'gm', 'gms', 'kg', 'ml', 'L' without dropping units.
    """
    line = {"text": line_text, "confidence": 0.92, "bbox": None}
    res = extract_net_quantity([line])
    assert res is not None, f"Failed to extract net quantity from: {line_text}"
    assert res["value"] == expected_qty


def test_regression_net_quantity_mixed_line():
    """
    Regression: Net quantity on a line containing other numbers (e.g. 'Best Before 9 Months. Net Qty: 500 g')
    must extract '500 g', not '9 Months'.
    """
    line = {"text": "Best Before 9 Months. Net Qty: 500 g", "confidence": 0.90, "bbox": None}
    res = extract_net_quantity([line])
    assert res is not None
    assert res["value"] == "500 g"


# ── Regression 3: Manufacturing vs Expiry Date Confusion ──────────────────────
def test_regression_mfg_and_exp_on_same_line():
    """
    Regression: When MFD and EXP appear on the same line, both must be extracted into their respective slots.
    """
    lines = [{"text": "MFD: 10/01/2025 EXP: 10/07/2025", "confidence": 0.92, "bbox": None}]
    dates = extract_dates_with_context(lines)
    assert dates["manufacturing_date"] is not None
    assert dates["manufacturing_date"]["value"] == "10/01/2025"
    assert dates["expiry_date"] is not None
    assert dates["expiry_date"]["value"] == "10/07/2025"


def test_regression_exp_before_mfg_reversed_order():
    """
    Regression: When EXP appears before MFD on the same line, EXP must not be assigned to manufacturing date.
    """
    lines = [{"text": "EXP: 10/07/2025 MFD: 10/01/2025", "confidence": 0.92, "bbox": None}]
    dates = extract_dates_with_context(lines)
    assert dates["manufacturing_date"] is not None
    assert dates["manufacturing_date"]["value"] == "10/01/2025"
    assert dates["expiry_date"] is not None
    assert dates["expiry_date"]["value"] == "10/07/2025"


# ── Regression 4: Expiry vs Best-Before Separation ────────────────────────────
def test_regression_expiry_and_best_before_separation():
    """
    Regression: A package having both explicit expiry and best before text must not merge or overwrite them.
    """
    lines = [
        {"text": "MFD: 01/01/2025", "confidence": 0.92, "bbox": None},
        {"text": "BEST BEFORE: 6 MONTHS FROM PACKAGING", "confidence": 0.95, "bbox": None},
        {"text": "EXPIRY DATE: 30/06/2025", "confidence": 0.91, "bbox": None},
    ]
    dates = extract_dates_with_context(lines)
    assert dates["best_before"] is not None
    assert "6 MONTHS" in dates["best_before"]["value"].upper()
    assert dates["expiry_date"] is not None
    assert dates["expiry_date"]["value"] == "30/06/2025"
    assert dates["best_before"]["value"] != dates["expiry_date"]["value"]


# ── Regression 5: Unreadable Field Fallback Prevention ────────────────────────
def test_regression_unreadable_field_does_not_fallback(client, citizen_headers, sample_product_label_path):
    """
    Regression: Marking a field as unreadable must NOT display original OCR value as confirmed value.
    """
    # 1. Create scan
    with open(sample_product_label_path, "rb") as f:
        res = client.post(
            "/scans/ocr-extract",
            headers=citizen_headers,
            files={"image": ("sample.jpg", f, "image/jpeg")},
            data={"force_proceed": "true"},
        )
    scan_id = res.json()["scan_id"]

    # 2. Mark net_quantity as unreadable
    client.put(
        f"/scans/{scan_id}/fields",
        headers=citizen_headers,
        json={"corrections": [{"field_name": "net_quantity", "mark_unreadable": True}]}
    )

    # 3. Confirm scan
    confirm_res = client.post(f"/scans/{scan_id}/confirm", headers=citizen_headers, json={})
    conf_fields = confirm_res.json()["fields"]

    # Must be None, not the original OCR value
    assert conf_fields["net_quantity"] is None, f"Expected None for unreadable field, got: {conf_fields['net_quantity']}"


# ── Regression 6: Premature Compliance Evaluation ─────────────────────────────
def test_regression_no_premature_compliance(client, citizen_headers, sample_product_label_path):
    """
    Regression: OCR extraction alone must not finalize compliance evaluation before human confirmation.
    """
    with open(sample_product_label_path, "rb") as f:
        res = client.post(
            "/scans/ocr-extract",
            headers=citizen_headers,
            files={"image": ("sample.jpg", f, "image/jpeg")},
            data={"force_proceed": "true"},
        )
    data = res.json()
    assert data["status"] == "review_pending"
    assert data["user_confirmed"] is False

    db = SessionLocal()
    scan = db.query(Scan).filter(Scan.id == data["scan_id"]).first()
    assert scan.user_confirmed is False
    assert scan.confirmed_at is None
    db.close()


# ── Regression 7: Corrections Reflected in Final Report ───────────────────────
def test_regression_corrections_in_final_report(client, citizen_headers, sample_product_label_path):
    """
    Regression: User corrections must be used in the final compliance result and PDF report.
    """
    with open(sample_product_label_path, "rb") as f:
        res = client.post(
            "/scans/ocr-extract",
            headers=citizen_headers,
            files={"image": ("sample.jpg", f, "image/jpeg")},
            data={"force_proceed": "true"},
        )
    scan_id = res.json()["scan_id"]

    # Correct MRP to ₹199.00
    client.put(
        f"/scans/{scan_id}/fields",
        headers=citizen_headers,
        json={"corrections": [{"field_name": "mrp", "corrected_value": "199.00"}]}
    )

    confirm_res = client.post(f"/scans/{scan_id}/confirm", headers=citizen_headers, json={})
    assert confirm_res.json()["fields"]["mrp"] == "199.00"

    # Fetch PDF report and verify 200 OK
    pdf_res = client.get(f"/scans/{scan_id}/report/pdf", headers=citizen_headers)
    assert pdf_res.status_code == 200
    assert pdf_res.content.startswith(b"%PDF")


# ── Regression 8: Image Quality Communication ─────────────────────────────────
def test_regression_image_quality_communicated_to_user(client, citizen_headers, blurry_package_path):
    """
    Regression: Degraded / blurry images must communicate quality warning to user in review and pipeline output.
    """
    with open(blurry_package_path, "rb") as f:
        res = client.post(
            "/scans/ocr-extract",
            headers=citizen_headers,
            files={"image": ("blurry.jpg", f, "image/jpeg")},
            data={"force_proceed": "true"},
        )
    data = res.json()
    assert data.get("has_quality_warning") is True or data.get("image_quality_warning") is not None
    assert data["quality_tier"] in ("POOR", "VERY_POOR")


# ── Regression 9: Synthetic Packaging Multi-Field OCR (Synthetic Lay's Fixture) ─
def test_regression_lays_packaging_extraction():
    """
    Regression: Test synthetic packaging fixture (AI-generated Lay's mock label).
    Note: This is an AI-generated synthetic test fixture, NOT a verified real retail product.
    Verifies that multi-variant OCR extracts dates, MRP, product name, and address
    without bracket corruption, zero inflation, or date confusion.
    """
    import os
    fixture_path = "backend/uploads/Lays_yellow_3553e1c9.png"
    if not os.path.exists(fixture_path):
        pytest.skip(f"Synthetic fixture not found: {fixture_path}")

    res = analyze_product(fixture_path)
    fields = res.get("fields", {})

    # MRP extracted accurately with rupee symbol and correct decimal
    assert fields.get("mrp") == "₹20.00"
    # Dates extracted accurately without inversion
    assert fields.get("manufacturing_date") == "15/06/2024"
    assert fields.get("expiry_date") == "14/12/2024"
    # Clean product name without bracket noise
    assert fields.get("product_name") == "Lay's"
    # Address recognized
    assert "Industrial Area" in str(fields.get("manufacturer_address", ""))
    # Identified as food product
    assert res.get("is_food_product") is True


# ── Regression 10: ReportLab PDF Draft Banner & Regime Segregation ───────────
def test_regression_report_regime_segregation_and_draft_watermark():
    """
    Regression: PDF and JSON reports must segregate Legal Metrology vs FSSAI findings,
    display a draft watermark banner for unconfirmed scans, and omit misleading
    'Declared on Package' placeholders.
    """
    from datetime import datetime, timezone
    from app.services.report_service import build_inspection_report, generate_pdf_report_buffer
    from app.models.scan import Scan
    from app.models.extracted_field import ExtractedField
    from app.models.violation import Violation

    # 1. Unconfirmed scan (Draft)
    unconfirmed_scan = Scan(
        id=901,
        image_path="test.jpg",
        status="REVIEW REQUIRED",
        score=75.0,
        rules_checked=8,
        violation_count=2,
        user_confirmed=False,
        created_at=datetime.now(timezone.utc),
    )
    fields = [
        ExtractedField(scan_id=901, field_name="product_name", field_value="Lay's", original_ocr_value="Lay's", confidence=0.90),
        ExtractedField(scan_id=901, field_name="mrp", field_value="₹20.00", original_ocr_value="₹20.00", confidence=0.95),
    ]
    violations = [
        Violation(scan_id=901, field="net_quantity", description="Net quantity declaration is absent from label", severity="high"),
        Violation(scan_id=901, field="fssai", description="FSSAI license number was not detected by OCR on this panel", severity="medium"),
    ]

    report = build_inspection_report(unconfirmed_scan, fields, violations)
    assert report["is_draft"] is True
    assert "DRAFT" in report["draft_banner"]
    assert report["declared_information"]["mrp"] == "₹20.00"
    # Misleading placeholder must not be present
    assert report["product"]["manufacturer"] != "Declared on Package"
    assert report["product"]["manufacturer"] == "NOT DETECTED"
    # Separate regime listings
    assert len(report["legal_metrology_violations"]) == 1
    assert len(report["fssai_violations"]) == 1
    assert report["legal_metrology_violations"][0]["field"] == "net_quantity"
    assert report["fssai_violations"][0]["field"] == "fssai"

    # Verify PDF compilation with draft watermark
    pdf_buf = generate_pdf_report_buffer(report)
    pdf_bytes = pdf_buf.getvalue()
    assert pdf_bytes.startswith(b"%PDF")
    assert len(pdf_bytes) > 2000

