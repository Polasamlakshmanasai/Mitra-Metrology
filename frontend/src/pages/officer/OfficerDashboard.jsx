import { useState, useEffect, useCallback } from "react";
import axios from "axios";
import { Search, AlertTriangle, ShieldCheck, Download, RefreshCw, Eye, Package, X, CheckCircle, FileText, Scale } from "lucide-react";
import Navbar from "../../components/Navbar";
import Footer from "../../components/Footer";
import API_BASE_URL from "../../config";

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
    setLoading(true);
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
    <div className="min-h-screen bg-[#FFFFFF] flex flex-col justify-between">
      <Navbar role="officer" />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        
        {/* Header Section */}
        <div className="flex flex-wrap items-center justify-between gap-4 mb-8 pb-4 border-b border-[#D5DCE5]">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="text-[11px] px-2 py-0.5 rounded bg-[#F5F7FA] text-[#174A7E] font-bold border border-[#D5DCE5]">
                OFFICER CONSOLE
              </span>
              <span className="text-xs font-semibold text-[#64748B]">Legal Metrology Regulatory Department</span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-bold text-[#183153] tracking-tight">
              Inspection & Regulatory Enforcement Dashboard
            </h1>
          </div>

          <button
            onClick={loadData}
            className="bg-white border border-[#D5DCE5] hover:bg-[#F5F7FA] text-[#183153] px-3.5 py-2 rounded text-xs font-semibold flex items-center gap-2 shadow-xs transition-colors"
          >
            <RefreshCw size={14} className="text-[#174A7E]" />
            Refresh Records
          </button>
        </div>

        {/* Metrics Grid */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          <div className="bg-[#F5F7FA] border border-[#D5DCE5] rounded p-5">
            <div className="flex items-center justify-between mb-1.5">
              <span className="text-[11px] font-bold text-[#64748B] uppercase tracking-wider">Total Audits</span>
              <FileText size={15} className="text-[#174A7E]" />
            </div>
            <div className="text-3xl font-bold text-[#183153]">
              {stats.total_inspections ?? stats.total_scans ?? 0}
            </div>
            <span className="text-[11px] text-[#64748B] mt-1 block">Packaged commodity scans</span>
          </div>

          <div className="bg-[#F5F7FA] border border-[#D5DCE5] rounded p-5">
            <div className="flex items-center justify-between mb-1.5">
              <span className="text-[11px] font-bold text-[#15803D] uppercase tracking-wider">Compliant</span>
              <ShieldCheck size={15} className="text-[#15803D]" />
            </div>
            <div className="text-3xl font-bold text-[#15803D]">
              {stats.compliant ?? stats.compliant_scans ?? 0}
            </div>
            <span className="text-[11px] text-[#64748B] mt-1 block">Rule 6 declarations verified</span>
          </div>

          <div className="bg-[#F5F7FA] border border-[#D5DCE5] rounded p-5">
            <div className="flex items-center justify-between mb-1.5">
              <span className="text-[11px] font-bold text-[#B45309] uppercase tracking-wider">Review Pending</span>
              <Search size={15} className="text-[#B45309]" />
            </div>
            <div className="text-3xl font-bold text-[#B45309]">
              {stats.review_required ?? 0}
            </div>
            <span className="text-[11px] text-[#64748B] mt-1 block">Awaiting officer / user review</span>
          </div>

          <div className="bg-[#F5F7FA] border border-[#D5DCE5] rounded p-5">
            <div className="flex items-center justify-between mb-1.5">
              <span className="text-[11px] font-bold text-[#B91C1C] uppercase tracking-wider">Non-Compliant</span>
              <AlertTriangle size={15} className="text-[#B91C1C]" />
            </div>
            <div className="text-3xl font-bold text-[#B91C1C]">
              {stats.non_compliant ?? stats.non_compliant_scans ?? 0}
            </div>
            <span className="text-[11px] text-[#64748B] mt-1 block">Actionable statutory violations</span>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex items-center gap-4 border-b border-[#D5DCE5] mb-6">
          <button
            onClick={() => setActiveTab("INSPECTIONS")}
            className={`text-xs sm:text-sm font-bold pb-3 px-2 transition-colors flex items-center gap-2 border-b-2 ${
              activeTab === "INSPECTIONS"
                ? "text-[#174A7E] border-[#174A7E]"
                : "text-[#64748B] border-transparent hover:text-[#183153]"
            }`}
          >
            <Search size={15} /> Inspections & Audits ({inspections.length})
          </button>

          <button
            onClick={() => setActiveTab("COMPLAINTS")}
            className={`text-xs sm:text-sm font-bold pb-3 px-2 transition-colors flex items-center gap-2 border-b-2 ${
              activeTab === "COMPLAINTS"
                ? "text-[#174A7E] border-[#174A7E]"
                : "text-[#64748B] border-transparent hover:text-[#183153]"
            }`}
          >
            <AlertTriangle size={15} /> Consumer Grievances ({complaints.length})
          </button>
        </div>

        {/* Tab 1: Inspections Table */}
        {activeTab === "INSPECTIONS" && (
          <div className="bg-white border border-[#D5DCE5] rounded shadow-sm overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs whitespace-nowrap">
                <thead className="bg-[#F5F7FA] text-[#64748B] uppercase tracking-wider font-semibold border-b border-[#D5DCE5]">
                  <tr>
                    <th className="py-3 px-6">Audit ID</th>
                    <th className="py-3 px-6">Commodity / Manufacturer</th>
                    <th className="py-3 px-6">Compliance Verdict</th>
                    <th className="py-3 px-6">Inspection Date</th>
                    <th className="py-3 px-6 text-right">Statutory Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#D5DCE5] text-[#183153]">
                  {loading ? (
                    <tr>
                      <td colSpan="5" className="py-12 text-center text-[#64748B]">
                        Loading inspection data from database...
                      </td>
                    </tr>
                  ) : inspections.length === 0 ? (
                    <tr>
                      <td colSpan="5" className="py-12 text-center text-[#64748B]">
                        No product inspections recorded in system.
                      </td>
                    </tr>
                  ) : (
                    inspections.map((insp) => (
                      <tr
                        key={insp.id}
                        onClick={() => handleSelectInspection(insp.id)}
                        className="hover:bg-[#F5F7FA] transition-colors cursor-pointer group"
                      >
                        <td className="py-3.5 px-6 font-mono text-[#64748B] font-semibold">#{insp.id}</td>
                        <td className="py-3.5 px-6">
                          <p className="font-bold text-[#183153]">{insp.product_name || "Packaged Commodity"}</p>
                          {insp.manufacturer && (
                            <p className="text-[11px] text-[#64748B]">{insp.manufacturer}</p>
                          )}
                        </td>
                        <td className="py-3.5 px-6">
                          <span
                            className={`inline-flex items-center px-2 py-0.5 rounded text-[11px] font-semibold border ${
                              insp.status === "COMPLIANT"
                                ? "bg-[#DCFCE7] text-[#15803D] border-[#BBF7D0]"
                                : insp.status === "NON-COMPLIANT" || insp.status === "NON_COMPLIANT"
                                ? "bg-[#FEE2E2] text-[#B91C1C] border-[#FECACA]"
                                : "bg-[#FEF3C7] text-[#B45309] border-[#FDE68A]"
                            }`}
                          >
                            {insp.status.replace("_", "-")}
                          </span>
                        </td>
                        <td className="py-3.5 px-6 text-[#64748B]">
                          {insp.date || (insp.created_at ? new Date(insp.created_at).toLocaleDateString() : "--")}
                        </td>
                        <td className="py-3.5 px-6 text-right space-x-2" onClick={(e) => e.stopPropagation()}>
                          <button
                            onClick={() => handleSelectInspection(insp.id)}
                            className="px-2.5 py-1 bg-white border border-[#D5DCE5] hover:bg-[#F5F7FA] text-[#174A7E] text-xs font-semibold rounded"
                          >
                            Examine
                          </button>
                          <button
                            onClick={() => downloadPdf(insp.id)}
                            className="px-2.5 py-1 bg-[#174A7E] hover:bg-[#133D68] text-white text-xs font-semibold rounded inline-flex items-center gap-1 shadow-xs"
                            title="Download Legal Metrology PDF Report"
                          >
                            <Download size={12} /> PDF
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
          <div className="bg-white border border-[#D5DCE5] rounded shadow-sm overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs whitespace-nowrap">
                <thead className="bg-[#F5F7FA] text-[#64748B] uppercase tracking-wider font-semibold border-b border-[#D5DCE5]">
                  <tr>
                    <th className="py-3 px-6">Grievance Ref</th>
                    <th className="py-3 px-6">Commodity / Manufacturer</th>
                    <th className="py-3 px-6">Allegation Summary</th>
                    <th className="py-3 px-6">Status</th>
                    <th className="py-3 px-6 text-right">Regulatory Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#D5DCE5] text-[#183153]">
                  {loading ? (
                    <tr>
                      <td colSpan="5" className="py-12 text-center text-[#64748B]">
                        Loading consumer grievances...
                      </td>
                    </tr>
                  ) : complaints.length === 0 ? (
                    <tr>
                      <td colSpan="5" className="py-12 text-center text-[#64748B]">
                        No consumer grievances currently registered.
                      </td>
                    </tr>
                  ) : (
                    complaints.map((c) => (
                      <tr key={c.id} className="hover:bg-[#F5F7FA] transition-colors">
                        <td className="py-3.5 px-6 font-mono text-[#64748B] font-semibold">#GRIEV-{c.id}</td>
                        <td className="py-3.5 px-6">
                          <p className="font-bold text-[#183153]">{c.product_name || "Unknown Product"}</p>
                          {c.manufacturer && (
                            <p className="text-[11px] text-[#64748B]">{c.manufacturer}</p>
                          )}
                        </td>
                        <td className="py-3.5 px-6 max-w-[280px] truncate text-[#475569]" title={c.description}>
                          {c.description}
                        </td>
                        <td className="py-3.5 px-6">
                          <span
                            className={`inline-flex items-center px-2 py-0.5 rounded text-[11px] font-semibold border ${
                              c.status === "RESOLVED"
                                ? "bg-[#DCFCE7] text-[#15803D] border-[#BBF7D0]"
                                : c.status === "UNDER_REVIEW" || c.status === "INVESTIGATING"
                                ? "bg-[#EDF2F7] text-[#174A7E] border-[#CBD5E1]"
                                : "bg-[#FEF3C7] text-[#B45309] border-[#FDE68A]"
                            }`}
                          >
                            {c.status.replace("_", " ")}
                          </span>
                        </td>
                        <td className="py-3.5 px-6 text-right space-x-2">
                          {c.status !== "RESOLVED" && (
                            <button
                              onClick={() => handleUpdateComplaintStatus(c.id, "RESOLVED")}
                              className="text-xs bg-white border border-[#BBF7D0] text-[#15803D] hover:bg-[#DCFCE7] px-2.5 py-1 rounded font-semibold transition-colors"
                            >
                              Mark Resolved
                            </button>
                          )}
                          {c.status === "PENDING" && (
                            <button
                              onClick={() => handleUpdateComplaintStatus(c.id, "UNDER_REVIEW")}
                              className="text-xs bg-white border border-[#CBD5E1] text-[#174A7E] hover:bg-[#F5F7FA] px-2.5 py-1 rounded font-semibold transition-colors"
                            >
                              Initiate Investigation
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

        {/* Inspection Details Dossier Modal */}
        {selectedInspection && (
          <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-xs flex items-center justify-center p-4 sm:p-6 overflow-y-auto">
            <div className="bg-white rounded border border-[#D5DCE5] max-w-4xl w-full max-h-[90vh] flex flex-col shadow-xl text-[#183153]">
              
              {/* Modal Header */}
              <div className="flex items-start justify-between border-b border-[#D5DCE5] p-5 bg-[#F5F7FA]">
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-xs font-mono text-[#64748B]">
                      Inspection Record #{selectedInspection.scan_id || selectedInspection.id}
                    </span>
                    <span
                      className={`text-[11px] px-2 py-0.5 rounded font-semibold border uppercase ${
                        selectedInspection.status === "COMPLIANT"
                          ? "bg-[#DCFCE7] text-[#15803D] border-[#BBF7D0]"
                          : selectedInspection.status === "NON-COMPLIANT" || selectedInspection.status === "NON_COMPLIANT"
                          ? "bg-[#FEE2E2] text-[#B91C1C] border-[#FECACA]"
                          : "bg-[#FEF3C7] text-[#B45309] border-[#FDE68A]"
                      }`}
                    >
                      {selectedInspection.status.replace("_", "-")}
                    </span>
                  </div>
                  <h2 className="text-xl font-bold text-[#183153]">Statutory Evidence Dossier</h2>
                  <p className="text-xs text-[#64748B] mt-0.5">
                    {selectedInspection.date || (selectedInspection.created_at ? new Date(selectedInspection.created_at).toLocaleDateString() : "--")}
                  </p>
                </div>
                <button
                  onClick={() => setSelectedInspection(null)}
                  className="p-1.5 text-[#64748B] hover:text-[#183153] hover:bg-white rounded transition-colors"
                >
                  <X size={18} />
                </button>
              </div>

              {/* Modal Body */}
              <div className="flex-1 overflow-y-auto p-6 space-y-6 bg-white">
                
                {/* 1. Evidence Image */}
                <div>
                  <h3 className="text-xs font-bold text-[#183153] uppercase tracking-wider mb-2">
                    1. Photographic Package Label Evidence
                  </h3>
                  <div className="bg-[#F5F7FA] border border-[#D5DCE5] rounded p-3 flex justify-center">
                    {selectedInspection.evidence?.image_url ? (
                      <img
                        src={`${API_BASE_URL}${selectedInspection.evidence.image_url}`}
                        alt="Audited package label"
                        className="max-h-72 object-contain rounded border border-[#D5DCE5] bg-white"
                      />
                    ) : (
                      <div className="py-12 flex flex-col items-center justify-center text-[#94A3B8]">
                        <Package size={40} className="mb-2 opacity-50" />
                        <span className="text-xs">Image path: {selectedInspection.evidence?.image_path || "Stored on secure server"}</span>
                      </div>
                    )}
                  </div>
                </div>

                {/* 2. OCR Fields Table */}
                <div>
                  <h3 className="text-xs font-bold text-[#183153] uppercase tracking-wider mb-2">
                    2. Extracted Declarations & Confidence Evaluation
                  </h3>
                  <div className="border border-[#D5DCE5] rounded overflow-hidden">
                    <table className="w-full text-xs text-left">
                      <thead className="bg-[#F5F7FA] border-b border-[#D5DCE5] text-[#64748B] uppercase font-semibold">
                        <tr>
                          <th className="px-4 py-2.5">Statutory Declaration</th>
                          <th className="px-4 py-2.5">Extracted Value</th>
                          <th className="px-4 py-2.5 text-right">Confidence</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-[#D5DCE5]">
                        {Object.entries(selectedInspection.fields || {}).map(([key, val]) => {
                          const conf = selectedInspection.confidences?.[key]?.confidence ?? selectedInspection.confidences?.[key] ?? 0.85;
                          return (
                            <tr key={key} className="hover:bg-[#F5F7FA]">
                              <td className="px-4 py-2.5 font-semibold text-[#183153] capitalize">
                                {key.replace(/_/g, " ")}
                              </td>
                              <td className="px-4 py-2.5 text-[#183153] font-mono">
                                {typeof val === "object" ? JSON.stringify(val) : String(val || "Not detected")}
                              </td>
                              <td className="px-4 py-2.5 text-right">
                                <span className={`inline-flex items-center px-2 py-0.5 rounded text-[11px] font-mono font-semibold border ${
                                  conf >= 0.85 ? "bg-[#DCFCE7] text-[#15803D] border-[#BBF7D0]" : conf >= 0.6 ? "bg-[#FEF3C7] text-[#B45309] border-[#FDE68A]" : "bg-[#FEE2E2] text-[#B91C1C] border-[#FECACA]"
                                }`}>
                                  {Math.round(conf * 100)}%
                                </span>
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                </div>

                {/* 3. Statutory Violations */}
                <div>
                  <h3 className="text-xs font-bold text-[#183153] uppercase tracking-wider mb-2">
                    3. Statutory Compliance Findings
                  </h3>
                  {!selectedInspection.violations || selectedInspection.violations.length === 0 ? (
                    <div className="p-3.5 bg-[#DCFCE7] border border-[#BBF7D0] text-[#15803D] rounded flex items-start gap-2.5">
                      <CheckCircle size={18} className="shrink-0 mt-0.5" />
                      <div>
                        <p className="font-bold text-xs">No statutory violations detected.</p>
                        <p className="text-xs mt-0.5">Commodity complies with mandatory Legal Metrology (Packaged Commodities) Rules, 2011 declarations.</p>
                      </div>
                    </div>
                  ) : (
                    <div className="space-y-2">
                      {selectedInspection.violations.map((v, i) => (
                        <div key={i} className="p-3 bg-[#FEE2E2] border border-[#FECACA] rounded text-xs text-[#B91C1C]">
                          <div className="flex justify-between items-center mb-1">
                            <span className="font-bold uppercase tracking-wider">{v.field}</span>
                            <span className="text-[10px] uppercase font-bold px-1.5 py-0.5 bg-white text-[#B91C1C] border border-[#FECACA] rounded">
                              {v.severity}
                            </span>
                          </div>
                          <p>{v.description}</p>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

              </div>

              {/* Modal Footer */}
              <div className="flex justify-between items-center p-4 border-t border-[#D5DCE5] bg-[#F5F7FA]">
                <button
                  onClick={() => setSelectedInspection(null)}
                  className="px-4 py-2 text-xs font-semibold text-[#183153] bg-white border border-[#D5DCE5] rounded hover:bg-[#F5F7FA]"
                >
                  Close Dossier
                </button>
                <button
                  onClick={() => downloadPdf(selectedInspection.scan_id || selectedInspection.id)}
                  className="px-4 py-2 text-xs font-semibold text-white bg-[#174A7E] hover:bg-[#133D68] rounded shadow-sm flex items-center gap-1.5"
                >
                  <Download size={14} /> Download Official PDF Report
                </button>
              </div>

            </div>
          </div>
        )}

      </main>

      <Footer />
    </div>
  );
}

export default OfficerDashboard;
