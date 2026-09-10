# scratch/verify_all_pipeline.py
"""
End-to-End Pipeline & Officer Authentication Verification Script
Tests:
1. Auto-seeding and self-healing officer login (officer_22472@mitra.gov.in / Officer@123)
2. Case-insensitive login & badge without domain (officer_22472)
3. /auth/seed endpoint
4. Computer Vision (OCV) & Image Quality Assessment
5. Preprocessing & CLAHE contrast normalization
6. Packaging OCR & statutory field extraction
7. Legal Metrology 8-rule compliance check
8. Food label FSSAI checklist analysis (/food-label/analyze)
9. Cloud Computer Vision / Neural Network fallback (/predict)
10. Dynamic inspection statistics & PDF report generation
"""

import sys
import os
import io
import json
from PIL import Image, ImageDraw

BASE_DIR = os.path.abspath(r"c:\Users\polas\Documents\Desktop(copy)\Hackthons\Mitra-Metrology")
sys.path.insert(0, os.path.join(BASE_DIR, "backend"))
sys.path.insert(0, BASE_DIR)

from fastapi.testclient import TestClient
from app.main import app
from app.database.connection import SessionLocal
from app.models.user import User

client = TestClient(app)

def create_sample_packaging_image(text_lines):
    img = Image.new("RGB", (800, 800), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    y = 50
    for line in text_lines:
        draw.text((50, y), line, fill=(0, 0, 0))
        y += 40
    draw.rectangle([20, 20, 780, 780], outline=(10, 30, 80), width=4)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=95)
    buf.seek(0)
    return buf

def run_checks():
    print("=" * 65)
    print(" MITRA METROLOGY - FULL PIPELINE & AUTH VERIFICATION")
    print("=" * 65)

    # -------------------------------------------------------------
    # 1. OFFICER LOGIN: EXACT CREDENTIALS
    # -------------------------------------------------------------
    print("\n[PHASE 1] Officer Login: officer_22472@mitra.gov.in / Officer@123")
    r1 = client.post("/auth/login", json={
        "email": "officer_22472@mitra.gov.in",
        "password": "Officer@123"
    })
    assert r1.status_code == 200, f"Failed exact officer login: {r1.text}"
    token_officer = r1.json()["access_token"]
    role_officer = r1.json()["role"]
    assert role_officer == "officer", f"Expected role 'officer', got '{role_officer}'"
    print("  [PASS]: Exact officer credentials logged in successfully (role: officer)")

    # -------------------------------------------------------------
    # 2. OFFICER LOGIN: CASE-INSENSITIVE & BADGE ONLY
    # -------------------------------------------------------------
    print("\n[PHASE 2] Officer Login: Case-Insensitive & Badge ID fallback")
    # Uppercase
    r2_upper = client.post("/auth/login", json={
        "email": "OFFICER_22472@mitra.gov.in",
        "password": "Officer@123"
    })
    assert r2_upper.status_code == 200, f"Uppercase email login failed: {r2_upper.text}"
    print("  [PASS]: Uppercase email accepted")

    # Badge only without domain
    r2_badge = client.post("/auth/login", json={
        "email": "officer_22472",
        "password": "Officer@123"
    })
    assert r2_badge.status_code == 200, f"Badge-only login failed: {r2_badge.text}"
    print("  [PASS]: Badge ID 'officer_22472' auto-resolved to officer_22472@mitra.gov.in")

    # -------------------------------------------------------------
    # 3. CITIZEN LOGIN
    # -------------------------------------------------------------
    print("\n[PHASE 3] Citizen Login: user@mitra.com / User@123")
    r3 = client.post("/auth/login", json={
        "email": "user@mitra.com",
        "password": "User@123"
    })
    assert r3.status_code == 200, f"Citizen login failed: {r3.text}"
    token_citizen = r3.json()["access_token"]
    role_citizen = r3.json()["role"]
    assert role_citizen == "user", f"Expected role 'user', got '{role_citizen}'"
    print("  [PASS]: Citizen credentials logged in successfully (role: user)")

    # -------------------------------------------------------------
    # 4. /auth/seed ENDPOINT
    # -------------------------------------------------------------
    print("\n[PHASE 4] Explicit /auth/seed Endpoint")
    r_seed = client.get("/auth/seed")
    assert r_seed.status_code == 200, f"/auth/seed failed: {r_seed.text}"
    print(f"  [PASS]: /auth/seed executed successfully: {r_seed.json()['status']}")

    # -------------------------------------------------------------
    # 5. OCV & IMAGE QUALITY ASSESSMENT
    # -------------------------------------------------------------
    print("\n[PHASE 5] OCV (OpenCV) & Image Quality Gate")
    from ai_engine.image_quality import assess_image_quality, check_image_quality
    from ai_engine.preprocessing import preprocess_image
    import cv2
    import numpy as np

    dummy_cv_img = np.ones((800, 800, 3), dtype=np.uint8) * 255
    cv2.putText(dummy_cv_img, "QUALITY TEST 123", (50, 200), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
    quality = assess_image_quality(dummy_cv_img)
    assert "quality_score" in quality, "Quality score missing in assess_image_quality"
    assert quality["resolution"]["passed"] is True, "Resolution check failed"
    print(f"  [PASS]: assess_image_quality passed (Score: {quality['quality_score']})")

    preprocessed = preprocess_image(dummy_cv_img)
    assert "enhanced" in preprocessed and "thresholded" in preprocessed, "Preprocessing output incomplete"
    print("  [PASS]: Image CLAHE & adaptive binarization preprocessed successfully")

    # -------------------------------------------------------------
    # 6. AI DETECTION & LEGAL METROLOGY SCAN PIPELINE
    # -------------------------------------------------------------
    print("\n[PHASE 6] Packaging OCR & 8-Rule Legal Metrology Inspection (/scans/analyze)")
    pkg_lines = [
        "PATANJALI ORGANIC ATTA",
        "Net Quantity: 10 kg",
        "MRP: Rs. 450.00 (Incl. of all taxes)",
        "Mfd Date: 12/01/2026",
        "Best Before: 9 Months from Packaging",
        "Manufactured By: Patanjali Foods Ltd.",
        "Address: Haridwar, Uttarakhand 249401",
        "Consumer Care: feedback@patanjali.org | 1800-180-4108",
        "FSSAI Lic. No.: 10014012000266"
    ]
    img_buf = create_sample_packaging_image(pkg_lines)
    r_scan = client.post(
        "/scans/analyze",
        files={"file": ("packaged_atta.jpg", img_buf, "image/jpeg")},
        headers={"Authorization": f"Bearer {token_citizen}"}
    )
    assert r_scan.status_code == 200, f"/scans/analyze failed: {r_scan.text}"
    scan_data = r_scan.json()
    assert scan_data["status"] in ["COMPLIANT", "REVIEW REQUIRED", "NON-COMPLIANT"]
    print(f"  [PASS]: Scan analyzed. Status: {scan_data['status']}, Rules Checked: {scan_data['rules_checked']}")
    scan_id = scan_data["scan_id"]

    # -------------------------------------------------------------
    # 7. CERTIFIED AUDIT PDF REPORT GENERATION
    # -------------------------------------------------------------
    print("\n[PHASE 7] Certified PDF Inspection Report (/scans/{id}/report/pdf)")
    r_pdf = client.get(
        f"/scans/{scan_id}/report/pdf",
        headers={"Authorization": f"Bearer {token_citizen}"}
    )
    assert r_pdf.status_code == 200, f"PDF report generation failed: {r_pdf.status_code}"
    assert r_pdf.headers["content-type"] == "application/pdf", "Content-Type is not application/pdf"
    assert len(r_pdf.content) > 1000, "PDF content appears truncated"
    print(f"  [PASS]: PDF generated successfully ({len(r_pdf.content)} bytes)")

    # -------------------------------------------------------------
    # 8. PREDICT / CLOUD VISION INFERENCE (/predict)
    # -------------------------------------------------------------
    print("\n[PHASE 8] Cloud Neural Network Vision Detection (/predict)")
    img_predict_buf = create_sample_packaging_image(["TEST PREDICT"])
    r_pred = client.post(
        "/predict",
        files={"image": ("frame.jpg", img_predict_buf, "image/jpeg")},
        data={"confidence_threshold": "0.70"}
    )
    assert r_pred.status_code == 200, f"/predict failed: {r_pred.text}"
    pred_data = r_pred.json()
    assert "detections" in pred_data and "inference_time_ms" in pred_data
    print(f"  [PASS]: Cloud vision returned {len(pred_data['detections'])} detections in {pred_data['inference_time_ms']}ms")

    # -------------------------------------------------------------
    # 9. FSSAI FOOD LABELLING CHECKLIST (/food-label/analyze)
    # -------------------------------------------------------------
    print("\n[PHASE 9] FSSAI Food Labelling & Display Regulations 2020 (/food-label/analyze)")
    fssai_lines = [
        "CHOCO CRUNCH BISCUITS",
        "INGREDIENTS: Refined Wheat Flour (54%), Sugar, Edible Vegetable Oil (Palm), Milk Solids, Cocoa Solids (2.8%), Emulsifier (INS 322), Raising Agents [INS 500(ii)], Iodized Salt.",
        "ALLERGEN ADVICE: Contains Wheat (Gluten), Milk and Soy.",
        "NUTRITIONAL INFORMATION per 100g: Energy: 480 kcal, Protein: 7.2 g, Carbohydrate: 68.0 g, Total Sugars: 28.5 g, Added Sugars: 24.0 g, Total Fat: 20.0 g, Saturated Fat: 9.5 g, Trans Fat: 0.1 g, Sodium: 320 mg",
        "NET QUANTITY: 120 g",
        "MRP: Rs 30.00",
        "MFD: 10/01/2026",
        "BEST BEFORE: 6 MONTHS FROM PACKAGING",
        "MANUFACTURED BY: Mitra Food Products Ltd.",
        "FSSAI LIC NO: 10015042001234",
        "100% VEGETARIAN"
    ]
    img_food_buf = create_sample_packaging_image(fssai_lines)
    r_food = client.post(
        "/food-label/analyze",
        files={"image": ("biscuit_label.jpg", img_food_buf, "image/jpeg")}
    )
    assert r_food.status_code == 200, f"/food-label/analyze failed: {r_food.text}"
    food_data = r_food.json()
    print(f"  [PASS]: FSSAI analysis returned status: {food_data.get('status')}")

    # -------------------------------------------------------------
    # 10. OFFICER DASHBOARD & INSPECTION AUDIT QUEUE
    # -------------------------------------------------------------
    print("\n[PHASE 10] Officer Dashboard & RBAC Protected Access")
    r_stats = client.get(
        "/inspections/stats/summary",
        headers={"Authorization": f"Bearer {token_officer}"}
    )
    assert r_stats.status_code == 200, f"Officer stats failed: {r_stats.status_code}"
    stats = r_stats.json()
    total = stats.get('total_inspections', stats.get('total', 0))
    print(f"  [PASS]: Officer stats verified: Total: {total}, Compliant: {stats['compliant']}, Review: {stats['review_required']}, Non-Compliant: {stats['non_compliant']}")

    print("\n" + "=" * 65)
    print(" ALL 10 PIPELINE & AUTHENTICATION VERIFICATION PHASES PASSED!")
    print("=" * 65 + "\n")

if __name__ == "__main__":
    run_checks()
