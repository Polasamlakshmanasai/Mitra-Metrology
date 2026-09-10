# app/api/inspections.py
"""
Inspections API router providing analytical metrics and inspection oversight for Officers.
"""

import os
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.scan import Scan
from app.models.violation import Violation
from app.models.complaint import Complaint
from app.models.extracted_field import ExtractedField
from app.core.dependencies import require_officer


router = APIRouter(
    prefix="/inspections",
    tags=["Inspections"]
)


@router.get("/stats")
def get_inspection_stats(db: Session = Depends(get_db)):
    """
    Step 19: Returns real dynamic metrics computed directly from database records.
    Matches format:
    {
      "total_inspections": 120,
      "compliant": 72,
      "review_required": 28,
      "non_compliant": 20
    }
    """
    total_scans = db.query(Scan).count()
    compliant_scans = db.query(Scan).filter(Scan.status == "COMPLIANT").count()
    review_scans = db.query(Scan).filter(
        Scan.status.in_(["REVIEW REQUIRED", "REVIEW_REQUIRED", "FLAGGED_FOR_REVIEW"])
    ).count()
    non_compliant_scans = db.query(Scan).filter(
        Scan.status.in_(["NON-COMPLIANT", "NON_COMPLIANT"])
    ).count()

    total_violations = db.query(Violation).count()
    pending_complaints = db.query(Complaint).filter(Complaint.status == "PENDING").count()

    compliance_rate = round((compliant_scans / total_scans * 100), 1) if total_scans > 0 else 100.0

    return {
        "total_inspections": total_scans,
        "compliant": compliant_scans,
        "review_required": review_scans,
        "non_compliant": non_compliant_scans,
        "total_scans": total_scans,
        "compliant_scans": compliant_scans,
        "non_compliant_scans": non_compliant_scans,
        "compliance_rate": compliance_rate,
        "total_violations": total_violations,
        "pending_complaints": pending_complaints
    }


@router.get("/")
def list_all_inspections(
    status: Optional[str] = None,
    limit: int = 100,
    db: Session = Depends(get_db),
    officer=Depends(require_officer)
):
    """
    Step 18: Officer-only endpoint listing all scans across the system.
    """
    query = db.query(Scan)
    if status:
        query = query.filter(Scan.status == status.upper())

    scans = query.order_by(Scan.created_at.desc()).limit(limit).all()

    inspections = []
    for s in scans:
        prod_field = db.query(ExtractedField).filter(
            ExtractedField.scan_id == s.id,
            ExtractedField.field_name.in_(["product_name", "product"])
        ).first()

        mfr_field = db.query(ExtractedField).filter(
            ExtractedField.scan_id == s.id,
            ExtractedField.field_name.in_(["manufacturer", "manufacturer_name"])
        ).first()

        filename = os.path.basename(s.image_path) if s.image_path else ""

        inspections.append({
            "id": s.id,
            "scan_id": s.id,
            "user_id": s.user_id,
            "product_name": prod_field.field_value if prod_field else "Packaged Commodity",
            "manufacturer": mfr_field.field_value if mfr_field else "Declared on Package",
            "status": s.status,
            "score": s.score,
            "image_url": f"/uploads/{filename}" if filename else None,
            "date": s.created_at.strftime("%d %b %Y") if s.created_at else None,
            "created_at": s.created_at.isoformat() if s.created_at else None
        })

    return inspections


@router.get("/{scan_id}")
def get_officer_inspection_detail(
    scan_id: int,
    db: Session = Depends(get_db),
    officer=Depends(require_officer)
):
    """
    Step 18 & 28: Full officer evidence view:
    Inspection -> Package Image -> OCR -> Fields -> Confidence -> Rules -> Violations -> Evidence.
    """
    scan = db.query(Scan).filter(Scan.id == scan_id).first()
    if not scan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Inspection record not found"
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
        "date": scan.created_at.strftime("%d %b %Y, %H:%M") if scan.created_at else None,
        "created_at": scan.created_at.isoformat() if scan.created_at else None,
        "ocr_text": ocr_text,
        "fields": fields_dict,
        "confidences": confidences_dict,
        "rules_checked": 8,
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
        "evidence": {
            "image_path": scan.image_path,
            "image_url": f"/uploads/{filename}" if filename else None
        }
    }
