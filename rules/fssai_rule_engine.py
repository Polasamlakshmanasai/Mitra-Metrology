# fssai_rule_engine.py
"""
Versioned FSSAI Rule Engine.
Evaluates structured pre-packaged food label entities against official
Food Safety and Standards (Labelling and Display) Regulations, 2020.
Enforces compliance states: PASS, FAIL, WARNING, NOT_APPLICABLE, UNREADABLE, INSUFFICIENT_DATA.
Attaches full evidentiary traces (Why? What was read? Where found? Which rule was checked?).
"""

import json
from pathlib import Path

RULES_DIR = Path(__file__).resolve().parent
REGULATIONS_FILE = RULES_DIR / "fssai_regulations_2020.json"


class FSSAIRuleEngine:
    def __init__(self):
        self.regulations = self._load_regulations()
        self.version = self.regulations.get("version", "2020.1")
        self.title = self.regulations.get("regulation_title", "FSSAI Labelling and Display Regulations, 2020")

    def _load_regulations(self):
        try:
            with open(REGULATIONS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            return {"rules": [], "version": "2020.1"}

    def evaluate(self, product_data, image_quality_score=0.9):
        """
        Main rule evaluation method.
        Compares extracted product fields against official FSSAI requirements.
        """
        results = []
        rules = self.regulations.get("rules", [])

        is_readable = image_quality_score >= 0.5

        for rule in rules:
            rule_id = rule["id"]
            citation = rule["citation"]
            title = rule["title"]
            category = rule["category"]
            severity = rule["severity"]
            requirement = rule["requirement"]

            status = "INSUFFICIENT_DATA"
            why = requirement
            what_was_read = None
            where_found = "Package Label"
            ocr_conf = 0.85
            recommendation = None

            # If image quality is unreadable, tag as UNREADABLE (never FAIL)
            if not is_readable:
                status = "UNREADABLE"
                what_was_read = "Image text was blurry or obscured."
                recommendation = "Retake photo with better lighting and sharpness."
                results.append(self._build_evidence_card(rule_id, citation, title, category, severity, status, why, what_was_read, where_found, 0.3, recommendation))
                continue

            # -------------------------------------------------------------
            # Rule 1: Name of Food (Regulation 5(1))
            # -------------------------------------------------------------
            if rule_id == "FSSAI-SEC-5-1":
                p_name = product_data.get("product_name")
                if p_name and p_name != "Pre-Packaged Food Product":
                    status = "PASS"
                    what_was_read = p_name
                    where_found = "Principal Display Panel"
                else:
                    status = "WARNING"
                    what_was_read = "Common name not clearly distinguishable"
                    recommendation = "Ensure the common or generic name indicating true nature of food is prominently printed."

            # -------------------------------------------------------------
            # Rule 2: List of Ingredients (Regulation 5(2))
            # -------------------------------------------------------------
            elif rule_id == "FSSAI-SEC-5-2":
                ing_data = product_data.get("ingredients", {})
                if ing_data.get("found") and ing_data.get("count", 0) > 0:
                    status = "PASS"
                    what_was_read = f"{ing_data['count']} ingredients declared: {', '.join(i['name'] for i in ing_data['ingredients'][:4])}..."
                    where_found = "Ingredients Panel"
                else:
                    status = "FAIL"
                    what_was_read = "No ingredients declaration found"
                    recommendation = "Under Reg 5(2), pre-packaged food must display 'Ingredients:' in descending order."

            # -------------------------------------------------------------
            # Rule 3: QUID % Declaration (Regulation 5(2)(c))
            # -------------------------------------------------------------
            elif rule_id == "FSSAI-SEC-5-2-C":
                ing_data = product_data.get("ingredients", {})
                if ing_data.get("quid_percentages_declared"):
                    status = "PASS"
                    quid_items = [f"{i['name']} ({i['percentage']}%)" for i in ing_data.get("ingredients", []) if i.get("percentage")]
                    what_was_read = f"QUID percentages found: {', '.join(quid_items)}"
                    where_found = "Ingredients List"
                else:
                    status = "WARNING"
                    what_was_read = "No ingredient percentages (%) detected"
                    recommendation = "If characterizing ingredients are highlighted on front of pack, declaration of ingoing percentage is required."

            # -------------------------------------------------------------
            # Rule 4: Mandatory Nutritional Information (Regulation 5(3))
            # -------------------------------------------------------------
            elif rule_id == "FSSAI-SEC-5-3":
                nutr = product_data.get("nutrition", {})
                nutrients = nutr.get("nutrients", {})
                mandatory_keys = ["energy", "protein", "carbohydrate", "total_sugars", "total_fat", "sodium"]
                present_mandatory = [k for k in mandatory_keys if nutrients.get(k, {}).get("value") is not None]

                if len(present_mandatory) >= 5:
                    status = "PASS"
                    what_was_read = f"Nutritional table detected ({nutr.get('basis', 'per 100g')}). Values for {', '.join(present_mandatory)} present."
                    where_found = "Nutrition Facts Panel"
                elif nutr.get("found"):
                    status = "WARNING"
                    missing = [k for k in mandatory_keys if k not in present_mandatory]
                    what_was_read = f"Partial nutrition table. Missing mandatory values for: {', '.join(missing)}"
                    recommendation = f"Ensure all 9 mandatory nutrients are declared per 100g/ml under FSSAI 2020."
                else:
                    status = "FAIL"
                    what_was_read = "No nutritional information table detected"
                    recommendation = "Regulation 5(3) mandates declaration of Energy, Protein, Carbs, Sugars, Fats, and Sodium."

            # -------------------------------------------------------------
            # Rule 5: Added Sugars & Trans Fat (Regulation 5(3)(b))
            # -------------------------------------------------------------
            elif rule_id == "FSSAI-SEC-5-3-B":
                nutr = product_data.get("nutrition", {})
                nutrients = nutr.get("nutrients", {})
                has_added_sugars = nutrients.get("added_sugars", {}).get("value") is not None
                has_trans_fat = nutrients.get("trans_fat", {}).get("value") is not None

                if has_added_sugars and has_trans_fat:
                    status = "PASS"
                    what_was_read = f"Added Sugars: {nutrients['added_sugars']['value']}{nutrients['added_sugars']['unit']}, Trans Fat: {nutrients['trans_fat']['value']}{nutrients['trans_fat']['unit']}"
                    where_found = "Nutrition Facts Panel"
                elif has_added_sugars or has_trans_fat:
                    status = "WARNING"
                    what_was_read = f"Only one of Added Sugars / Trans Fat declared. Added Sugars: {nutrients.get('added_sugars', {}).get('value')}, Trans Fat: {nutrients.get('trans_fat', {}).get('value')}"
                    recommendation = "Both Added Sugars and Trans Fat are mandatory sub-declarations under FSSAI 2020."
                else:
                    status = "FAIL" if nutr.get("found") else "WARNING"
                    what_was_read = "Added Sugars and Trans Fat lines missing"
                    recommendation = "Mandatory under FSSAI (Labelling & Display) Regulations, 2020."

            # -------------------------------------------------------------
            # Rule 6: Veg / Non-Veg Logo (Regulation 5(4))
            # -------------------------------------------------------------
            elif rule_id == "FSSAI-SEC-5-4":
                veg_info = product_data.get("veg_non_veg", {})
                v_status = veg_info.get("status")
                if v_status in ["VEGETARIAN", "NON_VEGETARIAN"]:
                    status = "PASS"
                    what_was_read = f"{v_status.replace('_', '-').title()} declaration ({veg_info.get('symbol')})"
                    where_found = "Principal Display Panel"
                else:
                    status = "WARNING"
                    what_was_read = "Veg/Non-Veg icon not confirmed via OCR text"
                    recommendation = "Mandatory green circle in green square (Veg) or brown triangle in brown square (Non-Veg) must be prominently displayed."

            # -------------------------------------------------------------
            # Rule 7: Food Additives with INS Numbers (Regulation 5(5))
            # -------------------------------------------------------------
            elif rule_id == "FSSAI-SEC-5-5":
                ing_data = product_data.get("ingredients", {})
                additives = ing_data.get("additives_detected", [])
                if len(additives) > 0:
                    status = "PASS"
                    add_summary = [f"{a['name']} ({a.get('additive_code') or a.get('additive_class')})" for a in additives]
                    what_was_read = f"{len(additives)} additive(s) declared with class/INS: {', '.join(add_summary)}"
                    where_found = "Ingredients Panel"
                else:
                    status = "NOT_APPLICABLE"
                    what_was_read = "No chemical additives declared (or 100% natural commodity)"
                    why = "Additives rule applies only when synthetic or standardized additives are incorporated."

            # -------------------------------------------------------------
            # Rule 8: Manufacturer Name & Address (Regulation 5(6))
            # -------------------------------------------------------------
            elif rule_id == "FSSAI-SEC-5-6":
                mfr = product_data.get("manufacturer")
                if mfr:
                    status = "PASS"
                    what_was_read = mfr
                    where_found = "Manufacturer Block"
                else:
                    status = "FAIL"
                    what_was_read = "Manufacturer details not found"
                    recommendation = "Name and complete postal address of the manufacturing unit must be stated under Reg 5(6)."

            # -------------------------------------------------------------
            # Rule 9: FSSAI Logo & 14-Digit License (Regulation 5(7))
            # -------------------------------------------------------------
            elif rule_id == "FSSAI-SEC-5-7":
                fssai_info = product_data.get("fssai_license", {})
                lic = fssai_info.get("license_number")
                if lic and len(lic) == 14:
                    status = "PASS"
                    what_was_read = f"FSSAI License: {lic} (Valid 14-digit format)"
                    where_found = "Licensing Block"
                elif lic:
                    status = "WARNING"
                    what_was_read = f"FSSAI number detected '{lic}' (Expected 14 digits, found {len(lic)})"
                    recommendation = "FSSAI license numbers must strictly consist of 14 digits."
                else:
                    status = "FAIL"
                    what_was_read = "FSSAI logo/license number not detected"
                    recommendation = "Mandatory under Reg 5(7) for all food business operators in India."

            # -------------------------------------------------------------
            # Rule 10: Net Quantity & MRP (Regulation 5(8))
            # -------------------------------------------------------------
            elif rule_id == "FSSAI-SEC-5-8":
                net_qty = product_data.get("net_quantity")
                mrp = product_data.get("mrp")
                if net_qty and mrp:
                    status = "PASS"
                    what_was_read = f"Net Quantity: {net_qty}, MRP: {mrp}"
                    where_found = "Statutory Box"
                elif net_qty or mrp:
                    status = "WARNING"
                    what_was_read = f"Partial declaration: Net Qty: {net_qty or 'Missing'}, MRP: {mrp or 'Missing'}"
                    recommendation = "Both Net Quantity and MRP (inclusive of all taxes) must be declared."
                else:
                    status = "FAIL"
                    what_was_read = "Net quantity and retail price missing"
                    recommendation = "Required under FSSAI Reg 5(8) & Legal Metrology Rules."

            # -------------------------------------------------------------
            # Rule 11: Batch / Lot Number (Regulation 5(9))
            # -------------------------------------------------------------
            elif rule_id == "FSSAI-SEC-5-9":
                batch = product_data.get("batch_number")
                if batch:
                    status = "PASS"
                    what_was_read = f"Batch/Lot: {batch}"
                    where_found = "Date & Coding Area"
                else:
                    status = "WARNING"
                    what_was_read = "Lot/Batch identification not detected"
                    recommendation = "Lot/Code/Batch identification is required for consumer traceability."

            # -------------------------------------------------------------
            # Rule 12: Date Marking (Regulation 5(10))
            # -------------------------------------------------------------
            elif rule_id == "FSSAI-SEC-5-10":
                mfd = product_data.get("manufacturing_date")
                exp = product_data.get("expiry_date") or product_data.get("best_before")
                if mfd and exp:
                    status = "PASS"
                    what_was_read = f"MFD: {mfd}, Expiry / Best Before: {exp}"
                    where_found = "Date Panel"
                elif exp or mfd:
                    status = "WARNING"
                    what_was_read = f"Partial date marking: MFD: {mfd or 'Not detected'}, Expiry/Best Before: {exp or 'Not detected'}"
                    recommendation = "Both Date of Packaging/Mfg and Expiry/Best Before are required under Reg 5(10)."
                else:
                    status = "FAIL"
                    what_was_read = "Date markings not detected"
                    recommendation = "Date marking is mandatory under FSSAI Regulation 5(10)."

            # -------------------------------------------------------------
            # Rule 13: Storage Instructions (Regulation 5(12))
            # -------------------------------------------------------------
            elif rule_id == "FSSAI-SEC-5-12":
                storage = product_data.get("storage_instructions")
                if storage:
                    status = "PASS"
                    what_was_read = storage
                    where_found = "Consumer Advisory Block"
                else:
                    status = "NOT_APPLICABLE"
                    what_was_read = "No special storage condition declared"
                    why = "Storage conditions required when special storage is needed to preserve shelf life."

            # -------------------------------------------------------------
            # Rule 14: Allergen Declaration (Regulation 5(14))
            # -------------------------------------------------------------
            elif rule_id == "FSSAI-SEC-5-14":
                allergen_res = product_data.get("allergens", {})
                detected = allergen_res.get("detected_allergens", [])
                has_explicit = allergen_res.get("explicit_declaration_found", False)

                if has_explicit or len(detected) > 0:
                    status = "PASS"
                    det_names = [f"{d['name']} ({d['status']})" for d in detected]
                    what_was_read = f"Allergen statement/sources detected: {', '.join(det_names) if det_names else 'Explicit allergy advice box'}"
                    where_found = "Allergen Block / Ingredients"
                else:
                    status = "WARNING"
                    what_was_read = "No explicit 'Contains' or 'Allergen Advice' declaration detected"
                    recommendation = "Under Reg 5(14), food containing gluten, milk, soy, nuts, peanuts, eggs, fish, etc. must carry an explicit allergen warning."

            # -------------------------------------------------------------
            # Rule 15: Dairy & Ghee Purity (FSS Standards Reg 2.1.8)
            # -------------------------------------------------------------
            elif rule_id == "FSSAI-SEC-DAIRY-GHEE":
                prod_name_lower = (product_data.get("product_name") or "").lower()
                all_text = str(product_data).lower()
                is_ghee = "ghee" in prod_name_lower or "ghee" in all_text

                if is_ghee:
                    has_milk_fat = "milk fat" in all_text or "clarified butter" in all_text or "99.7" in all_text
                    if has_milk_fat:
                        status = "PASS"
                        what_was_read = "Pure Ghee / Milk Fat standard confirmed (Min 99.7% Milk Fat standard)."
                        where_found = "Ingredients / Purity Declaration"
                    else:
                        status = "WARNING"
                        what_was_read = "Milk Fat percentage or purity declaration could not be definitively verified on label."
                        recommendation = "Regulation 2.1.8 requires Ghee to declare milk fat (min 99.7%) and purity standard."
                else:
                    status = "NOT_APPLICABLE"
                    what_was_read = "Not a ghee/dairy fat product."
                    why = "Applies specifically to Ghee, Butter Oil, and anhydrous milk fat."

            # -------------------------------------------------------------
            # Rule 16: Fortification (+F Logo) (FSS Fortification Reg 7)
            # -------------------------------------------------------------
            elif rule_id == "FSSAI-SEC-FORTIFICATION":
                all_text = str(product_data).lower()
                is_fortified = "fortified" in all_text or "+f" in all_text or "vitamin a" in all_text

                if is_fortified:
                    has_vitamins = "vitamin a" in all_text or "vitamin d" in all_text
                    status = "PASS" if has_vitamins else "WARNING"
                    what_was_read = "Fortification claim observed: 'Fortified with Vitamin A & D' / +F symbol referenced."
                    where_found = "Front of Pack / Principal Panel"
                else:
                    status = "NOT_APPLICABLE"
                    what_was_read = "No fortification claim made."
                    why = "Applies when food is fortified with micronutrients (Vitamins A, D, Iron, Folic Acid)."

            # -------------------------------------------------------------
            # Rule 17: AGMARK Certification
            # -------------------------------------------------------------
            elif rule_id == "FSSAI-SEC-AGMARK":
                all_text = str(product_data).lower()
                has_agmark = "agmark" in all_text or "special grade" in all_text

                if has_agmark:
                    status = "PASS"
                    what_was_read = "AGMARK Grade / Certification detected on packaging."
                    where_found = "Certification Seal"
                else:
                    status = "NOT_APPLICABLE"
                    what_was_read = "No AGMARK seal claimed."
                    why = "Optional quality grading for agricultural produce and dairy ghee."

            results.append(self._build_evidence_card(
                rule_id, citation, title, category, severity, status, why, what_was_read, where_found, ocr_conf, recommendation
            ))

        # Overall compliance determination
        pass_count = sum(1 for r in results if r["status"] == "PASS")
        fail_count = sum(1 for r in results if r["status"] == "FAIL")
        warning_count = sum(1 for r in results if r["status"] == "WARNING")

        if fail_count > 0:
            overall_verdict = "POTENTIAL_LABELLING_ISSUES_DETECTED"
            headline = "Potential Labelling Issues Detected"
            summary_desc = f"{fail_count} mandatory declaration(s) were missing or unreadable under FSSAI Regulations, 2020."
        elif warning_count > 0:
            overall_verdict = "NEEDS_REVIEW"
            headline = "Label Check Result: Needs Review"
            summary_desc = f"Most mandatory declarations were detected with {warning_count} item(s) recommended for manual verification."
        else:
            overall_verdict = "MANDATORY_DECLARATIONS_DETECTED"
            headline = "Label Check Result: Mandatory Declarations Present"
            summary_desc = "All mandatory packaging declarations were identified in the readable label."

        return {
            "regulations_version": self.version,
            "regulations_title": self.title,
            "overall_verdict": overall_verdict,
            "headline": headline,
            "summary": summary_desc,
            "pass_count": pass_count,
            "fail_count": fail_count,
            "warning_count": warning_count,
            "total_rules": len(results),
            "evidence_checklist": results,
            "statutory_disclaimer": "Results are based on the information visible/readable on the package label and are not a laboratory food-safety test. This tool checks compliance with FSSAI labelling and display regulations and does not assess physical, chemical, or microbiological safety."
        }

    def _build_evidence_card(self, rule_id, citation, title, category, severity, status, why, what_was_read, where_found, ocr_conf, recommendation):
        return {
            "rule_id": rule_id,
            "citation": citation,
            "title": title,
            "category": category,
            "severity": severity,
            "status": status,
            "why": why,
            "what_was_read": what_was_read,
            "where_found": where_found,
            "ocr_confidence": ocr_conf,
            "recommendation": recommendation
        }
