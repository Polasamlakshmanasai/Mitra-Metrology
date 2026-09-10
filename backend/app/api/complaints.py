# app/api/complaints.py
"""
Complaints API router for consumer grievance submission and officer resolution lifecycle.
"""

from typing import Optional, List
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.complaint import Complaint
from app.core.dependencies import get_current_user, require_officer

router = APIRouter(
    prefix="/complaints",
    tags=["Complaints"]
)

VALID_STATUSES = ["PENDING", "UNDER_REVIEW", "RESOLVED", "REJECTED"]


class ComplaintCreate(BaseModel):
    scan_id: Optional[int] = None
    product_name: Optional[str] = None
    manufacturer: Optional[str] = None
    violation_type: Optional[str] = None
    description: str


class ComplaintStatusUpdate(BaseModel):
    status: str


@router.post("/")
def create_complaint(
    complaint_data: ComplaintCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """
    Step 20: Submit a formal grievance against a non-compliant packaged commodity.
    Automatically assigns the authenticated user's ID.
    """
    if not complaint_data.description or not complaint_data.description.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Complaint description cannot be empty"
        )

    new_complaint = Complaint(
        scan_id=complaint_data.scan_id,
        user_id=current_user["user_id"],
        product_name=complaint_data.product_name or "Packaged Commodity",
        manufacturer=complaint_data.manufacturer or "Declared on Package",
        violation_type=complaint_data.violation_type or "Legal Metrology Non-Compliance",
        description=complaint_data.description.strip(),
        status="PENDING"
    )
    db.add(new_complaint)
    db.commit()
    db.refresh(new_complaint)

    return {
        "message": "Complaint submitted successfully",
        "complaint_id": new_complaint.id,
        "status": new_complaint.status,
        "created_at": new_complaint.created_at.isoformat() if new_complaint.created_at else None
    }


@router.get("/")
def list_complaints(
    status_filter: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """
    Step 20: List complaints.
    - Officers see all complaints across the system.
    - Citizens see only their own filed complaints.
    """
    query = db.query(Complaint)

    if current_user.get("role") != "officer":
        query = query.filter(Complaint.user_id == current_user["user_id"])

    if status_filter:
        query = query.filter(Complaint.status == status_filter.upper())

    complaints = query.order_by(Complaint.created_at.desc()).limit(limit).all()

    return [
        {
            "id": c.id,
            "scan_id": c.scan_id,
            "user_id": c.user_id,
            "product_name": c.product_name,
            "manufacturer": c.manufacturer,
            "violation_type": c.violation_type,
            "description": c.description,
            "status": c.status,
            "created_at": c.created_at.strftime("%d %b %Y, %H:%M") if c.created_at else None
        }
        for c in complaints
    ]


@router.patch("/{complaint_id}/status")
def update_complaint_status(
    complaint_id: int,
    status_update: ComplaintStatusUpdate,
    db: Session = Depends(get_db),
    officer=Depends(require_officer)
):
    """
    Step 20: Update complaint status (Officers only: PENDING, UNDER_REVIEW, RESOLVED, REJECTED).
    """
    new_status = status_update.status.upper().strip()
    if new_status not in VALID_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status '{status_update.status}'. Allowed: {', '.join(VALID_STATUSES)}"
        )

    complaint = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")

    complaint.status = new_status
    db.commit()

    return {
        "message": f"Complaint status updated to {new_status}",
        "complaint_id": complaint_id,
        "status": complaint.status
    }
