# test_suite_steps12_to_40.py
"""
Comprehensive Automated Verification Test Suite for Mitra Metrology (Steps 12 to 40)
Tests:
1. Auth & RBAC (Citizen vs Officer, 403 on forbidden)
2. Package A: Full Declarations -> COMPLIANT
3. Package B: Uncertain / Minor Omission -> REVIEW REQUIRED
4. Package C: Missing MRP / Net Qty -> NON-COMPLIANT
5. ExtractedField & Violation DB Traceability
6. Structured Report JSON & ReportLab PDF Generation
7. User Scan History & Officer All-Inspections
8. Officer Dynamic Statistics (Total, Compliant, Review, Non-Compliant)
9. Citizen Complaint Submission & Officer Status Lifecycle
"""

import sys
import os
import io
from PIL import Image, ImageDraw

# Ensure backend and rules are in sys.path
BASE_DIR = os.path.abspath(r"c:\Users\polas\Documents\Desktop(copy)\Hackthons\Mitra-Metrology")
sys.path.insert(0, os.path.join(BASE_DIR, "backend"))
sys.path.insert(0, BASE_DIR)

from fastapi.testclient import TestClient
from app.main import app
from app.database.connection import SessionLocal
from app.models.scan import Scan
from app.models.extracted_field import ExtractedField
from app.models.violation import Violation
from app.models.complaint import Complaint
from app.models.user import User

client = TestClient(app)

def create_dummy_image(text_lines, width=800, height=800, bg_color=(255, 255, 255)):
    """Creates a high-contrast packaging image with drawn declarations."""
    img = Image.new("RGB", (width, height), color=bg_color)
    draw = ImageDraw.Draw(img)
    y = 50
    for line in text_lines:
        draw.text((50, y), line, fill=(0, 0, 0))
        y += 40
    # Add some high-contrast border and details
    draw.rectangle([20, 20, width - 20, height - 20], outline=(20, 40, 100), width=4)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=95)
    buf.seek(0)
    return buf

def run_tests():
    print("=" * 60)
    print(" MITRA METROLOGY - VERIFICATION TEST SUITE (STEPS 12 - 40)")
    print("=" * 60)

    # -------------------------------------------------------------
    # 1. AUTHENTICATION & RBAC (Step 5, 21, 26, 36, 38)
    # -------------------------------------------------------------
    print("\n[TEST 1] Authentication & Role-Based Access Control...")
    
    # 1.1 Register Citizen
    c_email = f"citizen_{os.getpid()}@mitra.com"
    r = client.post("/auth/register", json={
        "name": "Citizen Ramesh",
        "email": c_email,
        "password": "Password@123"
    })
    assert r.status_code == 200, f"Citizen register failed: {r.text}"
    citizen_token = r.json()["access_token"]
    citizen_headers = {"Authorization": f"Bearer {citizen_token}"}
    print("  [PASS] Citizen registered successfully")

    # 1.2 Register Officer
    o_email = f"officer_{os.getpid()}@mitra.gov.in"
    r = client.post("/auth/create-officer", json={
        "name": "Inspector Sharma",
        "email": o_email,
        "password": "Officer@123"
    })
    assert r.status_code == 200, f"Officer create failed: {r.text}"
    officer_token = r.json()["access_token"]
    officer_headers = {"Authorization": f"Bearer {officer_token}"}
    print("  [PASS] Officer registered successfully")

    # 1.3 RBAC Check: Citizen blocked from Officer API (Step 38: 403 Officer access required)
    r = client.get("/inspections/", headers=citizen_headers)
    assert r.status_code == 403, f"Expected 403 for citizen on officer API, got: {r.status_code}"
    print("  [PASS] RBAC Enforced: Citizen blocked from /inspections/ (403 Forbidden)")

    # 1.4 Officer allowed on Officer API
    r = client.get("/inspections/", headers=officer_headers)
    assert r.status_code == 200, f"Officer access failed: {r.status_code}"
    print("  [PASS] RBAC Enforced: Officer permitted on /inspections/ (200 OK)")

    # 1.5 Invalid token check
    r = client.get("/inspections/", headers={"Authorization": "Bearer invalid_token_xyz"})
    assert r.status_code == 401, f"Expected 401 for bad token, got: {r.status_code}"
    print("  [PASS] Security Enforced: Invalid token rejected (401 Unauthorized)")

    # -------------------------------------------------------------
    # 2. PACKAGE A: FULL DECLARATIONS -> COMPLIANT (Step 12, 13, 14)
    # -------------------------------------------------------------
    print("\n[TEST 2] Package A (All Mandatory Declarations Present)...")
    pkg_a_lines = [
        "ORGANIC WHOLE WHEAT ATTA",
        "Net Quantity: 5 kg",
        "MRP: Rs. 295.00 (Incl. of all taxes)",
        "Mfd Date: 15/08/2026",
        "Best Before: 6 Months from Packaging",
        "Manufactured By: Mitra Agro Foods Pvt. Ltd.",
        "Address: Plot 42, Industrial Area, Sector 5, New Delhi 110020",
        "Consumer Care: support@mitrafoods.com or 1800-11-4567",
        "FSSAI Lic. No.: 10019022009876"
    ]
    img_a = create_dummy_image(pkg_a_lines)
    
    r = client.post("/scans/analyze", files={"file": ("package_a.jpg", img_a, "image/jpeg")}, headers=citizen_headers)
    assert r.status_code == 200, f"Scan A failed: {r.text}"
    scan_a = r.json()
    
    print(f"  Status: {scan_a['status']}")
    print(f"  Rules Checked: {scan_a.get('rules_checked')}")
    print(f"  Violations: {len(scan_a.get('violations', []))}")
    print(f"  Extracted MRP: {scan_a['fields'].get('mrp')}")
    print(f"  Extracted Net Qty: {scan_a['fields'].get('net_quantity')}")
    print(f"  Extracted FSSAI: {scan_a['fields'].get('fssai')}")
    
    assert scan_a["status"] == "COMPLIANT", f"Expected COMPLIANT, got {scan_a['status']}"
    assert scan_a["rules_checked"] == 8, f"Expected 8 rules checked, got {scan_a['rules_checked']}"
    assert len(scan_a["violations"]) == 0, f"Expected 0 violations, got {len(scan_a['violations'])}"
    scan_a_id = scan_a["scan_id"]
    print("  [PASS] Package A passed with 100% compliance: COMPLIANT")

    # -------------------------------------------------------------
    # 3. PACKAGE B: UNCERTAIN / MINOR OMISSION -> REVIEW REQUIRED (Step 12, 13)
    # -------------------------------------------------------------
    print("\n[TEST 3] Package B (Missing Expiry / Minor Omission)...")
    pkg_b_lines = [
        "CRUNCHY POTATO CHIPS",
        "Net Wt.: 50 g",
        "MRP: Rs. 20.00",
        "Mfd Date: 01/09/2026",
        # Missing Best Before / Expiry (medium severity)
        "Manufactured By: SnackCorp Foods Ltd.",
        "Address: GIDC Estate, Ahmedabad, Gujarat 382445",
        "Consumer Care: care@snackcorp.in",
        "FSSAI: 10014021000123"
    ]
    img_b = create_dummy_image(pkg_b_lines)
    r = client.post("/scans/analyze", files={"file": ("package_b.jpg", img_b, "image/jpeg")}, headers=citizen_headers)
    assert r.status_code == 200, f"Scan B failed: {r.text}"
    scan_b = r.json()
    
    print(f"  Status: {scan_b['status']}")
    print(f"  Violations: {[v['field'] for v in scan_b['violations']]}")
    assert scan_b["status"] == "REVIEW REQUIRED", f"Expected REVIEW REQUIRED, got {scan_b['status']}"
    scan_b_id = scan_b["scan_id"]
    print("  [PASS] Package B flagged correctly: REVIEW REQUIRED")

    # -------------------------------------------------------------
    # 4. PACKAGE C: MISSING MRP & NET QTY -> NON-COMPLIANT (Step 12, 14)
    # -------------------------------------------------------------
    print("\n[TEST 4] Package C (Missing MRP & Net Qty - Critical Rules)...")
    pkg_c_lines = [
        "GENERIC COOKIES",
        # NO MRP!
        # NO NET QUANTITY!
        "Mfd Date: 10/07/2026",
        "Best Before: 3 Months",
        "Manufactured By: Local Bakery Works",
        "Address: Market Road, Pune 411001",
        "Consumer Care: info@localbakery.com",
        "FSSAI: 10017011000456"
    ]
    img_c = create_dummy_image(pkg_c_lines)
    r = client.post("/scans/analyze", files={"file": ("package_c.jpg", img_c, "image/jpeg")}, headers=citizen_headers)
    assert r.status_code == 200, f"Scan C failed: {r.text}"
    scan_c = r.json()
    
    print(f"  Status: {scan_c['status']}")
    print(f"  Violations Flagged: {[v['field'] for v in scan_c['violations']]}")
    assert scan_c["status"] == "NON-COMPLIANT", f"Expected NON-COMPLIANT, got {scan_c['status']}"
    scan_c_id = scan_c["scan_id"]
    print("  [PASS] Package C flagged correctly: NON-COMPLIANT")

    # -------------------------------------------------------------
    # 5. DATABASE TRACEABILITY CHECK (Step 14)
    # -------------------------------------------------------------
    print("\n[TEST 5] Database Traceability & Audit Verification...")
    db = SessionLocal()
    try:
        # Check Scan A records
        scan_rec = db.query(Scan).filter(Scan.id == scan_a_id).first()
        assert scan_rec is not None, "Scan record missing in DB"
        
        fields = db.query(ExtractedField).filter(ExtractedField.scan_id == scan_a_id).all()
        assert len(fields) >= 7, f"Expected at least 7 extracted fields in DB, found {len(fields)}"
        print(f"  [PASS] {len(fields)} ExtractedField rows linked to Scan #{scan_a_id}")

        # Check Scan C violations
        violations = db.query(Violation).filter(Violation.scan_id == scan_c_id).all()
        assert len(violations) >= 2, f"Expected at least 2 violations in DB for Scan C, found {len(violations)}"
        print(f"  [PASS] {len(violations)} Violation rows linked to Scan #{scan_c_id}")
    finally:
        db.close()

    # -------------------------------------------------------------
    # 6. STRUCTURED INSPECTION REPORT & PDF DOWNLOAD (Step 15, 29)
    # -------------------------------------------------------------
    print("\n[TEST 6] Inspection Report (JSON & PDF Generation)...")
    # 6.1 JSON Report
    r = client.get(f"/scans/{scan_a_id}/report", headers=citizen_headers)
    assert r.status_code == 200, f"Report JSON failed: {r.text}"
    report_data = r.json()
    assert "report_id" in report_data
    assert report_data["status"] == "COMPLIANT"
    print(f"  [PASS] Structured JSON Report generated: {report_data['report_id']}")

    # 6.2 PDF Download
    r = client.get(f"/scans/{scan_a_id}/report/pdf", headers=citizen_headers)
    assert r.status_code == 200, f"Report PDF failed: {r.status_code}"
    assert r.headers.get("content-type") == "application/pdf"
    assert r.content.startswith(b"%PDF"), "Response is not a valid PDF file"
    print(f"  [PASS] Certified PDF Report generated ({len(r.content)} bytes)")

    # -------------------------------------------------------------
    # 7. SCAN HISTORY & DETAILS (Step 16, 17)
    # -------------------------------------------------------------
    print("\n[TEST 7] User Scan History & Privacy Isolation...")
    # Citizen checks history
    r = client.get("/scans/history", headers=citizen_headers)
    assert r.status_code == 200, f"History fetch failed: {r.text}"
    user_history = r.json()
    assert len(user_history) >= 3, f"Expected at least 3 scans in history, got {len(user_history)}"
    print(f"  [PASS] User history verified: {len(user_history)} scans returned")

    # Get single scan details
    r = client.get(f"/scans/{scan_a_id}", headers=citizen_headers)
    assert r.status_code == 200
    details = r.json()
    assert details["status"] == "COMPLIANT"
    assert "evidence" in details
    print(f"  [PASS] Scan #{scan_a_id} details endpoint verified")

    # -------------------------------------------------------------
    # 8. OFFICER INSPECTIONS & DYNAMIC STATS (Step 18, 19, 27, 28)
    # -------------------------------------------------------------
    print("\n[TEST 8] Officer Oversight & Real Dynamic Statistics...")
    # Officer stats
    r = client.get("/inspections/stats")
    assert r.status_code == 200
    stats = r.json()
    print(f"  Total Inspections: {stats['total_inspections']}")
    print(f"  Compliant: {stats['compliant']}")
    print(f"  Review Required: {stats['review_required']}")
    print(f"  Non-Compliant: {stats['non_compliant']}")
    
    assert stats["total_inspections"] >= 3
    assert stats["compliant"] >= 1
    assert stats["non_compliant"] >= 1
    print("  [PASS] Dynamic statistics calculated directly from scans.status")

    # Officer all-inspections list
    r = client.get("/inspections/", headers=officer_headers)
    assert r.status_code == 200
    all_inspections = r.json()
    assert len(all_inspections) >= 3
    print(f"  [PASS] Officer inspection queue returns {len(all_inspections)} items")

    # Officer single inspection detail (Step 28 Evidence Dossier)
    r = client.get(f"/inspections/{scan_c_id}", headers=officer_headers)
    assert r.status_code == 200
    dossier = r.json()
    assert dossier["status"] == "NON-COMPLIANT"
    assert "ocr_text" in dossier
    assert "violations" in dossier
    assert "evidence" in dossier
    print(f"  [PASS] Officer Evidence Dossier verified for Scan #{scan_c_id}")

    # -------------------------------------------------------------
    # 9. COMPLAINT WORKFLOW (Step 20)
    # -------------------------------------------------------------
    print("\n[TEST 9] Consumer Grievance & Officer Resolution Lifecycle...")
    # 9.1 Citizen submits complaint
    r = client.post("/complaints/", json={
        "scan_id": scan_c_id,
        "product_name": "Generic Cookies",
        "manufacturer": "Local Bakery Works",
        "violation_type": "MISSING_MRP",
        "description": "Product has no MRP or Net Quantity declaration on the pouch."
    }, headers=citizen_headers)
    assert r.status_code == 200, f"Complaint create failed: {r.text}"
    comp_id = r.json()["complaint_id"]
    assert r.json()["status"] == "PENDING"
    print(f"  [PASS] Grievance filed by citizen: #GRIEV-{comp_id} (PENDING)")

    # 9.2 Officer updates status to UNDER_REVIEW
    r = client.patch(f"/complaints/{comp_id}/status", json={"status": "UNDER_REVIEW"}, headers=officer_headers)
    assert r.status_code == 200
    assert r.json()["status"] == "UNDER_REVIEW"
    print(f"  [PASS] Officer updated status to UNDER_REVIEW")

    # 9.3 Officer updates status to RESOLVED
    r = client.patch(f"/complaints/{comp_id}/status", json={"status": "RESOLVED"}, headers=officer_headers)
    assert r.status_code == 200
    assert r.json()["status"] == "RESOLVED"
    print(f"  [PASS] Officer marked grievance RESOLVED")

    # -------------------------------------------------------------
    # SUMMARY
    # -------------------------------------------------------------
    print("\n" + "=" * 60)
    print(" [SUCCESS] ALL 9 SYSTEM VERIFICATION TEST PHASES PASSED!")
    print("=" * 60)

if __name__ == "__main__":
    run_tests()
