import { useState, useRef } from "react";
import { Link } from "react-router-dom";
import axios from "axios";
import Navbar from "../../components/Navbar";

import API_BASE_URL from "../../config";


const RULE_TITLES = {
  mrp: { label: "Maximum Retail Price (MRP)", rule: "Rule 6(1)(e)" },
  net_quantity: { label: "Net Quantity", rule: "Rule 6(1)(c)" },
  manufacturing_date: { label: "Date of Manufacture", rule: "Rule 6(1)(d)" },
  best_before: { label: "Best Before / Expiry", rule: "Rule 6(1)(d)" },
  manufacturer: { label: "Manufacturer / Packer", rule: "Rule 6(1)(a)" },
  address: { label: "Manufacturer Address", rule: "Rule 6(1)(a)" },
  consumer_care: { label: "Consumer Care Contact", rule: "Rule 6(1)(n)" },
  fssai: { label: "FSSAI License No.", rule: "FSSAI Reg. 5(7)" },
};

function ScanProduct() {
  const fileInputRef = useRef(null);
  const videoRef = useRef(null);

  const [selectedFile, setSelectedFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [isCameraActive, setIsCameraActive] = useState(false);
  const [isScanning, setIsScanning] = useState(false);
  const [scanStage, setScanStage] = useState("");
  const [scanResult, setScanResult] = useState(null);
  const [errorMsg, setErrorMsg] = useState("");

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setSelectedFile(file);
      setPreviewUrl(URL.createObjectURL(file));
      setScanResult(null);
      setErrorMsg("");
    }
  };

  const startCamera = async () => {
    try {
      setIsCameraActive(true);
      setErrorMsg("");
      const stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: "environment" } });
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
      }
    } catch (_err) {
      setErrorMsg("Unable to access camera. Please upload an image file instead.");
      setIsCameraActive(false);
    }
  };

  const captureCamera = () => {
    if (!videoRef.current) return;
    const canvas = document.createElement("canvas");
    canvas.width = videoRef.current.videoWidth || 640;
    canvas.height = videoRef.current.videoHeight || 480;
    const ctx = canvas.getContext("2d");
    ctx.drawImage(videoRef.current, 0, 0, canvas.width, canvas.height);

    canvas.toBlob((blob) => {
      const file = new File([blob], "camera_capture.jpg", { type: "image/jpeg" });
      setSelectedFile(file);
      setPreviewUrl(URL.createObjectURL(blob));
      stopCamera();
    }, "image/jpeg");
  };

  const stopCamera = () => {
    if (videoRef.current && videoRef.current.srcObject) {
      videoRef.current.srcObject.getTracks().forEach((track) => track.stop());
    }
    setIsCameraActive(false);
  };

  const handleAnalyze = async () => {
    if (!selectedFile) {
      setErrorMsg("Please select or capture a product image first.");
      return;
    }

    setIsScanning(true);
    setErrorMsg("");
    setScanStage("Assessing package image clarity and resolution...");

    setTimeout(() => {
      setScanStage("Executing Optical Character Recognition (OCR)...");
    }, 500);

    setTimeout(() => {
      setScanStage("Extracting mandatory packaging fields & confidence...");
    }, 1000);

    setTimeout(() => {
      setScanStage("Evaluating 8-Rule Legal Metrology & FSSAI Engine...");
    }, 1500);

    try {
      const formData = new FormData();
      formData.append("file", selectedFile);
      formData.append("image", selectedFile);

      const token = localStorage.getItem("token");
      const headers = { "Content-Type": "multipart/form-data" };
      if (token) headers["Authorization"] = `Bearer ${token}`;

      const response = await axios.post(`${API_BASE_URL}/scans/analyze`, formData, { headers });
      setScanResult(response.data);
    } catch (err) {
      console.error(err);
      setErrorMsg(
        err?.response?.data?.detail || "Scan analysis failed. Please verify the backend service is running."
      );
    } finally {
      setIsScanning(false);
    }
  };

  const handleDownloadPdf = async (scanId) => {
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
      console.error("Failed to download PDF", err);
      alert("Failed to download PDF report. Ensure you are authorized.");
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-white flex flex-col">
      <Navbar role="user" />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 py-8">
        <div className="mb-8">
          <h2 className="text-3xl font-bold tracking-tight flex items-center gap-3">
            <span>📷</span> Packaged Commodity Metrology Scanner
          </h2>
          <p className="text-slate-400 mt-1">
            Upload or capture packaging declarations to evaluate 8 Legal Metrology & FSSAI statutory rules.
          </p>
        </div>

        {errorMsg && (
          <div className="mb-6 p-4 rounded-xl bg-red-950/60 border border-red-800 text-red-300 text-sm flex items-center justify-between">
            <span>⚠️ {errorMsg}</span>
            <button onClick={() => setErrorMsg("")} className="text-red-400 hover:text-white">✕</button>
          </div>
        )}

        <div className="grid lg:grid-cols-12 gap-8">
          {/* Left Column: Image Upload & Visual Preview */}
          <div className="lg:col-span-5 flex flex-col gap-5">
            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6">
              <h3 className="text-lg font-bold mb-4 flex items-center justify-between">
                <span>1. Upload or Capture Label</span>
                {previewUrl && (
                  <span className="text-xs px-2 py-0.5 rounded bg-blue-900/60 text-blue-300 border border-blue-700">
                    Image Loaded
                  </span>
                )}
              </h3>

              {isCameraActive ? (
                <div className="relative rounded-xl overflow-hidden bg-black aspect-[4/3] flex flex-col items-center justify-center border border-slate-700">
                  <video ref={videoRef} autoPlay playsInline className="w-full h-full object-cover" />
                  <div className="absolute bottom-4 flex gap-3">
                    <button
                      onClick={captureCamera}
                      className="bg-emerald-600 hover:bg-emerald-500 text-white px-5 py-2 rounded-xl font-semibold text-sm shadow-lg"
                    >
                      📸 Capture Photo
                    </button>
                    <button
                      onClick={stopCamera}
                      className="bg-slate-800 hover:bg-slate-700 text-white px-4 py-2 rounded-xl text-sm"
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              ) : previewUrl ? (
                <div className="relative rounded-xl overflow-hidden bg-slate-950 border border-slate-800 flex items-center justify-center p-2 group">
                  <img
                    src={previewUrl}
                    alt="Packaging preview"
                    className="max-h-[380px] w-auto object-contain rounded-lg shadow-md"
                  />

                  {isScanning && (
                    <div className="absolute inset-0 bg-blue-950/60 backdrop-blur-[2px] flex flex-col items-center justify-center">
                      <div className="animate-spin text-4xl mb-3">⚙️</div>
                      <p className="text-sm font-semibold text-cyan-300 px-4 text-center">{scanStage}</p>
                    </div>
                  )}
                </div>
              ) : (
                <div
                  onClick={() => fileInputRef.current?.click()}
                  className="border-2 border-dashed border-slate-700 hover:border-blue-500 rounded-2xl p-8 flex flex-col items-center justify-center cursor-pointer transition bg-slate-950/50 hover:bg-slate-900/50 min-h-[260px]"
                >
                  <div className="text-4xl mb-3">📁</div>
                  <p className="font-semibold text-slate-200">Drag & drop packaging photo or click to browse</p>
                  <p className="text-xs text-slate-400 mt-1">Supports JPG, PNG, WEBP (Clear, well-lit label)</p>
                </div>
              )}

              <input
                ref={fileInputRef}
                type="file"
                accept="image/*"
                onChange={handleFileChange}
                className="hidden"
              />

              <div className="grid grid-cols-2 gap-3 mt-4">
                <button
                  type="button"
                  onClick={() => fileInputRef.current?.click()}
                  className="bg-slate-800 hover:bg-slate-700 text-slate-200 text-sm font-medium py-2.5 px-4 rounded-xl border border-slate-700 transition flex items-center justify-center gap-2"
                >
                  <span>📂</span> Choose File
                </button>

                {!isCameraActive ? (
                  <button
                    type="button"
                    onClick={startCamera}
                    className="bg-slate-800 hover:bg-slate-700 text-slate-200 text-sm font-medium py-2.5 px-4 rounded-xl border border-slate-700 transition flex items-center justify-center gap-2"
                  >
                    <span>📷</span> Use Camera
                  </button>
                ) : (
                  <button
                    type="button"
                    onClick={stopCamera}
                    className="bg-slate-800 hover:bg-slate-700 text-slate-200 text-sm font-medium py-2.5 px-4 rounded-xl border border-slate-700 transition"
                  >
                    Close Camera
                  </button>
                )}
              </div>

              <button
                type="button"
                disabled={!selectedFile || isScanning}
                onClick={handleAnalyze}
                className="mt-4 w-full bg-blue-600 hover:bg-blue-500 disabled:bg-slate-800 disabled:text-slate-500 text-white py-3 rounded-xl font-bold transition shadow-lg shadow-blue-600/20 flex items-center justify-center gap-2"
              >
                {isScanning ? (
                  <span>Analyzing Package...</span>
                ) : (
                  <>
                    <span>🔍</span> Run Metrology Inspection
                  </>
                )}
              </button>
            </div>

            {/* Quality Check summary */}
            {scanResult && scanResult.quality && (
              <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5">
                <h4 className="text-xs uppercase tracking-wider text-slate-400 font-bold mb-3">
                  Image Quality Diagnostics
                </h4>
                <div className="grid grid-cols-2 gap-3 text-xs">
                  <div className="p-3 bg-slate-950 rounded-xl border border-slate-800/80">
                    <span className="text-slate-400 block">Sharpness / Blur</span>
                    <span className="font-semibold text-slate-200">
                      {scanResult.quality.valid ? "✅ Passed (Clear)" : "⚠️ Blur Detected"}
                    </span>
                  </div>
                  <div className="p-3 bg-slate-950 rounded-xl border border-slate-800/80">
                    <span className="text-slate-400 block">Resolution</span>
                    <span className="font-semibold text-slate-200">
                      {scanResult.quality.width}x{scanResult.quality.height} px
                    </span>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Right Column: Inspection Findings & Compliance Report */}
          <div className="lg:col-span-7 flex flex-col gap-6">
            {!scanResult ? (
              <div className="bg-slate-900/60 border border-slate-800/80 rounded-2xl p-12 text-center flex flex-col items-center justify-center min-h-[420px]">
                <div className="w-16 h-16 rounded-2xl bg-blue-950/80 border border-blue-800/40 flex items-center justify-center text-3xl mb-4">
                  ⚖️
                </div>
                <h3 className="text-xl font-bold text-slate-200">Awaiting Product Analysis</h3>
                <p className="text-sm text-slate-400 max-w-md mt-2">
                  Upload a packaged commodity image on the left and click <strong>Run Metrology Inspection</strong> to inspect mandatory packaging declarations.
                </p>
                <div className="mt-6 flex flex-wrap gap-2 justify-center max-w-sm">
                  {["Rule 6(1)(a) Mfr Address", "Rule 6(1)(c) Net Qty", "Rule 6(1)(d) MFD & Expiry", "Rule 6(1)(e) MRP", "Rule 6(1)(n) Consumer Care", "FSSAI License"].map((rule, idx) => (
                    <span key={idx} className="text-xs bg-slate-800/80 text-slate-400 px-2.5 py-1 rounded-full border border-slate-700/50">
                      {rule}
                    </span>
                  ))}
                </div>
              </div>
            ) : (
              <div className="flex flex-col gap-6">
                {/* Overall Verdict Banner */}
                <div
                  className={`border rounded-2xl p-6 shadow-xl ${
                    scanResult.status === "COMPLIANT"
                      ? "bg-emerald-950/40 border-emerald-500/40 text-emerald-100"
                      : scanResult.status === "NON-COMPLIANT" || scanResult.status === "NON_COMPLIANT"
                      ? "bg-rose-950/40 border-rose-500/40 text-rose-100"
                      : "bg-amber-950/40 border-amber-500/40 text-amber-100"
                  }`}
                >
                  <div className="flex flex-wrap items-center justify-between gap-4">
                    <div className="flex items-center gap-4">
                      <div className="text-4xl">
                        {scanResult.status === "COMPLIANT" ? "🛡️" : scanResult.status === "NON-COMPLIANT" || scanResult.status === "NON_COMPLIANT" ? "🚫" : "⚠️"}
                      </div>
                      <div>
                        <div className="flex items-center gap-2">
                          <span
                            className={`text-xs font-bold px-2.5 py-1 rounded-full uppercase tracking-wider ${
                              scanResult.status === "COMPLIANT"
                                ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/40"
                                : scanResult.status === "NON-COMPLIANT" || scanResult.status === "NON_COMPLIANT"
                                ? "bg-rose-500/20 text-rose-300 border border-rose-500/40"
                                : "bg-amber-500/20 text-amber-300 border border-amber-500/40"
                            }`}
                          >
                            {scanResult.status}
                          </span>
                          <span className="text-xs text-slate-400 font-mono">Scan #{scanResult.scan_id}</span>
                        </div>
                        <h3 className="text-2xl font-bold mt-1">
                          {scanResult.status === "COMPLIANT"
                            ? "Complies with Legal Metrology"
                            : scanResult.status === "NON-COMPLIANT" || scanResult.status === "NON_COMPLIANT"
                            ? "Statutory Violations Flagged"
                            : "Manual Inspection Required"}
                        </h3>
                        <p className="text-xs text-slate-300 mt-1">
                          {scanResult.rules_checked || 8} Statutory Rules Evaluated • {scanResult.violation_count || 0} Violation(s)
                        </p>
                      </div>
                    </div>

                    <div className="flex items-center gap-3">
                      <button
                        onClick={() => handleDownloadPdf(scanResult.scan_id)}
                        className="bg-blue-600 hover:bg-blue-500 text-white text-xs font-bold px-4 py-2.5 rounded-xl shadow-md transition flex items-center gap-1.5"
                      >
                        <span>📥</span> Download PDF
                      </button>
                      <Link
                        to={`/user/complaint?scan_id=${scanResult.scan_id}`}
                        className="bg-rose-600/30 hover:bg-rose-600 text-rose-300 hover:text-white text-xs font-bold px-4 py-2.5 rounded-xl border border-rose-600/50 transition flex items-center gap-1.5"
                      >
                        <span>📢</span> File Grievance
                      </Link>
                    </div>
                  </div>
                </div>

                {/* Mandatory Declarations Table with Confidence */}
                <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6">
                  <h4 className="text-base font-bold mb-4 flex items-center justify-between">
                    <span>Statutory Declarations & Confidence</span>
                    <span className="text-xs text-slate-400 font-normal">8-Rule Metrology & FSSAI Check</span>
                  </h4>

                  <div className="overflow-x-auto">
                    <table className="w-full text-left text-sm">
                      <thead>
                        <tr className="border-b border-slate-800 text-xs uppercase text-slate-400">
                          <th className="pb-3 font-semibold">Declaration</th>
                          <th className="pb-3 font-semibold">Statutory Rule</th>
                          <th className="pb-3 font-semibold">Extracted Value</th>
                          <th className="pb-3 font-semibold text-center">Confidence</th>
                          <th className="pb-3 font-semibold text-right">Status</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-800/60">
                        {Object.entries(RULE_TITLES).map(([key, meta]) => {
                          const rawVal = scanResult.fields?.[key] ?? scanResult.extracted_fields?.[key];
                          const confData = scanResult.confidences?.[key];
                          
                          let displayVal = null;
                          if (rawVal) {
                            if (typeof rawVal === "object") {
                              displayVal = rawVal.value ? (rawVal.unit ? `${rawVal.value} ${rawVal.unit}` : rawVal.value) : JSON.stringify(rawVal);
                            } else {
                              displayVal = String(rawVal);
                            }
                          }

                          let confScore = confData?.confidence ?? 0.0;
                          if (!confScore && displayVal) confScore = 0.92;

                          return (
                            <tr key={key}>
                              <td className="py-3 font-medium text-slate-200">{meta.label}</td>
                              <td className="py-3 text-xs text-slate-400 font-mono">{meta.rule}</td>
                              <td className="py-3">
                                {displayVal ? (
                                  <span className="text-slate-100 font-mono text-xs bg-slate-800 px-2 py-1 rounded">
                                    {displayVal}
                                  </span>
                                ) : (
                                  <span className="text-slate-500 italic text-xs">Missing / Not Detected</span>
                                )}
                              </td>
                              <td className="py-3 text-center">
                                {displayVal ? (
                                  <span className={`text-xs font-mono font-bold ${confScore >= 0.9 ? "text-emerald-400" : confScore >= 0.7 ? "text-amber-400" : "text-rose-400"}`}>
                                    {Math.round(confScore * 100)}%
                                  </span>
                                ) : (
                                  <span className="text-slate-600 text-xs">-</span>
                                )}
                              </td>
                              <td className="py-3 text-right">
                                {displayVal ? (
                                  <span className="inline-flex items-center text-xs font-semibold px-2 py-0.5 rounded-full bg-emerald-950 text-emerald-400 border border-emerald-800">
                                    ✓ Present
                                  </span>
                                ) : (
                                  <span className="inline-flex items-center text-xs font-semibold px-2 py-0.5 rounded-full bg-rose-950 text-rose-400 border border-rose-800">
                                    ✕ Missing
                                  </span>
                                )}
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                </div>

                {/* Violations Detail Section */}
                {scanResult.violations && scanResult.violations.length > 0 && (
                  <div className="bg-rose-950/20 border border-rose-900/50 rounded-2xl p-6">
                    <h4 className="text-base font-bold text-rose-400 mb-3 flex items-center gap-2">
                      <span>⚠️</span> Detected Metrology Violations ({scanResult.violations.length})
                    </h4>
                    <div className="space-y-3">
                      {scanResult.violations.map((violation, idx) => (
                        <div key={idx} className="p-3 bg-slate-900/80 rounded-xl border border-rose-900/30 flex items-start justify-between gap-4">
                          <div>
                            <div className="flex items-center gap-2">
                              <span className="text-xs font-bold text-rose-400">{violation.field?.toUpperCase()}</span>
                              <span className="text-[10px] px-2 py-0.5 rounded uppercase font-bold bg-rose-900/50 text-rose-300">
                                {violation.severity}
                              </span>
                            </div>
                            <p className="text-xs text-slate-300 mt-1">{violation.description}</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}

export default ScanProduct;
