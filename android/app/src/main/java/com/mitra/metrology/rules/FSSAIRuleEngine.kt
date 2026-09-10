package com.mitra.metrology.rules

import com.mitra.metrology.nlp.AllergenDetector
import com.mitra.metrology.nlp.IngredientParser
import java.util.regex.Pattern

class FSSAIRuleEngine {

    fun evaluate(rawOcrText: String, isGheeOrDairy: Boolean = false): FSSAIComplianceReport {
        val checklist = mutableListOf<RuleEvidence>()
        val lower = rawOcrText.lowercase()

        // 1. Name of Food
        val hasName = rawOcrText.lines().any { it.trim().length in 3..50 }
        checklist.add(
            RuleEvidence(
                ruleId = "FSSAI-SEC-5-1",
                title = "Name of Food",
                status = if (hasName) ComplianceStatus.PASS else ComplianceStatus.FAIL,
                citation = "Regulation 5(1)",
                whatWasRead = rawOcrText.lines().firstOrNull { it.isNotBlank() } ?: "None",
                whereFound = "Principal Display Panel"
            )
        )

        // 2. Ingredients List
        val ingredients = IngredientParser.parse(rawOcrText)
        val hasIngredients = rawOcrText.contains("ingredient", ignoreCase = true) || ingredients.isNotEmpty()
        checklist.add(
            RuleEvidence(
                ruleId = "FSSAI-SEC-5-2",
                title = "List of Ingredients in Descending Order",
                status = if (hasIngredients) ComplianceStatus.PASS else ComplianceStatus.FAIL,
                citation = "Regulation 5(2)",
                whatWasRead = if (hasIngredients) "${ingredients.size} ingredients detected" else "No ingredients declaration found",
                whereFound = "Ingredients Panel"
            )
        )

        // 3. QUID %
        val hasQuid = ingredients.any { it.quidPercentage != null } || rawOcrText.contains("%")
        checklist.add(
            RuleEvidence(
                ruleId = "FSSAI-SEC-5-2-C",
                title = "Quantitative Ingredient Declaration (QUID)",
                status = if (hasQuid) ComplianceStatus.PASS else ComplianceStatus.WARNING,
                citation = "Regulation 5(2)(c)",
                whatWasRead = if (hasQuid) "QUID % declared for key ingredients" else "QUID % not observed",
                whereFound = "Ingredients List",
                recommendation = "Declare percentage of characterizing ingredients mentioned in product name."
            )
        )

        // 4. Nutritional Information
        val hasNutrition = rawOcrText.contains("nutritional", ignoreCase = true) || rawOcrText.contains("energy", ignoreCase = true)
        checklist.add(
            RuleEvidence(
                ruleId = "FSSAI-SEC-5-3",
                title = "Nutritional Information (Mandatory 9 Nutrients)",
                status = if (hasNutrition) ComplianceStatus.PASS else ComplianceStatus.FAIL,
                citation = "Regulation 5(3)",
                whatWasRead = if (hasNutrition) "Nutritional information table detected" else "Nutritional values missing",
                whereFound = "Nutrition Facts Panel"
            )
        )

        // 5. Veg / Non-Veg Logo
        val hasVeg = rawOcrText.contains("veg", ignoreCase = true) || rawOcrText.contains("green dot", ignoreCase = true)
        checklist.add(
            RuleEvidence(
                ruleId = "FSSAI-SEC-5-4",
                title = "Vegetarian / Non-Vegetarian Logo",
                status = if (hasVeg) ComplianceStatus.PASS else ComplianceStatus.WARNING,
                citation = "Regulation 5(4)",
                whatWasRead = if (hasVeg) "Vegetarian logo/declaration found" else "Symbol unconfirmed via OCR text",
                whereFound = "Principal Display Panel"
            )
        )

        // 6. Food Additives INS
        val additives = ingredients.filter { it.isAdditive }
        checklist.add(
            RuleEvidence(
                ruleId = "FSSAI-SEC-5-5",
                title = "Food Additives and INS Declarations",
                status = ComplianceStatus.PASS,
                citation = "Regulation 5(5)",
                whatWasRead = if (additives.isNotEmpty()) "${additives.size} INS additive(s) identified" else "No additives declared / single ingredient food",
                whereFound = "Ingredients Panel"
            )
        )

        // 7. FSSAI License 14-Digit Number
        val licPattern = Pattern.compile("(?i)(?:fssai|lic[\\.\\s]*no)[^0-9]{0,10}([0-9]{14})")
        val licMatcher = licPattern.matcher(rawOcrText)
        val hasLic = licMatcher.find()
        val licNumber = if (hasLic) licMatcher.group(1) else null
        checklist.add(
            RuleEvidence(
                ruleId = "FSSAI-SEC-5-7",
                title = "FSSAI Logo & 14-Digit License Number",
                status = if (hasLic) ComplianceStatus.PASS else ComplianceStatus.FAIL,
                citation = "Regulation 5(7)",
                whatWasRead = if (hasLic) "FSSAI Lic No: $licNumber" else "14-digit FSSAI license not detected",
                whereFound = "Licensing Block"
            )
        )

        // 8. Net Quantity & MRP
        val hasNetQty = rawOcrText.contains("net", ignoreCase = true) && (rawOcrText.contains("g") || rawOcrText.contains("ml") || rawOcrText.contains("kg") || rawOcrText.contains("l"))
        checklist.add(
            RuleEvidence(
                ruleId = "FSSAI-SEC-5-8",
                title = "Net Quantity and MRP",
                status = if (hasNetQty) ComplianceStatus.PASS else ComplianceStatus.WARNING,
                citation = "Regulation 5(8)",
                whatWasRead = if (hasNetQty) "Net quantity and retail price declared" else "Net quantity not confirmed",
                whereFound = "Statutory Box"
            )
        )

        // 9. Mandatory Allergen Declaration
        val allergens = AllergenDetector.evaluate(rawOcrText)
        val hasAllergenStmt = rawOcrText.contains("allergen", ignoreCase = true) || rawOcrText.contains("contains", ignoreCase = true) || allergens.isNotEmpty()
        checklist.add(
            RuleEvidence(
                ruleId = "FSSAI-SEC-5-14",
                title = "Mandatory Allergen Declaration",
                status = if (hasAllergenStmt) ComplianceStatus.PASS else ComplianceStatus.WARNING,
                citation = "Regulation 5(14)",
                whatWasRead = if (allergens.isNotEmpty()) "Identified: " + allergens.joinToString { "${it.name} (${it.status})" } else "No allergen warning found",
                whereFound = "Allergen Block / Ingredients"
            )
        )

        // 10. Ghee / Dairy Standards
        if (isGheeOrDairy || lower.contains("ghee") || lower.contains("butter")) {
            val hasMilkFat = rawOcrText.contains("milk fat", ignoreCase = true) || rawOcrText.contains("99.", ignoreCase = true)
            checklist.add(
                RuleEvidence(
                    ruleId = "FSSAI-SEC-DAIRY-GHEE",
                    title = "Ghee & Dairy Fat Purity Declaration",
                    status = if (hasMilkFat) ComplianceStatus.PASS else ComplianceStatus.WARNING,
                    citation = "FSS (Food Product Standards) Reg 2.1.8",
                    whatWasRead = if (hasMilkFat) "Pure milk fat declaration confirmed (min 99.7% standard)" else "Milk fat % not explicitly specified",
                    whereFound = "Purity / Ingredients Declaration"
                )
            )

            val hasAgmark = rawOcrText.contains("agmark", ignoreCase = true)
            checklist.add(
                RuleEvidence(
                    ruleId = "FSSAI-SEC-AGMARK",
                    title = "AGMARK Certification Seal & Grading",
                    status = if (hasAgmark) ComplianceStatus.PASS else ComplianceStatus.WARNING,
                    citation = "Agricultural Produce (Grading and Marking) Act",
                    whatWasRead = if (hasAgmark) "AGMARK Grade / CA Number confirmed on packaging" else "AGMARK seal not observed",
                    whereFound = "Certification Seal"
                )
            )
        }

        val passCount = checklist.count { it.status == ComplianceStatus.PASS }
        val score = (passCount.toFloat() / checklist.size) * 100f
        val verdict = if (score >= 80f) "MANDATORY_DECLARATIONS_DETECTED" else "POTENTIAL_LABELLING_ISSUES_DETECTED"

        return FSSAIComplianceReport(
            overallVerdict = verdict,
            complianceScore = score,
            totalRules = checklist.size,
            passCount = passCount,
            checklist = checklist
        )
    }
}
