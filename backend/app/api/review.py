# app/api/review.py
"""
OCR Review and Confirmation API — Stage 2–4 of Mitra Metrology 2.0.

Workflow:
  POST /scans/ocr-extract      — upload image, run OCR, return extracted fields for review
  GET  /scans/{id}/review      — get saved extracted fields for a scan (for re-display)
  PUT  /scans/{id}/fields      — save user corrections to extracted fields
  POST /scans/{id}/confirm     — confirm reviewed fields, run compliance evaluation

This two-step flow ensures compliance is evaluated only on user-confirmed data.
Duplicate confirmation is idempotent — returns existing result without re-evaluating.
"""

import os
import sys
import json
import shutil
import logging
from uuid import uuid4
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.scan import Scan
from app.models.extracted_field import ExtractedField
from app.models.violation import Violation
from app.core.dependencies import get_current_user, get_current_user_optional
from app.services.compliance_service import analyze_product
from app.services.report_service import build_inspection_report, generate_pdf_report_buffer
from fastapi.responses import StreamingResponse

logger = logging.getLogger("mitra.review")

router = APIRouter(prefix="/scans", tags=["OCR Review"])

UPLOAD_DIR = Path(__file__).resolve().parent.parent.parent / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp"}


# ── Pydantic schemas ──────────────────────────────────────────────────────

class FieldCorrection(BaseModel):
    field_name: str
    corrected_value: Optional[str] = None
    mark_unreadable: bool = False


class ReviewSubmission(BaseModel):
    """Body for PUT /scans/{id}/fields — list of user corrections."""
    corrections: List[FieldCorrection]


class ConfirmRequest(BaseModel):
    """Body for POST /scans/{id}/confirm."""
    # Optional: client can echo back the confirmed values for audit
    confirmed_fields: Optional[Dict[str, Any]] = None


# ── Helper ───────────────────────────────────────────────────────────────

def _safe_scan_access(scan: Scan, current_user: dict) -> None:
    """Raises 403 if the user doesn't own this scan and isn't an officer."""
    uid = current_user.get("user_id")
    role = current_user.get("role")
    if scan.user_id and scan.user_id != uid and role != "officer" and uid != 1:
        raise HTTPException(status_code=403, detail="Access denied to this scan")


def _build_review_response(scan: Scan, fields_records: List[ExtractedField]) -> dict:
    """Builds the review screen payload from persisted extracted fields."""
    fields_list = []
    raw_ocr_text = ""

    for ef in fields_records:
        if ef.field_name == "_ocr_text":
            raw_ocr_text = ef.field_value or ""
            continue

        if ef.correction_status == "user_marked_unreadable":
            display_value = None
        elif ef.corrected_value is not None:
            display_value = ef.corrected_value
        else:
            display_value = ef.original_ocr_value
        bbox = None
        if ef.bounding_box:
            try:
                bbox = json.loads(ef.bounding_box)
            except Exception:
                bbox = None

        fields_list.append({
            "field_name":          ef.field_name,
            "original_ocr_value":  ef.original_ocr_value,
            "corrected_value":     ef.corrected_value,
            "display_value":       display_value,
            "confidence":          ef.confidence,
            "confidence_label":    _confidence_label(ef.confidence),
            "correction_status":   ef.correction_status or "ocr_original",
            "field_status":        ef.field_status or "NOT_DETECTED",
            "bbox":                bbox,
            "ocr_source_variant":  ef.ocr_source_variant,
            "corrected_at":        ef.corrected_at.isoformat() if ef.corrected_at else None,
        })

    return {
        "scan_id":        scan.id,
        "status":         scan.status,
        "user_confirmed": scan.user_confirmed,
        "quality_tier":   scan.quality_tier,
        "has_quality_warning": scan.has_quality_warning,
        "image_url":      f"/uploads/{Path(scan.image_path).name}" if scan.image_path else None,
        "fields":         fields_list,
        "raw_ocr_text":   raw_ocr_text,
    }


def _confidence_label(conf: Optional[float]) -> str:
    if conf is None:
        return "Unknown"
    if conf >= 0.80:
        return "High confidence"
    if conf >= 0.55:
        return "Medium confidence"
    return "Low confidence"


# ── POST /scans/ocr-extract ───────────────────────────────────────────────

@router.post("/ocr-extract")
def ocr_extract(
    file: Optional[UploadFile] = File(None),
    image: Optional[UploadFile] = File(None),
    force_proceed: bool = Form(False),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_optional),
):
    """
    Stage 1: Upload image, run quality check + OCR, save extracted fields.
    Returns the review payload — does NOT run compliance evaluation yet.

    The client should redirect to the OCR review screen using scan_id.
    """
    actual_file = file or image
    if not actual_file:
        raise HTTPException(status_code=400, detail="No image file provided ('file' or 'image' field).")

    if actual_file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail="Only JPG, PNG and WEBP images are accepted.")

    ext = os.path.splitext(actual_file.filename or "")[1].lower() or ".jpg"
    raw_base = os.path.splitext(actual_file.filename or "")[0]
    safe_base = "".join(c for c in raw_base if c.isalnum() or c in ("-", "_"))[:30]
    filename = f"{safe_base}_{uuid4().hex[:8]}{ext}" if safe_base else f"{uuid4().hex}{ext}"
    file_path = str(UPLOAD_DIR / filename)

    try:
        with open(file_path, "wb") as buf:
            shutil.copyfileobj(actual_file.file, buf)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to save image: {exc}")

    user_id = current_user.get("user_id", 1)

    # Create scan record immediately so we have an ID
    scan = Scan(
        user_id=user_id,
        image_path=file_path,
        status="review_pending",
        quality_override=force_proceed,
    )
    db.add(scan)
    db.commit()
    db.refresh(scan)

    # Run OCR pipeline (no compliance evaluation)
    try:
        result = analyze_product(file_path, force_proceed=force_proceed)
    except Exception as exc:
        logger.error(f"[scan:{scan.id}] OCR pipeline error: {exc}")
        scan.status = "review_pending"
        scan.quality_tier = "VERY_POOR"
        db.commit()
        raise HTTPException(status_code=500, detail=f"OCR processing failed: {exc}")

    quality_tier = result.get("quality_tier", "GOOD")
    quality = result.get("quality", {})
    has_quality_warning = quality_tier in ("POOR", "VERY_POOR")

    # Update scan with quality info
    scan.quality_tier = quality_tier
    scan.has_quality_warning = has_quality_warning
    scan.is_food_product = result.get("is_food_product", False)

    # Persist extracted fields with full audit trail
    fields_data = result.get("fields", {})
    confidences_data = result.get("confidences", {})
    field_statuses = result.get("field_statuses", {})
    field_level_results = {}  # raw per-field OCR results (has bbox, variant info)

    # Try to get bboxes from the pipeline result
    # The analyze_product doesn't directly return field_level_results but we can
    # get them from the confidence data
    for f_name, raw_val in fields_data.items():
        val_str = (
            str(raw_val["value"]) if isinstance(raw_val, dict) and "value" in raw_val
            else str(raw_val) if raw_val is not None else None
        )
        conf_entry = confidences_data.get(f_name, {})
        conf_val = conf_entry.get("confidence", None) if isinstance(conf_entry, dict) else None
        fs = field_statuses.get(f_name, "NOT_DETECTED")

        ef = ExtractedField(
            scan_id=scan.id,
            field_name=f_name,
            field_value=val_str,
            original_ocr_value=val_str,
            corrected_value=None,
            confidence=conf_val,
            bounding_box=None,  # bboxes would need deeper pipeline access
            correction_status="ocr_original",
            field_status=fs,
            created_at=datetime.now(timezone.utc),
        )
        db.add(ef)

    # Store raw OCR text for the expandable section
    ocr_text = result.get("ocr_text", "")
    if ocr_text:
        db.add(ExtractedField(
            scan_id=scan.id,
            field_name="_ocr_text",
            field_value=ocr_text,
            original_ocr_value=ocr_text,
            confidence=1.0,
            correction_status="ocr_original",
            created_at=datetime.now(timezone.utc),
        ))

    db.commit()

    # Build review response
    fields_records = db.query(ExtractedField).filter(ExtractedField.scan_id == scan.id).all()

    review_data = _build_review_response(scan, fields_records)
    review_data["needs_retake_prompt"] = result.get("needs_retake_prompt", False)
    review_data["image_quality_warning"] = result.get("image_quality_warning")
    review_data["quality_summary"] = quality
    review_data["image_url"] = f"/uploads/{filename}"

    return {
        "message": "OCR extraction complete. Please review the extracted fields.",
        "scan_id": scan.id,
        **review_data,
    }


# ── GET /scans/{id}/review ────────────────────────────────────────────────

@router.get("/{scan_id}/review")
def get_scan_review(
    scan_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_optional),
):
    """Returns the OCR review payload for an existing scan."""
    scan = db.query(Scan).filter(Scan.id == scan_id).first()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    _safe_scan_access(scan, current_user)

    fields_records = db.query(ExtractedField).filter(ExtractedField.scan_id == scan_id).all()
    return _build_review_response(scan, fields_records)


# ── PUT /scans/{id}/fields ────────────────────────────────────────────────

@router.put("/{scan_id}/fields")
def save_field_corrections(
    scan_id: int,
    body: ReviewSubmission,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Save user corrections to extracted fields.

    For each correction:
    - Sets corrected_value, corrected_at, corrected_by_user_id
    - Updates field_value (used for compliance) to the corrected value
    - Sets correction_status to "user_corrected" or "user_marked_unreadable"
    - NEVER overwrites original_ocr_value (preserves audit trail)

    Raises 409 if the scan is already confirmed.
    """
    scan = db.query(Scan).filter(Scan.id == scan_id).first()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    _safe_scan_access(scan, current_user)

    if scan.user_confirmed:
        raise HTTPException(
            status_code=409,
            detail="Scan already confirmed. Cannot modify fields after confirmation."
        )

    uid = current_user.get("user_id")
    now = datetime.now(timezone.utc)
    updated = []

    for correction in body.corrections:
        ef = db.query(ExtractedField).filter(
            ExtractedField.scan_id == scan_id,
            ExtractedField.field_name == correction.field_name,
        ).first()

        if not ef:
            # Create a new field record if it was entirely absent from OCR
            ef = ExtractedField(
                scan_id=scan_id,
                field_name=correction.field_name,
                original_ocr_value=None,
                confidence=None,
                correction_status="user_corrected",
                created_at=now,
            )
            db.add(ef)

        if correction.mark_unreadable:
            ef.corrected_value = None
            ef.field_value = None
            ef.correction_status = "user_marked_unreadable"
            ef.field_status = "UNREADABLE"
        else:
            new_val = correction.corrected_value
            ef.corrected_value = new_val
            ef.field_value = new_val
            ef.correction_status = "user_corrected"
            ef.field_status = "VALID" if new_val else "NOT_DETECTED"

        ef.corrected_at = now
        ef.corrected_by_user_id = uid
        updated.append(correction.field_name)

    db.commit()
    return {"message": f"Corrections saved for {len(updated)} field(s).", "updated_fields": updated}


# ── POST /scans/{id}/confirm ──────────────────────────────────────────────

@router.post("/{scan_id}/confirm")
def confirm_and_generate_report(
    scan_id: int,
    body: Optional[ConfirmRequest] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_optional),
):
    """
    Confirm the reviewed fields and run the compliance evaluation.

    - Idempotent: if scan is already confirmed, returns existing result.
    - Compliance is evaluated on the current field values (corrected if corrected, original otherwise).
    - Does NOT rerun OCR — uses stored field values.
    - Violation records are only created once; duplicate confirmation is a no-op.
    """
    scan = db.query(Scan).filter(Scan.id == scan_id).first()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    _safe_scan_access(scan, current_user)

    # Idempotency: return existing report if already confirmed
    if scan.user_confirmed:
        return _build_confirmed_result(scan, db)

    # Gather the current (reviewed) field values from DB
    fields_records = db.query(ExtractedField).filter(
        ExtractedField.scan_id == scan_id,
        ExtractedField.field_name != "_ocr_text",
    ).all()

    fields = {}
    field_statuses = {}
    confidences = {}
    ocr_text_record = db.query(ExtractedField).filter(
        ExtractedField.scan_id == scan_id,
        ExtractedField.field_name == "_ocr_text",
    ).first()
    ocr_text = ocr_text_record.field_value if ocr_text_record else ""

    for ef in fields_records:
        val = ef.field_value
        fields[ef.field_name] = val
        field_statuses[ef.field_name] = ef.field_status or "NOT_DETECTED"
        if ef.confidence is not None:
            confidences[ef.field_name] = {"confidence": ef.confidence, "status": ef.field_status or "NOT_DETECTED"}

    # Import rule engine
    try:
        from rules.rule_engine import check_compliance, is_food_product
    except ImportError:
        _root = Path(__file__).resolve().parent.parent.parent.parent
        sys.path.insert(0, str(_root / "rules"))
        from rule_engine import check_compliance, is_food_product

    quality_tier = scan.quality_tier or "GOOD"

    compliance = check_compliance(
        fields,
        confidences=confidences,
        field_statuses=field_statuses,
        ocr_text=ocr_text,
        quality_tier=quality_tier,
    )

    # Persist violations (only on first confirmation)
    for viol in compliance.get("violations", []):
        db.add(Violation(
            scan_id=scan_id,
            field=viol.get("field", "unknown"),
            description=viol.get("description", ""),
            severity=viol.get("severity", "medium"),
            evidence_path=scan.image_path,
        ))

    # Update scan status
    rules_checked = compliance.get("rules_checked", 8)
    violation_count = compliance.get("violation_count", 0)
    passed_count = max(0, rules_checked - violation_count)
    score = round((passed_count / rules_checked) * 100, 1) if rules_checked else 0.0

    scan.status = compliance["status"]
    scan.score = score
    scan.user_confirmed = True
    scan.confirmed_at = datetime.now(timezone.utc)
    scan.rules_checked = rules_checked
    scan.violation_count = violation_count
    scan.is_food_product = compliance.get("is_food_product", False)

    db.commit()

    return _build_confirmed_result(scan, db)


def _build_confirmed_result(scan: Scan, db: Session) -> dict:
    """Build the post-confirmation result response."""
    fields_records = db.query(ExtractedField).filter(ExtractedField.scan_id == scan.id).all()
    violations_records = db.query(Violation).filter(Violation.scan_id == scan.id).all()

    fields_dict = {}
    confidences_dict = {}
    corrections_summary = {}
    ocr_text = ""

    for ef in fields_records:
        if ef.field_name == "_ocr_text":
            ocr_text = ef.field_value or ""
            continue
        fields_dict[ef.field_name] = ef.field_value
        confidences_dict[ef.field_name] = ef.confidence
        corrections_summary[ef.field_name] = {
            "original_ocr_value": ef.original_ocr_value,
            "corrected_value":    ef.corrected_value,
            "correction_status":  ef.correction_status or "ocr_original",
        }

    filename = Path(scan.image_path).name if scan.image_path else ""

    return {
        "scan_id":            scan.id,
        "status":             scan.status,
        "score":              scan.score,
        "user_confirmed":     scan.user_confirmed,
        "confirmed_at":       scan.confirmed_at.isoformat() if scan.confirmed_at else None,
        "quality_tier":       scan.quality_tier,
        "has_quality_warning": scan.has_quality_warning,
        "is_food_product":    scan.is_food_product,
        "image_url":          f"/uploads/{filename}" if filename else None,
        "fields":             fields_dict,
        "confidences":        confidences_dict,
        "corrections_summary": corrections_summary,
        "violations": [
            {
                "field":       v.field,
                "severity":    v.severity,
                "description": v.description,
            }
            for v in violations_records
        ],
        "violation_count": len(violations_records),
        "rules_checked":   scan.rules_checked or 8,
        "summary": (
            f"Compliance status: {scan.status} with "
            f"{scan.violation_count or 0} violation(s) across "
            f"{scan.rules_checked or 8} rules."
        ),
    }
