# ingredient_parser.py
"""
NLP & Food Knowledge Base Ingredient Parser.
Parses complex packaged food ingredient declarations into structured Ingredient entities,
identifying INS numbers, additive classes, QUID percentages, and compound ingredients.
"""

import re
import json
from pathlib import Path

RULES_DIR = Path(__file__).resolve().parent.parent / "rules"
INS_DB_PATH = RULES_DIR / "ins_additives_db.json"

_INS_DB = None

def get_ins_db():
    global _INS_DB
    if _INS_DB is None:
        try:
            with open(INS_DB_PATH, "r", encoding="utf-8") as f:
                _INS_DB = json.load(f)
        except Exception:
            _INS_DB = {"classes": {}, "specific_additives": {}}
    return _INS_DB


def split_ingredients_safely(text):
    """
    Splits comma-delimited ingredients while respecting nested parentheses.
    E.g. "Wheat Flour (55%), Milk Solids (Whey, Butter), Emulsifier (INS 322)"
    -> ["Wheat Flour (55%)", "Milk Solids (Whey, Butter)", "Emulsifier (INS 322)"]
    """
    items = []
    current = []
    depth = 0

    for char in text:
        if char in "([{":
            depth += 1
            current.append(char)
        elif char in ")]}":
            depth = max(0, depth - 1)
            current.append(char)
        elif char in ",;" and depth == 0:
            item = "".join(current).strip()
            if item:
                items.append(item)
            current = []
        else:
            current.append(char)

    if current:
        item = "".join(current).strip()
        if item:
            items.append(item)

    return items


def extract_percentage(text):
    """Extracts QUID percentage, e.g. 'Wheat Flour (55%)' -> 55.0"""
    match = re.search(r"(\d+(?:\.\d+)?)\s*%", text)
    if match:
        try:
            return float(match.group(1))
        except ValueError:
            return None
    return None


def extract_ins_codes(text):
    """Finds all INS or E codes, e.g. INS 500(ii), INS 322, E471"""
    pattern = r"\b(?:INS|E)\s*[-:]?\s*([0-9]{3,4}(?:\([a-z0-9]+\)|[a-z])?)\b"
    matches = re.finditer(pattern, text, re.IGNORECASE)
    ins_codes = []
    for m in matches:
        code = m.group(1).lower()
        ins_codes.append(code)
    return ins_codes


def classify_ingredient_text(raw_text):
    """
    Classifies an individual ingredient snippet into a structured dictionary.
    """
    ins_db = get_ins_db()
    specific_additives = ins_db.get("specific_additives", {})

    percentage = extract_percentage(raw_text)
    ins_codes = extract_ins_codes(raw_text)

    # Clean display name by stripping outer prefix if present
    cleaned_name = re.sub(r"^(?:ingredients?|contains)\s*[:\-]\s*", "", raw_text, flags=re.IGNORECASE).strip()

    is_additive = len(ins_codes) > 0
    additive_class = None
    additive_chemical_name = None
    additive_code = None

    if ins_codes:
        additive_code = f"INS {ins_codes[0]}"
        raw_code = ins_codes[0]
        # Match against specific database
        if raw_code in specific_additives:
            entry = specific_additives[raw_code]
            additive_chemical_name = entry.get("name")
            additive_class = entry.get("class")
        else:
            # Try numeric prefix match (e.g. 500 in 500(ii))
            base_digits = re.match(r"\d+", raw_code)
            if base_digits and base_digits.group(0) in specific_additives:
                entry = specific_additives[base_digits.group(0)]
                additive_chemical_name = entry.get("name")
                additive_class = entry.get("class")
            else:
                additive_class = "Food Additive"

    # Check for functional class mentions in text
    functional_classes = [
        "Emulsifier", "Preservative", "Acidity Regulator", "Antioxidant",
        "Raising Agent", "Thickener", "Stabilizer", "Sweetener", "Colour",
        "Flavouring Substance", "Artificial Flavour", "Nature Identical Flavour"
    ]
    for fc in functional_classes:
        if re.search(r"\b" + re.escape(fc) + r"\b", raw_text, re.IGNORECASE):
            is_additive = True
            if not additive_class or additive_class == "Food Additive":
                additive_class = fc
            break

    # Sub-ingredients if compound ingredient (nested parentheses)
    sub_ingredients = []
    sub_match = re.search(r"\(([^)]+)\)", raw_text)
    if sub_match and not re.search(r"^\s*INS|\b%\b", sub_match.group(1), re.IGNORECASE):
        nested_items = split_ingredients_safely(sub_match.group(1))
        if len(nested_items) > 1:
            sub_ingredients = [item.strip() for item in nested_items]

    # Category determination
    if is_additive:
        category = "FOOD_ADDITIVE"
    elif any(grain in raw_text.lower() for grain in ["flour", "atta", "maida", "suji", "sugar", "oil", "fat", "milk", "water"]):
        category = "MAJOR_INGREDIENT"
    else:
        category = "INGREDIENT"

    return {
        "raw_text": raw_text.strip(),
        "name": cleaned_name,
        "percentage": percentage,
        "category": category,
        "is_additive": is_additive,
        "additive_code": additive_code,
        "additive_class": additive_class,
        "additive_chemical_name": additive_chemical_name,
        "sub_ingredients": sub_ingredients,
        "confidence": 0.92
    }


def parse_ingredients_declaration(raw_ingredients_text):
    """
    Main entry point for parsing ingredient declarations.
    """
    if not raw_ingredients_text or not raw_ingredients_text.strip():
        return {
            "found": False,
            "raw_text": "",
            "ingredients": [],
            "additives_detected": [],
            "quid_percentages_declared": False,
            "count": 0
        }

    # Remove leading "INGREDIENTS:" or "INGREDIENT DECLARATION:"
    cleaned = re.sub(r"^(?:ingredients?|contains)\s*[:\-]\s*", "", raw_ingredients_text.strip(), flags=re.IGNORECASE)

    raw_items = split_ingredients_safely(cleaned)
    parsed_items = [classify_ingredient_text(item) for item in raw_items if item.strip()]

    additives = [item for item in parsed_items if item["is_additive"]]
    has_quid = any(item["percentage"] is not None for item in parsed_items)

    return {
        "found": True,
        "raw_text": raw_ingredients_text.strip(),
        "ingredients": parsed_items,
        "additives_detected": additives,
        "quid_percentages_declared": has_quid,
        "count": len(parsed_items)
    }
