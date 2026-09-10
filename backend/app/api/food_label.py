# app/api/food_label.py
"""
Indian Pre-Packaged Food Label FSSAI Compliance API.
Implements the multi-stage pipeline:
Image Quality Gate -> Region OCR -> Document Parsing -> Ingredient/INS Parsing ->
Allergen Detection -> Nutrition Extraction -> Versioned FSSAI Rule Engine.
"""

import os
import sys
import uuid
import shutil
from pathlib import Path
from typing import Optional, List
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from sqlalchemy.orm import Session

# Setup import paths
candidate_roots = [
    Path(__file__).resolve().parent.parent.parent.parent,
    Path(__file__).resolve().parent.parent.parent,
    Path(__file__).resolve().parent.parent,
    Path("/app")
]

for root in candidate_roots:
    ai_dir = root / "ai_engine"
    rules_dir = root / "rules"
    if ai_dir.is_dir():
        if str(ai_dir) not in sys.path:
            sys.path.insert(0, str(ai_dir))
        if str(root) not in sys.path:
            sys.path.insert(0, str(root))
    if rules_dir.is_dir():
        if str(rules_dir) not in sys.path:
            sys.path.insert(0, str(rules_dir))

import cv2
from image_quality import assess_image_quality
from preprocessing import preprocess_image
from ocr import run_ocr, group_ocr_lines, combine_ocr_text
from food_document_parser import parse_food_label_document
from fssai_rule_engine import FSSAIRuleEngine

from app.database.connection import get_db
from app.models.scan import Scan
from app.models.extracted_field import ExtractedField
from app.models.violation import Violation

UPLOAD_DIR = Path(__file__).resolve().parent.parent.parent / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

router = APIRouter(
    prefix="/food-label",
    tags=["Food Label FSSAI Compliance"]
)

rule_engine = FSSAIRuleEngine()


@router.post("/analyze")
async def analyze_food_label(
    image: UploadFile = File(...),
    panel_type: Optional[str] = Form("all"),  # 'ingredients', 'nutrition', 'all'
    user_id: Optional[int] = Form(1),
    db: Session = Depends(get_db)
):
    """
    Executes full FSSAI Food Labelling & Display analysis.
    Implements a pre-OCR quality gate: rejects low-quality frames with actionable retake guidance.
    """
    if not image.filename:
        raise HTTPException(status_code=400, detail="No label image uploaded")

    # Save uploaded image
    file_ext = Path(image.filename).suffix.lower() or ".jpg"
    unique_name = f"food_{uuid.uuid4().hex[:10]}{file_ext}"
    saved_path = UPLOAD_DIR / unique_name

    try:
        with open(saved_path, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save image: {str(e)}")

    cv_image = cv2.imread(str(saved_path))
    if cv_image is None:
        raise HTTPException(status_code=400, detail="Unable to read food package image")

    # 1. IMAGE QUALITY GATE
    quality = assess_image_quality(cv_image)
    quality_score = quality.get("quality_score", 0.0)

    rejection_reasons = []
    if not quality["blur"]["passed"]:
        rejection_reasons.append("Image is too blurry. Please hold camera steady or ensure proper autofocus.")
    if not quality["brightness"]["passed"]:
        if quality["brightness"]["status"] == "too_dark":
            rejection_reasons.append("Image is too dark. Turn on torch or move to better lighting.")
        else:
            rejection_reasons.append("Excessive glare on glossy packaging surface. Tilt package slightly to reduce reflections.")
    if not quality["text_visibility"]["passed"]:
        rejection_reasons.append("Text is too small or package is not fully in frame. Move closer to the label.")

    # Quality Gate Enforcement: If score is critically low (< 0.40) and multiple checks fail
    if quality_score < 0.40 and len(rejection_reasons) >= 2:
        return {
            "status": "QUALITY_CHECK_FAILED",
            "message": "Please retake the photo",
            "can_proceed_with_analysis": False,
            "quality": quality,
            "reasons": rejection_reasons,
            "retake_guidance": [
                "Hold your camera 15-25 cm from the back label",
                "Ensure package text is sharply in focus",
                "Avoid bright overhead lights creating specular glare",
                "Keep the label flat and fully inside the view"
            ]
        }

    # 2. IMAGE PREPROCESSING & ENHANCEMENT
    preprocessed = preprocess_image(cv_image)
    ocr_target = preprocessed["enhanced"]

    # 3. PACKAGING OCR
    ocr_words = run_ocr(ocr_target)
    ocr_lines = group_ocr_lines(ocr_words)

    # 4. DOCUMENT UNDERSTANDING & DOMAIN EXTRACTION
    product_data = parse_food_label_document(ocr_lines, image_quality_score=quality_score)

    # 5. VERSIONED FSSAI RULE ENGINE EVALUATION
    fssai_report = rule_engine.evaluate(product_data, image_quality_score=quality_score)

    # Calculate statutory compliance percentage
    total_rules = fssai_report["total_rules"]
    pass_rules = fssai_report["pass_count"]
    compliance_score = round((pass_rules / total_rules * 100), 1) if total_rules > 0 else 0.0

    # Persist to database
    try:
        new_scan = Scan(
            user_id=user_id or 1,
            image_path=f"/uploads/{unique_name}",
            status=fssai_report["overall_verdict"],
            score=compliance_score
        )
        db.add(new_scan)
        db.commit()
        db.refresh(new_scan)

        # Store product name and key fields
        db.add(ExtractedField(
            scan_id=new_scan.id,
            field_name="product_name",
            field_value=product_data["product_name"],
            confidence=0.92
        ))
        db.add(ExtractedField(
            scan_id=new_scan.id,
            field_name="ingredients_count",
            field_value=str(product_data["ingredients"]["count"]),
            confidence=0.90
        ))
        if product_data["fssai_license"]["license_number"]:
            db.add(ExtractedField(
                scan_id=new_scan.id,
                field_name="fssai_license",
                field_value=product_data["fssai_license"]["license_number"],
                confidence=0.95
            ))

        # Store violations
        for r in fssai_report["evidence_checklist"]:
            if r["status"] in ["FAIL", "WARNING"]:
                db.add(Violation(
                    scan_id=new_scan.id,
                    field=r["category"],
                    description=f"[{r['citation']}] {r['title']}: {r['recommendation'] or r['what_was_read']}",
                    severity=r["severity"],
                    evidence_path=f"/uploads/{unique_name}"
                ))
        db.commit()
        scan_id = new_scan.id
    except Exception as db_err:
        print("Database save note:", db_err)
        scan_id = 1

    return {
        "status": "ANALYSIS_COMPLETE",
        "scan_id": scan_id,
        "image_url": f"/uploads/{unique_name}",
        "can_proceed_with_analysis": True,
        "product_overview": {
            "name": product_data["product_name"],
            "category": product_data["category"],
            "veg_non_veg": product_data["veg_non_veg"],
            "fssai_license": product_data["fssai_license"],
            "net_quantity": product_data["net_quantity"],
            "mrp": product_data["mrp"],
            "dates": {
                "mfd": product_data["manufacturing_date"],
                "expiry": product_data["expiry_date"],
                "best_before": product_data["best_before"],
                "batch": product_data["batch_number"]
            },
            "manufacturer": product_data["manufacturer"]
        },
        "ingredients_analysis": product_data["ingredients"],
        "allergen_analysis": product_data["allergens"],
        "nutrition_facts": product_data["nutrition"],
        "fssai_report": fssai_report,
        "quality_metrics": quality,
        "statutory_disclaimer": fssai_report["statutory_disclaimer"]
    }
