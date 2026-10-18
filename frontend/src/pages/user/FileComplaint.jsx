import { useState } from "react";
import { useSearchParams, useNavigate, Link } from "react-router-dom";
import axios from "axios";
import { AlertTriangle, CheckCircle, FileText, ArrowLeft, Send } from "lucide-react";
import Navbar from "../../components/Navbar";
import Footer from "../../components/Footer";
import API_BASE_URL from "../../config";

function FileComplaint() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();

  const [scanId, setScanId] = useState(searchParams.get("scan_id") || "");
  const [productName, setProductName] = useState(searchParams.get("product") || "");
  const [manufacturer, setManufacturer] = useState(searchParams.get("manufacturer") || "");
  const [violationType, setViolationType] = useState("MISSING_MANDATORY_DECLARATIONS");
  const [description, setDescription] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [successData, setSuccessData] = useState(null);
  const [errorMsg, setErrorMsg] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsSubmitting(true);
    setErrorMsg("");

    try {
      const token = localStorage.getItem("token");
      const headers = token ? { Authorization: `Bearer ${token}` } : {};

      const res = await axios.post(
        `${API_BASE_URL}/complaints/`,
        {
          scan_id: scanId ? parseInt(scanId, 10) : null,
          product_name: productName,
          manufacturer: manufacturer,
          violation_type: violationType,
          description: description,
        },
        { headers }
      );

      setSuccessData(res.data);
    } catch (err) {
      console.error(err);
      setErrorMsg(err?.response?.data?.detail || "Failed to submit statutory grievance. Please try again.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#FFFFFF] flex flex-col justify-between">
      <Navbar role="user" />

      <main className="flex-1 max-w-4xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-10">
        
        {/* Page Header */}
        <div className="mb-8 pb-4 border-b border-[#D5DCE5] flex flex-wrap items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <Link to="/user/dashboard" className="text-xs font-semibold text-[#174A7E] hover:underline flex items-center gap-1">
                <ArrowLeft size={13} /> Back to Dashboard
              </Link>
            </div>
            <h1 className="text-2xl sm:text-3xl font-bold text-[#183153] tracking-tight">
              Report Statutory Grievance
            </h1>
            <p className="text-[#64748B] text-xs sm:text-sm mt-0.5">
              Lodge a formal complaint regarding packaged commodity violations under the Legal Metrology Act, 2009.
            </p>
          </div>
          <span className="text-xs px-2.5 py-1 bg-[#F5F7FA] text-[#174A7E] border border-[#D5DCE5] font-semibold rounded">
            Consumer Grievance Redressal
          </span>
        </div>

        {/* Success Alert */}
        {successData ? (
          <div className="bg-white border border-[#BBF7D0] rounded p-8 sm:p-10 text-center shadow-sm">
            <div className="w-14 h-14 rounded-full bg-[#DCFCE7] text-[#15803D] flex items-center justify-center mx-auto mb-4">
              <CheckCircle size={32} />
            </div>
            <h2 className="text-xl font-bold text-[#183153]">Grievance Registered Successfully</h2>
            <p className="text-sm text-[#475569] mt-2 max-w-lg mx-auto">
              Your grievance has been formally entered into the Legal Metrology inspection log for officer review and follow-up.
            </p>
            
            <div className="inline-block my-6 bg-[#F5F7FA] px-6 py-3 rounded border border-[#D5DCE5] font-mono text-sm">
              Grievance Reference Number: <span className="text-[#174A7E] font-bold">#GRIEV-{successData.complaint_id}</span>
            </div>

            <div className="flex flex-wrap justify-center gap-4">
              <button
                onClick={() => {
                  setSuccessData(null);
                  setDescription("");
                }}
                className="bg-white border border-[#D5DCE5] hover:bg-[#F5F7FA] text-[#183153] px-5 py-2.5 rounded text-xs font-semibold"
              >
                File Another Grievance
              </button>
              <button
                onClick={() => navigate("/user/dashboard")}
                className="bg-[#174A7E] hover:bg-[#133D68] text-white px-5 py-2.5 rounded text-xs font-semibold shadow-sm"
              >
                Return to Dashboard →
              </button>
            </div>
          </div>
        ) : (
          <form
            onSubmit={handleSubmit}
            className="bg-white border border-[#D5DCE5] rounded p-6 sm:p-8 shadow-sm space-y-6"
          >
            {errorMsg && (
              <div className="p-3.5 rounded bg-[#FEE2E2] border border-[#FECACA] text-[#B91C1C] text-xs flex items-start gap-2">
                <AlertTriangle size={16} className="mt-0.5 shrink-0" />
                <p>{errorMsg}</p>
              </div>
            )}

            <div className="grid md:grid-cols-2 gap-6">
              
              <div>
                <label className="block text-xs font-bold text-[#183153] uppercase tracking-wider mb-1.5">
                  Associated Inspection Scan ID (Optional)
                </label>
                <input
                  type="text"
                  value={scanId}
                  onChange={(e) => setScanId(e.target.value)}
                  placeholder="e.g. 51"
                  className="w-full px-3 py-2 text-sm bg-white border border-[#D5DCE5] rounded text-[#183153] placeholder-[#94A3B8] focus:border-[#174A7E] focus:outline-none focus:ring-1 focus:ring-[#174A7E]"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-[#183153] uppercase tracking-wider mb-1.5">
                  Commodity / Product Name *
                </label>
                <input
                  type="text"
                  required
                  value={productName}
                  onChange={(e) => setProductName(e.target.value)}
                  placeholder="e.g. Brand Whole Wheat Atta 5kg"
                  className="w-full px-3 py-2 text-sm bg-white border border-[#D5DCE5] rounded text-[#183153] placeholder-[#94A3B8] focus:border-[#174A7E] focus:outline-none focus:ring-1 focus:ring-[#174A7E]"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-[#183153] uppercase tracking-wider mb-1.5">
                  Manufacturer / Packer / Brand
                </label>
                <input
                  type="text"
                  value={manufacturer}
                  onChange={(e) => setManufacturer(e.target.value)}
                  placeholder="e.g. ABC Foods Pvt. Ltd."
                  className="w-full px-3 py-2 text-sm bg-white border border-[#D5DCE5] rounded text-[#183153] placeholder-[#94A3B8] focus:border-[#174A7E] focus:outline-none focus:ring-1 focus:ring-[#174A7E]"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-[#183153] uppercase tracking-wider mb-1.5">
                  Alleged Statutory Violation Type *
                </label>
                <select
                  value={violationType}
                  onChange={(e) => setViolationType(e.target.value)}
                  className="w-full px-3 py-2 text-sm bg-white border border-[#D5DCE5] rounded text-[#183153] focus:border-[#174A7E] focus:outline-none focus:ring-1 focus:ring-[#174A7E]"
                >
                  <option value="MISSING_MANDATORY_DECLARATIONS">Rule 6: Missing Mandatory Declarations</option>
                  <option value="OVERCHARGING_MRP">Rule 18(2): Charging Above Maximum Retail Price (MRP)</option>
                  <option value="NET_QUANTITY_DEFICIENCY">Rule 11: Deficient Net Quantity / Non-Standard Unit</option>
                  <option value="SMUDGED_ALTERED_DATE">Rule 6(1)(d): Smudged or Altered Expiry / Manufacturing Date</option>
                  <option value="DECEPTIVE_PACKAGING">Rule 23: Deceptive / Slack Package Dimensions</option>
                  <option value="OTHER_STATUTORY_DEFECT">Other Legal Metrology Non-Compliance</option>
                </select>
              </div>

            </div>

            <div>
              <label className="block text-xs font-bold text-[#183153] uppercase tracking-wider mb-1.5">
                Detailed Description of Violation *
              </label>
              <textarea
                rows={4}
                required
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Describe where the product was purchased, date of purchase, specific missing labels, or price charged above printed MRP..."
                className="w-full px-3 py-2 text-sm bg-white border border-[#D5DCE5] rounded text-[#183153] placeholder-[#94A3B8] focus:border-[#174A7E] focus:outline-none focus:ring-1 focus:ring-[#174A7E]"
              />
            </div>

            <div className="pt-2 flex items-center justify-between border-t border-[#D5DCE5]">
              <span className="text-xs text-[#64748B]">
                Complaints are reviewed by the concerned Inspector of Legal Metrology.
              </span>
              <button
                type="submit"
                disabled={isSubmitting}
                className="px-6 py-2.5 bg-[#174A7E] hover:bg-[#133D68] text-white text-xs sm:text-sm font-semibold rounded shadow-sm flex items-center gap-2 transition-colors disabled:opacity-60"
              >
                <Send size={15} />
                {isSubmitting ? "Transmitting Grievance..." : "Submit Formal Grievance"}
              </button>
            </div>
          </form>
        )}

      </main>

      <Footer />
    </div>
  );
}

export default FileComplaint;
