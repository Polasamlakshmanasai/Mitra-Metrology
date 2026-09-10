import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import axios from "axios";
import Navbar from "../../components/Navbar";

const API_BASE_URL = "http://localhost:8000";

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
    <div className="min-h-screen bg-slate-950 text-white flex flex-col">
      <Navbar role="user" />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 py-8">
        <div className="flex flex-wrap items-center justify-between gap-4 mb-8">
          <div>
            <h2 className="text-3xl font-bold tracking-tight flex items-center gap-3">
              <span>📋</span> My Product Inspection History
            </h2>
            <p className="text-slate-400 mt-1">
              Audit log of all packages scanned and evaluated for Legal Metrology & FSSAI compliance.
            </p>
          </div>

          <Link
            to="/user/scan"
            className="bg-blue-600 hover:bg-blue-500 text-white px-5 py-2.5 rounded-xl font-bold text-sm shadow-lg shadow-blue-600/20 transition flex items-center gap-2"
          >
            <span>📷</span> New Scan
          </Link>
        </div>

        {/* Filter Chips */}
        <div className="flex items-center gap-2 mb-6 border-b border-slate-800 pb-4">
          {[
            { id: "ALL", label: "All Inspections" },
            { id: "COMPLIANT", label: "Compliant" },
            { id: "REVIEW_REQUIRED", label: "Review Required" },
            { id: "NON-COMPLIANT", label: "Non-Compliant" },
          ].map((f) => (
            <button
              key={f.id}
              onClick={() => setFilter(f.id)}
              className={`text-xs px-3.5 py-1.5 rounded-xl font-semibold transition ${
                filter === f.id
                  ? "bg-blue-600 text-white shadow-md"
                  : "bg-slate-900 text-slate-400 hover:text-white border border-slate-800"
              }`}
            >
              {f.label}
            </button>
          ))}
          <span className="text-xs text-slate-500 ml-auto font-mono">
            {filteredScans.length} item{filteredScans.length === 1 ? "" : "s"}
          </span>
        </div>

        {loading ? (
          <div className="p-16 text-center text-slate-400">
            <div className="animate-spin text-3xl mb-3">⚙️</div>
            <p className="text-sm">Loading inspection logs...</p>
          </div>
        ) : filteredScans.length === 0 ? (
          <div className="bg-slate-900/40 border border-slate-800 rounded-2xl p-12 text-center">
            <div className="text-4xl mb-3">📦</div>
            <h3 className="text-lg font-bold text-slate-300">No product scans found</h3>
            <p className="text-sm text-slate-500 mt-1">Start by scanning your first commodity package.</p>
            <Link
              to="/user/scan"
              className="inline-block mt-5 bg-blue-600 hover:bg-blue-500 text-white px-5 py-2 rounded-xl text-sm font-semibold"
            >
              Scan Package Now
            </Link>
          </div>
        ) : (
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-5">
            {filteredScans.map((scan) => (
              <div
                key={scan.scan_id || scan.id}
                onClick={() => viewScanDetails(scan.scan_id || scan.id)}
                className="bg-slate-900 border border-slate-800 hover:border-slate-700 rounded-2xl p-5 shadow-lg transition cursor-pointer flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-start justify-between gap-3 mb-3">
                    <span className="text-xs font-mono text-slate-400">
                      Scan #{scan.scan_id || scan.id}
                    </span>
                    <span
                      className={`text-xs px-2.5 py-0.5 rounded-full font-bold uppercase ${
                        scan.status === "COMPLIANT"
                          ? "bg-emerald-950 text-emerald-400 border border-emerald-800"
                          : scan.status === "NON-COMPLIANT" || scan.status === "NON_COMPLIANT"
                          ? "bg-rose-950 text-rose-400 border border-rose-800"
                          : "bg-amber-950 text-amber-400 border border-amber-800"
                      }`}
                    >
                      {scan.status}
                    </span>
                  </div>

                  <h3 className="text-base font-bold text-white mb-1">
                    {scan.product_name || "Packaged Commodity"}
                  </h3>
                  <p className="text-xs text-slate-400 mb-4">{scan.created_at || "Recent"}</p>
                </div>

                <div className="pt-3 border-t border-slate-800/80 flex items-center justify-between">
                  <span className="text-xs text-blue-400 font-semibold hover:underline">
                    View Evidence & Audit →
                  </span>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      downloadPdf(scan.scan_id || scan.id);
                    }}
                    className="text-xs bg-slate-800 hover:bg-slate-700 text-slate-300 px-2.5 py-1 rounded-lg border border-slate-700 transition"
                  >
                    📥 PDF
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Scan Details Modal */}
        {selectedScan && (
          <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4 overflow-y-auto">
            <div className="bg-slate-900 border border-slate-800 rounded-3xl max-w-2xl w-full max-h-[90vh] overflow-y-auto p-6 shadow-2xl">
              <div className="flex items-start justify-between border-b border-slate-800 pb-4 mb-5">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-mono text-slate-400">Scan #{selectedScan.scan_id}</span>
                    <span
                      className={`text-xs px-2.5 py-0.5 rounded-full font-bold uppercase ${
                        selectedScan.status === "COMPLIANT"
                          ? "bg-emerald-950 text-emerald-400 border border-emerald-800"
                          : selectedScan.status === "NON-COMPLIANT" || selectedScan.status === "NON_COMPLIANT"
                          ? "bg-rose-950 text-rose-400 border border-rose-800"
                          : "bg-amber-950 text-amber-400 border border-amber-800"
                      }`}
                    >
                      {selectedScan.status}
                    </span>
                  </div>
                  <h3 className="text-xl font-bold text-white mt-1">Inspection Audit Evidence</h3>
                </div>
                <button
                  onClick={() => setSelectedScan(null)}
                  className="text-slate-400 hover:text-white text-lg p-1"
                >
                  ✕
                </button>
              </div>

              {/* Package Evidence Image */}
              {selectedScan.evidence?.image_url && (
                <div className="mb-5 rounded-xl overflow-hidden bg-slate-950 border border-slate-800 p-2 flex justify-center">
                  <img
                    src={`http://localhost:8000${selectedScan.evidence.image_url}`}
                    alt="Package evidence"
                    className="max-h-56 object-contain rounded"
                  />
                </div>
              )}

              {/* Extracted Declarations Table */}
              <h4 className="text-xs uppercase tracking-wider text-slate-400 font-bold mb-2">
                Declared Statutory Fields
              </h4>
              <div className="bg-slate-950 border border-slate-800 rounded-xl divide-y divide-slate-800 text-xs mb-5">
                {Object.entries(selectedScan.fields || {}).map(([key, val]) => (
                  <div key={key} className="p-2.5 flex items-center justify-between">
                    <span className="text-slate-400 capitalize">{key.replace(/_/g, " ")}</span>
                    <span className="text-slate-200 font-mono font-semibold">
                      {typeof val === "object" ? JSON.stringify(val) : String(val)}
                    </span>
                  </div>
                ))}
              </div>

              {/* Violations */}
              {selectedScan.violations && selectedScan.violations.length > 0 && (
                <div className="mb-5">
                  <h4 className="text-xs uppercase tracking-wider text-rose-400 font-bold mb-2">
                    Violations Flagged ({selectedScan.violations.length})
                  </h4>
                  <div className="space-y-2">
                    {selectedScan.violations.map((v, i) => (
                      <div key={i} className="p-2.5 bg-rose-950/30 border border-rose-900/50 rounded-xl text-xs">
                        <span className="font-bold text-rose-300 uppercase">{v.field}: </span>
                        <span className="text-slate-200">{v.description}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              <div className="flex justify-between items-center pt-3 border-t border-slate-800">
                <button
                  onClick={() => downloadPdf(selectedScan.scan_id)}
                  className="bg-blue-600 hover:bg-blue-500 text-white text-xs font-bold px-4 py-2.5 rounded-xl shadow-md flex items-center gap-1.5"
                >
                  <span>📥</span> Download Full PDF Report
                </button>
                <button
                  onClick={() => setSelectedScan(null)}
                  className="bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold px-4 py-2.5 rounded-xl"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

export default ScanHistory;
