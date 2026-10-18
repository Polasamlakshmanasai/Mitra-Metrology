# app/services/report_service.py
"""
Inspection Report Service for Mitra Metrology.
Generates audit-grade commodity inspection reports in structured JSON and downloadable PDF formats.
"""

import os
import re
from datetime import datetime, timezone
from typing import Dict, Any, List
from io import BytesIO

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch


def build_inspection_report(scan, fields_records: List, violations_records: List) -> Dict[str, Any]:
    """
    Constructs the standard Mitra Metrology structured inspection report.
    Single source of truth snapshot used by API and PDF generation.
    """
    fields_dict = {}
    confidence_dict = {}
    status_dict = {}

    for f in fields_records:
        if f.field_name == "_ocr_text":
            fields_dict["ocr_text"] = f.field_value
            continue

        # Priority: corrected_value if edited, otherwise field_value or original_ocr_value
        val = f.corrected_value if f.corrected_value is not None else (f.field_value or f.original_ocr_value)
        fields_dict[f.field_name] = val
        confidence_dict[f.field_name] = f.confidence
        if f.field_status:
            status_dict[f.field_name] = f.field_status
        else:
            status_dict[f.field_name] = "VALID" if val and str(val).strip() != "" else "NOT_DETECTED"

    # Derive statuses from violations if not already set on field
    for v in violations_records:
        if v.field in status_dict and status_dict[v.field] == "NOT_DETECTED":
            desc = v.description.lower()
            if "could not be read" in desc or "unreadable" in desc:
                status_dict[v.field] = "UNREADABLE"
            elif "confirmed absent" in desc or "is absent" in desc:
                status_dict[v.field] = "MISSING"
            elif "low ocr confidence" in desc or "low confidence" in desc:
                status_dict[v.field] = "LOW_CONFIDENCE"

    # Clean product name (remove brackets, normalize capitalization)
    raw_prod = fields_dict.get("product_name")
    if not raw_prod or str(raw_prod).strip() in ("", "None", "N/A"):
        product_name = "Packaged Commodity Sample"
    else:
        p_clean = re.sub(r"^[\(\[\{\"\':\s\-_=]+|[\)\]\}\"\':\s\-_=]+$", "", str(raw_prod)).strip()
        if p_clean.lower() == "lays":
            product_name = "Lay's"
        elif p_clean.islower():
            product_name = p_clean.title()
        else:
            product_name = p_clean

    # Do not use placeholder "Declared on Package" as manufacturer
    mfg_raw = fields_dict.get("manufacturer") or fields_dict.get("manufacturer_name")
    if not mfg_raw or str(mfg_raw).strip() in ("", "None", "N/A", "Declared on Package"):
        manufacturer = "NOT DETECTED"
    else:
        manufacturer = str(mfg_raw).strip()

    addr_raw = fields_dict.get("manufacturer_address") or fields_dict.get("address")
    if not addr_raw or str(addr_raw).strip() in ("", "None", "N/A"):
        address = "NOT DETECTED"
    else:
        address = str(addr_raw).strip()

    created_iso = scan.created_at.strftime("%d/%m/%Y %H:%M:%S") if hasattr(scan, "created_at") and scan.created_at else datetime.now(timezone.utc).strftime("%d/%m/%Y %H:%M:%S")

    # Determine if image quality was poor
    has_unreadable = any(s == "UNREADABLE" for s in status_dict.values())
    quality_warning = "Image quality may be too low for reliable OCR." if has_unreadable else None

    user_confirmed = getattr(scan, "user_confirmed", False)
    is_food = getattr(scan, "is_food_product", False)

    # Resolve best before and expiry dates reliably
    best_before_val = (
        fields_dict.get("best_before")
        or fields_dict.get("expiry_date")
        or fields_dict.get("expiry_best_before")
        or "NOT DETECTED"
    )

    violations_list = []
    lm_violations = []
    fssai_violations = []

    for v in violations_records:
        regime = getattr(v, "regime", None)
        if not regime:
            regime = "FSSAI" if (v.field == "fssai" or "fssai" in v.description.lower()) else "LEGAL_METROLOGY"
        v_item = {
            "field": v.field,
            "severity": v.severity,
            "description": v.description,
            "evidence_path": v.evidence_path,
            "regime": regime,
        }
        violations_list.append(v_item)
        if regime == "FSSAI":
            fssai_violations.append(v_item)
        else:
            lm_violations.append(v_item)

    return {
        "report_id": f"REP-MM-{scan.id:05d}",
        "scan_id": scan.id,
        "date": created_iso,
        "status": scan.status,
        "user_confirmed": user_confirmed,
        "is_draft": not user_confirmed,
        "draft_banner": "PRELIMINARY AUDIT REPORT — DRAFT (PENDING HUMAN VERIFICATION)" if not user_confirmed else None,
        "is_food_product": is_food,
        "image_quality_warning": quality_warning,
        "product": {
            "name": product_name,
            "manufacturer": manufacturer,
            "address": address,
        },
        "declared_information": {
            "mrp": fields_dict.get("mrp", "NOT DETECTED"),
            "net_quantity": fields_dict.get("net_quantity", "NOT DETECTED"),
            "manufacturing_date": fields_dict.get("manufacturing_date", "NOT DETECTED"),
            "best_before": best_before_val,
            "expiry_date": fields_dict.get("expiry_date", best_before_val),
            "fssai": fields_dict.get("fssai", "NOT DETECTED"),
            "consumer_care": fields_dict.get("consumer_care", "NOT DETECTED")
        },
        "confidence_scores": confidence_dict,
        "field_statuses": status_dict,
        "compliance": {
            "status": scan.status,
            "rules_checked": getattr(scan, "rules_checked", 8) or 8,
            "violations_count": len(violations_records)
        },
        "violations": violations_list,
        "legal_metrology_violations": lm_violations,
        "fssai_violations": fssai_violations,
        "evidence": {
            "image_path": scan.image_path,
            "ocr_text_available": bool(fields_dict.get("ocr_text"))
        },
        "disclaimer": "This inspection was automatically conducted by Mitra Metrology in accordance with the Legal Metrology (Packaged Commodities) Rules, 2011 and FSSAI Labelling Regulations. Physical laboratory testing is required for substance validation."
    }


def generate_pdf_report_buffer(report: Dict[str, Any]) -> BytesIO:
    """
    Renders an official PDF inspection document matching the statutory Mitra Metrology format.
    Segregates Legal Metrology from FSSAI findings and displays draft banner if unconfirmed.
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Heading1"],
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#1e3a8a"),
        alignment=1
    )
    subtitle_style = ParagraphStyle(
        "DocSubTitle",
        parent=styles["Normal"],
        fontSize=11,
        leading=14,
        textColor=colors.HexColor("#475569"),
        alignment=1
    )
    section_heading = ParagraphStyle(
        "SectionHeading",
        parent=styles["Heading2"],
        fontSize=11.5,
        leading=14.5,
        textColor=colors.HexColor("#0f172a"),
        spaceBefore=7,
        spaceAfter=3
    )
    cell_style = ParagraphStyle("Cell", parent=styles["Normal"], fontSize=8.5, leading=11)
    cell_bold = ParagraphStyle("CellBold", parent=styles["Normal"], fontSize=8.5, leading=11, fontName="Helvetica-Bold")

    elements = []

    # 1. Draft banner if not yet user-confirmed
    user_confirmed = report.get("user_confirmed", True)
    if not user_confirmed:
        draft_p = Paragraph(
            "<b>PRELIMINARY AUDIT REPORT — DRAFT (PENDING HUMAN VERIFICATION)</b><br/>"
            "<font size=7.5>This inspection snapshot reflects automated OCR extraction prior to final officer/user confirmation.</font>",
            ParagraphStyle("DraftB", fontSize=9, leading=12, alignment=1, textColor=colors.HexColor("#92400e"))
        )
        t_draft = Table([[draft_p]], colWidths=[540])
        t_draft.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#fef3c7")),
            ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#f59e0b")),
            ('PADDING', (0,0), (-1,-1), 5),
        ]))
        elements.append(t_draft)
        elements.append(Spacer(1, 6))

    # Header
    elements.append(Paragraph("MITRA METROLOGY", title_style))
    elements.append(Paragraph("COMMODITY INSPECTION AUDIT REPORT", subtitle_style))
    elements.append(Spacer(1, 6))
    elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#1e3a8a"), spaceAfter=10))

    # Meta banner
    status = report.get("status", "REVIEW REQUIRED")
    status_color = "#16a34a" if status == "COMPLIANT" else ("#dc2626" if status == "NON-COMPLIANT" else "#ca8a04")

    status_p = Paragraph(f"<font color='{status_color}'><b>STATUS: {status}</b></font>", ParagraphStyle("St", fontSize=12, fontName="Helvetica-Bold"))
    id_p = Paragraph(f"<b>Inspection ID:</b> {report.get('scan_id')} | <b>Report ID:</b> {report.get('report_id')}", cell_style)
    date_p = Paragraph(f"<b>Date:</b> {report.get('date')} | <b>Confirmation:</b> {'Confirmed' if user_confirmed else 'Pending Review'}", cell_style)

    meta_table = Table([[id_p, status_p], [date_p, ""]], colWidths=[340, 200])
    meta_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
    ]))
    elements.append(meta_table)
    elements.append(Spacer(1, 8))

    # Quality Warning if applicable
    qw = report.get("image_quality_warning")
    if qw:
        qw_p = Paragraph(f"<b>Image Quality Notice:</b> {qw} Declarations not detected on image must be physically inspected.", ParagraphStyle("QW", fontSize=8, leading=10, textColor=colors.HexColor("#b45309")))
        t_qw = Table([[qw_p]], colWidths=[540])
        t_qw.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#fffbeb")),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#fcd34d")),
            ('PADDING', (0,0), (-1,-1), 4),
        ]))
        elements.append(t_qw)
        elements.append(Spacer(1, 6))

    # Product Section
    elements.append(Paragraph("PRODUCT & MANUFACTURER DETAILS", section_heading))
    prod = report.get("product", {})
    prod_data = [
        [Paragraph("Product Name", cell_bold), Paragraph(str(prod.get("name", "NOT DETECTED")), cell_style)],
        [Paragraph("Manufacturer / Packer", cell_bold), Paragraph(str(prod.get("manufacturer", "NOT DETECTED")), cell_style)],
        [Paragraph("Factory Address", cell_bold), Paragraph(str(prod.get("address", "NOT DETECTED")), cell_style)],
    ]
    t_prod = Table(prod_data, colWidths=[150, 390])
    t_prod.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (0,-1), colors.HexColor("#f8fafc")),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
        ('PADDING', (0,0), (-1,-1), 4),
    ]))
    elements.append(t_prod)
    elements.append(Spacer(1, 8))

    # Declared Information & Confidence
    elements.append(Paragraph("DECLARED INFORMATION & OCR CONFIDENCE", section_heading))
    decl = report.get("declared_information", {})
    conf = report.get("confidence_scores", {})
    f_statuses = report.get("field_statuses", {})

    decl_data = [
        [Paragraph("Statutory Declaration", cell_bold), Paragraph("Extracted / Reviewed Value", cell_bold), Paragraph("Confidence", cell_bold), Paragraph("Status", cell_bold)]
    ]
    for key, label in [
        ("mrp", "MRP (Max Retail Price)"),
        ("net_quantity", "Net Quantity"),
        ("manufacturing_date", "Date of Mfg / Packing"),
        ("best_before", "Best Before / Expiry"),
        ("fssai", "FSSAI License No."),
        ("consumer_care", "Consumer Grievance Care"),
    ]:
        val = decl.get(key, "NOT DETECTED")
        c_val = conf.get(key, 0.0)
        c_pct = f"{int(c_val * 100)}%" if c_val else "N/A"
        fs = f_statuses.get(key, "NOT_DETECTED")
        decl_data.append([
            Paragraph(label, cell_style),
            Paragraph(str(val), cell_style),
            Paragraph(c_pct, cell_bold if c_val and c_val >= 0.9 else cell_style),
            Paragraph(fs, cell_style)
        ])

    t_decl = Table(decl_data, colWidths=[160, 230, 75, 75])
    t_decl.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#f1f5f9")),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
        ('PADDING', (0,0), (-1,-1), 3),
    ]))
    elements.append(t_decl)
    elements.append(Spacer(1, 8))

    # Compliance & Violations: Segregated by Regime
    elements.append(Paragraph("STATUTORY COMPLIANCE EVALUATION", section_heading))
    lm_viols = report.get("legal_metrology_violations", [])
    fssai_viols = report.get("fssai_violations", [])
    if not lm_viols and not fssai_viols:
        viols = report.get("violations", [])
        lm_viols = [v for v in viols if v.get("regime") != "FSSAI"]
        fssai_viols = [v for v in viols if v.get("regime") == "FSSAI"]

    # 1. Legal Metrology
    elements.append(Paragraph("<b>1. Legal Metrology (Packaged Commodities) Rules, 2011 Findings</b>", cell_bold))
    if not lm_viols:
        t_lm = Table([[Paragraph("<font color='#16a34a'><b>COMPLIANT</b> — All mandatory Legal Metrology declarations verified on package.</font>", cell_style)]], colWidths=[540])
        t_lm.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#f0fdf4")),
            ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#16a34a")),
            ('PADDING', (0,0), (-1,-1), 5),
        ]))
        elements.append(t_lm)
    else:
        v_data = [[Paragraph("Field", cell_bold), Paragraph("Severity", cell_bold), Paragraph("Rule & Description", cell_bold)]]
        for v in lm_viols:
            sev = v.get("severity", "medium").upper()
            v_data.append([
                Paragraph(str(v.get("field", "N/A")).upper(), cell_style),
                Paragraph(sev, cell_bold),
                Paragraph(str(v.get("description", "")), cell_style)
            ])
        t_viol = Table(v_data, colWidths=[110, 70, 360])
        t_viol.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#fef2f2")),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#fca5a5")),
            ('PADDING', (0,0), (-1,-1), 3),
        ]))
        elements.append(t_viol)

    elements.append(Spacer(1, 6))

    # 2. FSSAI
    is_food = report.get("is_food_product", False) or bool(fssai_viols)
    if is_food:
        elements.append(Paragraph("<b>2. Food Safety & Standards (Labelling & Display) Regulations Findings</b>", cell_bold))
        if not fssai_viols:
            t_fssai = Table([[Paragraph("<font color='#16a34a'><b>COMPLIANT</b> — Mandatory FSSAI food declarations verified.</font>", cell_style)]], colWidths=[540])
            t_fssai.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#f0fdf4")),
                ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#16a34a")),
                ('PADDING', (0,0), (-1,-1), 5),
            ]))
            elements.append(t_fssai)
        else:
            v_data = [[Paragraph("Field", cell_bold), Paragraph("Severity", cell_bold), Paragraph("Regulation & Finding", cell_bold)]]
            for v in fssai_viols:
                sev = v.get("severity", "medium").upper()
                v_data.append([
                    Paragraph(str(v.get("field", "N/A")).upper(), cell_style),
                    Paragraph(sev, cell_bold),
                    Paragraph(str(v.get("description", "")), cell_style)
                ])
            t_viol = Table(v_data, colWidths=[110, 70, 360])
            t_viol.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#fff7ed")),
                ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#fdba74")),
                ('PADDING', (0,0), (-1,-1), 3),
            ]))
            elements.append(t_viol)
    else:
        elements.append(Paragraph("<b>2. Food Safety & Standards (FSSAI) Regulations</b>", cell_bold))
        t_fssai_na = Table([[Paragraph("<i>Exempt / Not Applicable — Commodity is classified as a non-food packaged commodity.</i>", cell_style)]], colWidths=[540])
        t_fssai_na.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#f8fafc")),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
            ('PADDING', (0,0), (-1,-1), 4),
        ]))
        elements.append(t_fssai_na)

    elements.append(Spacer(1, 10))
    elements.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#94a3b8"), spaceAfter=6))
    elements.append(Paragraph(f"<b>Statutory Disclaimer:</b> {report.get('disclaimer')}", ParagraphStyle("Disc", parent=styles["Normal"], fontSize=7.5, leading=9.5, textColor=colors.HexColor("#64748b"))))

    doc.build(elements)
    buffer.seek(0)
    return buffer
