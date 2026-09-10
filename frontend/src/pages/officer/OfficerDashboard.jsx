import { useState, useEffect, useCallback } from "react";
import axios from "axios";
import Navbar from "../../components/Navbar";

const API_BASE_URL = "http://localhost:8000";

function OfficerDashboard() {
  const [stats, setStats] = useState({
    total_inspections: 0,
    compliant: 0,
    review_required: 0,
    non_compliant: 0,
    total_violations: 0,
    pending_complaints: 0,
  });

  const [inspections, setInspections] = useState([]);
  const [complaints, setComplaints] = useState([]);
  const [activeTab, setActiveTab] = useState("INSPECTIONS"); // INSPECTIONS | COMPLAINTS
  const [loading, setLoading] = useState(true);
  const [selectedInspection, setSelectedInspection] = useState(null);

  const getAuthHeaders = () => {
    const token = localStorage.getItem("token");
    return token ? { Authorization: `Bearer ${token}` } : {};
  };

  const loadData = useCallback(async () => {
    try {
      const headers = getAuthHeaders();

      const [statsRes, inspRes, compRes] = await Promise.allSettled([
        axios.get(`${API_BASE_URL}/inspections/stats`),
        axios.get(`${API_BASE_URL}/inspections/`, { headers }),
        axios.get(`${API_BASE_URL}/complaints/`, { headers }),
      ]);

      if (statsRes.status === "fulfilled") setStats(statsRes.value.data);
      if (inspRes.status === "fulfilled") setInspections(inspRes.value.data || []);
      if (compRes.status === "fulfilled") setComplaints(compRes.value.data || []);
    } catch (err) {
      console.error("Failed to load officer dashboard data", err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleSelectInspection = async (scanId) => {
    try {
      const headers = getAuthHeaders();
      const res = await axios.get(`${API_BASE_URL}/inspections/${scanId}`, { headers });
      setSelectedInspection(res.data);
    } catch (err) {
      console.error("Failed to load inspection detail", err);
      // Fallback to scans endpoint
      try {
        const headers = getAuthHeaders();
        const res = await axios.get(`${API_BASE_URL}/scans/${scanId}`, { headers });
        setSelectedInspection(res.data);
      } catch {
        alert("Failed to load inspection evidence.");
      }
    }
  };

  const handleUpdateComplaintStatus = async (id, newStatus) => {
    try {
      const headers = getAuthHeaders();
      await axios.patch(`${API_BASE_URL}/complaints/${id}/status`, { status: newStatus }, { headers });
      loadData();
    } catch (err) {
      console.error(err);
      alert("Failed to update grievance status.");
    }
  };

  const downloadPdf = async (scanId) => {
    try {
      const headers = getAuthHeaders();
      const res = await axios.get(`${API_BASE_URL}/scans/${scanId}/report/pdf`, {
        headers,
        responseType: "blob"
      });
      const blob = new Blob([res.data], { type: "application/pdf" });
      const link = document.createElement("a");
      link.href = window.URL.createObjectURL(blob);
      link.download = `mitra_metrology_inspection_${scanId}.pdf`;
      link.click();
    } catch (err) {
      console.error(err);
      alert("Failed to download PDF report.");
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-white flex flex-col">
      <Navbar role="officer" />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 py-8">
        <div className="flex flex-wrap items-center justify-between gap-4 mb-8">
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs px-2.5 py-1 rounded bg-emerald-950 text-emerald-400 font-bold border border-emerald-800">
                OFFICER CONSOLE
              </span>
              <span className="text-xs text-slate-400">Department of Legal Metrology</span>
            </div>
            <h2 className="text-3xl font-bold tracking-tight mt-1">Inspection & Legal Enforcement Dashboard</h2>
          </div>

          <button
            onClick={loadData}
            className="bg-slate-800 hover:bg-slate-700 text-slate-200 px-4 py-2 rounded-xl text-xs font-semibold border border-slate-700 flex items-center gap-2 transition"
          >
            <span>🔄</span> Refresh Data
          </button>
        </div>

        {/* Step 27: 4 KPI Cards */}
        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-5 mb-8">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-lg">
            <span className="text-xs text-slate-400 font-medium block">Total Inspections</span>
            <div className="flex items-baseline justify-between mt-2">
              <span className="text-3xl font-black text-white">
                {stats.total_inspections ?? stats.total_scans ?? 0}
              </span>
              <span className="text-xl">📦</span>
            </div>
          </div>

          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-lg">
            <span className="text-xs text-slate-400 font-medium block">Compliant Packages</span>
            <div className="flex items-baseline justify-between mt-2">
              <span className="text-3xl font-black text-emerald-400">
                {stats.compliant ?? stats.compliant_scans ?? 0}
              </span>
              <span className="text-xs px-2 py-0.5 rounded bg-emerald-950 text-emerald-300 border border-emerald-800">
                Valid
              </span>
            </div>
          </div>

          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-lg">
            <span className="text-xs text-slate-400 font-medium block">Review Required</span>
            <div className="flex items-baseline justify-between mt-2">
              <span className="text-3xl font-black text-amber-400">
                {stats.review_required ?? 0}
              </span>
              <span className="text-xs px-2 py-0.5 rounded bg-amber-950 text-amber-300 border border-amber-800">
                Uncertain
              </span>
            </div>
          </div>

          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-lg">
            <span className="text-xs text-slate-400 font-medium block">Non-Compliant Violations</span>
            <div className="flex items-baseline justify-between mt-2">
              <span className="text-3xl font-black text-rose-400">
                {stats.non_compliant ?? stats.non_compliant_scans ?? 0}
              </span>
              <span className="text-xl">⚠️</span>
            </div>
          </div>
        </div>

        {/* Tab Selection */}
        <div className="flex items-center gap-4 border-b border-slate-800 pb-4 mb-6">
          <button
            onClick={() => setActiveTab("INSPECTIONS")}
            className={`text-sm font-bold pb-1 transition flex items-center gap-2 ${
              activeTab === "INSPECTIONS"
                ? "text-blue-400 border-b-2 border-blue-400"
                : "text-slate-400 hover:text-white"
            }`}
          >
            <span>🔍</span> Inspections & Audits ({inspections.length})
          </button>

          <button
            onClick={() => setActiveTab("COMPLAINTS")}
            className={`text-sm font-bold pb-1 transition flex items-center gap-2 ${
              activeTab === "COMPLAINTS"
                ? "text-emerald-400 border-b-2 border-emerald-400"
                : "text-slate-400 hover:text-white"
            }`}
          >
            <span>📢</span> Consumer Grievance Queue ({complaints.length})
          </button>
        </div>

        {/* Tab 1: Inspections Table */}
        {activeTab === "INSPECTIONS" && (
          <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden shadow-xl">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="border-b border-slate-800 text-xs uppercase text-slate-400 bg-slate-950/60">
                    <th className="py-3 px-5 font-semibold">ID</th>
                    <th className="py-3 px-5 font-semibold">Product Name</th>
                    <th className="py-3 px-5 font-semibold">Status</th>
                    <th className="py-3 px-5 font-semibold">Date</th>
                    <th className="py-3 px-5 font-semibold text-right">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {loading ? (
                    <tr>
                      <td colSpan="5" className="py-8 text-center text-slate-400">
                        Loading inspections...
                      </td>
                    </tr>
                  ) : inspections.length === 0 ? (
                    <tr>
                      <td colSpan="5" className="py-8 text-center text-slate-500">
                        No product inspections recorded yet.
                      </td>
                    </tr>
                  ) : (
                    inspections.map((insp) => (
                      <tr
                        key={insp.id}
                        onClick={() => handleSelectInspection(insp.id)}
                        className="hover:bg-slate-800/50 transition cursor-pointer"
                      >
                        <td className="py-3.5 px-5 font-mono text-xs text-blue-400">#{insp.id}</td>
                        <td className="py-3.5 px-5 font-medium text-slate-200">
                          {insp.product_name}
                          {insp.manufacturer && (
                            <span className="block text-xs text-slate-400">{insp.manufacturer}</span>
                          )}
                        </td>
                        <td className="py-3.5 px-5">
                          <span
                            className={`text-xs px-2.5 py-0.5 rounded-full font-bold uppercase ${
                              insp.status === "COMPLIANT"
                                ? "bg-emerald-950 text-emerald-400 border border-emerald-800"
                                : insp.status === "NON-COMPLIANT" || insp.status === "NON_COMPLIANT"
                                ? "bg-rose-950 text-rose-400 border border-rose-800"
                                : "bg-amber-950 text-amber-400 border border-amber-800"
                            }`}
                          >
                            {insp.status}
                          </span>
                        </td>
                        <td className="py-3.5 px-5 text-xs text-slate-400 font-mono">
                          {insp.date || (insp.created_at ? new Date(insp.created_at).toLocaleDateString() : "-")}
                        </td>
                        <td className="py-3.5 px-5 text-right">
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              downloadPdf(insp.id);
                            }}
                            className="text-xs bg-slate-800 hover:bg-blue-600 text-slate-300 hover:text-white px-3 py-1 rounded-lg border border-slate-700 transition"
                          >
                            📥 PDF Report
                          </button>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Tab 2: Complaints Table */}
        {activeTab === "COMPLAINTS" && (
          <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden shadow-xl">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="border-b border-slate-800 text-xs uppercase text-slate-400 bg-slate-950/60">
                    <th className="py-3 px-5 font-semibold">Ref ID</th>
                    <th className="py-3 px-5 font-semibold">Commodity</th>
                    <th className="py-3 px-5 font-semibold">Grievance Details</th>
                    <th className="py-3 px-5 font-semibold">Status</th>
                    <th className="py-3 px-5 font-semibold text-right">Officer Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {complaints.length === 0 ? (
                    <tr>
                      <td colSpan="5" className="py-8 text-center text-slate-500">
                        No consumer grievances registered.
                      </td>
                    </tr>
                  ) : (
                    complaints.map((c) => (
                      <tr key={c.id} className="hover:bg-slate-800/40 transition">
                        <td className="py-3.5 px-5 font-mono text-xs text-emerald-400">#GRIEV-{c.id}</td>
                        <td className="py-3.5 px-5 font-medium text-slate-200">
                          {c.product_name}
                          {c.manufacturer && (
                            <span className="block text-xs text-slate-400">{c.manufacturer}</span>
                          )}
                        </td>
                        <td className="py-3.5 px-5 text-xs text-slate-300 max-w-xs">
                          {c.description}
                        </td>
                        <td className="py-3.5 px-5">
                          <span
                            className={`text-xs px-2.5 py-0.5 rounded-full font-bold uppercase ${
                              c.status === "RESOLVED"
                                ? "bg-emerald-950 text-emerald-400 border border-emerald-800"
                                : c.status === "UNDER_REVIEW" || c.status === "INVESTIGATING"
                                ? "bg-blue-950 text-blue-400 border border-blue-800"
                                : "bg-amber-950 text-amber-400 border border-amber-800"
                            }`}
                          >
                            {c.status}
                          </span>
                        </td>
                        <td className="py-3.5 px-5 text-right space-x-2">
                          {c.status !== "RESOLVED" && (
                            <button
                              onClick={() => handleUpdateComplaintStatus(c.id, "RESOLVED")}
                              className="text-xs bg-emerald-600/20 hover:bg-emerald-600 text-emerald-300 hover:text-white px-2.5 py-1 rounded-lg border border-emerald-700/50 transition"
                            >
                              Resolve ✓
                            </button>
                          )}
                          {c.status === "PENDING" && (
                            <button
                              onClick={() => handleUpdateComplaintStatus(c.id, "UNDER_REVIEW")}
                              className="text-xs bg-blue-600/20 hover:bg-blue-600 text-blue-300 hover:text-white px-2.5 py-1 rounded-lg border border-blue-700/50 transition"
                            >
                              Investigate 🔍
                            </button>
                          )}
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Step 28: Officer Evidence-First Inspection Details Modal */}
        {selectedInspection && (
          <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4 overflow-y-auto">
            <div className="bg-slate-900 border border-slate-800 rounded-3xl max-w-3xl w-full max-h-[90vh] overflow-y-auto p-6 sm:p-8 shadow-2xl">
              <div className="flex items-start justify-between border-b border-slate-800 pb-4 mb-6">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-mono text-slate-400">Inspection #{selectedInspection.scan_id || selectedInspection.id}</span>
                    <span
                      className={`text-xs px-2.5 py-0.5 rounded-full font-bold uppercase ${
                        selectedInspection.status === "COMPLIANT"
                          ? "bg-emerald-950 text-emerald-400 border border-emerald-800"
                          : selectedInspection.status === "NON-COMPLIANT" || selectedInspection.status === "NON_COMPLIANT"
                          ? "bg-rose-950 text-rose-400 border border-rose-800"
                          : "bg-amber-950 text-amber-400 border border-amber-800"
                      }`}
                    >
                      {selectedInspection.status}
                    </span>
                  </div>
                  <h3 className="text-2xl font-bold text-white mt-1">Official Packaging Evidence Dossier</h3>
                  <p className="text-xs text-slate-400">{selectedInspection.date || selectedInspection.created_at}</p>
                </div>
                <button
                  onClick={() => setSelectedInspection(null)}
                  className="text-slate-400 hover:text-white text-xl p-1"
                >
                  ✕
                </button>
              </div>

              {/* Evidence Flow: Image -> OCR -> Fields -> Confidence -> Rules -> Violations */}
              <div className="space-y-6">
                {/* 1. Original Image */}
                <div>
                  <h4 className="text-xs uppercase tracking-wider text-slate-400 font-bold mb-2">
                    1. Original Packaging Photo
                  </h4>
                  <div className="rounded-xl overflow-hidden bg-slate-950 border border-slate-800 p-2 flex justify-center">
                    {selectedInspection.evidence?.image_url ? (
                      <img
                        src={`http://localhost:8000${selectedInspection.evidence.image_url}`}
                        alt="Evidence"
                        className="max-h-64 object-contain rounded"
                      />
                    ) : (
                      <div className="py-12 text-slate-500 text-xs">Image path: {selectedInspection.evidence?.image_path || "Stored on server"}</div>
                    )}
                  </div>
                </div>

                {/* 2. Extracted Fields & Confidence */}
                <div>
                  <h4 className="text-xs uppercase tracking-wider text-slate-400 font-bold mb-2">
                    2. OCR Declarations & Confidence Ratings
                  </h4>
                  <div className="bg-slate-950 border border-slate-800 rounded-xl divide-y divide-slate-800 text-xs">
                    {Object.entries(selectedInspection.fields || {}).map(([key, val]) => {
                      const conf = selectedInspection.confidences?.[key]?.confidence ?? selectedInspection.confidences?.[key] ?? 0.90;
                      return (
                        <div key={key} className="p-3 flex items-center justify-between">
                          <span className="text-slate-400 font-medium capitalize">{key.replace(/_/g, " ")}</span>
                          <div className="flex items-center gap-3">
                            <span className="text-slate-200 font-mono font-semibold">
                              {typeof val === "object" ? JSON.stringify(val) : String(val)}
                            </span>
                            <span className={`px-2 py-0.5 rounded font-mono font-bold ${conf >= 0.9 ? "bg-emerald-950 text-emerald-400 border border-emerald-800" : conf >= 0.7 ? "bg-amber-950 text-amber-400 border border-amber-800" : "bg-rose-950 text-rose-400 border border-rose-800"}`}>
                              {Math.round(conf * 100)}%
                            </span>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>

                {/* 3. OCR Raw Text */}
                {selectedInspection.ocr_text && (
                  <div>
                    <h4 className="text-xs uppercase tracking-wider text-slate-400 font-bold mb-2">
                      3. Packaging Raw OCR Text
                    </h4>
                    <pre className="p-3 bg-slate-950 border border-slate-800 rounded-xl text-xs font-mono text-slate-300 max-h-32 overflow-y-auto whitespace-pre-wrap">
                      {selectedInspection.ocr_text}
                    </pre>
                  </div>
                )}

                {/* 4. Violations */}
                <div>
                  <h4 className="text-xs uppercase tracking-wider text-rose-400 font-bold mb-2">
                    4. Statutory Violations ({selectedInspection.violations?.length || 0})
                  </h4>
                  {!selectedInspection.violations || selectedInspection.violations.length === 0 ? (
                    <div className="p-3 bg-emerald-950/30 border border-emerald-900/40 text-emerald-300 rounded-xl text-xs">
                      ✓ No statutory violations detected. Package fully adheres to the 8 Legal Metrology and FSSAI rules.
                    </div>
                  ) : (
                    <div className="space-y-2">
                      {selectedInspection.violations.map((v, i) => (
                        <div key={i} className="p-3 bg-rose-950/30 border border-rose-900/50 rounded-xl text-xs flex justify-between items-start">
                          <div>
                            <span className="font-bold text-rose-300 uppercase">{v.field}: </span>
                            <span className="text-slate-200">{v.description}</span>
                          </div>
                          <span className="text-[10px] uppercase font-bold px-2 py-0.5 bg-rose-900 text-rose-200 rounded">
                            {v.severity}
                          </span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>

              {/* Action Footer */}
              <div className="flex justify-between items-center pt-6 mt-6 border-t border-slate-800">
                <button
                  onClick={() => downloadPdf(selectedInspection.scan_id || selectedInspection.id)}
                  className="bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold px-5 py-2.5 rounded-xl shadow-lg shadow-emerald-600/20 flex items-center gap-2"
                >
                  <span>📥</span> Download Certified PDF Inspection Report
                </button>
                <button
                  onClick={() => setSelectedInspection(null)}
                  className="bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold px-4 py-2.5 rounded-xl"
                >
                  Close Dossier
                </button>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

export default OfficerDashboard;
