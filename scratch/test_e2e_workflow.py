import os
import sys
import json
import requests
import cv2
import numpy as np

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

BASE_URL = "http://127.0.0.1:8000"

def run_tests():
    print("=== Mitra Metrology E2E Workflow & Image Quality Validation ===")
    
    # ── Authenticate ──────────────────────────────────────────────────────────
    print("\n1. Testing Authentication...")
    login_res = requests.post(
        f"{BASE_URL}/auth/login",
        json={"email": "user@mitra.com", "password": "User@123"}
    )
    assert login_res.status_code == 200, f"Login failed: {login_res.text}"
    token_data = login_res.json()
    token = token_data["access_token"]
    user_id = token_data["user_id"]
    headers = {"Authorization": f"Bearer {token}"}
    print(f"   [PASS] Logged in as user_id={user_id}, role={token_data['role']}")

    # ── Task 3: Complete OCR Workflow on Clear Image ─────────────────────────
    print("\n2. Testing POST /scans/ocr-extract with Clear Packaged Product Image...")
    # Use real product image
    img_path = "backend/uploads/packaged_atta_0280d152.jpg"
    assert os.path.exists(img_path), f"Sample image {img_path} not found"

    with open(img_path, "rb") as f:
        files = {"file": ("product.jpg", f, "image/jpeg")}
        extract_res = requests.post(f"{BASE_URL}/scans/ocr-extract", headers=headers, files=files)
    
    assert extract_res.status_code == 200, f"OCR extraction failed: {extract_res.text}"
    extract_data = extract_res.json()
    scan_id = extract_data["scan_id"]
    print(f"   [PASS] ocr-extract returned scan_id={scan_id}, status={extract_data.get('status')}")
    print(f"   Quality tier: {extract_data.get('quality_tier')}, needs_retake: {extract_data.get('needs_retake_prompt')}")
    assert extract_data["status"] == "review_pending", f"Expected review_pending, got {extract_data['status']}"
    assert extract_data["user_confirmed"] is False, "user_confirmed must be False at extraction"
    
    # Check fields and confidences
    fields = extract_data.get("fields", [])
    print(f"   Extracted {len(fields)} field records:")
    mrp_field = None
    for fld in fields:
        fname = fld.get("field_name")
        val = fld.get("display_value")
        conf = fld.get("confidence")
        status = fld.get("field_status")
        if fname != "_ocr_text":
            print(f"     - {fname}: '{val}' (conf: {conf}, status: {status})")
        if fname == "mrp":
            mrp_field = fld

    # ── Step 4: GET /scans/{id}/review ──────────────────────────────────────
    print("\n3. Testing GET /scans/{id}/review (Review Page Payload)...")
    review_res = requests.get(f"{BASE_URL}/scans/{scan_id}/review", headers=headers)
    assert review_res.status_code == 200, f"Review fetch failed: {review_res.text}"
    review_data = review_res.json()
    assert review_data["scan_id"] == scan_id
    assert review_data["user_confirmed"] is False
    print(f"   [PASS] Review payload verified for scan {scan_id}")

    # Record original MRP value for audit trail check
    orig_mrp = mrp_field.get("original_ocr_value") if mrp_field else None

    # ── Step 5 & 6: PUT /scans/{id}/fields (Manual Corrections) ────────────
    print("\n4. Testing PUT /scans/{id}/fields (Manual Field Correction & Marking Unreadable)...")
    corrections_payload = {
        "corrections": [
            {
                "field_name": "mrp",
                "corrected_value": "Rs. 295.00",
                "mark_unreadable": False
            },
            {
                "field_name": "consumer_care",
                "corrected_value": None,
                "mark_unreadable": True
            }
        ]
    }
    put_res = requests.put(
        f"{BASE_URL}/scans/{scan_id}/fields",
        headers=headers,
        json=corrections_payload
    )
    assert put_res.status_code == 200, f"PUT fields failed: {put_res.text}"
    put_data = put_res.json()
    print(f"   [PASS] PUT fields succeeded: {put_data}")
    assert "mrp" in put_data["updated_fields"]
    assert "consumer_care" in put_data["updated_fields"]

    # ── Step 7: Verify Audit Trail Preservation ─────────────────────────────
    print("\n5. Verifying Audit Trail (original_ocr_value vs corrected_value)...")
    review_after_res = requests.get(f"{BASE_URL}/scans/{scan_id}/review", headers=headers)
    review_after = review_after_res.json()
    fields_dict = {f["field_name"]: f for f in review_after["fields"]}

    mrp_after = fields_dict.get("mrp")
    assert mrp_after is not None
    print(f"   MRP original_ocr_value: '{mrp_after.get('original_ocr_value')}'")
    print(f"   MRP corrected_value:    '{mrp_after.get('corrected_value')}'")
    print(f"   MRP display_value:      '{mrp_after.get('display_value')}'")
    print(f"   MRP correction_status:  '{mrp_after.get('correction_status')}'")
    assert mrp_after["corrected_value"] == "Rs. 295.00"
    assert mrp_after["display_value"] == "Rs. 295.00"
    assert mrp_after["correction_status"] == "user_corrected"
    assert mrp_after["original_ocr_value"] == orig_mrp, "Original OCR value was corrupted!"

    cc_after = fields_dict.get("consumer_care")
    assert cc_after is not None
    print(f"   Consumer Care status:   '{cc_after.get('correction_status')}' (field_status: {cc_after.get('field_status')})")
    assert cc_after["correction_status"] == "user_marked_unreadable"
    assert cc_after["field_status"] == "UNREADABLE"
    assert cc_after["display_value"] is None
    print("   [PASS] Audit trail preserved! Original OCR values untouched, corrections saved.")

    # ── Step 8 & 9: POST /scans/{id}/confirm ────────────────────────────────
    print("\n6. Testing POST /scans/{id}/confirm (Execute Compliance Engine)...")
    confirm_res = requests.post(f"{BASE_URL}/scans/{scan_id}/confirm", headers=headers, json={})
    assert confirm_res.status_code == 200, f"Confirm failed: {confirm_res.text}"
    confirm_data = confirm_res.json()
    print(f"   [PASS] Confirmation result:")
    print(f"     Status:           {confirm_data.get('status')}")
    print(f"     Compliance Score: {confirm_data.get('score')}%")
    print(f"     Rules Checked:    {confirm_data.get('rules_checked')}")
    print(f"     Violations Count: {confirm_data.get('violation_count')}")
    print(f"     User Confirmed:   {confirm_data.get('user_confirmed')}")
    assert confirm_data["user_confirmed"] is True
    assert confirm_data["status"] in ("COMPLIANT", "NON-COMPLIANT", "REVIEW REQUIRED")
    # Verify that the confirmed values were used
    assert confirm_data["fields"].get("mrp") == "Rs. 295.00", "Corrected MRP was not used in compliance evaluation!"
    print(f"   [PASS] Confirmed fields used in rule evaluation: MRP='{confirm_data['fields'].get('mrp')}'")

    # ── Step 10: Idempotency & Conflict Checks ─────────────────────────────
    print("\n7. Testing Idempotency & Immutability...")
    # Duplicate confirm must return existing result without error
    confirm_res_2 = requests.post(f"{BASE_URL}/scans/{scan_id}/confirm", headers=headers, json={})
    assert confirm_res_2.status_code == 200
    assert confirm_res_2.json()["scan_id"] == scan_id
    print("   [PASS] Duplicate confirm is idempotent.")

    # Modifying fields after confirmation must return 409 Conflict
    put_res_after = requests.put(
        f"{BASE_URL}/scans/{scan_id}/fields",
        headers=headers,
        json={"corrections": [{"field_name": "mrp", "corrected_value": "Rs. 500"}]}
    )
    assert put_res_after.status_code == 409, f"Expected 409 Conflict after confirm, got {put_res_after.status_code}"
    print(f"   [PASS] Modifying confirmed scan properly rejected with 409 Conflict: {put_res_after.json()['detail']}")

    # ── Step 11: Scan History & PDF Report ──────────────────────────────────
    print("\n8. Testing Scan History & PDF Report Generation...")
    history_res = requests.get(f"{BASE_URL}/scans/history", headers=headers)
    assert history_res.status_code == 200, f"History fetch failed: {history_res.text}"
    history_list = history_res.json()
    matching_scan = next((s for s in history_list if s["id"] == scan_id), None)
    assert matching_scan is not None, f"Scan {scan_id} not found in scan history"
    print(f"   [PASS] Scan {scan_id} present in history with status='{matching_scan['status']}'")

    pdf_res = requests.get(f"{BASE_URL}/scans/{scan_id}/report/pdf", headers=headers)
    assert pdf_res.status_code == 200, f"PDF generation failed: {pdf_res.text}"
    assert pdf_res.headers.get("content-type") == "application/pdf"
    assert len(pdf_res.content) > 1000, "PDF content too small"
    print(f"   [PASS] PDF report generated successfully ({len(pdf_res.content)} bytes, application/pdf)")

    # ── Task 4: Image Quality Handling (Blurry Image) ──────────────────────
    print("\n9. Testing Task 4: Image Quality Handling on Blurry Image...")
    # Generate a severely blurred image
    clear_img = cv2.imread(img_path)
    blurry_img = cv2.GaussianBlur(clear_img, (51, 51), 30)
    blurry_path = "scratch/test_blurry_atta.jpg"
    cv2.imwrite(blurry_path, blurry_img)

    # Test blurry upload without force_proceed
    with open(blurry_path, "rb") as f:
        files = {"file": ("blurry.jpg", f, "image/jpeg")}
        blur_res = requests.post(f"{BASE_URL}/scans/ocr-extract", headers=headers, files=files)
    
    assert blur_res.status_code == 200
    blur_data = blur_res.json()
    print(f"   Blurry scan response:")
    print(f"     Quality tier:        {blur_data.get('quality_tier')}")
    print(f"     Needs retake prompt: {blur_data.get('needs_retake_prompt')}")
    print(f"     Quality warning:     {blur_data.get('image_quality_warning')}")
    assert blur_data.get("quality_tier") in ("POOR", "VERY_POOR")
    assert blur_data.get("needs_retake_prompt") is True
    print("   [PASS] Blurry image triggered retake prompt and quality warning!")

    # Test blurry upload with force_proceed="true" (Continue Anyway)
    print("\n10. Testing Task 4: 'Continue Anyway' (force_proceed=true) on Blurry Image...")
    with open(blurry_path, "rb") as f:
        files = {"file": ("blurry.jpg", f, "image/jpeg")}
        data = {"force_proceed": "true"}
        proceed_res = requests.post(
            f"{BASE_URL}/scans/ocr-extract",
            headers=headers,
            files=files,
            data=data
        )
    assert proceed_res.status_code == 200
    proceed_data = proceed_res.json()
    print(f"   'Continue Anyway' scan {proceed_data['scan_id']}:")
    print(f"     Quality tier:        {proceed_data.get('quality_tier')}")
    print(f"     Has quality warning: {proceed_data.get('has_quality_warning')}")
    assert proceed_data.get("has_quality_warning") is True
    print("   [PASS] 'Continue Anyway' proceeded while preserving image quality warning!")

    print("\n=== ALL E2E WORKFLOW AND IMAGE QUALITY TESTS PASSED ===")

if __name__ == "__main__":
    run_tests()
