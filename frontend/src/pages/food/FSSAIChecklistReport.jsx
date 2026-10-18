import { useState } from "react";

function FSSAIChecklistReport({ reportData, onReset }) {
  const [selectedEvidence, setSelectedEvidence] = useState(null);
  const [filterStatus, setFilterStatus] = useState("ALL");

  if (!reportData) return null;

  const {
    product_overview = {},
    ingredients_analysis = {},
    allergen_analysis = {},
    nutrition_facts = {},
    fssai_report = {},
    statutory_disclaimer,
  } = reportData;

  const checklist = fssai_report.evidence_checklist || [];

  const filteredChecklist = checklist.filter((item) => {
    if (filterStatus === "ALL") return true;
    if (filterStatus === "ISSUES") return item.status === "FAIL" || item.status === "WARNING";
    if (filterStatus === "PASS") return item.status === "PASS";
    return true;
  });

  const getStatusBadge = (status) => {
    switch (status) {
      case "PASS":
        return "bg-green-50 text-green-700 border-green-200";
      case "FAIL":
        return "bg-red-50 text-red-700 border-red-200";
      case "WARNING":
        return "bg-amber-50 text-amber-700 border-amber-200";
      case "UNREADABLE":
        return "bg-purple-50 text-purple-700 border-purple-200";
      case "NOT_APPLICABLE":
        return "bg-slate-100 text-slate-500 border-slate-200";
      default:
        return "bg-slate-100 text-slate-700 border-slate-200";
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case "PASS":
        return "✓";
      case "FAIL":
        return "✕";
      case "WARNING":
        return "⚠️";
      case "UNREADABLE":
        return "👁️";
      case "NOT_APPLICABLE":
        return "—";
      default:
        return "•";
    }
  };

  return (
    <div className="space-y-8 animate-fadeIn text-[#183153]">
      {/* 1. MANDATORY FOOD SAFETY & REGULATORY DISCLAIMER */}
      <div className="p-4 sm:p-5 rounded-2xl bg-amber-50 border border-amber-300 text-amber-900 text-xs sm:text-sm flex items-start gap-3 shadow-sm">
        <span className="text-xl shrink-0">⚖️</span>
        <div>
          <h4 className="font-bold uppercase tracking-wider text-amber-800 text-xs mb-1">
            Mandatory Regulatory & Safety Disclaimer
          </h4>
          <p className="leading-relaxed text-slate-700">
            {statutory_disclaimer ||
              "Results are based on information visible and readable on the package label and are NOT a laboratory food-safety test. This tool verifies compliance with FSSAI (Labelling and Display) Regulations, 2020 and cannot assess physical, chemical, or microbiological safety."}
          </p>
        </div>
      </div>

      {/* 2. OVERALL AUDIT HEADLINE BANNER */}
      <div
        className={`border rounded-2xl p-6 sm:p-8 shadow-sm ${
          fssai_report.overall_verdict === "MANDATORY_DECLARATIONS_DETECTED"
            ? "bg-emerald-50/80 border-emerald-300"
            : fssai_report.overall_verdict === "POTENTIAL_LABELLING_ISSUES_DETECTED"
            ? "bg-rose-50/80 border-rose-300"
            : "bg-amber-50/80 border-amber-300"
        }`}
      >
        <div className="flex flex-wrap items-center justify-between gap-6">
          <div className="flex items-start gap-4">
            <div className="w-14 h-14 rounded-2xl bg-white border border-[#D5DCE5] flex items-center justify-center text-3xl shrink-0 shadow-sm">
              {fssai_report.overall_verdict === "MANDATORY_DECLARATIONS_DETECTED"
                ? "🛡️"
                : fssai_report.overall_verdict === "POTENTIAL_LABELLING_ISSUES_DETECTED"
                ? "🚫"
                : "⚠️"}
            </div>
            <div>
              <span className="text-xs font-mono uppercase tracking-widest text-slate-600 font-semibold">
                {fssai_report.regulations_title || "FSSAI Regulations, 2020"} (v{fssai_report.regulations_version})
              </span>
              <h2 className="text-2xl sm:text-3xl font-bold text-[#183153] mt-1">
                {fssai_report.headline || "Label Check Result"}
              </h2>
              <p className="text-sm text-slate-600 mt-1 max-w-2xl">{fssai_report.summary}</p>
            </div>
          </div>

          {/* Metric Pills */}
          <div className="flex items-center gap-3 bg-white border border-[#D5DCE5] p-3 rounded-2xl shadow-sm">
            <div className="text-center px-3">
              <span className="text-xs text-slate-500 block font-medium">Passed</span>
              <span className="text-2xl font-black text-green-700">{fssai_report.pass_count || 0}</span>
            </div>
            <div className="h-8 w-px bg-slate-200" />
            <div className="text-center px-3">
              <span className="text-xs text-slate-500 block font-medium">Warnings</span>
              <span className="text-2xl font-black text-amber-700">{fssai_report.warning_count || 0}</span>
            </div>
            <div className="h-8 w-px bg-slate-200" />
            <div className="text-center px-3">
              <span className="text-xs text-slate-500 block font-medium">Non-Compliant</span>
              <span className="text-2xl font-black text-red-700">{fssai_report.fail_count || 0}</span>
            </div>
          </div>
        </div>
      </div>

      {/* 3. PRODUCT OVERVIEW CARD */}
      <div className="bg-white border border-[#D5DCE5] rounded-2xl p-6 sm:p-7 shadow-sm">
        <h3 className="text-base font-bold text-[#183153] mb-4 flex items-center justify-between">
          <span className="flex items-center gap-2">
            <span>📦</span> Packaged Commodity Identification
          </span>
          {product_overview.veg_non_veg?.status === "VEGETARIAN" && (
            <span className="text-xs px-2.5 py-1 rounded-full font-bold bg-green-50 text-green-700 border border-green-200 flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-green-600 inline-block" /> 100% Vegetarian
            </span>
          )}
          {product_overview.veg_non_veg?.status === "NON_VEGETARIAN" && (
            <span className="text-xs px-2.5 py-1 rounded-full font-bold bg-amber-50 text-amber-800 border border-amber-300 flex items-center gap-1.5">
              <span className="w-2 h-2 bg-amber-600 rotate-45 inline-block" /> Non-Vegetarian
            </span>
          )}
        </h3>

        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4 text-xs">
          <div className="p-3.5 bg-[#F5F7FA] rounded-xl border border-[#D5DCE5]">
            <span className="text-slate-500 block font-medium">Declared Product Name</span>
            <span className="font-bold text-[#183153] text-sm mt-0.5 line-clamp-1">
              {product_overview.name || "Pre-Packaged Food"}
            </span>
          </div>

          <div className="p-3.5 bg-[#F5F7FA] rounded-xl border border-[#D5DCE5]">
            <span className="text-slate-500 block font-medium">FSSAI 14-Digit License</span>
            <span className="font-mono font-bold text-[#174A7E] text-sm mt-0.5">
              {product_overview.fssai_license?.license_number || "Not detected on panel"}
            </span>
          </div>

          <div className="p-3.5 bg-[#F5F7FA] rounded-xl border border-[#D5DCE5]">
            <span className="text-slate-500 block font-medium">Net Quantity & Retail Price</span>
            <span className="font-bold text-[#183153] text-sm mt-0.5">
              {product_overview.net_quantity || "Qty unstated"} • {product_overview.mrp || "MRP unstated"}
            </span>
          </div>

          <div className="p-3.5 bg-[#F5F7FA] rounded-xl border border-[#D5DCE5]">
            <span className="text-slate-500 block font-medium">Date of Mfg & Expiry / Best Before</span>
            <span className="font-mono text-slate-700 text-xs mt-0.5 block">
              MFD: {product_overview.dates?.mfd || "—"} | EXP: {product_overview.dates?.expiry || product_overview.dates?.best_before || "—"}
            </span>
          </div>

          {product_overview.manufacturer && (
            <div className="p-3.5 bg-[#F5F7FA] rounded-xl border border-[#D5DCE5] sm:col-span-2 lg:col-span-4">
              <span className="text-slate-500 block font-medium">Manufacturer / Packer / Marketer</span>
              <span className="font-semibold text-slate-800 text-xs mt-0.5">{product_overview.manufacturer}</span>
            </div>
          )}
        </div>
      </div>

      {/* 4. THREE-COLUMN DOMAIN BREAKDOWN (INGREDIENTS, ALLERGENS, NUTRITION) */}
      <div className="grid lg:grid-cols-12 gap-6">
        {/* INGREDIENTS & ADDITIVES (5 Cols) */}
        <div className="lg:col-span-5 bg-white border border-[#D5DCE5] rounded-2xl p-6 shadow-sm flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-base font-bold text-[#183153] flex items-center gap-2">
                <span>🧪</span> Ingredients & Food Additives
              </h3>
              <span className="text-xs text-[#174A7E] font-mono font-bold">
                {ingredients_analysis.count || 0} declared
              </span>
            </div>

            {ingredients_analysis.ingredients && ingredients_analysis.ingredients.length > 0 ? (
              <div className="space-y-2.5 max-h-72 overflow-y-auto pr-1">
                {ingredients_analysis.ingredients.map((ing, idx) => (
                  <div
                    key={idx}
                    className="p-2.5 rounded-xl bg-[#F5F7FA] border border-[#D5DCE5] text-xs flex items-center justify-between"
                  >
                    <div>
                      <span className="font-semibold text-[#183153]">{ing.name}</span>
                      {ing.percentage !== null && (
                        <span className="ml-2 font-mono text-[#174A7E] font-bold">
                          ({ing.percentage}%)
                        </span>
                      )}
                      {ing.additive_class && (
                        <span className="block text-[11px] text-amber-700 font-medium mt-0.5">
                          {ing.additive_code ? `${ing.additive_code}: ` : ""}{ing.additive_class}
                        </span>
                      )}
                    </div>
                    <span
                      className={`text-[10px] px-2 py-0.5 rounded font-bold uppercase border ${
                        ing.is_additive
                          ? "bg-amber-50 text-amber-800 border-amber-200"
                          : "bg-slate-100 text-slate-600 border-slate-200"
                      }`}
                    >
                      {ing.is_additive ? "Additive" : "Base"}
                    </span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-xs text-slate-500 italic py-6 text-center">
                No ingredient statement extracted.
              </p>
            )}
          </div>

          <div className="mt-4 pt-3 border-t border-slate-200 text-[11px] text-slate-500 flex items-center justify-between">
            <span>INS Codes Mapped: {ingredients_analysis.additives_detected?.length || 0}</span>
            <span>QUID % Declared: {ingredients_analysis.quid_percentages_declared ? "Yes ✓" : "No"}</span>
          </div>
        </div>

        {/* ALLERGEN MATRIX (3 Cols) */}
        <div className="lg:col-span-3 bg-white border border-[#D5DCE5] rounded-2xl p-6 shadow-sm flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-base font-bold text-[#183153] flex items-center gap-2">
                <span>⚠️</span> Allergen Check
              </h3>
              <span className="text-xs text-slate-500 font-medium">Reg 5(14)</span>
            </div>

            <div className="space-y-2 max-h-72 overflow-y-auto pr-1">
              {allergen_analysis.allergen_breakdown?.map((item, idx) => (
                <div
                  key={idx}
                  className="p-2 rounded-xl bg-[#F5F7FA] border border-[#D5DCE5] text-xs flex items-center justify-between"
                >
                  <span className="text-slate-800 font-medium truncate max-w-[130px]">{item.name}</span>
                  <span
                    className={`text-[10px] px-2 py-0.5 rounded font-bold uppercase border ${
                      item.status === "CONTAINS"
                        ? "bg-rose-50 text-rose-700 border-rose-200"
                        : item.status === "POSSIBLE_SOURCE"
                        ? "bg-amber-50 text-amber-800 border-amber-200"
                        : item.status === "UNABLE_TO_DETERMINE"
                        ? "bg-purple-50 text-purple-700 border-purple-200"
                        : "bg-slate-100 text-slate-500 border-slate-200"
                    }`}
                  >
                    {item.status === "CONTAINS"
                      ? "Contains"
                      : item.status === "POSSIBLE_SOURCE"
                      ? "Traces"
                      : item.status === "UNABLE_TO_DETERMINE"
                      ? "Unclear"
                      : "Not detected"}
                  </span>
                </div>
              ))}
            </div>
          </div>

          <p className="mt-4 pt-3 border-t border-slate-200 text-[10px] text-slate-500 leading-tight">
            *Lack of detection on label does not certify product is allergen-free.
          </p>
        </div>

        {/* NUTRITION FACTS (4 Cols) */}
        <div className="lg:col-span-4 bg-white border border-[#D5DCE5] rounded-2xl p-6 shadow-sm flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-base font-bold text-[#183153] flex items-center gap-2">
                <span>🥗</span> Nutritional Info
              </h3>
              <span className="text-xs text-slate-500 font-mono">
                {nutrition_facts.basis || "per 100g"}
              </span>
            </div>

            {nutrition_facts.found ? (
              <div className="space-y-1.5 text-xs max-h-72 overflow-y-auto pr-1">
                {Object.entries(nutrition_facts.nutrients || {}).map(([k, n]) => (
                  <div
                    key={k}
                    className="flex items-center justify-between py-1.5 px-2.5 rounded-lg bg-[#F5F7FA] border border-[#D5DCE5]"
                  >
                    <span className="text-slate-600 capitalize">
                      {k.replace(/_/g, " ")}:
                    </span>
                    <span className="font-mono font-bold text-[#183153]">
                      {n.value !== null ? `${n.value} ${n.unit}` : "Not declared"}
                    </span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-xs text-slate-500 italic py-6 text-center">
                No nutritional panel detected.
              </p>
            )}
          </div>

          {nutrition_facts.consistency_warnings?.length > 0 && (
            <div className="mt-3 p-2 rounded-xl bg-amber-50 border border-amber-200 text-[11px] text-amber-800">
              ⚠️ {nutrition_facts.consistency_warnings[0]}
            </div>
          )}
        </div>
      </div>

      {/* 5. INTERACTIVE STATUTORY EVIDENCE CHECKLIST */}
      <div className="bg-white border border-[#D5DCE5] rounded-2xl p-6 sm:p-8 shadow-sm">
        <div className="flex flex-wrap items-center justify-between gap-4 mb-6">
          <div>
            <h3 className="text-lg font-bold text-[#183153] flex items-center gap-2">
              <span>🔍</span> FSSAI Statutory Declarations Checklist
            </h3>
            <p className="text-xs text-slate-600 mt-1">
              Click any statutory rule to open the verifiable evidentiary trace (*Why, What was read, Where found*).
            </p>
          </div>

          <div className="flex gap-2 text-xs">
            {["ALL", "ISSUES", "PASS"].map((btn) => (
              <button
                key={btn}
                onClick={() => setFilterStatus(btn)}
                className={`px-3 py-1.5 rounded-lg font-semibold transition ${
                  filterStatus === btn
                    ? "bg-[#174A7E] text-white shadow-sm"
                    : "bg-[#F5F7FA] text-slate-700 hover:bg-slate-200 border border-[#D5DCE5]"
                }`}
              >
                {btn === "ALL" ? "All Rules" : btn === "ISSUES" ? "Issues Only" : "Passed"}
              </button>
            ))}
          </div>
        </div>

        <div className="divide-y divide-[#D5DCE5]">
          {filteredChecklist.map((item, idx) => (
            <div
              key={idx}
              onClick={() => setSelectedEvidence(item)}
              className="py-3.5 px-3 rounded-xl hover:bg-[#F5F7FA] cursor-pointer transition flex items-center justify-between gap-4 group"
            >
              <div className="flex items-center gap-3.5">
                <span
                  className={`w-7 h-7 rounded-lg flex items-center justify-center text-xs font-bold border shrink-0 ${getStatusBadge(
                    item.status
                  )}`}
                >
                  {getStatusIcon(item.status)}
                </span>
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-bold text-[#183153] group-hover:text-[#174A7E] transition">
                      {item.title}
                    </span>
                    <span className="text-xs font-mono text-slate-500">[{item.citation}]</span>
                  </div>
                  <p className="text-xs text-slate-600 line-clamp-1 mt-0.5">
                    {item.what_was_read || item.why}
                  </p>
                </div>
              </div>

              <div className="flex items-center gap-3 shrink-0">
                <span
                  className={`text-[11px] px-2.5 py-0.5 rounded-full font-bold uppercase border ${getStatusBadge(
                    item.status
                  )}`}
                >
                  {item.status.replace(/_/g, " ")}
                </span>
                <span className="text-xs text-slate-500 group-hover:translate-x-1 transition font-medium">
                  Details →
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* 6. TRANSPARENT EVIDENCE MODAL */}
      {selectedEvidence && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white border border-[#D5DCE5] rounded-2xl max-w-2xl w-full p-6 sm:p-8 shadow-2xl space-y-5">
            <div className="flex items-center justify-between pb-4 border-b border-slate-200">
              <div>
                <span className="text-xs font-mono text-[#174A7E] font-semibold">
                  Citation: {selectedEvidence.citation} ({selectedEvidence.rule_id})
                </span>
                <h3 className="text-xl font-bold text-[#183153] mt-0.5">{selectedEvidence.title}</h3>
              </div>
              <button
                onClick={() => setSelectedEvidence(null)}
                className="text-slate-400 hover:text-slate-700 p-2 rounded-xl hover:bg-slate-100"
              >
                ✕
              </button>
            </div>

            <div className="space-y-4 text-xs">
              {/* STATUS */}
              <div className="flex items-center justify-between p-3.5 bg-[#F5F7FA] rounded-xl border border-[#D5DCE5]">
                <span className="text-slate-600 font-medium">Evaluated Compliance Status:</span>
                <span
                  className={`px-3 py-1 rounded-full font-bold uppercase border ${getStatusBadge(
                    selectedEvidence.status
                  )}`}
                >
                  {selectedEvidence.status}
                </span>
              </div>

              {/* WHY? */}
              <div className="p-4 bg-[#F5F7FA] rounded-xl border border-[#D5DCE5]">
                <h4 className="font-bold text-[#183153] uppercase tracking-wider text-[11px] mb-1">
                  1. Why was this checked? (Statutory Requirement)
                </h4>
                <p className="text-slate-700 leading-relaxed">{selectedEvidence.why}</p>
              </div>

              {/* WHAT WAS READ? */}
              <div className="p-4 bg-[#F5F7FA] rounded-xl border border-[#D5DCE5]">
                <h4 className="font-bold text-[#183153] uppercase tracking-wider text-[11px] mb-1">
                  2. What was read from the package? (Extracted Text / Value)
                </h4>
                <p className="font-mono text-[#183153] text-sm bg-white p-2.5 rounded-lg border border-[#D5DCE5]">
                  {selectedEvidence.what_was_read || "No visible text detected for this declaration."}
                </p>
              </div>

              {/* WHERE WAS IT FOUND? */}
              <div className="p-4 bg-[#F5F7FA] rounded-xl border border-[#D5DCE5] flex items-center justify-between">
                <div>
                  <h4 className="font-bold text-[#183153] uppercase tracking-wider text-[11px]">
                    3. Where was it found?
                  </h4>
                  <p className="text-slate-700 mt-0.5">{selectedEvidence.where_found}</p>
                </div>
                <div className="text-right">
                  <span className="text-slate-500 block">OCR Confidence</span>
                  <span className="font-mono font-bold text-[#183153]">
                    {Math.round((selectedEvidence.ocr_confidence || 0.85) * 100)}%
                  </span>
                </div>
              </div>

              {/* RECOMMENDATION IF ANY */}
              {selectedEvidence.recommendation && (
                <div className="p-4 bg-red-50 border border-red-200 rounded-xl text-red-900">
                  <h4 className="font-bold text-red-800 uppercase tracking-wider text-[11px] mb-1">
                    Corrective Recommendation
                  </h4>
                  <p className="text-red-700">{selectedEvidence.recommendation}</p>
                </div>
              )}
            </div>

            <div className="pt-2 flex justify-end">
              <button
                onClick={() => setSelectedEvidence(null)}
                className="bg-[#174A7E] hover:bg-[#133D68] text-white px-6 py-2.5 rounded-xl font-bold text-sm shadow-sm transition"
              >
                Close Inspection
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 7. RESET / NEW SCAN BUTTON */}
      <div className="flex justify-between items-center pt-4">
        <button
          onClick={onReset}
          className="bg-white hover:bg-[#F5F7FA] text-[#183153] px-6 py-3 rounded-xl font-bold text-sm border border-[#D5DCE5] transition shadow-sm"
        >
          ← Inspect Another Food Package
        </button>

        <button
          onClick={() => window.print()}
          className="bg-[#174A7E] hover:bg-[#133D68] text-white px-6 py-3 rounded-xl font-bold text-sm shadow-sm transition flex items-center gap-2"
        >
          <span>🖨️</span> Export FSSAI Audit Summary
        </button>
      </div>
    </div>
  );
}

export default FSSAIChecklistReport;
