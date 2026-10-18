# extraction.py
"""
Field Extraction Engine for Mitra Metrology.

v2 changes:
  - Context-aware date extraction: manufacturing_date, expiry_date, best_before kept separate.
  - extract_dates_with_context(): classifies each date by surrounding label keywords.
  - classify_field_status(): returns one of 7 field statuses.
  - select_best_field_candidate(): field-level selection across OCR variants.
  - All existing extract_* functions and extract_fields() are UNCHANGED.
"""

import re
from typing import Any, Dict, List, Optional

# ── Field status constants ──────────────────────────────────────────────────
FIELD_STATUS_VALID           = "VALID"
FIELD_STATUS_DETECTED        = "DETECTED"         # Canonical synonym for VALID
FIELD_STATUS_LOW_CONFIDENCE  = "LOW_CONFIDENCE"
FIELD_STATUS_UNREADABLE      = "UNREADABLE"
FIELD_STATUS_NOT_DETECTED    = "NOT_DETECTED"
FIELD_STATUS_MISSING         = "MISSING"         # set when absent
FIELD_STATUS_VERIFIED_ABSENT = "VERIFIED_ABSENT" # when verified physically absent after review
FIELD_STATUS_NOT_APPLICABLE  = "NOT_APPLICABLE"
FIELD_STATUS_USER_CORRECTED  = "USER_CORRECTED"
FIELD_STATUS_CONFIRMED       = "CONFIRMED"
FIELD_STATUS_REVIEW_REQUIRED = "REVIEW_REQUIRED"

FIELD_NAMES = [
    "product_name",
    "mrp",
    "net_quantity",
    "manufacturer",
    "manufacturer_address",
    "manufacturing_date",
    "expiry_date",
    "best_before",
    "consumer_care",
    "fssai",
]

# ── Date keyword context maps ──────────────────────────────────────────────
_MFG_KEYWORDS = re.compile(
    r"\b(mfg|mfd|mfg\.?|mfd\.?|manufactured|manufacturing|pkd|packed on|date of manufacture|dom)\b",
    re.IGNORECASE
)

_EXP_KEYWORDS = re.compile(
    r"\b(exp|expiry|expiration|use by|use before|exp\.?date|exp\s*date|consume by)\b",
    re.IGNORECASE
)

_BB_KEYWORDS = re.compile(
    r"\b(best before|best\s*bef|bbd)\b",
    re.IGNORECASE
)

# All recognized date formats
_DATE_PATTERNS = [
    # DD/MM/YYYY   DD-MM-YYYY   DD.MM.YYYY
    re.compile(r"\b(\d{1,2})[/\-\.](\d{1,2})[/\-\.](\d{4})\b"),
    # DD/MM/YY     DD-MM-YY     DD.MM.YY
    re.compile(r"\b(\d{1,2})[/\-\.](\d{1,2})[/\-\.](\d{2})\b"),
    # 15 AUG 2024  15 August 2024  AUG 2024  August 2024
    re.compile(
        r"\b(\d{1,2}\s+)?"
        r"(Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|"
        r"Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)"
        r"\s*[,]?\s*(\d{2,4})\b",
        re.IGNORECASE
    ),
    # MM/YYYY      MM-YYYY      MM.YYYY
    re.compile(r"\b(\d{1,2})[/\-\.](\d{4})\b"),
]


def _try_extract_date(text: str) -> Optional[str]:
    """Returns the first matching date string from text, or None."""
    for pattern in _DATE_PATTERNS:
        m = pattern.search(text)
        if m:
            return m.group(0).strip()
    return None


def _best_before_text(text: str) -> Optional[str]:
    """
    For best-before text like "BEST BEFORE 6 MONTHS FROM PACKAGING",
    returns the period/duration text after the keyword.
    """
    m = re.search(r"(?:best\s+before|bbd|use\s+before)?\s*[:\-]?\s*(.+)", text, re.IGNORECASE)
    if m:
        val = m.group(1).strip()
        if val:
            return val
    if re.search(r"\d+\s*(?:month|months|days|years|year)", text, re.IGNORECASE):
        return text.strip()
    return None


def extract_dates_with_context(lines: List[dict]) -> Dict[str, Optional[dict]]:
    """
    Context-aware date extraction.

    Processes grouped OCR lines (each with "text", "confidence", "bbox").
    Returns dict with keys:
      manufacturing_date, expiry_date, best_before
    Each value is either None or:
      {
        "value":          str,    # extracted date or period text
        "ocr_text":       str,    # full source line text
        "ocr_confidence": float,
        "bbox":           dict | None,
        "date_format":    str,    # e.g. "DD/MM/YYYY" or "text_period"
      }

    Rules:
    - Disambiguates manufacturing, expiry, and best before dates even if on the same line or in reversed order.
    - Never merges the three into one field.
    - Uses inline keyword segments first, falling back to adjacent lines if a line only has a date.
    """
    result = {
        "manufacturing_date": None,
        "expiry_date":        None,
        "best_before":        None,
    }

    def _make_entry(text, date_val, confidence, bbox, fmt):
        return {
            "value":          date_val,
            "ocr_text":       text,
            "ocr_confidence": confidence,
            "bbox":           bbox,
            "date_format":    fmt,
        }

    def _fmt(text, date_val):
        if not date_val:
            return "unknown"
        if re.search(r"\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{4}", date_val):
            return "DD/MM/YYYY"
        if re.search(r"\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2}$", date_val):
            return "DD/MM/YY"
        if re.search(r"\d{1,2}[/\-\.]\d{4}", date_val):
            return "MM/YYYY"
        if re.search(r"(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)", date_val, re.IGNORECASE):
            return "text_month"
        if re.search(r"\d+\s*(month|months|days|years)", date_val, re.IGNORECASE):
            return "text_period"
        return "other"

    # Pass 1: Parse lines with inline keywords (supporting multiple dates per line)
    for idx, line in enumerate(lines):
        text = line.get("text", "")
        conf = line.get("confidence", 0.0)
        bbox = line.get("bbox")

        matches = []
        for m in _BB_KEYWORDS.finditer(text):
            matches.append((m.start(), m.end(), "bb", m.group(0)))
        for m in _MFG_KEYWORDS.finditer(text):
            matches.append((m.start(), m.end(), "mfg", m.group(0)))
        for m in _EXP_KEYWORDS.finditer(text):
            # Avoid matching if within bb match
            if not any(b_start <= m.start() and m.end() <= b_end for b_start, b_end, cat, _ in matches if cat == "bb"):
                matches.append((m.start(), m.end(), "exp", m.group(0)))

        matches.sort(key=lambda x: x[0])

        if matches:
            for i, (m_start, m_end, cat, kw) in enumerate(matches):
                seg_end = matches[i + 1][0] if i + 1 < len(matches) else len(text)
                segment = text[m_end:seg_end].strip(" :-")

                if cat == "bb" and result["best_before"] is None:
                    d = _try_extract_date(segment)
                    if d:
                        result["best_before"] = _make_entry(text, d, conf, bbox, _fmt(text, d))
                    else:
                        bb_t = _best_before_text(segment) or _best_before_text(text)
                        if bb_t:
                            result["best_before"] = _make_entry(text, bb_t, conf, bbox, "text_period")
                elif cat == "mfg" and result["manufacturing_date"] is None:
                    d = _try_extract_date(segment)
                    if d:
                        result["manufacturing_date"] = _make_entry(text, d, conf, bbox, _fmt(text, d))
                elif cat == "exp" and result["expiry_date"] is None:
                    d = _try_extract_date(segment)
                    if d:
                        result["expiry_date"] = _make_entry(text, d, conf, bbox, _fmt(text, d))

    # Pass 2: Fallback for lines without inline keywords (e.g. date on line immediately below keyword)
    for idx, line in enumerate(lines):
        text = line.get("text", "")
        conf = line.get("confidence", 0.0)
        bbox = line.get("bbox")
        d = _try_extract_date(text)
        if not d:
            continue
        assigned_vals = [v["value"] for v in result.values() if v is not None]
        if d in assigned_vals:
            continue

        prev_text = lines[idx - 1].get("text", "") if idx > 0 else ""
        if _MFG_KEYWORDS.search(prev_text) and result["manufacturing_date"] is None:
            result["manufacturing_date"] = _make_entry(text, d, conf, bbox, _fmt(text, d))
        elif _EXP_KEYWORDS.search(prev_text) and result["expiry_date"] is None:
            result["expiry_date"] = _make_entry(text, d, conf, bbox, _fmt(text, d))
        elif _BB_KEYWORDS.search(prev_text) and result["best_before"] is None:
            result["best_before"] = _make_entry(text, d, conf, bbox, _fmt(text, d))

    return result


# ── Field status classification ────────────────────────────────────────────
def classify_field_status(
    field_name: str,
    value: Any,
    ocr_confidence: float,
    quality_score: float,
    quality_tier: str = "GOOD"
) -> str:
    """
    Classify a single extracted field into one of 7 statuses.

    VALID           — extracted, confidence >= 0.65, quality OK
    LOW_CONFIDENCE  — extracted, confidence < 0.65
    UNREADABLE      — not extracted AND quality_tier is VERY_POOR (OCR physically blocked)
    NOT_DETECTED    — not extracted AND quality is acceptable (label may genuinely lack it,
                      but OCR failure is NOT treated as proof it is missing)
    MISSING         — ONLY set by the rule engine after deterministic analysis
    NOT_APPLICABLE  — rule doesn't apply to this product type
    REVIEW_REQUIRED — borderline case requiring human check

    Critical rule: OCR failure alone → NOT_DETECTED or UNREADABLE, NEVER MISSING.
    """
    has_value = value is not None and str(value).strip() != ""

    if not has_value:
        if quality_tier == "VERY_POOR":
            return FIELD_STATUS_UNREADABLE
        return FIELD_STATUS_NOT_DETECTED

    # Value was extracted
    if ocr_confidence < 0.50:
        return FIELD_STATUS_LOW_CONFIDENCE
    if ocr_confidence < 0.65:
        return FIELD_STATUS_LOW_CONFIDENCE
    return FIELD_STATUS_VALID


# ── Field-level candidate selection across OCR variants ───────────────────
def select_best_field_candidate(
    field_name: str,
    variant_results: dict,
    quality_tier: str = "GOOD"
) -> dict:
    """
    Selects the best extracted value for a single field across all OCR variants.

    variant_results is the "variants" sub-dict from run_ocr_multi_variant():
    {
        "clahe":    { "lines": [...], "text": str, ... },
        "otsu":     { ... },
        "sharp":    { ... },
        "inverted": { ... },
    }

    Returns:
    {
        "value":          Any,
        "ocr_text":       str,
        "ocr_confidence": float,
        "source_variant": str,
        "bbox":           dict | None,
        "status":         str,         # from classify_field_status()
        "candidates":     list,        # all found values (for audit)
    }
    """
    from ai_engine.extraction import (
        extract_mrp, extract_net_quantity, extract_manufacturing_date,
        extract_expiry, extract_fssai, extract_consumer_care,
        extract_manufacturer, extract_manufacturer_address, extract_product_name,
        extract_dates_with_context
    )

    # Map field_name → extraction function
    extractor_map = {
        "mrp":                  extract_mrp,
        "net_quantity":         extract_net_quantity,
        "manufacturing_date":   None,  # handled via extract_dates_with_context
        "expiry_date":          None,
        "best_before":          None,
        "fssai":                extract_fssai,
        "consumer_care":        extract_consumer_care,
        "manufacturer":         extract_manufacturer,
        "manufacturer_address": extract_manufacturer_address,
        "product_name":         extract_product_name,
    }

    candidates = []

    for variant_name, vdata in variant_results.items():
        lines = vdata.get("lines", [])

        if field_name in ("manufacturing_date", "expiry_date", "best_before"):
            dates = extract_dates_with_context(lines)
            extracted = dates.get(field_name)
            if extracted:
                candidates.append({
                    "value":          extracted["value"],
                    "ocr_text":       extracted["ocr_text"],
                    "ocr_confidence": extracted["ocr_confidence"],
                    "source_variant": variant_name,
                    "bbox":           extracted.get("bbox"),
                    "date_format":    extracted.get("date_format", ""),
                })
        else:
            fn = extractor_map.get(field_name)
            if fn is None:
                continue
            extracted = fn(lines)
            if extracted:
                candidates.append({
                    "value":          extracted.get("value"),
                    "ocr_text":       extracted.get("ocr_text", ""),
                    "ocr_confidence": extracted.get("ocr_confidence", 0.0),
                    "source_variant": variant_name,
                    "bbox":           extracted.get("bbox"),
                })

    if not candidates:
        return {
            "value":          None,
            "ocr_text":       "",
            "ocr_confidence": 0.0,
            "source_variant": None,
            "bbox":           None,
            "status":         classify_field_status(field_name, None, 0.0, 0.0, quality_tier),
            "candidates":     [],
        }

    # ── Scoring each candidate ──────────────────────────────────────────────
    def score_candidate(c: dict) -> float:
        s = c["ocr_confidence"] * 0.60
        val = str(c.get("value", "")).strip()

        # Format validity bonus
        if field_name == "mrp":
            try:
                v = float(re.sub(r"[^\d.]", "", val))
                if 0 < v < 100000:
                    s += 0.25
            except Exception:
                pass
        elif field_name == "net_quantity":
            if re.search(r"\d+(\.\d+)?\s*(kg|g|ml|l|pcs|litre|mg)", val, re.IGNORECASE):
                s += 0.25
        elif field_name == "fssai":
            clean = re.sub(r"\D", "", val)
            if len(clean) == 14:
                s += 0.30
            elif len(clean) >= 10:
                s += 0.10
        elif field_name in ("manufacturing_date", "expiry_date", "best_before"):
            if re.search(r"\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{4}", val):
                s += 0.25
            elif re.search(r"\d{1,2}[/\-\.]\d{4}", val):
                s += 0.15
            elif re.search(r"(month|months|days|years)", val, re.IGNORECASE):
                s += 0.10
        elif field_name in ("manufacturer", "product_name"):
            if len(val) > 5:
                s += 0.10
            if len(val) > 15:
                s += 0.05

        # Agreement bonus: same value appears in multiple variants
        same_count = sum(
            1 for other in candidates
            if other is not c and str(other.get("value", "")).strip().lower() == val.lower()
        )
        s += min(same_count * 0.10, 0.20)

        return min(s, 1.0)

    best = max(candidates, key=score_candidate)
    best_conf = best["ocr_confidence"]

    return {
        "value":          best["value"],
        "ocr_text":       best["ocr_text"],
        "ocr_confidence": best_conf,
        "source_variant": best["source_variant"],
        "bbox":           best.get("bbox"),
        "status":         classify_field_status(field_name, best["value"], best_conf, 0.0, quality_tier),
        "candidates":     candidates,
    }


def extract_best_fields_from_variants(variant_results: dict, quality_tier: str = "GOOD") -> dict:
    """
    Run field-level candidate selection for all known fields.

    Returns:
    {
        "mrp":                  { value, ocr_text, ocr_confidence, source_variant, bbox, status },
        "net_quantity":         { ... },
        "manufacturing_date":   { ... },
        "expiry_date":          { ... },
        "best_before":          { ... },
        "fssai":                { ... },
        "consumer_care":        { ... },
        "manufacturer":         { ... },
        "manufacturer_address": { ... },
        "product_name":         { ... },
    }
    """
    fields_to_extract = [
        "mrp", "net_quantity",
        "manufacturing_date", "expiry_date", "best_before",
        "fssai", "consumer_care",
        "manufacturer", "manufacturer_address",
        "product_name",
    ]

    return {
        field: select_best_field_candidate(field, variant_results, quality_tier)
        for field in fields_to_extract
    }


# ══════════════════════════════════════════════════════════════════════════════
#  All v1 functions UNCHANGED below — backward compatibility
# ══════════════════════════════════════════════════════════════════════════════

def clean_text(text):
    if not isinstance(text, str):
        text = str(text or "")
    text = text.replace("|", "I")
    # Normalize spaced decimals and OCR comma decimals (e.g. 450 . 00 or 450,00 -> 450.00)
    text = re.sub(r"\b(\d+)\s*[.,]\s*(\d{1,2})\b", r"\1.\2", text)
    return re.sub(r"\s+", " ", text).strip()


def normalize_mrp(text):
    text = clean_text(text)
    match = re.search(
        r"(?:MAXIMUM\s*RETAIL\s*PRICE|MRP|M\.R\.P\.?)[^\d]*(?:RS\.?|INR|PS\.?|₹)?\s*₹?\s*([0-9]+(?:\.[0-9]{1,2})?)",
        text, re.IGNORECASE
    )
    if not match:
        match = re.search(r"(?:RS\.?|INR|₹)\s*([0-9]+(?:\.[0-9]{1,2})?)", text, re.IGNORECASE)
    if not match:
        return None
    return f"₹{match.group(1)}"


def extract_mrp(lines):
    patterns = [r"\bMRP\b", r"\bM\.R\.P\b", r"\bMAXIMUM RETAIL PRICE\b"]
    for line in lines:
        text = line["text"]
        if any(re.search(p, text, re.IGNORECASE) for p in patterns):
            value = normalize_mrp(text)
            if value:
                return {"ocr_text": text, "value": value, "bbox": line["bbox"], "ocr_confidence": line["confidence"]}
    return None


def normalize_quantity(text):
    text = clean_text(text)
    match = re.search(
        r"(\d+(?:\.\d+)?)\s*(kilograms?|kg|gms?|g|mg|litres?|liters?|ltr|l|ml|cm|pcs|pieces?)\b",
        text, re.IGNORECASE
    )
    if not match:
        return None
    value = match.group(1)
    unit = match.group(2).lower()
    unit_map = {
        "kilogram": "kg", "kilograms": "kg", "kg": "kg",
        "g": "g", "gm": "g", "gms": "g", "mg": "mg",
        "l": "L", "ltr": "L", "litre": "L", "litres": "L", "liter": "L", "liters": "L",
        "ml": "ml", "pcs": "pcs", "piece": "pcs", "pieces": "pcs", "cm": "cm"
    }
    return f"{value} {unit_map.get(unit, unit)}"


def extract_net_quantity(lines):
    keywords = [
        "NET QTY", "NET QUANTITY", "NET WT", "NET WEIGHT", "NET CONTENT",
        "NET VOL", "NET VOLUME", "CONTENTS", "CONTENT", "NET:", "QUANTITY:", "QTY:"
    ]
    for line in lines:
        text = line["text"]
        upper = text.upper()
        if any(k in upper for k in keywords):
            value = normalize_quantity(text)
            if value:
                return {"ocr_text": text, "value": value, "bbox": line["bbox"], "ocr_confidence": line["confidence"]}
    # Secondary pass: if line contains quantity keyword
    for line in lines:
        text = line["text"]
        if "QUANTITY" in text.upper() or "QTY" in text.upper():
            value = normalize_quantity(text)
            if value:
                return {"ocr_text": text, "value": value, "bbox": line["bbox"], "ocr_confidence": line["confidence"]}
    return None


def extract_date(text):
    patterns = [
        # DD/MM/YYYY, DD-MM-YYYY, DD.MM.YYYY
        r"\b\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4}\b",
        # 15 Aug 2024, 15 August 2024
        r"\b\d{1,2}\s*[A-Za-z]{3,9}\s*\d{2,4}\b",
        # Aug 2024, August 2024
        r"\b[A-Za-z]{3,9}\s*\d{4}\b",
        # MM/YYYY, MM-YYYY, MM.YYYY
        r"\b\d{1,2}[/\-\.]\d{4}\b",
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(0)
    return None


def extract_manufacturing_date(lines):
    keywords = ["MFG", "MFD", "MANUFACTURED", "MANUFACTURING DATE"]
    for line in lines:
        text = line["text"]
        if any(k in text.upper() for k in keywords):
            date = extract_date(text)
            if date:
                return {"ocr_text": text, "value": date, "bbox": line["bbox"], "ocr_confidence": line["confidence"]}
    return None


def extract_expiry(lines):
    keywords = ["EXP", "EXPIRY", "EXP DATE", "BEST BEFORE", "USE BY"]
    for line in lines:
        text = line["text"]
        if any(k in text.upper() for k in keywords):
            date = extract_date(text)
            if date:
                return {"ocr_text": text, "value": date, "bbox": line["bbox"], "ocr_confidence": line["confidence"]}
            match = re.search(r"BEST BEFORE\s*[:\-]?\s*(.*)", text, re.IGNORECASE)
            if match:
                value = match.group(1).strip()
                if value:
                    return {"ocr_text": text, "value": value, "bbox": line["bbox"], "ocr_confidence": line["confidence"]}
    return None


def extract_fssai(lines):
    fssai_keywords = ["FSSAI", "FSSAT", "LIC. NO", "LIC NO", "LICENSE NO", "LICENCE NO", "CENTRAL LICENCE", "STATE LICENCE"]
    for line in lines:
        text = line["text"]
        upper = text.upper()
        if any(k in upper for k in fssai_keywords):
            match = re.search(r"\b\d{14}\b", text) or re.search(r"\b\d{10,14}\b", text)
            if match:
                return {"ocr_text": text, "value": match.group(0), "bbox": line["bbox"], "ocr_confidence": line["confidence"]}
    return None


def extract_consumer_care(lines):
    keywords = ["CONSUMER CARE", "CUSTOMER CARE", "CONTACT", "HELPLINE", "TOLL FREE", "FEEDBACK"]
    matched_lines = []
    for line in lines:
        text = line["text"]
        upper = text.upper()
        if any(k in upper for k in keywords):
            matched_lines.append(line)
        elif "@" in text and any(domain in text.lower() for domain in ["care", "support", "feedback", "pepsico", "mitra"]):
            matched_lines.append(line)

    if not matched_lines:
        return None

    # Search for phone and email across matched lines
    combined_context = " ".join(l["text"] for l in matched_lines)
    phone_match = re.search(r"(?:1800[-\s]?\d{2,3}[-\s]?\d{3,4}|\b\d{10}\b|\b\d{3,5}[-\s]\d{6,8}\b)", combined_context)
    email_match = re.search(r"[\w\.-]+@[\w\.-]+\.\w+", combined_context)

    parts = []
    if phone_match:
        parts.append(f"Phone: {phone_match.group(0).strip()}")
    if email_match:
        parts.append(f"Email: {email_match.group(0).strip()}")

    primary_line = matched_lines[0]
    if parts:
        clean_val = " | ".join(parts)
    else:
        clean_val = re.sub(r"\s+", " ", primary_line["text"]).strip()
        if len(clean_val) > 80:
            clean_val = clean_val[:77] + "..."

    return {
        "ocr_text": primary_line["text"],
        "value": clean_val,
        "bbox": primary_line["bbox"],
        "ocr_confidence": primary_line["confidence"]
    }


def extract_manufacturer(lines):
    keywords = ["MANUFACTURED BY", "MANUFACTURER", "MFG BY", "MARKETED BY", "MKT. BY", "MKT BY", "MFD. BY", "MFD BY", "PACKED BY", "IMPORTED BY"]
    for index, line in enumerate(lines):
        text = line["text"]
        upper = text.upper()
        if any(k in upper for k in keywords):
            parts = re.split(r"[:\-]", text, maxsplit=1)
            if len(parts) == 2 and len(parts[1].strip()) > 3:
                value = parts[1].strip()
            elif index + 1 < len(lines):
                value = lines[index + 1]["text"].strip()
            else:
                value = text.strip()
            # Clean noise like trailing @ web addresses or leading punctuation
            value = re.sub(r"[@|].*", "", value).strip(" :-")
            if len(value) > 2:
                return {"ocr_text": text, "value": value, "bbox": line["bbox"], "ocr_confidence": line["confidence"]}
    return None


def extract_manufacturer_address(lines):
    keywords = [
        "ADDRESS", "ADD:", "REGISTERED OFFICE", "REGD OFFICE",
        "MFD AT", "MFG AT", "PACKED AT", "FACTORY", "PLOT NO", "INDUSTRIAL AREA", "UNIT:"
    ]
    for line in lines:
        text = line["text"]
        upper = text.upper()
        if any(k in upper for k in keywords):
            parts = re.split(r"[:\-]", text, maxsplit=1)
            if len(parts) == 2 and len(parts[1].strip()) > 3:
                value = parts[1].strip()
            else:
                value = text.strip()
            value = value.strip(" :-")
            if len(value) > 3:
                return {"ocr_text": text, "value": value, "bbox": line["bbox"], "ocr_confidence": line["confidence"]}
    return None


def extract_product_name(lines):
    ignore_words = [
        "MRP", "NET", "QUANTITY", "MANUFACTURED", "MANUFACTURER", "MKT. BY", "MFD. BY",
        "FSSAI", "BEST BEFORE", "EXPIRY", "CONSUMER", "CUSTOMER", "ADDRESS", "INGREDIENTS",
        "NUTRITIONAL", "NUTRITION", "VALUES", "APPROX"
    ]
    for line in lines[:8]:
        text = line["text"].strip()
        if len(text) < 3:
            continue
        upper = text.upper()
        if any(w in upper for w in ignore_words):
            continue
        if re.search(r"\d{1,2}[/-]\d{1,2}[/-]\d{2,4}", text):
            continue
        # Strip brackets, quotes, special chars
        cleaned = re.sub(r"^[\(\[\{\"\':\s\-_=]+|[\)\]\}\"\':\s\-_=]+$", "", text).strip()
        if len(cleaned) < 2:
            continue
        if cleaned.lower() == "lays":
            cleaned = "Lay's"
        elif cleaned.islower():
            cleaned = cleaned.title()
        return {"ocr_text": text, "value": cleaned, "bbox": line["bbox"], "ocr_confidence": line["confidence"]}
    return None


def extract_fields(text):
    """
    Flat-text field extraction. UNCHANGED from v1.
    """
    if isinstance(text, list):
        text = "\n".join(item.get("text", "") if isinstance(item, dict) else str(item) for item in text)
    elif not isinstance(text, str):
        text = str(text or "")

    fields = {}

    mrp = re.search(r"(?:MRP|M\.R\.P)[^\d]*(?:Rs\.?|₹)?\s*(\d+(?:\.\d+)?)", text, re.IGNORECASE)
    if mrp:
        fields["mrp"] = float(mrp.group(1))

    quantity = re.search(
        r"(?:Net\s*Quantity|Net\s*Wt\.?|Net)[^\d]*(\d+(?:\.\d+)?)\s*(kg|g|ml|l)",
        text, re.IGNORECASE
    )
    if quantity:
        fields["net_quantity"] = {"value": float(quantity.group(1)), "unit": quantity.group(2).lower()}

    mfd = re.search(
        r"(?:Mfd|Manufactured|Mfg)[^\d]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
        text, re.IGNORECASE
    )
    if mfd:
        fields["manufacturing_date"] = mfd.group(1)

    best_before = re.search(r"(?:Best\s*Before|Use\s*Before)[:\s-]*(.{0,50})", text, re.IGNORECASE)
    if best_before:
        value = best_before.group(1).strip()
        if value:
            fields["best_before"] = value

    fssai = re.search(r"(?:FSSAI|LIC(?:ENSE)?)[^\d]*(\d{10,15})", text, re.IGNORECASE)
    if fssai:
        fields["fssai"] = fssai.group(1)

    manufacturer = re.search(
        r"(?:Manufactured\s*By|Manufactured\s*&\s*Marketed\s*By)\s*[:\-]?\s*(.+)",
        text, re.IGNORECASE
    )
    if manufacturer:
        fields["manufacturer"] = manufacturer.group(1).strip()

    address = re.search(r"(?:Address|Mfg\.?\s*Address)\s*[:\-]?\s*(.+)", text, re.IGNORECASE)
    if address:
        fields["address"] = address.group(1).strip()

    consumer = re.search(r"(?:Consumer\s*Care|Customer\s*Care)\s*[:\-]?\s*(.+)", text, re.IGNORECASE)
    if consumer:
        fields["consumer_care"] = consumer.group(1).strip()

    return fields