import { useState, useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import axios from "axios";
import { Camera, Search, FileText, AlertTriangle, ChevronRight, Activity, Package, History, CheckCircle, Shield } from "lucide-react";
import Navbar from "../../components/Navbar";
import Footer from "../../components/Footer";
import API_BASE_URL from "../../config";

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
        axios
          .get(`${API_BASE_URL}/scans/`, { headers })
          .then((res) => {
            if (Array.isArray(res.data)) setScans(res.data);
          })
          .catch(() => {});
      })
      .finally(() => setLoading(false));
  }, []);

  const totalScans = scans.length;
  const compliantCount = scans.filter((s) => s.status === "COMPLIANT").length;
  const violationCount = scans.filter((s) => s.status === "NON-COMPLIANT" || s.status === "NON_COMPLIANT").length;
  const reviewCount = totalScans - compliantCount - violationCount;

  return (
    <div className="min-h-screen bg-[#FFFFFF] flex flex-col justify-between">
      <Navbar role="user" />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        
        {/* Page Header */}
        <div className="mb-8 pb-4 border-b border-[#D5DCE5] flex flex-wrap items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl sm:text-3xl font-bold text-[#183153] tracking-tight">
              Citizen Compliance Dashboard
            </h1>
            <p className="text-[#64748B] text-xs sm:text-sm mt-1">
              Verify statutory declarations on packaged commodities under the Legal Metrology (Packaged Commodities) Rules, 2011.
            </p>
          </div>
          <Link
            to="/user/scan"
            className="px-4 py-2 bg-[#174A7E] hover:bg-[#133D68] text-white text-xs sm:text-sm font-semibold rounded shadow-sm transition-colors flex items-center gap-2"
          >
            <Camera size={16} />
            Scan New Package
          </Link>
        </div>

        {/* Metrics Grid */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          
          <div className="bg-[#F5F7FA] border border-[#D5DCE5] rounded p-5">
            <span className="text-[11px] font-bold text-[#64748B] uppercase tracking-wider">Total Inspections</span>
            <div className="mt-2 flex items-baseline gap-2">
              <span className="text-3xl font-bold text-[#183153]">{totalScans}</span>
            </div>
            <span className="text-[11px] text-[#64748B] mt-1 block">Recorded in audit log</span>
          </div>
          
          <div className="bg-[#F5F7FA] border border-[#D5DCE5] rounded p-5">
            <span className="text-[11px] font-bold text-[#15803D] uppercase tracking-wider">Fully Compliant</span>
            <div className="mt-2 flex items-baseline gap-2">
              <span className="text-3xl font-bold text-[#15803D]">{compliantCount}</span>
            </div>
            <span className="text-[11px] text-[#64748B] mt-1 block">Passed all rule checks</span>
          </div>

          <div className="bg-[#F5F7FA] border border-[#D5DCE5] rounded p-5">
            <span className="text-[11px] font-bold text-[#B45309] uppercase tracking-wider">Review Required</span>
            <div className="mt-2 flex items-baseline gap-2">
              <span className="text-3xl font-bold text-[#B45309]">{reviewCount}</span>
            </div>
            <span className="text-[11px] text-[#64748B] mt-1 block">Pending field confirmation</span>
          </div>

          <div className="bg-[#F5F7FA] border border-[#D5DCE5] rounded p-5">
            <span className="text-[11px] font-bold text-[#B91C1C] uppercase tracking-wider">Non-Compliant</span>
            <div className="mt-2 flex items-baseline gap-2">
              <span className="text-3xl font-bold text-[#B91C1C]">{violationCount}</span>
            </div>
            <span className="text-[11px] text-[#64748B] mt-1 block">Statutory violations detected</span>
          </div>

        </div>

        {/* Services & Actions Grid */}
        <div className="grid md:grid-cols-3 gap-6 mb-10">
          
          <div
            onClick={() => navigate("/user/scan")}
            className="bg-white border border-[#D5DCE5] rounded p-6 shadow-sm hover:border-[#174A7E] hover:shadow transition-all cursor-pointer flex flex-col justify-between group"
          >
            <div>
              <div className="w-11 h-11 rounded bg-[#F5F7FA] text-[#174A7E] border border-[#D5DCE5] flex items-center justify-center mb-4">
                <Camera size={22} />
              </div>
              <h3 className="text-base font-bold text-[#183153] group-hover:text-[#174A7E] transition-colors">
                New Package Scan
              </h3>
              <p className="text-xs text-[#475569] mt-2 leading-relaxed">
                Upload or capture photos of package labels. Runs OCR extraction with a mandatory 2-step review before compliance checks.
              </p>
            </div>
            <span className="mt-5 text-xs font-semibold text-[#174A7E] flex items-center gap-1 group-hover:underline">
              Start Scan Workflow <ChevronRight size={14} />
            </span>
          </div>

          <div
            onClick={() => navigate("/food-scan")}
            className="bg-white border border-[#D5DCE5] rounded p-6 shadow-sm hover:border-[#174A7E] hover:shadow transition-all cursor-pointer flex flex-col justify-between group"
          >
            <div>
              <div className="w-11 h-11 rounded bg-[#F5F7FA] text-[#174A7E] border border-[#D5DCE5] flex items-center justify-center mb-4">
                <Search size={22} />
              </div>
              <h3 className="text-base font-bold text-[#183153] group-hover:text-[#174A7E] transition-colors">
                FSSAI Food Label Validation
              </h3>
              <p className="text-xs text-[#475569] mt-2 leading-relaxed">
                Verify nutritional tables, INS additive codes, allergen statements, and statutory FSSAI licence declarations for food products.
              </p>
            </div>
            <span className="mt-5 text-xs font-semibold text-[#174A7E] flex items-center gap-1 group-hover:underline">
              Verify Food Label <ChevronRight size={14} />
            </span>
          </div>

          <div
            onClick={() => navigate("/user/complaint")}
            className="bg-white border border-[#D5DCE5] rounded p-6 shadow-sm hover:border-[#174A7E] hover:shadow transition-all cursor-pointer flex flex-col justify-between group"
          >
            <div>
              <div className="w-11 h-11 rounded bg-[#F5F7FA] text-[#B45309] border border-[#D5DCE5] flex items-center justify-center mb-4">
                <AlertTriangle size={22} />
              </div>
              <h3 className="text-base font-bold text-[#183153] group-hover:text-[#174A7E] transition-colors">
                File Statutory Grievance
              </h3>
              <p className="text-xs text-[#475569] mt-2 leading-relaxed">
                Report missing declarations, smudged prices, missing manufacturing dates, or tampered MRP labels to the regulatory authority.
              </p>
            </div>
            <span className="mt-5 text-xs font-semibold text-[#B45309] flex items-center gap-1 group-hover:underline">
              Submit Grievance <ChevronRight size={14} />
            </span>
          </div>

        </div>

        {/* Recent Activity Table */}
        <div className="bg-white border border-[#D5DCE5] rounded shadow-sm overflow-hidden">
          <div className="flex items-center justify-between px-6 py-4 bg-[#F5F7FA] border-b border-[#D5DCE5]">
            <h3 className="text-sm font-bold text-[#183153] flex items-center gap-2">
              <History size={16} className="text-[#174A7E]" />
              Recent Package Inspections
            </h3>
            <Link
              to="/user/history"
              className="text-xs font-semibold text-[#174A7E] hover:text-[#133D68] hover:underline flex items-center gap-1"
            >
              View Full History <ChevronRight size={14} />
            </Link>
          </div>

          {loading ? (
            <div className="p-8 text-center">
              <Activity className="animate-spin h-6 w-6 text-[#174A7E] mx-auto mb-2" />
              <p className="text-xs text-[#64748B]">Loading inspection records from database...</p>
            </div>
          ) : scans.length === 0 ? (
            <div className="p-12 text-center flex flex-col items-center">
              <Package size={40} className="text-[#94A3B8] mb-3" />
              <h4 className="text-sm font-semibold text-[#183153]">No inspection records found</h4>
              <p className="text-xs text-[#64748B] mt-1">Uploaded and scanned packaged products will appear here.</p>
              <Link
                to="/user/scan"
                className="mt-4 px-3 py-1.5 bg-[#174A7E] text-white text-xs font-semibold rounded hover:bg-[#133D68]"
              >
                Scan First Package
              </Link>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs whitespace-nowrap">
                <thead className="bg-[#F5F7FA] text-[#64748B] uppercase tracking-wider font-semibold border-b border-[#D5DCE5]">
                  <tr>
                    <th className="px-6 py-3">Inspection ID</th>
                    <th className="px-6 py-3">Commodity / Product</th>
                    <th className="px-6 py-3">Status</th>
                    <th className="px-6 py-3">Date</th>
                    <th className="px-6 py-3 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#D5DCE5] text-[#183153]">
                  {scans.slice(0, 5).map((scan) => (
                    <tr key={scan.scan_id || scan.id} className="hover:bg-[#F5F7FA] transition-colors">
                      <td className="px-6 py-3.5 font-mono text-[#64748B]">
                        #{scan.scan_id || scan.id}
                      </td>
                      <td className="px-6 py-3.5 font-semibold text-[#183153]">
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
                      <td className="px-6 py-3.5 text-[#64748B]">
                        {scan.date || (scan.created_at ? new Date(scan.created_at).toLocaleDateString() : "--")}
                      </td>
                      <td className="px-6 py-3.5 text-right">
                        <Link
                          to={`/user/history`}
                          className="text-xs text-[#174A7E] font-semibold hover:underline"
                        >
                          View Report
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

      </main>

      <Footer />
    </div>
  );
}

export default Dashboard;