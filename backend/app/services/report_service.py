# app/services/report_service.py
"""
Inspection Report Service for Mitra Metrology.
Generates audit-grade commodity inspection reports in structured JSON and downloadable PDF formats.
"""

import os
from datetime import datetime
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
    """
    fields_dict = {}
    confidence_dict = {}
    for f in fields_records:
        fields_dict[f.field_name] = f.field_value
        confidence_dict[f.field_name] = f.confidence

    product_name = fields_dict.get("product_name", "Packaged Commodity Sample")
    manufacturer = fields_dict.get("manufacturer", fields_dict.get("manufacturer_name", "Declared on Package"))

    created_iso = scan.created_at.strftime("%d/%m/%Y %H:%M:%S") if hasattr(scan, "created_at") and scan.created_at else datetime.utcnow().strftime("%d/%m/%Y %H:%M:%S")

    return {
        "report_id": f"REP-MM-{scan.id:05d}",
        "scan_id": scan.id,
        "date": created_iso,
        "status": scan.status,
        "product": {
            "name": product_name,
            "manufacturer": manufacturer,
            "address": fields_dict.get("address", fields_dict.get("manufacturer_address", "N/A"))
        },
        "declared_information": {
            "mrp": fields_dict.get("mrp", "N/A"),
            "net_quantity": fields_dict.get("net_quantity", "N/A"),
            "manufacturing_date": fields_dict.get("manufacturing_date", "N/A"),
            "best_before": fields_dict.get("best_before", fields_dict.get("expiry_best_before", "N/A")),
            "fssai": fields_dict.get("fssai", "N/A"),
            "consumer_care": fields_dict.get("consumer_care", "N/A")
        },
        "confidence_scores": confidence_dict,
        "compliance": {
            "status": scan.status,
            "rules_checked": 8,
            "violations_count": len(violations_records)
        },
        "violations": [
            {
                "field": v.field,
                "severity": v.severity,
                "description": v.description,
                "evidence_path": v.evidence_path
            }
            for v in violations_records
        ],
        "evidence": {
            "image_path": scan.image_path,
            "ocr_text_available": bool(fields_dict.get("ocr_text"))
        },
        "disclaimer": "This inspection was automatically conducted by Mitra Metrology in accordance with the Legal Metrology (Packaged Commodities) Rules, 2011 and FSSAI Labelling Regulations. Physical laboratory testing is required for substance validation."
    }


def generate_pdf_report_buffer(report: Dict[str, Any]) -> BytesIO:
    """
    Renders an official PDF inspection document matching the statutory Mitra Metrology format.
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
        fontSize=13,
        leading=16,
        textColor=colors.HexColor("#0f172a"),
        spaceBefore=8,
        spaceAfter=4
    )
    cell_style = ParagraphStyle("Cell", parent=styles["Normal"], fontSize=9, leading=12)
    cell_bold = ParagraphStyle("CellBold", parent=styles["Normal"], fontSize=9, leading=12, fontName="Helvetica-Bold")

    elements = []

    # Header
    elements.append(Paragraph("MITRA METROLOGY", title_style))
    elements.append(Paragraph("COMMODITY INSPECTION AUDIT REPORT", subtitle_style))
    elements.append(Spacer(1, 10))
    elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#1e3a8a"), spaceAfter=12))

    # Meta banner
    status = report.get("status", "REVIEW REQUIRED")
    status_color = "#16a34a" if status == "COMPLIANT" else ("#dc2626" if status == "NON-COMPLIANT" else "#ca8a04")

    status_p = Paragraph(f"<font color='{status_color}'><b>STATUS: {status}</b></font>", ParagraphStyle("St", fontSize=12, fontName="Helvetica-Bold"))
    id_p = Paragraph(f"<b>Inspection ID:</b> {report.get('scan_id')} | <b>Report ID:</b> {report.get('report_id')}", cell_style)
    date_p = Paragraph(f"<b>Date:</b> {report.get('date')}", cell_style)

    meta_table = Table([[id_p, status_p], [date_p, ""]], colWidths=[340, 200])
    meta_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    elements.append(meta_table)
    elements.append(Spacer(1, 10))

    # Product Section
    elements.append(Paragraph("PRODUCT & MANUFACTURER DETAILS", section_heading))
    prod = report.get("product", {})
    prod_data = [
        [Paragraph("Product Name", cell_bold), Paragraph(str(prod.get("name", "N/A")), cell_style)],
        [Paragraph("Manufacturer / Packer", cell_bold), Paragraph(str(prod.get("manufacturer", "N/A")), cell_style)],
        [Paragraph("Factory Address", cell_bold), Paragraph(str(prod.get("address", "N/A")), cell_style)],
    ]
    t_prod = Table(prod_data, colWidths=[150, 390])
    t_prod.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (0,-1), colors.HexColor("#f8fafc")),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
        ('PADDING', (0,0), (-1,-1), 5),
    ]))
    elements.append(t_prod)
    elements.append(Spacer(1, 10))

    # Declared Information & Confidence
    elements.append(Paragraph("DECLARED INFORMATION & OCR CONFIDENCE", section_heading))
    decl = report.get("declared_information", {})
    conf = report.get("confidence_scores", {})

    decl_data = [
        [Paragraph("Mandatory Declaration", cell_bold), Paragraph("Extracted Value", cell_bold), Paragraph("Confidence", cell_bold)]
    ]
    for key, label in [
        ("mrp", "MRP (Max Retail Price)"),
        ("net_quantity", "Net Quantity"),
        ("manufacturing_date", "Date of Mfg / Packing"),
        ("best_before", "Best Before / Expiry"),
        ("fssai", "FSSAI License No."),
        ("consumer_care", "Consumer Grievance Care"),
    ]:
        val = decl.get(key, "MISSING")
        c_val = conf.get(key, 0.0)
        c_pct = f"{int(c_val * 100)}%" if c_val else "N/A"
        decl_data.append([
            Paragraph(label, cell_style),
            Paragraph(str(val), cell_style),
            Paragraph(c_pct, cell_bold if c_val and c_val >= 0.9 else cell_style)
        ])

    t_decl = Table(decl_data, colWidths=[180, 260, 100])
    t_decl.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#f1f5f9")),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
        ('PADDING', (0,0), (-1,-1), 4),
    ]))
    elements.append(t_decl)
    elements.append(Spacer(1, 10))

    # Compliance & Violations
    elements.append(Paragraph("COMPLIANCE EVALUATION & VIOLATIONS", section_heading))
    viols = report.get("violations", [])
    if not viols:
        v_data = [[Paragraph("No statutory violations detected. All required Legal Metrology and FSSAI declarations are present.", cell_style)]]
        t_viol = Table(v_data, colWidths=[540])
        t_viol.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#f0fdf4")),
            ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#16a34a")),
            ('PADDING', (0,0), (-1,-1), 8),
        ]))
        elements.append(t_viol)
    else:
        v_data = [
            [Paragraph("Field / Rule", cell_bold), Paragraph("Severity", cell_bold), Paragraph("Violation Description", cell_bold)]
        ]
        for v in viols:
            sev = v.get("severity", "medium").upper()
            v_data.append([
                Paragraph(str(v.get("field", "N/A")).upper(), cell_style),
                Paragraph(sev, cell_bold),
                Paragraph(str(v.get("description", "")), cell_style)
            ])
        t_viol = Table(v_data, colWidths=[120, 80, 340])
        t_viol.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#fef2f2")),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#fca5a5")),
            ('PADDING', (0,0), (-1,-1), 4),
        ]))
        elements.append(t_viol)

    elements.append(Spacer(1, 14))
    elements.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#94a3b8"), spaceAfter=8))
    elements.append(Paragraph(f"<b>Statutory Disclaimer:</b> {report.get('disclaimer')}", ParagraphStyle("Disc", parent=styles["Normal"], fontSize=8, leading=10, textColor=colors.HexColor("#64748b"))))

    doc.build(elements)
    buffer.seek(0)
    return buffer
