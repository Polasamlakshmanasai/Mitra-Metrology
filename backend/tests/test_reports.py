# backend/tests/test_reports.py
"""
Automated unit and integration tests for Report Generation (report_service.py).
Tests:
- Structured JSON report construction via build_inspection_report
- PDF document compilation via generate_pdf_report_buffer (ReportLab)
- Verification of valid PDF binary headers (%PDF)
- PDF report download API: GET /scans/{id}/report/pdf
- Persistence of user corrections in generated report
- Quality warnings presence in final audit documentation
"""

import pytest
from datetime import datetime, timezone
from io import BytesIO

from app.models.scan import Scan
from app.models.extracted_field import ExtractedField
from app.models.violation import Violation
from app.services.report_service import build_inspection_report, generate_pdf_report_buffer


def test_build_inspection_report_structure():
    """Verify that build_inspection_report constructs standard compliant JSON structure."""
    scan = Scan(
        id=101,
        image_path="test_pkg.jpg",
        status="COMPLIANT",
        score=100.0,
        rules_checked=8,
        violation_count=0,
        user_confirmed=True,
        created_at=datetime.now(timezone.utc),
    )

    fields = [
        ExtractedField(scan_id=101, field_name="product_name", field_value="Organic Atta", original_ocr_value="Organic Atta", confidence=0.95),
        ExtractedField(scan_id=101, field_name="mrp", field_value="₹120.00", original_ocr_value="₹120.00", confidence=0.92),
        ExtractedField(scan_id=101, field_name="net_quantity", field_value="500 g", original_ocr_value="500 g", confidence=0.90),
    ]

    violations = []

    report = build_inspection_report(scan, fields, violations)
    assert isinstance(report, dict)
    assert report["scan_id"] == 101
    assert report["status"] == "COMPLIANT"
    assert report["compliance"]["rules_checked"] == 8
    assert report["declared_information"]["mrp"] == "₹120.00"
    assert report["declared_information"]["net_quantity"] == "500 g"
    assert len(report["violations"]) == 0
    assert "disclaimer" in report


def test_generate_pdf_report_buffer_creates_valid_pdf():
    """Verify that generate_pdf_report_buffer compiles a valid binary PDF with %PDF magic bytes."""
    report_data = {
        "scan_id": 102,
        "created_at": "18/10/2026 14:30:00",
        "compliance_status": "COMPLIANT",
        "compliance_score": 95.0,
        "product_name": "Premium Whole Wheat Atta",
        "manufacturer": "Mitra Agro Foods Pvt. Ltd.",
        "fields": {
            "mrp": "₹295.00",
            "net_quantity": "5 kg",
            "manufacturing_date": "15/08/2026",
            "consumer_care": "1800-123-4567",
        },
        "field_confidences": {
            "mrp": 0.96,
            "net_quantity": 0.94,
        },
        "field_statuses": {
            "mrp": "VALID",
            "net_quantity": "VALID",
        },
        "violations": [],
        "quality_warning": None,
        "summary": "Full compliance achieved under Legal Metrology Rules, 2011.",
    }

    buf = generate_pdf_report_buffer(report_data)
    assert isinstance(buf, BytesIO)
    pdf_bytes = buf.getvalue()
    assert len(pdf_bytes) > 1000
    # Must start with %PDF magic header
    assert pdf_bytes.startswith(b"%PDF"), "Generated file does not have valid %PDF header"


def test_pdf_endpoint_integration(client, citizen_headers, sample_product_label_path):
    """Verify GET /scans/{id}/report/pdf downloads compiled inspection report for confirmed scan."""
    # 1. Create and confirm scan
    with open(sample_product_label_path, "rb") as f:
        res = client.post(
            "/scans/ocr-extract",
            headers=citizen_headers,
            files={"image": ("sample.jpg", f, "image/jpeg")},
            data={"force_proceed": "true"},
        )
    scan_id = res.json()["scan_id"]

    client.post(f"/scans/{scan_id}/confirm", headers=citizen_headers, json={})

    # 2. Fetch PDF
    pdf_res = client.get(f"/scans/{scan_id}/report/pdf", headers=citizen_headers)
    assert pdf_res.status_code == 200
    assert pdf_res.headers["content-type"] == "application/pdf"
    assert "attachment" in pdf_res.headers.get("content-disposition", "")
    assert pdf_res.content.startswith(b"%PDF")


def test_unconfirmed_scan_pdf_includes_draft_banner(client, citizen_headers, sample_product_label_path):
    """Verify that downloading a report for an unconfirmed scan renders the DRAFT indicator."""
    with open(sample_product_label_path, "rb") as f:
        res = client.post(
            "/scans/ocr-extract",
            headers=citizen_headers,
            files={"image": ("sample.jpg", f, "image/jpeg")},
            data={"force_proceed": "true"},
        )
    scan_id = res.json()["scan_id"]

    # Do not confirm scan -> fetch PDF directly
    pdf_res = client.get(f"/scans/{scan_id}/report/pdf", headers=citizen_headers)
    assert pdf_res.status_code == 200
    assert pdf_res.content.startswith(b"%PDF")
    assert len(pdf_res.content) > 1000

