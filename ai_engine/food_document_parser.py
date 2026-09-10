# food_document_parser.py
"""
Document Understanding & Packaging Parser for Indian Pre-Packaged Foods.
Converts OCR text lines and bounding boxes into a standardized Product entity.
"""

import re
from ingredient_parser import parse_ingredients_declaration
from allergen_engine import evaluate_allergens
from nutrition_parser import parse_nutrition_table


def detect_veg_nonveg(ocr_text):
    """
    Identifies vegetarian vs non-vegetarian indicator from packaging text or symbols.
    """
    text_lower = ocr_text.lower()
    if re.search(r"\bnon[\s\-_]?veg(?:etarian)?\b", text_lower):
        return {
            "status": "NON_VEGETARIAN",
            "symbol": "Brown triangle in brown square",
            "confidence": 0.90
        }
    elif re.search(r"\b100%\s*veg(?:etarian)?\b|\bveg(?:etarian)?\b", text_lower):
        return {
            "status": "VEGETARIAN",
            "symbol": "Green dot in green square",
            "confidence": 0.92
        }
    return {
        "status": "NOT_DETECTED",
        "symbol": "Unknown / Logo requires visual icon check",
        "confidence": 0.50
    }


def extract_fssai_license(ocr_text):
    """
    Extracts 14-digit FSSAI license number.
    Format: 14 digits starting typically with 1 or 2 (e.g. 10019022009876).
    """
    matches = re.findall(r"\b([12]\d{13})\b", ocr_text)
    if matches:
        return {
            "license_number": matches[0],
            "is_valid_format": len(matches[0]) == 14,
            "confidence": 0.95
        }
    # Check looser pattern near "FSSAI" keyword
    fssai_keyword = re.search(r"fssai[^\d]{1,15}(\d{10,14})", ocr_text, re.IGNORECASE)
    if fssai_keyword:
        lic = fssai_keyword.group(1)
        return {
            "license_number": lic,
            "is_valid_format": len(lic) == 14,
            "confidence": 0.85
        }
    return {
        "license_number": None,
        "is_valid_format": False,
        "confidence": 0.0
    }


def extract_batch_and_dates(ocr_text):
    """
    Extracts batch/lot number and date markings (MFD, Expiry, Best Before).
    """
    batch_match = re.search(r"\b(?:batch|lot|b\.?\s*no|code)\s*[:\-.]?\s*([A-Za-z0-9\-_/]+)", ocr_text, re.IGNORECASE)
    batch_no = batch_match.group(1) if batch_match else None

    # Date regex
    date_regex = r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b|\b[A-Za-z]{3,9}\s*\d{2,4}\b"

    mfd_match = re.search(r"\b(?:mfd|mfg|manufactured|pkd|packed)\s*[:\-.]?\s*(" + date_regex + ")", ocr_text, re.IGNORECASE)
    mfd = mfd_match.group(1) if mfd_match else None

    exp_match = re.search(r"\b(?:expiry|exp|use\s*by)\s*[:\-.]?\s*(" + date_regex + ")", ocr_text, re.IGNORECASE)
    expiry = exp_match.group(1) if exp_match else None

    best_before_match = re.search(r"\bbest\s*before\s*[:\-.]?\s*([^\n.;]+)", ocr_text, re.IGNORECASE)
    best_before = best_before_match.group(1).strip() if best_before_match else None

    return {
        "batch_number": batch_no,
        "manufacturing_date": mfd,
        "expiry_date": expiry,
        "best_before": best_before
    }


def extract_storage_and_warnings(ocr_text):
    """
    Extracts storage conditions and statutory warnings.
    """
    storage = None
    storage_match = re.search(r"(?:storage(?:\s*instructions)?|store\s*in)\s*[:\-]?\s*([^\n;.]+)", ocr_text, re.IGNORECASE)
    if storage_match:
        storage = storage_match.group(0).strip()

    warnings = []
    if re.search(r"\bcontains\s+artificial\s+sweetener\b", ocr_text, re.IGNORECASE):
        warnings.append("Contains Artificial Sweetener declaration required under FSSAI.")
    if re.search(r"\bnot\s+recommended\s+for\s+children\b", ocr_text, re.IGNORECASE):
        warnings.append("Precautionary warning: Not recommended for children.")

    return {
        "storage_instructions": storage,
        "warnings": warnings
    }


def parse_food_label_document(ocr_lines, image_quality_score=0.9):
    """
    Orchestrates the entire packaging document parsing into a structured Product entity.
    """
    lines_text = [l["text"] if isinstance(l, dict) else str(l) for l in ocr_lines]
    combined_text = "\n".join(lines_text)

    # 1. Ingredients section identification
    ing_text = ""
    ing_start = False
    for line in lines_text:
        if re.search(r"\b(?:ingredients?)\s*[:\-]", line, re.IGNORECASE):
            ing_start = True
        if ing_start:
            ing_text += " " + line
            if re.search(r"\b(?:nutrition|mrp|net\s*wt|mfd)\b", line, re.IGNORECASE) and len(ing_text) > 40:
                break

    if not ing_text:
        # Fallback to lines mentioning common food ingredients
        ing_text = combined_text

    parsed_ingredients = parse_ingredients_declaration(ing_text)

    # 2. Explicit allergen declaration identification
    allergen_match = re.search(r"(?:allergen\s*(?:advice|information|warning)|contains)\s*[:\-]?\s*([^\n;.]+)", combined_text, re.IGNORECASE)
    explicit_allergen_str = allergen_match.group(0) if allergen_match else ""

    parsed_allergens = evaluate_allergens(
        ing_text,
        explicit_allergen_str,
        is_label_readable=(image_quality_score >= 0.5)
    )

    # 3. Nutrition table parsing
    parsed_nutrition = parse_nutrition_table(ocr_lines)

    # 4. Veg / Non-Veg detection
    veg_status = detect_veg_nonveg(combined_text)

    # 5. FSSAI License Number
    fssai_info = extract_fssai_license(combined_text)

    # 6. Batch & Date markings
    dates_info = extract_batch_and_dates(combined_text)

    # 7. Net Quantity & MRP
    mrp_match = re.search(
        r"(?:mrp|m\.r\.p\.?|maximum\s+retail\s+price)\s*[:\-()]*\s*(?:rs\.?|inr|₹)?\s*([0-9]+(?:\.[0-9]{1,2})?)",
        combined_text, re.IGNORECASE
    )
    mrp_val = f"₹{mrp_match.group(1)}" if mrp_match else None

    qty_match = re.search(r"(\d+(?:\.\d+)?)\s*(kg|g|mg|l|ml|pcs)", combined_text, re.IGNORECASE)
    net_qty = f"{qty_match.group(1)} {qty_match.group(2).lower()}" if qty_match else None

    # 8. Manufacturer details
    mfr_match = re.search(
        r"(?:manufactured(?:\s*(?:&|and)\s*packed)?\s*by|mfg\s*(?:&|and)?\s*pkd\s*by|packed\s*by|marketed\s*by)\s*[:\-]?\s*([^\n]+)",
        combined_text, re.IGNORECASE
    )
    manufacturer = mfr_match.group(0).strip() if mfr_match else None

    # 9. Storage & Warnings
    storage_info = extract_storage_and_warnings(combined_text)

    # 10. Product Name heuristic: combine top 1-2 lines that are not statutory declarations
    product_name = "Pre-Packaged Food Product"
    skip_keywords = re.compile(
        r"\b(?:mrp|ingredients|nutrition|fssai|batch|net|quantity|maximum|retail|price|"
        r"mfd|best|before|manufactured|address|consumer|care|packed|marketed|inclusive)\b",
        re.IGNORECASE
    )
    name_parts = []
    for line in lines_text[:5]:
        cleaned = line.strip()
        if len(cleaned) > 3 and not skip_keywords.search(cleaned):
            name_parts.append(cleaned)
        if len(name_parts) >= 2:
            break
    if name_parts:
        product_name = " ".join(name_parts)

    return {
        "product_name": product_name,
        "category": "Pre-Packaged Food",
        "ingredients": parsed_ingredients,
        "allergens": parsed_allergens,
        "nutrition": parsed_nutrition,
        "veg_non_veg": veg_status,
        "fssai_license": fssai_info,
        "batch_number": dates_info["batch_number"],
        "manufacturing_date": dates_info["manufacturing_date"],
        "expiry_date": dates_info["expiry_date"],
        "best_before": dates_info["best_before"],
        "net_quantity": net_qty,
        "mrp": mrp_val,
        "manufacturer": manufacturer,
        "storage_instructions": storage_info["storage_instructions"],
        "warnings": storage_info["warnings"],
        "full_text": combined_text,
        "raw_ocr_summary": {
            "total_lines": len(ocr_lines),
            "combined_length": len(combined_text)
        }
    }
