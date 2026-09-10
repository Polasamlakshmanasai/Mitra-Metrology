# extraction.py

import re


FIELD_NAMES = [
    "product_name",
    "mrp",
    "net_quantity",
    "manufacturer",
    "manufacturer_address",
    "manufacturing_date",
    "expiry_best_before",
    "consumer_care",
    "fssai"
]


def clean_text(text):
    """
    Basic OCR cleanup.
    """

    text = text.replace("|", "I")
    text = text.replace("₹", "₹")

    return re.sub(
        r"\s+",
        " ",
        text
    ).strip()


def normalize_mrp(text):
    """
    Normalize MRP text.
    """

    text = clean_text(text)

    match = re.search(
        r"(?:MRP|M\.R\.P\.?)\s*[:\-]?\s*(?:RS\.?|INR)?\s*₹?\s*([0-9]+(?:\.[0-9]{1,2})?)",
        text,
        re.IGNORECASE
    )

    if not match:
        return None

    amount = match.group(1)

    return f"₹{amount}"


def extract_mrp(lines):

    patterns = [
        r"\bMRP\b",
        r"\bM\.R\.P\b",
        r"\bMAXIMUM RETAIL PRICE\b"
    ]

    for line in lines:

        text = line["text"]

        if any(
            re.search(pattern, text, re.IGNORECASE)
            for pattern in patterns
        ):

            value = normalize_mrp(text)

            if value:
                return {
                    "ocr_text": text,
                    "value": value,
                    "bbox": line["bbox"],
                    "ocr_confidence": line["confidence"]
                }

    return None


def normalize_quantity(text):

    text = clean_text(text)

    match = re.search(
        r"(\d+(?:\.\d+)?)\s*(kg|g|mg|l|ml|litre|liter|ltr|cm|pcs|piece)",
        text,
        re.IGNORECASE
    )

    if not match:
        return None

    value = match.group(1)
    unit = match.group(2).lower()

    unit_map = {
        "kilogram": "kg",
        "kg": "kg",
        "g": "g",
        "mg": "mg",
        "l": "L",
        "ltr": "L",
        "litre": "L",
        "liter": "L",
        "ml": "ml",
        "pcs": "pcs",
        "piece": "pcs"
    }

    unit = unit_map.get(unit, unit)

    return f"{value} {unit}"


def extract_net_quantity(lines):

    keywords = [
        "NET QTY",
        "NET QUANTITY",
        "NET WT",
        "NET WEIGHT",
        "CONTENTS"
    ]

    for line in lines:

        text = line["text"]

        if any(
            keyword in text.upper()
            for keyword in keywords
        ):

            value = normalize_quantity(text)

            if value:

                return {
                    "ocr_text": text,
                    "value": value,
                    "bbox": line["bbox"],
                    "ocr_confidence": line["confidence"]
                }

    return None


def extract_date(text):

    patterns = [
        r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b",
        r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2}\b",
        r"\b\d{1,2}\s*[A-Za-z]{3,9}\s*\d{2,4}\b",
        r"\b[A-Za-z]{3,9}\s*\d{4}\b"
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            text
        )

        if match:
            return match.group(0)

    return None


def extract_manufacturing_date(lines):

    keywords = [
        "MFG",
        "MFD",
        "MANUFACTURED",
        "MANUFACTURING DATE"
    ]

    for line in lines:

        text = line["text"]

        if any(
            keyword in text.upper()
            for keyword in keywords
        ):

            date = extract_date(text)

            if date:

                return {
                    "ocr_text": text,
                    "value": date,
                    "bbox": line["bbox"],
                    "ocr_confidence": line["confidence"]
                }

    return None


def extract_expiry(lines):

    keywords = [
        "EXP",
        "EXPIRY",
        "EXP DATE",
        "BEST BEFORE",
        "USE BY"
    ]

    for line in lines:

        text = line["text"]

        if any(
            keyword in text.upper()
            for keyword in keywords
        ):

            date = extract_date(text)

            if date:

                return {
                    "ocr_text": text,
                    "value": date,
                    "bbox": line["bbox"],
                    "ocr_confidence": line["confidence"]
                }

            # Sometimes "Best Before 12 Months"
            # doesn't contain a date.
            match = re.search(
                r"BEST BEFORE\s*[:\-]?\s*(.*)",
                text,
                re.IGNORECASE
            )

            if match:

                value = match.group(1).strip()

                if value:

                    return {
                        "ocr_text": text,
                        "value": value,
                        "bbox": line["bbox"],
                        "ocr_confidence": line["confidence"]
                    }

    return None


def extract_fssai(lines):

    for line in lines:

        text = line["text"]

        if "FSSAI" in text.upper():

            match = re.search(
                r"\b\d{10,14}\b",
                text
            )

            if match:

                return {
                    "ocr_text": text,
                    "value": match.group(0),
                    "bbox": line["bbox"],
                    "ocr_confidence": line["confidence"]
                }

    return None


def extract_consumer_care(lines):

    keywords = [
        "CONSUMER CARE",
        "CUSTOMER CARE",
        "CONTACT",
        "HELPLINE",
        "TOLL FREE"
    ]

    for line in lines:

        text = line["text"]

        if any(
            keyword in text.upper()
            for keyword in keywords
        ):

            return {
                "ocr_text": text,
                "value": text,
                "bbox": line["bbox"],
                "ocr_confidence": line["confidence"]
            }

    return None


def extract_manufacturer(lines):

    keywords = [
        "MANUFACTURED BY",
        "MANUFACTURER",
        "MFG BY",
        "MARKETED BY"
    ]

    for index, line in enumerate(lines):

        text = line["text"]

        if any(
            keyword in text.upper()
            for keyword in keywords
        ):

            # Try text after colon first.
            parts = re.split(
                r"[:\-]",
                text,
                maxsplit=1
            )

            if len(parts) == 2 and parts[1].strip():

                value = parts[1].strip()

            elif index + 1 < len(lines):

                value = lines[index + 1]["text"]

            else:

                value = text

            return {
                "ocr_text": text,
                "value": value,
                "bbox": line["bbox"],
                "ocr_confidence": line["confidence"]
            }

    return None


def extract_manufacturer_address(lines):

    keywords = [
        "ADDRESS",
        "ADD:",
        "REGISTERED OFFICE",
        "REGD OFFICE"
    ]

    for line in lines:

        text = line["text"]

        if any(
            keyword in text.upper()
            for keyword in keywords
        ):

            return {
                "ocr_text": text,
                "value": text,
                "bbox": line["bbox"],
                "ocr_confidence": line["confidence"]
            }

    return None


def extract_product_name(lines):

    """
    Heuristic:
    Product name is often near the top of the package.
    We avoid lines that clearly represent other fields.
    """

    ignore_words = [
        "MRP",
        "NET",
        "QUANTITY",
        "MANUFACTURED",
        "MANUFACTURER",
        "FSSAI",
        "BEST BEFORE",
        "EXPIRY",
        "CONSUMER",
        "CUSTOMER",
        "ADDRESS"
    ]

    for line in lines[:8]:

        text = line["text"].strip()

        if len(text) < 3:
            continue

        upper = text.upper()

        if any(
            word in upper
            for word in ignore_words
        ):
            continue

        if re.search(
            r"\d{1,2}[/-]\d{1,2}[/-]\d{2,4}",
            text
        ):
            continue

        return {
            "ocr_text": text,
            "value": text,
            "bbox": line["bbox"],
            "ocr_confidence": line["confidence"]
        }

    return None


def extract_fields(text):
    if isinstance(text, list):
        text = "\n".join(item.get("text", "") if isinstance(item, dict) else str(item) for item in text)
    elif not isinstance(text, str):
        text = str(text or "")

    fields = {}

    # -------------------------
    # MRP
    # -------------------------
    mrp = re.search(
        r"(?:MRP|M\.R\.P)[^\d]*(?:Rs\.?|₹)?\s*(\d+(?:\.\d+)?)",
        text,
        re.IGNORECASE
    )

    if mrp:
        fields["mrp"] = float(mrp.group(1))

    # -------------------------
    # NET QUANTITY
    # -------------------------
    quantity = re.search(
        r"(?:Net\s*Quantity|Net\s*Wt\.?|Net)[^\d]*(\d+(?:\.\d+)?)\s*(kg|g|ml|l)",
        text,
        re.IGNORECASE
    )

    if quantity:
        fields["net_quantity"] = {
            "value": float(quantity.group(1)),
            "unit": quantity.group(2).lower()
        }

    # -------------------------
    # MANUFACTURING DATE
    # -------------------------
    mfd = re.search(
        r"(?:Mfd|Manufactured|Mfg)[^\d]*"
        r"(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
        text,
        re.IGNORECASE
    )

    if mfd:
        fields["manufacturing_date"] = mfd.group(1)

    # -------------------------
    # BEST BEFORE
    # -------------------------
    best_before = re.search(
        r"(?:Best\s*Before|Use\s*Before)"
        r"[:\s-]*(.{0,50})",
        text,
        re.IGNORECASE
    )

    if best_before:
        value = best_before.group(1).strip()
        if value:
            fields["best_before"] = value

    # -------------------------
    # FSSAI
    # -------------------------
    fssai = re.search(
        r"(?:FSSAI|LIC(?:ENSE)?)[^\d]*(\d{10,15})",
        text,
        re.IGNORECASE
    )

    if fssai:
        fields["fssai"] = fssai.group(1)

    # -------------------------
    # MANUFACTURER
    # -------------------------
    manufacturer = re.search(
        r"(?:Manufactured\s*By|Manufactured\s*&\s*Marketed\s*By)"
        r"\s*[:\-]?\s*(.+)",
        text,
        re.IGNORECASE
    )

    if manufacturer:
        fields["manufacturer"] = manufacturer.group(1).strip()

    # -------------------------
    # ADDRESS
    # -------------------------
    address = re.search(
        r"(?:Address|Mfg\.?\s*Address)"
        r"\s*[:\-]?\s*(.+)",
        text,
        re.IGNORECASE
    )

    if address:
        fields["address"] = address.group(1).strip()

    # -------------------------
    # CONSUMER CARE
    # -------------------------
    consumer = re.search(
        r"(?:Consumer\s*Care|Customer\s*Care)"
        r"\s*[:\-]?\s*(.+)",
        text,
        re.IGNORECASE
    )

    if consumer:
        fields["consumer_care"] = consumer.group(1).strip()

    return fields