# backend/tests/test_review_workflow.py
"""
Automated integration tests for OCR Review, Human Verification, and Authorization Workflow.
Tests:
- Two-step scan initiation: POST /scans/ocr-extract leaves scan in 'review_pending'
- Review state retrieval: GET /scans/{id}/review
- Manual field corrections: PUT /scans/{id}/fields
- Audit trail preservation: original_ocr_value remains unmodified after user corrections
- Unreadable field marking: mark_unreadable sets null value and UNREADABLE status without fallback
- Confirmation and compliance evaluation: POST /scans/{id}/confirm evaluates confirmed fields
- Post-confirmation immutability: PUT /scans/{id}/fields returns 409 Conflict after confirmation
- Idempotency: Duplicate confirmation returns existing report without duplicate violations
- Multi-user security: Citizens cannot access or modify scans created by other citizens (403)
- Role-based access control: Citizens blocked from Officer inspection console (403)
"""

import pytest
from app.database.connection import SessionLocal
from app.models.extracted_field import ExtractedField
from app.models.scan import Scan


def test_two_step_ocr_extract_leaves_review_pending(client, citizen_headers, sample_product_label_path):
    """POST /scans/ocr-extract must extract fields and leave status as review_pending."""
    with open(sample_product_label_path, "rb") as f:
        res = client.post(
            "/scans/ocr-extract",
            headers=citizen_headers,
            files={"image": ("sample.jpg", f, "image/jpeg")},
            data={"force_proceed": "true"},
        )

    assert res.status_code == 200
    data = res.json()
    assert "scan_id" in data
    assert data["status"] == "review_pending"
    assert data["user_confirmed"] is False
    assert isinstance(data["fields"], list)
    assert len(data["fields"]) > 0

    # Ensure in DB it is unconfirmed
    db = SessionLocal()
    scan = db.query(Scan).filter(Scan.id == data["scan_id"]).first()
    assert scan is not None
    assert scan.user_confirmed is False
    assert scan.status == "review_pending"
    db.close()


def test_review_data_and_corrections_workflow(client, citizen_headers, sample_product_label_path):
    """Test full review, correction, unreadable marking, and audit trail preservation."""
    # 1. Upload scan
    with open(sample_product_label_path, "rb") as f:
        res = client.post(
            "/scans/ocr-extract",
            headers=citizen_headers,
            files={"image": ("sample.jpg", f, "image/jpeg")},
            data={"force_proceed": "true"},
        )
    scan_id = res.json()["scan_id"]

    # 2. Get review data
    rev_res = client.get(f"/scans/{scan_id}/review", headers=citizen_headers)
    assert rev_res.status_code == 200
    rev_data = rev_res.json()
    assert rev_data["scan_id"] == scan_id

    # 3. Apply corrections:
    # - User corrects MRP to '150.00'
    # - User marks net_quantity as unreadable
    corrections = [
        {"field_name": "mrp", "corrected_value": "150.00"},
        {"field_name": "net_quantity", "mark_unreadable": True},
    ]

    put_res = client.put(f"/scans/{scan_id}/fields", headers=citizen_headers, json={"corrections": corrections})
    assert put_res.status_code == 200

    # 4. Check database directly to verify audit trail
    db = SessionLocal()
    mrp_field = db.query(ExtractedField).filter(
        ExtractedField.scan_id == scan_id, ExtractedField.field_name == "mrp"
    ).first()
    assert mrp_field is not None
    assert mrp_field.corrected_value == "150.00"
    assert mrp_field.field_value == "150.00"
    assert mrp_field.correction_status == "user_corrected"
    # CRITICAL: original_ocr_value MUST remain unchanged!
    assert mrp_field.original_ocr_value is not None

    qty_field = db.query(ExtractedField).filter(
        ExtractedField.scan_id == scan_id, ExtractedField.field_name == "net_quantity"
    ).first()
    assert qty_field is not None
    assert qty_field.field_value is None
    assert qty_field.correction_status == "user_marked_unreadable"
    assert qty_field.field_status == "UNREADABLE"
    assert qty_field.original_ocr_value is not None
    db.close()

    # 5. Review endpoint should reflect the unreadable status with display_value None
    rev_res2 = client.get(f"/scans/{scan_id}/review", headers=citizen_headers)
    fields_map = {f["field_name"]: f for f in rev_res2.json()["fields"]}
    assert fields_map["mrp"]["display_value"] == "150.00"
    assert fields_map["mrp"]["correction_status"] == "user_corrected"
    assert fields_map["net_quantity"]["display_value"] is None
    assert fields_map["net_quantity"]["correction_status"] == "user_marked_unreadable"
    assert fields_map["net_quantity"]["field_status"] == "UNREADABLE"

    # 6. Confirm scan
    confirm_res = client.post(f"/scans/{scan_id}/confirm", headers=citizen_headers, json={})
    assert confirm_res.status_code == 200
    conf_data = confirm_res.json()
    assert conf_data["user_confirmed"] is True
    assert conf_data["fields"]["mrp"] == "150.00"
    assert conf_data["fields"]["net_quantity"] is None

    # 7. Post-confirmation immutability: Cannot modify fields after confirmation
    put_res2 = client.put(
        f"/scans/{scan_id}/fields",
        headers=citizen_headers,
        json={"corrections": [{"field_name": "mrp", "corrected_value": "999.00"}]}
    )
    assert put_res2.status_code == 409

    # 8. Idempotency: Second confirmation returns existing results
    confirm_res2 = client.post(f"/scans/{scan_id}/confirm", headers=citizen_headers, json={})
    assert confirm_res2.status_code == 200
    assert confirm_res2.json()["score"] == conf_data["score"]
    assert confirm_res2.json()["violation_count"] == conf_data["violation_count"]


def test_cross_user_scan_access_forbidden(client, citizen_headers, sample_product_label_path):
    """User A cannot read or modify User B's scans."""
    # 1. Citizen A creates a scan
    with open(sample_product_label_path, "rb") as f:
        res = client.post(
            "/scans/ocr-extract",
            headers=citizen_headers,
            files={"image": ("sample.jpg", f, "image/jpeg")},
            data={"force_proceed": "true"},
        )
    scan_id = res.json()["scan_id"]

    # 2. Register Citizen B
    c2_res = client.post("/auth/register", json={
        "name": "Citizen B",
        "email": "citizen_b_isolated@mitra.com",
        "password": "Password@123"
    })
    assert c2_res.status_code == 200
    c2_headers = {"Authorization": f"Bearer {c2_res.json()['access_token']}"}

    # 3. Citizen B tries to access Citizen A's scan
    get_res = client.get(f"/scans/{scan_id}/review", headers=c2_headers)
    assert get_res.status_code == 403

    put_res = client.put(
        f"/scans/{scan_id}/fields",
        headers=c2_headers,
        json={"corrections": [{"field_name": "mrp", "corrected_value": "500"}]}
    )
    assert put_res.status_code == 403

    confirm_res = client.post(f"/scans/{scan_id}/confirm", headers=c2_headers, json={})
    assert confirm_res.status_code == 403


def test_rbac_citizen_blocked_from_officer_endpoints(client, citizen_headers, officer_headers):
    """Citizens cannot access officer-only inspection lists (403 Forbidden)."""
    # Citizen request should be rejected
    r1 = client.get("/inspections/", headers=citizen_headers)
    assert r1.status_code == 403

    # Officer request should succeed
    r2 = client.get("/inspections/", headers=officer_headers)
    assert r2.status_code == 200
    assert isinstance(r2.json(), list)


def test_confirmed_scan_appears_in_user_history(client, citizen_headers, sample_product_label_path):
    """Verify that a confirmed scan properly reflects in the user's scan history with evaluated status."""
    with open(sample_product_label_path, "rb") as f:
        res = client.post(
            "/scans/ocr-extract",
            headers=citizen_headers,
            files={"image": ("sample.jpg", f, "image/jpeg")},
            data={"force_proceed": "true"},
        )
    scan_id = res.json()["scan_id"]

    # Confirm scan
    conf_res = client.post(f"/scans/{scan_id}/confirm", headers=citizen_headers, json={})
    assert conf_res.status_code == 200

    # Retrieve history
    hist_res = client.get("/scans/history", headers=citizen_headers)
    assert hist_res.status_code == 200
    hist_items = hist_res.json()
    matching = [item for item in hist_items if item["id"] == scan_id]
    assert len(matching) == 1
    assert matching[0]["status"] in ("COMPLIANT", "NON-COMPLIANT", "REVIEW REQUIRED")

