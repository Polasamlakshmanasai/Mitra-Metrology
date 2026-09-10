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
        return "bg-emerald-950/80 text-emerald-300 border-emerald-700/60";
      case "FAIL":
        return "bg-rose-950/80 text-rose-300 border-rose-700/60";
      case "WARNING":
        return "bg-amber-950/80 text-amber-300 border-amber-700/60";
      case "UNREADABLE":
        return "bg-purple-950/80 text-purple-300 border-purple-700/60";
      case "NOT_APPLICABLE":
        return "bg-slate-800 text-slate-400 border-slate-700";
      default:
        return "bg-slate-800 text-slate-300 border-slate-700";
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
    <div className="space-y-8 animate-fadeIn">
      {/* 1. MANDATORY FOOD SAFETY & REGULATORY DISCLAIMER */}
      <div className="p-4 sm:p-5 rounded-2xl bg-amber-950/30 border border-amber-600/40 text-amber-200 text-xs sm:text-sm flex items-start gap-3 shadow-md">
        <span className="text-xl shrink-0">⚖️</span>
        <div>
          <h4 className="font-bold uppercase tracking-wider text-amber-400 text-xs mb-1">
            Mandatory Regulatory & Safety Disclaimer
          </h4>
          <p className="leading-relaxed text-slate-300">
            {statutory_disclaimer ||
              "Results are based on information visible and readable on the package label and are NOT a laboratory food-safety test. This tool verifies compliance with FSSAI (Labelling and Display) Regulations, 2020 and cannot assess physical, chemical, or microbiological safety."}
          </p>
        </div>
      </div>

      {/* 2. OVERALL AUDIT HEADLINE BANNER */}
      <div
        className={`border rounded-3xl p-6 sm:p-8 shadow-xl ${
          fssai_report.overall_verdict === "MANDATORY_DECLARATIONS_DETECTED"
            ? "bg-gradient-to-r from-emerald-950/60 via-slate-900 to-slate-900 border-emerald-500/40"
            : fssai_report.overall_verdict === "POTENTIAL_LABELLING_ISSUES_DETECTED"
            ? "bg-gradient-to-r from-rose-950/60 via-slate-900 to-slate-900 border-rose-500/40"
            : "bg-gradient-to-r from-amber-950/60 via-slate-900 to-slate-900 border-amber-500/40"
        }`}
      >
        <div className="flex flex-wrap items-center justify-between gap-6">
          <div className="flex items-start gap-4">
            <div className="w-14 h-14 rounded-2xl bg-slate-900/80 border border-slate-700/60 flex items-center justify-center text-3xl shrink-0 shadow-md">
              {fssai_report.overall_verdict === "MANDATORY_DECLARATIONS_DETECTED"
                ? "🛡️"
                : fssai_report.overall_verdict === "POTENTIAL_LABELLING_ISSUES_DETECTED"
                ? "🚫"
                : "⚠️"}
            </div>
            <div>
              <span className="text-xs font-mono uppercase tracking-widest text-slate-400">
                {fssai_report.regulations_title || "FSSAI Regulations, 2020"} (v{fssai_report.regulations_version})
              </span>
              <h2 className="text-2xl sm:text-3xl font-black text-white mt-1">
                {fssai_report.headline || "Label Check Result"}
              </h2>
              <p className="text-sm text-slate-300 mt-1 max-w-2xl">{fssai_report.summary}</p>
            </div>
          </div>

          {/* Metric Pills */}
          <div className="flex items-center gap-3 bg-slate-950/80 border border-slate-800 p-3 rounded-2xl">
            <div className="text-center px-3">
              <span className="text-xs text-slate-400 block font-medium">Passed</span>
              <span className="text-2xl font-black text-emerald-400">{fssai_report.pass_count || 0}</span>
            </div>
            <div className="h-8 w-px bg-slate-800" />
            <div className="text-center px-3">
              <span className="text-xs text-slate-400 block font-medium">Warnings</span>
              <span className="text-2xl font-black text-amber-400">{fssai_report.warning_count || 0}</span>
            </div>
            <div className="h-8 w-px bg-slate-800" />
            <div className="text-center px-3">
              <span className="text-xs text-slate-400 block font-medium">Non-Compliant</span>
              <span className="text-2xl font-black text-rose-400">{fssai_report.fail_count || 0}</span>
            </div>
          </div>
        </div>
      </div>

      {/* 3. PRODUCT OVERVIEW CARD */}
      <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 sm:p-7 shadow-lg">
        <h3 className="text-lg font-bold text-white mb-4 flex items-center justify-between">
          <span className="flex items-center gap-2">
            <span>📦</span> Packaged Commodity Identification
          </span>
          {product_overview.veg_non_veg?.status === "VEGETARIAN" && (
            <span className="text-xs px-2.5 py-1 rounded-full font-bold bg-emerald-950 text-emerald-400 border border-emerald-700 flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-emerald-400 inline-block" /> 100% Vegetarian
            </span>
          )}
          {product_overview.veg_non_veg?.status === "NON_VEGETARIAN" && (
            <span className="text-xs px-2.5 py-1 rounded-full font-bold bg-amber-950 text-amber-400 border border-amber-700 flex items-center gap-1.5">
              <span className="w-2 h-2 bg-amber-600 rotate-45 inline-block" /> Non-Vegetarian
            </span>
          )}
        </h3>

        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4 text-xs">
          <div className="p-3.5 bg-slate-950 rounded-xl border border-slate-800/80">
            <span className="text-slate-400 block">Declared Product Name</span>
            <span className="font-bold text-slate-200 text-sm mt-0.5 line-clamp-1">
              {product_overview.name || "Pre-Packaged Food"}
            </span>
          </div>

          <div className="p-3.5 bg-slate-950 rounded-xl border border-slate-800/80">
            <span className="text-slate-400 block">FSSAI 14-Digit License</span>
            <span className="font-mono font-bold text-blue-400 text-sm mt-0.5">
              {product_overview.fssai_license?.license_number || "Not detected on panel"}
            </span>
          </div>

          <div className="p-3.5 bg-slate-950 rounded-xl border border-slate-800/80">
            <span className="text-slate-400 block">Net Quantity & Retail Price</span>
            <span className="font-semibold text-slate-200 text-sm mt-0.5">
              {product_overview.net_quantity || "Qty unstated"} • {product_overview.mrp || "MRP unstated"}
            </span>
          </div>

          <div className="p-3.5 bg-slate-950 rounded-xl border border-slate-800/80">
            <span className="text-slate-400 block">Date of Mfg & Expiry / Best Before</span>
            <span className="font-mono text-slate-300 text-xs mt-0.5 block">
              MFD: {product_overview.dates?.mfd || "—"} | EXP: {product_overview.dates?.expiry || product_overview.dates?.best_before || "—"}
            </span>
          </div>

          {product_overview.manufacturer && (
            <div className="p-3.5 bg-slate-950 rounded-xl border border-slate-800/80 sm:col-span-2 lg:col-span-4">
              <span className="text-slate-400 block">Manufacturer / Packer / Marketer</span>
              <span className="font-medium text-slate-300 text-xs mt-0.5">{product_overview.manufacturer}</span>
            </div>
          )}
        </div>
      </div>

      {/* 4. THREE-COLUMN DOMAIN BREAKDOWN (INGREDIENTS, ALLERGENS, NUTRITION) */}
      <div className="grid lg:grid-cols-12 gap-6">
        {/* INGREDIENTS & ADDITIVES (5 Cols) */}
        <div className="lg:col-span-5 bg-slate-900 border border-slate-800 rounded-3xl p-6 shadow-lg flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <span>🧪</span> Ingredients & Food Additives
              </h3>
              <span className="text-xs text-blue-400 font-mono">
                {ingredients_analysis.count || 0} declared
              </span>
            </div>

            {ingredients_analysis.ingredients && ingredients_analysis.ingredients.length > 0 ? (
              <div className="space-y-2.5 max-h-72 overflow-y-auto pr-1">
                {ingredients_analysis.ingredients.map((ing, idx) => (
                  <div
                    key={idx}
                    className="p-2.5 rounded-xl bg-slate-950 border border-slate-800/80 text-xs flex items-center justify-between"
                  >
                    <div>
                      <span className="font-medium text-slate-200">{ing.name}</span>
                      {ing.percentage !== null && (
                        <span className="ml-2 font-mono text-cyan-400 font-bold">
                          ({ing.percentage}%)
                        </span>
                      )}
                      {ing.additive_class && (
                        <span className="block text-[11px] text-amber-400 mt-0.5">
                          {ing.additive_code ? `${ing.additive_code}: ` : ""}{ing.additive_class}
                        </span>
                      )}
                    </div>
                    <span
                      className={`text-[10px] px-2 py-0.5 rounded font-bold uppercase ${
                        ing.is_additive
                          ? "bg-amber-950 text-amber-300 border border-amber-800"
                          : "bg-slate-800 text-slate-400"
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

          <div className="mt-4 pt-3 border-t border-slate-800 text-[11px] text-slate-400 flex items-center justify-between">
            <span>INS Codes Mapped: {ingredients_analysis.additives_detected?.length || 0}</span>
            <span>QUID % Declared: {ingredients_analysis.quid_percentages_declared ? "Yes ✓" : "No"}</span>
          </div>
        </div>

        {/* ALLERGEN MATRIX (3 Cols) */}
        <div className="lg:col-span-3 bg-slate-900 border border-slate-800 rounded-3xl p-6 shadow-lg flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <span>⚠️</span> Allergen Check
              </h3>
              <span className="text-xs text-slate-400">Reg 5(14)</span>
            </div>

            <div className="space-y-2 max-h-72 overflow-y-auto pr-1">
              {allergen_analysis.allergen_breakdown?.map((item, idx) => (
                <div
                  key={idx}
                  className="p-2 rounded-xl bg-slate-950 border border-slate-800/80 text-xs flex items-center justify-between"
                >
                  <span className="text-slate-300 font-medium truncate max-w-[130px]">{item.name}</span>
                  <span
                    className={`text-[10px] px-2 py-0.5 rounded font-bold uppercase ${
                      item.status === "CONTAINS"
                        ? "bg-rose-950 text-rose-300 border border-rose-800"
                        : item.status === "POSSIBLE_SOURCE"
                        ? "bg-amber-950 text-amber-300 border border-amber-800"
                        : item.status === "UNABLE_TO_DETERMINE"
                        ? "bg-purple-950 text-purple-300 border border-purple-800"
                        : "bg-slate-900 text-slate-500"
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

          <p className="mt-4 pt-3 border-t border-slate-800 text-[10px] text-slate-500 leading-tight">
            *Lack of detection on label does not certify product is allergen-free.
          </p>
        </div>

        {/* NUTRITION FACTS (4 Cols) */}
        <div className="lg:col-span-4 bg-slate-900 border border-slate-800 rounded-3xl p-6 shadow-lg flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <span>🥗</span> Nutritional Info
              </h3>
              <span className="text-xs text-slate-400 font-mono">
                {nutrition_facts.basis || "per 100g"}
              </span>
            </div>

            {nutrition_facts.found ? (
              <div className="space-y-1.5 text-xs max-h-72 overflow-y-auto pr-1">
                {Object.entries(nutrition_facts.nutrients || {}).map(([k, n]) => (
                  <div
                    key={k}
                    className="flex items-center justify-between py-1.5 px-2.5 rounded-lg bg-slate-950 border border-slate-800/60"
                  >
                    <span className="text-slate-400 capitalize">
                      {k.replace(/_/g, " ")}:
                    </span>
                    <span className="font-mono font-bold text-slate-200">
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
            <div className="mt-3 p-2 rounded-xl bg-amber-950/40 border border-amber-800 text-[11px] text-amber-300">
              ⚠️ {nutrition_facts.consistency_warnings[0]}
            </div>
          )}
        </div>
      </div>

      {/* 5. INTERACTIVE STATUTORY EVIDENCE CHECKLIST */}
      <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 sm:p-8 shadow-xl">
        <div className="flex flex-wrap items-center justify-between gap-4 mb-6">
          <div>
            <h3 className="text-xl font-bold text-white flex items-center gap-2">
              <span>🔍</span> FSSAI Statutory Declarations Checklist
            </h3>
            <p className="text-xs text-slate-400 mt-1">
              Click any statutory rule to open the verifiable evidentiary trace (*Why, What was read, Where found*).
            </p>
          </div>

          <div className="flex gap-2 text-xs">
            {["ALL", "ISSUES", "PASS"].map((btn) => (
              <button
                key={btn}
                onClick={() => setFilterStatus(btn)}
                className={`px-3 py-1.5 rounded-xl font-semibold transition ${
                  filterStatus === btn
                    ? "bg-blue-600 text-white"
                    : "bg-slate-800 text-slate-400 hover:text-white"
                }`}
              >
                {btn === "ALL" ? "All Rules" : btn === "ISSUES" ? "Issues Only" : "Passed"}
              </button>
            ))}
          </div>
        </div>

        <div className="divide-y divide-slate-800/70">
          {filteredChecklist.map((item, idx) => (
            <div
              key={idx}
              onClick={() => setSelectedEvidence(item)}
              className="py-3.5 px-3 rounded-xl hover:bg-slate-800/50 cursor-pointer transition flex items-center justify-between gap-4 group"
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
                    <span className="text-sm font-bold text-slate-200 group-hover:text-blue-400 transition">
                      {item.title}
                    </span>
                    <span className="text-xs font-mono text-slate-500">[{item.citation}]</span>
                  </div>
                  <p className="text-xs text-slate-400 line-clamp-1 mt-0.5">
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
                <span className="text-xs text-slate-500 group-hover:translate-x-1 transition">
                  Details →
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* 6. TRANSPARENT EVIDENCE MODAL */}
      {selectedEvidence && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-3xl max-w-2xl w-full p-6 sm:p-8 shadow-2xl space-y-5">
            <div className="flex items-center justify-between pb-4 border-b border-slate-800">
              <div>
                <span className="text-xs font-mono text-blue-400">
                  Citation: {selectedEvidence.citation} ({selectedEvidence.rule_id})
                </span>
                <h3 className="text-xl font-bold text-white mt-0.5">{selectedEvidence.title}</h3>
              </div>
              <button
                onClick={() => setSelectedEvidence(null)}
                className="text-slate-400 hover:text-white p-2 rounded-xl hover:bg-slate-800"
              >
                ✕
              </button>
            </div>

            <div className="space-y-4 text-xs">
              {/* STATUS */}
              <div className="flex items-center justify-between p-3.5 bg-slate-950 rounded-xl border border-slate-800">
                <span className="text-slate-400">Evaluated Compliance Status:</span>
                <span
                  className={`px-3 py-1 rounded-full font-bold uppercase border ${getStatusBadge(
                    selectedEvidence.status
                  )}`}
                >
                  {selectedEvidence.status}
                </span>
              </div>

              {/* WHY? */}
              <div className="p-4 bg-slate-950 rounded-xl border border-slate-800">
                <h4 className="font-bold text-slate-300 uppercase tracking-wider text-[11px] mb-1">
                  1. Why was this checked? (Statutory Requirement)
                </h4>
                <p className="text-slate-400 leading-relaxed">{selectedEvidence.why}</p>
              </div>

              {/* WHAT WAS READ? */}
              <div className="p-4 bg-slate-950 rounded-xl border border-slate-800">
                <h4 className="font-bold text-slate-300 uppercase tracking-wider text-[11px] mb-1">
                  2. What was read from the package? (Extracted Text / Value)
                </h4>
                <p className="font-mono text-emerald-300 text-sm bg-slate-900/80 p-2.5 rounded-lg border border-slate-800">
                  {selectedEvidence.what_was_read || "No visible text detected for this declaration."}
                </p>
              </div>

              {/* WHERE WAS IT FOUND? */}
              <div className="p-4 bg-slate-950 rounded-xl border border-slate-800 flex items-center justify-between">
                <div>
                  <h4 className="font-bold text-slate-300 uppercase tracking-wider text-[11px]">
                    3. Where was it found?
                  </h4>
                  <p className="text-slate-400 mt-0.5">{selectedEvidence.where_found}</p>
                </div>
                <div className="text-right">
                  <span className="text-slate-500 block">OCR Confidence</span>
                  <span className="font-mono font-bold text-slate-200">
                    {Math.round((selectedEvidence.ocr_confidence || 0.85) * 100)}%
                  </span>
                </div>
              </div>

              {/* RECOMMENDATION IF ANY */}
              {selectedEvidence.recommendation && (
                <div className="p-4 bg-rose-950/20 border border-rose-900/40 rounded-xl">
                  <h4 className="font-bold text-rose-400 uppercase tracking-wider text-[11px] mb-1">
                    Corrective Recommendation
                  </h4>
                  <p className="text-slate-300">{selectedEvidence.recommendation}</p>
                </div>
              )}
            </div>

            <div className="pt-2 flex justify-end">
              <button
                onClick={() => setSelectedEvidence(null)}
                className="bg-blue-600 hover:bg-blue-500 text-white px-6 py-2.5 rounded-xl font-bold text-sm shadow-lg shadow-blue-600/20"
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
          className="bg-slate-800 hover:bg-slate-700 text-slate-200 px-6 py-3 rounded-xl font-bold text-sm border border-slate-700 transition"
        >
          ← Inspect Another Food Package
        </button>

        <button
          onClick={() => window.print()}
          className="bg-blue-600 hover:bg-blue-500 text-white px-6 py-3 rounded-xl font-bold text-sm shadow-lg shadow-blue-600/20 transition flex items-center gap-2"
        >
          <span>🖨️</span> Export FSSAI Audit Summary
        </button>
      </div>
    </div>
  );
}

export default FSSAIChecklistReport;
