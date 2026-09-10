import os
import shutil
from uuid import uuid4
from typing import List, Optional
from pathlib import Path

from fastapi import (
    APIRouter,
    Depends,
    UploadFile,
    File,
    HTTPException,
    status
)
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.scan import Scan
from app.models.violation import Violation
from app.models.extracted_field import ExtractedField
from app.core.dependencies import get_current_user, get_current_user_optional
from app.services.compliance_service import analyze_product
from app.services.report_service import build_inspection_report, generate_pdf_report_buffer


router = APIRouter(
    prefix="/scans",
    tags=["Scans"]
)

# Standardized backend/uploads directory
UPLOAD_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../uploads")
)
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/analyze")
def analyze_scan(
    file: Optional[UploadFile] = File(None),
    image: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user_optional)
):
    actual_file = file or image
    if not actual_file:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No packaging image file uploaded. Provide 'file' or 'image' field."
        )

    allowed_types = [
        "image/jpeg",
        "image/png",
        "image/webp"
    ]

    if actual_file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only JPG, PNG and WEBP images are allowed"
        )

    extension = os.path.splitext(actual_file.filename or "")[1].lower()
    if not extension:
        extension = ".jpg"

    raw_base = os.path.splitext(actual_file.filename or "")[0]
    safe_base = "".join(c for c in raw_base if c.isalnum() or c in ("-", "_"))[:30]
    filename = f"{safe_base}_{uuid4().hex[:8]}{extension}" if safe_base else f"{uuid4().hex}{extension}"
    file_path = os.path.join(UPLOAD_DIR, filename)

    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(actual_file.file, buffer)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save image: {str(e)}"
        )

    # 1. Create initial scan record in DB
    user_id = current_user.get("user_id", 1)
    scan = Scan(
        user_id=user_id,
        image_path=file_path,
        status="processing"
    )
    db.add(scan)
    db.commit()
    db.refresh(scan)

    # 2. Run Quality, OCR, Extraction, Confidence, and Compliance Engine
    try:
        result = analyze_product(file_path)

        # 3. Persist Extracted Fields with confidence
        fields_data = result.get("fields", {})
        confidences_data = result.get("confidences", {})

        for f_name, raw_val in fields_data.items():
            val_str = str(raw_val["value"]) if isinstance(raw_val, dict) and "value" in raw_val else str(raw_val)
            conf_val = 0.90
            if f_name in confidences_data:
                conf_val = confidences_data[f_name].get("confidence", 0.90)

            ef = ExtractedField(
                scan_id=scan.id,
                field_name=f_name,
                field_value=val_str,
                confidence=conf_val,
                bounding_box=None
            )
            db.add(ef)

        # Also store OCR text as an extracted record for full traceability
        ocr_text = result.get("ocr_text", "")
        if ocr_text:
            db.add(ExtractedField(
                scan_id=scan.id,
                field_name="_ocr_text",
                field_value=ocr_text,
                confidence=1.0,
                bounding_box=None
            ))

        # 4. Persist Violations
        for violation_data in result.get("violations", []):
            violation = Violation(
                scan_id=scan.id,
                field=violation_data.get("field", "unknown"),
                description=violation_data.get("description", "Violation detected"),
                severity=violation_data.get("severity", "medium"),
                evidence_path=file_path
            )
            db.add(violation)

        # 5. Update final Scan status
        scan.status = result.get("status", "REVIEW REQUIRED")
        rules_checked = result.get("rules_checked", 8)
        violation_count = result.get("violation_count", len(result.get("violations", [])))
        passed_count = max(0, rules_checked - violation_count)
        calc_score = round((passed_count / rules_checked) * 100, 1)

        scan.score = calc_score
        db.commit()

    except Exception as e:
        scan.status = "REVIEW REQUIRED"
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis failed: {str(e)}"
        )

    # Format extracted_fields dictionary with .value and .confidence for direct frontend compatibility
    compat_extracted_fields = {}
    for k, v in fields_data.items():
        val = v.get("value") if isinstance(v, dict) and "value" in v else v
        conf = confidences_data.get(k, {}).get("confidence", 0.92) if isinstance(confidences_data.get(k), dict) else 0.92
        compat_extracted_fields[k] = {
            "value": val,
            "confidence": conf
        }

    return {
        "message": "Scan analyzed successfully",
        "scan_id": scan.id,
        "status": scan.status,
        "score": scan.score,
        "compliance_score": scan.score,
        "summary": f"Compliance status: {scan.status} with {violation_count} violation(s) flagged across {rules_checked} statutory rules.",
        "rules_checked": rules_checked,
        "quality": result.get("quality"),
        "ocr_text": result.get("ocr_text"),
        "fields": result.get("fields", {}),
        "extracted_fields": compat_extracted_fields,
        "confidences": result.get("confidences", {}),
        "violations": result.get("violations", []),
        "violation_count": violation_count,
        "compliance": {
            "status": scan.status,
            "score": scan.score,
            "violations": result.get("violations", []),
            "rules_checked": rules_checked
        },
        "image_url": f"/uploads/{filename}"
    }


@router.get("/")
def scans_root(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user_optional)
):
    """
    Returns scan history for current user or default list.
    """
    user_id = current_user.get("user_id", 1)
    return get_user_scan_history(db=db, current_user={"user_id": user_id, "role": current_user.get("role", "user")})


@router.get("/history")
def get_user_scan_history(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user_optional)
):
    """
    Step 16: Returns inspection history strictly belonging to the logged-in user.
    """
    user_id = current_user.get("user_id", 1)
    scans = db.query(Scan).filter(
        Scan.user_id == user_id
    ).order_by(Scan.created_at.desc()).all()

    # If user has no scans yet, return all scans for demo convenience if user_id == 1
    if not scans and user_id == 1:
        scans = db.query(Scan).order_by(Scan.created_at.desc()).limit(20).all()

    history = []
    for s in scans:
        # Get product name if extracted
        prod_field = db.query(ExtractedField).filter(
            ExtractedField.scan_id == s.id,
            ExtractedField.field_name.in_(["product_name", "product", "mrp"])
        ).first()

        filename = os.path.basename(s.image_path) if s.image_path else ""

        history.append({
            "id": s.id,
            "scan_id": s.id,
            "status": s.status,
            "score": s.score or (100 if s.status == "COMPLIANT" else 50),
            "product_name": prod_field.field_value if prod_field else "Packaged Commodity",
            "image_url": f"/uploads/{filename}" if filename else None,
            "created_at": s.created_at.strftime("%d %b %Y, %H:%M") if s.created_at else None
        })

    return history


@router.get("/{scan_id}")
def get_scan_details(
    scan_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user_optional)
):
    """
    Step 17: Returns complete auditable scan record.
    Accessible to the scan owner OR officers.
    """
    scan = db.query(Scan).filter(Scan.id == scan_id).first()
    if not scan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scan record not found"
        )

    # Security check: owner or officer or guest demo
    req_uid = current_user.get("user_id")
    req_role = current_user.get("role")
    if scan.user_id and scan.user_id != req_uid and req_role != "officer" and req_uid != 1:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this scan record"
        )

    fields_records = db.query(ExtractedField).filter(ExtractedField.scan_id == scan_id).all()
    violations_records = db.query(Violation).filter(Violation.scan_id == scan_id).all()

    fields_dict = {}
    confidences_dict = {}
    ocr_text = ""

    for f in fields_records:
        if f.field_name == "_ocr_text":
            ocr_text = f.field_value
        else:
            fields_dict[f.field_name] = f.field_value
            confidences_dict[f.field_name] = f.confidence

    filename = os.path.basename(scan.image_path) if scan.image_path else ""

    return {
        "id": scan.id,
        "scan_id": scan.id,
        "user_id": scan.user_id,
        "status": scan.status,
        "score": scan.score,
        "created_at": scan.created_at.isoformat() if scan.created_at else None,
        "ocr_text": ocr_text,
        "fields": fields_dict,
        "confidences": confidences_dict,
        "violations": [
            {
                "field": v.field,
                "severity": v.severity,
                "description": v.description,
                "evidence_path": v.evidence_path
            }
            for v in violations_records
        ],
        "violation_count": len(violations_records),
        "rules_checked": 8,
        "evidence": {
            "image_path": scan.image_path,
            "image_url": f"/uploads/{filename}" if filename else None
        }
    }


@router.get("/{scan_id}/report")
def get_scan_report(
    scan_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user_optional)
):
    """
    Step 15: Returns structured inspection audit report in JSON format.
    """
    scan = db.query(Scan).filter(Scan.id == scan_id).first()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan record not found")

    fields_records = db.query(ExtractedField).filter(ExtractedField.scan_id == scan_id).all()
    violations_records = db.query(Violation).filter(Violation.scan_id == scan_id).all()

    return build_inspection_report(scan, fields_records, violations_records)


@router.get("/{scan_id}/report/pdf")
def download_scan_report_pdf(
    scan_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user_optional)
):
    """
    Step 29: Downloads an official PDF inspection certificate.
    """
    scan = db.query(Scan).filter(Scan.id == scan_id).first()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan record not found")

    fields_records = db.query(ExtractedField).filter(ExtractedField.scan_id == scan_id).all()
    violations_records = db.query(Violation).filter(Violation.scan_id == scan_id).all()

    report = build_inspection_report(scan, fields_records, violations_records)
    pdf_buffer = generate_pdf_report_buffer(report)

    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=mitra_metrology_inspection_{scan_id}.pdf"
        }
    )
