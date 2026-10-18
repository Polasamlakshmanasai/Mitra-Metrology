import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import axios from "axios";
import { Camera, FileText, Download, Eye, ChevronRight, X, ShieldCheck, AlertTriangle, Filter, CheckCircle } from "lucide-react";
import Navbar from "../../components/Navbar";
import Footer from "../../components/Footer";
import API_BASE_URL from "../../config";

function ScanHistory() {
  const [scans, setScans] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState("ALL");
  const [selectedScan, setSelectedScan] = useState(null);

  const fetchScans = async () => {
    try {
      const token = localStorage.getItem("token");
      const headers = token ? { Authorization: `Bearer ${token}` } : {};
      const res = await axios.get(`${API_BASE_URL}/scans/history`, { headers });
      setScans(res.data || []);
    } catch (err) {
      console.error("Failed to load scans", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchScans();
  }, []);

  const filteredScans = scans.filter((scan) => {
    if (filter === "ALL") return true;
    if (filter === "COMPLIANT") return scan.status === "COMPLIANT";
    if (filter === "NON-COMPLIANT") return scan.status === "NON-COMPLIANT" || scan.status === "NON_COMPLIANT";
    if (filter === "REVIEW_REQUIRED") return scan.status.includes("REVIEW");
    return true;
  });

  const viewScanDetails = async (scanId) => {
    try {
      const token = localStorage.getItem("token");
      const headers = token ? { Authorization: `Bearer ${token}` } : {};
      const res = await axios.get(`${API_BASE_URL}/scans/${scanId}`, { headers });
      setSelectedScan(res.data);
    } catch (err) {
      console.error(err);
      alert("Failed to load scan details.");
    }
  };

  const downloadPdf = async (scanId) => {
    try {
      const token = localStorage.getItem("token");
      const headers = token ? { Authorization: `Bearer ${token}` } : {};
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
      <Navbar role="user" />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        
        {/* Page Header */}
        <div className="flex flex-wrap items-center justify-between gap-4 mb-8 pb-4 border-b border-[#D5DCE5]">
          <div>
            <h1 className="text-2xl sm:text-3xl font-bold text-[#183153] tracking-tight">
              Package Inspection History & Audit Log
            </h1>
            <p className="text-[#64748B] text-xs sm:text-sm mt-1">
              Official records of all packaged commodities inspected under Legal Metrology (Packaged Commodities) Rules, 2011.
            </p>
          </div>

          <Link
            to="/user/scan"
            className="bg-[#174A7E] hover:bg-[#133D68] text-white px-4 py-2 rounded text-xs sm:text-sm font-semibold shadow-sm transition flex items-center gap-2"
          >
            <Camera size={16} /> New Package Scan
          </Link>
        </div>

        {/* Filter Bar */}
        <div className="flex flex-wrap items-center gap-2 mb-6">
          <span className="text-xs font-bold text-[#64748B] uppercase tracking-wider mr-2 flex items-center gap-1">
            <Filter size={13} /> Filter:
          </span>
          {[
            { id: "ALL", label: "All Inspections" },
            { id: "COMPLIANT", label: "Compliant" },
            { id: "REVIEW_REQUIRED", label: "Review Required" },
            { id: "NON-COMPLIANT", label: "Non-Compliant" },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setFilter(tab.id)}
              className={`px-3 py-1.5 rounded text-xs font-semibold border transition-colors ${
                filter === tab.id
                  ? "bg-[#174A7E] text-white border-[#174A7E]"
                  : "bg-white text-[#183153] border-[#D5DCE5] hover:bg-[#F5F7FA]"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Inspections Table */}
        {loading ? (
          <div className="p-12 text-center bg-white border border-[#D5DCE5] rounded">
            <div className="w-8 h-8 border-2 border-[#174A7E] border-t-transparent rounded-full animate-spin mx-auto mb-3" />
            <p className="text-xs text-[#64748B]">Loading inspection history records...</p>
          </div>
        ) : filteredScans.length === 0 ? (
          <div className="p-12 text-center bg-white border border-[#D5DCE5] rounded flex flex-col items-center">
            <FileText size={40} className="text-[#94A3B8] mb-3" />
            <h3 className="text-sm font-bold text-[#183153]">No inspection records found</h3>
            <p className="text-xs text-[#64748B] mt-1">There are no records matching your current filter criteria.</p>
          </div>
        ) : (
          <div className="bg-white border border-[#D5DCE5] rounded shadow-sm overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs whitespace-nowrap">
                <thead className="bg-[#F5F7FA] text-[#64748B] uppercase tracking-wider font-semibold border-b border-[#D5DCE5]">
                  <tr>
                    <th className="px-6 py-3">Scan ID</th>
                    <th className="px-6 py-3">Commodity / Label</th>
                    <th className="px-6 py-3">Compliance Verdict</th>
                    <th className="px-6 py-3">Score</th>
                    <th className="px-6 py-3">Date</th>
                    <th className="px-6 py-3 text-right">Statutory Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#D5DCE5] text-[#183153]">
                  {filteredScans.map((scan) => (
                    <tr
                      key={scan.scan_id || scan.id}
                      className="hover:bg-[#F5F7FA] transition-colors cursor-pointer"
                      onClick={() => viewScanDetails(scan.scan_id || scan.id)}
                    >
                      <td className="px-6 py-3.5 font-mono text-[#64748B] font-semibold">
                        #{scan.scan_id || scan.id}
                      </td>
                      <td className="px-6 py-3.5 font-bold text-[#183153]">
                        {scan.product_name || "Packaged Commodity"}
                      </td>
                      <td className="px-6 py-3.5">
                        <span
                          className={`inline-flex items-center px-2 py-0.5 rounded text-[11px] font-semibold border ${
                            scan.status === "COMPLIANT"
                              ? "bg-[#DCFCE7] text-[#15803D] border-[#BBF7D0]"
                              : scan.status === "NON-COMPLIANT" || scan.status === "NON_COMPLIANT"
                              ? "bg-[#FEE2E2] text-[#B91C1C] border-[#FECACA]"
                              : "bg-[#FEF3C7] text-[#B45309] border-[#FDE68A]"
                          }`}
                        >
                          {scan.status.replace("_", "-")}
                        </span>
                      </td>
                      <td className="px-6 py-3.5 font-semibold text-[#183153]">
                        {scan.score !== undefined && scan.score !== null ? `${scan.score}%` : "--"}
                      </td>
                      <td className="px-6 py-3.5 text-[#64748B]">
                        {scan.created_at || (scan.date ? scan.date : "--")}
                      </td>
                      <td className="px-6 py-3.5 text-right space-x-2" onClick={(e) => e.stopPropagation()}>
                        <button
                          onClick={() => viewScanDetails(scan.scan_id || scan.id)}
                          className="px-2.5 py-1 bg-white border border-[#D5DCE5] hover:bg-[#F5F7FA] text-[#174A7E] text-xs font-semibold rounded"
                        >
                          Details
                        </button>
                        <button
                          onClick={() => downloadPdf(scan.scan_id || scan.id)}
                          className="px-2.5 py-1 bg-[#174A7E] hover:bg-[#133D68] text-white text-xs font-semibold rounded inline-flex items-center gap-1 shadow-xs"
                          title="Download Legal Metrology PDF Report"
                        >
                          <Download size={12} /> PDF
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Scan Details Modal */}
        {selectedScan && (
          <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-xs flex items-center justify-center p-4 overflow-y-auto">
            <div className="bg-white border border-[#D5DCE5] rounded max-w-2xl w-full max-h-[90vh] overflow-y-auto p-6 shadow-xl text-[#183153]">
              
              {/* Modal Header */}
              <div className="flex items-start justify-between border-b border-[#D5DCE5] pb-4 mb-5">
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-xs font-mono text-[#64748B]">Inspection #{selectedScan.scan_id || selectedScan.id}</span>
                    <span
                      className={`text-[11px] px-2 py-0.5 rounded font-semibold border ${
                        selectedScan.status === "COMPLIANT"
                          ? "bg-[#DCFCE7] text-[#15803D] border-[#BBF7D0]"
                          : selectedScan.status === "NON-COMPLIANT" || selectedScan.status === "NON_COMPLIANT"
                          ? "bg-[#FEE2E2] text-[#B91C1C] border-[#FECACA]"
                          : "bg-[#FEF3C7] text-[#B45309] border-[#FDE68A]"
                      }`}
                    >
                      {selectedScan.status}
                    </span>
                  </div>
                  <h2 className="text-xl font-bold text-[#183153]">
                    {selectedScan.product_name || "Statutory Inspection Audit Record"}
                  </h2>
                </div>
                <button
                  onClick={() => setSelectedScan(null)}
                  className="text-[#64748B] hover:text-[#183153] p-1.5 rounded hover:bg-[#F5F7FA]"
                  aria-label="Close modal"
                >
                  <X size={18} />
                </button>
              </div>

              {/* Package Evidence Image */}
              {selectedScan.evidence?.image_url && (
                <div className="mb-5 rounded overflow-hidden bg-[#F5F7FA] border border-[#D5DCE5] p-3 flex justify-center">
                  <img
                    src={`${API_BASE_URL}${selectedScan.evidence.image_url}`}
                    alt="Package statutory evidence"
                    className="max-h-56 object-contain rounded border border-[#D5DCE5]"
                  />
                </div>
              )}

              {/* Extracted Declarations Table */}
              <h3 className="text-xs uppercase tracking-wider text-[#183153] font-bold mb-2">
                Declared Statutory Fields
              </h3>
              <div className="bg-[#F5F7FA] border border-[#D5DCE5] rounded divide-y divide-[#D5DCE5] text-xs mb-5">
                {Object.entries(selectedScan.fields || {}).map(([key, val]) => (
                  <div key={key} className="p-2.5 flex items-center justify-between">
                    <span className="text-[#64748B] capitalize">{key.replace(/_/g, " ")}</span>
                    <span className="text-[#183153] font-mono font-semibold">
                      {typeof val === "object" ? JSON.stringify(val) : String(val || "Not detected")}
                    </span>
                  </div>
                ))}
              </div>

              {/* Violations Flagged */}
              {selectedScan.violations && selectedScan.violations.length > 0 && (
                <div className="mb-5">
                  <h3 className="text-xs uppercase tracking-wider text-[#B91C1C] font-bold mb-2">
                    Statutory Violations Flagged ({selectedScan.violations.length})
                  </h3>
                  <div className="space-y-2">
                    {selectedScan.violations.map((v, i) => (
                      <div key={i} className="p-3 bg-[#FEE2E2] border border-[#FECACA] rounded text-xs text-[#B91C1C]">
                        <span className="font-bold uppercase">{v.field}: </span>
                        <span>{v.description}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Modal Actions */}
              <div className="flex justify-between items-center pt-4 border-t border-[#D5DCE5]">
                <button
                  onClick={() => downloadPdf(selectedScan.scan_id || selectedScan.id)}
                  className="bg-[#174A7E] hover:bg-[#133D68] text-white text-xs font-semibold px-4 py-2 rounded shadow-sm flex items-center gap-1.5"
                >
                  <Download size={14} /> Download Official PDF Report
                </button>
                <button
                  onClick={() => setSelectedScan(null)}
                  className="bg-white border border-[#D5DCE5] hover:bg-[#F5F7FA] text-[#183153] text-xs font-semibold px-4 py-2 rounded"
                >
                  Close
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

export default ScanHistory;
