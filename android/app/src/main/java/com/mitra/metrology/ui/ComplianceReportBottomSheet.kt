package com.mitra.metrology.ui

import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.TextView
import com.google.android.material.bottomsheet.BottomSheetDialogFragment
import com.mitra.metrology.R
import com.mitra.metrology.rules.FSSAIComplianceReport

class ComplianceReportBottomSheet(
    private val report: FSSAIComplianceReport
) : BottomSheetDialogFragment() {

    override fun onCreateView(
        inflater: LayoutInflater,
        container: ViewGroup?,
        savedInstanceState: Bundle?
    ): View? {
        return inflater.inflate(R.layout.bottom_sheet_report, container, false)
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)

        val tvTitle = view.findViewById<TextView>(R.id.tvReportTitle)
        val tvScore = view.findViewById<TextView>(R.id.tvReportScore)
        val tvChecklist = view.findViewById<TextView>(R.id.tvChecklistContent)
        val tvDisclaimer = view.findViewById<TextView>(R.id.tvDisclaimer)

        tvTitle.text = "Verdict: ${report.overallVerdict}"
        tvScore.text = "FSSAI Statutory Score: ${report.complianceScore.toInt()}% (${report.passCount}/${report.totalRules} Rules Met)"

        val sb = StringBuilder()
        for (item in report.checklist) {
            val badge = when (item.status.name) {
                "PASS" -> "[PASS]"
                "WARNING" -> "[WARNING]"
                "FAIL" -> "[VIOLATION]"
                else -> "[N/A]"
            }
            sb.append("$badge ${item.title} (${item.citation})
")
            sb.append("  • Found: ${item.whatWasRead}
")
            sb.append("  • At: ${item.whereFound}

")
        }
        tvChecklist.text = sb.toString()
        tvDisclaimer.text = report.disclaimer
    }
}
