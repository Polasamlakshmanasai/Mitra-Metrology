package com.mitra.metrology.nlp

enum class AllergenStatus {
    CONTAINS,
    POSSIBLE_SOURCE,
    NOT_DETECTED
}

data class AllergenFinding(
    val name: String,
    val status: AllergenStatus,
    val matchedTerm: String? = null
)

object AllergenDetector {
    private val MANDATORY_ALLERGENS = mapOf(
        "Cereals containing Gluten" to listOf("wheat", "barley", "oats", "rye", "spelt", "gluten", "maida", "atta"),
        "Crustaceans" to listOf("crab", "prawn", "shrimp", "lobster"),
        "Milk and Milk Products" to listOf("milk", "butter", "cheese", "cream", "ghee", "casein", "whey", "lactose", "curd"),
        "Eggs and Egg Products" to listOf("egg", "albumin", "ovalbumin"),
        "Fish and Fish Products" to listOf("fish", "cod", "salmon", "anchovy"),
        "Peanuts and Tree Nuts" to listOf("peanut", "almond", "cashew", "walnut", "pistachio", "hazelnut"),
        "Soybeans" to listOf("soy", "soya", "soybean", "tofu"),
        "Sulphites" to listOf("sulphite", "sulfite", "metabisulphite", "ins 220", "ins 221", "ins 222")
    )

    fun evaluate(labelContent: String): List<AllergenFinding> {
        val lower = labelContent.lowercase()
        val findings = mutableListOf<AllergenFinding>()

        for ((allergen, terms) in MANDATORY_ALLERGENS) {
            val matched = terms.firstOrNull { lower.contains(it) }
            if (matched != null) {
                val isMayContain = lower.contains("may contain $matched") || lower.contains("traces of $matched")
                val status = if (isMayContain) AllergenStatus.POSSIBLE_SOURCE else AllergenStatus.CONTAINS
                findings.add(AllergenFinding(allergen, status, matched))
            }
        }
        return findings
    }
}
