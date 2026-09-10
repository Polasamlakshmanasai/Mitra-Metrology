package com.mitra.metrology.rules

enum class ComplianceStatus {
    PASS,
    WARNING,
    FAIL,
    NOT_APPLICABLE,
    UNREADABLE
}

data class RuleEvidence(
    val ruleId: String,
    val title: String,
    val status: ComplianceStatus,
    val citation: String,
    val whatWasRead: String,
    val whereFound: String,
    val recommendation: String? = null
)

data class FSSAIComplianceReport(
    val overallVerdict: String,
    val complianceScore: Float,
    val totalRules: Int,
    val passCount: Int,
    val checklist: List<RuleEvidence>,
    val disclaimer: String = "Statutory Note: Label compliance assessment is based strictly on visible packaging text against FSSAI Labelling & Display Regulations 2020. This is not a substitute for authorized laboratory chemical/microbiological testing. System does not certify packages as FSSAI Approved."
)
