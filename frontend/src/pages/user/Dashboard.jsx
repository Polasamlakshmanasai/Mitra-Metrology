import { useState, useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import axios from "axios";
import Navbar from "../../components/Navbar";

const API_BASE_URL = "http://localhost:8000";

function Dashboard() {
  const navigate = useNavigate();
  const [scans, setScans] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem("token");
    const headers = token ? { Authorization: `Bearer ${token}` } : {};

    axios
      .get(`${API_BASE_URL}/scans/history`, { headers })
      .then((res) => setScans(res.data || []))
      .catch((_err) => {
        // Fallback to general scans endpoint if history is empty
        axios
          .get(`${API_BASE_URL}/scans/`, { headers })
          .then((res) => {
            if (Array.isArray(res.data)) setScans(res.data);
          })
          .catch(() => {});
      })
      .finally(() => setLoading(false));
  }, []);

  const compliantCount = scans.filter((s) => s.status === "COMPLIANT").length;
  const violationCount = scans.filter((s) => s.status === "NON-COMPLIANT" || s.status === "NON_COMPLIANT").length;

  return (
    <div className="min-h-screen bg-slate-950 text-white flex flex-col">
      <Navbar role="user" />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 py-10">
        {/* Welcome Banner */}
        <div className="bg-gradient-to-r from-blue-950/60 via-slate-900 to-slate-900 border border-slate-800 rounded-3xl p-8 sm:p-10 shadow-xl mb-10">
          <div className="max-w-2xl">
            <div className="flex flex-wrap gap-2 items-center">
              <span className="text-xs font-bold uppercase tracking-wider text-blue-400 bg-blue-950/80 px-3 py-1 rounded-full border border-blue-800">
                Legal Metrology Verification
              </span>
              <span className="text-xs font-bold text-emerald-400 bg-emerald-950/80 px-3 py-1 rounded-full border border-emerald-800">
                {compliantCount} Compliant
              </span>
              {violationCount > 0 && (
                <span className="text-xs font-bold text-rose-400 bg-rose-950/80 px-3 py-1 rounded-full border border-rose-800">
                  {violationCount} Violations
                </span>
              )}
            </div>
            <h2 className="text-3xl sm:text-4xl font-black mt-3 text-white">
              Packaged Commodity Compliance Portal
            </h2>
            <p className="text-slate-300 mt-2 text-sm sm:text-base leading-relaxed">
              Verify maximum retail prices (MRP), net quantities, manufacturing dates, and mandatory statutory declarations with AI-powered computer vision.
            </p>

            <div className="flex flex-wrap gap-3 mt-6">
              <Link
                to="/user/scan"
                className="bg-blue-600 hover:bg-blue-500 text-white px-6 py-3 rounded-xl font-bold text-sm shadow-lg shadow-blue-600/30 transition flex items-center gap-2"
              >
                <span>📷</span> Scan New Package
              </Link>
              <Link
                to="/food-scan"
                className="bg-emerald-600 hover:bg-emerald-500 text-white px-5 py-3 rounded-xl font-bold text-sm shadow-lg shadow-emerald-600/20 transition flex items-center gap-2"
              >
                <span>🥗</span> Food Label (FSSAI)
              </Link>
              <Link
                to="/user/complaint"
                className="bg-slate-800 hover:bg-slate-700 text-slate-200 px-5 py-3 rounded-xl font-semibold text-sm border border-slate-700 transition"
              >
                📢 Report Violation
              </Link>
            </div>
          </div>
        </div>

        {/* Quick Action Grid */}
        <div className="grid md:grid-cols-3 gap-6 mb-10">
          <div
            onClick={() => navigate("/user/scan")}
            className="bg-slate-900 border border-slate-800 hover:border-blue-500/60 rounded-3xl p-6 transition cursor-pointer group shadow-lg"
          >
            <div className="w-12 h-12 rounded-2xl bg-blue-950 border border-blue-800/60 flex items-center justify-center text-2xl mb-4 group-hover:scale-110 transition">
              📷
            </div>
            <h3 className="text-xl font-bold text-white group-hover:text-blue-400 transition">
              Inspect Package
            </h3>
            <p className="text-slate-400 text-sm mt-2">
              Capture or upload packaging labels for instant OCR extraction and statutory verification.
            </p>
            <div className="mt-5 text-sm font-bold text-blue-400 flex items-center gap-1">
              Start Scan →
            </div>
          </div>

          <div
            onClick={() => navigate("/user/history")}
            className="bg-slate-900 border border-slate-800 hover:border-purple-500/60 rounded-3xl p-6 transition cursor-pointer group shadow-lg"
          >
            <div className="w-12 h-12 rounded-2xl bg-purple-950 border border-purple-800/60 flex items-center justify-center text-2xl mb-4 group-hover:scale-110 transition">
              📋
            </div>
            <h3 className="text-xl font-bold text-white group-hover:text-purple-400 transition">
              My Scan History
            </h3>
            <p className="text-slate-400 text-sm mt-2">
              Review previous product audits, certificates of compliance, and violation logs.
            </p>
            <div className="mt-5 text-sm font-bold text-purple-400 flex items-center gap-1">
              View History ({scans.length}) →
            </div>
          </div>

          <div
            onClick={() => navigate("/user/complaint")}
            className="bg-slate-900 border border-slate-800 hover:border-rose-500/60 rounded-3xl p-6 transition cursor-pointer group shadow-lg"
          >
            <div className="w-12 h-12 rounded-2xl bg-rose-950 border border-rose-800/60 flex items-center justify-center text-2xl mb-4 group-hover:scale-110 transition">
              📢
            </div>
            <h3 className="text-xl font-bold text-white group-hover:text-rose-400 transition">
              File Complaint
            </h3>
            <p className="text-slate-400 text-sm mt-2">
              Submit formal complaints directly to the Legal Metrology Department for non-compliant goods.
            </p>
            <div className="mt-5 text-sm font-bold text-rose-400 flex items-center gap-1">
              File Report →
            </div>
          </div>
        </div>

        {/* Recent Activity Table */}
        <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 sm:p-8 shadow-xl">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h3 className="text-xl font-bold text-white">Recent Package Audits</h3>
              <p className="text-xs text-slate-400 mt-0.5">Live feed of processed commodity packages</p>
            </div>
            <Link
              to="/user/history"
              className="text-xs font-bold text-blue-400 hover:text-blue-300"
            >
              View Full History →
            </Link>
          </div>

          {loading ? (
            <div className="py-8 text-center text-slate-500 text-sm">Loading recent audits...</div>
          ) : scans.length === 0 ? (
            <div className="py-8 text-center text-slate-500 text-sm">
              No scans yet. Click <strong>Scan New Package</strong> above to get started.
            </div>
          ) : (
            <div className="divide-y divide-slate-800/70">
              {scans.slice(0, 5).map((scan) => (
                <div key={scan.scan_id || scan.id} className="py-3.5 flex items-center justify-between gap-4">
                  <div className="flex items-center gap-3">
                    <div className="w-9 h-9 rounded-xl bg-slate-800 flex items-center justify-center text-lg">
                      📦
                    </div>
                    <div>
                      <h4 className="font-semibold text-sm text-slate-200">{scan.product_name || "Packaged Commodity"}</h4>
                      <span className="text-xs text-slate-400 font-mono">Scan #{scan.scan_id || scan.id} • {scan.created_at || "Recent"}</span>
                    </div>
                  </div>

                  <div className="flex items-center gap-4">
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
                </div>
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}

export default Dashboard;