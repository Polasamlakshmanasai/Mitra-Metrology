import { useState } from "react";
import { useSearchParams, useNavigate } from "react-router-dom";
import axios from "axios";
import Navbar from "../../components/Navbar";

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
      setErrorMsg(err?.response?.data?.detail || "Failed to submit grievance. Please try again.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-white flex flex-col">
      <Navbar role="user" />

      <main className="flex-1 max-w-4xl w-full mx-auto px-4 sm:px-6 py-10">
        <div className="mb-8">
          <h2 className="text-3xl font-bold tracking-tight flex items-center gap-3">
            <span>📢</span> Report Statutory Grievance
          </h2>
          <p className="text-slate-400 mt-1">
            Lodge a formal complaint under the Legal Metrology Act, 2009 for packaged commodity non-compliance.
          </p>
        </div>

        {successData ? (
          <div className="bg-emerald-950/40 border border-emerald-500/50 rounded-3xl p-8 text-center shadow-xl">
            <div className="text-5xl mb-4">✅</div>
            <h3 className="text-2xl font-bold text-emerald-300">Grievance Registered Successfully</h3>
            <p className="text-slate-300 mt-2">
              Your complaint has been submitted to the Department of Legal Metrology.
            </p>
            <div className="inline-block my-6 bg-slate-900 px-5 py-3 rounded-2xl border border-slate-800 font-mono text-sm">
              Complaint Reference: <span className="text-emerald-400 font-bold">#GRIEV-{successData.complaint_id}</span>
            </div>
            <div className="flex justify-center gap-4">
              <button
                onClick={() => {
                  setSuccessData(null);
                  setDescription("");
                }}
                className="bg-slate-800 hover:bg-slate-700 px-5 py-2.5 rounded-xl text-sm font-semibold"
              >
                File Another Complaint
              </button>
              <button
                onClick={() => navigate("/user/dashboard")}
                className="bg-emerald-600 hover:bg-emerald-500 px-5 py-2.5 rounded-xl text-sm font-semibold shadow-lg shadow-emerald-600/20"
              >
                Return to Dashboard →
              </button>
            </div>
          </div>
        ) : (
          <form
            onSubmit={handleSubmit}
            className="bg-slate-900 border border-slate-800 rounded-3xl p-6 sm:p-10 shadow-xl space-y-6"
          >
            {errorMsg && (
              <div className="p-4 rounded-xl bg-red-950/60 border border-red-800 text-red-300 text-sm">
                ⚠️ {errorMsg}
              </div>
            )}

            <div className="grid sm:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-semibold text-slate-300 mb-2">
                  Scan Reference ID (Optional)
                </label>
                <input
                  type="text"
                  value={scanId}
                  onChange={(e) => setScanId(e.target.value)}
                  placeholder="e.g. 8"
                  className="w-full bg-slate-800 text-white border border-slate-700 rounded-xl px-4 py-3 outline-none focus:border-blue-500 text-sm"
                />
              </div>

              <div>
                <label className="block text-sm font-semibold text-slate-300 mb-2">
                  Product / Commodity Name
                </label>
                <input
                  type="text"
                  value={productName}
                  onChange={(e) => setProductName(e.target.value)}
                  placeholder="e.g. Whole Wheat Atta 5kg"
                  className="w-full bg-slate-800 text-white border border-slate-700 rounded-xl px-4 py-3 outline-none focus:border-blue-500 text-sm"
                />
              </div>
            </div>

            <div className="grid sm:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-semibold text-slate-300 mb-2">
                  Manufacturer / Packer
                </label>
                <input
                  type="text"
                  value={manufacturer}
                  onChange={(e) => setManufacturer(e.target.value)}
                  placeholder="e.g. Mitra Agro Foods Pvt. Ltd."
                  className="w-full bg-slate-800 text-white border border-slate-700 rounded-xl px-4 py-3 outline-none focus:border-blue-500 text-sm"
                />
              </div>

              <div>
                <label className="block text-sm font-semibold text-slate-300 mb-2">
                  Violation Category
                </label>
                <select
                  value={violationType}
                  onChange={(e) => setViolationType(e.target.value)}
                  className="w-full bg-slate-800 text-white border border-slate-700 rounded-xl px-4 py-3 outline-none focus:border-blue-500 text-sm"
                >
                  <option value="MISSING_MRP">Rule 6(1)(e): Missing or Altered MRP</option>
                  <option value="MISSING_NET_QUANTITY">Rule 6(1)(c): Missing or Deceptive Net Quantity</option>
                  <option value="MISSING_MFG_DATE">Rule 6(1)(d): Missing Manufacturing Date</option>
                  <option value="MISSING_MANUFACTURER_ADDRESS">Rule 6(1)(a): Missing Manufacturer Identity</option>
                  <option value="MISSING_CONSUMER_CARE">Rule 6(1)(n): Missing Consumer Grievance Contact</option>
                  <option value="MISSING_FSSAI_LICENSE">Missing / Invalid FSSAI Food License</option>
                  <option value="OTHER_VIOLATION">Other Statutory Non-Compliance</option>
                </select>
              </div>
            </div>

            <div>
              <label className="block text-sm font-semibold text-slate-300 mb-2">
                Detailed Grievance Description *
              </label>
              <textarea
                required
                rows={4}
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Describe the packaging defect, location purchased, and specific statutory violation observed..."
                className="w-full bg-slate-800 text-white border border-slate-700 rounded-xl px-4 py-3 outline-none focus:border-blue-500 text-sm"
              />
            </div>

            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full bg-rose-600 hover:bg-rose-500 text-white py-3.5 rounded-xl font-bold transition shadow-lg shadow-rose-600/20 text-sm flex items-center justify-center gap-2"
            >
              {isSubmitting ? "Registering Grievance..." : "📢 Submit Official Grievance"}
            </button>
          </form>
        )}
      </main>
    </div>
  );
}

export default FileComplaint;
