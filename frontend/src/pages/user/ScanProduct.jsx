import React, { useState, useRef } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  Upload, Camera, RefreshCw, AlertTriangle, ShieldCheck, CheckCircle,
  FileText, ChevronRight, X, ArrowRight, Info
} from "lucide-react";
import Navbar from "../../components/Navbar";
import Footer from "../../components/Footer";
import API_BASE_URL from "../../config";

// Posts FormData to /scans/ocr-extract with auth token
const scanProduct = async (formData) => {
  const token = localStorage.getItem("token");
  const headers = token ? { Authorization: `Bearer ${token}` } : {};
  const res = await fetch(`${API_BASE_URL}/scans/ocr-extract`, {
    method: "POST",
    headers,
    body: formData,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }
  return res.json();
};

const ScanProduct = () => {
  const navigate = useNavigate();

  const [selectedFile, setSelectedFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [isScanning, setIsScanning] = useState(false);
  
  // Stages: upload -> analysis -> error -> quality_warning
  const [scanStage, setScanStage] = useState("upload");
  const [scanResult, setScanResult] = useState(null);
  const [errorMsg, setErrorMsg] = useState("");

  const fileInputRef = useRef(null);
  const videoRef = useRef(null);
  const streamRef = useRef(null);
  const [isCameraActive, setIsCameraActive] = useState(false);

  const handleFileSelect = (e) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      setSelectedFile(file);
      setPreviewUrl(URL.createObjectURL(file));
      setScanStage("upload");
      setErrorMsg("");
      setScanResult(null);
    }
  };

  const clearSelection = () => {
    setSelectedFile(null);
    setPreviewUrl(null);
    setScanStage("upload");
    setScanResult(null);
    setErrorMsg("");
  };

  // ---------------- Camera Handling ----------------
  const startCamera = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: "environment" }
      });
      setIsCameraActive(true);
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
      }
      streamRef.current = stream;
    } catch (err) {
      setErrorMsg("Camera access denied or unavailable. Please upload a clear photo instead.");
    }
  };

  const stopCamera = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }
    setIsCameraActive(false);
  };

  const capturePhoto = () => {
    if (videoRef.current) {
      const canvas = document.createElement("canvas");
      canvas.width = videoRef.current.videoWidth;
      canvas.height = videoRef.current.videoHeight;
      const ctx = canvas.getContext("2d");
      ctx.drawImage(videoRef.current, 0, 0, canvas.width, canvas.height);

      canvas.toBlob((blob) => {
        if (blob) {
          const file = new File([blob], "camera-capture.jpg", { type: "image/jpeg" });
          setSelectedFile(file);
          setPreviewUrl(URL.createObjectURL(file));
          stopCamera();
        }
      }, "image/jpeg");
    }
  };
  // --------------------------------------------------

  const processScan = async (forceProceed = false) => {
    if (!selectedFile) return;

    setIsScanning(true);
    setScanStage("analysis");
    setErrorMsg("");

    try {
      const formData = new FormData();
      formData.append("file", selectedFile);
      formData.append("image", selectedFile);

      if (forceProceed) {
        formData.append("force_proceed", "true");
      }

      const response = await scanProduct(formData);
      
      if (response.needs_retake_prompt && !forceProceed) {
        setScanResult(response);
        setScanStage("quality_warning");
      } else {
        // Extraction successful, navigate to the review page
        navigate(`/user/review/${response.scan_id}`);
      }

    } catch (error) {
      setErrorMsg(error.message || "Failed to process scan. Please verify server connection and try again.");
      setScanStage("error");
    } finally {
      setIsScanning(false);
    }
  };

  const handleRetake = () => {
    clearSelection();
  };

  const handleContinueAnyway = () => {
    processScan(true);
  };

  return (
    <div className="min-h-screen bg-[#FFFFFF] flex flex-col justify-between">
      <Navbar role="user" />
      
      <main className="flex-1 max-w-7xl mx-auto w-full px-4 sm:px-6 lg:px-8 py-8">
        
        {/* ── Step Indicator ────────────────────────────────────────── */}
        <div className="mb-8 border-b border-[#D5DCE5] pb-6">
          <div className="flex flex-wrap items-center justify-between gap-4 mb-4">
            <div>
              <h1 className="text-2xl font-bold text-[#183153] tracking-tight">
                Package Commodity Inspection
              </h1>
              <p className="text-xs sm:text-sm text-[#64748B] mt-0.5">
                Upload packaging label for OCR extraction and statutory declaration verification
              </p>
            </div>
            <span className="text-xs px-2.5 py-1 bg-[#F5F7FA] text-[#174A7E] border border-[#D5DCE5] font-semibold rounded">
              Rule 6 Compliance Check
            </span>
          </div>

          {/* Workflow Steps */}
          <div className="grid grid-cols-4 gap-2 text-xs font-semibold">
            <div className="flex items-center gap-2 p-2.5 rounded bg-[#174A7E] text-white">
              <span className="w-5 h-5 rounded-full bg-white text-[#174A7E] flex items-center justify-center text-[11px] font-bold">1</span>
              <span className="hidden sm:inline">Upload Image</span>
            </div>
            <div className="flex items-center gap-2 p-2.5 rounded bg-[#F5F7FA] text-[#64748B] border border-[#D5DCE5]">
              <span className="w-5 h-5 rounded-full bg-[#D5DCE5] text-[#183153] flex items-center justify-center text-[11px] font-bold">2</span>
              <span className="hidden sm:inline">Review Data</span>
            </div>
            <div className="flex items-center gap-2 p-2.5 rounded bg-[#F5F7FA] text-[#64748B] border border-[#D5DCE5]">
              <span className="w-5 h-5 rounded-full bg-[#D5DCE5] text-[#183153] flex items-center justify-center text-[11px] font-bold">3</span>
              <span className="hidden sm:inline">Confirm Review</span>
            </div>
            <div className="flex items-center gap-2 p-2.5 rounded bg-[#F5F7FA] text-[#64748B] border border-[#D5DCE5]">
              <span className="w-5 h-5 rounded-full bg-[#D5DCE5] text-[#183153] flex items-center justify-center text-[11px] font-bold">4</span>
              <span className="hidden sm:inline">Audit Report</span>
            </div>
          </div>
        </div>

        {/* ── Main Scan Layout ──────────────────────────────────────── */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          
          {/* Left Column: Upload / Camera (7 Cols) */}
          <div className="lg:col-span-7 space-y-6">
            
            <div className="bg-white rounded border border-[#D5DCE5] p-6 shadow-sm">
              <div className="flex items-center justify-between mb-4 pb-3 border-b border-[#D5DCE5]">
                <h2 className="text-sm font-bold text-[#183153] uppercase tracking-wider flex items-center gap-2">
                  <Upload size={16} className="text-[#174A7E]" />
                  Provide Package Label Image
                </h2>
                <span className="text-xs text-[#64748B]">JPEG, PNG, WEBP</span>
              </div>
              
              {!previewUrl && !isCameraActive && (
                <div className="flex flex-col items-center">
                  <div className="w-full h-64 border-2 border-dashed border-[#D5DCE5] rounded flex flex-col items-center justify-center bg-[#F5F7FA] p-6 text-center mb-5">
                    <div className="w-12 h-12 rounded bg-white border border-[#D5DCE5] flex items-center justify-center text-[#174A7E] mb-3">
                      <Upload size={22} />
                    </div>
                    <p className="text-xs sm:text-sm font-semibold text-[#183153]">
                      Click browse or drop image of the packaged commodity
                    </p>
                    <p className="text-xs text-[#64748B] mt-1 max-w-sm">
                      Ensure mandatory declarations (MRP, Net Quantity, Mfg Date, Address) are clearly visible and well-lit.
                    </p>
                    <button
                      onClick={() => fileInputRef.current?.click()}
                      className="mt-4 px-4 py-2 bg-white border border-[#174A7E] text-[#174A7E] hover:bg-[#F5F7FA] rounded text-xs font-semibold shadow-sm transition-colors"
                    >
                      Browse Device Files
                    </button>
                    <input
                      type="file"
                      ref={fileInputRef}
                      onChange={handleFileSelect}
                      accept="image/jpeg, image/png, image/webp"
                      className="hidden"
                    />
                  </div>

                  <div className="relative w-full text-center">
                    <div className="absolute inset-0 flex items-center" aria-hidden="true">
                      <div className="w-full border-t border-[#D5DCE5]" />
                    </div>
                    <div className="relative">
                      <span className="px-3 bg-white text-xs text-[#64748B] font-medium uppercase tracking-wider">
                        Or Capture Directly
                      </span>
                    </div>
                  </div>

                  <button
                    onClick={startCamera}
                    className="mt-4 w-full flex justify-center items-center gap-2 px-4 py-2.5 border border-[#D5DCE5] rounded text-xs font-semibold text-[#183153] bg-[#F5F7FA] hover:bg-[#EDF2F7] transition-colors"
                  >
                    <Camera size={16} className="text-[#174A7E]" />
                    Open Device Camera
                  </button>
                </div>
              )}

              {/* Camera Active View */}
              {isCameraActive && (
                <div className="flex flex-col items-center">
                  <div className="relative w-full h-80 bg-black rounded overflow-hidden mb-4 border border-[#D5DCE5]">
                    <video 
                      ref={videoRef} 
                      autoPlay 
                      playsInline 
                      className="w-full h-full object-cover"
                    />
                    <div className="absolute inset-0 border-2 border-white/60 m-6 rounded pointer-events-none flex items-center justify-center">
                      <span className="text-[11px] text-white/80 bg-black/60 px-2.5 py-1 rounded">
                        Position label within frame
                      </span>
                    </div>
                  </div>
                  <div className="flex w-full space-x-3">
                    <button
                      onClick={stopCamera}
                      className="flex-1 px-4 py-2 bg-white border border-[#D5DCE5] rounded text-xs font-semibold text-[#64748B] hover:bg-[#F5F7FA]"
                    >
                      Cancel
                    </button>
                    <button
                      onClick={capturePhoto}
                      className="flex-1 px-4 py-2 bg-[#174A7E] hover:bg-[#133D68] text-white text-xs font-semibold rounded shadow-sm"
                    >
                      Capture Photo
                    </button>
                  </div>
                </div>
              )}

              {/* Image Preview View */}
              {previewUrl && (
                <div className="flex flex-col">
                  <div className="relative w-full h-80 bg-[#F5F7FA] rounded border border-[#D5DCE5] overflow-hidden mb-4 flex items-center justify-center p-2">
                    <img 
                      src={previewUrl} 
                      alt="Uploaded package preview" 
                      className="w-full h-full object-contain"
                    />
                    {isScanning && (
                      <div className="absolute inset-0 bg-white/80 backdrop-blur-xs flex flex-col items-center justify-center">
                        <RefreshCw className="w-8 h-8 text-[#174A7E] animate-spin mb-3" />
                        <p className="text-sm font-bold text-[#183153]">Running Multi-Variant OCR Extraction...</p>
                        <p className="text-xs text-[#64748B] mt-1">Analyzing declarations for Legal Metrology compliance</p>
                      </div>
                    )}
                  </div>

                  {!isScanning && scanStage === "upload" && (
                    <div className="flex flex-col sm:flex-row gap-3">
                      <button
                        onClick={() => processScan(false)}
                        className="flex-1 flex justify-center items-center gap-2 px-4 py-2.5 bg-[#174A7E] hover:bg-[#133D68] text-white text-xs sm:text-sm font-semibold rounded shadow-sm transition-colors"
                      >
                        <ShieldCheck size={16} />
                        Run OCR & Proceed to Review
                      </button>
                      <button
                        onClick={clearSelection}
                        className="px-4 py-2.5 bg-white border border-[#D5DCE5] hover:bg-[#F5F7FA] text-[#183153] text-xs sm:text-sm font-semibold rounded transition-colors"
                      >
                        Change Photo
                      </button>
                    </div>
                  )}
                </div>
              )}

              {/* Quality Warning Dialog */}
              {scanStage === "quality_warning" && scanResult && (
                <div className="mt-4 p-4 bg-[#FEF3C7] rounded border border-[#FDE68A] text-[#B45309]">
                  <div className="flex items-start gap-3">
                    <AlertTriangle size={20} className="mt-0.5 shrink-0" />
                    <div>
                      <h3 className="text-xs font-bold uppercase tracking-wider">
                        Image Quality Warning ({scanResult.quality_tier})
                      </h3>
                      <p className="text-xs mt-1 leading-relaxed text-[#92400E]">
                        {scanResult.image_quality_warning || "The image appears blurry or has poor lighting. OCR extraction may be incomplete or low-confidence."}
                      </p>
                      <div className="mt-4 flex flex-wrap gap-2.5">
                        <button
                          onClick={handleRetake}
                          className="px-3.5 py-1.5 bg-[#B45309] hover:bg-[#92400E] text-white text-xs font-semibold rounded shadow-sm"
                        >
                          Retake Clearer Photo
                        </button>
                        <button
                          onClick={handleContinueAnyway}
                          className="px-3.5 py-1.5 bg-white border border-[#B45309] text-[#B45309] hover:bg-[#FFFBEB] text-xs font-semibold rounded"
                        >
                          Continue Anyway (Flagged in Report)
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Error Message */}
              {errorMsg && (
                <div className="mt-4 p-3.5 bg-[#FEE2E2] border border-[#FECACA] rounded text-xs text-[#B91C1C] flex items-start gap-2">
                  <AlertTriangle size={16} className="mt-0.5 shrink-0" />
                  <p>{errorMsg}</p>
                </div>
              )}

            </div>

          </div>

          {/* Right Column: Statutory Regulatory Reference (5 Cols) */}
          <div className="lg:col-span-5 space-y-6">
            
            <div className="bg-[#F5F7FA] border border-[#D5DCE5] rounded p-6">
              <h2 className="text-xs font-bold text-[#183153] uppercase tracking-wider mb-3 flex items-center gap-1.5">
                <Info size={14} className="text-[#174A7E]" />
                Legal Metrology Rule 6 Checklist
              </h2>
              <p className="text-xs text-[#475569] leading-relaxed mb-4">
                Every packaged commodity sold in India must display these statutory declarations clearly and conspicuously:
              </p>

              <div className="space-y-2.5 text-xs">
                <div className="p-2.5 bg-white rounded border border-[#D5DCE5]">
                  <span className="font-bold text-[#183153] block">1. Maximum Retail Price (MRP)</span>
                  <span className="text-[#64748B]">Inclusive of all taxes in standard Rupees format.</span>
                </div>
                <div className="p-2.5 bg-white rounded border border-[#D5DCE5]">
                  <span className="font-bold text-[#183153] block">2. Net Quantity</span>
                  <span className="text-[#64748B]">In standard metric units (g, kg, ml, l, or number).</span>
                </div>
                <div className="p-2.5 bg-white rounded border border-[#D5DCE5]">
                  <span className="font-bold text-[#183153] block">3. Month & Year of Manufacture</span>
                  <span className="text-[#64748B]">Distinct from best before / expiry date information.</span>
                </div>
                <div className="p-2.5 bg-white rounded border border-[#D5DCE5]">
                  <span className="font-bold text-[#183153] block">4. Manufacturer & Packer Details</span>
                  <span className="text-[#64748B]">Full name and complete registered commercial address.</span>
                </div>
                <div className="p-2.5 bg-white rounded border border-[#D5DCE5]">
                  <span className="font-bold text-[#183153] block">5. Consumer Care Details</span>
                  <span className="text-[#64748B]">Helpline telephone number or official contact email.</span>
                </div>
              </div>

              <div className="mt-5 pt-4 border-t border-[#D5DCE5] text-[11px] text-[#64748B]">
                <span>Two-step protocol: Extracted declarations must be confirmed on the </span>
                <span className="font-semibold text-[#183153]">Review Screen</span>
                <span> before the compliance report is generated.</span>
              </div>
            </div>

          </div>

        </div>

      </main>

      <Footer />
    </div>
  );
};

export default ScanProduct;
